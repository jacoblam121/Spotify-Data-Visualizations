#!/usr/bin/env python3
"""
Test ANYUJIN with Last.fm API
==============================
Direct test to see if Last.fm API finds the ANYUJIN-BTS connection
that was previously working with 0.86 edge weight.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI

def test_anyujin_lastfm():
    """Test ANYUJIN specifically with Last.fm API."""
    print("🔍 Testing ANYUJIN with Last.fm API (PRIMARY source)")
    print("=" * 55)
    
    # Initialize Last.fm API
    try:
        config = AppConfig("configurations.txt")
        lastfm_config = config.get_lastfm_config()
        
        if not lastfm_config['enabled'] or not lastfm_config['api_key']:
            print("❌ Last.fm API not configured!")
            return
        
        api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        print("✅ Last.fm API initialized")
        
    except Exception as e:
        print(f"❌ Last.fm API initialization error: {e}")
        return
    
    # Test ANYUJIN
    print(f"\n🎯 Testing ANYUJIN similarity search...")
    
    try:
        # Get comprehensive results (up to 100)
        results = api.get_similar_artists("ANYUJIN", limit=100)
        print(f"✅ Last.fm returned {len(results)} similar artists for ANYUJIN")
        
        if len(results) == 0:
            print(f"❌ ANYUJIN not found in Last.fm database")
            
            # Try alternative spellings
            print(f"\n🔍 Trying alternative spellings...")
            
            alternatives = ["An Yujin", "Ahn Yujin", "안유진", "ANYUJIN (IVE)", "Yujin"]
            
            for alt_name in alternatives:
                try:
                    alt_results = api.get_similar_artists(alt_name, limit=20)
                    if alt_results:
                        print(f"   ✅ '{alt_name}': {len(alt_results)} results found")
                        # Check if BTS is in results
                        bts_found = any('bts' in r['name'].lower() for r in alt_results)
                        if bts_found:
                            bts_result = next(r for r in alt_results if 'bts' in r['name'].lower())
                            print(f"      🎉 BTS FOUND! '{bts_result['name']}' (score: {bts_result['match']:.3f})")
                        else:
                            print(f"      Top results: {', '.join([r['name'] for r in alt_results[:5]])}")
                    else:
                        print(f"   ❌ '{alt_name}': Not found")
                except Exception as e:
                    print(f"   ❌ '{alt_name}': Error - {e}")
            
            return
        
        # Show all results
        print(f"\n📋 All Last.fm similarity results for ANYUJIN:")
        for i, result in enumerate(results, 1):
            score = result['match']
            name = result['name']
            print(f"   {i:2}. {name} ({score:.3f})")
        
        # Check specifically for BTS
        bts_results = [r for r in results if 'bts' in r['name'].lower()]
        
        if bts_results:
            print(f"\n🎉 BTS CONNECTION FOUND!")
            for bts in bts_results:
                print(f"   ✅ {bts['name']} (score: {bts['match']:.3f})")
                if abs(bts['match'] - 0.86) < 0.01:
                    print(f"      🎯 This matches your reported 0.86 score!")
        else:
            print(f"\n❌ BTS not found in ANYUJIN's Last.fm results")
        
        # Check for other artists from user's data
        print(f"\n🔍 Checking for other artists from your data...")
        
        # Load user's artists for cross-reference
        try:
            import json
            with open('spotify_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            user_artists = set()
            for entry in data:
                if 'master_metadata_album_artist_name' in entry:
                    artist_name = entry['master_metadata_album_artist_name']
                    if artist_name:
                        user_artists.add(artist_name.strip())
            
            user_artists_lower = {a.lower() for a in user_artists}
            
            matches_found = []
            for result in results:
                if result['name'].lower() in user_artists_lower:
                    original_name = next(a for a in user_artists if a.lower() == result['name'].lower())
                    matches_found.append((original_name, result['match']))
            
            if matches_found:
                print(f"   ✅ Found {len(matches_found)} artists from your data:")
                for name, score in matches_found:
                    print(f"      • {name} ({score:.3f})")
            else:
                print(f"   ❌ No artists from your data found in ANYUJIN's Last.fm results")
        
        except Exception as e:
            print(f"   ⚠️  Could not cross-reference with your data: {e}")
        
    except Exception as e:
        print(f"❌ Error testing ANYUJIN: {e}")

if __name__ == "__main__":
    test_anyujin_lastfm()