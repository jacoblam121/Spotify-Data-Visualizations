#!/usr/bin/env python3
"""
Data Source Availability Checker
Verifies that data files are present and readable before running tests.
"""

import os
import json
import pandas as pd
from config_loader import AppConfig

def check_spotify_data():
    """Check if Spotify data is available"""
    print("🎵 Checking Spotify data...")
    
    config = AppConfig('configurations.txt')
    spotify_file = config.get('DataSource', 'INPUT_FILENAME_SPOTIFY', 'spotify_data.json')
    
    if not os.path.exists(spotify_file):
        print(f"   ❌ {spotify_file} not found")
        return False
    
    try:
        with open(spotify_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list) or len(data) == 0:
            print(f"   ❌ {spotify_file} is empty or invalid format")
            return False
        
        # Check first entry structure - support both old and new formats
        first_entry = data[0]
        
        # Old format fields
        old_fields = ['ts', 'artistName', 'trackName', 'msPlayed']
        # New format fields  
        new_fields = ['ts', 'master_metadata_album_artist_name', 'master_metadata_track_name', 'ms_played']
        
        has_old_format = all(field in first_entry for field in old_fields)
        has_new_format = all(field in first_entry for field in new_fields)
        
        if not has_old_format and not has_new_format:
            print(f"   ❌ {spotify_file} has unrecognized format")
            print(f"      Available fields: {list(first_entry.keys())}")
            return False
        
        print(f"   ✅ {spotify_file} found with {len(data):,} entries")
        
        if has_old_format:
            print(f"      Format: Old Spotify format")
            print(f"      Sample: \"{first_entry.get('trackName')}\" by {first_entry.get('artistName')}")
        else:
            print(f"      Format: New Spotify format")
            track_name = first_entry.get('master_metadata_track_name')
            artist_name = first_entry.get('master_metadata_album_artist_name')
            print(f"      Sample: \"{track_name}\" by {artist_name}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error reading {spotify_file}: {e}")
        return False

def check_lastfm_data():
    """Check if Last.fm data is available"""
    print("🎶 Checking Last.fm data...")
    
    config = AppConfig('configurations.txt')
    lastfm_file = config.get('DataSource', 'INPUT_FILENAME_LASTFM', 'lastfm_data.csv')
    
    if not os.path.exists(lastfm_file):
        print(f"   ⚠️  {lastfm_file} not found (optional)")
        return False
    
    try:
        df = pd.read_csv(lastfm_file, encoding='utf-8')
        
        if len(df) == 0:
            print(f"   ❌ {lastfm_file} is empty")
            return False
        
        # Check expected columns (Last.fm export format varies)
        expected_cols = ['artist', 'track', 'date']  # Common columns
        missing_cols = [col for col in expected_cols if col not in df.columns]
        
        if len(missing_cols) == len(expected_cols):
            print(f"   ⚠️  {lastfm_file} has unexpected format")
            print(f"      Columns: {list(df.columns)}")
        
        print(f"   ✅ {lastfm_file} found with {len(df):,} entries")
        if 'artist' in df.columns and 'track' in df.columns:
            sample_row = df.iloc[0]
            print(f"      Sample: \"{sample_row.get('track', 'N/A')}\" by {sample_row.get('artist', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error reading {lastfm_file}: {e}")
        return False

def check_configuration():
    """Check configuration file"""
    print("⚙️  Checking configuration...")
    
    config_file = 'configurations.txt'
    if not os.path.exists(config_file):
        print(f"   ❌ {config_file} not found")
        return False
    
    try:
        config = AppConfig(config_file)
        
        # Check key settings
        source = config.get('DataSource', 'SOURCE', 'spotify')
        mode = config.get('VisualizationMode', 'MODE', 'tracks')
        resolution = config.get('AnimationOutput', 'RESOLUTION', '4k')
        
        print(f"   ✅ Configuration loaded")
        print(f"      Data source: {source}")
        print(f"      Visualization mode: {mode}")
        print(f"      Resolution: {resolution}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error loading configuration: {e}")
        return False

def check_dependencies():
    """Check that required Python packages are available"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        'pandas', 'numpy', 'matplotlib', 'PIL', 'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"   ❌ Missing packages: {missing_packages}")
        print("      Run: pip install -r requirements.txt")
        return False
    
    print("   ✅ All required packages available")
    return True

def main():
    """Run all checks"""
    print("=" * 50)
    print("DATA SOURCE AVAILABILITY CHECK")
    print("=" * 50)
    print()
    
    checks = [
        ("Configuration", check_configuration),
        ("Dependencies", check_dependencies),
        ("Spotify Data", check_spotify_data),
        ("Last.fm Data", check_lastfm_data),
    ]
    
    results = {}
    for name, check_func in checks:
        results[name] = check_func()
        print()
    
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    spotify_available = results.get("Spotify Data", False)
    lastfm_available = results.get("Last.fm Data", False)
    config_ok = results.get("Configuration", False)
    deps_ok = results.get("Dependencies", False)
    
    if not config_ok:
        print("❌ Configuration issue - fix configurations.txt")
        return 1
    
    if not deps_ok:
        print("❌ Missing dependencies - run pip install -r requirements.txt")
        return 1
    
    if not spotify_available and not lastfm_available:
        print("❌ No data sources available")
        print("   Need either spotify_data.json or lastfm_data.csv")
        return 1
    
    if spotify_available and lastfm_available:
        print("✅ Both data sources available - all tests can run")
        test_recommendation = "python test_phase1_comprehensive.py"
    elif spotify_available:
        print("✅ Spotify data available - most tests can run")
        print("   (Last.fm test will be skipped)")
        test_recommendation = "python test_phase1_comprehensive.py"
    else:  # lastfm_available
        print("✅ Last.fm data available - most tests can run")
        print("   (Spotify tests will use Last.fm data)")
        test_recommendation = "python test_phase1_comprehensive.py"
    
    print()
    print("READY TO TEST!")
    print(f"Run: {test_recommendation}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())