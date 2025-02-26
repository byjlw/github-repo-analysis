"""
Chart module for GitHub repository analysis.

This module provides visualization functions for GitHub repository data.
It's a thin wrapper around the specialized chart modules.
"""

# Re-export all chart functions from their respective modules
from chart_utils import get_date_range, save_chart, ensure_output_dir
from chart_base import count_open_issues, setup_chart, setup_dual_axis_chart
from chart_issues import plot_issues_by_label, plot_issue_trends
from chart_contributors import plot_contributor_trends, plot_open_prs_trend

# This allows other modules to import these functions from chart.py
# without having to change their import statements
__all__ = [
    'get_date_range',
    'save_chart',
    'ensure_output_dir',
    'count_open_issues',
    'setup_chart',
    'setup_dual_axis_chart',
    'plot_issues_by_label',
    'plot_issue_trends',
    'plot_contributor_trends',
    'plot_open_prs_trend'
]
