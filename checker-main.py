import os
import subprocess
import sys
import time
import requests

def clone_repo(url):
    subprocess.run(["git", "clone", url], check=True)

def build_and_run_docker(directory):
    os.chdir(directory)
    subprocess.run(["docker", "build", "-t", "student-app", "."], check=True)
    container = subprocess.run(["docker", "run", "-d", "--name", "student", "student-app"], check=True, stdout=subprocess.PIPE)
    container_id = container.stdout.strip().decode("utf-8")
    os.chdir("..")
    return container_id

def test_app(container_id):
    time.sleep(5)
    tests = [
        {"method": "GET", "path": "http://127.0.0.1:6001/help", "status_code": 200},
    ]

    for test in tests:
        response = requests.get(test["path"])
        if response.status_code != test["status_code"]:
            print(f"Test failed: expected status code {test['status_code']}, got {response.status_code}")
            return False

    return True

def stop_and_remove_docker(container_id):
    subprocess.run(["docker", "stop", container_id], check=True)
    subprocess.run(["docker", "rm", container_id], check=True)

def main():
    repos = [
        "https://github.com/CS-intro-with-Python/midterm-StandartIvard",
        "https://github.com/CS-intro-with-Python/exam-variant-2-StandartIvard",

    ]

    for repo in repos:
        print(f"Cloning {repo}")
        #clone_repo(repo)
        print(f"Building and running Docker for {repo}")
        directory = repo.split("/")[-1].rstrip(".git")
        container_id = build_and_run_docker(directory)
        print(f"Testing {repo}")
        if test_app(container_id):
            print(f"Tests passed for {repo}")
        else:
            print(f"Tests failed for {repo}")
        print(f"Stopping and removing Docker for {repo}")
        stop_and_remove_docker(container_id)

if __name__ == "__main__":
    main()