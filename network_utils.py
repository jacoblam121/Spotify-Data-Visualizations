"""
Network analysis utilities for artist similarity and co-listening analysis.
Creates artist networks based on both Last.fm similarity and user listening patterns.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, Counter
import json
import os
from config_loader import AppConfig
from lastfm_utils import LastfmAPI


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
        
        # Initialize Last.fm API if available
        self.lastfm_api = None
        if self.lastfm_config['enabled'] and self.lastfm_config['api_key']:
            self.lastfm_api = LastfmAPI(
                self.lastfm_config['api_key'],
                self.lastfm_config['api_secret'],
                self.lastfm_config['cache_dir']
            )
    
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
            
            # Get similar artists from Last.fm
            similar_artists = self.lastfm_api.get_similar_artists(
                artist_name=artist, 
                limit=limit_per_artist
            )
            
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
                          include_lastfm: bool = True,
                          include_colistening: bool = True,
                          min_plays_threshold: int = 5) -> Dict:
        """
        Create network data structure combining similarity and co-listening.
        
        Args:
            df: DataFrame with listening history
            top_n_artists: Number of top artists to include
            include_lastfm: Whether to include Last.fm similarities
            include_colistening: Whether to include co-listening scores
            min_plays_threshold: Minimum plays to include artist
            
        Returns:
            Network data dict with nodes and edges
        """
        print(f"Creating network data for top {top_n_artists} artists...")
        
        if df.empty or 'artist' not in df.columns:
            print("❌ No artist data available")
            return {'nodes': [], 'edges': [], 'metadata': {}}
        
        # Get top artists by play count
        artist_plays = df.groupby('artist').size().sort_values(ascending=False)
        
        # Filter by minimum threshold
        artist_plays_filtered = artist_plays[artist_plays >= min_plays_threshold]
        top_artists = artist_plays_filtered.head(top_n_artists)
        
        print(f"Selected {len(top_artists)} artists (min {min_plays_threshold} plays)")
        
        # Create nodes
        nodes = []
        for rank, (artist, play_count) in enumerate(top_artists.items(), 1):
            nodes.append({
                'id': artist,
                'name': artist,
                'play_count': int(play_count),
                'rank': rank,
                'size': play_count,  # For visualization sizing
                'in_library': True
            })
        
        # Create edges
        edges = []
        artist_list = list(top_artists.index)
        
        # Get Last.fm similarities
        lastfm_similarities = {}
        if include_lastfm and self.lastfm_api:
            lastfm_similarities = self.get_lastfm_similarity_matrix(artist_list)
        
        # Get co-listening scores
        colistening_scores = {}
        if include_colistening:
            colistening_scores = self.calculate_co_listening_scores(df)
        
        # Combine into edges
        all_pairs = set()
        all_pairs.update(lastfm_similarities.keys())
        all_pairs.update(colistening_scores.keys())
        
        for pair in all_pairs:
            artist1, artist2 = pair
            
            # Skip if either artist not in top list
            if artist1 not in artist_list or artist2 not in artist_list:
                continue
            
            # Get scores
            lastfm_score = lastfm_similarities.get(pair, 0.0)
            colistening_score = colistening_scores.get(pair, 0.0)
            
            # Combine scores (weighted average)
            combined_score = 0.0
            weight_sum = 0.0
            
            if lastfm_score > 0:
                combined_score += lastfm_score * 0.7  # Last.fm weight
                weight_sum += 0.7
            
            if colistening_score > 0:
                combined_score += colistening_score * 0.3  # Co-listening weight
                weight_sum += 0.3
            
            if weight_sum > 0:
                combined_score /= weight_sum
                
                # Only include significant relationships
                if combined_score > 0.1:  # Threshold for inclusion
                    edges.append({
                        'source': artist1,
                        'target': artist2,
                        'weight': combined_score,
                        'lastfm_similarity': lastfm_score,
                        'colistening_score': colistening_score,
                        'relationship_type': self._classify_relationship(lastfm_score, colistening_score)
                    })
        
        # Create metadata
        metadata = {
            'generated': datetime.now().isoformat(),
            'total_artists_in_data': len(artist_plays),
            'artists_included': len(nodes),
            'total_plays': len(df),
            'date_range': {
                'start': df.index.min().isoformat() if hasattr(df.index, 'min') else None,
                'end': df.index.max().isoformat() if hasattr(df.index, 'max') else None
            },
            'edge_types': {
                'lastfm_only': len([e for e in edges if e['relationship_type'] == 'lastfm_only']),
                'colistening_only': len([e for e in edges if e['relationship_type'] == 'colistening_only']),
                'both': len([e for e in edges if e['relationship_type'] == 'both'])
            },
            'parameters': {
                'top_n_artists': top_n_artists,
                'min_plays_threshold': min_plays_threshold,
                'include_lastfm': include_lastfm,
                'include_colistening': include_colistening
            }
        }
        
        network_data = {
            'nodes': nodes,
            'edges': edges,
            'metadata': metadata
        }
        
        print(f"✅ Network created: {len(nodes)} nodes, {len(edges)} edges")
        
        return network_data
    
    def _classify_relationship(self, lastfm_score: float, colistening_score: float) -> str:
        """Classify the type of relationship between artists."""
        has_lastfm = lastfm_score > 0.1
        has_colistening = colistening_score > 0.1
        
        if has_lastfm and has_colistening:
            return 'both'
        elif has_lastfm:
            return 'lastfm_only'
        elif has_colistening:
            return 'colistening_only'
        else:
            return 'weak'
    
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