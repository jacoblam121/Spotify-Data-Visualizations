#!/usr/bin/env python3
"""
Debug script to check what similarity scores are being used in network edge creation.
"""

from network_utils import ArtistNetworkAnalyzer, prepare_dataframe_for_network_analysis
from data_processor import clean_and_filter_data
from config_loader import AppConfig

def debug_network_edges():
    """Debug what similarity scores are being used when creating network edges."""
    print("🕸️  Debugging Network Edge Creation")
    print("=" * 50)
    
    # Load data
    config = AppConfig('configurations.txt')
    df = clean_and_filter_data(config)
    df = prepare_dataframe_for_network_analysis(df)
    
    analyzer = ArtistNetworkAnalyzer(config)
    
    # Get top artists from user's data
    top_artists = df.groupby('artist').size().sort_values(ascending=False).head(10)
    print("🎵 Top 10 artists in your data:")
    for i, (artist, plays) in enumerate(top_artists.items(), 1):
        print(f"  {i:2d}. {artist} ({plays} plays)")
    
    print("\n🔍 Checking similarity data for each artist...")
    
    # Test enhanced artist fetcher to see what similarity data we get
    from artist_data_fetcher import EnhancedArtistDataFetcher
    fetcher = EnhancedArtistDataFetcher(config)
    
    artist_list = list(top_artists.head(5).index)  # Test with top 5
    
    for artist in artist_list:
        print(f"\n--- {artist} ---")
        result = fetcher.fetch_artist_data(artist, include_similar=True)
        
        if result['similar_artists']:
            print(f"  Found {len(result['similar_artists'])} similar artists:")
            for similar in result['similar_artists'][:5]:  # Show top 5
                score = similar['match']
                in_our_data = similar['name'] in artist_list
                status = "✅ IN DATA" if in_our_data else "❌ not in data"
                print(f"    {similar['name']:<20} | {score:.3f} | {status}")
                
                # This is what would create an edge
                if in_our_data and score >= 0.3:  # Using 0.3 as threshold
                    print(f"      🔗 WOULD CREATE EDGE: {artist} ↔ {similar['name']} ({score:.3f})")
        else:
            print("  ❌ No similar artists found")

if __name__ == "__main__":
    debug_network_edges()