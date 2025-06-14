#!/usr/bin/env python3
"""
Complete test of ANYUJIN-IVE connection using the full enhanced pipeline
"""

import json
from integrated_network_generator import IntegratedNetworkGenerator

def test_complete_anyujin_ive():
    """Test the complete ANYUJIN-IVE connection pipeline."""
    
    print("🎯 Complete ANYUJIN-IVE Connection Test")
    print("=" * 45)
    
    # Load a small subset of artist data for testing
    with open('artist_data.json', 'r', encoding='utf-8') as f:
        all_artists = json.load(f)
    
    # Create a test dataset with just ANYUJIN, IVE, and a few others
    test_artists = []
    for artist in all_artists:
        if artist['name'] in ['anyujin', 'ive', 'taylor swift', 'paramore', 'twice']:
            test_artists.append(artist)
    
    print(f"📊 Test dataset: {[a['name'] for a in test_artists]}")
    
    # Initialize network generator
    generator = IntegratedNetworkGenerator()
    
    print(f"\n🔗 Generating network with enhanced matching...")
    
    # Generate the full network using the enhanced system
    network_data = generator.generate_comprehensive_network(test_artists, "test_anyujin_ive_network.json")
    
    print(f"\n📈 Network Results:")
    print(f"   Total nodes: {len(network_data['nodes'])}")
    print(f"   Total edges: {len(network_data['edges'])}")
    
    # Look for ANYUJIN-IVE connections specifically
    anyujin_edges = [e for e in network_data['edges'] if e['source'] == 'anyujin']
    ive_edges = [e for e in network_data['edges'] if e['source'] == 'ive']
    
    print(f"\n🎯 ANYUJIN connections:")
    for edge in anyujin_edges:
        target_name = [n['name'] for n in network_data['nodes'] if n['id'] == edge['target']][0]
        print(f"   -> {target_name}: weight={edge['weight']:.3f}, sources={edge['sources']}")
    
    print(f"\n🎯 IVE connections:")
    for edge in ive_edges:
        target_name = [n['name'] for n in network_data['nodes'] if n['id'] == edge['target']][0]
        print(f"   -> {target_name}: weight={edge['weight']:.3f}, sources={edge['sources']}")
    
    # Check for bidirectional connection
    anyujin_to_ive = [e for e in anyujin_edges if e['target'] == 'ive']
    ive_to_anyujin = [e for e in ive_edges if e['target'] == 'anyujin']
    
    print(f"\n✅ Final Results:")
    if anyujin_to_ive:
        edge = anyujin_to_ive[0]
        print(f"   ANYUJIN -> IVE: weight={edge['weight']:.3f}, confidence={edge['confidence']:.3f}")
    else:
        print(f"   ❌ No ANYUJIN -> IVE edge found")
    
    if ive_to_anyujin:
        edge = ive_to_anyujin[0]
        print(f"   IVE -> ANYUJIN: weight={edge['weight']:.3f}, confidence={edge['confidence']:.3f}")
    else:
        print(f"   ❌ No IVE -> ANYUJIN edge found")
    
    total_connections = len(anyujin_to_ive) + len(ive_to_anyujin)
    if total_connections > 0:
        print(f"\n🎉 SUCCESS: {total_connections} bidirectional connections found!")
        print(f"   Enhanced name matching system is working!")
    else:
        print(f"\n💔 No connections found - needs further debugging")
    
    return network_data

if __name__ == "__main__":
    test_complete_anyujin_ive()