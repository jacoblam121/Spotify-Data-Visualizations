#!/usr/bin/env python3
"""
Phase 0.0.1: Analyze Current Network Output Structure
Creates a sample network and analyzes its structure for enhancement planning.
"""

import json
import os
from datetime import datetime
from network_utils import initialize_network_analyzer, prepare_dataframe_for_network_analysis
from data_processor import clean_and_filter_data
from config_loader import AppConfig

def analyze_current_structure():
    """Analyze current network JSON structure and identify gaps."""
    print("🔍 Phase 0.0.1: Analyzing Current Network Structure")
    print("=" * 60)
    
    try:
        # Load configuration and add missing network config
        config = AppConfig('configurations.txt')
        
        # Temporarily patch missing network config
        def get_network_config():
            return {
                'node_sizing_strategy': 'hybrid_multiply',
                'listener_count_source': 'spotify',
                'fetch_both_sources': True,
                'fallback_behavior': 'fallback'
            }
        
        # Monkey patch the method
        config.get_network_visualization_config = get_network_config
        
        print(f"📊 Loading user data...")
        df = clean_and_filter_data(config)
        
        if df is None or df.empty:
            print("❌ No data available")
            return False
        
        print(f"✅ Loaded {len(df)} plays")
        
        # Prepare for network analysis
        df_network = prepare_dataframe_for_network_analysis(df)
        
        # Create small sample network
        analyzer = initialize_network_analyzer()
        analyzer.config = config  # Use patched config
        
        print(f"🕸️  Generating sample network (5 artists)...")
        network_data = analyzer.create_network_data(
            df_network,
            top_n_artists=5,
            min_plays_threshold=10,
            min_similarity_threshold=0.1
        )
        
        if not network_data:
            print("❌ Failed to generate network data")
            return False
        
        # Save sample for analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sample_file = f"current_network_sample_{timestamp}.json"
        
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Sample saved: {sample_file}")
        
        # Analyze structure
        print(f"\n📊 Current Structure Analysis:")
        print(f"=" * 40)
        
        nodes = network_data.get('nodes', [])
        edges = network_data.get('edges', [])
        metadata = network_data.get('metadata', {})
        
        print(f"📈 Overview:")
        print(f"  Nodes: {len(nodes)}")
        print(f"  Edges: {len(edges)}")
        print(f"  Has metadata: {'✅' if metadata else '❌'}")
        
        # Analyze node structure
        if nodes:
            sample_node = nodes[0]
            print(f"\n🎵 Sample Node Structure:")
            for key, value in sample_node.items():
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                print(f"  {key}: {type(value).__name__} = {value}")
            
            # Check what's missing for D3.js
            print(f"\n❌ Missing for D3.js Visualization:")
            missing_fields = []
            
            if 'id' not in sample_node or sample_node['id'] == sample_node.get('name'):
                missing_fields.append("Stable ID system (currently uses artist names)")
            
            viz_fields = ['radius', 'size_score', 'image_url', 'placeholder_color']
            missing_viz = [f for f in viz_fields if f not in sample_node]
            if missing_viz:
                missing_fields.append(f"Visualization properties: {', '.join(missing_viz)}")
            
            if 'spotify_id' not in sample_node:
                missing_fields.append("Spotify IDs for stable identification")
            
            for i, field in enumerate(missing_fields, 1):
                print(f"    {i}. {field}")
        
        # Analyze edge structure
        if edges:
            sample_edge = edges[0]
            print(f"\n🔗 Sample Edge Structure:")
            for key, value in sample_edge.items():
                print(f"  {key}: {type(value).__name__} = {value}")
            
            print(f"\n❌ Missing for D3.js Edges:")
            edge_missing = []
            
            if 'type' not in sample_edge:
                edge_missing.append("Edge type classification")
            
            if 'strength' not in sample_edge:
                edge_missing.append("Normalized strength (0-1) for force simulation")
            
            for i, field in enumerate(edge_missing, 1):
                print(f"    {i}. {field}")
        else:
            print(f"\n🔗 No edges found in sample")
        
        # Enhancement recommendations
        print(f"\n🎯 Enhancement Recommendations:")
        print(f"=" * 40)
        recommendations = [
            "Implement stable ID system (spotify:id, mbid:id, local:hash)",
            "Add visualization properties (radius, size_score, colors)",
            "Create hybrid sizing algorithm emphasizing Spotify metrics",
            "Add image URLs from existing cache",
            "Implement D3.js standard nodes/links structure",
            "Add edge type classification and strength normalization"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        
        print(f"\n✅ Structure analysis complete!")
        print(f"📄 Review detailed output in: {sample_file}")
        
        return sample_file
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = analyze_current_structure()
    if result:
        print(f"\n🎉 Phase 0.0.1 completed successfully!")
        print(f"Next: Design enhanced data structure based on analysis")
    else:
        print(f"\n💥 Phase 0.0.1 failed - check configuration")