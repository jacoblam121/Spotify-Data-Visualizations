#!/usr/bin/env python3
"""
Test Integrated Network Generator (Small Sample)
================================================
Test the integrated network generator with a small sample to verify it's working
with Last.fm as primary source.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from integrated_network_generator import IntegratedNetworkGenerator

def test_small_network():
    """Test network generation with a small sample of artists."""
    print("🧪 Testing Integrated Network Generator (Small Sample)")
    print("=" * 55)
    
    # Create test artist data
    test_artists = [
        {'name': 'ANYUJIN', 'play_count': 411},
        {'name': 'IVE', 'play_count': 662},
        {'name': 'TWICE', 'play_count': 1057},
        {'name': 'IU', 'play_count': 2265},
        {'name': 'Taylor Swift', 'play_count': 5216},
        {'name': 'Paramore', 'play_count': 3460},
        {'name': 'Tonight Alive', 'play_count': 852},
        {'name': 'BTS', 'play_count': 800}
    ]
    
    print(f"🎯 Testing with {len(test_artists)} artists:")
    for artist in test_artists:
        print(f"   • {artist['name']} ({artist['play_count']} plays)")
    
    # Initialize generator
    generator = IntegratedNetworkGenerator()
    
    # Generate network
    network_data = generator.generate_comprehensive_network(
        test_artists,
        output_filename="test_integrated_network_small.json"
    )
    
    # Show statistics
    stats = generator.get_network_statistics(network_data)
    
    print(f"\n📊 Test Results:")
    print(f"   Nodes: {stats['total_nodes']}")
    print(f"   Edges: {stats['total_edges']}")
    print(f"   Average confidence: {stats['average_confidence']:.3f}")
    print(f"   Average similarity: {stats['average_similarity']:.3f}")
    print(f"   Factual edges: {stats['factual_edges']} ({stats['factual_percentage']:.1f}%)")
    
    print(f"\n🔌 Source Usage:")
    for source, count in stats['source_statistics'].items():
        percentage = (count / stats['total_edges']) * 100
        print(f"   {source}: {count} edges ({percentage:.1f}%)")
    
    # Check specific critical connections
    print(f"\n🔍 Critical Connection Analysis:")
    
    edges = network_data.get('edges', [])
    
    # Check ANYUJIN-IVE connection
    anyujin_ive = any(
        (edge['source'] == 'anyujin' and edge['target'] == 'ive') or
        (edge['source'] == 'ive' and edge['target'] == 'anyujin')
        for edge in edges
    )
    print(f"   ANYUJIN ↔ IVE: {'✅ Connected' if anyujin_ive else '❌ Missing'}")
    
    if anyujin_ive:
        # Find the edge details
        anyujin_ive_edge = next(
            edge for edge in edges
            if ((edge['source'] == 'anyujin' and edge['target'] == 'ive') or
                (edge['source'] == 'ive' and edge['target'] == 'anyujin'))
        )
        print(f"      Weight: {anyujin_ive_edge['weight']:.3f}")
        print(f"      Sources: {', '.join(anyujin_ive_edge['sources'])}")
        print(f"      Factual: {anyujin_ive_edge['is_factual']}")
    
    # Check IU-TWICE connection
    iu_twice = any(
        (edge['source'] == 'iu' and edge['target'] == 'twice') or
        (edge['source'] == 'twice' and edge['target'] == 'iu')
        for edge in edges
    )
    print(f"   IU ↔ TWICE: {'✅ Connected' if iu_twice else '❌ Missing'}")
    
    # Check Paramore-Tonight Alive connection  
    paramore_tonight = any(
        (edge['source'] == 'paramore' and edge['target'] == 'tonight_alive') or
        (edge['source'] == 'tonight_alive' and edge['target'] == 'paramore')
        for edge in edges
    )
    print(f"   Paramore ↔ Tonight Alive: {'✅ Connected' if paramore_tonight else '❌ Missing'}")
    
    print(f"\n🎉 Integration test complete!")
    print(f"   Last.fm as primary: {'✅' if 'lastfm' in stats['source_statistics'] else '❌'}")
    print(f"   Multi-source fusion: {'✅' if len(stats['source_statistics']) > 1 else '❌'}")
    print(f"   Manual connections: {'✅' if 'manual' in stats['source_statistics'] else '❌'}")

if __name__ == "__main__":
    test_small_network()