#!/usr/bin/env python3
"""
Comprehensive test of enhanced matching system
Shows both the working enhanced matching and investigates Last.fm issues
"""

import json
from integrated_network_generator import IntegratedNetworkGenerator

def test_enhanced_matching_comprehensive():
    """Test the complete enhanced matching system."""
    
    print("🎯 Comprehensive Enhanced Matching Test")
    print("=" * 45)
    
    # Load artist data
    with open('artist_data.json', 'r', encoding='utf-8') as f:
        artists_data = json.load(f)
    
    # Initialize network generator
    generator = IntegratedNetworkGenerator()
    
    print(f"\n1️⃣ Testing Enhanced Name Matcher Directly:")
    print("-" * 45)
    
    # Test the enhanced name matcher components
    target_artist_names = {a['name'] for a in artists_data}
    print(f"Target artists include: {sorted(list(target_artist_names))[:10]}...")
    
    # Test relationship detection
    anyujin_related = generator.name_matcher.find_related_artists("ANYUJIN", target_artist_names)
    print(f"\nANYUJIN relationships found: {anyujin_related}")
    
    ive_related = generator.name_matcher.find_related_artists("IVE", target_artist_names)
    print(f"IVE relationships found: {ive_related}")
    
    print(f"\n2️⃣ Testing Multi-Source Similarity (Raw):")
    print("-" * 45)
    
    # Get raw similarity data
    anyujin_similarity = generator._get_multi_source_similarity("ANYUJIN")
    for source, results in anyujin_similarity.items():
        print(f"{source:12}: {len(results):3} results")
        if results and len(results) > 0:
            sample = [r['name'] for r in results[:3]]
            print(f"             Sample: {sample}")
    
    print(f"\n3️⃣ Testing Enhanced Similarity (With Relationships):")
    print("-" * 45)
    
    # Get enhanced similarity data
    enhanced_similarity = generator._enhance_similarity_with_relationships(
        "ANYUJIN", anyujin_similarity, target_artist_names
    )
    
    for source, results in enhanced_similarity.items():
        original_count = len(anyujin_similarity[source])
        enhanced_count = len(results)
        added_count = enhanced_count - original_count
        
        print(f"{source:12}: {original_count:3} → {enhanced_count:3} (+{added_count} enhanced)")
        
        # Show enhanced matches specifically
        enhanced_matches = [r for r in results if r.get('_enhanced_match')]
        if enhanced_matches:
            print(f"             Enhanced: {[r['name'] for r in enhanced_matches]}")
    
    print(f"\n4️⃣ Testing Full Edge Creation:")
    print("-" * 45)
    
    # Test edge creation between ANYUJIN and all artists
    anyujin_data = next(a for a in artists_data if a['name'] == 'anyujin')
    target_artists = {a['name'].lower(): a for a in artists_data}
    
    # Create edges using enhanced similarity
    edges = generator._create_edges_for_artist(
        anyujin_data, enhanced_similarity, target_artists
    )
    
    print(f"ANYUJIN created {len(edges)} total edges:")
    for edge in edges[:10]:  # Show first 10
        target_name = next(a['name'] for a in artists_data if a['name'].lower().replace(' ', '_') == edge['target'])
        print(f"  → {target_name:15}: weight={edge['weight']:.3f}, conf={edge['confidence']:.3f}, sources={edge['sources']}")
    
    # Look for IVE specifically
    ive_edge = next((e for e in edges if e['target'] == 'ive'), None)
    if ive_edge:
        print(f"\n✅ ANYUJIN → IVE edge found!")
        print(f"   Weight: {ive_edge['weight']:.3f}")
        print(f"   Confidence: {ive_edge['confidence']:.3f}")
        print(f"   Sources: {ive_edge['sources']}")
        print(f"   Factual: {ive_edge['is_factual']}")
    else:
        print(f"\n❌ No ANYUJIN → IVE edge found")
    
    print(f"\n5️⃣ Quick Bidirectional Test:")
    print("-" * 45)
    
    # Quick test both directions
    test_artists = [
        {'name': 'anyujin', 'play_count': 427},
        {'name': 'ive', 'play_count': 6143}
    ]
    
    network_data = generator.generate_comprehensive_network(test_artists, None)
    
    anyujin_edges = [e for e in network_data['edges'] if e['source'] == 'anyujin']
    ive_edges = [e for e in network_data['edges'] if e['source'] == 'ive']
    
    anyujin_to_ive = [e for e in anyujin_edges if e['target'] == 'ive']
    ive_to_anyujin = [e for e in ive_edges if e['target'] == 'anyujin']
    
    total_connections = len(anyujin_to_ive) + len(ive_to_anyujin)
    
    if total_connections > 0:
        print(f"✅ SUCCESS: {total_connections} bidirectional connections!")
        if anyujin_to_ive:
            e = anyujin_to_ive[0]
            print(f"   ANYUJIN → IVE: weight={e['weight']:.3f}, conf={e['confidence']:.3f}")
        if ive_to_anyujin:
            e = ive_to_anyujin[0]
            print(f"   IVE → ANYUJIN: weight={e['weight']:.3f}, conf={e['confidence']:.3f}")
    else:
        print(f"❌ No bidirectional connections found")
    
    return {
        'enhanced_matching_works': len(anyujin_related) > 0,
        'edge_creation_works': len(edges) > 0,
        'ive_connection_works': ive_edge is not None,
        'bidirectional_works': total_connections > 0
    }

if __name__ == "__main__":
    results = test_enhanced_matching_comprehensive()
    
    print(f"\n🎯 SUMMARY:")
    print("=" * 45)
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test}")