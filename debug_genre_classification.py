#!/usr/bin/env python3
"""
Debug Genre Classification
==========================
Quick test to diagnose why genre classification is failing.
"""

import sys
from pathlib import Path

# Add project modules
sys.path.insert(0, str(Path(__file__).parent))

from artist_data_fetcher import EnhancedArtistDataFetcher
from config_loader import AppConfig

def test_artist_data_fetcher():
    """Test the artist data fetcher directly to see why success=False."""
    print("🔍 Testing Artist Data Fetcher")
    print("=" * 32)
    
    # Initialize
    config = AppConfig("configurations.txt")
    fetcher = EnhancedArtistDataFetcher(config)
    
    # Test with a few well-known artists
    test_artists = ["Taylor Swift", "Paramore", "IVE"]
    
    print(f"📋 Testing {len(test_artists)} artists...")
    
    for artist in test_artists:
        print(f"\n🎯 Testing: {artist}")
        
        try:
            enhanced_data = fetcher.fetch_artist_data(artist)
            
            print(f"   Success: {enhanced_data.get('success', 'Unknown')}")
            print(f"   Error: {enhanced_data.get('error', 'None')}")
            print(f"   Canonical name: {enhanced_data.get('canonical_name', 'Missing')}")
            
            # Check data sources
            has_lastfm = bool(enhanced_data.get('lastfm_data'))
            has_spotify = bool(enhanced_data.get('spotify_data'))
            
            print(f"   Last.fm data: {'✅' if has_lastfm else '❌'}")
            print(f"   Spotify data: {'✅' if has_spotify else '❌'}")
            
            if has_lastfm:
                lastfm_data = enhanced_data['lastfm_data']
                tags = lastfm_data.get('tags', [])
                print(f"   Last.fm tags: {[tag.get('name', 'no-name') for tag in tags[:3]]}")
                print(f"   Listeners: {lastfm_data.get('listeners', 0)}")
            
            if has_spotify:
                spotify_data = enhanced_data['spotify_data']
                genres = spotify_data.get('genres', [])
                print(f"   Spotify genres: {genres[:3]}")
                print(f"   Followers: {spotify_data.get('followers', 0)}")
            
            # Test genre classification if data is available
            if enhanced_data.get('success'):
                from network_utils import ArtistNetworkAnalyzer
                analyzer = ArtistNetworkAnalyzer(config)
                primary_genre, all_genres = analyzer.classify_artist_genre(enhanced_data)
                print(f"   🎨 Classified genre: {primary_genre}")
                print(f"   🎨 All genres: {all_genres[:3]}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()

def test_genre_classification_directly():
    """Test genre classification with mock data."""
    print(f"\n🧪 Testing Genre Classification Logic")
    print("=" * 37)
    
    from network_utils import ArtistNetworkAnalyzer
    config = AppConfig("configurations.txt")
    analyzer = ArtistNetworkAnalyzer(config)
    
    # Mock enhanced data for testing
    mock_data = {
        'success': True,
        'lastfm_data': {
            'tags': [
                {'name': 'k-pop', 'count': 100},
                {'name': 'pop', 'count': 90},
                {'name': 'korean', 'count': 80}
            ]
        },
        'spotify_data': {
            'genres': ['k-pop', 'korean pop']
        }
    }
    
    print("🎯 Testing with mock K-pop data:")
    primary_genre, all_genres = analyzer.classify_artist_genre(mock_data)
    print(f"   Primary genre: {primary_genre}")
    print(f"   All genres: {all_genres}")
    
    if primary_genre == 'asian':  # K-pop now maps to 'asian' in simplified system
        print("   ✅ Genre classification logic is working!")
    else:
        print("   ❌ Genre classification logic is broken!")

if __name__ == "__main__":
    test_artist_data_fetcher()
    test_genre_classification_directly()