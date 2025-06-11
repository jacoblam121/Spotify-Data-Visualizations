"""
Test Phase 1A: ARTMS Fix and Enhanced Last.fm Data Fetching
===========================================================

This test validates that ARTMS and other problematic artists now work correctly,
and that we can fetch all required data (listeners, playcount, images) from Last.fm.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from config_loader import AppConfig
from lastfm_utils import LastfmAPI
import json

# Get the parent directory path for config file
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PARENT_DIR, 'configurations.txt')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def print_separator(title, char="=", width=70):
    """Print a formatted separator."""
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}")


def test_artms_fix():
    """Test that ARTMS now returns similar artists."""
    print_separator("TESTING ARTMS FIX")
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        if not lastfm_config.get('enabled') or not lastfm_config.get('api_key'):
            print("❌ Last.fm API not configured")
            return False
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        print("🎵 Testing ARTMS artist...")
        
        # Test similar artists
        similar = lastfm_api.get_similar_artists('ARTMS', limit=10, use_enhanced_matching=True)
        
        if similar:
            matched_variant = similar[0].get('_matched_variant', 'ARTMS')
            print(f"✅ SUCCESS: Found {len(similar)} similar artists")
            print(f"🎯 Using variant: '{matched_variant}'")
            print(f"\n📊 Top 5 similar artists:")
            for i, s in enumerate(similar[:5], 1):
                print(f"   {i}. {s['name']}: {s['match']:.3f}")
            return True
        else:
            print(f"❌ FAILED: No similar artists found for ARTMS")
            return False
            
    except Exception as e:
        print(f"❌ Error testing ARTMS: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_artist_info_fetching():
    """Test fetching complete artist information including listeners and images."""
    print_separator("TESTING ARTIST INFO FETCHING")
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test various artists including problematic ones
        test_artists = ['ARTMS', 'ILLIT', 'IVE', 'Taylor Swift', 'ANYUJIN', 'KISS OF LIFE']
        results = {}
        
        for artist in test_artists:
            print(f"\n🎵 Fetching info for: {artist}")
            
            # Get artist info with enhanced matching
            info = lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
            
            if info:
                results[artist] = {
                    'success': True,
                    'listeners': info.get('listeners', 0),
                    'playcount': info.get('playcount', 0),
                    'has_image': bool(info.get('images', {}).get('large')),
                    'tags': [tag['name'] for tag in info.get('tags', [])[:3]],
                    'matched_variant': info.get('_matched_variant', artist)
                }
                
                print(f"   ✅ SUCCESS")
                print(f"   👥 Listeners: {info.get('listeners', 0):,}")
                print(f"   ▶️  Playcount: {info.get('playcount', 0):,}")
                print(f"   🖼️  Has image: {'Yes' if info.get('images', {}).get('large') else 'No'}")
                print(f"   🏷️  Tags: {', '.join(results[artist]['tags']) or 'None'}")
                if info.get('_matched_variant') != artist:
                    print(f"   🎯 Matched variant: '{info.get('_matched_variant')}'")
            else:
                results[artist] = {'success': False}
                print(f"   ❌ FAILED: Could not fetch artist info")
        
        # Summary
        print_separator("ARTIST INFO SUMMARY")
        successful = sum(1 for r in results.values() if r.get('success', False))
        print(f"Success rate: {successful}/{len(test_artists)} ({successful/len(test_artists)*100:.0f}%)")
        
        # Show data quality
        print("\n📊 Data Quality Check:")
        for artist, data in results.items():
            if data.get('success'):
                quality_score = 0
                if data['listeners'] > 0: quality_score += 1
                if data['playcount'] > 0: quality_score += 1
                if data['has_image']: quality_score += 1
                if data['tags']: quality_score += 1
                
                print(f"   {artist}: {quality_score}/4 data points")
        
        return successful == len(test_artists)
        
    except Exception as e:
        print(f"❌ Error testing artist info: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_comprehensive_data_fetching():
    """Test fetching all data needed for network visualization."""
    print_separator("COMPREHENSIVE DATA FETCHING TEST")
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Simulate what network_utils.py will need
        print("📊 Simulating network data requirements...")
        
        test_artist = 'ARTMS'
        print(f"\n🎵 Testing comprehensive data for: {test_artist}")
        
        # 1. Get similar artists
        similar = lastfm_api.get_similar_artists(test_artist, limit=5, use_enhanced_matching=True)
        print(f"   ✓ Similar artists: {len(similar) if similar else 0}")
        
        # 2. Get artist info (for listeners, images, etc.)
        info = lastfm_api.get_artist_info(test_artist, use_enhanced_matching=True)
        if info:
            print(f"   ✓ Artist info fetched")
            print(f"     - Listeners: {info.get('listeners', 0):,}")
            print(f"     - Image URL: {info.get('images', {}).get('large', 'None')[:50]}...")
        
        # 3. Get tags for genre classification
        tags = lastfm_api.get_artist_tags(test_artist)
        print(f"   ✓ Tags: {len(tags) if tags else 0}")
        if tags:
            print(f"     - Top tags: {', '.join(t['name'] for t in tags[:3])}")
        
        # Validate we have everything needed
        has_similar = bool(similar)
        has_listeners = info and info.get('listeners', 0) > 0
        has_image = info and bool(info.get('images', {}).get('large'))
        has_tags = bool(tags)
        
        print(f"\n✅ Data Completeness Check:")
        print(f"   Similar artists: {'✓' if has_similar else '✗'}")
        print(f"   Listener count: {'✓' if has_listeners else '✗'}")
        print(f"   Artist image: {'✓' if has_image else '✗'}")
        print(f"   Genre tags: {'✓' if has_tags else '✗'}")
        
        return all([has_similar, has_listeners])  # Image and tags are optional
        
    except Exception as e:
        print(f"❌ Error in comprehensive test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 1A tests."""
    print("=" * 70)
    print("PHASE 1A: ARTMS FIX & ENHANCED DATA FETCHING")
    print("=" * 70)
    
    # Track test results
    tests_passed = 0
    tests_total = 3
    
    # Test 1: ARTMS Fix
    if test_artms_fix():
        tests_passed += 1
    
    # Test 2: Artist Info Fetching
    if test_artist_info_fetching():
        tests_passed += 1
    
    # Test 3: Comprehensive Data
    if test_comprehensive_data_fetching():
        tests_passed += 1
    
    # Final Assessment
    print_separator("PHASE 1A FINAL ASSESSMENT")
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\n🎉 PHASE 1A COMPLETE!")
        print("   ✅ ARTMS artist is now working")
        print("   ✅ Enhanced data fetching is functional")
        print("   ✅ Ready to proceed to Phase 1B")
    else:
        print("\n⚠️  PHASE 1A INCOMPLETE")
        print("   Some tests failed. Please review the output above.")
    
    return tests_passed == tests_total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)