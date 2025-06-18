#!/usr/bin/env python3
"""
Test Multi-Source Detection with Specific Artist Pairs
======================================================
Test with artist pairs that are likely to have multi-source overlap.
"""

import sys
from pathlib import Path

# Add project modules
sys.path.insert(0, str(Path(__file__).parent))

from ultimate_similarity_system import UltimateSimilaritySystem
from comprehensive_edge_weighting_system import ComprehensiveEdgeWeighter, EdgeWeightingConfig
from config_loader import AppConfig

def test_specific_artist_overlap():
    """Test specific artists that should have multi-source overlap."""
    print("🔍 Testing Multi-Source Overlap with Popular Artists")
    print("=" * 55)
    
    # Initialize systems
    config = AppConfig("configurations.txt")
    ultimate_system = UltimateSimilaritySystem(config)
    edge_config = EdgeWeightingConfig()
    edge_weighter = ComprehensiveEdgeWeighter(edge_config)
    
    # Test with very popular artists that should have overlap
    test_artist = "taylor swift"
    print(f"\n🎯 Testing similarities for '{test_artist}'")
    
    # Get individual source edges (no premature fusion)
    similarities = ultimate_system.get_ultimate_similar_artists(
        test_artist, 
        limit=20,  # Get more results to increase chance of overlap
        min_threshold=0.1
    )
    
    print(f"\n📊 Found {len(similarities)} total similarities:")
    
    # Group by target artist to find multi-source overlaps
    target_groups = {}
    for sim in similarities:
        target = sim['name']
        if target not in target_groups:
            target_groups[target] = []
        target_groups[target].append(sim)
    
    # Look for multi-source targets
    multi_source_targets = {target: sources for target, sources in target_groups.items() if len(sources) > 1}
    
    print(f"\n🔍 Target artist analysis:")
    for target, sources in target_groups.items():
        source_names = [s['source'] for s in sources]
        if len(sources) > 1:
            print(f"   ✅ {target}: {len(sources)} sources - {source_names}")
        else:
            print(f"   📍 {target}: 1 source - {source_names[0]}")
    
    if multi_source_targets:
        print(f"\n🌟 Found {len(multi_source_targets)} targets with multi-source overlap!")
        
        # Test edge creation for a multi-source target
        for target, sources in multi_source_targets.items():
            print(f"\n🧪 Testing edge creation for {test_artist} -> {target}")
            
            # Simulate the grouped data that ComprehensiveEdgeWeighter expects
            grouped_data = {}
            for source in sources:
                source_name = source['source']
                if source_name not in grouped_data:
                    grouped_data[source_name] = []
                grouped_data[source_name].append(source)
            
            # Create weighted edge
            edge = edge_weighter.create_weighted_edge(test_artist, target, grouped_data)
            if edge:
                edge_dict = edge.to_d3_format()
                print(f"   ✅ Edge created successfully!")
                print(f"   Sources: {edge_dict['sources']}")
                print(f"   Source count: {edge_dict['source_count']}")
                print(f"   Weight: {edge_dict['weight']:.3f}")
                print(f"   Confidence: {edge_dict['confidence']:.3f}")
                print(f"   Fusion method: {edge_dict['fusion_method']}")
                
                if edge_dict['source_count'] > 1:
                    print(f"   🎉 MULTI-SOURCE EDGE DETECTED!")
                    return True
            else:
                print(f"   ❌ Edge creation failed")
            
            break  # Test only the first multi-source target
    else:
        print(f"\n❌ No multi-source overlaps found for {test_artist}")
        print("   This could mean:")
        print("   1. Last.fm and Deezer have different similarity algorithms")
        print("   2. Need to test with different artists")
        print("   3. Need to lower similarity thresholds")
    
    return False

if __name__ == "__main__":
    success = test_specific_artist_overlap()
    if success:
        print(f"\n✅ Multi-source edge detection is working!")
    else:
        print(f"\n⚠️  No multi-source edges found in this test")
        print(f"   Try testing with more popular artists or lower thresholds")