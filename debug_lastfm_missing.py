#!/usr/bin/env python3
"""
Debug Last.fm Missing
=====================
Debug why Last.fm isn't being called for ANYUJIN when we know it should work.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from integrated_network_generator import IntegratedNetworkGenerator
from config_loader import AppConfig
from lastfm_utils import LastfmAPI

def debug_lastfm_missing():
    """Debug why Last.fm isn't being called."""
    print("🔍 Debug Last.fm Missing Issue")
    print("=" * 35)
    
    # Test 1: Direct Last.fm API call (like we did before)
    print("\n1️⃣ Direct Last.fm API Test:")
    try:
        config = AppConfig("configurations.txt")
        lastfm_config = config.get_lastfm_config()
        
        if lastfm_config['enabled'] and lastfm_config['api_key']:
            api = LastfmAPI(
                lastfm_config['api_key'],
                lastfm_config['api_secret'],
                lastfm_config['cache_dir']
            )
            print("✅ Direct Last.fm API initialized")
            
            # Test ANYUJIN directly
            results = api.get_similar_artists("ANYUJIN", limit=10)
            print(f"✅ Direct call: {len(results)} results for ANYUJIN")
            if results:
                print(f"   Sample results: {[r['name'] for r in results[:5]]}")
            
        else:
            print("❌ Last.fm API not configured")
    except Exception as e:
        print(f"❌ Direct Last.fm test failed: {e}")
    
    # Test 2: IntegratedNetworkGenerator Last.fm access
    print("\n2️⃣ IntegratedNetworkGenerator Last.fm Test:")
    try:
        generator = IntegratedNetworkGenerator()
        
        print(f"   Last.fm API object: {generator.lastfm_api}")
        
        if generator.lastfm_api:
            print("✅ Generator has Last.fm API")
            
            # Test the _get_multi_source_similarity method
            print("\n   Testing _get_multi_source_similarity for ANYUJIN:")
            similarity_data = generator._get_multi_source_similarity("ANYUJIN")
            
            print(f"   Similarity data keys: {list(similarity_data.keys())}")
            for source, results in similarity_data.items():
                print(f"      {source}: {len(results)} results")
                if results and source == 'lastfm':
                    print(f"         Sample: {[r.get('name', 'unknown') for r in results[:3]]}")
        else:
            print("❌ Generator does NOT have Last.fm API")
            
    except Exception as e:
        print(f"❌ Generator Last.fm test failed: {e}")
    
    # Test 3: Check if Last.fm is being silently skipped
    print("\n3️⃣ Check for Silent Last.fm Skipping:")
    
    # Enable more detailed logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        generator = IntegratedNetworkGenerator()
        
        # Call the method with debug logging
        print("   Calling _get_multi_source_similarity with debug logging...")
        similarity_data = generator._get_multi_source_similarity("ANYUJIN")
        
        print(f"   Final result: {[(k, len(v)) for k, v in similarity_data.items()]}")
        
    except Exception as e:
        print(f"❌ Debug logging test failed: {e}")

if __name__ == "__main__":
    debug_lastfm_missing()