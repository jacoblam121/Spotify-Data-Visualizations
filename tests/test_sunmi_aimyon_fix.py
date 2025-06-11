"""
Test SUNMI and Aimyon Fixes
===========================

Tests that SUNMI doesn't match to SunMin and Aimyon works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PARENT_DIR, 'configurations.txt')


def test_sunmi_aimyon():
    """Test SUNMI and Aimyon matching."""
    print("=" * 80)
    print("TESTING SUNMI AND AIMYON")
    print("=" * 80)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test SUNMI
        print("\n1️⃣ Testing SUNMI:")
        print("-" * 60)
        
        # Get artist info
        info = lastfm_api.get_artist_info('SUNMI', use_enhanced_matching=True)
        if info:
            print(f"✅ Artist found: {info['name']}")
            print(f"   Listeners: {info.get('listeners', 0):,}")
            if info['name'].lower() == 'sunmin':
                print("   ❌ ERROR: Matched to wrong artist 'SunMin'!")
        
        # Get similar artists
        similar = lastfm_api.get_similar_artists('SUNMI', limit=5, use_enhanced_matching=True)
        if similar:
            variant = similar[0].get('_matched_variant', 'SUNMI')
            method = similar[0].get('_search_method', 'unknown')
            print(f"✅ Found {len(similar)} similar artists")
            print(f"   Working variant: '{variant}'")
            print(f"   Method: {method}")
            
            # Verify we didn't match to SunMin
            if 'sunmin' in variant.lower():
                print("   ❌ ERROR: Used wrong variant 'SunMin'!")
            else:
                print("   ✅ Correct artist variant used")
                
            print("   Similar artists:")
            for i, artist in enumerate(similar[:3], 1):
                print(f"      {i}. {artist['name']}: {artist['match']:.3f}")
        else:
            print("❌ No similar artists found")
        
        # Test Aimyon
        print("\n2️⃣ Testing Aimyon:")
        print("-" * 60)
        
        # Get artist info
        info = lastfm_api.get_artist_info('Aimyon', use_enhanced_matching=True)
        if info:
            print(f"✅ Artist found: {info['name']}")
            print(f"   Listeners: {info.get('listeners', 0):,}")
        
        # Get similar artists
        similar = lastfm_api.get_similar_artists('Aimyon', limit=5, use_enhanced_matching=True)
        if similar:
            variant = similar[0].get('_matched_variant', 'Aimyon')
            method = similar[0].get('_search_method', 'unknown')
            print(f"✅ Found {len(similar)} similar artists")
            print(f"   Working variant: '{variant}'")
            print(f"   Method: {method}")
            print("   Similar artists:")
            for i, artist in enumerate(similar[:3], 1):
                print(f"      {i}. {artist['name']}: {artist['match']:.3f}")
        else:
            print("❌ No similar artists found")
        
        # Test relevance filter directly
        print("\n3️⃣ Testing relevance filter:")
        print("-" * 60)
        
        test_cases = [
            ('SUNMI', 'Sunmi', True),
            ('SUNMI', 'SUNMI', True),
            ('SUNMI', 'Lee Sun-mi', True),
            ('SUNMI', 'SunMin', False),
            ('SUNMI', 'Sun Min', False),
            ('Aimyon', 'Aimyon', True),
            ('Aimyon', 'あいみょん', True),
            ('Aimyon', 'Aimon', False),
        ]
        
        for original, candidate, should_match in test_cases:
            is_relevant = lastfm_api._is_relevant_artist_match(original, candidate)
            status = "✅" if is_relevant == should_match else "❌"
            print(f"{status} '{original}' vs '{candidate}': {'match' if is_relevant else 'no match'} "
                  f"(expected: {'match' if should_match else 'no match'})")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_collaboration_handling():
    """Test that collaborations are properly handled."""
    print("\n" + "=" * 80)
    print("TESTING COLLABORATION HANDLING")
    print("=" * 80)
    
    # Import data processor to test collaboration splitting
    from data_processor import split_artist_collaborations
    
    test_cases = [
        "IU feat. SUGA",
        "Ariana Grande & The Weeknd",
        "Taylor Swift x Ed Sheeran",
        "BLACKPINK with Dua Lipa",
        "BTS featuring Halsey",
        "Machine Gun Kelly & blackbear",
        "ILLIT, NewJeans",
        "IVE (아이브)",
        "Simple Artist Name"
    ]
    
    print("\nTesting artist collaboration splitting:")
    print("-" * 60)
    
    for artist_string in test_cases:
        artists = split_artist_collaborations(artist_string)
        print(f"'{artist_string}' → {artists} ({len(artists)} artist(s))")


if __name__ == '__main__':
    test_sunmi_aimyon()
    test_collaboration_handling()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nThe system should now:")
    print("1. ✅ Correctly match SUNMI without false positives (SunMin)")
    print("2. ✅ Correctly match Aimyon")  
    print("3. ✅ Properly split and credit all artists in collaborations")