"""
Debug Artist Name Investigation
===============================

Investigates the IVE artist name issue - why it sometimes finds similarities
and sometimes doesn't. Examines name normalization, Spotify URIs, and 
Last.fm API responses.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from config_loader import AppConfig
from data_processor import clean_and_filter_data
from lastfm_utils import LastfmAPI


def print_separator(title, char="=", width=70):
    """Print a formatted separator."""
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}")


def investigate_ive_artist_data():
    """Investigate IVE's artist data in detail."""
    print_separator("INVESTIGATING IVE ARTIST DATA")
    
    try:
        config = AppConfig('configurations.txt')
        config.config['DataSource']['SOURCE'] = 'spotify'
        
        df = clean_and_filter_data(config)
        
        if df is None or df.empty:
            print("❌ No data available")
            return
        
        # Find all IVE entries
        ive_entries = df[df['artist'].str.contains('ive', case=False, na=False)]
        
        print(f"📊 Found {len(ive_entries)} entries with 'ive' in artist name")
        print(f"📈 Unique artist name variations:")
        
        ive_artist_variants = ive_entries['artist'].value_counts()
        for variant, count in ive_artist_variants.items():
            print(f"   '{variant}': {count} plays")
        
        print(f"\n📋 Original artist name variations:")
        ive_original_variants = ive_entries['original_artist'].value_counts()
        for variant, count in ive_original_variants.items():
            print(f"   '{variant}': {count} plays")
        
        # Show some sample entries
        print(f"\n🔍 Sample IVE entries:")
        sample_entries = ive_entries[['artist', 'original_artist', 'track', 'spotify_track_uri']].head(5)
        for idx, row in sample_entries.iterrows():
            print(f"   Normalized: '{row['artist']}'")
            print(f"   Original: '{row['original_artist']}'")
            print(f"   Track: '{row['track']}'")
            print(f"   URI: '{row['spotify_track_uri']}'")
            print()
        
        return ive_entries
        
    except Exception as e:
        print(f"❌ Error investigating IVE data: {e}")
        return None


def test_lastfm_api_with_ive_variants():
    """Test Last.fm API with different IVE name variants."""
    print_separator("TESTING LAST.FM API WITH IVE VARIANTS")
    
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test different name variants
        test_variants = [
            'IVE',
            'ive',
            'Ive',
            'IVE (아이브)',
            '아이브',
            'IVE (K-pop)',
        ]
        
        print("🧪 Testing different IVE name variants:")
        
        for i, variant in enumerate(test_variants, 1):
            print(f"\n{i}. Testing variant: '{variant}'")
            
            try:
                similar_artists = lastfm_api.get_similar_artists(variant, limit=10)
                
                if similar_artists:
                    print(f"   ✅ Found {len(similar_artists)} similar artists:")
                    for j, similar in enumerate(similar_artists[:5], 1):
                        print(f"      {j}. {similar['name']}: {similar['match']:.3f}")
                else:
                    print(f"   ❌ No similar artists found")
                    
            except Exception as e:
                print(f"   ❌ API error: {e}")
        
        # Test with artist info call to see if artist exists
        print(f"\n🔍 Testing artist info lookup:")
        for variant in ['IVE', 'ive']:
            print(f"\nTesting artist info for: '{variant}'")
            
            try:
                artist_info = lastfm_api.get_artist_info(variant)
                
                if artist_info:
                    print(f"   ✅ Artist found:")
                    print(f"      Name: {artist_info.get('name', 'N/A')}")
                    print(f"      Playcount: {artist_info.get('playcount', 'N/A')}")
                    print(f"      Listeners: {artist_info.get('listeners', 'N/A')}")
                    print(f"      Tags: {[tag['name'] for tag in artist_info.get('tags', [])[:3]]}")
                else:
                    print(f"   ❌ Artist not found")
                    
            except Exception as e:
                print(f"   ❌ API error: {e}")
        
    except Exception as e:
        print(f"❌ Error testing Last.fm variants: {e}")


def examine_spotify_track_uris():
    """Examine Spotify track URIs to understand exact artist data."""
    print_separator("EXAMINING SPOTIFY TRACK URIS")
    
    try:
        config = AppConfig('configurations.txt')
        config.config['DataSource']['SOURCE'] = 'spotify'
        
        df = clean_and_filter_data(config)
        
        if df is None or df.empty:
            print("❌ No data available")
            return
        
        # Get IVE entries
        ive_entries = df[df['artist'].str.contains('ive', case=False, na=False)]
        
        if ive_entries.empty:
            print("❌ No IVE entries found")
            return
        
        print(f"📊 Examining {len(ive_entries)} IVE entries for URI patterns")
        
        # Get unique track URIs
        unique_uris = ive_entries['spotify_track_uri'].value_counts()
        
        print(f"\n🎵 Top IVE tracks by play count:")
        for i, (uri, count) in enumerate(unique_uris.head(10).items(), 1):
            # Get track info for this URI
            track_info = ive_entries[ive_entries['spotify_track_uri'] == uri].iloc[0]
            print(f"   {i:2d}. {track_info['original_track']} ({count} plays)")
            print(f"       Artist: '{track_info['original_artist']}'")
            print(f"       URI: {uri}")
            print()
        
        # Extract artist URIs from track URIs (if possible)
        print(f"📋 URI analysis:")
        print(f"   Track URIs typically look like: spotify:track:TRACK_ID")
        print(f"   We'd need Spotify API to get exact artist info from these")
        print(f"   But we can see the original artist names are consistent")
        
        return ive_entries
        
    except Exception as e:
        print(f"❌ Error examining URIs: {e}")
        return None


def compare_working_vs_failing_artists():
    """Compare IVE (failing) with TWICE (working) for patterns."""
    print_separator("COMPARING WORKING VS FAILING ARTISTS")
    
    try:
        config = AppConfig('configurations.txt')
        config.config['DataSource']['SOURCE'] = 'spotify'
        
        df = clean_and_filter_data(config)
        
        if df is None or df.empty:
            print("❌ No data available")
            return
        
        # Compare IVE vs TWICE (both K-pop, similar artists)
        test_artists = ['ive', 'twice']  # normalized names
        
        for artist_norm in test_artists:
            print(f"\n🔍 Analyzing: {artist_norm.upper()}")
            
            artist_entries = df[df['artist'] == artist_norm]
            
            if artist_entries.empty:
                print(f"   ❌ No entries found for '{artist_norm}'")
                continue
            
            print(f"   📊 {len(artist_entries)} total plays")
            
            # Get original name variants
            original_variants = artist_entries['original_artist'].value_counts()
            print(f"   📋 Original name variants:")
            for variant, count in original_variants.items():
                print(f"      '{variant}': {count} plays")
            
            # Test with Last.fm API
            primary_original = original_variants.index[0]  # Most common variant
            print(f"   🌐 Testing Last.fm with: '{primary_original}'")
            
            try:
                lastfm_config = config.get_lastfm_config()
                lastfm_api = LastfmAPI(
                    lastfm_config['api_key'],
                    lastfm_config['api_secret'],
                    lastfm_config['cache_dir']
                )
                
                similar_artists = lastfm_api.get_similar_artists(primary_original, limit=5)
                
                if similar_artists:
                    print(f"      ✅ Found {len(similar_artists)} similar artists")
                    for similar in similar_artists[:3]:
                        print(f"         - {similar['name']}: {similar['match']:.3f}")
                else:
                    print(f"      ❌ No similar artists found")
                    
                # Also test artist info
                artist_info = lastfm_api.get_artist_info(primary_original)
                if artist_info:
                    print(f"      ✅ Artist info found: {artist_info.get('listeners', 'N/A')} listeners")
                else:
                    print(f"      ❌ No artist info found")
                    
            except Exception as e:
                print(f"      ❌ Last.fm error: {e}")
        
    except Exception as e:
        print(f"❌ Error comparing artists: {e}")


def test_cache_issues():
    """Check if there are cache-related issues."""
    print_separator("TESTING CACHE ISSUES")
    
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        print(f"📁 Cache directory: {lastfm_config.get('cache_dir', 'lastfm_cache')}")
        
        # Check if cache file exists
        cache_file = os.path.join(lastfm_config.get('cache_dir', 'lastfm_cache'), 'lastfm_cache.json')
        
        if os.path.exists(cache_file):
            print(f"✅ Cache file exists: {cache_file}")
            
            # Load cache and check for IVE entries
            import json
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            print(f"📊 Cache contains {len(cache_data)} entries")
            
            # Look for IVE-related cache entries
            ive_cache_entries = []
            for key, value in cache_data.items():
                if 'ive' in key.lower():
                    ive_cache_entries.append((key, value))
            
            if ive_cache_entries:
                print(f"🔍 Found {len(ive_cache_entries)} IVE-related cache entries:")
                for key, value in ive_cache_entries[:5]:
                    print(f"   Key: {key}")
                    if 'data' in value:
                        data = value['data']
                        if 'similarartists' in data:
                            similar_count = len(data['similarartists'].get('artist', []))
                            print(f"        Cached similar artists: {similar_count}")
                        else:
                            print(f"        No similar artists in cache")
                    print()
            else:
                print(f"⚠️  No IVE-related entries found in cache")
                
        else:
            print(f"❌ Cache file not found: {cache_file}")
        
    except Exception as e:
        print(f"❌ Error checking cache: {e}")


def main():
    """Run all diagnostic tests."""
    print_separator("ARTIST NAME DEBUGGING - IVE INVESTIGATION", "=", 70)
    print("Investigating why IVE sometimes finds similarities and sometimes doesn't")
    
    try:
        # Step 1: Examine IVE data in your dataset
        ive_entries = investigate_ive_artist_data()
        
        # Step 2: Test Last.fm API with different name variants
        test_lastfm_api_with_ive_variants()
        
        # Step 3: Examine Spotify URIs
        examine_spotify_track_uris()
        
        # Step 4: Compare with working artists
        compare_working_vs_failing_artists()
        
        # Step 5: Check cache issues
        test_cache_issues()
        
        print_separator("DIAGNOSTIC SUMMARY & RECOMMENDATIONS", "=", 70)
        
        print("🔍 Potential Issues Identified:")
        print("1. 📝 Name normalization inconsistencies")
        print("2. 🌐 Last.fm API artist name matching")
        print("3. 💾 Cache inconsistencies")
        print("4. 🔄 Timing differences between test runs")
        
        print("\n💡 Recommended Solutions:")
        print("1. 🎯 Use Spotify artist URIs to get exact artist names")
        print("2. 🔍 Implement fuzzy name matching for Last.fm queries")
        print("3. 🧹 Add cache debugging and refresh options")
        print("4. ✅ Add consistency checks between test runs")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Change to main directory for proper file access
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Investigation interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original directory
        os.chdir(original_dir)