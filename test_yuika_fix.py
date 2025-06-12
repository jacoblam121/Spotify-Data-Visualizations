#!/usr/bin/env python3
import logging
from lastfm_utils import LastfmAPI

# Set up logging to see the debug info
logging.basicConfig(level=logging.INFO)

def test_yuika():
    api = LastfmAPI('1e8f179baf2593c1ec228bf7eba1bfa4', '2b04ee3940408d3c13ff58ee5567ebd4')
    
    test_cases = ['ユイカ', 'blackbear']
    
    for artist in test_cases:
        print(f"\n🧪 Testing {artist} with enhanced matching...")
        result = api.get_artist_info(artist, use_enhanced_matching=True)
        
        if result:
            print(f"✅ Found: {result['name']}")
            print(f"   Listeners: {result.get('listeners', 0):,}")
            print(f"   Method: {result.get('_resolution_method', 'unknown')}")
            print(f"   Variant: {result.get('_matched_variant', 'unknown')}")
            print(f"   URL: {result.get('url', 'N/A')}")
        else:
            print("❌ No result found")

if __name__ == "__main__":
    test_yuika()