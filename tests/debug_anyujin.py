"""
Debug ANYUJIN Artist Name Issue
===============================

Investigates why ANYUJIN is not found by Last.fm API even though the artist
exists at https://www.last.fm/music/AnYujin
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI


def test_anyujin_variants():
    """Test different ANYUJIN name variants."""
    print("🔍 Testing ANYUJIN name variants...")
    
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test different variants based on the Last.fm URL
        test_variants = [
            'ANYUJIN',      # Current failing form
            'AnYujin',      # From Last.fm URL
            'anyujin',      # lowercase
            'Anyujin',      # Title case
            'An Yujin',     # With space
            'AN YUJIN',     # All caps with space
            'An-Yujin',     # With hyphen
            'AnyuJin',      # Different capitalization
            'ANYUJIN (IVE)',# With group name
            'AnYujin (IVE)',# Combination
            'An Yujin (IVE)',# With space and group
        ]
        
        print(f"Testing {len(test_variants)} variants:")
        
        successful_variants = []
        
        for i, variant in enumerate(test_variants, 1):
            print(f"\n{i:2d}. Testing: '{variant}'")
            
            try:
                # Test artist info first (faster than similar artists)
                artist_info = lastfm_api.get_artist_info(variant, use_enhanced_matching=False)
                
                if artist_info:
                    print(f"    ✅ Artist info found!")
                    print(f"    📊 Listeners: {artist_info.get('listeners', 'N/A'):,}")
                    print(f"    🎵 Playcount: {artist_info.get('playcount', 'N/A'):,}")
                    print(f"    🏷️  Tags: {[tag['name'] for tag in artist_info.get('tags', [])[:3]]}")
                    successful_variants.append(variant)
                    
                    # Also test similar artists if info worked
                    similar = lastfm_api.get_similar_artists(variant, limit=5, use_enhanced_matching=False)
                    if similar:
                        print(f"    🎯 Similar artists: {len(similar)} found")
                        for j, s in enumerate(similar[:3], 1):
                            print(f"       {j}. {s['name']}: {s['match']:.3f}")
                    else:
                        print(f"    ⚠️  No similar artists found (but info exists)")
                else:
                    print(f"    ❌ Artist info not found")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        print(f"\n📊 Summary:")
        print(f"   Successful variants: {len(successful_variants)}")
        for variant in successful_variants:
            print(f"   ✅ '{variant}'")
        
        if successful_variants:
            print(f"\n💡 Recommendation: Add these variants to K-pop patterns")
            return successful_variants
        else:
            print(f"\n⚠️  No working variants found - may need different approach")
            return []
        
    except Exception as e:
        print(f"❌ Error testing ANYUJIN variants: {e}")
        import traceback
        traceback.print_exc()
        return []


def main():
    print("=" * 70)
    print("ANYUJIN ARTIST NAME DEBUGGING")
    print("=" * 70)
    
    successful_variants = test_anyujin_variants()
    
    if successful_variants:
        print(f"\n🎉 Found working variants for ANYUJIN!")
        print(f"   Best variant: '{successful_variants[0]}'")
    else:
        print(f"\n❌ No working variants found")
        print(f"   Manual check: https://www.last.fm/music/AnYujin")


if __name__ == "__main__":
    # Change to main directory for proper file access
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        main()
    finally:
        os.chdir(original_dir)