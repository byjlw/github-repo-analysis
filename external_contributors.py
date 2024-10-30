import argparse
import json
import os
from datetime import datetime

import requests


def get_contributors(repo_owner, repo_name, github_token):
    """Fetch contributors to the repository."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contributors"
    headers = {
        "Authorization": f"token {github_token}",
        "Content-Type": "application/json",
    }
    contributors = []
    while True:
        response = requests.get(url, headers=headers)
        contributors.extend(response.json())
        if "next" in response.links:
            url = response.links["next"]["url"]
        else:
            break
    return contributors


def get_org_members(org, github_token, org_members_cache):
    """Fetch members of an organization and store them in the cache."""
    if org in org_members_cache:
        return org_members_cache[org]
    url = f"https://api.github.com/orgs/{org}/members?role=all"
    headers = {
        "Authorization": f"token {github_token}",
        "Content-Type": "application/json",
        "X-GitHub-Media-Type": "github.v3",
    }
    members = []
    while True:
        response = requests.get(url, headers=headers)
        members.extend(response.json())
        if "next" in response.links:
            url = response.links["next"]["url"]
        else:
            break
    org_members_cache[org] = [member["login"] for member in members]
    return org_members_cache[org]


def is_external_contributor(username, filter_orgs, github_token, org_members_cache):
    """Check if a contributor is external (not part of filtered organizations)."""
    for org in filter_orgs:
        if username in get_org_members(org, github_token, org_members_cache):
            return False
    return True


def get_pull_requests(repo_owner, repo_name, state, github_token):
    """Fetch pull requests for the repository."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls?state={state}"
    headers = {
        "Authorization": f"token {github_token}",
        "Content-Type": "application/json",
    }
    prs = []
    while True:
        response = requests.get(url, headers=headers)
        prs.extend(response.json())
        if "next" in response.links:
            url = response.links["next"]["url"]
        else:
            break
    return prs


def get_external_contributors(repo_owner, repo_name, filter_orgs, github_token):
    """Fetch external contributors and their monthly PR counts."""
    contributors = get_contributors(repo_owner, repo_name, github_token)
    org_members_cache = {}
    external_contributors = {}
    for contributor in contributors:
        username = contributor["login"]
        if is_external_contributor(
            username, filter_orgs, github_token, org_members_cache
        ):
            external_contributors[username] = {"prs": 0, "months": {}}
    prs = get_pull_requests(repo_owner, repo_name, "all", github_token)
    for pr in prs:
        username = pr["user"]["login"]
        if username in external_contributors:
            created_at = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            month_key = created_at.strftime("%Y-%m")
            external_contributors[username]["prs"] += 1
            external_contributors[username]["months"][month_key] = (
                external_contributors[username]["months"].get(month_key, 0) + 1
            )
    return external_contributors


def print_external_contributors(external_contributors):
    """Print external contributors and their monthly PR counts."""
    for username, data in external_contributors.items():
        print(f"Contributor: {username}")
        print(f'Total PRs: {data["prs"]}')
        print("Monthly PRs:")
        for month, count in data["months"].items():
            print(f"  {month}: {count}")
        print()


def convert_to_tsv(external_contributors):
    """Convert external contributors data to TSV format."""
    tsv_data = "Contributor\tTotal PRs\tMonth\tPRs\n"
    for username, data in external_contributors.items():
        for month, count in data["months"].items():
            tsv_data += f"{username}\t{data['prs']}\t{month}\t{count}\n"
    return tsv_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get external contributors")
    parser.add_argument("--repo-owner", help="Repository owner")
    parser.add_argument("--repo-name", help="Repository name")
    parser.add_argument("--github-token", help="GitHub token")
    parser.add_argument(
        "--filter-organizations", nargs="+", help="Organizations to filter out"
    )
    parser.add_argument(
        "--output-tsv", action="store_true", help="Output in TSV format"
    )
    args = parser.parse_args()
    repo_owner = args.repo_owner or os.environ.get("REPO_OWNER")
    repo_name = args.repo_name or os.environ.get("REPO_NAME")
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")
    filter_orgs = args.filter_organizations or os.environ.get("FILTER_ORGS")
    if not repo_owner or not repo_name or not github_token:
        print("Error: Repository owner, name, and GitHub token are required.")
        exit(1)
    if filter_orgs and isinstance(filter_orgs, str):
        filter_orgs = [filter_orgs]
    external_contributors = get_external_contributors(
        repo_owner, repo_name, filter_orgs or [], github_token
    )
    if args.output_tsv:
        tsv_data = convert_to_tsv(external_contributors)
        print(tsv_data)
    else:
        print(json.dumps(external_contributors, indent=4))
