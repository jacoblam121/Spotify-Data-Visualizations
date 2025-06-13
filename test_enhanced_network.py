#!/usr/bin/env python3
"""
Test Enhanced Network Creation
Tests the new dual-API network creation with configurable listener sources.
"""

import json
from network_utils import prepare_dataframe_for_network_analysis, ArtistNetworkAnalyzer
from data_processor import clean_and_filter_data
from config_loader import AppConfig

def test_enhanced_network():
    """Test the enhanced network creation with dual API sources."""
    print("🚀 Testing Enhanced Network Creation")
    print("=" * 60)
    
    # Load configuration
    config = AppConfig('configurations.txt')
    network_config = config.get_network_visualization_config()
    
    print(f"📊 Configuration:")
    print(f"  Primary source: {network_config['listener_count_source']}")
    print(f"  Fetch both sources: {network_config['fetch_both_sources']}")
    print(f"  Fallback behavior: {network_config['fallback_behavior']}")
    
    try:
        # Load user data
        print(f"\n📁 Loading user data...")
        df = clean_and_filter_data(config)
        
        if df is None or df.empty:
            print("❌ No data loaded")
            return False
        
        print(f"✅ Loaded {len(df)} plays")
        
        # Prepare for network analysis
        df_network = prepare_dataframe_for_network_analysis(df)
        
        # Initialize analyzer
        analyzer = ArtistNetworkAnalyzer(config)
        
        # Create enhanced network with small dataset for testing
        print(f"\n🕸️  Creating enhanced network...")
        network_data = analyzer.create_network_data(
            df_network,
            top_n_artists=10,  # Small for testing
            min_plays_threshold=3,
            min_similarity_threshold=0.1
        )
        
        if not network_data or not network_data.get('nodes'):
            print("❌ No network data created")
            return False
        
        # Analyze results
        nodes = network_data['nodes']
        edges = network_data['edges']
        metadata = network_data['metadata']
        
        print(f"\n📊 Network Results:")
        print(f"  Nodes: {len(nodes)}")
        print(f"  Edges: {len(edges)}")
        print(f"  Artists with API data: {metadata.get('artists_with_api_data', 0)}/{metadata.get('artists_included', 0)}")
        
        # Show sample nodes with their data sources
        print(f"\n🎵 Sample Artist Data:")
        for i, node in enumerate(nodes[:5]):
            print(f"  {i+1}. {node['name']}")
            print(f"     Primary: {node.get('listener_count', 0):,} {node.get('listener_source', 'unknown')}")
            
            if 'lastfm_listeners' in node:
                print(f"     Last.fm: {node['lastfm_listeners']:,} listeners")
            
            if 'spotify_followers' in node:
                print(f"     Spotify: {node['spotify_followers']:,} followers")
            else:
                print(f"     Spotify: Not available")
            
            if 'photo_url' in node and node['photo_url']:
                print(f"     Photo: Available")
            
            print()
        
        # Show listener count comparison if both sources available
        dual_source_nodes = [n for n in nodes if 'lastfm_listeners' in n and 'spotify_followers' in n and n['spotify_followers'] > 0]
        
        if dual_source_nodes:
            print(f"📈 Listener Count Comparison ({len(dual_source_nodes)} artists with both sources):")
            
            for node in dual_source_nodes[:3]:
                lastfm_count = node['lastfm_listeners']
                spotify_count = node['spotify_followers']
                ratio = spotify_count / lastfm_count if lastfm_count > 0 else 0
                
                print(f"  {node['name']}:")
                print(f"    Last.fm: {lastfm_count:,} listeners")
                print(f"    Spotify: {spotify_count:,} followers") 
                print(f"    Ratio: {ratio:.1f}x (Spotify/Last.fm)")
        
        # Save enhanced network data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_network_test_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Enhanced network saved: {filename}")
        print(f"✅ Test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_configuration_switching():
    """Test switching between different listener count sources."""
    print("\n🔄 Testing Configuration Switching")
    print("=" * 50)
    
    # Test both configurations
    configs_to_test = [
        {'source': 'lastfm', 'description': 'Last.fm listeners'},
        {'source': 'spotify', 'description': 'Spotify followers'}
    ]
    
    from config_loader import AppConfig
    
    for config_test in configs_to_test:
        print(f"\n📊 Testing with {config_test['description']}...")
        
        # Temporarily modify configuration (in memory only)
        config = AppConfig('configurations.txt')
        
        # Override the network config
        original_get_network_config = config.get_network_visualization_config
        def mock_network_config():
            return {
                'listener_count_source': config_test['source'],
                'fetch_both_sources': True,
                'fallback_behavior': 'fallback'
            }
        config.get_network_visualization_config = mock_network_config
        
        try:
            analyzer = ArtistNetworkAnalyzer(config)
            print(f"  ✅ Analyzer initialized with {config_test['source']} as primary source")
            print(f"  🔍 Primary source: {analyzer.network_config['listener_count_source']}")
            
        except Exception as e:
            print(f"  ❌ Failed to initialize with {config_test['source']}: {e}")
        
        # Restore original method
        config.get_network_visualization_config = original_get_network_config

if __name__ == "__main__":
    from datetime import datetime
    
    success = test_enhanced_network()
    test_configuration_switching()
    
    if success:
        print(f"\n🎉 All tests passed! Enhanced network creation is ready.")
    else:
        print(f"\n❌ Some tests failed. Check the issues above.")