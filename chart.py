import os
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Optional
import datetime

# Constants
OUTPUT_DIR = "output"

def ensure_output_dir():
    """Ensure output directory exists."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def plot_contributor_trends(external_contributors: Dict[str, Dict[str, dict]], output_filename: str = "contributor_trends.png") -> None:
    """Create a chart showing contributions and contributors per month.
    
    Args:
        external_contributors: Dictionary containing contributor data with the following structure:
            {
                "username1": {
                    "prs": int,  # Total number of PRs
                    "months": {
                        "YYYY-MM": int,  # Number of PRs for each month
                        ...
                    },
                    "contributions": int  # Total number of contributions
                },
                "username2": {
                    ...
                }
            }
        output_filename: Name of the output file
    
    Example input:
        {
            "user1": {
                "prs": 5,
                "months": {
                    "2023-01": 2,
                    "2023-02": 3
                },
                "contributions": 10
            }
        }
    """
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
            "contributions": stats["contributions"],
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

    ensure_output_dir()
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    plt.savefig(output_path)
    plt.close()
    print(f"Chart has been saved as {output_path}")

def plot_issue_trends(df_issues: pd.DataFrame, output_filename: str = "issue_trends.png") -> None:
    """Create a chart showing issue trends over time.
    
    Args:
        df_issues: DataFrame containing issue data with the following required columns:
            - created_at: datetime.date - When the issue was created
            - closed_at: datetime.date - When the issue was closed (None if still open)
            - state: str - Current state of the issue ('open' or 'closed')
        output_filename: Name of the output file
    
    Example DataFrame structure:
        | created_at | closed_at  | state  |
        |------------|------------|--------|
        | 2023-01-01 | 2023-02-01 | closed |
        | 2023-01-15 | None       | open   |
        | 2023-02-01 | 2023-02-15 | closed |
    """
    if df_issues.empty:
        print("No data to plot")
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

    # Get current open issues count
    current_open = len(df_issues[df_issues['state'] == 'open'])

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
    
    ensure_output_dir()
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    plt.savefig(output_path)
    plt.close()
    print(f"Chart has been saved as {output_path}")

def plot_open_prs_trend(open_prs_data: Dict[str, int], output_filename: str = "open_prs_trend.png") -> None:
    """Create a chart showing the number of open PRs from external contributors over time.
    
    Args:
        open_prs_data: Dictionary mapping dates to number of open PRs with structure:
            {
                "YYYY-MM-DD": int,  # Number of open PRs on this date
                ...
            }
        output_filename: Name of the output file
    
    Example input:
        {
            "2023-01-01": 5,
            "2023-01-02": 6,
            "2023-01-03": 4
        }
    """
    if not open_prs_data:
        print("No data to plot")
        return

    # Convert to DataFrame
    df = pd.DataFrame([
        {"date": datetime.datetime.strptime(date, "%Y-%m-%d"), "open_prs": count}
        for date, count in open_prs_data.items()
    ])
    df = df.sort_values("date")

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot open PRs
    ax.plot(df["date"], df["open_prs"], label="Open PRs", color="purple", marker="o")
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Open PRs")
    
    # Add title and grid
    plt.title("Open Pull Requests from External Contributors")
    ax.grid(True)
    ax.legend(loc="upper left")

    ensure_output_dir()
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    plt.savefig(output_path)
    plt.close()
    print(f"Chart has been saved as {output_path}")
