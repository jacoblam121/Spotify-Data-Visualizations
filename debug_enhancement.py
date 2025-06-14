#!/usr/bin/env python3
"""
Debug the enhancement step specifically
"""

import json
from integrated_network_generator import IntegratedNetworkGenerator

def debug_enhancement():
    """Debug why enhancement isn't working."""
    
    print("🔍 Debug Enhancement Step")
    print("=" * 30)
    
    # Load artist data
    with open('artist_data.json', 'r', encoding='utf-8') as f:
        artists_data = json.load(f)
    
    # Initialize network generator
    generator = IntegratedNetworkGenerator()
    
    # Get ANYUJIN similarity
    print("\n1️⃣ Original ANYUJIN similarity:")
    anyujin_similarity = generator._get_multi_source_similarity("ANYUJIN")
    
    for source, results in anyujin_similarity.items():
        print(f"   {source}: {len(results)} results")
    
    # Test enhancement
    target_artist_names = {a['name'] for a in artists_data}
    print(f"\n2️⃣ Target artists include: {list(target_artist_names)[:10]}...")
    
    print(f"\n3️⃣ Testing name matcher directly:")
    # Test if name matcher can find the relationship
    related = generator.name_matcher.find_related_artists("ANYUJIN", target_artist_names)
    print(f"   ANYUJIN related to targets: {related}")
    
    related_ive = generator.name_matcher.find_related_artists("IVE", target_artist_names)
    print(f"   IVE related to targets: {related_ive}")
    
    print(f"\n4️⃣ Testing enhancement function:")
    enhanced_data = generator._enhance_similarity_with_relationships(
        "ANYUJIN", anyujin_similarity, target_artist_names
    )
    
    for source, results in enhanced_data.items():
        enhanced_count = len([r for r in results if r.get('_enhanced_match')])
        print(f"   {source}: {len(results)} total, {enhanced_count} enhanced")
        
        # Show enhanced matches
        for result in results:
            if result.get('_enhanced_match'):
                print(f"      -> Enhanced: {result}")

if __name__ == "__main__":
    debug_enhancement()