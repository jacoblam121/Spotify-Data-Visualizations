"""
Debug Missing Artists
====================

Test the newly problematic artists: MIYEON and 88rising
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PARENT_DIR, 'configurations.txt')


def debug_missing_artists():
    """Debug MIYEON and 88rising."""
    print("=" * 80)
    print("DEBUGGING NEWLY PROBLEMATIC ARTISTS")
    print("=" * 80)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test problematic artists
        test_artists = [
            'MIYEON',
            '88rising',
            'blackbear',  # Known problematic one for comparison
        ]
        
        for artist in test_artists:
            print(f"\n{'='*60}")
            print(f"Testing: {artist}")
            print('='*60)
            
            # Clear cache for this artist
            keys_to_remove = []
            for key in lastfm_api.cache.keys():
                if artist.lower() in key.lower():
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del lastfm_api.cache[key]
            
            # Test with enhanced matching
            print(f"\n1️⃣ Testing enhanced matching:")
            similar = lastfm_api.get_similar_artists(artist, limit=5, use_enhanced_matching=True)
            if similar:
                variant = similar[0].get('_matched_variant', artist)
                method = similar[0].get('_search_method', 'unknown')
                print(f"✅ Found {len(similar)} similar artists")
                print(f"   Working variant: '{variant}'")
                print(f"   Method: {method}")
                print("   Top similar artists:")
                for i, s in enumerate(similar[:3], 1):
                    print(f"      {i}. {s['name']}: {s['match']:.3f}")
            else:
                print(f"❌ No similar artists found")
            
            # Test artist info
            print(f"\n2️⃣ Testing artist info:")
            info = lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
            if info:
                print(f"✅ Artist found: {info['name']}")
                print(f"   Listeners: {info.get('listeners', 0):,}")
                print(f"   Playcount: {info.get('playcount', 0):,}")
            else:
                print(f"❌ Artist info not found")
            
            # Test search API manually for collaborations
            print(f"\n3️⃣ Manual search for collaborations:")
            params = {'artist': artist, 'limit': '10'}
            response = lastfm_api._make_request('artist.search', params)
            
            if response and 'results' in response:
                matches = response['results'].get('artistmatches', {}).get('artist', [])
                if isinstance(matches, dict):
                    matches = [matches]
                
                print(f"Found {len(matches)} search matches:")
                collab_found = False
                
                for i, match in enumerate(matches[:5], 1):
                    name = match.get('name', '')
                    listeners = int(match.get('listeners', 0))
                    
                    print(f"\n{i}. '{name}' ({listeners:,} listeners)")
                    
                    # Test for similar artists
                    if listeners > 1000:  # Skip tiny artists
                        similar_test = lastfm_api.get_similar_artists(
                            name, limit=3, use_enhanced_matching=False
                        )
                        if similar_test:
                            print(f"   ✅ Has {len(similar_test)} similar artists!")
                            collab_found = True
                            break
                        else:
                            print(f"   ❌ No similar artists")
                
                if not collab_found:
                    print(f"\n❌ No working collaborations found for {artist}")
            else:
                print(f"❌ Search API returned no results")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_patterns():
    """Test if the new patterns work."""
    print("\n" + "=" * 80)
    print("TESTING NEW PATTERNS")
    print("=" * 80)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test new patterns
        pattern_tests = [
            ('MIYEON', ['Cho Mi-yeon', '미연', 'MIYEON ((G)I-DLE)', 'Mi-yeon']),
            ('88RISING', ['88rising', '88 Rising', 'eighty eight rising']),
        ]
        
        for original, variants in pattern_tests:
            print(f"\n🧪 Testing variants for '{original}':")
            
            for variant in variants:
                info = lastfm_api.get_artist_info(variant, use_enhanced_matching=False)
                similar = lastfm_api.get_similar_artists(variant, limit=3, use_enhanced_matching=False)
                
                status_info = "✅" if info else "❌"
                status_similar = "✅" if similar else "❌"
                
                listeners = info.get('listeners', 0) if info else 0
                
                print(f"   {status_info} '{variant}': {listeners:,} listeners")
                print(f"   {status_similar} Similar artists: {len(similar) if similar else 0}")
                
                if similar:
                    print(f"      Working! Found similar artists")
                    break
    
    except Exception as e:
        print(f"❌ Error testing patterns: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    debug_missing_artists()
    test_patterns()
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("\nIf these artists still fail after pattern testing,")
    print("they may have genuine Last.fm data gaps for similar artists.")
    print("This is an API limitation, not a matching issue.")