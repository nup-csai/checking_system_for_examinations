import sh

# List of repositories you want to download in the format 'user/repo'
repos = ["https://github.com/StandartIvard/MOODProject"]

for repo in repos:
    # Clone the repository using the GitHub CLI
    sh.gh("repo", "clone", repo)
