import os
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from typing import Optional

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
