"""
Manual testing interface for Last.fm API integration.
Provides interactive testing options for verifying functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from datetime import datetime
from configparser import ConfigParser
from lastfm_utils import LastfmAPI


def load_config():
    """Load configuration from configurations.txt."""
    config = ConfigParser()
    config.read('../configurations.txt')
    
    api_key = config.get('LastfmAPI', 'API_KEY')
    api_secret = config.get('LastfmAPI', 'API_SECRET')
    cache_dir = config.get('LastfmAPI', 'CACHE_DIR', fallback='lastfm_cache')
    
    return api_key, api_secret, cache_dir


def print_similar_artists(similar_artists, limit=10):
    """Pretty print similar artists."""
    print(f"\nFound {len(similar_artists)} similar artists:")
    print("-" * 60)
    
    for i, artist in enumerate(similar_artists[:limit]):
        print(f"{i+1:2d}. {artist['name']:<30} Score: {artist['match']:.3f}")
        if artist.get('mbid'):
            print(f"    MBID: {artist['mbid']}")
    print("-" * 60)


def test_artist_lookup():
    """Test artist lookup by name."""
    artist_name = input("\nEnter artist name: ").strip()
    if not artist_name:
        print("No artist name provided.")
        return
        
    api_key, api_secret, cache_dir = load_config()
    api = LastfmAPI(api_key, api_secret, cache_dir)
    
    print(f"\nFetching artist info for: {artist_name}")
    
    # Get artist info
    info = api.get_artist_info(artist_name=artist_name)
    
    if info:
        print(f"\nArtist: {info['name']}")
        print(f"Listeners: {info['listeners']:,}")
        print(f"Play count: {info['playcount']:,}")
        
        if info['tags']:
            print(f"Tags: {', '.join([tag['name'] for tag in info['tags'][:5]])}")
            
        if info.get('mbid'):
            print(f"MBID: {info['mbid']}")
    else:
        print(f"No artist info found for: {artist_name}")


def test_similar_artists():
    """Test fetching similar artists with scores."""
    artist_name = input("\nEnter artist name: ").strip()
    if not artist_name:
        print("No artist name provided.")
        return
        
    try:
        limit = int(input("Number of similar artists to fetch (default 20): ") or "20")
    except ValueError:
        limit = 20
        
    api_key, api_secret, cache_dir = load_config()
    api = LastfmAPI(api_key, api_secret, cache_dir)
    
    print(f"\nFetching similar artists for: {artist_name}")
    start_time = time.time()
    
    similar = api.get_similar_artists(artist_name=artist_name, limit=limit)
    
    duration = time.time() - start_time
    print(f"Request took: {duration:.3f} seconds")
    
    if similar:
        print_similar_artists(similar, limit)
        
        # Show score distribution
        scores = [a['match'] for a in similar]
        print(f"\nScore distribution:")
        print(f"  Highest: {max(scores):.3f}")
        print(f"  Lowest:  {min(scores):.3f}")
        print(f"  Average: {sum(scores)/len(scores):.3f}")
    else:
        print(f"No similar artists found for: {artist_name}")


def test_with_mbid():
    """Test with MBID from your data."""
    print("\nTesting with MusicBrainz ID (MBID)")
    print("Example MBIDs from your data:")
    print("  - Taylor Swift: 20244d07-534f-4eff-b4d4-930878889970")
    print("  - Ariana Grande: f4fdbb4c-e4b7-47a0-b83b-d91bbfcfa387")
    print("  - BLACKPINK: 38320b40-9f4a-4c50-9748-5dcf871f5627")
    
    mbid = input("\nEnter MBID: ").strip()
    if not mbid:
        print("No MBID provided.")
        return
        
    api_key, api_secret, cache_dir = load_config()
    api = LastfmAPI(api_key, api_secret, cache_dir)
    
    print(f"\nFetching similar artists for MBID: {mbid}")
    
    similar = api.get_similar_artists(mbid=mbid, limit=10)
    
    if similar:
        print_similar_artists(similar)
    else:
        print(f"No similar artists found for MBID: {mbid}")


def test_cache_performance():
    """Test cache performance."""
    api_key, api_secret, cache_dir = load_config()
    api = LastfmAPI(api_key, api_secret, cache_dir)
    
    test_artists = ["Taylor Swift", "BTS", "The Beatles", "Paramore", "BLACKPINK"]
    
    print("\nTesting cache performance...")
    print("First run (API calls):")
    
    # First run - API calls
    total_api_time = 0
    for artist in test_artists:
        start = time.time()
        api.get_similar_artists(artist_name=artist, limit=5)
        duration = time.time() - start
        total_api_time += duration
        print(f"  {artist:<20} {duration:.3f}s")
        
    print(f"Total time (API): {total_api_time:.3f}s")
    
    print("\nSecond run (cache hits):")
    
    # Second run - cache hits
    total_cache_time = 0
    for artist in test_artists:
        start = time.time()
        api.get_similar_artists(artist_name=artist, limit=5)
        duration = time.time() - start
        total_cache_time += duration
        print(f"  {artist:<20} {duration:.3f}s")
        
    print(f"Total time (cache): {total_cache_time:.3f}s")
    print(f"Speed improvement: {total_api_time/total_cache_time:.1f}x faster")
    
    # Show cache contents
    if os.path.exists(api.cache_file):
        with open(api.cache_file, 'r') as f:
            cache = json.load(f)
        print(f"\nCache contains {len(cache)} entries")


def test_error_scenarios():
    """Test various error scenarios."""
    api_key, api_secret, cache_dir = load_config()
    api = LastfmAPI(api_key, api_secret, cache_dir)
    
    print("\nTesting error scenarios...")
    
    test_cases = [
        ("Non-existent artist", "asdfghjkl123456789"),
        ("Special characters", "Beyoncé"),
        ("Unicode (Japanese)", "ヨルシカ"),
        ("Unicode (Korean)", "방탄소년단"),
        ("Empty string", ""),
        ("Very long name", "A" * 100),
        ("Special symbols", "AC/DC"),
        ("Numbers", "21 Pilots"),
    ]
    
    for description, artist_name in test_cases:
        print(f"\n{description}: '{artist_name}'")
        try:
            similar = api.get_similar_artists(artist_name=artist_name, limit=3)
            if similar:
                print(f"  ✓ Found {len(similar)} similar artists")
                print(f"    First match: {similar[0]['name']} (score: {similar[0]['match']:.3f})")
            else:
                print("  ✓ No results (handled gracefully)")
        except Exception as e:
            print(f"  ✗ Error: {e}")


def view_your_data_artists():
    """View artists from your Spotify/Last.fm data."""
    print("\nReading your music data to find top artists...")
    
    # Try to read from data processor
    try:
        # Change to the main directory temporarily
        original_dir = os.getcwd()
        main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(main_dir)
        
        sys.path.append('.')
        from data_processor import clean_and_filter_data
        from config_loader import AppConfig
        
        config = AppConfig('configurations.txt')
        
        df = clean_and_filter_data(config)
        
        if df is None or df.empty:
            print("No data found. Make sure your data files are in the correct location.")
            print(f"Current source: {config.get('DataSource', 'SOURCE')}")
            return []
        
        # Get top artists
        if 'artist' in df.columns:
            top_artists = df.groupby('artist').size().sort_values(ascending=False).head(20)
            
            print(f"\nYour top 20 artists (from {len(df)} total plays):")
            print("-" * 50)
            for i, (artist, plays) in enumerate(top_artists.items()):
                print(f"{i+1:2d}. {artist:<30} ({plays} plays)")
            print("-" * 50)
            
            return list(top_artists.index)
        else:
            print("No 'artist' column found in data.")
            print(f"Available columns: {list(df.columns)}")
            return []
            
    except Exception as e:
        print(f"Could not load your data: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your data files exist:")
        print("   - For Spotify: spotify_data.json")
        print("   - For Last.fm: lastfm_data.csv")
        print("2. Check your configurations.txt SOURCE setting")
        print("3. Run from the main directory, not the tests/ directory")
        
    finally:
        # Restore original directory
        try:
            os.chdir(original_dir)
        except:
            pass
        
    return []


def main():
    """Main interactive menu."""
    print("=" * 60)
    print("Last.fm API Manual Testing Interface")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. Test artist lookup by name")
        print("2. Test similar artists with scores")
        print("3. Test with MBID from your data")
        print("4. Test cache performance")
        print("5. Test error scenarios")
        print("6. View artists from your data")
        print("0. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            test_artist_lookup()
        elif choice == '2':
            test_similar_artists()
        elif choice == '3':
            test_with_mbid()
        elif choice == '4':
            test_cache_performance()
        elif choice == '5':
            test_error_scenarios()
        elif choice == '6':
            artists = view_your_data_artists()
            if artists:
                print("\nYou can use any of these artists in options 1 or 2")
        else:
            print("Invalid option. Please try again.")
            
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()