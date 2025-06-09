"""
Manual testing interface for artist similarity network analysis.
Tests Last.fm similarity API and network creation for Twitch Atlas-style visualization.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pandas as pd
from datetime import datetime
from config_loader import AppConfig
from data_processor import clean_and_filter_data
from lastfm_utils import LastfmAPI


def test_menu():
    """Display test menu and handle user selection."""
    while True:
        print("\n" + "="*60)
        print("🕸️  ARTIST SIMILARITY NETWORK - MANUAL TESTING")
        print("="*60)
        print("Phase 2A: Last.fm Similarity-Based Network")
        print("✨ Enhanced K-pop name matching: ENABLED")
        print("\n📋 Available Tests:")
        print("1. Test your top artists extraction")
        print("2. Test Last.fm similarity API") 
        print("3. Test similarity with your artists")
        print("4. Build similarity network")
        print("5. Analyze network connections")
        print("6. Compare Spotify vs Last.fm artist lists")
        print("7. Test with different artist counts")
        print("8. Export network data")
        print("0. Exit")
        
        try:
            choice = input("\n🔍 Enter your choice (0-8): ").strip()
            
            if choice == '0':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                test_top_artists_extraction()
            elif choice == '2':
                test_lastfm_api_basic()
            elif choice == '3':
                test_similarity_with_your_artists()
            elif choice == '4':
                build_similarity_network()
            elif choice == '5':
                analyze_network_connections()
            elif choice == '6':
                compare_artist_sources()
            elif choice == '7':
                test_different_artist_counts()
            elif choice == '8':
                export_network_data()
            else:
                print("❌ Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def test_top_artists_extraction():
    """Test extracting top artists from your listening data."""
    print("\n🎵 Testing Top Artists Extraction")
    print("-" * 50)
    
    try:
        config = AppConfig('configurations.txt')
        original_source = config.get('DataSource', 'SOURCE', fallback='spotify')
        
        sources = ['spotify', 'lastfm']
        results = {}
        
        for source in sources:
            print(f"\n📊 Extracting from {source.upper()} data...")
            config.config['DataSource']['SOURCE'] = source
            
            df = clean_and_filter_data(config)
            
            if df is None or df.empty:
                print(f"❌ No {source} data available")
                results[source] = None
                continue
            
            # Get top artists
            artist_counts = df.groupby('artist').size().sort_values(ascending=False)
            top_20 = artist_counts.head(20)
            
            print(f"✅ {source.upper()}: {len(df)} plays, {len(artist_counts)} unique artists")
            print(f"📈 Top 10 artists:")
            
            # Get original names for display
            original_names = df.drop_duplicates('artist').set_index('artist')['original_artist'].to_dict()
            
            for i, (artist, plays) in enumerate(top_20.head(10).items(), 1):
                original_name = original_names.get(artist, artist)
                print(f"   {i:2d}. {original_name}: {plays} plays")
            
            results[source] = {
                'top_artists': top_20,
                'original_names': original_names,
                'total_plays': len(df)
            }
        
        # Compare results
        if results.get('spotify') and results.get('lastfm'):
            spotify_artists = set(results['spotify']['top_artists'].index)
            lastfm_artists = set(results['lastfm']['top_artists'].index)
            overlap = spotify_artists.intersection(lastfm_artists)
            
            print(f"\n🔗 Cross-source comparison:")
            print(f"   Artists in both sources: {len(overlap)}")
            print(f"   Spotify only: {len(spotify_artists - lastfm_artists)}")
            print(f"   Last.fm only: {len(lastfm_artists - spotify_artists)}")
        
        # Restore original source
        config.config['DataSource']['SOURCE'] = original_source
        
    except Exception as e:
        print(f"❌ Error extracting top artists: {e}")


def test_lastfm_api_basic():
    """Test basic Last.fm API functionality."""
    print("\n🌐 Testing Last.fm API Setup")
    print("-" * 50)
    
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        print("📋 Configuration check:")
        print(f"   Enabled: {lastfm_config.get('enabled', False)}")
        print(f"   API Key: {'✅ Set' if lastfm_config.get('api_key') else '❌ Missing'}")
        print(f"   Cache Dir: {lastfm_config.get('cache_dir', 'Default')}")
        
        if not lastfm_config.get('enabled') or not lastfm_config.get('api_key'):
            print("❌ Last.fm API not properly configured")
            return
        
        # Initialize API
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test with popular artists
        test_artists = ['Taylor Swift', 'Drake', 'Paramore', 'BTS']
        
        print(f"\n🧪 Testing API with {len(test_artists)} popular artists...")
        
        for i, artist in enumerate(test_artists, 1):
            print(f"\n{i}. Testing: {artist}")
            
            similar_artists = lastfm_api.get_similar_artists(artist, limit=8)
            
            if similar_artists:
                print(f"   ✅ Found {len(similar_artists)} similar artists:")
                for j, similar in enumerate(similar_artists[:5], 1):
                    print(f"      {j}. {similar['name']}: {similar['match']:.3f}")
            else:
                print(f"   ❌ No similar artists found")
        
        print("\n✅ Last.fm API test completed!")
        
    except Exception as e:
        print(f"❌ Error testing Last.fm API: {e}")


def test_similarity_with_your_artists():
    """Test Last.fm similarity with your actual top artists."""
    print("\n🎵 Testing Similarity with Your Artists")
    print("-" * 50)
    
    try:
        config = AppConfig('configurations.txt')
        
        # Get your top artists
        print("📊 Loading your top artists...")
        original_source = config.get('DataSource', 'SOURCE', fallback='spotify')
        config.config['DataSource']['SOURCE'] = 'spotify'  # Use Spotify as primary
        
        df = clean_and_filter_data(config)
        
        if df is None or df.empty:
            print("❌ No data available")
            return
        
        # Get top artists
        artist_counts = df.groupby('artist').size().sort_values(ascending=False)
        top_artists = artist_counts.head(10)  # Test with top 10
        original_names = df.drop_duplicates('artist').set_index('artist')['original_artist'].to_dict()
        
        print(f"✅ Testing similarity for your top {len(top_artists)} artists")
        print(f"✨ Using enhanced K-pop name matching (includes variants like 'IVE (아이브)')")
        
        # Initialize Last.fm API
        lastfm_config = config.get_lastfm_config()
        if not lastfm_config.get('enabled') or not lastfm_config.get('api_key'):
            print("❌ Last.fm API not configured")
            return
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test similarity for each artist
        similarity_results = {}
        cross_references = []
        
        for i, (artist_norm, plays) in enumerate(top_artists.items(), 1):
            original_name = original_names.get(artist_norm, artist_norm)
            print(f"\n{i:2d}. {original_name} ({plays} plays)")
            
            similar_artists = lastfm_api.get_similar_artists(original_name, limit=12)
            
            if similar_artists:
                print(f"     ✅ {len(similar_artists)} similar artists found:")
                
                # Show top 5
                for j, similar in enumerate(similar_artists[:5], 1):
                    print(f"        {j}. {similar['name']}: {similar['match']:.3f}")
                
                similarity_results[artist_norm] = {
                    'original_name': original_name,
                    'similar_artists': similar_artists,
                    'plays': plays
                }
                
                # Check for cross-references with other artists in your top list
                similar_names_lower = [s['name'].lower().strip() for s in similar_artists]
                for other_artist in top_artists.index:
                    if other_artist != artist_norm:
                        other_original = original_names.get(other_artist, other_artist).lower().strip()
                        if other_original in similar_names_lower:
                            score = next(s['match'] for s in similar_artists 
                                       if s['name'].lower().strip() == other_original)
                            cross_references.append((original_name, original_names.get(other_artist, other_artist), score))
            else:
                print(f"     ❌ No similar artists found")
        
        # Show cross-references
        if cross_references:
            print(f"\n🔗 Connections within your library ({len(cross_references)} found):")
            cross_references.sort(key=lambda x: x[2], reverse=True)
            for artist1, artist2, score in cross_references[:10]:
                print(f"   {artist1} ↔ {artist2}: {score:.3f}")
        else:
            print(f"\n⚠️  No direct connections found among your top {len(top_artists)} artists")
            print("   This suggests diverse taste across genres!")
        
        # Restore original source
        config.config['DataSource']['SOURCE'] = original_source
        
    except Exception as e:
        print(f"❌ Error testing similarity: {e}")
        import traceback
        traceback.print_exc()


def build_similarity_network():
    """Build a complete similarity network from your artists."""
    print("\n🕸️  Building Similarity Network")
    print("-" * 50)
    
    try:
        config = AppConfig('configurations.txt')
        
        # Get number of artists to include
        try:
            num_artists = int(input("How many top artists to include? (default 15): ").strip() or "15")
        except ValueError:
            num_artists = 15
        
        print(f"📊 Building network with top {num_artists} artists...")
        
        # Load data and get top artists
        original_source = config.get('DataSource', 'SOURCE', fallback='spotify')
        config.config['DataSource']['SOURCE'] = 'spotify'
        
        df = clean_and_filter_data(config)
        if df is None or df.empty:
            print("❌ No data available")
            return
        
        artist_counts = df.groupby('artist').size().sort_values(ascending=False)
        top_artists = artist_counts.head(num_artists)
        original_names = df.drop_duplicates('artist').set_index('artist')['original_artist'].to_dict()
        
        # Initialize Last.fm API
        lastfm_config = config.get_lastfm_config()
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Build similarity matrix
        print("🔄 Fetching similarity data...")
        network_data = {
            'nodes': [],
            'edges': [],
            'metadata': {
                'created': datetime.now().isoformat(),
                'artist_count': len(top_artists),
                'data_source': 'spotify',
                'similarity_source': 'lastfm'
            }
        }
        
        # Create nodes
        for rank, (artist_norm, plays) in enumerate(top_artists.items(), 1):
            original_name = original_names.get(artist_norm, artist_norm)
            network_data['nodes'].append({
                'id': artist_norm,
                'name': original_name,
                'play_count': int(plays),
                'rank': rank,
                'size': plays  # For visualization
            })
        
        # Create edges based on similarity
        artist_similarities = {}
        edges_found = 0
        
        for i, (artist_norm, plays) in enumerate(top_artists.items(), 1):
            original_name = original_names.get(artist_norm, artist_norm)
            print(f"  {i}/{len(top_artists)}: {original_name}")
            
            similar_artists = lastfm_api.get_similar_artists(original_name, limit=50)
            
            if similar_artists:
                artist_similarities[artist_norm] = similar_artists
                
                # Check for connections to other artists in our list
                for similar in similar_artists:
                    similar_name_lower = similar['name'].lower().strip()
                    
                    for other_artist_norm in top_artists.index:
                        if other_artist_norm != artist_norm:
                            other_original = original_names.get(other_artist_norm, other_artist_norm).lower().strip()
                            
                            if similar_name_lower == other_original:
                                # Found a connection!
                                network_data['edges'].append({
                                    'source': artist_norm,
                                    'target': other_artist_norm,
                                    'weight': similar['match'],
                                    'similarity_score': similar['match']
                                })
                                edges_found += 1
        
        print(f"\n✅ Network built successfully!")
        print(f"   Nodes (artists): {len(network_data['nodes'])}")
        print(f"   Edges (connections): {len(network_data['edges'])}")
        print(f"   Network density: {len(network_data['edges']) / (len(network_data['nodes']) * (len(network_data['nodes']) - 1) / 2):.3f}")
        
        # Show strongest connections
        if network_data['edges']:
            edges_by_weight = sorted(network_data['edges'], key=lambda x: x['weight'], reverse=True)
            print(f"\n🔗 Strongest connections:")
            for i, edge in enumerate(edges_by_weight[:10], 1):
                source_name = original_names.get(edge['source'], edge['source'])
                target_name = original_names.get(edge['target'], edge['target'])
                print(f"   {i:2d}. {source_name} ↔ {target_name}: {edge['weight']:.3f}")
        
        # Save network
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"similarity_network_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Network saved: {filename}")
        
        # Restore original source
        config.config['DataSource']['SOURCE'] = original_source
        
    except Exception as e:
        print(f"❌ Error building network: {e}")
        import traceback
        traceback.print_exc()


def analyze_network_connections():
    """Analyze existing network data files."""
    print("\n📊 Analyzing Network Connections")
    print("-" * 50)
    
    try:
        # Find network files
        import glob
        network_files = glob.glob("similarity_network_*.json")
        
        if not network_files:
            print("❌ No network files found")
            print("💡 Run 'Build similarity network' first")
            return
        
        # Use most recent file
        latest_file = max(network_files)
        print(f"📄 Analyzing: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            network_data = json.load(f)
        
        nodes = network_data['nodes']
        edges = network_data['edges']
        
        print(f"\n📈 Network Statistics:")
        print(f"   Artists: {len(nodes)}")
        print(f"   Connections: {len(edges)}")
        print(f"   Density: {len(edges) / (len(nodes) * (len(nodes) - 1) / 2):.3f}")
        
        # Analyze node degrees (number of connections)
        node_degrees = {}
        for node in nodes:
            node_degrees[node['id']] = 0
        
        for edge in edges:
            node_degrees[edge['source']] += 1
            node_degrees[edge['target']] += 1
        
        # Sort by degree
        sorted_degrees = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n🌟 Most connected artists:")
        node_names = {n['id']: n['name'] for n in nodes}
        
        for i, (artist_id, degree) in enumerate(sorted_degrees[:10], 1):
            artist_name = node_names.get(artist_id, artist_id)
            print(f"   {i:2d}. {artist_name}: {degree} connections")
        
        # Analyze edge weights
        if edges:
            weights = [e['weight'] for e in edges]
            print(f"\n🔗 Connection strength analysis:")
            print(f"   Average similarity: {sum(weights)/len(weights):.3f}")
            print(f"   Strongest connection: {max(weights):.3f}")
            print(f"   Weakest connection: {min(weights):.3f}")
        
    except Exception as e:
        print(f"❌ Error analyzing network: {e}")


def compare_artist_sources():
    """Compare artist lists between Spotify and Last.fm."""
    print("\n🔄 Comparing Artist Sources")
    print("-" * 50)
    
    try:
        config = AppConfig('configurations.txt')
        original_source = config.get('DataSource', 'SOURCE', fallback='spotify')
        
        sources_data = {}
        
        for source in ['spotify', 'lastfm']:
            print(f"\n📊 Loading {source.upper()} artists...")
            config.config['DataSource']['SOURCE'] = source
            
            df = clean_and_filter_data(config)
            
            if df is not None and not df.empty:
                artist_counts = df.groupby('artist').size().sort_values(ascending=False)
                original_names = df.drop_duplicates('artist').set_index('artist')['original_artist'].to_dict()
                
                sources_data[source] = {
                    'artists': artist_counts,
                    'names': original_names,
                    'total_plays': len(df)
                }
                
                print(f"   ✅ {len(artist_counts)} unique artists, {len(df)} total plays")
            else:
                print(f"   ❌ No {source} data available")
                sources_data[source] = None
        
        # Compare if both sources available
        if sources_data.get('spotify') and sources_data.get('lastfm'):
            spotify_artists = set(sources_data['spotify']['artists'].index)
            lastfm_artists = set(sources_data['lastfm']['artists'].index)
            
            overlap = spotify_artists.intersection(lastfm_artists)
            spotify_only = spotify_artists - lastfm_artists
            lastfm_only = lastfm_artists - spotify_artists
            
            print(f"\n🔗 Detailed comparison:")
            print(f"   Total unique artists across both: {len(spotify_artists.union(lastfm_artists))}")
            print(f"   In both sources: {len(overlap)} ({len(overlap)/len(spotify_artists.union(lastfm_artists))*100:.1f}%)")
            print(f"   Spotify only: {len(spotify_only)}")
            print(f"   Last.fm only: {len(lastfm_only)}")
            
            if len(overlap) > 0:
                print(f"\n📈 Top artists in both sources:")
                spotify_names = sources_data['spotify']['names']
                
                for i, artist in enumerate(list(overlap)[:10], 1):
                    spotify_plays = sources_data['spotify']['artists'][artist]
                    lastfm_plays = sources_data['lastfm']['artists'][artist]
                    name = spotify_names.get(artist, artist)
                    print(f"   {i:2d}. {name}: Spotify {spotify_plays}, Last.fm {lastfm_plays}")
        
        # Restore original source
        config.config['DataSource']['SOURCE'] = original_source
        
    except Exception as e:
        print(f"❌ Error comparing sources: {e}")


def test_different_artist_counts():
    """Test network building with different numbers of artists."""
    print("\n🔢 Testing Different Artist Counts")
    print("-" * 50)
    
    try:
        config = AppConfig('configurations.txt')
        
        # Test different sizes
        test_sizes = [5, 10, 15, 20]
        
        print("🧪 Testing network density with different artist counts...")
        
        for size in test_sizes:
            print(f"\n📊 Testing with {size} artists:")
            
            # This would build a network but just report stats
            print(f"   Theoretical max edges: {size * (size - 1) // 2}")
            print(f"   Expected edges (assuming 10% connection rate): ~{size * (size - 1) // 2 * 0.1:.0f}")
        
        print(f"\n💡 Recommendation:")
        print(f"   • 5-10 artists: Good for testing, may lack connections")
        print(f"   • 15-20 artists: Balanced for visualization")
        print(f"   • 25+ artists: Rich network, may be cluttered")
        
    except Exception as e:
        print(f"❌ Error testing artist counts: {e}")


def export_network_data():
    """Export network data in different formats."""
    print("\n💾 Exporting Network Data")
    print("-" * 50)
    
    try:
        import glob
        network_files = glob.glob("similarity_network_*.json")
        
        if not network_files:
            print("❌ No network files found")
            return
        
        latest_file = max(network_files)
        print(f"📄 Exporting from: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            network_data = json.load(f)
        
        # Export as CSV for external tools
        nodes_df = pd.DataFrame(network_data['nodes'])
        edges_df = pd.DataFrame(network_data['edges'])
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        nodes_file = f"network_nodes_{timestamp}.csv"
        edges_file = f"network_edges_{timestamp}.csv"
        
        nodes_df.to_csv(nodes_file, index=False)
        edges_df.to_csv(edges_file, index=False)
        
        print(f"✅ Exported:")
        print(f"   Nodes: {nodes_file}")
        print(f"   Edges: {edges_file}")
        print(f"   Original JSON: {latest_file}")
        
    except Exception as e:
        print(f"❌ Error exporting: {e}")


if __name__ == "__main__":
    # Change to main directory for proper file access
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        test_menu()
    finally:
        # Restore original directory
        os.chdir(original_dir)