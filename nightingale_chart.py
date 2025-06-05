"""
nightingale_chart.py

Handles rendering of animated nightingale rose charts using matplotlib.
Integrates with the existing animation pipeline from main_animator.py.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
from matplotlib.figure import Figure
from typing import Dict, List, Tuple, Optional, Any
import math

__all__ = [
    "prepare_nightingale_animation_data", 
    "draw_nightingale_chart",
    "calculate_nightingale_layout"
]


def _cubic_ease_in_out(t: float) -> float:
    """
    Cubic ease-in-out easing function for smooth animations.
    
    Args:
        t: Progress value between 0.0 and 1.0
        
    Returns:
        Eased progress value between 0.0 and 1.0
    """
    if t < 0.5:
        return 4 * t * t * t
    else:
        p = 2 * t - 2
        return 1 + p * p * p / 2


def _elastic_ease_out(t: float) -> float:
    """
    Elastic ease-out easing function for bouncy growth effect.
    
    Args:
        t: Progress value between 0.0 and 1.0
        
    Returns:
        Eased progress value between 0.0 and 1.0
    """
    if t == 0 or t == 1:
        return t
    
    return math.pow(2, -10 * t) * math.sin((t - 0.1) * 5 * math.pi) + 1


def prepare_nightingale_animation_data(
    nightingale_time_data: Dict[pd.Timestamp, Dict[str, Any]],
    animation_frame_timestamps: List[pd.Timestamp],
    enable_smooth_transitions: bool = True,
    transition_duration_seconds: float = 0.3,
    target_fps: int = 30
) -> Dict[pd.Timestamp, Dict[str, Any]]:
    """
    Prepare nightingale data for smooth animation by generating interpolated frames.
    Uses the same interpolation approach as the main bar chart race.
    
    Args:
        nightingale_time_data: Raw nightingale data from time_aggregation.py
        animation_frame_timestamps: All animation frame timestamps
        enable_smooth_transitions: Whether to generate tween frames
        transition_duration_seconds: Duration of transitions
        target_fps: Target frames per second
        
    Returns:
        Dict with interpolated nightingale data for each frame timestamp
    """
    
    if not enable_smooth_transitions:
        return nightingale_time_data
    
    # Number of tween frames between keyframes
    num_tween_frames = int(transition_duration_seconds * target_fps)
    
    # Sort timestamps to create keyframe pairs
    keyframe_timestamps = sorted(nightingale_time_data.keys())
    interpolated_data = {}
    
    for i, frame_ts in enumerate(animation_frame_timestamps):
        # Find the surrounding keyframes
        current_keyframe = None
        next_keyframe = None
        
        for j, keyframe_ts in enumerate(keyframe_timestamps):
            if keyframe_ts <= frame_ts:
                current_keyframe = keyframe_ts
                if j + 1 < len(keyframe_timestamps):
                    next_keyframe = keyframe_timestamps[j + 1]
        
        if current_keyframe is None:
            # Before first keyframe - use empty data
            interpolated_data[frame_ts] = _create_empty_nightingale_frame()
            continue
        
        if next_keyframe is None or not enable_smooth_transitions:
            # At or after last keyframe - use current keyframe data
            interpolated_data[frame_ts] = nightingale_time_data[current_keyframe].copy()
            continue
        
        # Calculate interpolation progress between keyframes
        total_keyframe_duration = (next_keyframe - current_keyframe).total_seconds()
        elapsed_duration = (frame_ts - current_keyframe).total_seconds()
        raw_progress = min(1.0, elapsed_duration / total_keyframe_duration) if total_keyframe_duration > 0 else 1.0
        
        # Apply smooth easing for better visual transitions
        # Use cubic ease-in-out for natural growth animation
        progress = _cubic_ease_in_out(raw_progress)
        
        # Interpolate between current and next keyframe
        current_data = nightingale_time_data[current_keyframe]
        next_data = nightingale_time_data[next_keyframe]
        
        interpolated_frame = _interpolate_nightingale_frames(current_data, next_data, progress)
        interpolated_data[frame_ts] = interpolated_frame
    
    return interpolated_data


def _interpolate_nightingale_frames(
    current_frame: Dict[str, Any], 
    next_frame: Dict[str, Any], 
    progress: float
) -> Dict[str, Any]:
    """
    Interpolate between two nightingale frames for smooth transitions.
    """
    
    # Start with current frame structure
    interpolated = current_frame.copy()
    interpolated['periods'] = []
    
    # Create lookup for current and next periods by label
    current_periods = {p['label']: p for p in current_frame.get('periods', [])}
    next_periods = {p['label']: p for p in next_frame.get('periods', [])}
    
    # Get all unique period labels (union of current and next)
    all_labels = set(current_periods.keys()) | set(next_periods.keys())
    
    for label in sorted(all_labels):  # Sort for consistent ordering
        current_period = current_periods.get(label)
        next_period = next_periods.get(label)
        
        if current_period and next_period:
            # Period exists in both frames - interpolate values
            interpolated_period = _interpolate_period(current_period, next_period, progress)
        elif next_period and not current_period:
            # New period appearing - animate from 0 radius with elastic easing
            interpolated_period = next_period.copy()
            radius_progress = _elastic_ease_out(progress)  # Use elastic for new segments
            interpolated_period['plays'] = int(next_period['plays'] * progress)
            interpolated_period['radius'] = next_period.get('radius', 0) * radius_progress
        elif current_period and not next_period:
            # Period disappearing - animate to 0 radius
            interpolated_period = current_period.copy()
            interpolated_period['plays'] = int(current_period['plays'] * (1 - progress))
            interpolated_period['radius'] = current_period.get('radius', 0) * (1 - progress)
        else:
            continue  # Should not happen
        
        interpolated['periods'].append(interpolated_period)
    
    # Update visible_periods count
    interpolated['visible_periods'] = len(interpolated['periods'])
    
    # Interpolate high/low periods if they exist
    if current_frame.get('high_period') and next_frame.get('high_period'):
        # Only interpolate if same period remains high
        if current_frame['high_period']['label'] == next_frame['high_period']['label']:
            interpolated['high_period'] = _interpolate_period(
                current_frame['high_period'], 
                next_frame['high_period'], 
                progress
            )
        else:
            # Different high periods - use next frame's high period
            interpolated['high_period'] = next_frame['high_period']
    
    return interpolated


def _interpolate_period(period1: Dict, period2: Dict, progress: float) -> Dict:
    """Interpolate between two period dictionaries with enhanced easing."""
    interpolated = period1.copy()
    
    # Interpolate numeric values - use cubic easing for smooth transitions
    plays_progress = _cubic_ease_in_out(progress)
    interpolated['plays'] = int(period1['plays'] + (period2['plays'] - period1['plays']) * plays_progress)
    
    # Interpolate angles linearly (angular changes should be consistent)
    interpolated['angle_start'] = period1['angle_start'] + (period2['angle_start'] - period1['angle_start']) * progress
    interpolated['angle_end'] = period1['angle_end'] + (period2['angle_end'] - period1['angle_end']) * progress
    
    # Interpolate radius with cubic easing for natural growth/shrinkage
    if 'radius' in period1 and 'radius' in period2:
        radius_progress = _cubic_ease_in_out(progress)
        interpolated['radius'] = period1['radius'] + (period2['radius'] - period1['radius']) * radius_progress
    
    return interpolated


def _create_empty_nightingale_frame() -> Dict[str, Any]:
    """Create empty nightingale frame for timestamps before data starts."""
    return {
        'aggregation_type': 'monthly',
        'periods': [],
        'high_period': None,
        'low_period': None,
        'total_periods': 0,
        'visible_periods': 0
    }


def calculate_nightingale_layout(
    periods: List[Dict[str, Any]], 
    chart_radius: float,
    center_x: float, 
    center_y: float,
    max_radius_scale: float = 1.0,
    figure_width: float = 1.0,
    figure_height: float = 1.0
) -> List[Dict[str, Any]]:
    """
    Calculate the layout geometry for nightingale chart periods with perfect circular shape.
    
    Args:
        periods: List of period data with plays and angles
        chart_radius: Maximum radius of the chart in figure units
        center_x, center_y: Center position of the chart in figure units
        max_radius_scale: Scale factor for maximum radius (for animation)
        figure_width: Figure width for aspect ratio calculation
        figure_height: Figure height for aspect ratio calculation
        
    Returns:
        List of periods with added geometry information (radius, center_x, center_y)
    """
    
    if not periods:
        return []
    
    # For perfect circular shape, use the chart_radius directly without aspect ratio distortion
    # The figure coordinates should already be set up to maintain the circle
    effective_radius = chart_radius * max_radius_scale
    
    # Find maximum plays to scale radii
    max_plays = max(p['plays'] for p in periods) if periods else 1
    
    # Calculate radius for each period based on play count
    layout_periods = []
    for period in periods:
        period_copy = period.copy()
        
        # Calculate radius proportional to play count
        if max_plays > 0:
            radius_ratio = period['plays'] / max_plays
        else:
            radius_ratio = 0
        
        # Calculate final radius for this period
        period_radius = effective_radius * radius_ratio
        period_copy['radius'] = period_radius
        period_copy['center_x'] = center_x
        period_copy['center_y'] = center_y
        
        # Convert angles to degrees for matplotlib
        period_copy['angle_start_deg'] = math.degrees(period['angle_start'])
        period_copy['angle_end_deg'] = math.degrees(period['angle_end'])
        
        layout_periods.append(period_copy)
    
    return layout_periods


def draw_nightingale_chart(
    fig: Figure,
    nightingale_data: Dict[str, Any],
    chart_config: Dict[str, Any]
) -> None:
    """
    Draw the nightingale rose chart on the given figure.
    
    Args:
        fig: Matplotlib figure to draw on
        nightingale_data: Nightingale data for current frame
        chart_config: Configuration for chart appearance and positioning
    """
    
    # Extract configuration
    center_x = chart_config.get('center_x', 0.15)
    center_y = chart_config.get('center_y', 0.35)
    chart_radius = chart_config.get('radius', 0.08)
    show_labels = chart_config.get('show_labels', True)
    show_high_low = chart_config.get('show_high_low', True)
    label_font_size = chart_config.get('label_font_size', 10)
    label_font_color = chart_config.get('label_font_color', 'black')
    label_font_weight = chart_config.get('label_font_weight', 'normal')
    high_low_font_size = chart_config.get('high_low_font_size', 9)
    high_low_y_offset = chart_config.get('high_low_y_offset_fig', -0.12)
    high_low_spacing = chart_config.get('high_low_spacing_fig', 0.025)
    debug = chart_config.get('debug', False)
    
    periods = nightingale_data.get('periods', [])
    if not periods:
        if debug:
            print("DEBUG: No periods data for nightingale chart")
        return  # Nothing to draw
    
    if debug:
        print(f"DEBUG: Drawing nightingale chart with {len(periods)} periods at center ({center_x}, {center_y}), radius {chart_radius}")
    
    # Draw chart title above the chart
    aggregation_type = nightingale_data.get('aggregation_type', 'monthly')
    title_text = f"{'Monthly' if aggregation_type == 'monthly' else 'Yearly'} Distribution of Plays"
    title_y = center_y + chart_radius + 0.02  # Position above the chart
    
    fig.text(
        center_x, title_y,
        title_text,
        fontsize=label_font_size + 2,  # Slightly larger than labels
        ha='center', va='bottom',
        color='black',
        weight='bold',
        transform=fig.transFigure
    )
    
    if debug:
        print(f"DEBUG: Added title '{title_text}' at ({center_x:.3f}, {title_y:.3f})")
    
    # Get figure dimensions for aspect ratio calculation
    figure_width = fig.get_figwidth()
    figure_height = fig.get_figheight()
    
    # Calculate layout geometry with aspect ratio correction
    layout_periods = calculate_nightingale_layout(
        periods, chart_radius, center_x, center_y, 
        figure_width=figure_width, figure_height=figure_height
    )
    
    if debug:
        print(f"DEBUG: Layout periods calculated: {[p['label'] + ' (radius: ' + str(round(p.get('radius', 0), 3)) + ')' for p in layout_periods]}")
    
    # Draw each period as a wedge
    for period in layout_periods:
        if period['radius'] > 0:  # Only draw if radius > 0
            if debug:
                print(f"DEBUG: Drawing wedge for {period['label']}: center=({period['center_x']:.3f}, {period['center_y']:.3f}), " +
                      f"radius={period['radius']:.3f}, angles={period['angle_start_deg']:.1f}°-{period['angle_end_deg']:.1f}°")
            
            # Create circular wedge patch using figure coordinates
            # Use the period's calculated radius directly for perfect circular shape
            wedge_radius = period['radius']
            
            wedge = patches.Wedge(
                center=(period['center_x'], period['center_y']),
                r=wedge_radius,
                theta1=period['angle_start_deg'],
                theta2=period['angle_end_deg'],
                facecolor=period['color'],
                edgecolor='white',
                linewidth=2,
                alpha=0.8,
                transform=fig.transFigure  # Use figure coordinates
            )
            
            # Add wedge directly to figure
            fig.patches.append(wedge)
            
        # Add radial period labels outside the chart circle
        if show_labels and periods:
            label_radius_ratio = chart_config.get('label_radius_ratio', 1.15)  # Position outside circle
            label_radius = chart_radius * label_radius_ratio
            
            for period in layout_periods:
                if period['radius'] > 0:  # Only label visible segments
                    # Calculate label position (middle of wedge, outside circle)
                    mid_angle = math.radians((period['angle_start_deg'] + period['angle_end_deg']) / 2)
                    label_x = center_x + label_radius * math.cos(mid_angle)
                    label_y = center_y + label_radius * math.sin(mid_angle)
                    
                    if debug:
                        print(f"DEBUG: Adding radial label '{period['label']}' at ({label_x:.3f}, {label_y:.3f})")
                    
                    # Add text with configurable styling
                    fig.text(
                        label_x, label_y, 
                        period['label'],
                        fontsize=label_font_size,
                        ha='center', va='center',
                        color=label_font_color,
                        weight=label_font_weight,
                        transform=fig.transFigure
                    )
        else:
            if debug:
                print(f"DEBUG: Skipping {period['label']} - radius is {period.get('radius', 0)}")
    
    # Draw high/low period information below chart
    if show_high_low:
        high_period = nightingale_data.get('high_period')
        low_period = nightingale_data.get('low_period')
        
        text_y = center_y + high_low_y_offset  # Position below chart using config
        
        if high_period:
            high_text = f"High: {high_period['label']} ({high_period['plays']} plays)"
            fig.text(
                center_x, text_y,
                high_text,
                fontsize=high_low_font_size,
                ha='center', va='top',
                color='darkgreen',
                weight='bold',
                transform=fig.transFigure
            )
        
        if low_period and low_period != high_period:
            low_text = f"Low: {low_period['label']} ({low_period['plays']} plays)"
            fig.text(
                center_x, text_y - high_low_spacing,
                low_text,
                fontsize=high_low_font_size,
                ha='center', va='top',
                color='darkred',
                weight='bold',
                transform=fig.transFigure
            )


# Test functionality if run directly
if __name__ == "__main__":
    print("--- Testing nightingale_chart.py ---")
    
    # Create sample nightingale data
    sample_periods = [
        {
            'label': 'Jan 2024',
            'plays': 150,
            'angle_start': 0,
            'angle_end': math.pi / 2,
            'color': '#ff6b6b'
        },
        {
            'label': 'Feb 2024', 
            'plays': 200,
            'angle_start': math.pi / 2,
            'angle_end': math.pi,
            'color': '#4ecdc4'
        },
        {
            'label': 'Mar 2024',
            'plays': 120,
            'angle_start': math.pi,
            'angle_end': 3 * math.pi / 2,
            'color': '#45b7d1'
        }
    ]
    
    sample_data = {
        'aggregation_type': 'monthly',
        'periods': sample_periods,
        'high_period': {'label': 'Feb 2024', 'plays': 200},
        'low_period': {'label': 'Mar 2024', 'plays': 120},
        'total_periods': 3,
        'visible_periods': 3
    }
    
    # Test layout calculation
    layout_periods = calculate_nightingale_layout(sample_periods, 0.1, 0.15, 0.35)
    
    print("Layout calculation test:")
    for period in layout_periods:
        print(f"  {period['label']}: radius={period['radius']:.3f}, "
              f"angles={period['angle_start_deg']:.1f}°-{period['angle_end_deg']:.1f}°")
    
    print("\nNightingale chart module ready for integration!")