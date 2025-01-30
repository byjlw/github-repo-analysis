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
    df['created_at'] = pd.to_datetime(df['created_at'], format='%Y-%m-%dT%H:%M:%SZ', errors='coerce').dt.date
    df['closed_at'] = pd.to_datetime(df['closed_at'], format='%Y-%m-%dT%H:%M:%SZ', errors='coerce').dt.date
    # Add state column explicitly
    df['state'] = df['state'].astype(str)
    
    # Extract labels into a list
    df['labels'] = df['labels'].apply(lambda x: [label['name'] for label in x] if x else [])
    # Add a column for issues with no labels
    df['has_no_labels'] = df['labels'].apply(lambda x: len(x) == 0)
    
    return df

def plot_label_trends(df_issues, start_date=None, end_date=None):
    """Create a chart showing issue trends by label over time.
    
    Args:
        df_issues: DataFrame containing issue data
        start_date: Optional start date to constrain chart range
        end_date: Optional end date to constrain chart range
    """
    from chart import plot_issues_by_label
    
    # Get all unique labels
    all_labels = set()
    for labels in df_issues['labels']:
        all_labels.update(labels)
    
    plot_issues_by_label(df_issues, list(all_labels), start_date=start_date, end_date=end_date)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze GitHub repository issues")
    parser.add_argument("repo", help="Repository in format 'owner/name'")
    parser.add_argument("token", help="GitHub personal access token")
    parser.add_argument("--fetch-limit", type=int, default=1000, help="Maximum number of issues to fetch")
    parser.add_argument("--use-cache-only", action="store_true", help="Only use cached data")
    parser.add_argument("--start-date", help="Start date for charts (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date for charts (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    start_date = None
    end_date = None
    if args.start_date:
        start_date = datetime.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    if args.end_date:
        end_date = datetime.datetime.strptime(args.end_date, "%Y-%m-%d").date()

    issues = fetch_issues(args.repo, args.token, use_cache_only=args.use_cache_only, fetch_limit=args.fetch_limit)
    if issues:
        df_issues = create_issues_df(issues)
        # Generate both charts with date range
        plot_issue_trends(df_issues, start_date=start_date, end_date=end_date)
        plot_label_trends(df_issues, start_date=start_date, end_date=end_date)
    else:
        logging.info("No issues found in cache or API.")
