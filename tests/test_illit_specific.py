"""
Test ILLIT Artist Specifically
==============================

Tests both similar artists and artist info for ILLIT to understand the issue.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI

# Get the parent directory path for config file
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PARENT_DIR, 'configurations.txt')


def test_illit():
    """Test ILLIT comprehensively."""
    print("=" * 70)
    print("TESTING ILLIT ARTIST")
    print("=" * 70)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        print("\n1️⃣ Testing Artist Info:")
        info = lastfm_api.get_artist_info('ILLIT', use_enhanced_matching=True)
        if info:
            print(f"   ✅ Artist info found")
            print(f"   Name: {info.get('name')}")
            print(f"   Listeners: {info.get('listeners', 0):,}")
            print(f"   Playcount: {info.get('playcount', 0):,}")
            print(f"   Matched variant: {info.get('_matched_variant', 'ILLIT')}")
        else:
            print(f"   ❌ No artist info found")
        
        print("\n2️⃣ Testing Similar Artists (with enhanced matching):")
        similar = lastfm_api.get_similar_artists('ILLIT', limit=10, use_enhanced_matching=True)
        if similar:
            print(f"   ✅ Found {len(similar)} similar artists")
            print(f"   Using variant: {similar[0].get('_matched_variant', 'ILLIT')}")
            for i, s in enumerate(similar[:5], 1):
                print(f"   {i}. {s['name']}: {s['match']:.3f}")
        else:
            print(f"   ❌ No similar artists found")
        
        print("\n3️⃣ Testing Similar Artists (without enhanced matching):")
        similar_standard = lastfm_api.get_similar_artists('ILLIT', limit=10, use_enhanced_matching=False)
        if similar_standard:
            print(f"   ✅ Found {len(similar_standard)} similar artists")
        else:
            print(f"   ❌ No similar artists found")
        
        print("\n4️⃣ Testing Name Variants:")
        variants = lastfm_api._generate_name_variants('ILLIT')
        print(f"   Generated {len(variants)} variants")
        print(f"   First 10 variants:")
        for i, v in enumerate(variants[:10], 1):
            print(f"   {i:2d}. '{v}'")
        
        # Try each variant manually for similar artists
        print("\n5️⃣ Testing Each Variant Manually:")
        found_working_variant = False
        for variant in variants[:10]:  # Test first 10 variants
            # Clear cache for this specific call to force fresh API call
            params = {'artist': variant, 'limit': 1}
            method = 'artist.getsimilar'
            cache_key = lastfm_api._get_cache_key(method, params)
            if cache_key in lastfm_api.cache:
                del lastfm_api.cache[cache_key]
            
            # Try the variant
            response = lastfm_api._make_request(method, params)
            if response and 'similarartists' in response and response['similarartists'].get('artist'):
                print(f"   ✅ Variant '{variant}' returns similar artists!")
                found_working_variant = True
                break
            else:
                print(f"   ❌ Variant '{variant}' - no similar artists")
        
        if not found_working_variant:
            print("\n   ⚠️  No variant found that returns similar artists")
            print("   This suggests Last.fm's similar artists data for ILLIT is incomplete")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_illit()