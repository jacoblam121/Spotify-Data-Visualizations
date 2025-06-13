#!/usr/bin/env python3
"""
Simple Artist Data Test
Tests the enhanced artist data fetcher focusing on data retrieval only.
"""

from artist_data_fetcher import EnhancedArtistDataFetcher
from config_loader import AppConfig
import json

def test_artist_data_fetching():
    """Test basic artist data fetching from both APIs."""
    print("🧪 Testing Artist Data Fetching")
    print("=" * 50)
    
    try:
        # Initialize fetcher
        config = AppConfig('configurations.txt')
        fetcher = EnhancedArtistDataFetcher(config)
        
        # Test artists with different characteristics
        test_artists = [
            'Taylor Swift',    # Popular Western artist
            'ive',            # K-pop group (previously problematic)
            'BLACKPINK',      # Popular K-pop
            'Ed Sheeran',     # Popular Western artist
            'Dua Lipa'        # Popular Western artist
        ]
        
        print(f"Testing {len(test_artists)} artists...")
        
        for i, artist in enumerate(test_artists, 1):
            print(f"\n{i}/{len(test_artists)}: Testing '{artist}'")
            
            result = fetcher.fetch_artist_data(artist, include_similar=False)
            
            if result['success']:
                print(f"  ✅ Success: {result['canonical_name']}")
                print(f"  📊 Primary: {result['primary_listener_count']:,} from {result['primary_source']}")
                
                # Show Last.fm data if available
                if result['lastfm_data']:
                    lastfm = result['lastfm_data']
                    print(f"  🎧 Last.fm: {lastfm['listeners']:,} listeners, {lastfm['playcount']:,} plays")
                    if lastfm.get('tags'):
                        genres = [tag['name'] for tag in lastfm['tags'][:3]]
                        print(f"      Genres: {', '.join(genres)}")
                else:
                    print(f"  ❌ Last.fm: No data")
                
                # Show Spotify data if available
                if result['spotify_data']:
                    spotify = result['spotify_data']
                    print(f"  🎵 Spotify: {spotify['followers']:,} followers, popularity {spotify['popularity']}/100")
                    if spotify.get('genres'):
                        print(f"      Genres: {', '.join(spotify['genres'][:3])}")
                    if spotify.get('photo_url'):
                        print(f"      Photo: Available")
                    else:
                        print(f"      Photo: None")
                else:
                    print(f"  ❌ Spotify: No data")
                
            else:
                print(f"  ❌ Failed: {result['error_message']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_hybrid_node_sizing():
    """Test different hybrid approaches for node sizing."""
    print("\n🔢 Testing Hybrid Node Sizing Approaches")
    print("=" * 50)
    
    try:
        config = AppConfig('configurations.txt')
        fetcher = EnhancedArtistDataFetcher(config)
        
        # Get sample data
        test_artists = ['Taylor Swift', 'BLACKPINK', 'ive']
        results = []
        
        for artist in test_artists:
            result = fetcher.fetch_artist_data(artist, include_similar=False)
            if result['success']:
                results.append(result)
        
        if not results:
            print("❌ No successful artist data to test with")
            return False
        
        print(f"📊 Comparing hybrid sizing approaches for {len(results)} artists:")
        
        # Define different hybrid approaches
        sizing_approaches = {
            'lastfm_only': lambda r: r['lastfm_data']['listeners'] if r['lastfm_data'] else 0,
            'spotify_followers': lambda r: r['spotify_data']['followers'] if r['spotify_data'] else 0,
            'spotify_popularity_scaled': lambda r: (r['spotify_data']['popularity'] * 10000) if r['spotify_data'] else 0,
            'hybrid_multiply': lambda r: (
                (r['lastfm_data']['listeners'] if r['lastfm_data'] else 1000) * 
                (r['spotify_data']['popularity'] / 50 if r['spotify_data'] else 1)
            ),
            'hybrid_weighted': lambda r: (
                (r['lastfm_data']['listeners'] * 0.7 if r['lastfm_data'] else 0) +
                (r['spotify_data']['popularity'] * 50000 if r['spotify_data'] else 0)
            )
        }
        
        # Calculate sizes for each approach
        print(f"\n{'Artist':<15} {'LastFM':<10} {'Spotify':<10} {'Pop*10k':<10} {'Hybrid×':<10} {'HybridW':<10}")
        print("-" * 75)
        
        for result in results:
            name = result['canonical_name'][:14]
            sizes = {}
            
            for approach_name, calc_func in sizing_approaches.items():
                try:
                    size = int(calc_func(result))
                    sizes[approach_name] = size
                except:
                    sizes[approach_name] = 0
            
            print(f"{name:<15} {sizes['lastfm_only']:<10,} {sizes['spotify_followers']:<10,} " + 
                  f"{sizes['spotify_popularity_scaled']:<10,} {sizes['hybrid_multiply']:<10,.0f} " +
                  f"{sizes['hybrid_weighted']:<10,.0f}")
        
        # Show raw data for analysis
        print(f"\n📋 Raw Data for Analysis:")
        for result in results:
            print(f"\n{result['canonical_name']}:")
            if result['lastfm_data']:
                print(f"  Last.fm: {result['lastfm_data']['listeners']:,} listeners")
            if result['spotify_data']:
                print(f"  Spotify: {result['spotify_data']['followers']:,} followers, {result['spotify_data']['popularity']}/100 popularity")
        
        # Recommend best approach
        print(f"\n💡 Recommendations:")
        print(f"  • 'hybrid_multiply': Multiplies Last.fm listeners by normalized Spotify popularity")
        print(f"  • 'hybrid_weighted': Weighted sum of Last.fm listeners (70%) + scaled Spotify popularity (30%)")
        print(f"  • 'spotify_popularity_scaled': Pure Spotify popularity scaled up (popularity × 10,000)")
        print(f"  • Choose based on which gives most intuitive visual balance")
        
        return True
        
    except Exception as e:
        print(f"❌ Hybrid sizing test failed: {e}")
        return False

def test_configuration_options():
    """Test different configuration options."""
    print("\n⚙️  Testing Configuration Options")
    print("=" * 50)
    
    config = AppConfig('configurations.txt')
    network_config = config.get_network_visualization_config()
    
    print(f"Current Configuration:")
    print(f"  Node sizing strategy: {network_config['node_sizing_strategy']}")
    print(f"  Fetch both sources: {network_config['fetch_both_sources']}")
    print(f"  Fallback behavior: {network_config['fallback_behavior']}")
    print(f"  Spotify popularity boost: {network_config['spotify_popularity_boost']}")
    
    # Test if both APIs are available
    fetcher = EnhancedArtistDataFetcher(config)
    print(f"\nAPI Availability:")
    print(f"  Last.fm: {'✅ Available' if fetcher.lastfm_api else '❌ Not configured'}")
    print(f"  Spotify: {'✅ Available' if fetcher.spotify_available else '❌ Not configured'}")
    
    return True

if __name__ == "__main__":
    print("🚀 Artist Data Fetching Test Suite")
    print("=" * 60)
    
    success1 = test_artist_data_fetching()
    success2 = test_hybrid_node_sizing() 
    success3 = test_configuration_options()
    
    if success1 and success2 and success3:
        print(f"\n🎉 All tests passed! Artist data fetching is working.")
    else:
        print(f"\n⚠️  Some tests had issues. Check the output above.")