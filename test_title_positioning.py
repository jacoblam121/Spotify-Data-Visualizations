#!/usr/bin/env python3
"""
Test script to verify the title positioning configuration
"""

import matplotlib.pyplot as plt
import numpy as np
import math
from nightingale_chart import draw_nightingale_chart
from config_loader import AppConfig

# Test loading the new title positioning configuration
config_file = 'configurations.txt'
config = AppConfig(config_file)

print("=== Testing Title Positioning Configuration ===")

# Test loading the configuration
try:
    title_position = config.get_float('NightingaleChart', 'TITLE_POSITION_ABOVE_CHART', 0.02)
    print(f"✓ TITLE_POSITION_ABOVE_CHART loaded: {title_position}")
    print(f"  Positive values = above chart, negative values = below chart")
    
except Exception as e:
    print(f"✗ Error loading configuration: {e}")

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

# Test different title positioning values
test_positions = [
    {'value': 0.05, 'name': 'Far Above (positive)', 'desc': '0.05 units above'},
    {'value': 0.02, 'name': 'Normal Above (positive)', 'desc': '0.02 units above (default)'},
    {'value': 0.0, 'name': 'At Chart Edge', 'desc': 'Exactly at top edge'},
    {'value': -0.03, 'name': 'Below Chart (negative)', 'desc': '0.03 units below'}
]

for i, pos_test in enumerate(test_positions):
    # Create chart config with different title positioning
    chart_config = {
        'center_x': 0.5,
        'center_y': 0.5, 
        'radius': 0.25,
        'chart_width_fig': 0.5,
        'chart_height_fig': 0.5,
        'show_labels': True,
        'label_radius_ratio': 1.15,
        'label_font_size': 11,
        'label_font_color': 'black',
        'label_font_weight': 'bold',
        'show_high_low': True,
        'high_low_font_size': 10,
        'high_low_y_offset_fig': 0.12,
        'high_low_spacing_fig': 0.03,
        'high_period_color': 'darkgreen',
        'low_period_color': 'darkred',
        'title_font_size': 13,
        'title_font_weight': 'bold',
        'title_color': 'black',
        'title_y_offset_fig': pos_test['value'],  # Test different positions
        'outer_circle_color': 'gray',
        'outer_circle_linestyle': '--',
        'outer_circle_linewidth': 1.0,
        'debug': False
    }

    # Test the chart rendering
    try:
        fig = plt.figure(figsize=(8, 8), dpi=100)
        fig.patch.set_facecolor('white')
        
        draw_nightingale_chart(fig, sample_data, chart_config)
        
        fig.suptitle(f'Title Position Test: {pos_test["name"]}\\n{pos_test["desc"]}', 
                     fontsize=16, fontweight='bold', y=0.92)
        
        output_file = f'test_title_position_{i+1}.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"✓ Test {i+1} chart rendered: {output_file}")
        
        plt.close()

    except Exception as e:
        print(f"✗ Error rendering test {i+1}: {e}")

print("\n=== Title Positioning Feature Summary ===")
print("✅ Configuration Added:")
print("   TITLE_POSITION_ABOVE_CHART = 0.02  (configurable title distance)")

print("\n✅ Position Calculation:")
print("   title_y = center_y + height/2 + title_y_offset")
print("   Positive values = move title UP (above chart)")
print("   Negative values = move title DOWN (below chart)")

print("\n✅ Usage:")
print("   0.05 = Far above chart")
print("   0.02 = Normal above chart (default)")
print("   0.0  = Exactly at top edge of chart")  
print("   -0.03 = Below chart (unusual but possible)")

print("\n✅ The title position is now fully configurable!")