import os
import subprocess
import sys
import time
import requests
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget, QLineEdit, QLabel, \
    QHBoxLayout, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QThread, pyqtSignal
from dataclasses import dataclass, field
from typing import List

# Initialize logger
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()])

@dataclass
class Result:
    url: str
    passed: bool
    score: int
    details: str

class RepoChecker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(list)

    def __init__(self, urls, port, script_path, parent=None):
        super(RepoChecker, self).__init__(parent)
        self.urls = urls
        self.port = port
        self.script_path = script_path
        self.results = []

    def clone_repo(self, url, directory):
        logging.info(f"Cloning repository: {url}")
        subprocess.run(["git", "clone", url, directory], check=True)
        logging.info(f"Repository cloned: {url}")

    def build_and_run_docker(self, directory):
        logging.info(f"Building Docker image for directory: {directory}")
        os.chdir(directory)
        subprocess.run(["docker", "build", "-t", "student-app", "."], check=True)
        container = subprocess.run(
            ["docker", "run", "--network", "new-net", f"-p{self.port}:{self.port}", "-d", "--name", "student",
             "student-app"], check=True, stdout=subprocess.PIPE)
        container_id = container.stdout.strip().decode("utf-8")
        os.chdir("..")
        logging.info(f"Docker container started with ID: {container_id}")
        return container_id

    def test_app(self, container_id, directory):
        logging.info(f"Testing application in container ID: {container_id}")
        time.sleep(5)  # wait for the server to start
        details = ""
        passed = False
        score = 0
        result = subprocess.run([sys.executable, self.script_path, directory], capture_output=True, text=True)
        details += f"External script output: {result.stdout}\n"
        logging.info(f"External script output: {result.stdout}")

        if "score:" in result.stdout.lower():
            score_line = next((line for line in result.stdout.split('\n') if "score:" in line.lower()), None)
            if score_line:
                score = int(score_line.split(":")[-1].strip())

        if "passed:" in result.stdout.lower():
            pass_line = next((line for line in result.stdout.split('\n') if "passed:" in line.lower()), None)
            if pass_line:
                passed = pass_line.split(":")[-1].strip().lower() == "true"

        logging.info(f"Test result for {directory}: Passed={passed}, Score={score}")
        return passed, score, details

    def stop_and_remove_docker(self, container_id):
        logging.info(f"Stopping and removing Docker container ID: {container_id}")
        subprocess.run(["docker", "stop", container_id], check=True)
        subprocess.run(["docker", "rm", container_id], check=True)
        logging.info(f"Docker container ID: {container_id} stopped and removed")

    def run(self):
        for url in self.urls:
            self.log_signal.emit(f"Checking {url}\n")
            logging.info(f"Starting check for {url}")
            directory = url.split('/')[-1].replace('.git', '')
            self.clone_repo(url, directory)
            self.log_signal.emit(f"Building and running Docker for {url}\n")
            container_id = self.build_and_run_docker(directory)
            self.log_signal.emit(f"Testing {url}\n")
            passed, score, details = self.test_app(container_id, directory)
            self.results.append(Result(url, passed, score, details))
            if passed:
                self.log_signal.emit(f"Tests passed for {url}\n")
            else:
                self.log_signal.emit(f"Tests failed for {url}\n")
            self.log_signal.emit(f"Stopping and removing Docker for {url}\n")
            self.stop_and_remove_docker(container_id)
        self.finished_signal.emit(self.results)

class ResultsWindow(QWidget):
    def __init__(self, results):
        super().__init__()
        self.setWindowTitle("Test Results")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setRowCount(len(results))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Repo URL", "Passed", "Score", "Details"])

        for row, result in enumerate(results):
            self.table.setItem(row, 0, QTableWidgetItem(result.url))
            self.table.setItem(row, 1, QTableWidgetItem("Yes" if result.passed else "No"))
            self.table.setItem(row, 2, QTableWidgetItem(str(result.score)))
            self.table.setItem(row, 3, QTableWidgetItem(result.details))

        layout.addWidget(self.table)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GitHub Repo Docker Tester")
        self.setGeometry(100, 100, 800, 600)

        main_layout = QVBoxLayout()

        url_and_port_layout = QHBoxLayout()

        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("Enter GitHub repo URLs, one per line...")
        url_and_port_layout.addWidget(self.url_input)

        port_layout = QVBoxLayout()

        self.port_label = QLabel("Port:")
        port_layout.addWidget(self.port_label)

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Enter port number...")
        port_layout.addWidget(self.port_input)

        self.script_path_label = QLabel("Python script path:")
        port_layout.addWidget(self.script_path_label)

        self.script_path_input = QLineEdit()
        self.script_path_input.setPlaceholderText("Enter Python script path...")
        port_layout.addWidget(self.script_path_input)

        url_and_port_layout.addLayout(port_layout)

        main_layout.addLayout(url_and_port_layout)

        self.check_button = QPushButton("Check")
        self.check_button.clicked.connect(self.start_checking)
        main_layout.addWidget(self.check_button)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def start_checking(self):
        urls = self.url_input.toPlainText().strip().split('\n')
        port = self.port_input.text().strip()
        script_path = self.script_path_input.text().strip()
        if not port.isdigit():
            self.log_output.append("Invalid port number. Please enter a valid integer.")
            logging.error("Invalid port number entered")
            return
        if not os.path.isfile(script_path):
            self.log_output.append("Invalid script path. Please enter a valid path to the Python script.")
            logging.error("Invalid script path entered")
            return
        self.check_button.setEnabled(False)
        self.worker = RepoChecker(urls, port, script_path)
        self.worker.log_signal.connect(self.update_log)
        self.worker.finished_signal.connect(self.show_results)
        self.worker.finished.connect(self.checking_finished)
        self.worker.start()

    def update_log(self, message):
        self.log_output.append(message)
        logging.info(message.strip())

    def show_results(self, results):
        self.results_window = ResultsWindow(results)
        self.results_window.show()
        logging.info("Results window displayed")

    def checking_finished(self):
        self.check_button.setEnabled(True)
        logging.info("Checking finished")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
