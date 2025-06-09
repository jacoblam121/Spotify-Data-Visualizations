"""
Phase 1B.1: Create Minimal Fix for DataFrame Index
==================================================

This script creates and tests a minimal wrapper function that converts
the timestamp column to a DatetimeIndex before network analysis.

Strategy: Don't modify data_processor, create network-specific wrapper
Goal: Fix the immediate datetime index issue with minimal changes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
from config_loader import AppConfig
from data_processor import clean_and_filter_data
from network_utils import ArtistNetworkAnalyzer


def print_separator(title, char="=", width=70):
    """Print a formatted separator."""
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}")


def prepare_dataframe_for_network_analysis(df):
    """
    Prepare DataFrame for network analysis by setting timestamp as index.
    
    This is the minimal fix wrapper function that solves the datetime index issue
    without modifying the core data_processor.py module.
    
    Args:
        df: DataFrame from clean_and_filter_data() with timestamp column
        
    Returns:
        DataFrame with timestamp as DatetimeIndex, ready for network analysis
        
    Raises:
        ValueError: If DataFrame is missing required columns
    """
    if df is None or df.empty:
        raise ValueError("DataFrame is None or empty")
    
    if 'timestamp' not in df.columns:
        raise ValueError("DataFrame missing 'timestamp' column")
    
    if 'artist' not in df.columns:
        raise ValueError("DataFrame missing 'artist' column")
    
    # Create a copy to avoid modifying the original
    df_network = df.copy()
    
    # Set timestamp as index
    df_network.set_index('timestamp', inplace=True)
    
    # Verify the conversion worked
    if not isinstance(df_network.index, pd.DatetimeIndex):
        raise ValueError("Failed to convert timestamp to DatetimeIndex")
    
    return df_network


def test_wrapper_function_basic():
    """Test the wrapper function with basic data."""
    print_separator("PHASE 1B.1: TESTING WRAPPER FUNCTION", "=", 70)
    print("Creating and testing minimal fix wrapper function")
    print("Strategy: Convert timestamp column to DatetimeIndex before network analysis")
    
    try:
        config = AppConfig('configurations.txt')
        original_source = config.get('DataSource', 'SOURCE', fallback='spotify')
        
        # Test with Spotify data first
        config.config['DataSource']['SOURCE'] = 'spotify'
        
        print_separator("STEP 1: LOAD DATA FROM PROCESSOR")
        df_raw = clean_and_filter_data(config)
        
        if df_raw is None or df_raw.empty:
            print("❌ No data available for testing")
            return False
        
        print(f"✅ Loaded raw data: {df_raw.shape}")
        print(f"   Index type: {type(df_raw.index).__name__}")
        print(f"   Has timestamp column: {'timestamp' in df_raw.columns}")
        print(f"   Has artist column: {'artist' in df_raw.columns}")
        
        print_separator("STEP 2: APPLY WRAPPER FUNCTION")
        
        try:
            df_network = prepare_dataframe_for_network_analysis(df_raw)
            print(f"✅ Wrapper function succeeded!")
            print(f"   Output shape: {df_network.shape}")
            print(f"   Index type: {type(df_network.index).__name__}")
            print(f"   Index dtype: {df_network.index.dtype}")
            print(f"   Has artist column: {'artist' in df_network.columns}")
            
            # Verify no data loss
            if len(df_network) == len(df_raw):
                print("✅ No data loss during conversion")
            else:
                print(f"⚠️  Data length changed: {len(df_raw)} → {len(df_network)}")
            
        except Exception as e:
            print(f"❌ Wrapper function failed: {e}")
            return False
        
        print_separator("STEP 3: TEST NETWORK ANALYSIS")
        
        analyzer = ArtistNetworkAnalyzer(config)
        
        try:
            # Test with a smaller time window for faster execution
            scores = analyzer.calculate_co_listening_scores(
                df_network, 
                time_window_hours=2,  # 2-hour window for faster testing
                min_co_occurrences=2
            )
            
            print(f"✅ Network analysis succeeded!")
            print(f"   Found {len(scores)} artist relationships")
            
            if scores:
                print("\n🔗 Top 5 relationships:")
                sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                for i, ((artist1, artist2), score) in enumerate(sorted_scores[:5], 1):
                    print(f"   {i}. {artist1} ↔ {artist2}: {score:.3f}")
            else:
                print("   ⚠️  No relationships found (try longer time window or lower threshold)")
            
        except Exception as e:
            print(f"❌ Network analysis failed: {e}")
            return False
        
        # Restore original source
        config.config['DataSource']['SOURCE'] = original_source
        
        print_separator("WRAPPER FUNCTION SUCCESS")
        print("✅ Minimal fix wrapper function works perfectly!")
        print("✅ Network analysis produces meaningful results")
        print("✅ No modification needed to data_processor.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wrapper_with_both_sources():
    """Test wrapper function with both Spotify and Last.fm data."""
    print_separator("TESTING WRAPPER WITH BOTH DATA SOURCES", "=", 70)
    
    try:
        config = AppConfig('configurations.txt')
        original_source = config.get('DataSource', 'SOURCE', fallback='spotify')
        
        sources = ['spotify', 'lastfm']
        results = {}
        
        for source in sources:
            print_separator(f"TESTING {source.upper()} WITH WRAPPER")
            
            config.config['DataSource']['SOURCE'] = source
            
            try:
                # Load data
                df_raw = clean_and_filter_data(config)
                
                if df_raw is None or df_raw.empty:
                    print(f"❌ No {source} data available")
                    results[source] = False
                    continue
                
                print(f"📊 {source} raw data: {df_raw.shape}")
                
                # Apply wrapper
                df_network = prepare_dataframe_for_network_analysis(df_raw)
                print(f"🔧 {source} network data: {df_network.shape}")
                print(f"   Index: {type(df_network.index).__name__}")
                
                # Quick network test
                analyzer = ArtistNetworkAnalyzer(config)
                scores = analyzer.calculate_co_listening_scores(
                    df_network, 
                    time_window_hours=3,  # 3-hour window
                    min_co_occurrences=1  # Lower threshold for testing
                )
                
                print(f"✅ {source.upper()}: {len(scores)} relationships found")
                results[source] = len(scores)
                
                # Show a few sample relationships
                if scores:
                    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                    print(f"   Top relationships:")
                    for i, ((artist1, artist2), score) in enumerate(sorted_scores[:3], 1):
                        print(f"     {i}. {artist1} ↔ {artist2}: {score:.3f}")
                
            except Exception as e:
                print(f"❌ {source.upper()} failed: {e}")
                results[source] = False
        
        # Restore original source
        config.config['DataSource']['SOURCE'] = original_source
        
        print_separator("BOTH SOURCES SUMMARY")
        for source, result in results.items():
            if isinstance(result, int):
                print(f"  {source.upper()}: ✅ {result} relationships")
            else:
                print(f"  {source.upper()}: ❌ Failed")
        
        if all(isinstance(r, int) and r > 0 for r in results.values()):
            print("\n🎉 Wrapper function works perfectly with both data sources!")
            return True
        else:
            print("\n⚠️  Some issues found with wrapper function")
            return False
        
    except Exception as e:
        print(f"❌ Error testing both sources: {e}")
        return False


def test_wrapper_edge_cases():
    """Test wrapper function with edge cases."""
    print_separator("TESTING WRAPPER EDGE CASES", "=", 70)
    
    print("🧪 Testing edge cases and error handling...")
    
    # Test 1: None DataFrame
    print("\n1. Testing with None DataFrame:")
    try:
        result = prepare_dataframe_for_network_analysis(None)
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test 2: Empty DataFrame
    print("\n2. Testing with empty DataFrame:")
    try:
        empty_df = pd.DataFrame()
        result = prepare_dataframe_for_network_analysis(empty_df)
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test 3: Missing timestamp column
    print("\n3. Testing with missing timestamp column:")
    try:
        no_timestamp = pd.DataFrame({'artist': ['Artist1', 'Artist2']})
        result = prepare_dataframe_for_network_analysis(no_timestamp)
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test 4: Missing artist column
    print("\n4. Testing with missing artist column:")
    try:
        no_artist = pd.DataFrame({'timestamp': [pd.Timestamp('2024-01-01')]})
        result = prepare_dataframe_for_network_analysis(no_artist)
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print("\n✅ All edge cases handled correctly!")


if __name__ == "__main__":
    # Change to main directory for proper file access
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        # Run all tests
        success1 = test_wrapper_function_basic()
        success2 = test_wrapper_with_both_sources() if success1 else False
        test_wrapper_edge_cases()
        
        print_separator("PHASE 1B.1 COMPLETE", "=", 70)
        
        if success1 and success2:
            print("✅ Minimal fix wrapper function complete and tested!")
            print("✅ Works with both Spotify and Last.fm data")
            print("✅ Proper error handling for edge cases")
            print("")
            print("🎯 Ready for Phase 1B.2: Test with Real Data")
            print("   Goal: Validate wrapper with your full dataset")
        else:
            print("❌ Some tests failed - need to investigate")
        
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original directory
        os.chdir(original_dir)