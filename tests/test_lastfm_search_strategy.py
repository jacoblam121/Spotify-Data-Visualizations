"""
Test Last.fm Search Strategy
============================

Investigates why some artists have no similar artists despite having many listeners.
Tests if Last.fm has multiple artist entities for the same artist.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI
import json

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PARENT_DIR, 'configurations.txt')


def search_all_variations(lastfm_api, artist_name):
    """Search for all possible variations of an artist on Last.fm."""
    print(f"\n🔍 Searching for all variations of '{artist_name}'...")
    
    # Try artist.search to find all possible matches
    params = {'artist': artist_name, 'limit': '10'}
    response = lastfm_api._make_request('artist.search', params)
    
    if response and 'results' in response:
        matches = response['results'].get('artistmatches', {}).get('artist', [])
        if isinstance(matches, dict):
            matches = [matches]
        
        print(f"Found {len(matches)} potential matches:")
        
        results = []
        for i, match in enumerate(matches[:5], 1):  # Check top 5 matches
            name = match.get('name', '')
            listeners = int(match.get('listeners', 0))
            mbid = match.get('mbid', '')
            
            print(f"\n{i}. '{name}'")
            print(f"   Listeners: {listeners:,}")
            print(f"   MBID: {mbid or 'None'}")
            
            # Check if this variation has similar artists
            similar = lastfm_api.get_similar_artists(name, limit=5, use_enhanced_matching=False)
            has_similar = len(similar) > 0
            
            # Also try with MBID if available
            if not has_similar and mbid:
                similar_mbid = lastfm_api.get_similar_artists(mbid=mbid, limit=5)
                if similar_mbid:
                    has_similar = True
                    similar = similar_mbid
            
            print(f"   Similar artists: {'✅ YES' if has_similar else '❌ NO'} ({len(similar)} found)")
            
            results.append({
                'name': name,
                'listeners': listeners,
                'mbid': mbid,
                'has_similar': has_similar,
                'similar_count': len(similar)
            })
        
        return results
    else:
        print("❌ No search results found")
        return []


def test_problematic_artists():
    """Test the problematic artists with search strategy."""
    print("=" * 80)
    print("TESTING PROBLEMATIC ARTISTS WITH SEARCH STRATEGY")
    print("=" * 80)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test the problematic artists
        test_artists = [
            ('mgk', 'Machine Gun Kelly'),
            ('XXXTENTACION', 'XXXTentacion'), 
            ('blackbear', 'Blackbear')
        ]
        
        for original_name, full_name in test_artists:
            print(f"\n{'='*60}")
            print(f"Testing: {original_name}")
            print('='*60)
            
            # Test original name
            print(f"\n1️⃣ Testing original name: '{original_name}'")
            info = lastfm_api.get_artist_info(original_name, use_enhanced_matching=False)
            if info:
                print(f"   ✅ Artist found: {info.get('listeners', 0):,} listeners")
            similar = lastfm_api.get_similar_artists(original_name, limit=5, use_enhanced_matching=False)
            print(f"   Similar artists: {len(similar)}")
            
            # Test full name variant
            print(f"\n2️⃣ Testing full name: '{full_name}'")
            info_full = lastfm_api.get_artist_info(full_name, use_enhanced_matching=False)
            if info_full:
                print(f"   ✅ Artist found: {info_full.get('listeners', 0):,} listeners")
            similar_full = lastfm_api.get_similar_artists(full_name, limit=5, use_enhanced_matching=False)
            print(f"   Similar artists: {len(similar_full)}")
            
            # Search for all variations
            print(f"\n3️⃣ Searching all variations:")
            variations = search_all_variations(lastfm_api, original_name)
            
            # Find best variation (most listeners + has similar artists)
            best_variation = None
            for var in variations:
                if var['has_similar']:
                    if not best_variation or var['listeners'] > best_variation['listeners']:
                        best_variation = var
            
            if best_variation:
                print(f"\n✅ BEST VARIATION FOUND: '{best_variation['name']}'")
                print(f"   Listeners: {best_variation['listeners']:,}")
                print(f"   Similar artists: {best_variation['similar_count']}")
            else:
                print(f"\n❌ No variation with similar artists found")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_search_vs_direct():
    """Compare search results vs direct lookup."""
    print("\n" + "=" * 80)
    print("SEARCH vs DIRECT LOOKUP COMPARISON")
    print("=" * 80)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test case: XXXTentacion (multiple possible spellings)
        test_variations = [
            'XXXTENTACION',
            'XXXTentacion', 
            'xxxtentacion',
            'Xxxtentacion',
            'XXX Tentacion',
            'xxx tentacion'
        ]
        
        print("\nTesting different capitalizations for XXXTentacion:")
        print("-" * 60)
        
        for variant in test_variations:
            # Direct lookup
            info = lastfm_api.get_artist_info(variant, use_enhanced_matching=False)
            similar = lastfm_api.get_similar_artists(variant, limit=5, use_enhanced_matching=False)
            
            if info or similar:
                listeners = info.get('listeners', 0) if info else 0
                print(f"'{variant}':")
                print(f"   Info: {'✅' if info else '❌'} ({listeners:,} listeners)")
                print(f"   Similar: {'✅' if similar else '❌'} ({len(similar)} artists)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_problematic_artists()
    test_search_vs_direct()