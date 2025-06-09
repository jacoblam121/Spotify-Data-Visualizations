"""
Test Robust Artist Matching System
==================================

Comprehensive test of the enhanced robust matching system for all problematic artists.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from config_loader import AppConfig
from lastfm_utils import LastfmAPI

# Set up detailed logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_problematic_artists():
    """Test all known problematic artists."""
    print("🧪 Testing Robust Matching System")
    print("=" * 50)
    
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test all previously problematic artists
        test_artists = [
            'IVE',          # Fixed in phase 1
            'ANYUJIN',      # Fixed in phase 2
            'KISS OF LIFE', # New fix
            'JEON SOMI',    # New fix
            'TWICE',        # Should work (control)
            'Taylor Swift', # Should work (control)
        ]
        
        print(f"Testing {len(test_artists)} artists with robust matching...\n")
        
        results = {}
        
        for i, artist in enumerate(test_artists, 1):
            print(f"{i}. Testing: {artist}")
            print("   " + "─" * 45)
            
            # Test with enhanced matching
            similar_artists = lastfm_api.get_similar_artists(artist, limit=10, use_enhanced_matching=True)
            
            if similar_artists:
                matched_variant = similar_artists[0].get('_matched_variant', artist)
                print(f"   ✅ SUCCESS: {len(similar_artists)} similar artists found")
                print(f"   🎯 Using variant: '{matched_variant}'")
                print(f"   🎵 Top 3 similar:")
                for j, s in enumerate(similar_artists[:3], 1):
                    print(f"      {j}. {s['name']}: {s['match']:.3f}")
                
                results[artist] = {
                    'success': True,
                    'variant': matched_variant,
                    'count': len(similar_artists),
                    'top_similar': [s['name'] for s in similar_artists[:3]]
                }
            else:
                print(f"   ❌ FAILED: No similar artists found")
                results[artist] = {
                    'success': False,
                    'variant': None,
                    'count': 0,
                    'top_similar': []
                }
            
            print()  # Blank line for readability
        
        # Summary
        print("📊 ROBUST MATCHING RESULTS")
        print("=" * 50)
        
        successful = sum(1 for r in results.values() if r['success'])
        total = len(test_artists)
        
        print(f"Overall success rate: {successful}/{total} ({successful/total*100:.1f}%)")
        print()
        
        for artist, result in results.items():
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            print(f"{artist}: {status}")
            if result['success']:
                print(f"   Variant: '{result['variant']}'")
                print(f"   Similar: {result['count']}")
                print(f"   Top matches: {', '.join(result['top_similar'])}")
            print()
        
        # Specific validation for previously problematic artists
        problematic_fixed = 0
        problematic_artists = ['IVE', 'ANYUJIN', 'KISS OF LIFE', 'JEON SOMI']
        
        for artist in problematic_artists:
            if results.get(artist, {}).get('success'):
                problematic_fixed += 1
        
        print(f"🎯 PROBLEMATIC ARTISTS STATUS:")
        print(f"   Fixed: {problematic_fixed}/{len(problematic_artists)} ({problematic_fixed/len(problematic_artists)*100:.1f}%)")
        
        if problematic_fixed == len(problematic_artists):
            print(f"   🎉 ALL PROBLEMATIC ARTISTS ARE NOW WORKING!")
        elif problematic_fixed > 0:
            print(f"   📈 Significant improvement achieved")
        else:
            print(f"   ⚠️  System needs further enhancement")
        
        return results
        
    except Exception as e:
        print(f"❌ Error testing robust matching: {e}")
        import traceback
        traceback.print_exc()
        return {}


def test_variant_generation_coverage():
    """Test the comprehensiveness of variant generation."""
    print("🔍 Testing Variant Generation Coverage")
    print("=" * 50)
    
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        test_cases = [
            'KISS OF LIFE',
            'JEON SOMI', 
            'twenty one pilots',
            'The Beatles',
            'bbno$',
            'Against The Current'
        ]
        
        for artist in test_cases:
            variants = lastfm_api._generate_name_variants(artist)
            print(f"\n🎵 {artist} → {len(variants)} variants generated")
            
            # Show first 10 variants
            for i, variant in enumerate(variants[:10], 1):
                print(f"   {i:2d}. '{variant}'")
            
            if len(variants) > 10:
                print(f"   ... and {len(variants) - 10} more variants")
        
    except Exception as e:
        print(f"❌ Error testing variant generation: {e}")


def main():
    print("=" * 70)
    print("ROBUST ARTIST MATCHING SYSTEM - COMPREHENSIVE TEST")
    print("=" * 70)
    
    # Test problematic artists
    results = test_problematic_artists()
    
    # Test variant generation coverage
    test_variant_generation_coverage()
    
    print("\n" + "=" * 70)
    print("FINAL ASSESSMENT")
    print("=" * 70)
    
    if results:
        all_working = all(r['success'] for r in results.values())
        
        if all_working:
            print("🎉 SYSTEM STATUS: FULLY ROBUST")
            print("   All tested artists working correctly")
            print("   Enhanced matching system is comprehensive")
        else:
            failing = [artist for artist, result in results.items() if not result['success']]
            print(f"⚠️  SYSTEM STATUS: NEEDS IMPROVEMENT")
            print(f"   Still failing: {', '.join(failing)}")
        
        print(f"\n💡 Network building should now work with:")
        working_artists = [artist for artist, result in results.items() if result['success']]
        for artist in working_artists:
            variant = results[artist]['variant']
            print(f"   ✅ {artist} (using '{variant}')")


if __name__ == "__main__":
    # Change to main directory for proper file access
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        main()
    finally:
        os.chdir(original_dir)