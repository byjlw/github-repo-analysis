import pandas as pd
import matplotlib.pyplot as plt
import datetime
from typing import Dict, List, Optional, Tuple

from chart_utils import save_chart

def count_open_issues(df_issues: pd.DataFrame, date: datetime.date, label: Optional[str] = None) -> int:
    """Count open issues for a specific date and optional label.
    
    Args:
        df_issues: DataFrame containing issue data
        date: Date to count open issues for
        label: Optional label to filter issues by
        
    Returns:
        Number of open issues for the specified date and label
    """
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

def setup_chart(figsize: Tuple[int, int] = (12, 6)) -> Tuple[plt.Figure, plt.Axes]:
    """Set up a new chart with standard formatting.
    
    Args:
        figsize: Size of the figure (width, height)
        
    Returns:
        Figure and axes objects
    """
    fig, ax = plt.subplots(figsize=figsize)
    ax.grid(True)
    return fig, ax

def setup_dual_axis_chart(figsize: Tuple[int, int] = (12, 6)) -> Tuple[plt.Figure, plt.Axes, plt.Axes]:
    """Set up a chart with dual y-axes.
    
    Args:
        figsize: Size of the figure (width, height)
        
    Returns:
        Figure, primary axes, and secondary axes objects
    """
    fig, ax1 = plt.subplots(figsize=figsize)
    ax2 = ax1.twinx()
    ax1.grid(True)
    return fig, ax1, ax2
