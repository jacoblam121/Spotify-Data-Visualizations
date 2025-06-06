"""
time_aggregation.py

Handles time-based aggregation of listening data for nightingale rose chart visualization.
Supports both monthly (for ≤12 months) and yearly (for >12 months) aggregation patterns.
"""

from __future__ import annotations

import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import calendar

__all__ = ["calculate_nightingale_time_data", "determine_aggregation_type"]


def determine_aggregation_type(start_date: pd.Timestamp, end_date: pd.Timestamp) -> str:
    """
    Determine whether to use monthly or yearly aggregation based on date range.
    
    Args:
        start_date: Start of the time range
        end_date: End of the time range
        
    Returns:
        'monthly' if range is ≤12 months, 'yearly' if >12 months
    """
    # Calculate months difference
    months_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    
    # Add 1 to include both start and end months
    total_months = months_diff + 1
    
    return 'monthly' if total_months <= 12 else 'yearly'


def calculate_nightingale_time_data(
    cleaned_df: pd.DataFrame,
    animation_frame_timestamps: List[pd.Timestamp],
    aggregation_type: Optional[str] = None
) -> Dict[pd.Timestamp, Dict[str, any]]:
    """
    Calculate time-aggregated play counts for nightingale rose chart.
    
    Args:
        cleaned_df: DataFrame with timestamp and play event data
        animation_frame_timestamps: List of frame timestamps for animation
        aggregation_type: 'monthly' or 'yearly', auto-determined if None
        
    Returns:
        Dict mapping frame timestamps to nightingale data:
        {
            frame_timestamp: {
                'aggregation_type': 'monthly' | 'yearly',
                'periods': [
                    {
                        'label': 'Jan 2024' | '2024',
                        'plays': 150,
                        'start_date': pd.Timestamp,
                        'end_date': pd.Timestamp,
                        'is_complete': True,  # Whether this period is fully in the past
                        'angle_start': 0.0,   # Angular position (radians)
                        'angle_end': 1.047,   # Angular position (radians) 
                        'color': '#ff6b6b'    # Color for this period
                    }
                ],
                'high_period': {'label': 'Mar 2024', 'plays': 200},
                'low_period': {'label': 'Jan 2024', 'plays': 150},
                'total_periods': 4,  # Total periods that will eventually appear
                'visible_periods': 3  # Periods visible at this timestamp
            }
        }
    """
    
    if cleaned_df is None or cleaned_df.empty:
        return {ts: _empty_nightingale_data() for ts in animation_frame_timestamps}
    
    if 'timestamp' not in cleaned_df.columns:
        raise ValueError("cleaned_df must contain a 'timestamp' column")
    
    # Ensure timezone-aware timestamps
    df = cleaned_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    
    # Determine date range for aggregation type
    if aggregation_type is None:
        start_date = df['timestamp'].min()
        end_date = df['timestamp'].max()
        aggregation_type = determine_aggregation_type(start_date, end_date)
    
    print(f"Using {aggregation_type} aggregation for nightingale chart")
    
    # Create time periods
    if aggregation_type == 'monthly':
        period_data = _calculate_monthly_aggregation(df, animation_frame_timestamps)
    else:
        period_data = _calculate_yearly_aggregation(df, animation_frame_timestamps)
    
    return period_data


def _calculate_monthly_aggregation(
    df: pd.DataFrame, 
    animation_frame_timestamps: List[pd.Timestamp]
) -> Dict[pd.Timestamp, Dict[str, any]]:
    """Calculate progressive monthly play count aggregation.
    
    For each animation frame, calculates cumulative plays within each month
    up to the current frame timestamp, enabling smooth progressive growth.
    """
    
    # Get overall date range to determine total possible periods
    data_start = df['timestamp'].min().to_period('M')
    data_end = df['timestamp'].max().to_period('M')
    
    # Generate all months in range (for consistent ordering)
    all_months = pd.period_range(start=data_start, end=data_end, freq='M')
    
    # Color palette for months (cycling through colors)
    month_colors = [
        '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', 
        '#feca57', '#ff9ff3', '#54a0ff', '#5f27cd',
        '#00d2d3', '#ff9f43', '#c44569', '#40407a'
    ]
    
    results = {}
    
    for frame_ts in animation_frame_timestamps:
        frame_ts_period = frame_ts.to_period('M')
        
        # Find months that should be visible at this timestamp
        # Include months that have started (even if not complete)
        visible_months = [month for month in all_months if month.start_time.tz_localize('UTC') <= frame_ts]
        
        periods = []
        for i, month in enumerate(visible_months):
            month_start = month.start_time.tz_localize('UTC')
            month_end = month.end_time.tz_localize('UTC')
            
            # Calculate cumulative plays within this month up to current frame timestamp
            # Only count plays from month_start to min(month_end, frame_ts)
            effective_end = min(month_end, frame_ts)
            
            # Use a more efficient calculation
            # Since we're doing this for many frames, consider pre-calculating monthly data
            if effective_end < month_start:
                plays = 0
            elif effective_end >= month_end:
                # Use full month count (more efficient for completed months)
                if not hasattr(_calculate_monthly_aggregation, '_monthly_cache'):
                    _calculate_monthly_aggregation._monthly_cache = {}
                
                cache_key = month.strftime('%Y-%m')
                if cache_key not in _calculate_monthly_aggregation._monthly_cache:
                    month_data = df[
                        (df['timestamp'] >= month_start) & 
                        (df['timestamp'] <= month_end)
                    ]
                    _calculate_monthly_aggregation._monthly_cache[cache_key] = len(month_data)
                plays = _calculate_monthly_aggregation._monthly_cache[cache_key]
            else:
                # Partial month - need real-time calculation
                month_data = df[
                    (df['timestamp'] >= month_start) & 
                    (df['timestamp'] <= effective_end)
                ]
                plays = len(month_data)
            
            # Calculate angular position (equally spaced around circle)
            if len(visible_months) == 1:
                angle_start, angle_end = 0, 2 * 3.14159  # Full circle for single month
            else:
                angle_per_segment = 2 * 3.14159 / len(visible_months)
                angle_start = i * angle_per_segment
                angle_end = (i + 1) * angle_per_segment
            
            period_info = {
                'label': month.strftime('%b'),  # "Jan" (month only, no year)
                'plays': int(plays),
                'start_date': month_start,
                'end_date': month_end,
                'is_complete': month_end < frame_ts,
                'angle_start': angle_start,
                'angle_end': angle_end,
                'color': month_colors[i % len(month_colors)]
            }
            periods.append(period_info)
        
        # Find high/low periods
        high_period = None
        low_period = None
        if periods:
            max_plays = max(p['plays'] for p in periods)
            min_plays = min(p['plays'] for p in periods)
            
            high_period = next(p for p in periods if p['plays'] == max_plays)
            low_period = next(p for p in periods if p['plays'] == min_plays)
        
        results[frame_ts] = {
            'aggregation_type': 'monthly',
            'periods': periods,
            'high_period': high_period,
            'low_period': low_period,
            'total_periods': len(all_months),
            'visible_periods': len(visible_months)
        }
    
    return results


def _calculate_yearly_aggregation(
    df: pd.DataFrame, 
    animation_frame_timestamps: List[pd.Timestamp]
) -> Dict[pd.Timestamp, Dict[str, any]]:
    """Calculate progressive yearly play count aggregation.
    
    For each animation frame, calculates cumulative plays within each year
    up to the current frame timestamp, enabling smooth progressive growth.
    """
    
    # Get overall date range
    data_start = df['timestamp'].min().to_period('Y')
    data_end = df['timestamp'].max().to_period('Y')
    
    # Generate all years in range
    all_years = pd.period_range(start=data_start, end=data_end, freq='Y')
    
    # Color palette for years (different from months)
    year_colors = [
        '#e74c3c', '#3498db', '#2ecc71', '#f39c12', 
        '#9b59b6', '#1abc9c', '#34495e', '#e67e22'
    ]
    
    results = {}
    
    for frame_ts in animation_frame_timestamps:
        frame_ts_period = frame_ts.to_period('Y')
        
        # Find years that should be visible at this timestamp
        # Include years that have started (even if not complete)
        visible_years = [year for year in all_years if year.start_time.tz_localize('UTC') <= frame_ts]
        
        periods = []
        for i, year in enumerate(visible_years):
            year_start = year.start_time.tz_localize('UTC')
            year_end = year.end_time.tz_localize('UTC')
            
            # Calculate cumulative plays within this year up to current frame timestamp
            # Only count plays from year_start to min(year_end, frame_ts)
            effective_end = min(year_end, frame_ts)
            
            # Use a more efficient calculation
            if effective_end < year_start:
                plays = 0
            elif effective_end >= year_end:
                # Use full year count (more efficient for completed years)
                if not hasattr(_calculate_yearly_aggregation, '_yearly_cache'):
                    _calculate_yearly_aggregation._yearly_cache = {}
                
                cache_key = year.strftime('%Y')
                if cache_key not in _calculate_yearly_aggregation._yearly_cache:
                    year_data = df[
                        (df['timestamp'] >= year_start) & 
                        (df['timestamp'] <= year_end)
                    ]
                    _calculate_yearly_aggregation._yearly_cache[cache_key] = len(year_data)
                plays = _calculate_yearly_aggregation._yearly_cache[cache_key]
            else:
                # Partial year - need real-time calculation
                year_data = df[
                    (df['timestamp'] >= year_start) & 
                    (df['timestamp'] <= effective_end)
                ]
                plays = len(year_data)
            
            # Calculate angular position
            if len(visible_years) == 1:
                angle_start, angle_end = 0, 2 * 3.14159
            else:
                angle_per_segment = 2 * 3.14159 / len(visible_years)
                angle_start = i * angle_per_segment
                angle_end = (i + 1) * angle_per_segment
            
            period_info = {
                'label': year.strftime('%Y'),  # "2024"
                'plays': int(plays),
                'start_date': year_start,
                'end_date': year_end,
                'is_complete': year_end < frame_ts,
                'angle_start': angle_start,
                'angle_end': angle_end,
                'color': year_colors[i % len(year_colors)]
            }
            periods.append(period_info)
        
        # Find high/low periods
        high_period = None
        low_period = None
        if periods:
            max_plays = max(p['plays'] for p in periods)
            min_plays = min(p['plays'] for p in periods)
            
            high_period = next(p for p in periods if p['plays'] == max_plays)
            low_period = next(p for p in periods if p['plays'] == min_plays)
        
        results[frame_ts] = {
            'aggregation_type': 'yearly',
            'periods': periods,
            'high_period': high_period,
            'low_period': low_period,
            'total_periods': len(all_years),
            'visible_periods': len(visible_years)
        }
    
    return results


def _empty_nightingale_data() -> Dict[str, any]:
    """Return empty nightingale data structure."""
    return {
        'aggregation_type': 'monthly',
        'periods': [],
        'high_period': None,
        'low_period': None,
        'total_periods': 0,
        'visible_periods': 0
    }


# Test functionality if run directly
if __name__ == "__main__":
    print("--- Testing time_aggregation.py ---")
    
    # Create sample data
    dates = pd.date_range('2024-01-01', '2024-05-01', freq='D', tz='UTC')
    sample_data = []
    
    for date in dates:
        # Add random plays per day (varying by month for testing)
        plays_per_day = 5 + (date.month * 2) + (date.day % 3)
        for _ in range(plays_per_day):
            sample_data.append({'timestamp': date, 'play_count': 1})
    
    df = pd.DataFrame(sample_data)
    
    # Test aggregation type determination
    start_date = pd.Timestamp('2024-01-01', tz='UTC')
    end_date = pd.Timestamp('2024-05-01', tz='UTC')
    agg_type = determine_aggregation_type(start_date, end_date)
    print(f"Aggregation type for Jan-May 2024: {agg_type}")
    
    # Test long range
    end_date_long = pd.Timestamp('2026-01-01', tz='UTC')
    agg_type_long = determine_aggregation_type(start_date, end_date_long)
    print(f"Aggregation type for Jan 2024-Jan 2026: {agg_type_long}")
    
    # Test nightingale calculation
    frame_timestamps = [
        pd.Timestamp('2024-01-15', tz='UTC'),
        pd.Timestamp('2024-02-15', tz='UTC'),
        pd.Timestamp('2024-03-15', tz='UTC')
    ]
    
    nightingale_data = calculate_nightingale_time_data(df, frame_timestamps)
    
    print("\nNightingale data for sample frames:")
    for ts, data in list(nightingale_data.items())[:2]:  # Show first 2
        print(f"\nFrame {ts.strftime('%b %Y')}:")
        print(f"  Aggregation: {data['aggregation_type']}")
        print(f"  Visible periods: {data['visible_periods']}/{data['total_periods']}")
        for period in data['periods']:
            print(f"    {period['label']}: {period['plays']} plays")
        if data['high_period']:
            print(f"  High: {data['high_period']['label']} ({data['high_period']['plays']} plays)")
        if data['low_period']:
            print(f"  Low: {data['low_period']['label']} ({data['low_period']['plays']} plays)")