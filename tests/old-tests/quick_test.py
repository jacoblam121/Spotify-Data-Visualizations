#!/usr/bin/env python3
"""
Quick Interactive Test Script
============================

Simple script to quickly test specific functionality from Phases 1 & 2.
Run this for quick verification or debugging.
"""

import os
import sys

# Set encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_data_modes():
    """Quick test of data processing modes."""
    print("🔍 Testing Data Processing Modes...")
    
    try:
        from config_loader import AppConfig
        from data_processor import clean_and_filter_data, prepare_data_for_bar_chart_race
        
        config = AppConfig()
        print(f"Current visualization mode: {config.validate_visualization_mode()}")
        
        # Load data
        cleaned_data = clean_and_filter_data(config)
        if cleaned_data is None or cleaned_data.empty:
            print("❌ No data available")
            return
        
        print(f"✅ Loaded {len(cleaned_data)} rows of data")
        
        # Test both modes
        for mode in ["tracks", "artists"]:
            print(f"\nTesting {mode} mode...")
            race_data, details_map = prepare_data_for_bar_chart_race(cleaned_data, mode=mode)
            
            if race_data is not None:
                print(f"✅ {mode.title()} mode: {race_data.shape} race data, {len(details_map)} entities")
                
                # Show sample
                sample_id = list(details_map.keys())[0]
                sample_details = details_map[sample_id]
                print(f"   Sample: {sample_id}")
                
                if mode == "tracks":
                    print(f"   Artist: {sample_details.get('display_artist')}")
                    print(f"   Track: {sample_details.get('display_track')}")
                else:
                    print(f"   Artist: {sample_details.get('display_artist')}")
                    print(f"   Most played: {sample_details.get('most_played_track')}")
            else:
                print(f"❌ {mode.title()} mode failed")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_artist_photo(artist_name, artist_mbid=None):
    """Quick test of artist photo retrieval."""
    if artist_mbid:
        print(f"📸 Testing Artist Photo for: {artist_name} (MBID: {artist_mbid})")
    else:
        print(f"📸 Testing Artist Photo for: {artist_name}")
    
    try:
        from config_loader import AppConfig
        import album_art_utils
        
        config = AppConfig()
        album_art_utils.initialize_from_config(config)
        
        # Use the MBID parameter if provided
        photo_path, artist_info = album_art_utils.get_artist_profile_photo_and_spotify_info(
            artist_name, 
            artist_mbid=artist_mbid
        )
        
        if photo_path and os.path.exists(photo_path):
            file_size = os.path.getsize(photo_path)
            print(f"✅ SUCCESS: {photo_path}")
            print(f"   File size: {file_size:,} bytes")
            
            if artist_info:
                print(f"   Artist: {artist_info.get('canonical_artist_name')}")
                print(f"   Popularity: {artist_info.get('popularity')}")
                print(f"   Source: {artist_info.get('source')}")
                if artist_mbid and 'mbid_canonical_name' in artist_info:
                    print(f"   MBID canonical name: {artist_info.get('mbid_canonical_name')}")
            
            # Test dominant color
            try:
                dom_color = album_art_utils.get_artist_dominant_color(photo_path)
                print(f"   Dominant color: RGB{dom_color}")
            except Exception as e:
                print(f"   Dominant color failed: {e}")
                
        else:
            print(f"❌ FAILED: No photo retrieved")
            if artist_info:
                print(f"   But found artist info: {artist_info.get('canonical_artist_name')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_config_modes():
    """Test configuration mode validation."""
    print("⚙️  Testing Configuration...")
    
    try:
        from config_loader import AppConfig
        
        config = AppConfig()
        current_mode = config.validate_visualization_mode()
        
        print(f"✅ Current mode: {current_mode}")
        print(f"✅ Data source: {config.get('DataSource', 'SOURCE')}")
        print(f"✅ Config loaded successfully")
        
    except Exception as e:
        print(f"❌ Config error: {e}")

def interactive_menu():
    """Show interactive menu for testing."""
    while True:
        print("\n" + "="*50)
        print("🧪 QUICK TEST MENU")
        print("="*50)
        print("1. Test Configuration")
        print("2. Test Data Processing (Both Modes)")
        print("3. Test Artist Photo (Taylor Swift)")
        print("4. Test Artist Photo (Custom Artist)")
        print("5. Test Artist Photo (Japanese Artist)")
        print("6. Test Artist Photo with MBID (Taylor Swift)")
        print("7. Test Artist Photo with Custom MBID")
        print("8. Test Last.fm API Integration")
        print("9. Show Cache Files")
        print("10. Exit")
        print("-"*50)
        
        choice = input("Select option (1-10): ").strip()
        
        if choice == "1":
            test_config_modes()
            
        elif choice == "2":
            test_data_modes()
            
        elif choice == "3":
            test_artist_photo("Taylor Swift")
            
        elif choice == "4":
            artist_name = input("Enter artist name: ").strip()
            if artist_name:
                test_artist_photo(artist_name)
            else:
                print("❌ No artist name provided")
                
        elif choice == "5":
            test_artist_photo("ヨルシカ")
            
        elif choice == "6":
            # Taylor Swift's MBID for testing
            taylor_swift_mbid = "20244d07-534f-4eff-b4d4-930878889970"
            test_artist_photo("Taylor Swift", artist_mbid=taylor_swift_mbid)
            
        elif choice == "7":
            artist_name = input("Enter artist name: ").strip()
            artist_mbid = input("Enter artist MBID: ").strip()
            if artist_name and artist_mbid:
                test_artist_photo(artist_name, artist_mbid=artist_mbid)
            else:
                print("❌ Both artist name and MBID are required")
                
        elif choice == "8":
            test_lastfm_integration()
            
        elif choice == "9":
            show_cache_files()
            
        elif choice == "10":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please select 1-10.")

def test_lastfm_integration():
    """Test Last.fm API integration."""
    print("🎵 Testing Last.fm API Integration...")
    
    try:
        from config_loader import AppConfig
        from lastfm_utils import LastfmAPI
        
        # Load configuration
        config = AppConfig()
        lastfm_config = config.get_lastfm_config()
        
        if not lastfm_config['enabled']:
            print("❌ Last.fm integration is disabled in configuration")
            return
            
        if not lastfm_config['api_key']:
            print("❌ No Last.fm API key configured")
            return
            
        print(f"✅ Last.fm API key configured")
        print(f"   Cache directory: {lastfm_config['cache_dir']}")
        print(f"   Similarity limit: {lastfm_config['limit']}")
        
        # Initialize API
        api = LastfmAPI(
            lastfm_config['api_key'], 
            lastfm_config['api_secret'], 
            lastfm_config['cache_dir']
        )
        
        # Test with popular artist
        test_artist = "Taylor Swift"
        print(f"\n🔍 Testing with: {test_artist}")
        
        # Get similar artists
        similar = api.get_similar_artists(artist_name=test_artist, limit=5)
        
        if similar:
            print(f"✅ Found {len(similar)} similar artists:")
            for i, artist in enumerate(similar, 1):
                print(f"   {i}. {artist['name']} (score: {artist['match']:.3f})")
        else:
            print("❌ No similar artists found")
            
        # Get artist info
        info = api.get_artist_info(artist_name=test_artist)
        if info:
            print(f"\n📊 Artist Info:")
            print(f"   Name: {info['name']}")
            print(f"   Listeners: {info['listeners']:,}")
            print(f"   Play count: {info['playcount']:,}")
            if info['tags']:
                tags = ', '.join([tag['name'] for tag in info['tags'][:3]])
                print(f"   Tags: {tags}")
        else:
            print("❌ No artist info found")
            
    except Exception as e:
        print(f"❌ Error testing Last.fm: {e}")

def show_cache_files():
    """Show contents of cache directory."""
    print("📁 Cache Directory Contents...")
    
    try:
        # Show album art cache
        cache_dir = "album_art_cache"
        if os.path.exists(cache_dir):
            files = os.listdir(cache_dir)
            
            # Categorize files
            json_files = [f for f in files if f.endswith('.json')]
            artist_photos = [f for f in files if 'artist_' in f and f.endswith(('.jpg', '.png'))]
            album_art = [f for f in files if f.endswith(('.jpg', '.png')) and 'artist_' not in f]
            
            print(f"\n📊 Album Art Cache:")
            print(f"   JSON cache files: {len(json_files)}")
            print(f"   Artist photos: {len(artist_photos)}")
            print(f"   Album art: {len(album_art)}")
            print(f"   Total files: {len(files)}")
        
        # Show Last.fm cache
        lastfm_cache_dir = "lastfm_cache"
        if os.path.exists(lastfm_cache_dir):
            lastfm_files = os.listdir(lastfm_cache_dir)
            print(f"\n🎵 Last.fm Cache:")
            print(f"   Cache files: {len(lastfm_files)}")
            
            for f in lastfm_files:
                file_path = os.path.join(lastfm_cache_dir, f)
                size = os.path.getsize(file_path)
                print(f"   {f} ({size:,} bytes)")
        else:
            print(f"\n🎵 Last.fm Cache: Not created yet")
                
    except Exception as e:
        print(f"❌ Error reading cache: {e}")

def main():
    """Main function."""
    print("🚀 Quick Test Script for Phases 1 & 2")
    print("This script provides quick testing options for the new functionality.")
    
    if len(sys.argv) > 1:
        # Command line mode
        command = sys.argv[1].lower()
        
        if command == "config":
            test_config_modes()
        elif command == "data":
            test_data_modes()
        elif command == "artist" and len(sys.argv) > 2:
            artist_name = " ".join(sys.argv[2:])
            test_artist_photo(artist_name)
        elif command == "mbid" and len(sys.argv) > 3:
            artist_name = sys.argv[2]
            artist_mbid = sys.argv[3]
            test_artist_photo(artist_name, artist_mbid=artist_mbid)
        elif command == "cache":
            show_cache_files()
        elif command == "lastfm":
            test_lastfm_integration()
        else:
            print("Usage:")
            print("  python quick_test.py config                    # Test configuration")
            print("  python quick_test.py data                      # Test data processing")
            print("  python quick_test.py artist <name>             # Test artist photo")
            print("  python quick_test.py mbid <name> <mbid>        # Test artist photo with MBID")
            print("  python quick_test.py cache                     # Show cache files")
            print("  python quick_test.py lastfm                    # Test Last.fm integration")
            print("  python quick_test.py                           # Interactive menu")
            print("")
            print("Examples:")
            print("  python quick_test.py artist \"Taylor Swift\"")
            print("  python quick_test.py mbid \"Taylor Swift\" \"20244d07-534f-4eff-b4d4-930878889970\"")
            print("  python quick_test.py lastfm")
    else:
        # Interactive mode
        interactive_menu()

if __name__ == "__main__":
    main()