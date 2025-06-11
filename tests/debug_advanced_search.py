"""
Debug Advanced Search
====================

Debug what the advanced search is actually finding for the stubborn artists.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI
import logging

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PARENT_DIR, 'configurations.txt')

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


def debug_artist_search(artist_name):
    """Debug the advanced search for a specific artist."""
    print(f"\n{'='*60}")
    print(f"DEBUGGING: {artist_name}")
    print('='*60)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Clear any cached data for this artist
        keys_to_remove = []
        for key in lastfm_api.cache.keys():
            if artist_name.lower() in key.lower():
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del lastfm_api.cache[key]
        
        print(f"\n1️⃣ Testing direct lookup:")
        similar_direct = lastfm_api.get_similar_artists(artist_name, limit=5, use_enhanced_matching=False)
        print(f"   Direct result: {len(similar_direct)} similar artists")
        
        print(f"\n2️⃣ Testing search API manually:")
        params = {'artist': artist_name, 'limit': '10'}
        response = lastfm_api._make_request('artist.search', params)
        
        if response and 'results' in response:
            matches = response['results'].get('artistmatches', {}).get('artist', [])
            if isinstance(matches, dict):
                matches = [matches]
            
            print(f"   Search found {len(matches)} matches:")
            
            for i, match in enumerate(matches[:5], 1):
                name = match.get('name', '')
                listeners = int(match.get('listeners', 0))
                mbid = match.get('mbid', '')
                
                print(f"\n   Match {i}: '{name}'")
                print(f"      Listeners: {listeners:,}")
                print(f"      MBID: {mbid or 'None'}")
                
                # Test this variation manually
                print(f"      Testing similar artists...")
                similar = lastfm_api.get_similar_artists(name, limit=5, use_enhanced_matching=False)
                print(f"      Result: {len(similar)} similar artists found")
                
                if similar:
                    print(f"      ✅ SUCCESS! Similar artists:")
                    for j, s in enumerate(similar[:3], 1):
                        print(f"         {j}. {s['name']}: {s['match']:.3f}")
                    break
                else:
                    print(f"      ❌ No similar artists")
        else:
            print(f"   ❌ Search API returned no results")
        
        print(f"\n3️⃣ Testing enhanced matching (full system):")
        similar_enhanced = lastfm_api.get_similar_artists(artist_name, limit=5, use_enhanced_matching=True)
        if similar_enhanced:
            variant = similar_enhanced[0].get('_matched_variant', artist_name)
            method = similar_enhanced[0].get('_search_method', 'unknown')
            print(f"   ✅ Enhanced matching SUCCESS!")
            print(f"   Working variant: '{variant}'")
            print(f"   Method: {method}")
        else:
            print(f"   ❌ Enhanced matching failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # Debug the two stubborn artists
    debug_artist_search('XXXTENTACION')
    debug_artist_search('blackbear')
    
    print(f"\n{'='*80}")
    print("CONCLUSION")
    print('='*80)
    print("\nIf advanced search finds search results but no similar artists for any variation,")
    print("this confirms the issue is Last.fm's data completeness, not our matching logic.")