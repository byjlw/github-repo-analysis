import pandas as pd
from chart import plot_issue_trends
import json
import os
import sys
import logging
import datetime
from typing import Optional
from github_api import GitHubAPI

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
CACHE_DIR = ".cache"
OUTPUT_DIR = "output"

def save_cache(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def load_cache(path):
    with open(path, 'r') as f:
        return json.load(f)

def fetch_issues(repo: str, token: str, use_cache_only: bool = False, fetch_limit: Optional[int] = None) -> list:
    """Fetch issues from GitHub API with caching support.
    
    Args:
        repo: Repository in format 'owner/name'
        token: GitHub API token
        use_cache_only: If True, only use cached data
        fetch_limit: Optional maximum number of issues to fetch
        
    Returns:
        List of issues
    """
    github = GitHubAPI(token, use_cache=True, use_cache_only=use_cache_only)
    return github.fetch_issues(
        repo,
        limit=fetch_limit,
        use_cache_only=use_cache_only,
        include_details=True  # Always get full issue details
    )

def create_issues_df(issues):
    df = pd.DataFrame(issues)
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce').dt.date
    df['closed_at'] = pd.to_datetime(df['closed_at'], errors='coerce').dt.date
    # Add state column explicitly
    df['state'] = df['state'].astype(str)
    return df

if __name__ == "__main__":
    if len(sys.argv) < 3:
        logging.error("Usage: python script.py <github-repo> <personal-access-token> [fetch-limit] [--use-cache-only]")
        sys.exit(1)

    repo = sys.argv[1]
    token = sys.argv[2]
    fetch_limit = 1000  # Default fetch limit
    use_cache_only = False

    for arg in sys.argv[3:]:
        if arg.isdigit():
            fetch_limit = int(arg)
        elif arg == '--use-cache-only':
            use_cache_only = True

    issues = fetch_issues(repo, token, use_cache_only=use_cache_only, fetch_limit=fetch_limit)
    if issues:
        df_issues = create_issues_df(issues)
        plot_issue_trends(df_issues)
    else:
        logging.info("No issues found in cache or API.")
