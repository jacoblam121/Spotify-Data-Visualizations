"""
Data Setup Checker
Verifies that data files and configuration are properly set up.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from config_loader import AppConfig
from data_processor import clean_and_filter_data


def check_data_setup():
    """Check if data files and configuration are properly set up."""
    print("🔍 Data Setup Checker")
    print("=" * 50)
    
    # Check if we're in the right directory
    expected_files = ['configurations.txt', 'data_processor.py', 'lastfm_utils.py']
    missing_files = [f for f in expected_files if not os.path.exists(f'../{f}')]
    
    if missing_files:
        print("❌ Run this script from the tests/ directory")
        print(f"Missing files: {missing_files}")
        return False
    
    print("✅ Running from correct directory")
    
    # Load configuration
    try:
        config = AppConfig('../configurations.txt')
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Check data source setting
    data_source = config.get('DataSource', 'SOURCE')
    print(f"📊 Data source: {data_source}")
    
    # Check data files
    if data_source.lower() == 'spotify':
        spotify_file = config.get('DataSource', 'INPUT_FILENAME_SPOTIFY')
        spotify_path = f'../{spotify_file}'
        
        print(f"🔍 Looking for Spotify file: {spotify_file}")
        
        if os.path.exists(spotify_path):
            print(f"✅ Spotify data file found: {spotify_file}")
            
            # Check file contents
            try:
                with open(spotify_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ File is valid JSON with {len(data)} entries")
                
                # Show sample entry
                if data:
                    sample = data[0]
                    print(f"📋 Sample entry keys: {list(sample.keys())}")
                    
            except Exception as e:
                print(f"❌ Error reading Spotify file: {e}")
                return False
                
        else:
            print(f"❌ Spotify data file not found: {spotify_path}")
            print("Available .json files in main directory:")
            
            json_files = [f for f in os.listdir('..') if f.endswith('.json')]
            if json_files:
                for f in json_files:
                    print(f"   - {f}")
                print(f"💡 Update INPUT_FILENAME_SPOTIFY in configurations.txt")
            else:
                print("   No .json files found")
            return False
            
    elif data_source.lower() == 'lastfm':
        lastfm_file = config.get('DataSource', 'INPUT_FILENAME_LASTFM')
        lastfm_path = f'../{lastfm_file}'
        
        print(f"🔍 Looking for Last.fm file: {lastfm_file}")
        
        if os.path.exists(lastfm_path):
            print(f"✅ Last.fm data file found: {lastfm_file}")
            
            # Check file contents
            try:
                import pandas as pd
                df = pd.read_csv(lastfm_path, encoding='utf-8')
                print(f"✅ File is valid CSV with {len(df)} entries")
                print(f"📋 Columns: {list(df.columns)}")
                
            except Exception as e:
                print(f"❌ Error reading Last.fm file: {e}")
                return False
                
        else:
            print(f"❌ Last.fm data file not found: {lastfm_path}")
            print("Available .csv files in main directory:")
            
            csv_files = [f for f in os.listdir('..') if f.endswith('.csv')]
            if csv_files:
                for f in csv_files:
                    print(f"   - {f}")
                print(f"💡 Update INPUT_FILENAME_LASTFM in configurations.txt")
            else:
                print("   No .csv files found")
            return False
    
    else:
        print(f"❌ Unknown data source: {data_source}")
        print("Valid options: 'spotify' or 'lastfm'")
        return False
    
    # Try to load data
    print("\n🔄 Testing data loading...")
    try:
        df = clean_and_filter_data(config)
        
        if df is None or df.empty:
            print("❌ Data loading returned empty result")
            return False
            
        print(f"✅ Data loaded successfully: {len(df)} rows")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Check for artist column
        if 'artist' in df.columns:
            unique_artists = df['artist'].nunique()
            print(f"🎵 Found {unique_artists} unique artists")
            
            # Show top 5 artists
            top_artists = df.groupby('artist').size().sort_values(ascending=False).head(5)
            print("\n🏆 Top 5 artists:")
            for i, (artist, plays) in enumerate(top_artists.items(), 1):
                print(f"   {i}. {artist} ({plays} plays)")
        else:
            print("❌ No 'artist' column found in data")
            return False
            
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return False
    
    print("\n✅ Data setup is working correctly!")
    return True


def suggest_fixes():
    """Suggest fixes for common issues."""
    print("\n🔧 Common fixes:")
    print("1. Make sure data files are in the main directory (not tests/)")
    print("2. Check file names in configurations.txt match actual files")
    print("3. For Spotify: file should be JSON format")
    print("4. For Last.fm: file should be CSV format with UTF-8 encoding")
    print("5. Run tests from the main directory: python tests/script_name.py")


if __name__ == "__main__":
    success = check_data_setup()
    
    if not success:
        suggest_fixes()
        sys.exit(1)
    else:
        print("\n🎉 Ready to run Last.fm tests!")
        print("Try: python manual_test_lastfm.py")