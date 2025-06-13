#!/usr/bin/env python3
"""
Test the bidirectional fix with the full 100-artist network.
"""

from network_utils import ArtistNetworkAnalyzer, prepare_dataframe_for_network_analysis
from data_processor import clean_and_filter_data
from config_loader import AppConfig
import json
from datetime import datetime

def test_full_bidirectional():
    """Test bidirectional similarity with full config."""
    print("🌐 Testing Full Bidirectional Network (100 Artists)")
    print("=" * 60)
    
    # Load config and data
    config = AppConfig('configurations.txt')
    df = clean_and_filter_data(config)
    df = prepare_dataframe_for_network_analysis(df)
    
    print(f"📁 Loaded {len(df):,} plays from {df['artist'].nunique():,} artists")
    
    # Show K-pop artists in top 20 to see what we're working with
    top_20 = df.groupby('artist').size().sort_values(ascending=False).head(20)
    kpop_artists = []
    for artist, plays in top_20.items():
        # Simple heuristic to identify potential K-pop artists
        if any(keyword in artist.lower() for keyword in ['ive', 'blackpink', 'twice', 'rosé', 'iu', 'newjeans', 'aespa', 'itzy']):
            kpop_artists.append((artist, plays))
    
    print(f"🎵 K-pop artists in your top 20:")
    for artist, plays in kpop_artists:
        print(f"   - {artist} ({plays:,} plays)")
    print()
    
    # Generate full network
    analyzer = ArtistNetworkAnalyzer(config)
    
    print("🕸️  Generating full 100-artist network with bidirectional similarity...")
    print("   This will take several minutes...")
    
    start_time = datetime.now()
    network_data = analyzer.create_network_data(df)  # Uses config defaults
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    edges = network_data['edges']
    
    print(f"\n📊 Full Network Results:")
    print(f"   Generation time: {duration/60:.1f} minutes")
    print(f"   Nodes: {len(network_data['nodes'])}")
    print(f"   Edges: {len(edges)}")
    
    if edges:
        # Analyze edge types
        bidirectional_edges = [e for e in edges if 'bidirectional_data' in e]
        print(f"   Bidirectional edges: {len(bidirectional_edges)}")
        
        # Find K-pop connections
        kpop_names = [name.lower() for name, _ in kpop_artists]
        kpop_edges = []
        
        for edge in edges:
            source_is_kpop = any(kpop in edge['source'].lower() for kpop in ['ive', 'blackpink', 'twice', 'rosé', 'iu', 'newjeans', 'aespa', 'itzy'])
            target_is_kpop = any(kpop in edge['target'].lower() for kpop in ['ive', 'blackpink', 'twice', 'rosé', 'iu', 'newjeans', 'aespa', 'itzy'])
            
            if source_is_kpop or target_is_kpop:
                kpop_edges.append(edge)
        
        print(f"   K-pop related edges: {len(kpop_edges)}")
        
        # Show strongest relationships
        sorted_edges = sorted(edges, key=lambda x: x['weight'], reverse=True)
        print(f"\n🔗 Top 10 Strongest Relationships:")
        for i, edge in enumerate(sorted_edges[:10], 1):
            direction = edge.get('bidirectional_data', {}).get('max_direction', 'N/A')
            print(f"   {i:2d}. {edge['source']} ↔ {edge['target']}")
            print(f"       Similarity: {edge['weight']:.3f} (via {direction})")
        
        # Show K-pop specific connections
        if kpop_edges:
            print(f"\n🎌 K-pop Connections Found:")
            for i, edge in enumerate(kpop_edges, 1):
                direction = edge.get('bidirectional_data', {}).get('max_direction', 'N/A')
                print(f"   {i:2d}. {edge['source']} ↔ {edge['target']}")
                print(f"       Similarity: {edge['weight']:.3f} (via {direction})")
        
        # Save the network
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bidirectional_network_100artists_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Network saved: {filename}")
        print(f"✅ Bidirectional fix successful! Found {len(edges)} total relationships")
        
        return len(edges)
    else:
        print("❌ Still no edges found")
        return 0

if __name__ == "__main__":
    edge_count = test_full_bidirectional()
    print(f"\n🎉 Test completed! Network has {edge_count} edges.")