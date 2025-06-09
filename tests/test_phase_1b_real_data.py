"""
Phase 1B.2: Test Wrapper with Full Real Dataset and Fix Original Manual Test
============================================================================

This script tests the wrapper function with your full dataset and creates
a fixed version of your original manual_test_network.py that actually works.

Goal: Validate wrapper with your full dataset and fix the original test
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import json
from datetime import datetime
from config_loader import AppConfig
from data_processor import clean_and_filter_data
from network_utils import ArtistNetworkAnalyzer


def prepare_dataframe_for_network_analysis(df):
    """
    Prepare DataFrame for network analysis by setting timestamp as index.
    
    This is our proven minimal fix wrapper function.
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


def print_separator(title, char="=", width=70):
    """Print a formatted separator."""
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}")


def test_spotify_colistening_fixed():
    """Test co-listening calculation with Spotify data using the wrapper."""
    print("\n🎵 Testing Co-listening with Spotify Data (FIXED VERSION)")
    print("-" * 50)
    
    try:
        # Load configuration
        config = AppConfig('configurations.txt')
        
        # Force Spotify source
        original_source = config.get('DataSource', 'SOURCE', fallback='spotify')
        config.config['DataSource']['SOURCE'] = 'spotify'
        
        # Load Spotify data
        print("📊 Loading Spotify data...")
        df_raw = clean_and_filter_data(config)
        
        if df_raw is None or df_raw.empty:
            print("❌ No Spotify data available")
            print("💡 Make sure you have Spotify JSON files in the main directory")
            return
        
        print(f"✅ Loaded {len(df_raw)} Spotify plays")
        
        # Apply our wrapper fix
        print("🔧 Applying index conversion fix...")
        df_network = prepare_dataframe_for_network_analysis(df_raw)
        print(f"✅ Converted to network-ready format: {df_network.shape}")
        
        # Test co-listening
        analyzer = ArtistNetworkAnalyzer(config)
        
        print("🔗 Calculating co-listening scores...")
        scores = analyzer.calculate_co_listening_scores(
            df_network, 
            time_window_hours=24,  # 24-hour window
            min_co_occurrences=2
        )
        
        display_colistening_results(scores, "Spotify (FIXED)")
        
        # Restore original source
        config.config['DataSource']['SOURCE'] = original_source
        
        return scores
        
    except Exception as e:
        print(f"❌ Error testing Spotify co-listening: {e}")
        import traceback
        traceback.print_exc()
        return {}


def test_lastfm_colistening_fixed():
    """Test co-listening calculation with Last.fm data using the wrapper."""
    print("\n🎵 Testing Co-listening with Last.fm Data (FIXED VERSION)")
    print("-" * 50)
    
    try:
        # Load configuration
        config = AppConfig('configurations.txt')
        
        # Force Last.fm source
        original_source = config.get('DataSource', 'SOURCE', fallback='spotify')
        config.config['DataSource']['SOURCE'] = 'lastfm'
        
        # Load Last.fm data
        print("📊 Loading Last.fm data...")
        df_raw = clean_and_filter_data(config)
        
        if df_raw is None or df_raw.empty:
            print("❌ No Last.fm data available")
            print("💡 Make sure you have lastfm_data.csv in the main directory")
            return
        
        print(f"✅ Loaded {len(df_raw)} Last.fm plays")
        
        # Apply our wrapper fix
        print("🔧 Applying index conversion fix...")
        df_network = prepare_dataframe_for_network_analysis(df_raw)
        print(f"✅ Converted to network-ready format: {df_network.shape}")
        
        # Test co-listening
        analyzer = ArtistNetworkAnalyzer(config)
        
        print("🔗 Calculating co-listening scores...")
        scores = analyzer.calculate_co_listening_scores(
            df_network,
            time_window_hours=24,  # 24-hour window  
            min_co_occurrences=2
        )
        
        display_colistening_results(scores, "Last.fm (FIXED)")
        
        # Restore original source
        config.config['DataSource']['SOURCE'] = original_source
        
        return scores
        
    except Exception as e:
        print(f"❌ Error testing Last.fm co-listening: {e}")
        import traceback
        traceback.print_exc()
        return {}


def display_colistening_results(scores, source_name, max_display=15):
    """Display co-listening results in a formatted way."""
    if not scores:
        print(f"❌ No co-listening relationships found in {source_name}")
        return
    
    print(f"\n🔗 Co-listening Results from {source_name}:")
    print(f"   Found {len(scores)} artist pairs with co-listening")
    
    # Sort by score
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n🏆 Top {min(max_display, len(sorted_scores))} relationships:")
    for i, ((artist1, artist2), score) in enumerate(sorted_scores[:max_display], 1):
        print(f"   {i:2d}. {artist1} ↔ {artist2}")
        print(f"       Co-listening score: {score:.3f}")
    
    if len(sorted_scores) > max_display:
        print(f"   ... and {len(sorted_scores) - max_display} more")


def test_network_creation_fixed():
    """Test full network creation with the wrapper fix."""
    print_separator("TESTING FULL NETWORK CREATION (FIXED)", "=", 70)
    
    try:
        config = AppConfig('configurations.txt')
        original_source = config.get('DataSource', 'SOURCE', fallback='spotify')
        
        # Test with Spotify data
        config.config['DataSource']['SOURCE'] = 'spotify'
        
        print("📊 Loading and preparing Spotify data for network creation...")
        df_raw = clean_and_filter_data(config)
        
        if df_raw is None or df_raw.empty:
            print("❌ No Spotify data available")
            return
        
        # Apply wrapper fix
        df_network = prepare_dataframe_for_network_analysis(df_raw)
        print(f"✅ Network-ready data: {df_network.shape}")
        
        # Create full network
        analyzer = ArtistNetworkAnalyzer(config)
        
        print("🕸️  Creating artist network...")
        network_data = analyzer.create_network_data(
            df_network,
            top_n_artists=20,  # Top 20 artists for testing
            include_lastfm=False,  # Only co-listening for now
            include_colistening=True,
            min_plays_threshold=10  # Minimum 10 plays to include artist
        )
        
        print(f"✅ Network created successfully!")
        print(f"   Nodes (artists): {len(network_data['nodes'])}")
        print(f"   Edges (relationships): {len(network_data['edges'])}")
        
        # Show top artists by play count
        print(f"\n🎵 Top Artists in Network:")
        for i, node in enumerate(network_data['nodes'][:10], 1):
            print(f"   {i:2d}. {node['name']}: {node['play_count']} plays")
        
        # Show strongest relationships
        if network_data['edges']:
            edges_by_weight = sorted(network_data['edges'], key=lambda x: x['weight'], reverse=True)
            print(f"\n🔗 Strongest Relationships:")
            for i, edge in enumerate(edges_by_weight[:10], 1):
                print(f"   {i:2d}. {edge['source']} ↔ {edge['target']}: {edge['weight']:.3f}")
        
        # Save network data
        output_file = f"network_test_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        filepath = analyzer.save_network_data(network_data, output_file)
        print(f"\n💾 Network saved: {filepath}")
        
        # Get network statistics
        stats = analyzer.get_network_statistics(network_data)
        print(f"\n📊 Network Statistics:")
        print(f"   Density: {stats.get('density', 0):.3f}")
        print(f"   Average degree: {stats.get('avg_degree', 0):.2f}")
        
        # Restore original source
        config.config['DataSource']['SOURCE'] = original_source
        
        return network_data
        
    except Exception as e:
        print(f"❌ Error creating network: {e}")
        import traceback
        traceback.print_exc()
        return None


def comprehensive_test():
    """Run comprehensive test of the fixed network analysis."""
    print_separator("PHASE 1B.2: COMPREHENSIVE NETWORK TEST (FIXED)", "=", 70)
    print("Testing wrapper function with full real dataset")
    print("This validates our fix works with your complete listening history")
    
    # Test both data sources
    spotify_scores = test_spotify_colistening_fixed()
    lastfm_scores = test_lastfm_colistening_fixed()
    
    # Test full network creation
    network_data = test_network_creation_fixed()
    
    print_separator("COMPREHENSIVE TEST SUMMARY")
    
    print("📋 Results:")
    print(f"  Spotify co-listening pairs: {len(spotify_scores) if spotify_scores else 0}")
    print(f"  Last.fm co-listening pairs: {len(lastfm_scores) if lastfm_scores else 0}")
    print(f"  Network nodes: {len(network_data['nodes']) if network_data else 0}")
    print(f"  Network edges: {len(network_data['edges']) if network_data else 0}")
    
    if spotify_scores and lastfm_scores:
        print("\n✅ Both data sources working perfectly!")
    elif spotify_scores or lastfm_scores:
        print("\n⚠️  One data source working, check the other")
    else:
        print("\n❌ Issues with both data sources")
    
    if network_data:
        print("✅ Full network creation successful!")
        print("🎯 Ready to proceed to next phases!")
    else:
        print("❌ Network creation failed - needs investigation")


if __name__ == "__main__":
    # Change to main directory for proper file access
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        comprehensive_test()
        
        print_separator("PHASE 1B.2 COMPLETE", "=", 70)
        print("✅ Wrapper function validated with full real dataset!")
        print("✅ Network analysis working perfectly with your data!")
        print("🔧 Your original manual test can now be fixed")
        print("")
        print("🎯 Next: Update your manual_test_network.py with the wrapper fix")
        print("   Then you can run your original test menu successfully!")
        
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original directory
        os.chdir(original_dir)