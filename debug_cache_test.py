#!/usr/bin/env python3
"""
Debug script to test Last.fm caching behavior.
Tests if cache is working properly and if there are any issues with cache keys or line terminators.
"""

import os
import sys
import json
import time
os.chdir('/home/jacob/Spotify-Data-Visualizations')

from config_loader import AppConfig
from lastfm_utils import LastfmAPI

def debug_cache_behavior():
    """Test Last.fm caching behavior step by step."""
    print("🔍 Debugging Last.fm Cache Behavior")
    print("=" * 50)
    
    # Initialize Last.fm API
    config = AppConfig()
    lastfm_config = config.get_lastfm_config()
    
    if not lastfm_config['api_key']:
        print("❌ Last.fm API key not found")
        return
    
    print(f"📁 Cache directory: {lastfm_config['cache_dir']}")
    print(f"📄 Cache file: {os.path.join(lastfm_config['cache_dir'], 'lastfm_cache.json')}")
    
    # Check cache file before initialization
    cache_file = os.path.join(lastfm_config['cache_dir'], 'lastfm_cache.json')
    if os.path.exists(cache_file):
        file_size = os.path.getsize(cache_file)
        print(f"📊 Cache file exists: {file_size:,} bytes")
        
        # Check for line terminator issues
        with open(cache_file, 'rb') as f:
            first_1000_bytes = f.read(1000)
            print(f"🔍 First 1000 bytes contain:")
            print(f"   - \\r\\n (Windows): {first_1000_bytes.count(b'\\r\\n')} instances")
            print(f"   - \\n (Unix): {first_1000_bytes.count(b'\\n') - first_1000_bytes.count(b'\\r\\n')} instances")
            print(f"   - \\r (Mac): {first_1000_bytes.count(b'\\r') - first_1000_bytes.count(b'\\r\\n')} instances")
        
        # Try to load cache manually
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            print(f"✅ Cache loaded successfully: {len(cache_data)} entries")
            
            # Show some cache keys
            keys = list(cache_data.keys())[:5]
            print(f"📋 Sample cache keys:")
            for key in keys:
                print(f"   {key}")
                
        except Exception as e:
            print(f"❌ Failed to load cache manually: {e}")
    else:
        print("❌ Cache file does not exist")
    
    # Initialize API (this should load the cache)
    print(f"\n🔧 Initializing Last.fm API...")
    lastfm_api = LastfmAPI(
        lastfm_config['api_key'],
        lastfm_config['api_secret'],
        lastfm_config['cache_dir']
    )
    
    print(f"📦 API cache loaded: {len(lastfm_api.cache)} entries")
    
    # Test artist that should already be cached
    test_artist = "taylor swift"
    print(f"\n🧪 Testing cache for '{test_artist}'...")
    
    # Show manual cache key generation
    params = {'artist': test_artist, 'method': 'artist.getinfo', 'format': 'json'}
    cache_key = lastfm_api._get_cache_key('artist.getinfo', params)
    print(f"🔑 Generated cache key: {cache_key}")
    
    # Check if key exists in cache
    if cache_key in lastfm_api.cache:
        print(f"✅ Cache hit! Key found in cache")
        cache_entry = lastfm_api.cache[cache_key]
        print(f"📅 Cache timestamp: {cache_entry.get('timestamp', 'No timestamp')}")
    else:
        print(f"❌ Cache miss! Key not found in cache")
        print(f"📋 Available keys that might match:")
        for key in lastfm_api.cache.keys():
            if 'taylor' in str(lastfm_api.cache[key]).lower():
                print(f"   {key} (contains 'taylor')")
    
    # Test API call with timing
    print(f"\n⏱️  Testing API call with timing...")
    start_time = time.time()
    
    artist_info = lastfm_api.get_artist_info(test_artist, use_enhanced_matching=False)
    
    end_time = time.time()
    duration = end_time - start_time
    
    if artist_info:
        print(f"✅ API call successful in {duration:.3f} seconds")
        if duration < 0.1:
            print(f"🚀 Fast response suggests cache hit")
        else:
            print(f"🐌 Slow response suggests API call")
    else:
        print(f"❌ API call failed")
    
    # Test similar artists call
    print(f"\n🔗 Testing similar artists cache...")
    start_time = time.time()
    
    similar_artists = lastfm_api.get_similar_artists(test_artist, limit=5, use_enhanced_matching=False)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"📊 Found {len(similar_artists)} similar artists in {duration:.3f} seconds")
    if duration < 0.1:
        print(f"🚀 Fast response suggests cache hit")
    else:
        print(f"🐌 Slow response suggests API call")
    
    # Check cache size after operations
    print(f"\n📈 Cache size after operations: {len(lastfm_api.cache)} entries")

if __name__ == "__main__":
    debug_cache_behavior()