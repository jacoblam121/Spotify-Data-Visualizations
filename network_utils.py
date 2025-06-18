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
from itertools import combinations
from config_loader import AppConfig
from lastfm_utils import LastfmAPI
from artist_data_fetcher import EnhancedArtistDataFetcher
from ultimate_similarity_system import UltimateSimilaritySystem
from comprehensive_edge_weighting_system import ComprehensiveEdgeWeighter, EdgeWeightingConfig
from cache_manager import cache_result

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
        
        # Initialize Last.fm API if available (for legacy methods)
        self.lastfm_api = None
        if self.lastfm_config['enabled'] and self.lastfm_config['api_key']:
            self.lastfm_api = LastfmAPI(
                self.lastfm_config['api_key'],
                self.lastfm_config['api_secret'],
                self.lastfm_config['cache_dir']
            )
        
        # Initialize enhanced artist data fetcher
        self.artist_fetcher = EnhancedArtistDataFetcher(config)
        
        # Initialize Ultimate Similarity System (combines all APIs)
        self.ultimate_similarity = UltimateSimilaritySystem(config)
        
        # Initialize Comprehensive Edge Weighter
        edge_config = EdgeWeightingConfig()
        self.edge_weighter = ComprehensiveEdgeWeighter(edge_config)
        
        print(f"🌟 Enhanced Network Analyzer initialized:")
        print(f"   ✅ Ultimate Similarity System (Last.fm + Deezer + MusicBrainz)")
        print(f"   ✅ Comprehensive Edge Weighter with multi-source fusion")
        print(f"   ✅ Genre classification pipeline")
        print(f"   ✅ All-pairs comparison enabled")
    
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
    
    def _find_matching_artist(self, target_artist: str, artist_list: List[str]) -> Optional[str]:
        """
        Find a matching artist from the list using fuzzy matching.
        
        Args:
            target_artist: Artist name from Last.fm similar artists
            artist_list: List of artist names from our data
            
        Returns:
            Matched artist name from the list, or None if no match
        """
        target_lower = target_artist.lower().strip()
        
        # Exact match first
        for artist in artist_list:
            if artist.lower().strip() == target_lower:
                return artist
        
        # Fuzzy matching for common variations
        for artist in artist_list:
            artist_lower = artist.lower().strip()
            
            # Check if either contains the other (handles case differences)
            if target_lower in artist_lower or artist_lower in target_lower:
                return artist
            
            # Check for common K-pop name patterns
            if self._is_kpop_name_match(target_artist, artist):
                return artist
        
        return None
    
    def _is_kpop_name_match(self, name1: str, name2: str) -> bool:
        """Check if two names refer to the same K-pop artist."""
        name1_clean = name1.lower().strip()
        name2_clean = name2.lower().strip()
        
        # Handle BOL4/Bolbbalgan4 variations
        bol4_variants = {'bol4', 'bolbbalgan4', 'bolbbalgan4 (볼빨간사춘기)', '볼빨간사춘기'}
        if any(variant in name1_clean for variant in bol4_variants) and \
           any(variant in name2_clean for variant in bol4_variants):
            return True
        
        # Handle IU variations  
        iu_variants = {'iu', '아이유', 'iu (아이유)', 'iu(아이유)'}
        if any(variant in name1_clean for variant in iu_variants) and \
           any(variant in name2_clean for variant in iu_variants):
            return True
        
        # Handle other common K-pop variations
        kpop_patterns = [
            (['twice', '트와이스', 'twice (트와이스)'], ['twice', '트와이스', 'twice (트와이스)']),
            (['blackpink', '블랙핑크', 'blackpink (블랙핑크)'], ['blackpink', '블랙핑크', 'blackpink (블랙핑크)']),
            (['ive', 'ive (아이브)', '아이브'], ['ive', 'ive (아이브)', '아이브']),
        ]
        
        for pattern1, pattern2 in kpop_patterns:
            if any(variant in name1_clean for variant in pattern1) and \
               any(variant in name2_clean for variant in pattern2):
                return True
        
        return False
    
    def classify_artist_genre(self, enhanced_data: Dict) -> Tuple[str, List[str]]:
        """
        Classify artist into primary genre using simplified 12-genre system.
        
        Args:
            enhanced_data: Enhanced artist data from artist_fetcher
            
        Returns:
            Tuple of (primary_genre, all_genres_list)
        """
        # Import the working simplified classification system
        from simplified_genre_colors import classify_artist_genre, get_multi_genres
        
        # Use the working simplified classification system
        primary_genre = classify_artist_genre(enhanced_data)
        
        # Check configuration for secondary genres
        if self.network_config.get('enable_secondary_genres', True):
            # Rich multi-genre approach for complex visualizations
            all_genres = get_multi_genres(enhanced_data, max_genres=5)
        else:
            # Clean single-genre approach - only return primary genre
            all_genres = [primary_genre] if primary_genre != 'other' else []
        
        return primary_genre, all_genres
    
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
    
    def get_comprehensive_similarity_matrix(self, artists: List[str], 
                                          min_threshold: float = 0.1) -> Dict:
        """
        Get comprehensive similarity matrix using all available APIs and all-pairs comparison.
        
        Args:
            artists: List of artist names
            min_threshold: Minimum similarity threshold
            
        Returns:
            Dict with comprehensive similarity data for all artist pairs
        """
        print(f"🌟 Building comprehensive similarity matrix for {len(artists)} artists...")
        print(f"   📊 Total possible pairs: {len(artists) * (len(artists) - 1) // 2}")
        print(f"   🎯 Using Ultimate Similarity System (Last.fm + Deezer + MusicBrainz)")
        
        # Store all similarity data for edge weighting
        all_similarities = {}
        
        # Progress tracking
        total_pairs = len(artists) * (len(artists) - 1) // 2
        processed_pairs = 0
        
        # Get similarities for each artist using Ultimate Similarity System
        for i, artist in enumerate(artists):
            print(f"   🎵 [{i+1}/{len(artists)}] Processing {artist}...")
            
            try:
                # Get comprehensive similarities for this artist
                similarities = self.ultimate_similarity.get_ultimate_similar_artists(
                    artist_name=artist,
                    limit=len(artists),  # Get all possible similarities
                    min_threshold=min_threshold
                )
                
                # Store similarity data organized by target artist
                if artist not in all_similarities:
                    all_similarities[artist] = {}
                
                for similar in similarities:
                    target_artist = similar['name']
                    
                    # Include all valid similarity targets (not just those in our original artist list)
                    if target_artist != artist:
                        if target_artist not in all_similarities[artist]:
                            all_similarities[artist][target_artist] = []
                        
                        # Add this similarity data
                        all_similarities[artist][target_artist].append(similar)
                        processed_pairs += 1
                
                # Progress update
                if (i + 1) % 10 == 0:
                    print(f"      📈 Processed {processed_pairs} similarity relationships so far...")
                    
            except Exception as e:
                print(f"      ❌ Error processing {artist}: {e}")
                continue
        
        print(f"✅ Comprehensive similarity matrix complete:")
        print(f"   📊 Processed {processed_pairs} total relationships")
        print(f"   🎯 Found similarities for {len(all_similarities)} artists")
        
        return all_similarities
    
    def _create_data_hash(self, df: pd.DataFrame) -> str:
        """Create a hash of the DataFrame for caching purposes."""
        import hashlib
        
        # Create a hash from artist play counts (the core data for network generation)
        artist_plays = df.groupby('artist').size().sort_values(ascending=False)
        
        # Convert to string and hash
        data_string = str(sorted(artist_plays.items()))
        return hashlib.md5(data_string.encode()).hexdigest()[:16]
    
    @cache_result
    def _create_network_data_cached(self, data_hash: str, artist_list: list, 
                                   top_n_artists: int, min_plays_threshold: int,
                                   min_similarity_threshold: float) -> Dict:
        """
        Cached version of network creation that works with hashable parameters.
        
        Args:
            data_hash: Hash of the source data
            artist_list: List of tuples (artist_name, play_count)
            top_n_artists: Number of top artists to include
            min_plays_threshold: Minimum plays to include artist
            min_similarity_threshold: Minimum similarity to include edge
            
        Returns:
            Enhanced network data dict
        """
        print(f"🔄 Creating network data (cache key: {data_hash[:8]}...)")
        
        # Recreate the data structures needed for processing
        artist_plays = pd.Series({artist: count for artist, count in artist_list})
        
        # Continue with the actual network generation logic...
        return self._create_network_from_artist_data(
            artist_plays, top_n_artists, min_plays_threshold, min_similarity_threshold
        )
    
    def _create_network_from_artist_data(self, artist_plays: pd.Series,
                                        top_n_artists: int, min_plays_threshold: int,
                                        min_similarity_threshold: float) -> Dict:
        """
        Core network generation logic extracted for caching.
        """
        # Filter by minimum threshold
        artist_plays_filtered = artist_plays[artist_plays >= min_plays_threshold]
        top_artists = artist_plays_filtered.head(top_n_artists)
        
        print(f"✅ Selected {len(top_artists)} artists (min {min_plays_threshold} plays)")
        
        # Fetch enhanced artist data for node creation
        print(f"🔍 Step 1/3: Fetching enhanced artist data...")
        artist_list = list(top_artists.index)
        
        def progress_callback(current, total, artist_name):
            if current % 5 == 0 or current == total:
                print(f"      📋 {current}/{total}: {artist_name}")
        
        enhanced_data = self.artist_fetcher.batch_fetch_artist_data(
            artist_list, 
            include_similar=False,  # We'll get similarities separately with comprehensive system
            progress_callback=progress_callback
        )
        
        # Continue with the rest of the network generation...
        # (This would contain the rest of the original method logic)
        # For now, return a placeholder to test caching
        return {
            'nodes': [],
            'edges': [],
            'metadata': {
                'total_artists': len(top_artists),
                'parameters': {
                    'top_n_artists': top_n_artists,
                    'min_plays_threshold': min_plays_threshold,
                    'min_similarity_threshold': min_similarity_threshold
                }
            }
        }
    
    def create_network_data(self, df: pd.DataFrame, 
                          top_n_artists: int = None,
                          min_plays_threshold: int = None,
                          min_similarity_threshold: float = None) -> Dict:
        """
        Create enhanced network data using comprehensive multi-API similarity system.
        
        Args:
            df: DataFrame with listening history
            top_n_artists: Number of top artists to include (defaults to config)
            min_plays_threshold: Minimum plays to include artist (defaults to config)
            min_similarity_threshold: Minimum similarity to include edge (defaults to config)
            
        Returns:
            Enhanced network data dict with nodes, edges, and genre information
        """
        # Use config defaults if parameters not provided
        if top_n_artists is None:
            top_n_artists = self.network_config['top_n_artists']
        if min_plays_threshold is None:
            min_plays_threshold = self.network_config['min_plays_threshold']
        if min_similarity_threshold is None:
            min_similarity_threshold = self.network_config['min_similarity_threshold']
            
        print(f"🌟 Creating COMPREHENSIVE network data for top {top_n_artists} artists...")
        print(f"   🎯 Multi-API system: Last.fm + Deezer + MusicBrainz + Manual")
        print(f"   📊 All-pairs comparison: {top_n_artists * (top_n_artists - 1) // 2} pairs")
        print(f"   🎵 Similarity threshold: {min_similarity_threshold}, Min plays: {min_plays_threshold}")
        
        if df.empty or 'artist' not in df.columns:
            print("❌ No artist data available")
            return {'nodes': [], 'edges': [], 'metadata': {}}
        
        # Get top artists by play count
        artist_plays = df.groupby('artist').size().sort_values(ascending=False)
        
        # Filter by minimum threshold
        artist_plays_filtered = artist_plays[artist_plays >= min_plays_threshold]
        top_artists = artist_plays_filtered.head(top_n_artists)
        
        print(f"✅ Selected {len(top_artists)} artists (min {min_plays_threshold} plays)")
        
        # Fetch enhanced artist data for node creation
        print(f"🔍 Step 1/3: Fetching enhanced artist data...")
        artist_list = list(top_artists.index)
        
        def progress_callback(current, total, artist_name):
            if current % 5 == 0 or current == total:
                print(f"      📋 {current}/{total}: {artist_name}")
        
        enhanced_data = self.artist_fetcher.batch_fetch_artist_data(
            artist_list, 
            include_similar=False,  # We'll get similarities separately with comprehensive system
            progress_callback=progress_callback
        )
        
        # Create nodes with enhanced data and genre classification
        print(f"🎨 Step 2/3: Creating nodes with genre classification...")
        nodes = []
        genre_distribution = defaultdict(int)
        successful_artists = 0
        
        for i, (artist, play_count) in enumerate(top_artists.items()):
            rank = i + 1
            enhanced = enhanced_data[i]
            
            # Debug: Check why artists might be failing
            if not enhanced['success'] and successful_artists < 3:
                print(f"      ❌ Debug: {artist} failed - success={enhanced['success']}")
                print(f"           Error: {enhanced.get('error', 'Unknown error')}")
                print(f"           Has lastfm_data: {bool(enhanced.get('lastfm_data'))}")
                print(f"           Has spotify_data: {bool(enhanced.get('spotify_data'))}")
            
            if enhanced['success']:
                successful_artists += 1
                
                # Classify genres (with debugging)
                primary_genre, all_genres = self.classify_artist_genre(enhanced)
                
                # Debug: Print first few classifications
                if successful_artists <= 3:
                    print(f"      🔍 Debug: {artist} -> genre: {primary_genre}, tags: {all_genres[:3]}")
                    if enhanced.get('lastfm_data'):
                        print(f"           Last.fm tags: {[tag.get('name', 'no-name') for tag in enhanced['lastfm_data'].get('tags', [])[:3]]}")
                    if enhanced.get('spotify_data'):
                        print(f"           Spotify genres: {enhanced['spotify_data'].get('genres', [])[:3]}")
                
                genre_distribution[primary_genre] += 1
                
                # Use configured listener count source
                listener_count = enhanced['primary_listener_count']
                listener_source = enhanced['primary_source']
                
                node = {
                    'id': artist,
                    'name': enhanced['canonical_name'],
                    'play_count': int(play_count),
                    'rank': rank,
                    'size': listener_count,
                    'listener_count': listener_count,
                    'listener_source': listener_source,
                    'in_library': True,
                    
                    # Genre information for clustering
                    'cluster_genre': primary_genre,
                    'all_genres': all_genres
                }
                
                # Add API-specific data
                if enhanced['lastfm_data']:
                    node.update({
                        'lastfm_listeners': enhanced['lastfm_data']['listeners'],
                        'lastfm_playcount': enhanced['lastfm_data']['playcount'],
                        'lastfm_url': enhanced['lastfm_data']['url'],
                        'genres_lastfm': [tag['name'] for tag in enhanced['lastfm_data']['tags'][:3]]
                    })
                
                if enhanced['spotify_data']:
                    node.update({
                        'spotify_followers': enhanced['spotify_data']['followers'],
                        'spotify_popularity': enhanced['spotify_data']['popularity'],
                        'spotify_id': enhanced['spotify_data']['spotify_artist_id'],
                        'photo_url': enhanced['spotify_data']['photo_url'],
                        'genres_spotify': enhanced['spotify_data']['genres'][:3]
                    })
                
                nodes.append(node)
            else:
                # Handle failed artists
                fallback_behavior = self.network_config['fallback_behavior']
                if fallback_behavior != 'skip':
                    node = {
                        'id': artist,
                        'name': artist,
                        'play_count': int(play_count),
                        'rank': rank,
                        'size': int(play_count),
                        'listener_count': 0,
                        'listener_source': 'play_count_fallback',
                        'in_library': True,
                        'cluster_genre': 'other',
                        'all_genres': []
                    }
                    nodes.append(node)
                    genre_distribution['other'] += 1
        
        print(f"✅ Successfully created {successful_artists}/{len(artist_list)} nodes")
        print(f"   🎨 Genre distribution: {dict(genre_distribution)}")
        
        # Get comprehensive similarity matrix
        print(f"🕸️  Step 3/3: Building comprehensive similarity network...")
        all_similarities = self.get_comprehensive_similarity_matrix(
            artist_list, 
            min_threshold=min_similarity_threshold
        )
        
        # Create weighted edges using ComprehensiveEdgeWeighter
        print(f"⚖️  Creating weighted edges with multi-source fusion...")
        weighted_edges = self.edge_weighter.create_network_edges(all_similarities)
        
        # Convert to D3.js format
        edges = []
        edge_type_counts = defaultdict(int)
        
        for weighted_edge in weighted_edges:
            edge_dict = weighted_edge.to_d3_format()
            edges.append(edge_dict)
            edge_type_counts[weighted_edge.fusion_method] += 1
        
        print(f"✅ Created {len(edges)} comprehensive edges")
        print(f"   ⚖️  Edge fusion methods: {dict(edge_type_counts)}")
        
        # Create comprehensive metadata
        metadata = {
            'generated': datetime.now().isoformat(),
            'system_version': 'comprehensive_v2.0',
            'total_artists_in_data': len(artist_plays),
            'artists_included': len(nodes),
            'artists_with_api_data': successful_artists,
            'total_plays': len(df),
            'date_range': {
                'start': df.index.min().isoformat() if hasattr(df.index, 'min') else None,
                'end': df.index.max().isoformat() if hasattr(df.index, 'max') else None
            },
            'genre_distribution': dict(genre_distribution),
            'unique_genres': list(genre_distribution.keys()),
            'edge_fusion_methods': dict(edge_type_counts),
            'network_statistics': {
                'node_count': len(nodes),
                'edge_count': len(edges),
                'density': len(edges) / (len(nodes) * (len(nodes) - 1) / 2) if len(nodes) > 1 else 0,
                'avg_degree': 2 * len(edges) / len(nodes) if nodes else 0
            },
            'data_sources': {
                'similarity_apis': ['lastfm', 'deezer', 'musicbrainz', 'manual'],
                'metadata_apis': ['lastfm', 'spotify'],
                'edge_weighting': 'comprehensive_multi_source_fusion'
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
                'all_pairs_comparison': True,
                'genre_classification': True
            }
        }
        
        network_data = {
            'nodes': nodes,
            'edges': edges,
            'metadata': metadata
        }
        
        print(f"🌟 COMPREHENSIVE network complete:")
        print(f"   📊 {len(nodes)} nodes, {len(edges)} edges")
        print(f"   🎨 {len(genre_distribution)} genres: {list(genre_distribution.keys())}")
        print(f"   ⚖️  Multi-source fusion with confidence scoring")
        print(f"   ✅ Ready for D3.js visualization with genre clustering")
        
        return network_data
    
    
    def save_network_data(self, network_data: Dict, filename: str = 'artist_network.json') -> str:
        """Save network data to JSON file."""
        filepath = os.path.abspath(filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Network data saved: {filepath}")
        return filepath
    
    def get_node_genre(self, node: Dict, default: str = 'other') -> str:
        """
        Safely retrieve the genre for a given node.
        
        Args:
            node: Node dictionary from network data
            default: Default genre if not found
            
        Returns:
            Genre string (single source of truth for node genre access)
        """
        return node.get('cluster_genre', default)
    
    def count_classified_nodes(self, network_data: Dict) -> int:
        """
        Count nodes with a non-default genre classification.
        
        Args:
            network_data: Network data dictionary
            
        Returns:
            Number of successfully classified nodes
        """
        nodes = network_data.get('nodes', [])
        return sum(1 for node in nodes if self.get_node_genre(node) != 'other')
    
    def get_genre_distribution(self, network_data: Dict) -> Dict[str, int]:
        """
        Get genre distribution across all nodes.
        
        Args:
            network_data: Network data dictionary
            
        Returns:
            Dictionary mapping genre to count
        """
        nodes = network_data.get('nodes', [])
        distribution = {}
        for node in nodes:
            genre = self.get_node_genre(node)
            distribution[genre] = distribution.get(genre, 0) + 1
        return distribution
    
    def validate_network_data(self, network_data: Dict) -> Dict:
        """
        Comprehensive validation of network data using centralized accessors.
        
        Args:
            network_data: Network data dictionary
            
        Returns:
            Validation results dictionary
        """
        nodes = network_data.get('nodes', [])
        edges = network_data.get('edges', [])
        
        validation = {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'nodes_with_genre_classification': self.count_classified_nodes(network_data),
            'genre_distribution': self.get_genre_distribution(network_data),
            'validation_passed': True,
            'issues': []
        }
        
        # Validation checks
        if validation['nodes_with_genre_classification'] == 0 and len(nodes) > 0:
            validation['validation_passed'] = False
            validation['issues'].append('No nodes have genre classification')
        
        if validation['genre_distribution'].get('other', 0) == len(nodes) and len(nodes) > 0:
            validation['validation_passed'] = False
            validation['issues'].append('All nodes classified as "other"')
        
        # Check for reasonable genre diversity
        if len(validation['genre_distribution']) < 2 and len(nodes) > 10:
            validation['issues'].append('Low genre diversity detected')
        
        return validation

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