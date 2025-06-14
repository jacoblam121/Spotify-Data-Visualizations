#!/usr/bin/env python3
"""
Debug why IVE Last.fm similarity is failing
"""

from lastfm_utils import LastfmAPI
from config_loader import AppConfig
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def debug_ive_lastfm():
    """Debug IVE Last.fm API calls."""
    
    print("🔍 Debug IVE Last.fm API Issues")
    print("=" * 35)
    
    config = AppConfig()
    lastfm_config = config.get_lastfm_config()
    api = LastfmAPI(lastfm_config['api_key'], lastfm_config['api_secret'])
    
    print("1️⃣ Testing IVE variants for artist.getinfo:")
    print("-" * 45)
    
    ive_variants = ['IVE', 'ive', 'IVE (아이브)', '아이브']
    
    for variant in ive_variants:
        print(f"\n🧪 Testing getinfo for '{variant}':")
        try:
            params = {'artist': variant}
            response = api._make_request('artist.getinfo', params)
            if response and 'artist' in response:
                artist = response['artist']
                print(f"   ✅ Found: '{artist['name']}'")
                print(f"   👥 Listeners: {artist['stats']['listeners']:,}")
            else:
                print(f"   ❌ Not found or error")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n2️⃣ Testing IVE variants for artist.getsimilar:")
    print("-" * 45)
    
    for variant in ive_variants:
        print(f"\n🧪 Testing getsimilar for '{variant}':")
        try:
            params = {'artist': variant, 'limit': '10'}
            response = api._make_request('artist.getsimilar', params)
            if response and 'similarartists' in response:
                similar = response['similarartists'].get('artist', [])
                count = len(similar) if isinstance(similar, list) else (1 if similar else 0)
                print(f"   ✅ Found {count} similar artists")
                if count > 0 and isinstance(similar, list):
                    print(f"   📝 Sample: {[s['name'] for s in similar[:3]]}")
            else:
                print(f"   ❌ No similar artists or error")
                if response:
                    print(f"      Response keys: {list(response.keys())}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n3️⃣ Testing IVE enhanced matching:")
    print("-" * 45)
    
    print("Testing with use_enhanced_matching=True:")
    try:
        results = api.get_similar_artists('IVE', limit=50, use_enhanced_matching=True)
        print(f"   Enhanced matching: {len(results)} results")
        if results:
            print(f"   Sample: {[r['name'] for r in results[:3]]}")
    except Exception as e:
        print(f"   ❌ Enhanced matching failed: {e}")
    
    print("Testing with use_enhanced_matching=False:")
    try:
        results = api.get_similar_artists('IVE', limit=50, use_enhanced_matching=False)
        print(f"   Direct matching: {len(results)} results")
        if results:
            print(f"   Sample: {[r['name'] for r in results[:3]]}")
    except Exception as e:
        print(f"   ❌ Direct matching failed: {e}")
    
    print(f"\n4️⃣ Testing API rate limiting and cache:")
    print("-" * 45)
    
    # Check if it's a cache issue
    print("Testing cache status...")
    cache_key_info = api._get_cache_key('artist.getsimilar', {'artist': 'IVE', 'limit': '50'})
    if cache_key_info in api.cache:
        print(f"   ✅ IVE is cached")
        cached_data = api.cache[cache_key_info]
        print(f"   📅 Cached on: {cached_data.get('timestamp', 'unknown')}")
    else:
        print(f"   📂 IVE not in cache")
    
    # Test API key
    print("Testing API connectivity...")
    try:
        test_params = {'artist': 'Taylor Swift', 'limit': '5'}
        test_response = api._make_request('artist.getsimilar', test_params)
        if test_response and 'similarartists' in test_response:
            print(f"   ✅ API connectivity working (Taylor Swift test passed)")
        else:
            print(f"   ❌ API connectivity issue")
    except Exception as e:
        print(f"   ❌ API test failed: {e}")

if __name__ == "__main__":
    debug_ive_lastfm()