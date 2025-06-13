#!/usr/bin/env python3
"""
Test Large Network Generation with Configurable Parameters
==========================================================

This script tests network generation with your top 100 artists from all time,
using the configurable similarity threshold and other parameters.

This will test:
- Large network handling (100 artists = up to 4,950 possible edges)
- Performance with many API calls
- Edge distribution with diverse music taste
- Configuration-driven parameters
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from network_utils import ArtistNetworkAnalyzer, prepare_dataframe_for_network_analysis
from data_processor import clean_and_filter_data
from config_loader import AppConfig
import os

def test_large_network():
    """Test network generation with top 100 artists and configurable parameters."""
    print("🌐 Large Network Generation Test")
    print("=" * 60)
    
    try:
        # Change to project root
        original_cwd = Path.cwd()
        project_root = Path(__file__).parent.parent
        os.chdir(project_root)
        
        # Load configuration
        config = AppConfig("configurations.txt")
        network_config = config.get_network_visualization_config()
        
        print("📋 Configuration Settings:")
        print(f"   Top N Artists: {network_config['top_n_artists']}")
        print(f"   Similarity Threshold: {network_config['min_similarity_threshold']}")
        print(f"   Min Plays Threshold: {network_config['min_plays_threshold']}")
        print(f"   Node Sizing Strategy: {network_config['node_sizing_strategy']}")
        print()
        
        # Load data
        print("📁 Loading listening data from all time...")
        df = clean_and_filter_data(config)
        df = prepare_dataframe_for_network_analysis(df)
        
        total_plays = len(df)
        unique_artists = df['artist'].nunique()
        timeframe = f"{df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}"
        
        print(f"✅ Loaded {total_plays:,} plays from {unique_artists:,} unique artists")
        print(f"📅 Timeframe: {timeframe}")
        print()
        
        # Show top artists preview
        top_artists_preview = df.groupby('artist').size().sort_values(ascending=False).head(20)
        print("🎵 Top 20 artists in your all-time data:")
        for i, (artist, plays) in enumerate(top_artists_preview.items(), 1):
            print(f"   {i:2d}. {artist:<25} ({plays:,} plays)")
        print()
        
        # Initialize network analyzer
        print("🔧 Initializing network analyzer...")
        analyzer = ArtistNetworkAnalyzer(config)
        
        # Generate large network using config parameters
        print(f"🕸️  Generating network with {network_config['top_n_artists']} artists...")
        print("   ⚠️  This may take 5-10 minutes due to many API calls...")
        print("   📊 Progress will be shown every 5 artists")
        print()
        
        start_time = datetime.now()
        
        # Use config defaults (no parameters = use config)
        network_data = analyzer.create_network_data(df)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Results analysis
        nodes = network_data['nodes']
        edges = network_data['edges']
        
        print()
        print("📊 Network Generation Results:")
        print(f"   Generation time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"   Nodes (artists): {len(nodes)}")
        print(f"   Edges (similarities): {len(edges)}")
        
        if edges:
            # Edge analysis
            similarities = [edge['weight'] for edge in edges]
            avg_similarity = sum(similarities) / len(similarities)
            max_similarity = max(similarities)
            min_similarity = min(similarities)
            
            print(f"   Average similarity: {avg_similarity:.3f}")
            print(f"   Similarity range: {min_similarity:.3f} - {max_similarity:.3f}")
            print()
            
            # Show strongest relationships
            sorted_edges = sorted(edges, key=lambda x: x['weight'], reverse=True)
            print("🔗 Top 10 Strongest Artist Relationships:")
            for i, edge in enumerate(sorted_edges[:10], 1):
                similarity_pct = edge['weight'] * 100
                print(f"   {i:2d}. {edge['source']} ↔ {edge['target']}")
                print(f"       Similarity: {edge['weight']:.3f} ({similarity_pct:.1f}%)")
            print()
            
            # Network density analysis
            max_possible_edges = len(nodes) * (len(nodes) - 1) // 2
            density = len(edges) / max_possible_edges if max_possible_edges > 0 else 0
            print(f"📈 Network Statistics:")
            print(f"   Network density: {density:.4f} ({density*100:.2f}%)")
            print(f"   Max possible edges: {max_possible_edges:,}")
            print(f"   Actual edges: {len(edges):,}")
            
            # Save the large network
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"large_network_{len(nodes)}artists_{timestamp}.json"
            filepath = Path(__file__).parent / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(network_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Large network saved: {filename}")
            print(f"   File size: {filepath.stat().st_size / 1024 / 1024:.1f} MB")
            print()
            
            print("✅ SUCCESS: Large network generation completed!")
            print(f"   Your music library created a network with {len(edges)} relationships")
            print(f"   Ready for visualization with {len(nodes)} artists")
            
        else:
            print("❌ NO EDGES CREATED")
            print("   This could mean:")
            print(f"   - Similarity threshold too high ({network_config['min_similarity_threshold']:.2f})")
            print("   - Very diverse music taste with little cross-genre similarity")
            print("   - Artists don't have Last.fm similarity data")
            print()
            print("💡 Try lowering MIN_SIMILARITY_THRESHOLD in configurations.txt")
            print("   Recommended: 0.1 for diverse taste, 0.05 for maximum edges")
        
        return len(edges) > 0
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Restore working directory
        try:
            os.chdir(original_cwd)
        except:
            pass

if __name__ == "__main__":
    success = test_large_network()
    
    print()
    if success:
        print("🎉 Large network test completed successfully!")
        print("   Your network is ready for visualization.")
    else:
        print("❌ Large network test failed.")
        print("   Check the output above for details.")