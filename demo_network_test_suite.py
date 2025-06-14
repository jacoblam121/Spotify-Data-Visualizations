#!/usr/bin/env python3
"""
Demo script for the Comprehensive Network Test Suite
===================================================
Shows how to use the test suite and analyze results.
"""

import sys
import json
from pathlib import Path
from comprehensive_network_test_suite import (
    NetworkTestConfig, 
    ComprehensiveNetworkTestSuite,
    analyze_artist_connections,
    load_network_from_file
)

def demo_quick_test():
    """Run a quick test with minimal configuration."""
    print("🚀 Demo: Quick Network Test")
    print("=" * 35)
    
    # Create simple config for quick testing
    config = NetworkTestConfig(
        top_n_artists=8,
        seed_artists=["YOASOBI", "IVE", "BTS"],
        similarity_threshold=0.3,
        test_individual_connections=True,
        save_networks=True,
        generate_reports=True
    )
    
    # Run test suite
    suite = ComprehensiveNetworkTestSuite(config)
    suite.run_full_suite()
    
    return suite

def demo_config_file_test():
    """Run test using YAML configuration file."""
    print("\\n🚀 Demo: Configuration File Test")
    print("=" * 40)
    
    # Load config from YAML
    try:
        config = NetworkTestConfig.from_yaml("network_test_config.yaml")
        
        # Override for demo (use quick test scenario)
        config.top_n_artists = 10
        config.seed_artists = ["YOASOBI", "IVE"]
        
        print(f"✅ Loaded config from YAML")
        print(f"   Top N Artists: {config.top_n_artists}")
        print(f"   Seed Artists: {', '.join(config.seed_artists)}")
        print(f"   Similarity Threshold: {config.similarity_threshold}")
        
        # Run test suite
        suite = ComprehensiveNetworkTestSuite(config)
        suite.run_full_suite()
        
        return suite
        
    except FileNotFoundError:
        print("❌ network_test_config.yaml not found")
        return None
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

def demo_network_analysis():
    """Demo analyzing a saved network file."""
    print("\\n🔍 Demo: Network Analysis")
    print("=" * 30)
    
    # Find the most recent network file
    import glob
    network_files = glob.glob("network_test_results/comprehensive_network_*.json")
    
    if not network_files:
        print("❌ No network files found. Run a test first.")
        return
    
    # Use most recent file
    latest_file = max(network_files)
    print(f"📁 Using: {latest_file}")
    
    # Load and analyze
    graph = load_network_from_file(latest_file)
    if not graph:
        return
    
    print(f"\\n📊 Network Overview:")
    print(f"   Nodes: {graph.number_of_nodes()}")
    print(f"   Edges: {graph.number_of_edges()}")
    
    # Analyze each artist in the network
    artists = list(graph.nodes())[:5]  # First 5 artists
    
    for artist in artists:
        print(f"\\n{'='*50}")
        analyze_artist_connections(latest_file, artist)
        print("\\n" + "="*50)

def demo_visual_property_validation():
    """Demo visual property validation."""
    print("\\n🎨 Demo: Visual Property Validation")
    print("=" * 42)
    
    # Find the most recent network file
    import glob
    network_files = glob.glob("network_test_results/comprehensive_network_*.json")
    
    if not network_files:
        print("❌ No network files found. Run a test first.")
        return
    
    latest_file = max(network_files)
    
    # Load network data
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    print(f"📁 Analyzing: {latest_file}")
    print(f"\\n🎨 Visual Properties Analysis:")
    
    nodes = data.get('nodes', [])
    
    # Analyze visual properties
    node_sizes = [node.get('node_size', 0) for node in nodes]
    glow_values = [node.get('glow_value', 0) for node in nodes]
    colors = [node.get('color', '') for node in nodes]
    
    print(f"\\n📏 Node Sizes:")
    print(f"   Range: {min(node_sizes):.1f} - {max(node_sizes):.1f}")
    print(f"   Average: {sum(node_sizes)/len(node_sizes):.1f}")
    
    print(f"\\n✨ Glow Values:")
    print(f"   Range: {min(glow_values):.2f} - {max(glow_values):.2f}")
    print(f"   Average: {sum(glow_values)/len(glow_values):.2f}")
    
    print(f"\\n🌈 Colors:")
    color_counts = {}
    for color in colors:
        color_counts[color] = color_counts.get(color, 0) + 1
    
    for color, count in color_counts.items():
        print(f"   {color}: {count} artists")
    
    # Show detailed info for each artist
    print(f"\\n👥 Artist Details:")
    for node in nodes:
        name = node.get('display_name', node.get('id', 'Unknown'))
        listeners = node.get('lastfm_listeners', 0)
        size = node.get('node_size', 0)
        glow = node.get('glow_value', 0)
        color = node.get('color', '')
        confidence = node.get('verification_confidence', 0)
        method = node.get('verification_method', '')
        
        print(f"   {name}")
        print(f"     Listeners: {listeners:,}")
        print(f"     Visual: Size={size:.1f}, Glow={glow:.2f}, Color={color}")
        print(f"     Verification: {method} ({confidence:.3f})")

def demo_similarity_analysis():
    """Demo similarity relationship analysis."""
    print("\\n🔗 Demo: Similarity Analysis")
    print("=" * 32)
    
    # Find the most recent network file
    import glob
    network_files = glob.glob("network_test_results/comprehensive_network_*.json")
    
    if not network_files:
        print("❌ No network files found. Run a test first.")
        return
    
    latest_file = max(network_files)
    
    # Load network data
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    edges = data.get('edges', [])
    
    print(f"📁 Analyzing: {latest_file}")
    print(f"\\n🔗 Similarity Relationships:")
    print(f"   Total Edges: {len(edges)}")
    
    if not edges:
        print("   No edges found in network")
        return
    
    # Analyze similarity distribution
    similarities = [edge.get('similarity', 0) for edge in edges]
    sources = [edge.get('source', 'unknown') for edge in edges]
    
    print(f"\\n📊 Similarity Statistics:")
    print(f"   Range: {min(similarities):.3f} - {max(similarities):.3f}")
    print(f"   Average: {sum(similarities)/len(similarities):.3f}")
    print(f"   Median: {sorted(similarities)[len(similarities)//2]:.3f}")
    
    # Source breakdown
    source_counts = {}
    for source in sources:
        source_counts[source] = source_counts.get(source, 0) + 1
    
    print(f"\\n🌐 Data Sources:")
    for source, count in source_counts.items():
        print(f"   {source}: {count} edges")
    
    # Show top similarities
    edges_with_sim = [(edge.get('source', ''), edge.get('target', ''), edge.get('similarity', 0)) 
                      for edge in edges]
    edges_with_sim.sort(key=lambda x: x[2], reverse=True)
    
    print(f"\\n🏆 Top Similarities:")
    for i, (source, target, similarity) in enumerate(edges_with_sim[:10], 1):
        print(f"   {i:2d}. {source} ↔ {target}: {similarity:.3f}")

def main():
    """Run all demos."""
    print("🧪 Comprehensive Network Test Suite - Demo")
    print("=" * 50)
    
    # Make sure output directory exists
    Path("network_test_results").mkdir(exist_ok=True)
    
    # Run demos in sequence
    try:
        # 1. Quick test
        suite = demo_quick_test()
        
        # 2. Config file test (if available)
        demo_config_file_test()
        
        # 3. Network analysis
        demo_network_analysis()
        
        # 4. Visual property validation
        demo_visual_property_validation()
        
        # 5. Similarity analysis
        demo_similarity_analysis()
        
        print(f"\\n✨ Demo completed successfully!")
        print(f"💾 Check 'network_test_results/' directory for generated files")
        
    except KeyboardInterrupt:
        print("\\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()