#!/usr/bin/env python3
"""
Debug script to investigate IU ↔ BOL4 relationship by testing different name variants.
Tests the hypothesis that BOL4 vs Bolbbalgan4 name discrepancy is causing the issue.
"""

import os
import sys
os.chdir('/home/jacob/Spotify-Data-Visualizations')

from config_loader import AppConfig
from lastfm_utils import LastfmAPI

def debug_artist_names():
    """Test different name variants for BOL4 and IU in Last.fm."""
    print("🔍 Debugging IU ↔ BOL4 artist name variants")
    print("=" * 60)
    
    # Initialize Last.fm API
    config = AppConfig()
    lastfm_config = config.get_lastfm_config()
    
    if not lastfm_config['api_key']:
        print("❌ Last.fm API key not found")
        return
    
    lastfm_api = LastfmAPI(
        lastfm_config['api_key'],
        lastfm_config['api_secret'],
        lastfm_config['cache_dir']
    )
    
    # Test different name variants
    test_artists = {
        'IU variants': ['IU', '아이유', 'IU (아이유)'],
        'BOL4 variants': ['BOL4', 'Bolbbalgan4', 'bol4', 'Bolbbalgan4 (볼빨간사춘기)', '볼빨간사춘기']
    }
    
    results = {}
    
    for category, variants in test_artists.items():
        print(f"\n🎵 Testing {category}:")
        print("-" * 40)
        
        for variant in variants:
            print(f"\n  Testing variant: '{variant}'")
            
            try:
                # Get artist info
                artist_info = lastfm_api.get_artist_info(variant, use_enhanced_matching=False)
                
                if artist_info:
                    canonical_name = artist_info.get('name', 'Unknown')
                    listeners = artist_info.get('listeners', 0)
                    print(f"    ✅ Found: {canonical_name} ({listeners:,} listeners)")
                    
                    # Get similar artists
                    similar_artists = lastfm_api.get_similar_artists(variant, limit=20, use_enhanced_matching=False)
                    
                    if similar_artists:
                        print(f"    🔗 {len(similar_artists)} similar artists found")
                        
                        # Look for IU or BOL4 variants in similar artists
                        iu_variants = {'IU', '아이유', 'IU (아이유)'}
                        bol4_variants = {'BOL4', 'Bolbbalgan4', 'bol4', 'Bolbbalgan4 (볼빨간사춘기)', '볼빨간사춘기'}
                        
                        found_matches = []
                        for similar in similar_artists:
                            similar_name = similar['name']
                            similarity = similar['match']
                            
                            if 'IU' in category and any(bol4_var.lower() in similar_name.lower() for bol4_var in bol4_variants):
                                found_matches.append(f"      🎯 FOUND BOL4 MATCH: {similar_name} (similarity: {similarity})")
                            elif 'BOL4' in category and any(iu_var.lower() in similar_name.lower() for iu_var in iu_variants):
                                found_matches.append(f"      🎯 FOUND IU MATCH: {similar_name} (similarity: {similarity})")
                        
                        if found_matches:
                            for match in found_matches:
                                print(match)
                        else:
                            print("    ❌ No IU ↔ BOL4 matches found in similar artists")
                            
                        # Show top 5 similar artists for reference
                        print("    📋 Top 5 similar artists:")
                        for i, similar in enumerate(similar_artists[:5], 1):
                            print(f"      {i}. {similar['name']} ({similar['match']})")
                    else:
                        print("    ❌ No similar artists found")
                    
                    results[variant] = {
                        'canonical_name': canonical_name,
                        'listeners': listeners,
                        'similar_count': len(similar_artists) if similar_artists else 0,
                        'similar_artists': similar_artists[:10] if similar_artists else []  # Store top 10
                    }
                    
                else:
                    print("    ❌ Artist not found")
                    results[variant] = None
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
                results[variant] = None
    
    # Summary analysis
    print("\n" + "=" * 60)
    print("📊 SUMMARY ANALYSIS")
    print("=" * 60)
    
    # Find best variants for each artist
    best_iu = None
    best_bol4 = None
    
    for variant, data in results.items():
        if data and 'IU' in variant.upper():
            if not best_iu or data['listeners'] > results[best_iu]['listeners']:
                best_iu = variant
        elif data and ('BOL4' in variant.upper() or 'BOLBBALGAN' in variant.upper()):
            if not best_bol4 or data['listeners'] > results[best_bol4]['listeners']:
                best_bol4 = variant
    
    if best_iu and best_bol4:
        print(f"\n🎯 Best variants found:")
        print(f"   IU: '{best_iu}' → {results[best_iu]['canonical_name']} ({results[best_iu]['listeners']:,} listeners)")
        print(f"   BOL4: '{best_bol4}' → {results[best_bol4]['canonical_name']} ({results[best_bol4]['listeners']:,} listeners)")
        
        # Check if they reference each other
        iu_similar = results[best_iu]['similar_artists']
        bol4_similar = results[best_bol4]['similar_artists']
        
        bol4_canonical = results[best_bol4]['canonical_name']
        iu_canonical = results[best_iu]['canonical_name']
        
        iu_mentions_bol4 = any(bol4_canonical.lower() in similar['name'].lower() for similar in iu_similar)
        bol4_mentions_iu = any(iu_canonical.lower() in similar['name'].lower() for similar in bol4_similar)
        
        print(f"\n🔗 Cross-reference check:")
        print(f"   {iu_canonical} → {bol4_canonical}: {'✅ YES' if iu_mentions_bol4 else '❌ NO'}")
        print(f"   {bol4_canonical} → {iu_canonical}: {'✅ YES' if bol4_mentions_iu else '❌ NO'}")
        
        if iu_mentions_bol4 or bol4_mentions_iu:
            print(f"\n🎉 RELATIONSHIP FOUND! The issue is likely name variant mismatch.")
            print(f"   Recommended name mapping:")
            print(f"   'BOL4' → '{results[best_bol4]['canonical_name']}'")
        else:
            print(f"\n😞 No relationship found even with best name variants.")
            print(f"   The artists may not be similar according to Last.fm data.")
    
    return results

if __name__ == "__main__":
    debug_artist_names()