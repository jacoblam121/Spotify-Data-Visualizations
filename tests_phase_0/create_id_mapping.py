#!/usr/bin/env python3
"""
Phase 0.0.3: Create ID Mapping Tool
Practical tool to migrate current network data to stable ID system.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from network_utils import initialize_network_analyzer, prepare_dataframe_for_network_analysis
from data_processor import clean_and_filter_data
from config_loader import AppConfig
from id_migration_system import IDMigrationSystem

def create_enhanced_network_with_stable_ids(
    top_n_artists: int = 20,
    output_file: str = None,
    sizing_mode: str = 'adaptive'
) -> Dict:
    """
    Create network data with stable ID system applied.
    
    Args:
        top_n_artists: Number of artists to include
        output_file: Optional output file name
        sizing_mode: 'global', 'personal', or 'adaptive' sizing strategy
        
    Returns:
        Network data with stable IDs and visualization properties
    """
    print(f"🚀 Creating Enhanced Network with Stable IDs")
    print(f"Target: {top_n_artists} artists")
    print("=" * 60)
    
    try:
        # Load configuration and patch missing network config
        # Look for config file in parent directory if not found locally
        config_path = 'configurations.txt'
        if not os.path.exists(config_path):
            config_path = os.path.join('..', 'configurations.txt')
        
        config = AppConfig(config_path)
        
        def get_network_config():
            return {
                'node_sizing_strategy': 'hybrid_multiply',
                'listener_count_source': 'hybrid',
                'fetch_both_sources': True,
                'fallback_behavior': 'fallback'
            }
        
        config.get_network_visualization_config = get_network_config
        
        # Load user data
        print(f"📁 Loading user data...")
        df = clean_and_filter_data(config)
        
        if df is None or df.empty:
            print("❌ No data available")
            return {}
        
        print(f"✅ Loaded {len(df)} plays")
        
        # Prepare for network analysis
        df_network = prepare_dataframe_for_network_analysis(df)
        
        # Create network
        analyzer = initialize_network_analyzer()
        analyzer.config = config
        
        print(f"🕸️  Generating network...")
        network_data = analyzer.create_network_data(
            df_network,
            top_n_artists=top_n_artists,
            min_plays_threshold=5,
            min_similarity_threshold=0.1
        )
        
        if not network_data or not network_data.get('nodes'):
            print("❌ Failed to generate network data")
            return {}
        
        print(f"📊 Original network: {len(network_data['nodes'])} nodes, {len(network_data['edges'])} edges")
        
        # Apply ID migration
        print(f"🔄 Applying stable ID migration...")
        migration_system = IDMigrationSystem()
        migrated_data = migration_system.migrate_network_data(network_data)
        
        # Add visualization enhancements
        print(f"🎨 Adding D3.js visualization properties...")
        enhanced_data = add_d3js_visualization_properties(migrated_data, sizing_mode, config)
        
        # Save result
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"enhanced_network_stable_ids_{top_n_artists}artists_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Enhanced network saved: {output_file}")
        
        # Summary
        print(f"\\n📈 Final Results:")
        print(f"  Nodes: {len(enhanced_data['nodes'])}")
        print(f"  Edges: {len(enhanced_data['edges'])}")
        
        metadata = enhanced_data['metadata']
        if 'id_migration' in metadata:
            id_stats = metadata['id_migration']['id_types']
            print(f"  ID Types:")
            print(f"    Spotify: {id_stats['spotify']}")
            print(f"    MusicBrainz: {id_stats['musicbrainz']}")
            print(f"    Local hash: {id_stats['local_hash']}")
        
        # Show sample nodes
        print(f"\\n🎵 Sample Enhanced Nodes:")
        for i, node in enumerate(enhanced_data['nodes'][:3]):
            print(f"  {i+1}. {node['canonical_name']} ({node['id_type']})")
            print(f"     ID: {node['id']}")
            if 'viz' in node:
                print(f"     Size: {node['viz'].get('radius', 'N/A')} px")
                print(f"     Color: {node['viz'].get('color', 'N/A')}")
        
        return enhanced_data
        
    except Exception as e:
        print(f"❌ Failed to create enhanced network: {e}")
        import traceback
        traceback.print_exc()
        return {}

def add_d3js_visualization_properties(network_data: Dict, sizing_mode: str = 'adaptive', config=None) -> Dict:
    """
    Add D3.js-specific visualization properties to network data.
    
    Args:
        network_data: Network data with stable IDs
        
    Returns:
        Network data with visualization properties
    """
    from sizing_strategies import SizingStrategyFactory, calculate_context
    
    enhanced_data = network_data.copy()
    nodes = enhanced_data.get('nodes', [])
    
    if not nodes:
        return enhanced_data
    
    # Calculate context for sizing strategies
    context = calculate_context(nodes, config)
    
    # Create sizing strategy
    strategy = SizingStrategyFactory.create(sizing_mode)
    
    enhanced_nodes = []
    
    # Size constants
    MIN_RADIUS = 8
    MAX_RADIUS = 45
    
    # Broad genre categories with comprehensive mapping
    # Each genre family gets one distinctive color
    genre_mapping = {
        # Pop Family (Pink/Red tones) - Western pop music
        'pop': 'pop',
        'pop punk': 'pop',
        'teen pop': 'pop',
        'soft pop': 'pop',
        
        # Rock Family (Blue/Teal tones) - Western rock music
        'rock': 'rock',
        'alternative': 'rock',
        'alternative rock': 'rock',
        'punk': 'rock',
        'emo': 'rock',
        'pop rock': 'rock',
        
        # Indie Family (Cyan tones) - Independent/alternative music
        'indie': 'indie',
        'indie rock': 'indie',
        'indie pop': 'indie',
        'indie folk': 'indie',
        'indie electronic': 'indie',
        'alternative indie': 'indie',
        'indie alternative': 'indie',
        
        # Metal Family (Gray tones)
        'metal': 'metal',
        'alternative metal': 'metal',
        'metalcore': 'metal',
        'nu metal': 'metal',
        
        # Electronic Family (Green tones)
        'electronic': 'electronic',
        'edm': 'electronic',
        'house': 'electronic',
        'techno': 'electronic',
        'speedcore': 'electronic',
        'synthpop': 'electronic',
        'ambient': 'electronic',
        
        # Hip-Hop Family (Yellow/Orange tones)
        'hip hop': 'hip-hop',
        'rap': 'hip-hop',
        
        # R&B/Soul Family (Orange tones)
        'r&b': 'rnb',
        'rnb': 'rnb',
        'soul': 'rnb',
        
        # Country/Folk Family (Purple tones)
        'country': 'country',
        'folk': 'country',
        
        # Asian/Anime Family (Magenta tones) - East Asian music
        'k-pop': 'asian',
        'j-pop': 'asian', 
        'k-ballad': 'asian',
        'k-rap': 'asian',
        'j-rock': 'asian',
        'vocaloid': 'asian',  # Japanese virtual singer technology
        'korean': 'asian',
        'japanese': 'asian',
        'anime': 'asian',
        
        # Latin American Family (Coral tones) - Latin music
        'reggaeton': 'latin',
        'latin': 'latin',
        'spanish': 'latin',
        'bachata': 'latin',
        'salsa': 'latin',
        'merengue': 'latin',
        'cumbia': 'latin',
        'bossa nova': 'latin',
        'samba': 'latin',
        'tango': 'latin',
        'mariachi': 'latin',
        
        # OST/Soundtrack Family (Teal tones) - Film/Game/TV music
        'soundtrack': 'ost',
        'ost': 'ost',
        'game': 'ost',
        'movie': 'ost',
        'film': 'ost',
        'tv': 'ost',
        'video game': 'ost',
        'game soundtrack': 'ost',
        'movie soundtrack': 'ost',
        
        # Jazz/Classical Family (Brown tones)
        'jazz': 'jazz',
        'classical': 'jazz',
        
        # Misc/Vocal Tags (Light Pink)
        'female vocalists': 'misc',
        'new zealand': 'misc',
        'irish': 'misc',
        '80s': 'misc'
    }
    
    # Color palette for broad categories (13 distinct colors)
    genre_colors = {
        'pop': '#E91E63',        # Deep Pink
        'rock': '#2196F3',       # Blue  
        'indie': '#00BCD4',      # Cyan
        'metal': '#607D8B',      # Blue Gray
        'electronic': '#4CAF50', # Green
        'hip-hop': '#FF9800',    # Orange
        'rnb': '#FF5722',        # Deep Orange
        'country': '#9C27B0',    # Purple
        'asian': '#F06292',      # Light Pink
        'latin': '#FF7043',      # Coral
        'ost': '#26A69A',        # Teal
        'jazz': '#795548',       # Brown
        'misc': '#FFB6C1',       # Light Pink
        'default': '#90A4AE'     # Light Gray
    }
    
    for node in nodes:
        enhanced_node = node.copy()
        
        # Calculate sizing metrics using strategy pattern
        sizing_result = strategy.calculate(node, context)
        
        # Convert size_score to radius
        size_score = sizing_result['size_score']
        radius = MIN_RADIUS + (MAX_RADIUS - MIN_RADIUS) * size_score
        
        # Determine primary genre for coloring
        raw_genre = 'default'
        
        # Get genres from both sources
        spotify_genres = [g.lower() for g in (node.get('genres_spotify') or [])]
        lastfm_genres = [g.lower() for g in (node.get('genres_lastfm') or [])]
        
        # Prioritize Last.fm genres when they seem more accurate than Spotify
        asian_genres = ['j-pop', 'k-pop', 'j-rock', 'k-ballad', 'k-rap', 'japanese', 'korean', 'anime', 'vocaloid']
        electronic_genres = ['vocaloid', 'electronic', 'edm', 'house', 'techno', 'synthpop', 'ambient']
        
        # Check if Last.fm has more specific/accurate genres
        lastfm_has_asian = any(g in asian_genres for g in lastfm_genres)
        lastfm_has_electronic = any(g in electronic_genres for g in lastfm_genres)
        spotify_seems_wrong = any(g in ['reggaeton'] for g in spotify_genres) and (lastfm_has_asian or lastfm_has_electronic)
        
        # Choose genre source priority
        if spotify_seems_wrong or lastfm_has_asian:
            # Prefer Last.fm when Spotify seems wrong or Last.fm has Asian genres
            primary_genres = lastfm_genres + spotify_genres
        else:
            # Default: Spotify first, then Last.fm
            primary_genres = spotify_genres + lastfm_genres
        
        if primary_genres:
            # Genre priority rules for more accurate categorization
            
            # Asian music takes priority over generic Latin/Western tags
            asian_found = [g for g in primary_genres if g in asian_genres]
            if asian_found:
                raw_genre = asian_found[0]
            
            # Pop takes priority over country for crossover artists (Taylor Swift, etc.)
            elif 'pop' in primary_genres and 'country' in primary_genres:
                raw_genre = 'pop'
            
            # Default: take first genre
            else:
                raw_genre = primary_genres[0]
        
        # Map to broad genre category
        broad_genre = genre_mapping.get(raw_genre, 'default')
        color = genre_colors.get(broad_genre, genre_colors['default'])
        
        # Store both raw and mapped genre for reference
        primary_genre = broad_genre
        
        # Create image URL (use existing photo_url or placeholder)
        image_url = node.get('photo_url', '')
        if not image_url:
            # Create placeholder URL or use default
            image_url = f"/api/artist_image/{node['id']}"
        
        # Create visualization properties
        viz_properties = {
            'radius': round(radius, 1),
            'size_score': round(size_score, 3),
            'glow_intensity': round(sizing_result['glow_intensity'], 3),
            'color': color,
            'primary_genre': primary_genre,
            'image_url': image_url,
            'sizing_metric': sizing_result['sizing_metric'],
            'sizing_value': sizing_result['sizing_value'],
            'sizing_mode': sizing_mode
        }
        
        # Add strategy-specific metadata if available
        if 'personal_weight' in sizing_result:
            viz_properties['personal_weight'] = round(sizing_result['personal_weight'], 3)
            viz_properties['global_weight'] = round(sizing_result['global_weight'], 3)
        
        enhanced_node['viz'] = viz_properties
        enhanced_nodes.append(enhanced_node)
    
    enhanced_data['nodes'] = enhanced_nodes
    
    # Update metadata
    if 'metadata' not in enhanced_data:
        enhanced_data['metadata'] = {}
    
    enhanced_data['metadata']['visualization'] = {
        'enhanced_date': datetime.now().isoformat(),
        'size_range': {'min_radius': MIN_RADIUS, 'max_radius': MAX_RADIUS},
        'color_scheme': 'genre_based',
        'sizing_algorithm': 'spotify_emphasis_sqrt',
        'total_genres': len(set(n['viz']['primary_genre'] for n in enhanced_nodes))
    }
    
    return enhanced_data

def test_different_sizes():
    """Test network generation with different artist counts."""
    print(f"🧪 Testing Different Network Sizes")
    print("=" * 50)
    
    test_sizes = [5, 10, 20]
    results = {}
    
    for size in test_sizes:
        print(f"\\n📊 Testing {size} artists...")
        result = create_enhanced_network_with_stable_ids(
            top_n_artists=size,
            output_file=f"test_network_{size}artists.json"
        )
        
        if result:
            results[size] = {
                'nodes': len(result['nodes']),
                'edges': len(result['edges']),
                'file': f"test_network_{size}artists.json"
            }
            print(f"✅ {size} artists: {results[size]['nodes']} nodes, {results[size]['edges']} edges")
        else:
            print(f"❌ Failed to generate network for {size} artists")
    
    print(f"\\n📈 Test Summary:")
    for size, data in results.items():
        print(f"  {size} artists -> {data['file']}")
    
    return results

if __name__ == "__main__":
    # Test with different sizes
    test_results = test_different_sizes()
    
    if test_results:
        print(f"\\n🎉 Phase 0.0.3 completed successfully!")
        print(f"Enhanced network generation with stable IDs is ready.")
        print(f"\\nFiles generated:")
        for size, data in test_results.items():
            print(f"  - {data['file']}")
    else:
        print(f"\\n💥 Phase 0.0.3 failed - check configuration")