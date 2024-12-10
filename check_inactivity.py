import requests
import os
from datetime import datetime, timedelta

# Environment variables
TOKEN = os.getenv("GITHUB_TOKEN")
ORG = "CanarysPlayground"

if not TOKEN:
    raise ValueError("Missing GITHUB_TOKEN")

headers = {"Authorization": f"token {TOKEN}"}
six_months_ago = datetime.now() - timedelta(days=30)

def fetch_repos():
    repos_url = f"https://api.github.com/orgs/{ORG}/repos?per_page=100"
    repos = []
    while repos_url:
        response = requests.get(repos_url, headers=headers)
        response.raise_for_status()
        repos.extend(response.json())
        repos_url = response.links.get('next', {}).get('url')
    return repos

def check_inactive_repos(repos):
    inactive_repos = []
    for repo in repos:
        commits_url = repo["commits_url"].replace("{/sha}", "")
        commits_response = requests.get(commits_url, headers=headers)
        if commits_response.status_code == 200:
            commits = commits_response.json()
            if commits:
                last_commit_date = commits[0]["commit"]["committer"]["date"]
                last_commit_datetime = datetime.strptime(last_commit_date, "%Y-%m-%dT%H:%M:%SZ")
                if last_commit_datetime < six_months_ago:
                    inactive_repos.append(repo["name"])
    return inactive_repos

repos = fetch_repos()
inactive_repos = check_inactive_repos(repos)

if inactive_repos:
    print("Inactive Repositories (no commits in 6 months):")
    for repo in inactive_repos:
        print(f"- {repo}")
else:
    print("All repositories are active.")
