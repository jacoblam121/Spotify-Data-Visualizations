"""
Test ANYUJIN Enhanced Matching Fix
==================================

Tests that ANYUJIN now works with the enhanced matching system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI


def test_anyujin_enhanced_matching():
    """Test ANYUJIN with enhanced matching."""
    print("🧪 Testing ANYUJIN with Enhanced Matching")
    print("=" * 50)
    
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test with enhanced matching enabled
        print("🔧 Testing with enhanced matching ENABLED...")
        similar_enhanced = lastfm_api.get_similar_artists('ANYUJIN', limit=10, use_enhanced_matching=True)
        
        if similar_enhanced:
            matched_variant = similar_enhanced[0].get('_matched_variant', 'ANYUJIN')
            print(f"✅ SUCCESS: Found {len(similar_enhanced)} similar artists!")
            print(f"🎯 Matched using variant: '{matched_variant}'")
            print(f"🎵 Top similar artists:")
            for i, similar in enumerate(similar_enhanced[:5], 1):
                print(f"   {i}. {similar['name']}: {similar['match']:.3f}")
        else:
            print("❌ FAILED: No similar artists found with enhanced matching")
        
        # Test with enhanced matching disabled for comparison
        print(f"\n🔧 Testing with enhanced matching DISABLED...")
        similar_standard = lastfm_api.get_similar_artists('ANYUJIN', limit=10, use_enhanced_matching=False)
        
        if similar_standard:
            print(f"✅ Found {len(similar_standard)} similar artists with standard matching")
        else:
            print("❌ No similar artists found with standard matching")
        
        # Summary
        print(f"\n📊 Results Summary:")
        enhanced_success = len(similar_enhanced) > 0 if similar_enhanced else False
        standard_success = len(similar_standard) > 0 if similar_standard else False
        
        print(f"   Enhanced matching: {'✅ SUCCESS' if enhanced_success else '❌ FAILED'}")
        print(f"   Standard matching: {'✅ SUCCESS' if standard_success else '❌ FAILED'}")
        
        if enhanced_success and not standard_success:
            print(f"   🎉 Enhanced matching FIXED the ANYUJIN issue!")
        elif enhanced_success and standard_success:
            print(f"   ℹ️  Both methods work (no issue to fix)")
        else:
            print(f"   ⚠️  Issue not resolved")
        
        return enhanced_success
        
    except Exception as e:
        print(f"❌ Error testing ANYUJIN: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("ANYUJIN ENHANCED MATCHING FIX TEST")
    print("=" * 60)
    
    success = test_anyujin_enhanced_matching()
    
    if success:
        print(f"\n🎉 ANYUJIN issue has been FIXED!")
        print(f"   Enhanced matching system now handles ANYUJIN correctly")
        print(f"   Network building should now work with ANYUJIN included")
    else:
        print(f"\n❌ ANYUJIN issue NOT fixed")
        print(f"   Additional investigation needed")


if __name__ == "__main__":
    # Change to main directory for proper file access
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        main()
    finally:
        os.chdir(original_dir)