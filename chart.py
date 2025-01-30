import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional, Tuple
import datetime

# Constants
OUTPUT_DIR = "output"
MAX_LABELS = 14  # Maximum number of labels to show in label trends chart (excluding unlabeled)

def ensure_output_dir():
    """Ensure output directory exists."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def save_chart(output_filename: str):
    """Save the current chart and clean up."""
    ensure_output_dir()
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"Chart has been saved as {output_path}")

def get_date_range(df: pd.DataFrame, date_col: str = 'created_at', start: Optional[datetime.date] = None, end: Optional[datetime.date] = None) -> pd.DatetimeIndex:
    """Get date range from dataframe, optionally constrained by start/end dates.
    
    Args:
        df: DataFrame containing date column
        date_col: Name of date column
        start: Optional start date to constrain range
        end: Optional end date to constrain range
    """
    min_date = min(df[date_col])
    max_date = max(df[date_col])  # Use max date from data instead of current date
    
    if start:
        min_date = max(min_date, start)
    if end:
        max_date = min(max_date, end)
        
    return pd.date_range(start=min_date, end=max_date)

def count_open_issues(df_issues: pd.DataFrame, date: datetime.date, label: Optional[str] = None) -> int:
    """Count open issues for a specific date and optional label."""
    mask = (df_issues['created_at'] <= date) & (
        ((df_issues['state'] == 'open') & (df_issues['created_at'] <= date)) |
        ((df_issues['state'] == 'closed') & (df_issues['closed_at'] > date))
    )
    
    if label is not None:
        if label == 'no_labels':
            mask &= df_issues['has_no_labels']
        else:
            mask &= df_issues['labels'].apply(lambda x: label in x)
    
    return len(df_issues[mask])

def plot_contributor_trends(external_contributors: Dict[str, Dict[str, dict]], output_filename: str = "contributor_trends.png",
                          start_date: Optional[datetime.date] = None, end_date: Optional[datetime.date] = None) -> None:
    """Create a chart showing contributions and contributors per month.
    
    Args:
        external_contributors: Dictionary containing contributor data
        output_filename: Name of the output file
        start_date: Optional start date to constrain chart range
        end_date: Optional end date to constrain chart range
    
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
            month_date = datetime.datetime.strptime(month + "-01", "%Y-%m-%d").date()
            if (start_date and month_date < start_date) or (end_date and month_date > end_date):
                continue
            if month not in monthly_data:
                monthly_data[month] = {"contributions": 0, "contributors": set()}
            monthly_data[month]["contributions"] += prs
            monthly_data[month]["contributors"].add(username)

    if not monthly_data:
        print("No data in selected date range")
        return

    # Convert to DataFrame
    df = pd.DataFrame([
        {"month": month, "contributions": stats["contributions"], "contributors": len(stats["contributors"])}
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

    save_chart(output_filename)

def plot_issues_by_label(df_issues: pd.DataFrame, labels: list, output_filename: str = "issue_trends_by_label.png",
                        start_date: Optional[datetime.date] = None, end_date: Optional[datetime.date] = None) -> None:
    """Create a chart showing issue trends by label over time.
    
    Args:
        df_issues: DataFrame containing issue data
        labels: List of label names to plot
        output_filename: Name of the output file
        start_date: Optional start date to constrain chart range
        end_date: Optional end date to constrain chart range
    
    Example input DataFrame structure:
    | created_at | closed_at  | state  |
    |------------|------------|--------|
    | 2023-01-01 | 2023-02-01 | closed |
    | 2023-01-15 | None       | open   |
    | 2023-02-01 | 2023-02-15 | closed |
    """
    if df_issues.empty:
        print("No data to plot")
        return

    date_range = get_date_range(df_issues, start=start_date, end=end_date)
    if len(date_range) == 0:
        print("No data in selected date range")
        return

    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Set up logarithmic scale
    ax.set_yscale('log')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: '{:,.0f}'.format(x)))
    ax.yaxis.set_minor_formatter(plt.FuncFormatter(lambda x, _: '{:,.0f}'.format(x)))
    ax.yaxis.set_minor_locator(plt.LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=100))
    ax.grid(True, which='both', ls='-', alpha=0.2)

    # Calculate max issues for each label
    label_max_issues = {}
    for label in labels:
        max_count = max([count_open_issues(df_issues, date.date(), label) for date in date_range])
        label_max_issues[label] = max_count

    # Get top labels by max issues
    top_labels = sorted(label_max_issues.items(), key=lambda x: x[1], reverse=True)[:MAX_LABELS]
    top_label_names = [label for label, _ in top_labels]

    # Calculate and plot trends for top labels
    colors = plt.cm.rainbow(np.linspace(0, 1, len(top_label_names) + 1))
    legend_data = []

    for i, label in enumerate(top_label_names):
        open_issues = [count_open_issues(df_issues, date.date(), label) for date in date_range]
        line = ax.plot(date_range, open_issues, color=colors[i], marker='o', markersize=2)[0]
        legend_data.append((line, f"{label} ({open_issues[-1]})", open_issues[-1]))

    # Add unlabeled issues
    open_no_labels = [count_open_issues(df_issues, date.date(), 'no_labels') for date in date_range]
    if max(open_no_labels) > 0:
        line = ax.plot(date_range, open_no_labels, color=colors[-1], marker='o', markersize=2)[0]
        legend_data.append((line, f"No Labels ({open_no_labels[-1]})", open_no_labels[-1]))

    # Sort and create legend
    legend_data.sort(key=lambda x: x[2], reverse=True)
    ncol = min(4, len(legend_data))
    ax.legend(
        [x[0] for x in legend_data],
        [x[1] for x in legend_data],
        loc='upper center',
        bbox_to_anchor=(0.5, -0.15),
        fontsize='small',
        ncol=ncol
    )

    # Add title and labels
    plt.title("Open Issues by Label Over Time")
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of Open Issues (log scale)')

    save_chart(output_filename)

def plot_issue_trends(df_issues: pd.DataFrame, output_filename: str = "issue_trends.png",
                     start_date: Optional[datetime.date] = None, end_date: Optional[datetime.date] = None) -> None:
    """Create a chart showing issue trends over time.
    
    Args:
        df_issues: DataFrame containing issue data
        output_filename: Name of the output file
        start_date: Optional start date to constrain chart range
        end_date: Optional end date to constrain chart range
    
    Example input DataFrame structure:
    | created_at | closed_at  | state  |
    |------------|------------|--------|
    | 2023-01-01 | 2023-02-01 | closed |
    | 2023-01-15 | None       | open   |
    | 2023-02-01 | 2023-02-15 | closed |
    """
    if df_issues.empty:
        print("No data to plot")
        return

    date_range = get_date_range(df_issues, start=start_date, end=end_date)
    if len(date_range) == 0:
        print("No data in selected date range")
        return

    current_open = len(df_issues[df_issues['state'] == 'open'])
    
    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Calculate metrics
    open_issues = [count_open_issues(df_issues, date.date()) for date in date_range]
    closed_per_day = [len(df_issues[df_issues['closed_at'] == date.date()]) for date in date_range]

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
    
    save_chart(output_filename)

def plot_open_prs_trend(open_prs_data: Dict[str, int], output_filename: str = "open_prs_trend.png",
                       start_date: Optional[datetime.date] = None, end_date: Optional[datetime.date] = None) -> None:
    """Create a chart showing the number of open PRs from external contributors over time.
    
    Args:
        open_prs_data: Dictionary mapping dates to number of open PRs
        output_filename: Name of the output file
        start_date: Optional start date to constrain chart range
        end_date: Optional end date to constrain chart range
    
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

    # Convert dictionary dates to datetime objects for comparison
    dates = [datetime.datetime.strptime(date, "%Y-%m-%d").date() for date in open_prs_data.keys()]
    max_date = max(dates)
    
    df = pd.DataFrame([
        {"date": datetime.datetime.strptime(date, "%Y-%m-%d"), "open_prs": count}
        for date, count in open_prs_data.items()
        if (not start_date or datetime.datetime.strptime(date, "%Y-%m-%d").date() >= start_date) and
           (not end_date or datetime.datetime.strptime(date, "%Y-%m-%d").date() <= (end_date or max_date))
    ]).sort_values("date")

    if df.empty:
        print("No data in selected date range")
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df["date"], df["open_prs"], label="Open PRs", color="purple", marker="o")
    
    # Add title and labels
    plt.title("Open Pull Requests from External Contributors")
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Open PRs")
    ax.grid(True)
    ax.legend(loc="upper left")

    save_chart(output_filename)
