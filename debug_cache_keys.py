#!/usr/bin/env python3
"""
Debug script to investigate cache key generation and why certain calls aren't hitting the cache.
"""

import os
import sys
import json
import hashlib
os.chdir('/home/jacob/Spotify-Data-Visualizations')

from config_loader import AppConfig
from lastfm_utils import LastfmAPI

def debug_cache_keys():
    """Debug cache key generation to find why some calls aren't cached."""
    print("🔍 Debugging Cache Key Generation")
    print("=" * 50)
    
    # Initialize Last.fm API
    config = AppConfig()
    lastfm_config = config.get_lastfm_config()
    
    lastfm_api = LastfmAPI(
        lastfm_config['api_key'],
        lastfm_config['api_secret'],
        lastfm_config['cache_dir']
    )
    
    print(f"📦 Cache loaded: {len(lastfm_api.cache)} entries")
    
    # Test different parameter combinations that might be in cache
    test_artist = "taylor swift"
    test_cases = [
        # artist.getinfo variations
        ("artist.getinfo", {"artist": test_artist}),
        ("artist.getinfo", {"artist": test_artist, "format": "json"}),
        ("artist.getinfo", {"artist": "Taylor Swift"}),
        ("artist.getinfo", {"artist": "TAYLOR SWIFT"}),
        
        # artist.getsimilar variations
        ("artist.getsimilar", {"artist": test_artist, "limit": "5"}),
        ("artist.getsimilar", {"artist": test_artist, "limit": "20"}),
        ("artist.getsimilar", {"artist": test_artist, "limit": "100"}),
        ("artist.getsimilar", {"artist": "Taylor Swift", "limit": "100"}),
        ("artist.getsimilar", {"artist": test_artist}),
    ]
    
    print(f"\n🔑 Testing cache key generation for '{test_artist}':")
    print("-" * 60)
    
    for method, params in test_cases:
        # Generate cache key manually
        cache_key = lastfm_api._get_cache_key(method, params)
        
        # Check if it exists in cache
        cache_hit = cache_key in lastfm_api.cache
        
        print(f"\n📝 Method: {method}")
        print(f"   Params: {params}")
        print(f"   Key: {cache_key}")
        print(f"   Cache hit: {'✅ YES' if cache_hit else '❌ NO'}")
        
        if cache_hit:
            cache_entry = lastfm_api.cache[cache_key]
            timestamp = cache_entry.get('timestamp', 'No timestamp')
            print(f"   Timestamp: {timestamp}")
    
    # Find actual cache keys for Taylor Swift
    print(f"\n🕵️  Analyzing actual cache entries for Taylor Swift...")
    print("-" * 60)
    
    taylor_keys = []
    for key, value in lastfm_api.cache.items():
        data_str = json.dumps(value).lower()
        if 'taylor swift' in data_str or 'taylor' in data_str:
            taylor_keys.append((key, value))
    
    print(f"Found {len(taylor_keys)} cache entries related to Taylor Swift")
    
    # Show first few entries to understand the structure
    for i, (key, value) in enumerate(taylor_keys[:10]):
        print(f"\n{i+1}. Key: {key}")
        print(f"   Timestamp: {value.get('timestamp', 'No timestamp')}")
        
        # Try to identify what API call this was
        if 'data' in value:
            data = value['data']
            if 'artist' in data:
                artist_data = data['artist']
                artist_name = artist_data.get('name', 'Unknown')
                print(f"   Artist name: {artist_name}")
                
                # Check if it has similar artists (indicating getsimilar call)
                if 'similar' in artist_data and artist_data['similar']:
                    print(f"   Type: artist.getinfo (with similar)")
                elif 'stats' in artist_data:
                    print(f"   Type: artist.getinfo")
                else:
                    print(f"   Type: Unknown")
                    
            elif 'similarartists' in data:
                print(f"   Type: artist.getsimilar")
                similar_count = len(data['similarartists'].get('artist', []))
                print(f"   Similar artists: {similar_count}")
            else:
                print(f"   Type: Unknown structure")
        else:
            print(f"   No data field found")
    
    # Test manual cache key recreation for existing entries
    print(f"\n🔧 Reverse engineering cache keys...")
    print("-" * 60)
    
    # Let's try to recreate some of these keys manually
    for i, (actual_key, value) in enumerate(taylor_keys[:3]):
        print(f"\nEntry {i+1}: {actual_key}")
        
        # Try different parameter combinations to see if we can recreate this key
        possible_params = [
            {"artist": "taylor swift"},
            {"artist": "Taylor Swift"},
            {"artist": "TAYLOR SWIFT"},
            {"artist": "taylor swift", "limit": "5"},
            {"artist": "taylor swift", "limit": "20"},
            {"artist": "taylor swift", "limit": "100"},
            {"artist": "Taylor Swift", "limit": "100"},
        ]
        
        possible_methods = ["artist.getinfo", "artist.getsimilar", "artist.search"]
        
        found_match = False
        for method in possible_methods:
            for params in possible_params:
                test_key = lastfm_api._get_cache_key(method, params)
                if test_key == actual_key:
                    print(f"   ✅ MATCH: {method} with {params}")
                    found_match = True
                    break
            if found_match:
                break
        
        if not found_match:
            print(f"   ❌ No matching parameters found")

if __name__ == "__main__":
    debug_cache_keys()