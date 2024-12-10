import requests
import os
from datetime import datetime, timedelta

ORG = "CanarysPlayground"

TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    raise ValueError("Missing GITHUB_TOKEN. Please set it in the environment variables.")

headers = {"Authorization": f"token {TOKEN}"}
six_months_ago = datetime.now() - timedelta(days=180)

def fetch_repos():
    """Fetch all repositories for the organization or user."""
    repos_url = f"https://api.github.com/orgs/{ORG}/repos?per_page=100"
    repos = []
    while repos_url:
        response = requests.get(repos_url, headers=headers)
        response.raise_for_status()
        repos.extend(response.json())
        repos_url = response.links.get('next', {}).get('url')
    return repos

def fetch_branches(repo_name):
    """Fetch all branches for a given repository."""
    branches_url = f"https://api.github.com/repos/{ORG}/{repo_name}/branches"
    response = requests.get(branches_url, headers=headers)
    response.raise_for_status()
    return response.json()

def check_inactivity(repo_name):
    """Check if all branches in a repository are inactive."""
    branches = fetch_branches(repo_name)
    for branch in branches:
        branch_name = branch["name"]
        commit_sha = branch["commit"]["sha"]
        
        # Fetch the commit details
        commit_url = f"https://api.github.com/repos/{ORG}/{repo_name}/commits/{commit_sha}"
        commit_response = requests.get(commit_url, headers=headers)
        if commit_response.status_code == 200:
            commit_date = commit_response.json()["commit"]["committer"]["date"]
            commit_datetime = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ")
            
            # If any branch has a commit within 6 months, the repo is active
            if commit_datetime >= six_months_ago:
                return False
    return True

repos = fetch_repos()
inactive_repos = []

for repo in repos:
    print(f"Checking repository: {repo['name']}...")
    if check_inactivity(repo["name"]):
        inactive_repos.append(repo["name"])

# Export results to a file
output_file = "inactive_repos.txt"
with open(output_file, "w") as f:
    if inactive_repos:
        f.write("Inactive Repositories (no commits in any branch in 6 months):\n")
        for repo in inactive_repos:
            f.write(f"- {repo}\n")
        print(f"\nInactive repositories have been saved to {output_file}.")
    else:
        f.write("All repositories are active.\n")
        print(f"\nAll repositories are active. Results have been saved to {output_file}.")
