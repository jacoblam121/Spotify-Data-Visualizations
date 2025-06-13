#!/usr/bin/env python3
"""
Debug script to test Last.fm similarity fetching directly.
This will help us understand why edges are empty in the network data.
"""

import sys
import os
from pprint import pprint
from config_loader import AppConfig
from lastfm_utils import LastfmAPI
from artist_data_fetcher import EnhancedArtistDataFetcher

def test_lastfm_api_direct():
    """Test Last.fm API directly."""
    print("=== Testing Last.fm API Directly ===")
    
    # Load config
    config = AppConfig('configurations.txt')
    lastfm_config = config.get_lastfm_config()
    
    print(f"Last.fm API Key: {lastfm_config['api_key'][:10]}...")
    print(f"Last.fm enabled: {lastfm_config['enabled']}")
    
    # Initialize API
    lastfm_api = LastfmAPI(
        lastfm_config['api_key'],
        lastfm_config['api_secret'],
        lastfm_config['cache_dir']
    )
    
    # Test with a known artist
    test_artist = "Taylor Swift"
    print(f"\n--- Testing with artist: {test_artist} ---")
    
    # Get artist info
    print("Getting artist info...")
    artist_info = lastfm_api.get_artist_info(test_artist)
    if artist_info:
        print(f"✅ Artist info found: {artist_info['name']} ({artist_info['listeners']:,} listeners)")
    else:
        print("❌ No artist info found")
        return False
    
    # Get similar artists
    print("\nGetting similar artists...")
    similar_artists = lastfm_api.get_similar_artists(test_artist, limit=10)
    if similar_artists:
        print(f"✅ Found {len(similar_artists)} similar artists:")
        for i, similar in enumerate(similar_artists[:5], 1):
            print(f"  {i}. {similar['name']} (similarity: {similar['match']:.3f})")
    else:
        print("❌ No similar artists found")
        return False
    
    return True

def test_enhanced_artist_fetcher():
    """Test the enhanced artist fetcher used by network generation."""
    print("\n=== Testing Enhanced Artist Data Fetcher ===")
    
    config = AppConfig('configurations.txt')
    fetcher = EnhancedArtistDataFetcher(config)
    
    # Test with a known artist
    test_artist = "OneRepublic"
    print(f"\n--- Testing with artist: {test_artist} ---")
    
    result = fetcher.fetch_artist_data(test_artist, include_similar=True)
    
    print(f"Success: {result['success']}")
    print(f"Canonical name: {result['canonical_name']}")
    print(f"Primary listener count: {result['primary_listener_count']:,}")
    print(f"Primary source: {result['primary_source']}")
    
    if result['lastfm_data']:
        print(f"Last.fm data: ✅ ({result['lastfm_data']['listeners']:,} listeners)")
        if result['lastfm_data']['similar_artists']:
            print(f"  Similar artists: {len(result['lastfm_data']['similar_artists'])} found")
            for i, similar in enumerate(result['lastfm_data']['similar_artists'][:3], 1):
                print(f"    {i}. {similar['name']} (similarity: {similar['match']:.3f})")
        else:
            print("  ❌ No similar artists in Last.fm data")
    else:
        print("Last.fm data: ❌")
    
    if result['spotify_data']:
        print(f"Spotify data: ✅ ({result['spotify_data']['followers']:,} followers)")
    else:
        print("Spotify data: ❌")
    
    # Check if similar_artists is populated at the top level
    if result['similar_artists']:
        print(f"✅ Top-level similar_artists: {len(result['similar_artists'])} found")
        return True
    else:
        print("❌ Top-level similar_artists is empty/None")
        return False

def test_network_generation_logic():
    """Test the network generation logic with debug output."""
    print("\n=== Testing Network Generation Logic ===")
    
    from network_utils import ArtistNetworkAnalyzer
    from data_processor import clean_and_filter_data
    import pandas as pd
    
    config = AppConfig('configurations.txt')
    analyzer = ArtistNetworkAnalyzer(config)
    
    # Create a simple test dataset
    print("Creating test dataset...")
    test_data = [
        {'timestamp': '2022-06-01 10:00:00', 'artist': 'Taylor Swift', 'track': 'Song 1'},
        {'timestamp': '2022-06-01 11:00:00', 'artist': 'OneRepublic', 'track': 'Song 2'},
        {'timestamp': '2022-06-01 12:00:00', 'artist': 'Imagine Dragons', 'track': 'Song 3'},
        {'timestamp': '2022-06-01 13:00:00', 'artist': 'Taylor Swift', 'track': 'Song 4'},
        {'timestamp': '2022-06-01 14:00:00', 'artist': 'OneRepublic', 'track': 'Song 5'},
    ]
    
    df = pd.DataFrame(test_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    print(f"Test dataset: {len(df)} plays across {df['artist'].nunique()} artists")
    
    # Generate network with minimal parameters
    print("\nGenerating network...")
    network_data = analyzer.create_network_data(
        df, 
        top_n_artists=3,
        min_plays_threshold=1,
        min_similarity_threshold=0.1
    )
    
    print(f"Network generated:")
    print(f"  Nodes: {len(network_data['nodes'])}")
    print(f"  Edges: {len(network_data['edges'])}")
    
    if network_data['edges']:
        print("  Edge details:")
        for edge in network_data['edges']:
            print(f"    {edge['source']} -> {edge['target']} (weight: {edge['weight']:.3f})")
    else:
        print("  ❌ No edges created")
        
        # Debug why no edges were created
        print("\n--- Debugging edge creation ---")
        for node in network_data['nodes']:
            print(f"Node: {node['name']}")
    
    return len(network_data['edges']) > 0

if __name__ == "__main__":
    print("Last.fm Similarity Debug Script")
    print("=" * 50)
    
    success = True
    
    # Test 1: Direct Last.fm API
    if not test_lastfm_api_direct():
        success = False
    
    # Test 2: Enhanced Artist Fetcher
    if not test_enhanced_artist_fetcher():
        success = False
    
    # Test 3: Network Generation Logic
    if not test_network_generation_logic():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! Last.fm similarity should be working.")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    
    sys.exit(0 if success else 1)