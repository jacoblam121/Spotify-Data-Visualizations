#!/usr/bin/env python3
"""
Manual test script to generate a small network with edges for verification.
"""

from network_utils import ArtistNetworkAnalyzer
from data_processor import clean_and_filter_data
from config_loader import AppConfig
import pandas as pd
import json
from datetime import datetime

def create_test_network():
    """Create a small test network to verify edges are working."""
    print("🧪 Manual Network Test - Post Fix Verification")
    print("=" * 60)
    
    # Load configuration
    config = AppConfig('configurations.txt')
    analyzer = ArtistNetworkAnalyzer(config)
    
    # Load actual user data
    print("📁 Loading user listening data...")
    data_source = config.get('DataSource', 'SOURCE')
    
    if data_source == 'spotify':
        df = clean_and_filter_data(config)
        # Prepare dataframe for network analysis
        from network_utils import prepare_dataframe_for_network_analysis
        df = prepare_dataframe_for_network_analysis(df)
    else:
        print("❌ This test requires Spotify data source")
        return False
    
    print(f"✅ Loaded {len(df)} plays from {df['artist'].nunique()} artists")
    
    # Generate a small network (5 artists to keep it manageable)
    print(f"\n🕸️  Generating network with top 5 artists...")
    
    network_data = analyzer.create_network_data(
        df,
        top_n_artists=5,
        min_plays_threshold=10,
        min_similarity_threshold=0.3  # Lower threshold to get more edges
    )
    
    # Results
    print(f"\n📊 Network Results:")
    print(f"  Nodes: {len(network_data['nodes'])}")
    print(f"  Edges: {len(network_data['edges'])}")
    
    if network_data['edges']:
        print(f"\n🔗 Similarity Relationships Found:")
        for i, edge in enumerate(network_data['edges'], 1):
            print(f"  {i}. {edge['source']} ↔ {edge['target']}")
            print(f"     Similarity: {edge['weight']:.3f}")
    else:
        print("❌ No edges found - check similarity threshold")
        return False
    
    # Save the test network
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_network_fixed_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(network_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Test network saved: {filename}")
    
    # Verification summary
    print(f"\n✅ Verification Summary:")
    print(f"  - Last.fm API integration: Working")
    print(f"  - Similar artists fetching: Working") 
    print(f"  - Edge creation: Working ({len(network_data['edges'])} edges)")
    print(f"  - Network generation: Fixed!")
    
    return True

if __name__ == "__main__":
    success = create_test_network()
    if success:
        print("\n🎉 Last.fm similarity edges are now working correctly!")
    else:
        print("\n❌ Test failed - check configuration")