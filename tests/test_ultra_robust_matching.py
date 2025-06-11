"""
Test Ultra-Robust Matching System
=================================

Tests the complete system with all our improvements:
1. Known pattern database
2. Intelligent type detection
3. Priority-based variant generation
4. Advanced search strategy
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI
import time

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PARENT_DIR, 'configurations.txt')


def test_ultra_robust_system():
    """Test the complete ultra-robust system."""
    print("=" * 100)
    print("ULTRA-ROBUST MATCHING SYSTEM TEST")
    print("=" * 100)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Comprehensive test of all types of problematic artists
        test_artists = [
            # Previously problematic hip-hop artists
            ('mgk', 'Hip-hop abbreviation'),
            ('XXXTENTACION', 'Controversial rap artist'),
            ('blackbear', 'Lowercase rapper'),
            
            # K-pop artists
            ('ARTMS', 'K-pop with Korean variants'),
            ('ILLIT', 'New K-pop group'),
            ('IVE', 'Popular K-pop group'),
            ('MIYEON', 'K-pop soloist with Korean name'),
            ('SUNMI', 'K-pop soloist'),
            
            # J-pop artists  
            ('YOASOBI', 'Japanese duo'),
            ('ヨルシカ', 'Japanese with native script'),
            ('Aimyon', 'Japanese singer-songwriter'),
            
            # Hip-hop collectives
            ('88rising', 'Asian hip-hop collective'),
            
            # Western with special cases
            ('Twenty One Pilots', 'Common abbreviation'),
            ('Panic! At The Disco', 'Punctuation issues'),
            ('bbno$', 'Special characters'),
            
            # Edge cases
            ('P!nk', 'Stylized name'),
            ('Ke$ha', 'Dollar sign'),
            ('Fall Out Boy', 'Common abbreviation'),
            
            # Test some that should definitely work
            ('Taylor Swift', 'Control case'),
            ('The Beatles', 'Classic control'),
        ]
        
        print(f"\nTesting {len(test_artists)} challenging artists...\n")
        print(f"{'Artist':<20} {'Type':<25} {'Time':<8} {'Method':<15} {'Result':<15} {'Working Variant'}")
        print("-" * 120)
        
        results = []
        
        for artist, description in test_artists:
            start_time = time.time()
            
            # Test with full enhanced matching system
            similar = lastfm_api.get_similar_artists(artist, limit=5, use_enhanced_matching=True)
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            # Determine method used
            method = "unknown"
            if similar:
                if similar[0].get('_search_method') == 'advanced_search':
                    method = "advanced_search"
                elif similar[0].get('_matched_variant') != artist:
                    method = "pattern_match"
                else:
                    method = "direct"
            
            # Format results
            time_str = f"{elapsed:.2f}s"
            result = "✅ SUCCESS" if similar else "❌ FAILED"
            working_variant = similar[0].get('_matched_variant', 'N/A') if similar else "None"
            
            # Truncate long variant names
            if len(working_variant) > 20:
                working_variant = working_variant[:17] + "..."
            
            print(f"{artist:<20} {description:<25} {time_str:<8} {method:<15} {result:<15} {working_variant}")
            
            results.append({
                'artist': artist,
                'success': bool(similar),
                'method': method,
                'time': elapsed,
                'similar_count': len(similar) if similar else 0
            })
        
        # Summary statistics
        print("\n" + "=" * 100)
        print("COMPREHENSIVE RESULTS")
        print("=" * 100)
        
        total = len(results)
        successful = sum(1 for r in results if r['success'])
        success_rate = successful / total * 100
        
        print(f"\nOverall Success Rate: {successful}/{total} ({success_rate:.1f}%)")
        
        # Method breakdown
        method_counts = {}
        for r in results:
            if r['success']:
                method = r['method']
                method_counts[method] = method_counts.get(method, 0) + 1
        
        print(f"\nSuccess Methods:")
        for method, count in method_counts.items():
            print(f"   {method}: {count} artists")
        
        # Performance stats
        avg_time = sum(r['time'] for r in results) / len(results)
        print(f"\nAverage Response Time: {avg_time:.2f}s")
        
        # Failure analysis
        failures = [r for r in results if not r['success']]
        if failures:
            print(f"\nFailed Artists: {len(failures)}")
            for f in failures:
                print(f"   ❌ {f['artist']}")
        else:
            print(f"\n🎉 ALL ARTISTS SUCCESSFUL!")
        
        return success_rate >= 90.0  # Success if 90%+ work
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_method_progression():
    """Test how the system progresses through different methods."""
    print("\n" + "=" * 100)
    print("METHOD PROGRESSION ANALYSIS")
    print("=" * 100)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Clear cache for this artist to see full progression
        cache_to_clear = []
        for key in lastfm_api.cache.keys():
            if 'mgk' in key.lower():
                cache_to_clear.append(key)
        for key in cache_to_clear:
            del lastfm_api.cache[key]
        
        # Test with detailed logging
        print("\n🧪 Testing 'mgk' with detailed method progression:")
        
        import logging
        logging.getLogger('lastfm_utils').setLevel(logging.DEBUG)
        
        similar = lastfm_api.get_similar_artists('mgk', limit=5, use_enhanced_matching=True)
        
        if similar:
            method = similar[0].get('_search_method', 'pattern_match')
            variant = similar[0].get('_matched_variant', 'mgk')
            print(f"\n✅ Final result: Found {len(similar)} similar artists")
            print(f"   Method used: {method}")
            print(f"   Working variant: '{variant}'")
        else:
            print(f"\n❌ Failed to find similar artists")
        
        # Reset logging level
        logging.getLogger('lastfm_utils').setLevel(logging.INFO)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    success = test_ultra_robust_system()
    test_method_progression()
    
    print(f"\n{'='*100}")
    if success:
        print("🎉 ULTRA-ROBUST SYSTEM READY FOR PRODUCTION!")
    else:
        print("⚠️  System needs further refinement")
    print(f"{'='*100}")