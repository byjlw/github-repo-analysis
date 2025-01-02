import argparse
import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Set
import pandas as pd
import matplotlib.pyplot as plt
from github_api import GitHubAPI

# Constants
OUTPUT_DIR = "output"


def fetch_org_members(github: GitHubAPI, orgs: List[str]) -> Dict[str, Set[str]]:
    """Fetch members for each organization.
    
    Args:
        github: GitHubAPI instance
        orgs: List of organization names
        
    Returns:
        Dictionary mapping org names to sets of member logins
    """
    org_members = {}
    for org in orgs:
        members = github.fetch_org_members(org, include_details=False)
        org_members[org] = {member['login'] if isinstance(member, dict) else member for member in members}
    return org_members


def is_external_contributor(username: str, org_members: Dict[str, Set[str]], exclude_contributors: List[str]) -> bool:
    """Check if a contributor is external.
    
    Args:
        username: GitHub username to check
        org_members: Dictionary of org members from fetch_org_members
        exclude_contributors: List of contributors to exclude
        
    Returns:
        True if contributor is external, False otherwise
    """
    if username in exclude_contributors:
        return False
        
    for members in org_members.values():
        if username in members:
            return False
    return True


def fetch_contributor_data(
    github: GitHubAPI,
    repo_owner: str,
    repo_name: str,
    since: Optional[datetime] = None
) -> List[Dict]:
    """Fetch basic contributor data.
    
    Args:
        github: GitHubAPI instance
        repo_owner: Repository owner
        repo_name: Repository name
        since: Optional datetime to fetch data since
        
    Returns:
        List of contributors with basic data
    """
    return github.fetch_contributors(
        repo_owner,
        repo_name,
        since=since,
        include_details=False  # Skip detailed data to reduce API calls
    )


def fetch_pr_data(
    github: GitHubAPI,
    repo_owner: str,
    repo_name: str,
    since: Optional[datetime] = None
) -> List[Dict]:
    """Fetch pull request data.
    
    Args:
        github: GitHubAPI instance
        repo_owner: Repository owner
        repo_name: Repository name
        since: Optional datetime to fetch PRs since
        
    Returns:
        List of pull requests with basic data
    """
    return github.fetch_pull_requests(
        repo_owner,
        repo_name,
        state="all",
        since=since,
        include_details=False  # Skip PR details to reduce API calls
    )


def process_pr_data(prs: List[Dict], external_contributors: Dict) -> Dict:
    """Process PR data for external contributors.
    
    Args:
        prs: List of pull requests
        external_contributors: Dictionary of external contributors
        
    Returns:
        Updated external contributors dictionary with PR counts
    """
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


def get_external_contributors(
    repo_owner: str,
    repo_name: str,
    filter_orgs: list,
    exclude_contributors: list,
    github_token: str,
    since: Optional[datetime] = None,
    use_cache_only: bool = False
) -> Dict:
    """Fetch external contributors and their monthly PR counts.
    
    Args:
        repo_owner: Repository owner
        repo_name: Repository name
        filter_orgs: List of organizations to filter out
        exclude_contributors: List of contributors to exclude
        github_token: GitHub API token
        since: Optional datetime to fetch data since
        use_cache_only: If True, only use cached data
        
    Returns:
        Dictionary of external contributors and their PR counts
    """
    github = GitHubAPI(github_token, use_cache=True, use_cache_only=use_cache_only)
    
    # Get org members first to filter contributors
    org_members = fetch_org_members(github, filter_orgs)
    
    # Get contributors and filter external ones
    contributors = fetch_contributor_data(github, repo_owner, repo_name, since)
    
    # Initialize external contributors
    external_contributors = {}
    for contributor in contributors:
        username = contributor["login"]
        if is_external_contributor(username, org_members, exclude_contributors):
            external_contributors[username] = {
                "prs": 0,
                "months": {},
                "contributions": contributor.get('contributions', 0)
            }
    
    if not external_contributors:
        return {}
    
    # Get and process PR data
    prs = fetch_pr_data(github, repo_owner, repo_name, since)
    external_contributors = process_pr_data(prs, external_contributors)
    
    return external_contributors


def print_external_contributors(external_contributors: Dict) -> None:
    """Print external contributors and their monthly PR counts."""
    for username, data in external_contributors.items():
        print(f"Contributor: {username}")
        print(f'Total PRs: {data["prs"]}')
        print(f'Total Contributions: {data.get("contributions", "unknown")}')
        print("Monthly PRs:")
        for month, count in sorted(data["months"].items()):
            print(f"  {month}: {count}")
        print()


def convert_to_tsv(external_contributors: Dict) -> str:
    """Convert external contributors data to TSV format."""
    tsv_data = "Contributor\tTotal PRs\tTotal Contributions\tMonth\tPRs\n"
    for username, data in external_contributors.items():
        contributions = data.get("contributions", "unknown")
        for month, count in data["months"].items():
            tsv_data += f"{username}\t{data['prs']}\t{contributions}\t{month}\t{count}\n"
    return tsv_data

def plot_contributor_stats(external_contributors: Dict) -> None:
    """Create a chart showing contributions and contributors per month."""
    if not external_contributors:
        print("No data to plot")
        return

    # Create monthly aggregated data
    monthly_data = {}
    for username, data in external_contributors.items():
        for month, prs in data["months"].items():
            if month not in monthly_data:
                monthly_data[month] = {
                    "contributions": 0,
                    "contributors": set()
                }
            monthly_data[month]["contributions"] += prs
            monthly_data[month]["contributors"].add(username)

    # Convert to DataFrame
    df = pd.DataFrame([
        {
            "month": month,
            "contributions": stats["contributions"],  # Using the monthly aggregated contributions
            "contributors": len(stats["contributors"])
        }
        for month, stats in monthly_data.items()
    ])
    df["month"] = pd.to_datetime(df["month"] + "-01")
    df = df.sort_values("month")

    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot contributions on primary y-axis
    ax1.plot(df["month"], df["contributions"], label="Contributions", color="blue", marker="o")
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Number of Contributions", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")

    # Create secondary y-axis and plot contributors
    ax2 = ax1.twinx()
    ax2.plot(df["month"], df["contributors"], label="Contributors", color="red", marker="x")
    ax2.set_ylabel("Number of Contributors", color="red")
    ax2.tick_params(axis="y", labelcolor="red")

    # Add title and grid
    plt.title("External Contributor Activity by Month")
    ax1.grid(True)

    # Add legends for both lines
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    output_path = os.path.join(OUTPUT_DIR, "contributor_trends.png")
    plt.savefig(output_path)
    plt.close()
    print(f"Chart has been saved as {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get external contributors")
    parser.add_argument("--repo-owner", help="Repository owner")
    parser.add_argument("--repo-name", help="Repository name")
    parser.add_argument("--github-token", help="GitHub token")
    parser.add_argument(
        "--filter-organizations", nargs="+", help="Organizations to filter out"
    )
    parser.add_argument(
        "--exclude-contributors", nargs="+", help="Contributors to exclude"
    )
    parser.add_argument("--since", help="Date to start from (YYYY-MM-DD)")
    parser.add_argument(
        "--output-tsv", action="store_true", help="Output in TSV format"
    )
    parser.add_argument(
        "--use-cache-only", action="store_true", help="Only use cached data, no API calls"
    )
    args = parser.parse_args()
    repo_owner = args.repo_owner or os.environ.get("REPO_OWNER")
    repo_name = args.repo_name or os.environ.get("REPO_NAME")
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")
    filter_orgs = args.filter_organizations or os.environ.get("FILTER_ORGS")
    exclude_contributors = args.exclude_contributors or os.environ.get(
        "EXCLUDE_CONTRIBUTORS"
    )
    since_date = args.since
    if not repo_owner or not repo_name or not github_token:
        print("Error: Repository owner, name, and GitHub token are required.")
        exit(1)
    if filter_orgs and isinstance(filter_orgs, str):
        filter_orgs = [filter_orgs]
    if exclude_contributors and isinstance(exclude_contributors, str):
        exclude_contributors = [exclude_contributors]
    if since_date:
        since_date = datetime.strptime(since_date, "%Y-%m-%d")
    external_contributors = get_external_contributors(
        repo_owner,
        repo_name,
        filter_orgs or [],
        exclude_contributors or [],
        github_token,
        since=since_date,
        use_cache_only=args.use_cache_only
    )
    # Generate chart regardless of output format
    plot_contributor_stats(external_contributors)
    
    if args.output_tsv:
        tsv_data = convert_to_tsv(external_contributors)
        print(tsv_data)
    else:
        print(json.dumps(external_contributors, indent=4))
