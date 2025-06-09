"""
Phase 1A.1: Data Structure Diagnostic Script
============================================

This script examines the DataFrame structure from clean_and_filter_data()
to understand exactly what data network_utils receives and identify the
datetime index issue.

Goal: Understand current data flow and identify the exact problem
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import json
from datetime import datetime
from config_loader import AppConfig
from data_processor import clean_and_filter_data


def print_separator(title, char="=", width=70):
    """Print a formatted separator."""
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}")


def analyze_dataframe_structure(df, source_name):
    """Analyze and report DataFrame structure in detail."""
    print_separator(f"ANALYZING {source_name.upper()} DATA STRUCTURE")
    
    if df is None:
        print("❌ DataFrame is None")
        return False
    
    if df.empty:
        print("❌ DataFrame is empty")
        return False
    
    print(f"✅ DataFrame loaded successfully")
    print(f"📊 Shape: {df.shape} (rows: {df.shape[0]}, columns: {df.shape[1]})")
    
    # Check index
    print_separator("INDEX ANALYSIS", "-", 50)
    print(f"Index type: {type(df.index).__name__}")
    print(f"Index name: {df.index.name}")
    print(f"Index dtype: {df.index.dtype}")
    
    if isinstance(df.index, pd.DatetimeIndex):
        print("✅ Index IS a DatetimeIndex")
        print(f"   Timezone: {df.index.tz}")
        print(f"   Date range: {df.index.min()} to {df.index.max()}")
    else:
        print("❌ Index is NOT a DatetimeIndex")
        print(f"   First few index values: {df.index[:5].tolist()}")
    
    # Check columns
    print_separator("COLUMN ANALYSIS", "-", 50)
    print(f"Columns: {list(df.columns)}")
    print(f"Column count: {len(df.columns)}")
    
    for col in df.columns:
        dtype = df[col].dtype
        null_count = df[col].isnull().sum()
        unique_count = df[col].nunique()
        print(f"  {col}:")
        print(f"    - Type: {dtype}")
        print(f"    - Nulls: {null_count}")
        print(f"    - Unique values: {unique_count}")
        
        # Show sample values
        if col == 'timestamp' or 'time' in col.lower():
            print(f"    - Sample values: {df[col].head(3).tolist()}")
        elif col == 'artist':
            print(f"    - Sample artists: {df[col].head(3).tolist()}")
        elif unique_count <= 10:
            print(f"    - All values: {df[col].unique().tolist()}")
        else:
            print(f"    - Sample values: {df[col].head(3).tolist()}")
    
    # Check for timestamp-related columns
    print_separator("TIMESTAMP COLUMN SEARCH", "-", 50)
    timestamp_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
    if timestamp_cols:
        print(f"Found timestamp-related columns: {timestamp_cols}")
        for col in timestamp_cols:
            print(f"  {col}: {df[col].dtype} - Sample: {df[col].iloc[0]}")
    else:
        print("❌ No timestamp-related columns found")
    
    # Check for required network analysis columns
    print_separator("NETWORK ANALYSIS REQUIREMENTS", "-", 50)
    required_cols = ['artist']
    optional_cols = ['timestamp', 'track', 'album']
    
    for col in required_cols:
        if col in df.columns:
            print(f"✅ Required column '{col}' present")
        else:
            print(f"❌ Required column '{col}' MISSING")
    
    for col in optional_cols:
        if col in df.columns:
            print(f"✅ Optional column '{col}' present")
        else:
            print(f"⚠️  Optional column '{col}' missing")
    
    # Data sample
    print_separator("DATA SAMPLE", "-", 50)
    print("First 5 rows:")
    print(df.head().to_string())
    
    print(f"\nLast 5 rows:")
    print(df.tail().to_string())
    
    # Summary for network analysis compatibility
    print_separator("NETWORK ANALYSIS COMPATIBILITY", "-", 50)
    has_datetime_index = isinstance(df.index, pd.DatetimeIndex)
    has_artist_column = 'artist' in df.columns
    has_timestamp_column = 'timestamp' in df.columns
    
    print(f"DateTime Index: {'✅ YES' if has_datetime_index else '❌ NO'}")
    print(f"Artist Column: {'✅ YES' if has_artist_column else '❌ NO'}")
    print(f"Timestamp Column: {'✅ YES' if has_timestamp_column else '❌ NO'}")
    
    if has_datetime_index and has_artist_column:
        print("✅ READY for network analysis")
        return True
    elif has_timestamp_column and has_artist_column:
        print("⚠️  NEEDS index conversion (timestamp column → index)")
        return "needs_conversion"
    else:
        print("❌ NOT READY for network analysis")
        return False


def test_data_sources():
    """Test both Spotify and Last.fm data sources."""
    print_separator("PHASE 1A.1: DATA STRUCTURE DIAGNOSTIC", "=", 70)
    print("Examining DataFrame structure from clean_and_filter_data()")
    print("This will help us understand the datetime index issue.")
    
    try:
        # Load configuration
        config = AppConfig('configurations.txt')
        print(f"✅ Loaded configuration from configurations.txt")
        
        # Store original source
        original_source = config.get('DataSource', 'SOURCE', fallback='spotify')
        print(f"📋 Original data source: {original_source}")
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return
    
    results = {}
    
    # Test Spotify data
    print_separator("TESTING SPOTIFY DATA SOURCE")
    try:
        config.config['DataSource']['SOURCE'] = 'spotify'
        print("🔄 Loading Spotify data...")
        
        spotify_df = clean_and_filter_data(config)
        results['spotify'] = analyze_dataframe_structure(spotify_df, "Spotify")
        
    except Exception as e:
        print(f"❌ Error processing Spotify data: {e}")
        results['spotify'] = False
    
    # Test Last.fm data
    print_separator("TESTING LAST.FM DATA SOURCE")
    try:
        config.config['DataSource']['SOURCE'] = 'lastfm'
        print("🔄 Loading Last.fm data...")
        
        lastfm_df = clean_and_filter_data(config)
        results['lastfm'] = analyze_dataframe_structure(lastfm_df, "Last.fm")
        
    except Exception as e:
        print(f"❌ Error processing Last.fm data: {e}")
        results['lastfm'] = False
    
    # Restore original source
    config.config['DataSource']['SOURCE'] = original_source
    
    # Summary and recommendations
    print_separator("DIAGNOSTIC SUMMARY & RECOMMENDATIONS", "=", 70)
    
    print("📋 Results Summary:")
    for source, result in results.items():
        if result is True:
            print(f"  {source}: ✅ Ready for network analysis")
        elif result == "needs_conversion":
            print(f"  {source}: ⚠️  Needs timestamp → index conversion")
        else:
            print(f"  {source}: ❌ Has issues or unavailable")
    
    print("\n💡 Recommendations:")
    
    if any(result == "needs_conversion" for result in results.values()):
        print("  1. 🔧 Create wrapper function to set timestamp as DataFrame index")
        print("     - Convert timestamp column to DatetimeIndex before network analysis")
        print("     - Keep original data_processor unchanged to avoid breaking existing code")
        print("  2. 🧪 Test with network_utils after conversion")
    
    if any(result is True for result in results.values()):
        print("  3. ✅ Some data is already ready - proceed with network analysis")
    
    if not any(result for result in results.values()):
        print("  1. ❌ Investigate data loading issues")
        print("  2. 🔍 Check file paths and data formats")
        print("  3. 📝 Verify configuration settings")
    
    print(f"\n🎯 Next Phase: 1A.2 - Trace Network Analysis Entry Point")
    print(f"   Goal: See exactly what network_utils receives and where it fails")


def detailed_timestamp_analysis():
    """Perform detailed analysis of timestamp handling."""
    print_separator("DETAILED TIMESTAMP ANALYSIS", "=", 70)
    
    try:
        config = AppConfig('configurations.txt')
        config.config['DataSource']['SOURCE'] = 'spotify'  # Focus on Spotify for now
        
        df = clean_and_filter_data(config)
        
        if df is None or df.empty:
            print("❌ No data to analyze")
            return
        
        print("🔍 Analyzing timestamp handling in detail...")
        
        # Check if timestamp column exists
        if 'timestamp' in df.columns:
            print("✅ Timestamp column found")
            ts_col = df['timestamp']
            print(f"   Type: {ts_col.dtype}")
            print(f"   Sample: {ts_col.iloc[0]} (type: {type(ts_col.iloc[0])})")
            
            # Check if it's timezone-aware
            if hasattr(ts_col.iloc[0], 'tz') and ts_col.iloc[0].tz is not None:
                print(f"   Timezone: {ts_col.iloc[0].tz}")
            else:
                print("   Timezone: None (timezone-naive)")
            
            # Try converting to index
            print("\n🔄 Testing index conversion...")
            try:
                df_copy = df.copy()
                df_copy.set_index('timestamp', inplace=True)
                print("✅ Successfully converted timestamp to index")
                print(f"   New index type: {type(df_copy.index).__name__}")
                print(f"   Index dtype: {df_copy.index.dtype}")
                
                # Test if this would work with network analysis
                if isinstance(df_copy.index, pd.DatetimeIndex) and 'artist' in df_copy.columns:
                    print("✅ Converted DataFrame would work with network analysis!")
                else:
                    print("❌ Converted DataFrame still has issues")
                    
            except Exception as e:
                print(f"❌ Failed to convert timestamp to index: {e}")
        else:
            print("❌ No timestamp column found")
        
        # Check current index
        print(f"\n📋 Current Index Analysis:")
        print(f"   Type: {type(df.index).__name__}")
        print(f"   Dtype: {df.index.dtype}")
        print(f"   Sample: {df.index[:3].tolist()}")
        
    except Exception as e:
        print(f"❌ Error in timestamp analysis: {e}")


if __name__ == "__main__":
    # Change to main directory for proper file access
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        test_data_sources()
        detailed_timestamp_analysis()
        
        print_separator("PHASE 1A.1 COMPLETE", "=", 70)
        print("✅ Diagnostic complete!")
        print("📄 Review the output above to understand your data structure")
        print("🔄 Next: Run Phase 1A.2 to trace network analysis entry point")
        
    except KeyboardInterrupt:
        print("\n🛑 Diagnostic interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original directory
        os.chdir(original_dir)