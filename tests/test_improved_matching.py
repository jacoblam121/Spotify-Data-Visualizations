"""
Test Improved Smart Matching System
===================================

Tests the new intelligent matching system with priority ordering and early termination.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI
import time

# Get the parent directory path for config file
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PARENT_DIR, 'configurations.txt')


def test_problematic_artists():
    """Test artists that were having issues."""
    print("=" * 80)
    print("TESTING IMPROVED SMART MATCHING")
    print("=" * 80)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test problematic artists
        test_cases = [
            ('YOASOBI', 'Japanese artist'),
            ('Twenty One Pilots', 'Western with abbreviation'),
            ('ARTMS', 'K-pop with special patterns'),
            ('ILLIT', 'New K-pop group'),
            ('bbno$', 'Special characters'),
            ('Bring Me The Horizon', 'Common abbreviation'),
            ('Panic! At The Disco', 'Punctuation issues')
        ]
        
        print(f"\nTesting {len(test_cases)} challenging artists...\n")
        print(f"{'Artist':<25} {'Time':<8} {'Variants':<8} {'Result':<15} {'Working Variant'}")
        print("-" * 90)
        
        for artist, description in test_cases:
            start_time = time.time()
            
            # Test variant generation first
            variants = lastfm_api._generate_name_variants(artist)
            
            # Test actual similar artists
            similar = lastfm_api.get_similar_artists(artist, limit=5, use_enhanced_matching=True)
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            # Format results
            time_str = f"{elapsed:.2f}s"
            variant_count = len(variants)
            
            if similar:
                result = "✅ SUCCESS"
                working_variant = similar[0].get('_matched_variant', artist)
                working_variant = working_variant if working_variant != artist else "Original"
            else:
                result = "❌ FAILED"
                working_variant = "None"
            
            print(f"{artist:<25} {time_str:<8} {variant_count:<8} {result:<15} {working_variant}")
        
        print("\n" + "=" * 80)
        print("VARIANT GENERATION ANALYSIS")
        print("=" * 80)
        
        # Show variant generation for a few artists
        analysis_artists = ['YOASOBI', 'Twenty One Pilots', 'bbno$']
        
        for artist in analysis_artists:
            print(f"\n🎵 Variants for '{artist}':")
            variants = lastfm_api._generate_name_variants(artist)
            artist_type = lastfm_api._detect_artist_type(artist)
            print(f"   Detected type: {artist_type}")
            print(f"   Generated {len(variants)} variants:")
            
            for i, variant in enumerate(variants[:10], 1):  # Show first 10
                print(f"   {i:2d}. '{variant}'")
            
            if len(variants) > 10:
                print(f"   ... and {len(variants) - 10} more variants")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_efficiency():
    """Test the efficiency improvements."""
    print("\n" + "=" * 80)
    print("EFFICIENCY TESTING")
    print("=" * 80)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Clear cache for fair testing
        lastfm_api.cache.clear()
        
        # Test a challenging artist
        artist = 'Twenty One Pilots'
        print(f"\n🧪 Testing efficiency for '{artist}'...")
        
        start_time = time.time()
        similar = lastfm_api.get_similar_artists(artist, limit=5, use_enhanced_matching=True)
        end_time = time.time()
        
        print(f"   Time taken: {end_time - start_time:.2f} seconds")
        print(f"   Result: {'✅ SUCCESS' if similar else '❌ FAILED'}")
        
        if similar:
            variant = similar[0].get('_matched_variant', artist)
            print(f"   Working variant: '{variant}'")
            print(f"   Similar artists found: {len(similar)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_problematic_artists()
    test_efficiency()