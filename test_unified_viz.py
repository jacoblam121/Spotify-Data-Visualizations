#!/usr/bin/env python3
"""Test the unified network visualization"""

import json
import webbrowser
from pathlib import Path

def main():
    print("🧪 Testing Unified Network Visualization")
    print("=" * 50)
    
    # Check files
    if not Path("network_visualization.html").exists():
        print("❌ network_visualization.html not found")
        return
    
    if not Path("js/network-visualization.js").exists():
        print("❌ JavaScript file not found")
        return
    
    print("✅ Files found")
    
    # Check for data
    data_files = list(Path(".").glob("*network*.json"))
    if data_files:
        print(f"✅ Found {len(data_files)} network data files")
        with open(data_files[0]) as f:
            data = json.load(f)
        print(f"📊 {len(data.get('nodes', []))} nodes, {len(data.get('edges', []))} edges")
    else:
        print("⚠️  Using embedded sample data")
    
    # Open browser
    file_url = f"file://{Path('network_visualization.html').absolute()}"
    print(f"\n🌐 Opening: {file_url}")
    webbrowser.open(file_url)
    
    print("\n📋 Test Checklist:")
    print("✓ Mode switching (Global/Personal/Hybrid)")
    print("✓ Glow effects change per mode")
    print("✓ Node sizes change per mode")
    print("✓ Smooth transitions")
    print("✓ Force controls work")
    print("✓ Tooltips show mode-specific content")
    print("✓ Connection highlighting on hover")

if __name__ == "__main__":
    main()