#!/usr/bin/env python3
"""
Debug Edge Creation
===================
Debug why edges aren't being created from Last.fm data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from integrated_network_generator import IntegratedNetworkGenerator
from fixed_edge_weighting import FixedEdgeWeighter

def debug_edge_creation():
    """Debug edge creation process."""
    print("🔍 Debug Edge Creation Process")
    print("=" * 35)
    
    generator = IntegratedNetworkGenerator()
    
    # Test Taylor Swift (should have many connections)
    artist = "Taylor Swift"
    print(f"\n🎯 Testing edge creation for '{artist}':")
    
    # Get similarity data
    similarity_data = generator._get_multi_source_similarity(artist)
    
    print(f"\n📊 Similarity data summary:")
    for source, results in similarity_data.items():
        print(f"   {source}: {len(results)} results")
    
    # Test edge creation for a few specific targets
    test_targets = ["Ed Sheeran", "Olivia Rodrigo", "Harry Styles", "Sabrina Carpenter"]
    
    for target in test_targets:
        print(f"\n🔗 Testing edge creation: {artist} → {target}")
        
        # Check if target exists in similarity data
        found_in_sources = {}
        for source, results in similarity_data.items():
            for result in results:
                if result.get('name', '').lower() == target.lower():
                    found_in_sources[source] = result
                    break
        
        print(f"   Found in sources: {list(found_in_sources.keys())}")
        for source, data in found_in_sources.items():
            score = data.get('match', 0.0)
            print(f"      {source}: {score:.3f}")
        
        # Try to create edge
        edge = generator.edge_weighter.create_weighted_edge(artist, target, similarity_data)
        
        if edge:
            print(f"   ✅ Edge created: sim={edge.similarity:.3f}, conf={edge.confidence:.3f}")
            print(f"      Sources: {[c.source for c in edge.contributions]}")
        else:
            print(f"   ❌ Edge creation failed")
            
            # Debug why it failed
            print(f"   🔍 Debugging edge creation failure:")
            
            # Check if the fixed edge weighter can find the target
            weighter = FixedEdgeWeighter()
            
            # Test each source individually
            for source, result in found_in_sources.items():
                single_source_data = {source: [result]}
                test_edge = weighter.create_weighted_edge(artist, target, single_source_data)
                
                if test_edge:
                    print(f"      ✅ {source} alone works: {test_edge.similarity:.3f}")
                else:
                    print(f"      ❌ {source} alone fails")

if __name__ == "__main__":
    debug_edge_creation()