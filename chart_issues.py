import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime
from typing import Optional

from chart_utils import get_date_range, save_chart, MAX_LABELS
from chart_base import count_open_issues, setup_chart, setup_dual_axis_chart

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

    fig, ax = setup_chart(figsize=(12, 8))
    
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
    fig, ax1, ax2 = setup_dual_axis_chart()
    
    # Calculate metrics
    open_issues = [count_open_issues(df_issues, date.date()) for date in date_range]
    closed_per_day = [len(df_issues[df_issues['closed_at'] == date.date()]) for date in date_range]

    # Plot open issues on primary y-axis
    ax1.plot(date_range, open_issues, label='Open Issues', color='red', marker='o')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Number of Open Issues', color='red')
    ax1.tick_params(axis='y', labelcolor='red')
    
    # Plot closed issues on secondary y-axis
    ax2.plot(date_range, closed_per_day, label='Closed Issues per Day', color='blue', marker='x')
    ax2.set_ylabel('Number of Issues Closed per Day', color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')
    
    # Add title and grid
    plt.title(f"Issue Trends (Excluding Pull Requests)\nCurrent Open Issues: {current_open}")
    
    # Add legends for both lines
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    save_chart(output_filename)
