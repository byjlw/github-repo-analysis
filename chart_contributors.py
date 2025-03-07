import pandas as pd
import matplotlib.pyplot as plt
import datetime
from typing import Dict, Optional, Set

from chart_utils import save_chart
from chart_base import setup_chart, setup_dual_axis_chart

def plot_contributor_trends(contributors: Dict[str, Dict[str, dict]], output_filename: str = "contributor_trends.png",
                          show_internal: bool = False, show_external: bool = True, show_unknown: bool = True,
                          start_date: Optional[datetime.date] = None, end_date: Optional[datetime.date] = None) -> None:
    """Create a chart showing contributions and contributors per month.
    
    Args:
        contributors: Dictionary containing contributor data
        output_filename: Name of the output file
        show_internal: Whether to show internal contributors
        show_external: Whether to show external contributors
        show_unknown: Whether to show unknown contributors
        start_date: Optional start date to constrain chart range
        end_date: Optional end date to constrain chart range
    
    Example input:
    {
        "user1": {
            "type": "external",
            "prs": 5,
            "months": {
                "2023-01": 2,
                "2023-02": 3
            },
            "contributions": 10
        }
    }
    """
    if not contributors:
        print("No data to plot")
        return

    # Create monthly aggregated data by contributor type
    monthly_data = {
        "internal": {},
        "external": {},
        "unknown": {}
    }
    
    for username, data in contributors.items():
        contributor_type = data["type"]
        
        # Skip based on show flags
        if (contributor_type == "internal" and not show_internal) or \
           (contributor_type == "external" and not show_external):
            continue
            
        for month, prs in data["months"].items():
            month_date = datetime.datetime.strptime(month + "-01", "%Y-%m-%d").date()
            if (start_date and month_date < start_date) or (end_date and month_date > end_date):
                continue
                
            if month not in monthly_data[contributor_type]:
                monthly_data[contributor_type][month] = {"contributions": 0, "contributors": set()}
                
            monthly_data[contributor_type][month]["contributions"] += prs
            monthly_data[contributor_type][month]["contributors"].add(username)

    # Check if we have data to plot
    has_internal_data = bool(monthly_data["internal"]) and show_internal
    has_external_data = bool(monthly_data["external"]) and show_external
    has_unknown_data = bool(monthly_data["unknown"]) and show_unknown
    
    if not has_internal_data and not has_external_data and not has_unknown_data:
        print("No data in selected date range")
        return

    # Create figure with two y-axes
    fig, ax1, ax2 = setup_dual_axis_chart()
    
    # Colors for different contributor types
    colors = {
        "internal": {
            "contributions": "green",
            "contributors": "darkgreen"
        },
        "external": {
            "contributions": "blue",
            "contributors": "red"
        },
        "unknown": {
            "contributions": "orange",
            "contributors": "darkorange"
        }
    }
    
    # Plot data for each contributor type
    all_months = set()
    for contrib_type in ["internal", "external", "unknown"]:
        if (contrib_type == "internal" and not show_internal) or \
           (contrib_type == "external" and not show_external) or \
           (contrib_type == "unknown" and not show_unknown) or \
           not monthly_data[contrib_type]:
            continue
            
        # Collect all months for x-axis
        all_months.update(monthly_data[contrib_type].keys())
    
    if not all_months:
        print("No data to plot after filtering")
        return
        
    # Create a complete date range for all data points
    all_months = sorted(all_months)
    date_range = pd.date_range(
        start=datetime.datetime.strptime(min(all_months) + "-01", "%Y-%m-%d"),
        end=datetime.datetime.strptime(max(all_months) + "-01", "%Y-%m-%d"),
        freq='MS'
    )
    
    # Plot contributions and contributors for each type
    legend_handles = []
    legend_labels = []
    
    for contrib_type in ["internal", "external", "unknown"]:
        if (contrib_type == "internal" and not show_internal) or \
           (contrib_type == "external" and not show_external) or \
           (contrib_type == "unknown" and not show_unknown) or \
           not monthly_data[contrib_type]:
            continue
            
        # Convert to DataFrame for easier plotting
        df = pd.DataFrame([
            {
                "month": pd.to_datetime(month + "-01"),
                "contributions": stats["contributions"],
                "contributors": len(stats["contributors"])
            }
            for month, stats in monthly_data[contrib_type].items()
        ]).sort_values("month")
        
        # Ensure we have data for all months in the range
        full_date_df = pd.DataFrame({"month": date_range})
        df = pd.merge(full_date_df, df, on="month", how="left").fillna(0)
        
        # Plot contributions on primary y-axis
        contrib_line = ax1.plot(
            df["month"], 
            df["contributions"], 
            label=f"{contrib_type.capitalize()} Contributions", 
            color=colors[contrib_type]["contributions"], 
            marker="o",
            linestyle="-" if contrib_type == "external" else "--"
        )[0]
        legend_handles.append(contrib_line)
        legend_labels.append(f"{contrib_type.capitalize()} Contributions")
        
        # Plot contributors on secondary y-axis
        contrib_count_line = ax2.plot(
            df["month"], 
            df["contributors"], 
            label=f"{contrib_type.capitalize()} Contributors", 
            color=colors[contrib_type]["contributors"], 
            marker="x",
            linestyle="-" if contrib_type == "external" else "--"
        )[0]
        legend_handles.append(contrib_count_line)
        legend_labels.append(f"{contrib_type.capitalize()} Contributors")
    
    # Set labels and title
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Number of Contributions")
    ax2.set_ylabel("Number of Contributors")
    
    # Determine title based on what's being shown
    title_parts = []
    if show_internal:
        title_parts.append("Internal")
    if show_external:
        title_parts.append("External")
    if show_unknown:
        title_parts.append("Unknown")
        
    if len(title_parts) > 0:
        title = f"{' and '.join(title_parts)} Contributor Activity by Month"
    else:
        title = "Contributor Activity by Month"
        
    plt.title(title)
    
    # Add legend
    ax1.legend(legend_handles, legend_labels, loc="upper left")
    
    save_chart(output_filename)

def plot_open_prs_trend(open_prs_data: Dict[str, Dict[str, int]], output_filename: str = "open_prs_trend.png",
                       show_internal: bool = False, show_external: bool = True, show_unknown: bool = True,
                       start_date: Optional[datetime.date] = None, end_date: Optional[datetime.date] = None) -> None:
    """Create a chart showing the number of open PRs from contributors over time.
    
    Args:
        open_prs_data: Dictionary mapping contributor types to dates to number of open PRs
        output_filename: Name of the output file
        show_internal: Whether to show internal contributors
        show_external: Whether to show external contributors
        show_unknown: Whether to show unknown contributors
        start_date: Optional start date to constrain chart range
        end_date: Optional end date to constrain chart range
    
    Example input:
    {
        "internal": {
            "2023-01-01": 3,
            "2023-01-02": 4
        },
        "external": {
            "2023-01-01": 5,
            "2023-01-02": 6
        },
        "unknown": {
            "2023-01-01": 2,
            "2023-01-02": 3
        }
    }
    """
    if not open_prs_data:
        print("No data to plot")
        return

    # Check if we have data to plot after filtering
    has_internal_data = "internal" in open_prs_data and bool(open_prs_data["internal"]) and show_internal
    has_external_data = "external" in open_prs_data and bool(open_prs_data["external"]) and show_external
    has_unknown_data = "unknown" in open_prs_data and bool(open_prs_data["unknown"]) and show_unknown
    
    if not has_internal_data and not has_external_data and not has_unknown_data:
        print("No data to plot after filtering")
        return
    
    # Colors for different contributor types
    colors = {
        "internal": "green",
        "external": "purple",
        "unknown": "orange"
    }
    
    # Get all dates across all contributor types
    all_dates = set()
    for contrib_type, dates_data in open_prs_data.items():
        if (contrib_type == "internal" and not show_internal) or \
           (contrib_type == "external" and not show_external) or \
           (contrib_type == "unknown" and not show_unknown):
            continue
        all_dates.update(dates_data.keys())
    
    # Convert to datetime objects for comparison
    date_objects = [datetime.datetime.strptime(date, "%Y-%m-%d").date() for date in all_dates]
    
    if not date_objects:
        print("No data in selected date range")
        return
        
    min_date = min(date_objects)
    max_date = max(date_objects)
    
    # Apply date range constraints if provided
    if start_date:
        min_date = max(min_date, start_date)
    if end_date:
        max_date = min(max_date, end_date)
    
    # Create a complete date range
    date_range = pd.date_range(start=min_date, end=max_date)
    
    fig, ax = setup_chart()
    legend_handles = []
    legend_labels = []
    
    # Plot data for each contributor type
    for contrib_type in ["internal", "external", "unknown"]:
        if (contrib_type == "internal" and not show_internal) or \
           (contrib_type == "external" and not show_external) or \
           (contrib_type == "unknown" and not show_unknown) or \
           contrib_type not in open_prs_data or not open_prs_data[contrib_type]:
            continue
            
        # Filter dates based on date range
        filtered_data = {
            date: count for date, count in open_prs_data[contrib_type].items()
            if (not start_date or datetime.datetime.strptime(date, "%Y-%m-%d").date() >= start_date) and
               (not end_date or datetime.datetime.strptime(date, "%Y-%m-%d").date() <= max_date)
        }
        
        if not filtered_data:
            continue
            
        # Convert to DataFrame for easier plotting
        df = pd.DataFrame([
            {"date": datetime.datetime.strptime(date, "%Y-%m-%d"), "open_prs": count}
            for date, count in filtered_data.items()
        ]).sort_values("date")
        
        # Ensure we have data for all dates in the range
        full_date_df = pd.DataFrame({"date": date_range})
        df = pd.merge(full_date_df, df, on="date", how="left").fillna(0)
        
        # Plot the data
        line = ax.plot(
            df["date"], 
            df["open_prs"], 
            label=f"{contrib_type.capitalize()} Open PRs", 
            color=colors[contrib_type], 
            marker="o",
            linestyle="-" if contrib_type == "external" else ("--" if contrib_type == "internal" else ":")
        )[0]
        
        legend_handles.append(line)
        legend_labels.append(f"{contrib_type.capitalize()} Open PRs")
    
    # Determine title based on what's being shown
    title_parts = []
    if show_internal:
        title_parts.append("Internal")
    if show_external:
        title_parts.append("External")
    if show_unknown:
        title_parts.append("Unknown")
        
    if len(title_parts) > 1:
        title = "Open Pull Requests by Contributor Type"
    elif len(title_parts) == 1:
        title = f"Open Pull Requests from {title_parts[0]} Contributors"
    else:
        title = "Open Pull Requests"
    
    # Add title and labels
    plt.title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Open PRs")
    ax.legend(legend_handles, legend_labels, loc="upper left")

    save_chart(output_filename)
