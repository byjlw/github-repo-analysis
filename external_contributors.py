import argparse
import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Set, Tuple
import pandas as pd
from chart import plot_contributor_trends, plot_open_prs_trend
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


def classify_contributor(
    username: str, 
    org_members: Dict[str, Set[str]], 
    internal_contributors: List[str],
    external_contributors: List[str]
) -> str:
    """Classify a contributor as internal, external, or unknown.
    
    Args:
        username: GitHub username to check
        org_members: Dictionary of org members from fetch_org_members
        internal_contributors: List of contributors to explicitly mark as internal
        external_contributors: List of contributors to explicitly mark as external
        
    Returns:
        "internal", "external", or "unknown" based on classification rules
    """
    # If both internal and external lists are provided, contributors not in either list are "unknown"
    both_lists_provided = internal_contributors and external_contributors
    
    # Priority 1: Check if explicitly marked as external
    if username in external_contributors:
        return "external"
        
    # Priority 2: Check if explicitly marked as internal
    if username in internal_contributors:
        return "internal"
        
    # Priority 3: Check organization membership
    for members in org_members.values():
        if username in members:
            return "internal"
    
    # Priority 4: If both lists are provided and contributor is not in either, mark as unknown
    if both_lists_provided:
        return "unknown"
            
    # Default: external
    return "external"


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


def process_pr_data(prs: List[Dict], contributors: Dict) -> Tuple[Dict, Dict[str, Dict[str, int]]]:
    """Process PR data for contributors.
    
    Args:
        prs: List of pull requests
        contributors: Dictionary of contributors
        
    Returns:
        Tuple containing:
        - Updated contributors dictionary with PR counts
        - Dictionary mapping dates to number of open PRs by contributor type
    """
    # Track open PRs over time by contributor type
    open_prs_by_date = {
        "internal": {},
        "external": {},
        "unknown": {}
    }
    current_date = datetime.now().date()
    
    # Process each PR
    for pr in prs:
        username = pr["user"]["login"]
        if username not in contributors:
            continue
            
        contributor_type = contributors[username]["type"]
        
        # Update monthly PR counts
        created_at = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        month_key = created_at.strftime("%Y-%m")
        contributors[username]["prs"] += 1
        contributors[username]["months"][month_key] = (
            contributors[username]["months"].get(month_key, 0) + 1
        )
        
        # Track open PRs over time
        created_date = created_at.date()
        closed_date = None
        if pr["closed_at"]:
            closed_date = datetime.strptime(pr["closed_at"], "%Y-%m-%dT%H:%M:%SZ").date()
        
        # Initialize dates if needed
        date_range = pd.date_range(start=created_date, end=current_date)
        for date in date_range:
            date_str = date.strftime("%Y-%m-%d")
            
            # Initialize counters if needed
            if date_str not in open_prs_by_date[contributor_type]:
                open_prs_by_date[contributor_type][date_str] = 0
            
            # PR is open on this date if it's created and not yet closed
            if closed_date is None or date.date() < closed_date:
                open_prs_by_date[contributor_type][date_str] += 1
    
    return contributors, open_prs_by_date


def get_contributors(
    repo_owner: str,
    repo_name: str,
    filter_orgs: list,
    internal_contributors: list,
    external_contributors: list,
    github_token: str,
    since: Optional[datetime] = None,
    use_cache_only: bool = False
) -> Tuple[Dict, Dict[str, Dict[str, int]]]:
    """Fetch contributors and their monthly PR counts.
    
    Args:
        repo_owner: Repository owner
        repo_name: Repository name
        filter_orgs: List of organizations whose members are considered internal
        internal_contributors: List of contributors to explicitly mark as internal
        external_contributors: List of contributors to explicitly mark as external
        github_token: GitHub API token
        since: Optional datetime to fetch data since
        use_cache_only: If True, only use cached data
        
    Returns:
        Tuple containing:
        - Dictionary of contributors and their PR counts
        - Dictionary mapping dates to number of open PRs by contributor type
    """
    github = GitHubAPI(github_token, use_cache=True, use_cache_only=use_cache_only)
    
    # Get org members first to classify contributors
    org_members = fetch_org_members(github, filter_orgs)
    
    # Get all contributors
    all_contributors = fetch_contributor_data(github, repo_owner, repo_name, since)
    
    # Initialize contributors dictionary
    contributors = {}
    for contributor in all_contributors:
        username = contributor["login"]
        contributor_type = classify_contributor(username, org_members, internal_contributors, external_contributors)
        contributors[username] = {
            "type": contributor_type,
            "prs": 0,
            "months": {},
            "contributions": contributor.get('contributions', 0)
        }
    
    if not contributors:
        return {}, {"internal": {}, "external": {}}
    
    # Get and process PR data
    prs = fetch_pr_data(github, repo_owner, repo_name, since)
    contributors, open_prs_by_date = process_pr_data(prs, contributors)
    
    return contributors, open_prs_by_date


def print_contributors(contributors: Dict, show_internal: bool = False, show_external: bool = True, show_unknown: bool = True) -> None:
    """Print contributors and their monthly PR counts.
    
    Args:
        contributors: Dictionary of contributors
        show_internal: Whether to show internal contributors
        show_external: Whether to show external contributors
        show_unknown: Whether to show unknown contributors
    """
    for username, data in contributors.items():
        # Skip based on contributor type and show flags
        if (data["type"] == "internal" and not show_internal) or \
           (data["type"] == "external" and not show_external) or \
           (data["type"] == "unknown" and not show_unknown):
            continue
            
        print(f"Contributor: {username} ({data['type']})")
        print(f'Total PRs: {data["prs"]}')
        print(f'Total Contributions: {data.get("contributions", "unknown")}')
        print("Monthly PRs:")
        for month, count in sorted(data["months"].items()):
            print(f"  {month}: {count}")
        print()


def convert_to_tsv(contributors: Dict, show_internal: bool = False, show_external: bool = True, show_unknown: bool = True) -> str:
    """Convert contributors data to TSV format.
    
    Args:
        contributors: Dictionary of contributors
        show_internal: Whether to show internal contributors
        show_external: Whether to show external contributors
        show_unknown: Whether to show unknown contributors
    """
    tsv_data = "Contributor\tType\tTotal PRs\tTotal Contributions\tMonth\tPRs\n"
    for username, data in contributors.items():
        # Skip based on contributor type and show flags
        if (data["type"] == "internal" and not show_internal) or \
           (data["type"] == "external" and not show_external) or \
           (data["type"] == "unknown" and not show_unknown):
            continue
            
        contributions = data.get("contributions", "unknown")
        for month, count in data["months"].items():
            tsv_data += f"{username}\t{data['type']}\t{data['prs']}\t{contributions}\t{month}\t{count}\n"
    return tsv_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze GitHub repository contributors")
    parser.add_argument("--repo-owner", help="Repository owner")
    parser.add_argument("--repo-name", help="Repository name")
    parser.add_argument("--github-token", help="GitHub token")
    parser.add_argument(
        "--filter-organizations", nargs="+", help="Organizations whose members are considered internal"
    )
    parser.add_argument(
        "--internal-contributors", nargs="+", help="Contributors to explicitly mark as internal"
    )
    parser.add_argument(
        "--external-contributors", nargs="+", help="Contributors to explicitly mark as external"
    )
    parser.add_argument(
        "--show-internal", action="store_true", help="Show internal contributors in output and charts"
    )
    parser.add_argument(
        "--show-external", action="store_true", default=True, help="Show external contributors in output and charts"
    )
    parser.add_argument(
        "--show-unknown", action="store_true", default=True, help="Show unknown contributors in output and charts"
    )
    parser.add_argument("--since", help="Date to start from (YYYY-MM-DD)")
    parser.add_argument(
        "--output-tsv", action="store_true", help="Output in TSV format"
    )
    parser.add_argument(
        "--use-cache-only", action="store_true", help="Only use cached data"
    )
    parser.add_argument("--start-date", help="Start date for charts (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date for charts (YYYY-MM-DD)")
    
    # For backward compatibility
    parser.add_argument(
        "--exclude-contributors", nargs="+", help="[DEPRECATED] Use --internal-contributors instead"
    )
    
    args = parser.parse_args()
    repo_owner = args.repo_owner or os.environ.get("REPO_OWNER")
    repo_name = args.repo_name or os.environ.get("REPO_NAME")
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")
    filter_orgs = args.filter_organizations or os.environ.get("FILTER_ORGS")
    
    # Handle backward compatibility for exclude-contributors
    internal_contributors = args.internal_contributors
    if args.exclude_contributors and not internal_contributors:
        print("Warning: --exclude-contributors is deprecated. Use --internal-contributors instead.")
        internal_contributors = args.exclude_contributors
    
    internal_contributors = internal_contributors or os.environ.get("INTERNAL_CONTRIBUTORS")
    external_contributors = args.external_contributors or os.environ.get("EXTERNAL_CONTRIBUTORS")
    
    since_date = args.since
    if not repo_owner or not repo_name or not github_token:
        print("Error: Repository owner, name, and GitHub token are required.")
        exit(1)
    if filter_orgs and isinstance(filter_orgs, str):
        filter_orgs = [filter_orgs]
    if internal_contributors and isinstance(internal_contributors, str):
        internal_contributors = [internal_contributors]
    if external_contributors and isinstance(external_contributors, str):
        external_contributors = [external_contributors]
    if since_date:
        since_date = datetime.strptime(since_date, "%Y-%m-%d")
        
    contributors, open_prs_by_date = get_contributors(
        repo_owner,
        repo_name,
        filter_orgs or [],
        internal_contributors or [],
        external_contributors or [],
        github_token,
        since=since_date,
        use_cache_only=args.use_cache_only
    )
    
    # Parse date range for charts if provided
    start_date = None
    end_date = None
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()

    # Generate charts with date range and contributor filtering
    plot_contributor_trends(
        contributors, 
        show_internal=args.show_internal,
        show_external=args.show_external,
        show_unknown=args.show_unknown,
        start_date=start_date, 
        end_date=end_date
    )
    
    plot_open_prs_trend(
        open_prs_by_date, 
        show_internal=args.show_internal,
        show_external=args.show_external,
        show_unknown=args.show_unknown,
        start_date=start_date, 
        end_date=end_date
    )
    
    # Add open PRs data to the output
    output_data = {
        "contributors": contributors,
        "open_prs_by_date": open_prs_by_date
    }
    
    if args.output_tsv:
        tsv_data = convert_to_tsv(
            contributors, 
            show_internal=args.show_internal, 
            show_external=args.show_external,
            show_unknown=args.show_unknown
        )
        print(tsv_data)
    else:
        # Filter contributors for output based on show flags
        filtered_contributors = {}
        for username, data in contributors.items():
            if (data["type"] == "internal" and args.show_internal) or \
               (data["type"] == "external" and args.show_external) or \
               (data["type"] == "unknown" and args.show_unknown):
                filtered_contributors[username] = data
                
        # Filter open PRs data for output
        filtered_open_prs = {}
        if args.show_internal:
            for date, count in open_prs_by_date.get("internal", {}).items():
                if date not in filtered_open_prs:
                    filtered_open_prs[date] = 0
                filtered_open_prs[date] += count
                
        if args.show_external:
            for date, count in open_prs_by_date.get("external", {}).items():
                if date not in filtered_open_prs:
                    filtered_open_prs[date] = 0
                filtered_open_prs[date] += count
                
        if args.show_unknown:
            for date, count in open_prs_by_date.get("unknown", {}).items():
                if date not in filtered_open_prs:
                    filtered_open_prs[date] = 0
                filtered_open_prs[date] += count
        
        output_data = {
            "contributors": filtered_contributors,
            "open_prs_by_date": filtered_open_prs
        }
        
        print(json.dumps(output_data, indent=4))
