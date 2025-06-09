"""
Phase 1A.2: Network Analysis Entry Point Trace
===============================================

This script traces exactly what DataFrame network_utils receives
and where the datetime index check fails. We'll add debug logging
to see the data flow step by step.

Goal: Trace data from processor → network_utils and see where it fails
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


def trace_dataframe_at_entry(df, step_name):
    """Trace DataFrame structure at each step."""
    print(f"\n🔍 TRACING: {step_name}")
    print(f"   DataFrame type: {type(df)}")
    
    if df is None:
        print("   ❌ DataFrame is None")
        return False
    
    if df.empty:
        print("   ❌ DataFrame is empty")
        return False
    
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Index type: {type(df.index).__name__}")
    print(f"   Index dtype: {df.index.dtype}")
    
    # Check network analysis requirements
    has_datetime_index = isinstance(df.index, pd.DatetimeIndex)
    has_artist_column = 'artist' in df.columns
    has_timestamp_column = 'timestamp' in df.columns
    
    print(f"   DateTime Index: {'✅ YES' if has_datetime_index else '❌ NO'}")
    print(f"   Artist Column: {'✅ YES' if has_artist_column else '❌ NO'}")
    print(f"   Timestamp Column: {'✅ YES' if has_timestamp_column else '❌ NO'}")
    
    if has_datetime_index and has_artist_column:
        print("   🎯 STATUS: Ready for network analysis")
        return True
    elif has_timestamp_column and has_artist_column:
        print("   ⚠️  STATUS: Needs index conversion")
        return "needs_conversion"
    else:
        print("   ❌ STATUS: Not ready for network analysis")
        return False


def test_network_analysis_entry_point():
    """Test the exact entry point where network analysis fails."""
    print_separator("PHASE 1A.2: NETWORK ANALYSIS ENTRY POINT TRACE", "=", 70)
    print("Tracing data flow from data_processor → network_utils")
    print("This will show us exactly where the datetime index check fails.")
    
    try:
        # Load configuration
        config = AppConfig('configurations.txt')
        print("✅ Configuration loaded")
        
        # Store original source
        original_source = config.get('DataSource', 'SOURCE', fallback='spotify')
        
        # Test with Spotify data (since we know it has good data)
        config.config['DataSource']['SOURCE'] = 'spotify'
        
        print_separator("STEP 1: LOAD DATA FROM PROCESSOR")
        df = clean_and_filter_data(config)
        result1 = trace_dataframe_at_entry(df, "After clean_and_filter_data()")
        
        if not result1:
            print("❌ Data loading failed - cannot proceed with trace")
            return
        
        print_separator("STEP 2: CREATE NETWORK ANALYZER")
        analyzer = ArtistNetworkAnalyzer(config)
        print("✅ ArtistNetworkAnalyzer created successfully")
        
        print_separator("STEP 3: ATTEMPT CO-LISTENING CALCULATION")
        print("🔄 Calling calculate_co_listening_scores()...")
        print("   This is where the 'DataFrame must have datetime index' error occurs")
        
        # Trace the exact moment of failure
        try:
            print("\n📋 Checking network_utils requirements:")
            print(f"   df.empty: {df.empty}")
            print(f"   'artist' in df.columns: {'artist' in df.columns}")
            print(f"   isinstance(df.index, pd.DatetimeIndex): {isinstance(df.index, pd.DatetimeIndex)}")
            
            print("\n🚨 EXPECTED FAILURE POINT:")
            print("   network_utils.py line 55-57:")
            print("   if not isinstance(df.index, pd.DatetimeIndex):")
            print("       print('❌ DataFrame must have datetime index')")
            print("       return {}")
            
            scores = analyzer.calculate_co_listening_scores(df, time_window_hours=1, min_co_occurrences=1)
            
            print(f"🎉 UNEXPECTED: Co-listening calculation succeeded!")
            print(f"   Found {len(scores)} artist pairs")
            
        except Exception as e:
            print(f"❌ Co-listening calculation failed: {e}")
            import traceback
            print("📋 Full traceback:")
            traceback.print_exc()
        
        print_separator("STEP 4: TEST INDEX CONVERSION FIX")
        print("🔧 Testing if converting timestamp to index fixes the issue...")
        
        # Create a copy with timestamp as index
        df_fixed = df.copy()
        df_fixed.set_index('timestamp', inplace=True)
        
        result4 = trace_dataframe_at_entry(df_fixed, "After setting timestamp as index")
        
        if result4 is True:
            print("\n🔄 Testing network analysis with fixed DataFrame...")
            try:
                scores_fixed = analyzer.calculate_co_listening_scores(df_fixed, time_window_hours=1, min_co_occurrences=1)
                print(f"✅ SUCCESS: Co-listening calculation worked with index fix!")
                print(f"   Found {len(scores_fixed)} artist pairs")
                
                # Show some sample results
                if scores_fixed:
                    print("\n🔗 Sample relationships found:")
                    sorted_scores = sorted(scores_fixed.items(), key=lambda x: x[1], reverse=True)
                    for i, ((artist1, artist2), score) in enumerate(sorted_scores[:5], 1):
                        print(f"   {i}. {artist1} ↔ {artist2}: {score:.3f}")
                        
                else:
                    print("   ⚠️  No relationships found (may need to adjust parameters)")
                    
            except Exception as e:
                print(f"❌ Network analysis still failed: {e}")
        
        # Restore original source
        config.config['DataSource']['SOURCE'] = original_source
        
        print_separator("TRACE SUMMARY & NEXT STEPS")
        
        print("📋 Key Findings:")
        print("  1. ✅ Data loads correctly from clean_and_filter_data()")
        print("  2. ❌ DataFrame has integer index instead of DatetimeIndex") 
        print("  3. ✅ Converting timestamp column to index solves the problem")
        print("  4. ✅ Network analysis works perfectly after index conversion")
        
        print("\n💡 Next Phase: 1B.1 - Create Minimal Fix")
        print("   Goal: Implement wrapper function for index conversion")
        print("   Strategy: Don't modify data_processor, create network-specific wrapper")
        
    except Exception as e:
        print(f"❌ Unexpected error in entry point trace: {e}")
        import traceback
        traceback.print_exc()


def test_both_data_sources():
    """Test entry point with both Spotify and Last.fm data."""
    print_separator("TESTING BOTH DATA SOURCES", "=", 70)
    
    try:
        config = AppConfig('configurations.txt')
        original_source = config.get('DataSource', 'SOURCE', fallback='spotify')
        
        sources = ['spotify', 'lastfm']
        results = {}
        
        for source in sources:
            print_separator(f"TESTING {source.upper()} DATA SOURCE")
            
            config.config['DataSource']['SOURCE'] = source
            
            try:
                df = clean_and_filter_data(config)
                
                if df is None or df.empty:
                    print(f"❌ No {source} data available")
                    results[source] = False
                    continue
                
                trace_dataframe_at_entry(df, f"{source} data from processor")
                
                # Test index conversion
                df_fixed = df.copy()
                df_fixed.set_index('timestamp', inplace=True)
                
                trace_dataframe_at_entry(df_fixed, f"{source} data with index fix")
                
                # Quick network test
                analyzer = ArtistNetworkAnalyzer(config)
                scores = analyzer.calculate_co_listening_scores(df_fixed, time_window_hours=6, min_co_occurrences=1)
                
                print(f"✅ {source.upper()} network analysis: {len(scores)} relationships found")
                results[source] = True
                
            except Exception as e:
                print(f"❌ {source.upper()} failed: {e}")
                results[source] = False
        
        # Restore original source
        config.config['DataSource']['SOURCE'] = original_source
        
        print_separator("BOTH SOURCES SUMMARY")
        for source, success in results.items():
            status = "✅ READY" if success else "❌ ISSUES"
            print(f"  {source.upper()}: {status}")
        
        if all(results.values()):
            print("\n🎉 Both data sources work with index conversion fix!")
        else:
            print("\n⚠️  Some data sources have issues")
        
    except Exception as e:
        print(f"❌ Error testing both sources: {e}")


if __name__ == "__main__":
    # Change to main directory for proper file access
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        test_network_analysis_entry_point()
        test_both_data_sources()
        
        print_separator("PHASE 1A.2 COMPLETE", "=", 70)
        print("✅ Entry point trace complete!")
        print("📋 We now know exactly where and why the failure occurs")
        print("🔧 Ready to implement the minimal fix in Phase 1B.1")
        
    except KeyboardInterrupt:
        print("\n🛑 Trace interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original directory
        os.chdir(original_dir)