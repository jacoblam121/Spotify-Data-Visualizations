"""
Test Enhanced Name Matching System
==================================

Comprehensive test for the enhanced K-pop name matching system we implemented
to fix the IVE artist name issue. Tests multiple name variants and validates
that previously failing artists now work correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from config_loader import AppConfig
from lastfm_utils import LastfmAPI

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def print_separator(title, char="=", width=70):
    """Print a formatted separator."""
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}")


def test_kpop_artists():
    """Test the K-pop artists that were previously problematic."""
    print_separator("TESTING K-POP ARTISTS WITH ENHANCED MATCHING")
    
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        if not lastfm_config.get('enabled') or not lastfm_config.get('api_key'):
            print("❌ Last.fm API not configured")
            return
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test problematic artists that should now work
        test_artists = [
            'IVE',           # Main problem case
            'TWICE',         # Known working case for comparison
            'BLACKPINK',     # Another K-pop test
            'NewJeans',      # Case sensitivity test
            'LE SSERAFIM',   # Complex name test
            'BTS',           # Very popular K-pop group
            '(G)I-DLE',      # Special characters test
        ]
        
        print(f"🧪 Testing {len(test_artists)} K-pop artists...")
        
        results = {}
        
        for i, artist in enumerate(test_artists, 1):
            print(f"\n{i}. Testing: {artist}")
            print(f"   {'─' * 50}")
            
            # Test with enhanced matching enabled (default)
            print(f"   🔧 Enhanced matching: ON")
            similar_enhanced = lastfm_api.get_similar_artists(artist, limit=10, use_enhanced_matching=True)
            
            if similar_enhanced:
                matched_variant = similar_enhanced[0].get('_matched_variant', artist)
                print(f"   ✅ Found {len(similar_enhanced)} similar artists using variant: '{matched_variant}'")
                print(f"   🎵 Top similar artists:")
                for j, similar in enumerate(similar_enhanced[:5], 1):
                    print(f"      {j}. {similar['name']}: {similar['match']:.3f}")
                
                results[artist] = {
                    'enhanced_success': True,
                    'matched_variant': matched_variant,
                    'similar_count': len(similar_enhanced),
                    'top_similar': [s['name'] for s in similar_enhanced[:3]]
                }
            else:
                print(f"   ❌ No similar artists found even with enhanced matching")
                results[artist] = {
                    'enhanced_success': False,
                    'matched_variant': None,
                    'similar_count': 0,
                    'top_similar': []
                }
            
            # Test with enhanced matching disabled for comparison
            print(f"   🔧 Enhanced matching: OFF")
            similar_standard = lastfm_api.get_similar_artists(artist, limit=10, use_enhanced_matching=False)
            
            if similar_standard:
                print(f"   ✅ Found {len(similar_standard)} similar artists with standard matching")
                results[artist]['standard_success'] = True
                results[artist]['standard_count'] = len(similar_standard)
            else:
                print(f"   ❌ No similar artists found with standard matching")
                results[artist]['standard_success'] = False
                results[artist]['standard_count'] = 0
        
        # Summary
        print_separator("ENHANCED MATCHING RESULTS SUMMARY")
        
        enhanced_successes = sum(1 for r in results.values() if r['enhanced_success'])
        standard_successes = sum(1 for r in results.values() if r['standard_success'])
        
        print(f"📊 Overall Results:")
        print(f"   Enhanced matching: {enhanced_successes}/{len(test_artists)} artists successful")
        print(f"   Standard matching: {standard_successes}/{len(test_artists)} artists successful")
        print(f"   Improvement: +{enhanced_successes - standard_successes} additional artists found")
        
        print(f"\n🎯 Detailed Results:")
        for artist, result in results.items():
            enhanced_status = "✅" if result['enhanced_success'] else "❌"
            standard_status = "✅" if result['standard_success'] else "❌"
            
            print(f"   {artist}:")
            print(f"      Standard: {standard_status} ({result['standard_count']} similar)")
            print(f"      Enhanced: {enhanced_status} ({result['similar_count']} similar)")
            
            if result['enhanced_success'] and result['matched_variant']:
                print(f"      Matched using: '{result['matched_variant']}'")
            
            if result['top_similar']:
                print(f"      Top matches: {', '.join(result['top_similar'])}")
            print()
        
        # IVE-specific validation
        if 'IVE' in results and results['IVE']['enhanced_success']:
            print(f"🎉 SUCCESS: IVE artist issue has been FIXED!")
            print(f"   IVE now finds {results['IVE']['similar_count']} similar artists")
            print(f"   Using variant: '{results['IVE']['matched_variant']}'")
        elif 'IVE' in results:
            print(f"⚠️  WARNING: IVE still not working with enhanced matching")
        
        return results
        
    except Exception as e:
        print(f"❌ Error testing K-pop artists: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_name_variant_generation():
    """Test the name variant generation logic."""
    print_separator("TESTING NAME VARIANT GENERATION")
    
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test different types of artist names
        test_cases = [
            'IVE',
            'The Beatles',
            'taylor swift',
            'TWICE',
            'Panic! At The Disco',
            'twenty one pilots',
        ]
        
        print(f"🔍 Testing name variant generation for {len(test_cases)} cases:")
        
        for i, artist in enumerate(test_cases, 1):
            print(f"\n{i}. Artist: '{artist}'")
            variants = lastfm_api._generate_name_variants(artist)
            print(f"   Generated {len(variants)} variants:")
            for j, variant in enumerate(variants, 1):
                print(f"      {j:2d}. '{variant}'")
        
    except Exception as e:
        print(f"❌ Error testing variant generation: {e}")


def test_artist_info_enhancement():
    """Test enhanced matching for artist info endpoint."""
    print_separator("TESTING ENHANCED ARTIST INFO MATCHING")
    
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test artist info for problematic artists
        test_artists = ['IVE', 'NewJeans', 'LE SSERAFIM']
        
        print(f"🔍 Testing artist info enhancement for {len(test_artists)} artists:")
        
        for i, artist in enumerate(test_artists, 1):
            print(f"\n{i}. Testing artist info: {artist}")
            
            # Test with enhancement
            artist_info = lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
            
            if artist_info:
                matched_variant = artist_info.get('_matched_variant', artist)
                print(f"   ✅ Found artist info using variant: '{matched_variant}'")
                print(f"   👥 Listeners: {artist_info.get('listeners', 'N/A'):,}")
                print(f"   🎵 Playcount: {artist_info.get('playcount', 'N/A'):,}")
                print(f"   🏷️  Tags: {[tag['name'] for tag in artist_info.get('tags', [])[:3]]}")
            else:
                print(f"   ❌ No artist info found even with enhancement")
        
    except Exception as e:
        print(f"❌ Error testing artist info enhancement: {e}")


def test_cache_behavior():
    """Test that enhanced matching works with caching."""
    print_separator("TESTING CACHE BEHAVIOR WITH ENHANCED MATCHING")
    
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test artist that should be cached after first lookup
        test_artist = 'IVE'
        
        print(f"🔍 Testing cache behavior for: {test_artist}")
        
        # First lookup (should cache the successful variant)
        print(f"   First lookup (fresh):")
        similar1 = lastfm_api.get_similar_artists(test_artist, limit=5)
        
        if similar1:
            matched_variant1 = similar1[0].get('_matched_variant', test_artist)
            print(f"   ✅ Found {len(similar1)} artists using: '{matched_variant1}'")
        else:
            print(f"   ❌ First lookup failed")
            return
        
        # Second lookup (should use cache)
        print(f"   Second lookup (cached):")
        similar2 = lastfm_api.get_similar_artists(test_artist, limit=5)
        
        if similar2:
            matched_variant2 = similar2[0].get('_matched_variant', test_artist)
            print(f"   ✅ Found {len(similar2)} artists using: '{matched_variant2}'")
            
            # Verify consistency
            if len(similar1) == len(similar2) and matched_variant1 == matched_variant2:
                print(f"   ✅ Cache behavior consistent")
            else:
                print(f"   ⚠️  Cache behavior inconsistent")
                print(f"      First: {len(similar1)} artists, variant '{matched_variant1}'")
                print(f"      Second: {len(similar2)} artists, variant '{matched_variant2}'")
        else:
            print(f"   ❌ Second lookup failed (cache issue?)")
        
    except Exception as e:
        print(f"❌ Error testing cache behavior: {e}")


def main():
    """Run all enhanced matching tests."""
    print_separator("ENHANCED NAME MATCHING - COMPREHENSIVE TEST SUITE", "=", 70)
    print("Testing the enhanced K-pop name matching system to validate IVE fix")
    
    try:
        # Test 1: K-pop artists with enhanced matching
        kpop_results = test_kpop_artists()
        
        # Test 2: Name variant generation
        test_name_variant_generation()
        
        # Test 3: Artist info enhancement
        test_artist_info_enhancement()
        
        # Test 4: Cache behavior
        test_cache_behavior()
        
        # Overall summary
        print_separator("FINAL TEST RESULTS", "=", 70)
        
        if kpop_results:
            total_artists = len(kpop_results)
            enhanced_successes = sum(1 for r in kpop_results.values() if r['enhanced_success'])
            standard_successes = sum(1 for r in kpop_results.values() if r['standard_success'])
            
            print(f"🎯 Enhanced Matching Performance:")
            print(f"   Success rate: {enhanced_successes}/{total_artists} ({enhanced_successes/total_artists*100:.1f}%)")
            print(f"   Improvement over standard: +{enhanced_successes - standard_successes} artists")
            
            if kpop_results.get('IVE', {}).get('enhanced_success'):
                print(f"\n🎉 PRIMARY GOAL ACHIEVED:")
                print(f"   ✅ IVE artist name issue has been FIXED!")
                print(f"   ✅ Enhanced matching system working correctly")
            else:
                print(f"\n⚠️  PRIMARY GOAL NOT ACHIEVED:")
                print(f"   ❌ IVE still not working with enhanced matching")
                print(f"   🔧 Further investigation needed")
        
        print(f"\n💡 Next Steps:")
        print(f"   1. Update manual_test_network.py to use enhanced matching")
        print(f"   2. Test full similarity network building with enhanced matching")
        print(f"   3. Validate that IVE now appears in network connections")
        
    except Exception as e:
        print(f"❌ Unexpected error in test suite: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Change to main directory for proper file access
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Test suite interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original directory
        os.chdir(original_dir)