"""
Manual Test for Phase 1A: ARTMS Fix and Enhanced Data Fetching
==============================================================

Interactive test to validate ARTMS fix and explore artist data fetching.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI
import json


def print_menu():
    """Display the test menu."""
    print("\n" + "=" * 50)
    print("PHASE 1A MANUAL TEST MENU")
    print("=" * 50)
    print("1. Test ARTMS similar artists")
    print("2. Test ARTMS artist info")
    print("3. Test any artist (custom)")
    print("4. Compare with/without enhanced matching")
    print("5. Show name variants for an artist")
    print("6. Test all problematic artists")
    print("0. Exit")
    print("-" * 50)


def test_artms_similar(lastfm_api):
    """Test ARTMS similar artists."""
    print("\n🎵 Testing ARTMS similar artists...")
    
    similar = lastfm_api.get_similar_artists('ARTMS', limit=10, use_enhanced_matching=True)
    
    if similar:
        variant = similar[0].get('_matched_variant', 'ARTMS')
        print(f"\n✅ Found {len(similar)} similar artists using variant: '{variant}'")
        print("\nTop 10 similar artists:")
        for i, s in enumerate(similar, 1):
            print(f"{i:2d}. {s['name']:30s} Match: {s['match']:.3f}")
    else:
        print("❌ No similar artists found for ARTMS")


def test_artms_info(lastfm_api):
    """Test ARTMS artist info."""
    print("\n🎵 Testing ARTMS artist info...")
    
    info = lastfm_api.get_artist_info('ARTMS', use_enhanced_matching=True)
    
    if info:
        print(f"\n✅ Artist info found!")
        if info.get('_matched_variant'):
            print(f"   Using variant: '{info['_matched_variant']}'")
        print(f"\n📊 Artist Statistics:")
        print(f"   Name: {info.get('name', 'Unknown')}")
        print(f"   Listeners: {info.get('listeners', 0):,}")
        print(f"   Play count: {info.get('playcount', 0):,}")
        print(f"   On tour: {'Yes' if info.get('ontour') else 'No'}")
        
        if info.get('tags'):
            print(f"\n🏷️  Tags:")
            for tag in info['tags'][:5]:
                print(f"   - {tag['name']}")
        
        if info.get('images', {}).get('large'):
            print(f"\n🖼️  Image URL: {info['images']['large'][:80]}...")
    else:
        print("❌ No artist info found for ARTMS")


def test_custom_artist(lastfm_api):
    """Test a custom artist."""
    artist = input("\nEnter artist name: ").strip()
    if not artist:
        return
    
    print(f"\n🎵 Testing '{artist}'...")
    
    # Test similar artists
    print("\n1️⃣ Similar Artists:")
    similar = lastfm_api.get_similar_artists(artist, limit=5, use_enhanced_matching=True)
    if similar:
        variant = similar[0].get('_matched_variant', artist)
        print(f"   ✅ Found {len(similar)} similar (using '{variant}')")
        for i, s in enumerate(similar[:5], 1):
            print(f"      {i}. {s['name']}: {s['match']:.3f}")
    else:
        print("   ❌ No similar artists found")
    
    # Test artist info
    print("\n2️⃣ Artist Info:")
    info = lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
    if info:
        print(f"   ✅ Found info")
        print(f"      Listeners: {info.get('listeners', 0):,}")
        print(f"      Has image: {'Yes' if info.get('images', {}).get('large') else 'No'}")
    else:
        print("   ❌ No artist info found")


def compare_matching(lastfm_api):
    """Compare results with and without enhanced matching."""
    artist = input("\nEnter artist name to compare: ").strip()
    if not artist:
        return
    
    print(f"\n🔍 Comparing matching for '{artist}'...")
    
    # Without enhanced matching
    print("\n1️⃣ WITHOUT Enhanced Matching:")
    similar_standard = lastfm_api.get_similar_artists(artist, limit=5, use_enhanced_matching=False)
    print(f"   Found: {len(similar_standard) if similar_standard else 0} similar artists")
    
    # With enhanced matching
    print("\n2️⃣ WITH Enhanced Matching:")
    similar_enhanced = lastfm_api.get_similar_artists(artist, limit=5, use_enhanced_matching=True)
    if similar_enhanced:
        variant = similar_enhanced[0].get('_matched_variant', artist)
        print(f"   Found: {len(similar_enhanced)} similar artists")
        if variant != artist:
            print(f"   Using variant: '{variant}'")
    else:
        print(f"   Found: 0 similar artists")
    
    # Show the difference
    if not similar_standard and similar_enhanced:
        print("\n✅ Enhanced matching made the difference!")
    elif similar_standard and similar_enhanced:
        print("\n📊 Both methods worked")
    else:
        print("\n❌ Neither method found results")


def show_variants(lastfm_api):
    """Show all name variants for an artist."""
    artist = input("\nEnter artist name: ").strip()
    if not artist:
        return
    
    variants = lastfm_api._generate_name_variants(artist)
    print(f"\n🔄 Generated {len(variants)} variants for '{artist}':")
    
    for i, variant in enumerate(variants, 1):
        print(f"{i:3d}. '{variant}'")
        if i >= 20:
            print(f"... and {len(variants) - 20} more variants")
            break


def test_all_problematic(lastfm_api):
    """Test all known problematic artists."""
    artists = ['ARTMS', 'ILLIT', 'IVE', 'ANYUJIN', 'KISS OF LIFE', 'JEON SOMI']
    
    print(f"\n🧪 Testing {len(artists)} problematic artists...")
    
    results = []
    for artist in artists:
        similar = lastfm_api.get_similar_artists(artist, limit=5, use_enhanced_matching=True)
        info = lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
        
        success = bool(similar)
        listeners = info.get('listeners', 0) if info else 0
        variant = similar[0].get('_matched_variant', artist) if similar else None
        
        results.append({
            'artist': artist,
            'success': success,
            'listeners': listeners,
            'variant': variant
        })
    
    # Display results
    print("\n📊 RESULTS:")
    print(f"{'Artist':<15} {'Status':<10} {'Listeners':<12} {'Variant'}")
    print("-" * 60)
    
    for r in results:
        status = "✅ OK" if r['success'] else "❌ FAIL"
        listeners = f"{r['listeners']:,}" if r['listeners'] else "N/A"
        variant = r['variant'] if r['variant'] and r['variant'] != r['artist'] else ""
        print(f"{r['artist']:<15} {status:<10} {listeners:<12} {variant}")
    
    success_rate = sum(1 for r in results if r['success']) / len(results) * 100
    print(f"\nSuccess rate: {success_rate:.0f}%")


def main():
    """Run the manual test interface."""
    print("=" * 70)
    print("PHASE 1A: ARTMS FIX - MANUAL TEST")
    print("=" * 70)
    
    try:
        # Initialize API
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
        
        print("✅ Last.fm API initialized")
        
        # Interactive menu
        while True:
            print_menu()
            
            try:
                choice = input("\nSelect option: ").strip()
                
                if choice == '0':
                    print("\nExiting...")
                    break
                elif choice == '1':
                    test_artms_similar(lastfm_api)
                elif choice == '2':
                    test_artms_info(lastfm_api)
                elif choice == '3':
                    test_custom_artist(lastfm_api)
                elif choice == '4':
                    compare_matching(lastfm_api)
                elif choice == '5':
                    show_variants(lastfm_api)
                elif choice == '6':
                    test_all_problematic(lastfm_api)
                else:
                    print("Invalid option. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
    
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()