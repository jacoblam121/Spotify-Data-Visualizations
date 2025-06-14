#!/usr/bin/env python3
"""
Test the exact AnYujin profile the user mentioned
"""

from lastfm_utils import LastfmAPI
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_loader import AppConfig

def test_anyujin_direct():
    """Test direct API calls for various ANYUJIN spellings."""
    
    print("🔍 Testing Direct AnYujin API Calls")
    print("=" * 40)
    
    # Initialize Last.fm API
    config = AppConfig()
    try:
        lastfm_config = config.get_lastfm_config()
        api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret']
        )
        print("✅ Last.fm API initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Last.fm API: {e}")
        return
    
    # Test different spellings that might match the 6.8K listener profile
    test_variants = [
        "AnYujin",      # User's suggested spelling
        "An Yujin",     # Space variant
        "Ahn Yujin",    # Current system choice (81 listeners)
        "안유진",        # Korean
        "ANYUJIN",      # Original
        "AN YUJIN",     # All caps with space
        "Yujin",        # Short form
        "IVE AnYujin",  # With group name
        "AnYujin IVE",  # Different order
    ]
    
    results = []
    
    for variant in test_variants:
        print(f"\n🧪 Testing '{variant}':")
        
        try:
            # Test artist.getinfo first to see if the artist exists
            info_params = {'artist': variant}
            info_response = api._make_request('artist.getinfo', info_params)
            
            if info_response and 'artist' in info_response:
                artist_info = info_response['artist']
                listeners = int(artist_info['stats']['listeners'])
                name = artist_info['name']
                mbid = artist_info.get('mbid', '')
                
                print(f"   ✅ Artist exists: '{name}'")
                print(f"   👥 Listeners: {listeners:,}")
                if mbid:
                    print(f"   🆔 MBID: {mbid}")
                
                # Now test similar artists
                similar_params = {'artist': variant, 'limit': '10'}
                similar_response = api._make_request('artist.getsimilar', similar_params)
                
                similar_count = 0
                if similar_response and 'similarartists' in similar_response:
                    similar_artists = similar_response['similarartists'].get('artist', [])
                    similar_count = len(similar_artists) if isinstance(similar_artists, list) else (1 if similar_artists else 0)
                
                print(f"   🔗 Similar artists: {similar_count}")
                
                results.append({
                    'variant': variant,
                    'canonical_name': name,
                    'listeners': listeners,
                    'similar_count': similar_count,
                    'mbid': mbid
                })
                
                # If this has high listener count, show similar artists
                if listeners > 1000:
                    print(f"   🎯 HIGH LISTENER COUNT - showing similar artists:")
                    if similar_count > 0:
                        for i, sim in enumerate(similar_artists[:5], 1):
                            sim_name = sim['name'] if isinstance(sim, dict) else str(sim)
                            print(f"      {i}. {sim_name}")
                    
            else:
                print(f"   ❌ Artist not found or API error")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"=" * 40)
    
    if results:
        # Sort by listener count
        results.sort(key=lambda x: x['listeners'], reverse=True)
        
        print(f"Found {len(results)} valid artist profiles:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. '{result['canonical_name']}' ({result['listeners']:,} listeners, {result['similar_count']} similar)")
            print(f"      Query: '{result['variant']}'")
        
        # Identify the best candidate
        if results[0]['listeners'] > 1000:
            best = results[0]
            print(f"\n🏆 BEST CANDIDATE: '{best['canonical_name']}'")
            print(f"   Listeners: {best['listeners']:,}")
            print(f"   Query variant: '{best['variant']}'")
            print(f"   Similar artists: {best['similar_count']}")
            
            if best['listeners'] > results[1]['listeners'] * 10:
                print(f"   ⚠️  This has 10x+ more listeners than second choice!")
                print(f"      The scoring system should definitely pick this one.")
    else:
        print("No valid artist profiles found.")

if __name__ == "__main__":
    test_anyujin_direct()