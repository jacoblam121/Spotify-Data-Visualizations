#!/usr/bin/env python3
"""
Generate a small network to verify the complete dual-profile system.
"""

import json
from integrated_network_generator import IntegratedNetworkGenerator

def test_complete_network():
    """Generate a complete network with dual-profile system."""
    print("🎯 Testing Complete Dual-Profile Network Generation")
    print("=" * 60)
    
    # Initialize generator
    generator = IntegratedNetworkGenerator()
    
    # Load artist data
    with open('artist_data.json', 'r', encoding='utf-8') as f:
        all_artists = json.load(f)
    
    # Filter to test artists
    test_artist_names = ['anyujin', 'ive', 'newjeans', 'aespa', 'itzy']
    test_artists = []
    
    for artist in all_artists:
        for test_name in test_artist_names:
            if test_name.lower() in artist['name'].lower():
                test_artists.append(artist)
                break
    
    print(f"🌐 Generating network with {len(test_artists)} artists...")
    print(f"   Artists: {[a['name'] for a in test_artists]}")
    
    network_data = generator.generate_comprehensive_network(
        artists_data=test_artists,
        output_filename='test_dual_profile_network.json'
    )
    
    print(f"\n📊 Network Statistics:")
    print(f"   Nodes: {len(network_data['nodes'])}")
    print(f"   Edges: {len(network_data['edges'])}")
    
    # Check IVE node specifically
    ive_node = None
    for node in network_data['nodes']:
        if 'ive' in node['name'].lower():
            ive_node = node
            break
    
    if ive_node:
        print(f"\n🎯 IVE Node Details:")
        print(f"   Name: {ive_node['name']}")
        print(f"   Listeners: {ive_node.get('listeners', 0):,}")
        print(f"   Play count: {ive_node['play_count']}")
        print(f"   Canonical name: {ive_node.get('canonical_name', 'N/A')}")
        print(f"   Metadata source: {ive_node.get('display_metadata_source', 'N/A')}")
        
        if ive_node.get('listeners', 0) > 800000:
            print("   ✅ HIGH LISTENER COUNT - Dual-profile working!")
        else:
            print("   ⚠️  Low listener count - may need debugging")
    
    # Check for ANYUJIN-IVE connections
    anyujin_connections = []
    for edge in network_data['edges']:
        if 'anyujin' in edge['source'].lower() and 'ive' in edge['target'].lower():
            anyujin_connections.append(edge)
        elif 'ive' in edge['source'].lower() and 'anyujin' in edge['target'].lower():
            anyujin_connections.append(edge)
    
    print(f"\n🔗 ANYUJIN-IVE Connections: {len(anyujin_connections)}")
    for conn in anyujin_connections:
        print(f"   {conn['source']} → {conn['target']} (weight: {conn['weight']:.3f})")
    
    # Save network for inspection
    output_file = 'test_dual_profile_network.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(network_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Network saved to {output_file}")
    
    # Summary
    success_criteria = [
        ("Network generated", len(network_data['nodes']) > 0),
        ("IVE node found", ive_node is not None),
        ("High listener count", ive_node and ive_node.get('listeners', 0) > 800000),
        ("ANYUJIN connections", len(anyujin_connections) > 0)
    ]
    
    print(f"\n🏁 Success Criteria:")
    all_success = True
    for criterion, passed in success_criteria:
        status = "✅" if passed else "❌"
        print(f"   {status} {criterion}")
        if not passed:
            all_success = False
    
    if all_success:
        print(f"\n🎉 COMPLETE DUAL-PROFILE SYSTEM WORKING!")
        print(f"   Ready for production use with accurate visualization and functional connections")
    else:
        print(f"\n⚠️  Some criteria failed - system needs further debugging")

if __name__ == "__main__":
    test_complete_network()