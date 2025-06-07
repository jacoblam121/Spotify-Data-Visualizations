#!/usr/bin/env python3
"""
Test script to verify title positioning configuration is being loaded correctly
"""

from config_loader import AppConfig

# Test loading the configuration
config_file = 'configurations.txt'
config = AppConfig(config_file)

print("=== Testing Title Position Configuration Loading ===")

try:
    title_position = config.get_float('NightingaleChart', 'TITLE_POSITION_ABOVE_CHART', 0.02)
    print(f"✓ TITLE_POSITION_ABOVE_CHART loaded: {title_position}")
    print(f"  Expected: 0.15 (from configurations.txt)")
    print(f"  Actual: {title_position}")
    
    if title_position == 0.15:
        print("✅ Configuration loading is working correctly!")
    else:
        print("❌ Configuration not loading the expected value")
        
except Exception as e:
    print(f"✗ Error loading configuration: {e}")

print("\n=== Testing Other Nightingale Config Values ===")

try:
    chart_x = config.get_float('NightingaleChart', 'CHART_X', 0.15)
    chart_y = config.get_float('NightingaleChart', 'CHART_Y', 0.3)
    chart_radius = config.get_float('NightingaleChart', 'CHART_RADIUS', 0.12)
    
    print(f"CHART_X: {chart_x} (expected: 0.15)")
    print(f"CHART_Y: {chart_y} (expected: 0.27)")
    print(f"CHART_RADIUS: {chart_radius} (expected: 0.17)")
    
except Exception as e:
    print(f"Error loading other config: {e}")