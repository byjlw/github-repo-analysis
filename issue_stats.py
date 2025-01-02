import pandas as pd
import matplotlib.pyplot as plt
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

def plot_issues(df_issues):
    if df_issues.empty:
        logging.error("DataFrame is empty. No data to plot.")
        return

    # Convert dates to datetime for proper comparison
    start_date = min(df_issues['created_at'])
    end_date = datetime.datetime.now().date()
    date_range = pd.date_range(start=start_date, end=end_date)
    
    # Calculate open issues for each date
    open_issues = []
    closed_per_day = []
    
    for date in date_range:
        date = date.date()
        # Count open issues (total - closed)
        open_count = len(df_issues[
            (df_issues['created_at'] <= date) & 
            (
                ((df_issues['state'] == 'open') & (df_issues['created_at'] <= date)) |
                ((df_issues['state'] == 'closed') & (df_issues['closed_at'] > date))
            )
        ])
        open_issues.append(open_count)
        
        # Count issues closed on this specific date
        closed_count = len(df_issues[df_issues['closed_at'] == date])
        closed_per_day.append(closed_count)

    # Print current open issues count for verification
    current_open = len(df_issues[df_issues['state'] == 'open'])
    logging.info(f"Current number of open issues: {current_open}")

    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot open issues on primary y-axis
    ax1.plot(date_range, open_issues, label='Open Issues', color='red', marker='o')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Number of Open Issues', color='red')
    ax1.tick_params(axis='y', labelcolor='red')
    
    # Create secondary y-axis and plot closed issues
    ax2 = ax1.twinx()
    ax2.plot(date_range, closed_per_day, label='Closed Issues per Day', color='blue', marker='x')
    ax2.set_ylabel('Number of Issues Closed per Day', color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')
    
    # Add title and grid
    plt.title(f"Issue Trends (Excluding Pull Requests)\nCurrent Open Issues: {current_open}")
    ax1.grid(True)
    
    # Add legends for both lines
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    output_path = os.path.join(OUTPUT_DIR, 'issue_trends.png')
    plt.savefig(output_path)
    plt.show()
    logging.info(f"Chart has been saved as {output_path}")

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
        plot_issues(df_issues)
    else:
        logging.info("No issues found in cache or API.")
