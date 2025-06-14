#!/usr/bin/env python3
"""
Test ANYUJIN-IVE connection after Last.fm fix
"""

import json
from integrated_network_generator import IntegratedNetworkGenerator

def test_anyujin_ive_connection():
    """Test the specific ANYUJIN-IVE connection after fixing Last.fm integration."""
    
    print("🔍 Testing ANYUJIN-IVE Connection After Last.fm Fix")
    print("=" * 60)
    
    # Load artist data
    with open('artist_data.json', 'r', encoding='utf-8') as f:
        artists_data = json.load(f)
    
    # Initialize network generator
    generator = IntegratedNetworkGenerator()
    
    # Override thresholds for testing
    generator.min_similarity_threshold = 0.1  # Lower threshold to catch more connections
    generator.min_plays_threshold = 1
    
    # Test ANYUJIN connections
    print("\n1️⃣ Testing ANYUJIN similarity sources:")
    anyujin_similarity = generator._get_multi_source_similarity("ANYUJIN")
    
    for source, results in anyujin_similarity.items():
        print(f"   {source}: {len(results)} results")
        if results:
            # Look for IVE-related artists
            ive_related = [r for r in results if 'IVE' in r['name'].upper() or 'IVE' in r.get('tags', [])]
            if ive_related:
                print(f"      🎯 IVE-related matches: {[r['name'] for r in ive_related]}")
            
            # Show top 5 results
            top_5 = results[:5]
            print("      Top matches: " + str([f"{r['name']} ({r.get('similarity', 'N/A')})" for r in top_5]))
    
    # Test IVE connections back to ANYUJIN
    print("\n2️⃣ Testing IVE similarity sources:")
    ive_similarity = generator._get_multi_source_similarity("IVE")
    
    for source, results in ive_similarity.items():
        print(f"   {source}: {len(results)} results")
        if results:
            # Look for ANYUJIN-related artists
            anyujin_related = [r for r in results if 'ANYUJIN' in r['name'].upper() or 'YUJIN' in r['name'].upper()]
            if anyujin_related:
                print(f"      🎯 ANYUJIN-related matches: {[r['name'] for r in anyujin_related]}")
            
            # Show top 5 results
            top_5 = results[:5]
            print("      Top matches: " + str([f"{r['name']} ({r.get('similarity', 'N/A')})" for r in top_5]))
    
    # Test bidirectional edge creation
    print("\n3️⃣ Testing edge creation between ANYUJIN and IVE:")
    
    # Create artist lookup from actual data
    target_artists = {a['name'].lower(): a for a in artists_data}
    
    # Find ANYUJIN and IVE in actual data
    anyujin_data = target_artists.get('anyujin')
    ive_data = target_artists.get('ive')
    
    print(f"   ANYUJIN in data: {anyujin_data}")
    print(f"   IVE in data: {ive_data}")
    
    if not anyujin_data or not ive_data:
        print("   ⚠️  One or both artists not found in dataset - using mock data")
        anyujin_data = {'name': 'ANYUJIN', 'play_count': 100}
        ive_data = {'name': 'IVE', 'play_count': 200}
        target_artists['anyujin'] = anyujin_data
        target_artists['ive'] = ive_data
    
    # Test ANYUJIN -> IVE edge
    anyujin_edges = generator._create_edges_for_artist(
        anyujin_data, 
        anyujin_similarity, 
        target_artists
    )
    
    ive_edges = generator._create_edges_for_artist(
        ive_data, 
        ive_similarity, 
        target_artists
    )
    
    print(f"   ANYUJIN -> others: {len(anyujin_edges)} edges")
    print(f"   IVE -> others: {len(ive_edges)} edges")
    
    # Look for the specific connection
    anyujin_to_ive = [e for e in anyujin_edges if e['target'] == 'ive']
    ive_to_anyujin = [e for e in ive_edges if e['target'] == 'anyujin']
    
    if anyujin_to_ive:
        edge = anyujin_to_ive[0]
        print(f"   ✅ Found ANYUJIN -> IVE edge: weight={edge['weight']:.3f}, sources={edge['sources']}")
    else:
        print("   ❌ No ANYUJIN -> IVE edge found")
    
    if ive_to_anyujin:
        edge = ive_to_anyujin[0]
        print(f"   ✅ Found IVE -> ANYUJIN edge: weight={edge['weight']:.3f}, sources={edge['sources']}")
    else:
        print("   ❌ No IVE -> ANYUJIN edge found")
    
    # Summary
    total_connections = len(anyujin_to_ive) + len(ive_to_anyujin)
    print(f"\n🎯 Result: {total_connections} bidirectional connections found between ANYUJIN and IVE")
    
    if total_connections > 0:
        print("✅ Last.fm integration fix successful!")
    else:
        print("❌ Still no connections found - may need further investigation")

if __name__ == "__main__":
    test_anyujin_ive_connection()