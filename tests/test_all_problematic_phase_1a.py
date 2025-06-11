"""
Comprehensive Test of All Problematic Artists
=============================================

Tests all known problematic artists to ensure Phase 1A is truly complete.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI

# Get the parent directory path for config file
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PARENT_DIR, 'configurations.txt')


def test_all_problematic():
    """Test all problematic artists comprehensively."""
    print("=" * 80)
    print("COMPREHENSIVE TEST: ALL PROBLEMATIC ARTISTS")
    print("=" * 80)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # All known problematic artists
        test_artists = [
            'ARTMS',
            'ILLIT', 
            'IVE',
            'ANYUJIN',
            'KISS OF LIFE',
            'JEON SOMI',
            'LE SSERAFIM',
            'NEWJEANS',
            '(G)I-DLE',
            'TWICE',
            'BLACKPINK',
            'BTS',
            'STRAY KIDS',
            'SEVENTEEN',
            'ENHYPEN',
            'TXT',
            'aespa',
            'ITZY'
        ]
        
        results = []
        
        print(f"\nTesting {len(test_artists)} artists...\n")
        print(f"{'Artist':<15} {'Similar':<10} {'Info':<10} {'Listeners':<12} {'Variant Used'}")
        print("-" * 80)
        
        for artist in test_artists:
            # Test similar artists
            similar = lastfm_api.get_similar_artists(artist, limit=5, use_enhanced_matching=True)
            has_similar = bool(similar)
            similar_variant = similar[0].get('_matched_variant', artist) if similar else None
            
            # Test artist info
            info = lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
            has_info = bool(info)
            listeners = info.get('listeners', 0) if info else 0
            info_variant = info.get('_matched_variant', artist) if info else None
            
            # Use the variant that worked for similar artists (more important for network)
            variant_used = similar_variant if similar_variant else info_variant
            
            # Format results
            similar_status = "✅" if has_similar else "❌"
            info_status = "✅" if has_info else "❌"
            listeners_str = f"{listeners:,}" if listeners else "N/A"
            variant_display = variant_used if variant_used and variant_used != artist else ""
            
            print(f"{artist:<15} {similar_status:<10} {info_status:<10} {listeners_str:<12} {variant_display}")
            
            results.append({
                'artist': artist,
                'has_similar': has_similar,
                'has_info': has_info,
                'listeners': listeners,
                'variant': variant_used
            })
        
        # Summary statistics
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        total = len(results)
        similar_success = sum(1 for r in results if r['has_similar'])
        info_success = sum(1 for r in results if r['has_info'])
        both_success = sum(1 for r in results if r['has_similar'] and r['has_info'])
        
        print(f"\nSimilar Artists Success: {similar_success}/{total} ({similar_success/total*100:.1f}%)")
        print(f"Artist Info Success: {info_success}/{total} ({info_success/total*100:.1f}%)")
        print(f"Both APIs Success: {both_success}/{total} ({both_success/total*100:.1f}%)")
        
        # List any failures
        failures = [r for r in results if not r['has_similar']]
        if failures:
            print(f"\n⚠️  Artists without similar artists data:")
            for f in failures:
                print(f"   - {f['artist']}")
                if f['has_info']:
                    print(f"     (But has {f['listeners']:,} listeners)")
        
        # Success assessment
        print("\n" + "=" * 80)
        if similar_success == total:
            print("🎉 PERFECT! All artists have similar artists data!")
        elif similar_success >= total * 0.9:
            print("✅ EXCELLENT! Over 90% success rate!")
        elif similar_success >= total * 0.8:
            print("👍 GOOD! Over 80% success rate!")
        else:
            print("⚠️  NEEDS IMPROVEMENT! Less than 80% success rate.")
        
        # Network readiness check
        print(f"\n🌐 Network Visualization Readiness:")
        print(f"   {both_success}/{total} artists ready for network visualization")
        print(f"   {info_success}/{total} artists have listener data for node sizing")
        
        return similar_success == total
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_all_problematic()
    sys.exit(0 if success else 1)