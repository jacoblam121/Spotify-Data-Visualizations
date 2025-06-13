"""
Network analysis utilities for artist similarity and co-listening analysis.
Creates artist networks based on Last.fm similarity data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, Counter
import json
import os
import networkx as nx
from dotenv import load_dotenv
from config_loader import AppConfig
from lastfm_utils import LastfmAPI
from artist_data_fetcher import EnhancedArtistDataFetcher

# Load environment variables
load_dotenv()


def prepare_dataframe_for_network_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare DataFrame for network analysis by setting timestamp as index.
    
    This wrapper function fixes the datetime index issue without modifying
    the core data_processor.py module.
    
    Args:
        df: DataFrame from clean_and_filter_data() with timestamp column
        
    Returns:
        DataFrame with timestamp as DatetimeIndex, ready for network analysis
        
    Raises:
        ValueError: If DataFrame is missing required columns
    """
    if df is None or df.empty:
        raise ValueError("DataFrame is None or empty")
    
    if 'timestamp' not in df.columns:
        raise ValueError("DataFrame missing 'timestamp' column")
    
    if 'artist' not in df.columns:
        raise ValueError("DataFrame missing 'artist' column")
    
    # Create a copy to avoid modifying the original
    df_network = df.copy()
    
    # Set timestamp as index
    df_network.set_index('timestamp', inplace=True)
    
    # Verify the conversion worked
    if not isinstance(df_network.index, pd.DatetimeIndex):
        raise ValueError("Failed to convert timestamp to DatetimeIndex")
    
    return df_network


class ArtistNetworkAnalyzer:
    """Analyzes artist networks from listening history and similarity data."""
    
    def __init__(self, config: AppConfig):
        """Initialize the analyzer with configuration."""
        self.config = config
        self.lastfm_config = config.get_lastfm_config()
        self.network_config = config.get_network_visualization_config()
        
        # Initialize Last.fm API if available
        self.lastfm_api = None
        if self.lastfm_config['enabled'] and self.lastfm_config['api_key']:
            self.lastfm_api = LastfmAPI(
                self.lastfm_config['api_key'],
                self.lastfm_config['api_secret'],
                self.lastfm_config['cache_dir']
            )
        
        # Initialize enhanced artist data fetcher
        self.artist_fetcher = EnhancedArtistDataFetcher(config)
    
    def calculate_co_listening_scores(self, df: pd.DataFrame, 
                                    time_window_hours: int = 24,
                                    min_co_occurrences: int = 2) -> Dict[Tuple[str, str], float]:
        """
        Calculate co-listening scores between artists based on temporal proximity.
        
        Args:
            df: DataFrame with datetime index and 'artist' column
            time_window_hours: Hours within which plays count as co-listening
            min_co_occurrences: Minimum co-occurrences to include pair
            
        Returns:
            Dict mapping (artist1, artist2) tuples to co-listening scores (0-1)
        """
        print(f"Calculating co-listening scores (window: {time_window_hours}h)...")
        
        if df.empty or 'artist' not in df.columns:
            print("❌ No artist data available for co-listening analysis")
            return {}
        
        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            print("❌ DataFrame must have datetime index")
            return {}
        
        # Sort by time
        df_sorted = df.sort_index()
        
        # Track co-listening sessions
        co_listening_pairs = defaultdict(int)
        artist_play_counts = Counter(df_sorted['artist'])
        
        # Define time window
        time_window = timedelta(hours=time_window_hours)
        
        print(f"Processing {len(df_sorted)} plays...")
        
        # For each play, find other plays within time window
        for i, (timestamp, row) in enumerate(df_sorted.iterrows()):
            current_artist = row['artist']
            
            # Look backwards and forwards within time window
            window_start = timestamp - time_window
            window_end = timestamp + time_window
            
            # Get plays in window (excluding current play)
            window_plays = df_sorted[
                (df_sorted.index >= window_start) & 
                (df_sorted.index <= window_end) &
                (df_sorted.index != timestamp)
            ]
            
            # Count co-listening with different artists
            for _, window_row in window_plays.iterrows():
                other_artist = window_row['artist']
                
                if other_artist != current_artist:
                    # Create sorted tuple for consistent key
                    pair = tuple(sorted([current_artist, other_artist]))
                    co_listening_pairs[pair] += 1
            
            # Progress indicator
            if (i + 1) % 1000 == 0:
                print(f"  Processed {i + 1}/{len(df_sorted)} plays...")
        
        print(f"Found {len(co_listening_pairs)} artist pairs with co-listening")
        
        # Calculate normalized scores
        co_listening_scores = {}
        
        for (artist1, artist2), co_count in co_listening_pairs.items():
            if co_count >= min_co_occurrences:
                # Normalize by geometric mean of individual play counts
                artist1_plays = artist_play_counts[artist1]
                artist2_plays = artist_play_counts[artist2]
                
                # Jaccard-like coefficient
                max_possible = min(artist1_plays, artist2_plays)
                score = co_count / max_possible if max_possible > 0 else 0
                
                # Cap at 1.0
                score = min(score, 1.0)
                
                co_listening_scores[(artist1, artist2)] = score
        
        print(f"✅ Calculated scores for {len(co_listening_scores)} valid pairs")
        return co_listening_scores
    
    def get_lastfm_similarity_matrix(self, artists: List[str], 
                                   limit_per_artist: int = 100) -> Dict[Tuple[str, str], float]:
        """
        Get Last.fm similarity scores between artists.
        
        Args:
            artists: List of artist names
            limit_per_artist: Max similar artists to fetch per artist
            
        Returns:
            Dict mapping (artist1, artist2) tuples to similarity scores (0-1)
        """
        if not self.lastfm_api:
            print("❌ Last.fm API not available")
            return {}
        
        print(f"Fetching Last.fm similarities for {len(artists)} artists...")
        
        similarity_scores = {}
        
        for i, artist in enumerate(artists, 1):
            print(f"  {i}/{len(artists)}: {artist}")
            
            try:
                # Get similar artists from Last.fm
                similar_artists = self.lastfm_api.get_similar_artists(
                    artist_name=artist, 
                    limit=limit_per_artist
                )
            except Exception as e:
                print(f"    Error getting similar artists for {artist}: {e}")
                similar_artists = []
            
            # Add similarities to matrix
            for similar in similar_artists:
                similar_name = similar['name']
                score = similar['match']
                
                # Only include if similar artist is in our list
                if similar_name in artists:
                    pair = tuple(sorted([artist, similar_name]))
                    
                    # Keep highest score if duplicate
                    if pair not in similarity_scores or score > similarity_scores[pair]:
                        similarity_scores[pair] = score
        
        print(f"✅ Found {len(similarity_scores)} Last.fm similarity relationships")
        return similarity_scores
    
    def create_network_data(self, df: pd.DataFrame, 
                          top_n_artists: int = 50,
                          min_plays_threshold: int = 5,
                          min_similarity_threshold: float = 0.1) -> Dict:
        """
        Create network data structure with enhanced artist data (Last.fm + Spotify).
        
        Args:
            df: DataFrame with listening history
            top_n_artists: Number of top artists to include
            min_plays_threshold: Minimum plays to include artist
            min_similarity_threshold: Minimum Last.fm similarity to include edge
            
        Returns:
            Network data dict with nodes and edges
        """
        print(f"Creating enhanced network data for top {top_n_artists} artists...")
        print(f"Using {self.network_config['node_sizing_strategy']} as node sizing strategy")
        
        if df.empty or 'artist' not in df.columns:
            print("❌ No artist data available")
            return {'nodes': [], 'edges': [], 'metadata': {}}
        
        # Get top artists by play count
        artist_plays = df.groupby('artist').size().sort_values(ascending=False)
        
        # Filter by minimum threshold
        artist_plays_filtered = artist_plays[artist_plays >= min_plays_threshold]
        top_artists = artist_plays_filtered.head(top_n_artists)
        
        print(f"Selected {len(top_artists)} artists (min {min_plays_threshold} plays)")
        
        # Fetch enhanced artist data
        print(f"🔍 Fetching enhanced artist data from APIs...")
        artist_list = list(top_artists.index)
        
        def progress_callback(current, total, artist_name):
            if current % 5 == 0 or current == total:
                print(f"  {current}/{total}: {artist_name}")
        
        enhanced_data = self.artist_fetcher.batch_fetch_artist_data(
            artist_list, 
            include_similar=True,
            progress_callback=progress_callback
        )
        
        # Create nodes with enhanced data
        nodes = []
        artist_data_map = {}  # For edge creation
        
        successful_artists = 0
        for i, (artist, play_count) in enumerate(top_artists.items()):
            rank = i + 1
            enhanced = enhanced_data[i]
            artist_data_map[artist] = enhanced
            
            if enhanced['success']:
                successful_artists += 1
                
                # Use configured listener count source
                listener_count = enhanced['primary_listener_count']
                listener_source = enhanced['primary_source']
                
                node = {
                    'id': artist,
                    'name': enhanced['canonical_name'],
                    'play_count': int(play_count),
                    'rank': rank,
                    'size': listener_count,  # Primary listener count for sizing
                    'listener_count': listener_count,
                    'listener_source': listener_source,
                    'in_library': True
                }
                
                # Add additional data sources if available
                if enhanced['lastfm_data']:
                    node['lastfm_listeners'] = enhanced['lastfm_data']['listeners']
                    node['lastfm_playcount'] = enhanced['lastfm_data']['playcount']
                    node['lastfm_url'] = enhanced['lastfm_data']['url']
                    node['genres_lastfm'] = [tag['name'] for tag in enhanced['lastfm_data']['tags'][:3]]
                
                if enhanced['spotify_data']:
                    node['spotify_followers'] = enhanced['spotify_data']['followers']
                    node['spotify_popularity'] = enhanced['spotify_data']['popularity']
                    node['spotify_id'] = enhanced['spotify_data']['spotify_artist_id']
                    node['photo_url'] = enhanced['spotify_data']['photo_url']
                    node['genres_spotify'] = enhanced['spotify_data']['genres'][:3]
                
                nodes.append(node)
            else:
                # Handle failed artists based on fallback behavior
                fallback_behavior = self.network_config['fallback_behavior']
                if fallback_behavior != 'skip':
                    node = {
                        'id': artist,
                        'name': artist,
                        'play_count': int(play_count),
                        'rank': rank,
                        'size': int(play_count),  # Use play count as fallback
                        'listener_count': 0,
                        'listener_source': 'play_count_fallback',
                        'in_library': True
                    }
                    nodes.append(node)
        
        print(f"✅ Successfully fetched data for {successful_artists}/{len(artist_list)} artists")
        
        # Create edges from similarity data
        edges = []
        edges_created = 0
        
        print(f"🕸️  Creating similarity edges...")
        for enhanced in enhanced_data:
            if enhanced['similar_artists']:
                source_artist = enhanced['artist_name']
                similar_artists = enhanced['similar_artists']
                
                for similar in similar_artists:
                    target_artist = similar['name']
                    similarity_score = similar['match']
                    
                    # Only include if target artist is in our network and meets threshold
                    if (target_artist in artist_list and 
                        similarity_score >= min_similarity_threshold and
                        source_artist != target_artist):
                        
                        # Create sorted pair to avoid duplicates
                        pair = tuple(sorted([source_artist, target_artist]))
                        
                        # Check if edge already exists
                        existing_edge = None
                        for edge in edges:
                            edge_pair = tuple(sorted([edge['source'], edge['target']]))
                            if edge_pair == pair:
                                existing_edge = edge
                                break
                        
                        if not existing_edge:
                            edges.append({
                                'source': source_artist,
                                'target': target_artist,
                                'weight': similarity_score,
                                'lastfm_similarity': similarity_score,
                                'relationship_type': 'lastfm_similarity'
                            })
                            edges_created += 1
        
        print(f"✅ Created {edges_created} similarity edges")
        
        # Create metadata
        metadata = {
            'generated': datetime.now().isoformat(),
            'total_artists_in_data': len(artist_plays),
            'artists_included': len(nodes),
            'artists_with_api_data': successful_artists,
            'total_plays': len(df),
            'date_range': {
                'start': df.index.min().isoformat() if hasattr(df.index, 'min') else None,
                'end': df.index.max().isoformat() if hasattr(df.index, 'max') else None
            },
            'edge_types': {
                'lastfm_similarity': len(edges)
            },
            'configuration': {
                'listener_count_source': self.network_config.get('listener_count_source', 'hybrid'),
                'fetch_both_sources': self.network_config.get('fetch_both_sources', True),
                'fallback_behavior': self.network_config.get('fallback_behavior', 'fallback'),
                'node_sizing_strategy': self.network_config.get('node_sizing_strategy', 'hybrid_multiply')
            },
            'parameters': {
                'top_n_artists': top_n_artists,
                'min_plays_threshold': min_plays_threshold,
                'min_similarity_threshold': min_similarity_threshold,
                'data_source': 'enhanced_multi_api'
            }
        }
        
        network_data = {
            'nodes': nodes,
            'edges': edges,
            'metadata': metadata
        }
        
        print(f"✅ Enhanced network created: {len(nodes)} nodes, {len(edges)} edges")
        
        return network_data
    
    
    def save_network_data(self, network_data: Dict, filename: str = 'artist_network.json') -> str:
        """Save network data to JSON file."""
        filepath = os.path.abspath(filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Network data saved: {filepath}")
        return filepath
    
    def get_network_statistics(self, network_data: Dict) -> Dict:
        """Calculate network statistics."""
        nodes = network_data['nodes']
        edges = network_data['edges']
        
        if not nodes:
            return {}
        
        # Basic stats
        stats = {
            'node_count': len(nodes),
            'edge_count': len(edges),
            'density': len(edges) / (len(nodes) * (len(nodes) - 1) / 2) if len(nodes) > 1 else 0,
            'avg_degree': 2 * len(edges) / len(nodes) if nodes else 0
        }
        
        # Degree distribution
        degree_counts = defaultdict(int)
        for node in nodes:
            node_id = node['id']
            degree = len([e for e in edges if e['source'] == node_id or e['target'] == node_id])
            degree_counts[degree] += 1
        
        stats['degree_distribution'] = dict(degree_counts)
        
        # Weight distribution
        if edges:
            weights = [e['weight'] for e in edges]
            stats['weight_stats'] = {
                'min': min(weights),
                'max': max(weights),
                'mean': sum(weights) / len(weights),
                'median': sorted(weights)[len(weights) // 2]
            }
        
        return stats


def initialize_network_analyzer(config_file: str = 'configurations.txt') -> ArtistNetworkAnalyzer:
    """Initialize network analyzer with configuration."""
    config = AppConfig(config_file)
    return ArtistNetworkAnalyzer(config)


def analyze_user_network(df: pd.DataFrame, config_file: str = 'configurations.txt', 
                        output_file: str = 'artist_network.json') -> Dict:
    """
    Convenience function to analyze user's artist network.
    
    Args:
        df: DataFrame with listening history
        config_file: Path to configuration file
        output_file: Output JSON file for network data
        
    Returns:
        Network data dictionary
    """
    analyzer = initialize_network_analyzer(config_file)
    network_data = analyzer.create_network_data(df)
    
    if output_file:
        analyzer.save_network_data(network_data, output_file)
    
    return network_data