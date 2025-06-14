#!/usr/bin/env python3
"""
Debug ANYUJIN variant generation and scoring
"""

from lastfm_utils import LastfmAPI
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_loader import AppConfig

def debug_anyujin_variants():
    """Debug which variants are being generated and tested for ANYUJIN."""
    
    print("🔍 Debug ANYUJIN Variant Generation")
    print("=" * 40)
    
    # Initialize Last.fm API
    config = AppConfig()
    try:
        lastfm_config = config.get_lastfm_config()
        api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret']
        )
        print("✅ Last.fm API initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Last.fm API: {e}")
        return
    
    # Test variant generation
    print(f"\n1️⃣ Testing variant generation for 'ANYUJIN':")
    variants = api._generate_name_variants("ANYUJIN")
    
    print(f"   Generated {len(variants)} variants:")
    for i, variant in enumerate(variants, 1):
        print(f"   {i:2}. '{variant}'")
    
    # Check if 'AnYujin' is in the variants
    target_variant = "AnYujin"
    if target_variant in variants:
        print(f"\n✅ Target variant '{target_variant}' found at position {variants.index(target_variant) + 1}")
    else:
        print(f"\n❌ Target variant '{target_variant}' NOT found in variants")
        print(f"   Need to add this variant to the generation logic")
    
    # Test manual lookup of known variants
    print(f"\n2️⃣ Testing manual lookup of known ANYUJIN variants:")
    test_variants = ["ANYUJIN", "AnYujin", "Ahn Yujin", "안유진", "ANYUJIN (IVE)"]
    
    for variant in test_variants:
        print(f"\n   Testing '{variant}':")
        try:
            # Make direct API call to see what we get
            params = {'limit': '10', 'artist': variant}
            response = api._make_request('artist.getsimilar', params)
            
            if response and 'similarartists' in response:
                similar = response['similarartists'].get('artist', [])
                if similar:
                    print(f"      ✅ Found {len(similar)} similar artists")
                    # Try to get artist info to see listener count
                    try:
                        info_params = {'artist': variant}
                        info_response = api._make_request('artist.getinfo', info_params)
                        if info_response and 'artist' in info_response:
                            listeners = info_response['artist']['stats']['listeners']
                            print(f"      👥 Listeners: {listeners}")
                    except:
                        pass
                else:
                    print(f"      ❌ No similar artists found")
            else:
                print(f"      ❌ API call failed or no data")
        except Exception as e:
            print(f"      ❌ Error: {e}")

if __name__ == "__main__":
    debug_anyujin_variants()