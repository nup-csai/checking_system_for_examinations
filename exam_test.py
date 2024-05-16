import requests
import json

def test_help(base_url):
    try:
        response = requests.get(f"{base_url}/help")
        if response.status_code == 200:
            return "/help" in response.text and "/github" in response.text and "/bitwise" in response.text and "/pandas" in response.text
        return False
    except Exception as e:
        print(f"Exception in test_help: {str(e)}")
        return False

def test_github(base_url):
    try:
        params = {'owner': 'octocat', 'repo': 'Hello-World'}
        response = requests.get(f"{base_url}/github", params=params)
        return response.status_code == 200 and "Error with User or Repo" not in response.text
    except Exception as e:
        print(f"Exception in test_github: {str(e)}")
        return False

def test_bitwise(base_url):
    try:
        data = {"n": 5, "p": 3}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{base_url}/bitwise", headers=headers, data=json.dumps(data))
        return response.status_code == 200 and response.text in ["yes", "no"]
    except Exception as e:
        print(f"Exception in test_bitwise: {str(e)}")
        return False

def test_pandas(base_url):
    try:
        data = {"magnitude": 5, "depth": 10}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{base_url}/pandas", headers=headers, data=json.dumps(data))
        return response.status_code == 200 and response.text.isdigit()
    except Exception as e:
        print(f"Exception in test_pandas: {str(e)}")
        return False

def calculate_score(base_url):
    score = 0
    details = ""

    if test_help(base_url):
        details += "Help endpoint works\n"
        score += 10
    else:
        details += "Help endpoint failed\n"

    if test_github(base_url):
        details += "GitHub endpoint works\n"
        score += 10
    else:
        details += "GitHub endpoint failed\n"

    if test_bitwise(base_url):
        details += "Bitwise endpoint works\n"
        score += 10
    else:
        details += "Bitwise endpoint failed\n"

    if test_pandas(base_url):
        details += "Pandas endpoint works\n"
        score += 10
    else:
        details += "Pandas endpoint failed\n"

    passed = score == 40

    return score, details, passed

if __name__ == "__main__":
    base_url = "http://localhost:8080"
    score, details, passed = calculate_score(base_url)
    print(details)
    print(f"score: {score}")
    print(f"passed: {passed}")
