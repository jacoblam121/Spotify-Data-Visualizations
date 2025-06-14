#\!/usr/bin/env python3
"""Test script for the new unified network visualization"""

import json
import webbrowser
from pathlib import Path

def test_visualization():
    """Open and test the unified network visualization"""
    
    print("🧪 Testing Unified Network Visualization")
    print("=" * 50)
    
    # Check files exist
    html_file = Path("network_visualization.html")
    js_file = Path("js/network-visualization.js")
    
    if not html_file.exists():
        print("❌ network_visualization.html not found")
        return
        
    if not js_file.exists():
        print("❌ js/network-visualization.js not found")
        return
    
    print("✅ Files found")
    
    # Check for test data
    data_files = [
        "bidirectional_network_100artists_20250613_012900.json",
        "bidirectional_network_100artists_20250613_012658.json"
    ]
    
    available_data = [f for f in data_files if Path(f).exists()]
    
    if available_data:
        print(f"✅ Found {len(available_data)} network data files")
        
        # Check data structure
        with open(available_data[0], 'r') as f:
            data = json.load(f)
            
        print(f"📊 Sample data: {len(data.get('nodes', []))} nodes, {len(data.get('edges', []))} edges")
        
        if data.get('nodes') and len(data['nodes']) > 0:
            sample_node = data['nodes'][0]
            has_listeners = 'listeners' in sample_node or 'listener_count' in sample_node
            has_play_count = 'play_count' in sample_node
            
            if has_listeners and has_play_count:
                print("🎯 Perfect\! Data has both global and personal metrics")
            else:
                print("⚠️  Will use embedded sample data")
    else:
        print("⚠️  No network data files found - will use embedded sample data")
    
    # Open in browser
    file_url = f"file://{html_file.absolute()}"
    print(f"\n🌐 Opening: {file_url}")
    
    webbrowser.open(file_url)
    
    print("\n📋 Test these features:")
    print("1. Mode switching (Global/Personal/Hybrid)")
    print("2. Smooth transitions between modes") 
    print("3. Glow effects for different artist types")
    print("4. Force controls and zoom/pan")
    print("5. Tooltips and connection highlighting")

if __name__ == "__main__":
    test_visualization()
EOF < /dev/null
