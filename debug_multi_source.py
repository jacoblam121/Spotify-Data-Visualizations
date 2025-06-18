#!/usr/bin/env python3
"""
Debug Multi-Source Edge Detection
=================================
Quick test to verify multi-source edge creation and detection.
"""

import sys
from pathlib import Path

# Add project modules
sys.path.insert(0, str(Path(__file__).parent))

from network_utils import ArtistNetworkAnalyzer, prepare_dataframe_for_network_analysis
from data_processor import clean_and_filter_data
from config_loader import AppConfig

def test_multi_source_detection():
    """Test if multi-source edges are being created and detected properly."""
    print("🔍 Testing Multi-Source Edge Detection")
    print("=" * 40)
    
    # Initialize
    config = AppConfig("configurations.txt")
    analyzer = ArtistNetworkAnalyzer(config)
    
    # Load minimal data
    print("📂 Loading data...")
    raw_df = clean_and_filter_data(config)
    df = prepare_dataframe_for_network_analysis(raw_df)
    
    # Test with just 3 artists for quick debugging
    print("🧪 Testing with 3 artists...")
    network_data = analyzer.create_network_data(
        df,
        top_n_artists=3,
        min_plays_threshold=1,
        min_similarity_threshold=0.1
    )
    
    # Analyze edges
    edges = network_data.get('edges', [])
    print(f"\n📊 Found {len(edges)} total edges")
    
    # Check for multi-source indicators
    multi_source_edges = []
    sources_found = set()
    
    for i, edge in enumerate(edges[:5]):  # Check first 5 edges
        print(f"\n🔍 Edge {i+1}:")
        print(f"   {edge.get('source', 'unknown')} -> {edge.get('target', 'unknown')}")
        print(f"   Weight: {edge.get('weight', 0):.3f}")
        print(f"   Confidence: {edge.get('confidence', 0):.3f}")
        
        # Check for multi-source indicators
        sources = edge.get('sources', [])
        source_count = edge.get('source_count', 1)
        fusion_method = edge.get('fusion_method', 'unknown')
        
        print(f"   Sources: {sources}")
        print(f"   Source count: {source_count}")
        print(f"   Fusion method: {fusion_method}")
        
        if source_count > 1 or len(sources) > 1:
            multi_source_edges.append(edge)
            print(f"   ✅ MULTI-SOURCE DETECTED!")
        
        # Collect all unique sources
        if sources:
            sources_found.update(sources)
    
    print(f"\n📈 Summary:")
    print(f"   Total edges checked: {min(len(edges), 5)}")
    print(f"   Multi-source edges found: {len(multi_source_edges)}")
    print(f"   Unique sources: {list(sources_found)}")
    
    if len(multi_source_edges) > 0:
        print(f"   ✅ Multi-source edge detection: WORKING")
        return True
    else:
        print(f"   ❌ Multi-source edge detection: NOT WORKING")
        return False

if __name__ == "__main__":
    test_multi_source_detection()