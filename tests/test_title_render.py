#!/usr/bin/env python3
"""
Test script to verify the title positioning is working in actual rendering
"""

import matplotlib.pyplot as plt
import numpy as np
import math
from nightingale_chart import draw_nightingale_chart
from config_loader import AppConfig

# Load current configuration
config_file = 'configurations.txt'
config = AppConfig(config_file)

print("=== Testing Title Rendering with Current Configuration ===")

# Load the actual configuration values
NIGHTINGALE_TITLE_POSITION_ABOVE_CHART = config.get_float('NightingaleChart', 'TITLE_POSITION_ABOVE_CHART', 0.02)
NIGHTINGALE_CHART_X = config.get_float('NightingaleChart', 'CHART_X', 0.15)
NIGHTINGALE_CHART_Y = config.get_float('NightingaleChart', 'CHART_Y', 0.3)
NIGHTINGALE_CHART_RADIUS = config.get_float('NightingaleChart', 'CHART_RADIUS', 0.12)

print(f"Using configuration values:")
print(f"  TITLE_POSITION_ABOVE_CHART: {NIGHTINGALE_TITLE_POSITION_ABOVE_CHART}")
print(f"  CHART_X: {NIGHTINGALE_CHART_X}")
print(f"  CHART_Y: {NIGHTINGALE_CHART_Y}")
print(f"  CHART_RADIUS: {NIGHTINGALE_CHART_RADIUS}")

# Create test data
sample_periods = [
    {
        'label': 'Jan',
        'plays': 80,
        'angle_start': 0,
        'angle_end': 2 * math.pi / 3,
        'color': '#ff6b6b'
    },
    {
        'label': 'Feb', 
        'plays': 120,
        'angle_start': 2 * math.pi / 3,
        'angle_end': 4 * math.pi / 3,
        'color': '#4ecdc4'
    },
    {
        'label': 'Mar',
        'plays': 100,
        'angle_start': 4 * math.pi / 3,
        'angle_end': 2 * math.pi,
        'color': '#45b7d1'
    }
]

sample_data = {
    'aggregation_type': 'monthly',
    'periods': sample_periods,
    'high_period': {'label': 'Feb', 'plays': 120},
    'low_period': {'label': 'Jan', 'plays': 80},
    'total_periods': 3,
    'visible_periods': 3
}

# Calculate chart dimensions
chart_width_fig = NIGHTINGALE_CHART_RADIUS * 2
chart_height_fig = NIGHTINGALE_CHART_RADIUS * 2

# Create chart config using actual loaded values
chart_config = {
    'center_x': NIGHTINGALE_CHART_X,
    'center_y': NIGHTINGALE_CHART_Y, 
    'radius': NIGHTINGALE_CHART_RADIUS,
    'chart_width_fig': chart_width_fig,
    'chart_height_fig': chart_height_fig,
    'show_labels': True,
    'label_radius_ratio': 1.15,
    'label_font_size': 16,
    'label_font_color': 'black',
    'label_font_weight': 'normal',
    'show_high_low': True,
    'high_low_font_size': 20,
    'high_low_y_offset_fig': 0.07,
    'high_low_spacing_fig': 0.025,
    'high_period_color': 'darkgreen',
    'low_period_color': 'darkred',
    'title_font_size': 22,
    'title_font_weight': 'normal',
    'title_color': 'black',
    'title_y_offset_fig': NIGHTINGALE_TITLE_POSITION_ABOVE_CHART,  # Use actual config value
    'outer_circle_color': 'gray',
    'outer_circle_linestyle': '--',
    'outer_circle_linewidth': 1.0,
    'debug': False
}

print(f"\nChart config title_y_offset_fig: {chart_config['title_y_offset_fig']}")

# Expected title position calculation (same as in nightingale_chart.py)
expected_title_y = NIGHTINGALE_CHART_Y + chart_height_fig / 2 + NIGHTINGALE_TITLE_POSITION_ABOVE_CHART
print(f"Expected title Y position: {expected_title_y:.3f}")

# Test the chart rendering
try:
    fig = plt.figure(figsize=(12, 8), dpi=100)
    fig.patch.set_facecolor('white')
    
    # Add some reference lines to help visualize positioning
    fig.axhline(y=NIGHTINGALE_CHART_Y, color='red', linestyle=':', alpha=0.5, label='Chart Center Y')
    fig.axhline(y=NIGHTINGALE_CHART_Y + chart_height_fig/2, color='orange', linestyle=':', alpha=0.5, label='Chart Top Edge')
    fig.axhline(y=expected_title_y, color='blue', linestyle=':', alpha=0.5, label='Expected Title Y')
    
    draw_nightingale_chart(fig, sample_data, chart_config)
    
    fig.suptitle(f'Title Position Test: Config Value = {NIGHTINGALE_TITLE_POSITION_ABOVE_CHART}', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    output_file = 'test_current_title_config.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✓ Test chart rendered: {output_file}")
    
    plt.close()

except Exception as e:
    print(f"✗ Error rendering test chart: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Analysis ===")
print("If the title positioning is working correctly, you should see:")
print(f"- The title positioned at Y={expected_title_y:.3f} (blue reference line)")
print(f"- This should be {NIGHTINGALE_TITLE_POSITION_ABOVE_CHART} units above the chart's top edge (orange line)")
print(f"- Chart center is at Y={NIGHTINGALE_CHART_Y} (red line)")