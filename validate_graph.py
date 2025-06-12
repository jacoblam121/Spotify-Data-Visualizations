#!/usr/bin/env python3
"""
Phase 0C: Graph validation script for network visualization.
Creates and validates artist networks before visualization development.
"""

import os
import sys
import pandas as pd
import networkx as nx
from datetime import datetime
from network_utils import initialize_network_analyzer, prepare_dataframe_for_network_analysis
from data_processor import clean_and_filter_data
from config_loader import AppConfig


def validate_network_structure(network_data: dict) -> dict:
    """
    Validate the structure and quality of the generated network.
    
    Returns:
        Dict with validation results and recommendations
    """
    print("\n🔍 Validating Network Structure...")
    
    nodes = network_data['nodes']
    edges = network_data['edges']
    
    # Create NetworkX graph for analysis
    G = nx.Graph()
    
    # Add nodes
    for node in nodes:
        G.add_node(node['id'], **node)
    
    # Add edges
    for edge in edges:
        G.add_edge(edge['source'], edge['target'], weight=edge['weight'])
    
    # Calculate network metrics
    results = {
        'basic_stats': {
            'nodes': len(nodes),
            'edges': len(edges),
            'density': nx.density(G),
            'is_connected': nx.is_connected(G),
            'connected_components': nx.number_connected_components(G)
        }
    }
    
    # Connectivity analysis
    if not nx.is_connected(G):
        # Find largest connected component
        largest_cc = max(nx.connected_components(G), key=len)
        results['connectivity'] = {
            'largest_component_size': len(largest_cc),
            'largest_component_percentage': len(largest_cc) / len(nodes) * 100,
            'isolated_nodes': [node for node in G.nodes() if G.degree(node) == 0]
        }
    
    # Degree distribution
    degrees = [G.degree(node) for node in G.nodes()]
    results['degree_stats'] = {
        'min_degree': min(degrees) if degrees else 0,
        'max_degree': max(degrees) if degrees else 0,
        'avg_degree': sum(degrees) / len(degrees) if degrees else 0,
        'nodes_with_no_connections': len([d for d in degrees if d == 0])
    }
    
    # Weight distribution
    if edges:
        weights = [edge['weight'] for edge in edges]
        results['weight_stats'] = {
            'min_weight': min(weights),
            'max_weight': max(weights),
            'avg_weight': sum(weights) / len(weights)
        }
    
    return results, G


def export_to_gephi_formats(G: nx.Graph, base_filename: str):
    """Export graph to Gephi-compatible formats."""
    print(f"\n💾 Exporting to Gephi formats...")
    
    # Export as GEXF (recommended for Gephi)
    gexf_file = f"{base_filename}.gexf"
    nx.write_gexf(G, gexf_file)
    print(f"✅ GEXF export: {gexf_file}")
    
    # Export as GraphML (alternative format)
    graphml_file = f"{base_filename}.graphml" 
    nx.write_graphml(G, graphml_file)
    print(f"✅ GraphML export: {graphml_file}")
    
    return gexf_file, graphml_file


def print_validation_report(results: dict):
    """Print a comprehensive validation report."""
    print("\n📊 NETWORK VALIDATION REPORT")
    print("=" * 50)
    
    basic = results['basic_stats']
    print(f"📈 Basic Statistics:")
    print(f"  • Nodes: {basic['nodes']}")
    print(f"  • Edges: {basic['edges']}")
    print(f"  • Density: {basic['density']:.4f}")
    print(f"  • Connected: {'Yes' if basic['is_connected'] else 'No'}")
    print(f"  • Components: {basic['connected_components']}")
    
    if 'connectivity' in results:
        conn = results['connectivity']
        print(f"\n🔗 Connectivity Analysis:")
        print(f"  • Largest component: {conn['largest_component_size']} nodes ({conn['largest_component_percentage']:.1f}%)")
        if conn['isolated_nodes']:
            print(f"  • Isolated nodes: {len(conn['isolated_nodes'])}")
            print(f"    {conn['isolated_nodes'][:5]}{'...' if len(conn['isolated_nodes']) > 5 else ''}")
    
    degree = results['degree_stats']
    print(f"\n📊 Degree Distribution:")
    print(f"  • Min degree: {degree['min_degree']}")
    print(f"  • Max degree: {degree['max_degree']}")
    print(f"  • Avg degree: {degree['avg_degree']:.2f}")
    print(f"  • Nodes with no connections: {degree['nodes_with_no_connections']}")
    
    if 'weight_stats' in results:
        weight = results['weight_stats']
        print(f"\n⚖️  Edge Weight Distribution:")
        print(f"  • Min weight: {weight['min_weight']:.4f}")
        print(f"  • Max weight: {weight['max_weight']:.4f}")
        print(f"  • Avg weight: {weight['avg_weight']:.4f}")
    
    # Quality recommendations
    print(f"\n💡 Quality Assessment:")
    if basic['density'] < 0.01:
        print("  ⚠️  Very sparse network - consider lowering similarity threshold")
    if basic['density'] > 0.3:
        print("  ⚠️  Very dense network - consider raising similarity threshold")
    
    if not basic['is_connected']:
        print("  ⚠️  Disconnected network - some artist clusters are isolated")
    
    if degree['nodes_with_no_connections'] > 0:
        print(f"  ⚠️  {degree['nodes_with_no_connections']} artists have no connections")


def validate_artist_network(top_n: int = 30, min_threshold: float = 0.1):
    """
    Main validation function to test network generation.
    
    Args:
        top_n: Number of top artists to include
        min_threshold: Minimum Last.fm similarity threshold
    """
    print(f"🚀 Starting Network Validation")
    print(f"📊 Parameters: {top_n} artists, min similarity {min_threshold}")
    
    try:
        # Load data
        print("\n📁 Loading listening data...")
        config = AppConfig('configurations.txt')
        df = clean_and_filter_data(config)
        df_network = prepare_dataframe_for_network_analysis(df)
        print(f"✅ Loaded {len(df_network)} listening records")
        
        # Initialize analyzer
        print("\n🔧 Initializing network analyzer...")
        analyzer = initialize_network_analyzer()
        
        # Create network
        print(f"\n🕸️  Creating network for top {top_n} artists...")
        network_data = analyzer.create_network_data(
            df_network, 
            top_n_artists=top_n,
            min_similarity_threshold=min_threshold
        )
        
        if not network_data['edges']:
            print("❌ No edges created! Try lowering the similarity threshold.")
            return None
        
        # Validate structure
        results, G = validate_network_structure(network_data)
        print_validation_report(results)
        
        # Export for Gephi
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"artist_network_validation_{timestamp}"
        export_to_gephi_formats(G, base_filename)
        
        # Save JSON for reference
        json_file = f"{base_filename}.json"
        analyzer.save_network_data(network_data, json_file)
        
        print(f"\n🎉 Validation complete!")
        print(f"📂 Files created:")
        print(f"  • {base_filename}.gexf (for Gephi)")
        print(f"  • {base_filename}.graphml (alternative)")
        print(f"  • {json_file} (network data)")
        
        print(f"\n📋 Next steps:")
        print(f"  1. Open {base_filename}.gexf in Gephi")
        print(f"  2. Apply a layout algorithm (Force Atlas 2 recommended)")
        print(f"  3. Verify that artist relationships make sense")
        print(f"  4. If structure looks good, proceed to Phase 1")
        
        return network_data, results, G
        
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Default validation parameters
    top_n = 30
    min_threshold = 0.1
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        top_n = int(sys.argv[1])
    if len(sys.argv) > 2:
        min_threshold = float(sys.argv[2])
    
    validate_artist_network(top_n, min_threshold)