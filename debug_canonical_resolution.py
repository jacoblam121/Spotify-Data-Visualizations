#!/usr/bin/env python3
"""
Debug the canonical resolution step to see all tested variants
"""

from lastfm_utils import LastfmAPI
from config_loader import AppConfig
import logging

# Enable debug logging to see all variants tested
logging.basicConfig(level=logging.DEBUG)

def debug_canonical_resolution():
    """Debug what's happening in the canonical resolution."""
    
    print("🔍 Debug Canonical Resolution for ANYUJIN")
    print("=" * 45)
    
    config = AppConfig()
    lastfm_config = config.get_lastfm_config()
    api = LastfmAPI(lastfm_config['api_key'], lastfm_config['api_secret'])
    
    print("Testing enhanced matching with debug output...")
    
    # This should trigger the canonical resolution and show us all variants tested
    results = api.get_similar_artists('ANYUJIN', limit=50, use_enhanced_matching=True)
    
    print(f"\nFinal result: {len(results)} similar artists")
    if results:
        print(f"Sample results: {[r['name'] for r in results[:5]]}")
        
        # Check if any results have metadata about which variant was chosen
        if results[0].get('_matched_variant'):
            print(f"Matched variant: {results[0]['_matched_variant']}")
            if results[0].get('_canonical_listeners'):
                print(f"Canonical listeners: {results[0]['_canonical_listeners']:,}")

if __name__ == "__main__":
    debug_canonical_resolution()