#!/usr/bin/env python3
"""
Test the bidirectional similarity fix with a small dataset.
"""

from network_utils import ArtistNetworkAnalyzer, prepare_dataframe_for_network_analysis
from data_processor import clean_and_filter_data
from config_loader import AppConfig

def test_bidirectional_fix():
    """Test bidirectional similarity with 10 artists."""
    print("🔄 Testing Bidirectional Similarity Fix")
    print("=" * 50)
    
    # Load config and data
    config = AppConfig('configurations.txt')
    df = clean_and_filter_data(config)
    df = prepare_dataframe_for_network_analysis(df)
    
    # Show top artists
    top_artists = df.groupby('artist').size().sort_values(ascending=False).head(10)
    print("🎵 Testing with top 10 artists:")
    for i, (artist, plays) in enumerate(top_artists.items(), 1):
        print(f"   {i:2d}. {artist} ({plays} plays)")
    print()
    
    # Test with old vs new logic
    analyzer = ArtistNetworkAnalyzer(config)
    
    print("🕸️  Generating network with bidirectional similarity...")
    network_data = analyzer.create_network_data(
        df, 
        top_n_artists=10, 
        min_plays_threshold=5,
        min_similarity_threshold=0.2
    )
    
    edges = network_data['edges']
    print(f"\n📊 Results:")
    print(f"   Nodes: {len(network_data['nodes'])}")
    print(f"   Edges: {len(edges)}")
    
    if edges:
        print(f"\n🔗 Edge relationships found:")
        for i, edge in enumerate(edges, 1):
            direction = edge.get('bidirectional_data', {}).get('max_direction', 'unknown')
            print(f"   {i:2d}. {edge['source']} ↔ {edge['target']}")
            print(f"       Similarity: {edge['weight']:.3f} (via {direction})")
            
            # Show bidirectional data if available
            if 'bidirectional_data' in edge:
                bd = edge['bidirectional_data']
                print(f"       A→B: {bd['a_to_b']:.3f}, B→A: {bd['b_to_a']:.3f}")
        
        print(f"\n✅ Success! Found {len(edges)} relationships")
        return True
    else:
        print("❌ Still no edges found")
        return False

if __name__ == "__main__":
    test_bidirectional_fix()