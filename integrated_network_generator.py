#!/usr/bin/env python3
"""
Integrated Network Generator
============================
Main network generation system that integrates:
1. Last.fm as PRIMARY similarity source
2. Deezer as secondary source  
3. MusicBrainz for factual relationships
4. Manual connections for critical missing links
5. Comprehensive edge weighting system
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI
from deezer_similarity_api import DeezerSimilarityAPI
from musicbrainz_similarity_api import MusicBrainzSimilarityAPI
from fixed_edge_weighting import FixedEdgeWeighter
from enhanced_name_matcher import EnhancedNameMatcher
from enhanced_artist_metadata import EnhancedArtistMetadata
# No manual connections - all systematic/data-driven

logger = logging.getLogger(__name__)

class IntegratedNetworkGenerator:
    """
    Comprehensive network generator with multi-source similarity data
    and sophisticated edge weighting.
    """
    
    def __init__(self, config_file: str = "configurations.txt"):
        """Initialize with all APIs and systems."""
        print("🌐 Integrated Network Generator")
        print("=" * 35)
        
        # Load configuration
        self.config = AppConfig(config_file)
        
        # Try to get network config, use defaults if not available
        try:
            self.network_config = self.config.get_network_config()
        except AttributeError:
            # Use default network configuration
            self.network_config = {
                'TOP_N_ARTISTS': 100,
                'MIN_SIMILARITY_THRESHOLD': 0.2,
                'MIN_PLAYS_THRESHOLD': 5
            }
        
        # Initialize APIs with Last.fm as PRIMARY
        self._initialize_apis()
        
        # Initialize fixed edge weighting system
        self.edge_weighter = FixedEdgeWeighter()
        print("✅ Fixed edge weighting system initialized")
        
        # Initialize enhanced name matcher for cross-cultural matching
        self.name_matcher = EnhancedNameMatcher()
        print("✅ Enhanced name matcher initialized")
        
        # Initialize enhanced metadata system for accurate display data
        self.metadata_enhancer = EnhancedArtistMetadata()
        print("✅ Enhanced metadata system initialized")
        
        # Configuration parameters
        self.top_n_artists = self.network_config.get('TOP_N_ARTISTS', 100)
        self.min_similarity_threshold = self.network_config.get('MIN_SIMILARITY_THRESHOLD', 0.2)
        self.min_plays_threshold = self.network_config.get('MIN_PLAYS_THRESHOLD', 5)
        
        print(f"📊 Network parameters:")
        print(f"   Top artists: {self.top_n_artists}")
        print(f"   Min similarity: {self.min_similarity_threshold}")
        print(f"   Min plays: {self.min_plays_threshold}")
    
    def _initialize_apis(self):
        """Initialize all similarity APIs with Last.fm as primary."""
        # Last.fm API (PRIMARY source)
        lastfm_config = self.config.get_lastfm_config()
        self.lastfm_api = None
        
        if lastfm_config['enabled'] and lastfm_config['api_key']:
            self.lastfm_api = LastfmAPI(
                lastfm_config['api_key'],
                lastfm_config['api_secret'],
                lastfm_config['cache_dir']
            )
            print("✅ Last.fm API initialized (PRIMARY similarity source)")
        else:
            print("⚠️  Last.fm API not configured - this is your PRIMARY source!")
        
        # Deezer API (secondary source)
        self.deezer_api = DeezerSimilarityAPI()
        print("✅ Deezer API initialized (secondary source)")
        
        # MusicBrainz API (relationship source)
        self.musicbrainz_api = MusicBrainzSimilarityAPI()
        print("✅ MusicBrainz API initialized (factual relationships)")
    
    def generate_comprehensive_network(self, artists_data: List[Dict], 
                                     output_filename: Optional[str] = None) -> Dict:
        """
        Generate comprehensive artist network using multi-source similarity data.
        
        Args:
            artists_data: List of artist dictionaries with play counts
            output_filename: Optional filename to save network JSON
            
        Returns:
            Network data dictionary with nodes and weighted edges
        """
        print(f"\n🔗 Generating comprehensive network for {len(artists_data)} artists")
        print("=" * 60)
        
        if not artists_data:
            raise ValueError("No artists data provided")
        
        # Filter artists by play threshold
        filtered_artists = [
            artist for artist in artists_data 
            if artist.get('play_count', 0) >= self.min_plays_threshold
        ]
        
        # Limit to top N artists
        top_artists = sorted(
            filtered_artists, 
            key=lambda x: x.get('play_count', 0), 
            reverse=True
        )[:self.top_n_artists]
        
        print(f"📊 Processing {len(top_artists)} artists (after filtering)")
        
        # Create nodes
        nodes = self._create_nodes(top_artists)
        
        # Generate edges with comprehensive similarity data
        edges = self._generate_comprehensive_edges(top_artists)
        
        # Create network data
        network_data = {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'created': datetime.now().isoformat(),
                'total_artists': len(top_artists),
                'total_edges': len(edges),
                'parameters': {
                    'top_n_artists': self.top_n_artists,
                    'min_similarity_threshold': self.min_similarity_threshold,
                    'min_plays_threshold': self.min_plays_threshold
                },
                'apis_used': {
                    'lastfm': bool(self.lastfm_api),
                    'deezer': True,
                    'musicbrainz': True,
                    'manual_connections': True
                },
                'edge_weighting': 'comprehensive_multi_source'
            }
        }
        
        # Save to file if requested
        if output_filename:
            self._save_network(network_data, output_filename)
        
        print(f"\n🎉 Network generation complete!")
        print(f"   Nodes: {len(nodes)}")
        print(f"   Edges: {len(edges)}")
        
        return network_data
    
    def _create_nodes(self, artists_data: List[Dict]) -> List[Dict]:
        """Create network nodes from artist data with enhanced metadata."""
        print(f"🎯 Creating nodes with enhanced metadata for {len(artists_data)} artists...")
        
        nodes = []
        
        for i, artist in enumerate(artists_data):
            # Create basic node
            node = {
                'id': artist['name'].lower().replace(' ', '_'),
                'name': artist['name'],
                'play_count': artist.get('play_count', 0),
                'rank': i + 1
            }
            
            # Get enhanced display metadata (separate from similarity matching)
            display_metadata = self.metadata_enhancer.get_artist_display_metadata(artist['name'])
            
            if display_metadata:
                # Update with accurate display data
                node.update({
                    'listeners': display_metadata['listeners'],
                    'playcount': display_metadata['playcount'],
                    'lastfm_url': display_metadata['url'],
                    'canonical_name': display_metadata['name'],
                    'display_metadata_source': display_metadata['variant_used'],
                    'mbid': display_metadata['mbid']
                })
            else:
                # Fallback to basic data
                node.update({
                    'listeners': 0,
                    'playcount': 0,
                    'lastfm_url': '',
                    'canonical_name': artist['name'],
                    'display_metadata_source': 'not_found',
                    'mbid': ''
                })
            
            nodes.append(node)
        
        print(f"✅ Created {len(nodes)} nodes with enhanced metadata")
        return nodes
    
    def _generate_comprehensive_edges(self, artists_data: List[Dict]) -> List[Dict]:
        """Generate edges using comprehensive multi-source similarity data."""
        print(f"\n🔗 Generating edges with multi-source similarity data...")
        
        edges = []
        total_comparisons = len(artists_data)
        
        for i, source_artist in enumerate(artists_data, 1):
            source_name = source_artist['name']
            
            print(f"   [{i}/{total_comparisons}] Processing {source_name}...")
            
            # Get comprehensive similarity data from all sources
            similarity_data = self._get_multi_source_similarity(source_name)
            
            # Create target artist lookup
            target_artists = {a['name'].lower(): a for a in artists_data}
            target_artist_names = {a['name'] for a in artists_data}
            
            # Enhance similarity data with relationship-based matching
            enhanced_similarity_data = self._enhance_similarity_with_relationships(
                source_name, similarity_data, target_artist_names
            )
            
            # Generate edges for this artist using enhanced data
            artist_edges = self._create_edges_for_artist(
                source_artist, enhanced_similarity_data, target_artists
            )
            
            edges.extend(artist_edges)
            
            # Rate limiting
            if i % 5 == 0:
                time.sleep(0.5)
        
        print(f"✅ Generated {len(edges)} total edges")
        return edges
    
    def _get_multi_source_similarity(self, artist_name: str) -> Dict[str, List[Dict]]:
        """Get similarity data from all available sources."""
        similarity_data = {}
        
        # Last.fm (PRIMARY source)
        if self.lastfm_api:
            try:
                lastfm_results = self.lastfm_api.get_similar_artists(
                    artist_name, 
                    limit=50,
                    use_enhanced_matching=True
                )
                similarity_data['lastfm'] = lastfm_results
                
            except Exception as e:
                logger.warning(f"Last.fm error for {artist_name}: {e}")
                similarity_data['lastfm'] = []
        
        # Deezer (secondary source)
        try:
            deezer_results = self.deezer_api.get_similar_artists(artist_name, limit=30)
            similarity_data['deezer'] = deezer_results
            
        except Exception as e:
            logger.warning(f"Deezer error for {artist_name}: {e}")
            similarity_data['deezer'] = []
        
        # MusicBrainz (factual relationships)
        try:
            mb_results = self.musicbrainz_api.get_relationship_based_similar_artists(
                artist_name, limit=20
            )
            similarity_data['musicbrainz'] = mb_results
            
        except Exception as e:
            logger.warning(f"MusicBrainz error for {artist_name}: {e}")
            similarity_data['musicbrainz'] = []
        
        # NOTE: No manual connections per user request
        # All connections must be systematic and data-driven
        
        return similarity_data
    
    def _enhance_similarity_with_relationships(self, artist_name: str, similarity_data: Dict[str, List[Dict]], 
                                             target_artists: Set[str]) -> Dict[str, List[Dict]]:
        """Enhance similarity data using relationship-based matching."""
        enhanced_data = {}
        
        for source, results in similarity_data.items():
            # Use enhanced name matcher to add relationship-based connections
            enhanced_results = self.name_matcher.enhance_similarity_matching(
                artist_name, results, target_artists
            )
            enhanced_data[source] = enhanced_results
        
        return enhanced_data
    
    def _create_edges_for_artist(self, source_artist: Dict, similarity_data: Dict[str, List[Dict]], 
                                target_artists: Dict[str, Dict]) -> List[Dict]:
        """Create weighted edges for one artist using multi-source data."""
        edges = []
        source_name = source_artist['name']
        source_id = source_name.lower().replace(' ', '_')
        
        # Collect all potential targets from all sources
        potential_targets = set()
        
        for source, results in similarity_data.items():
            for result in results:
                target_name = result['name']
                if target_name.lower() in target_artists:
                    potential_targets.add(target_name)
        
        # Create edges for each potential target
        for target_name in potential_targets:
            target_artist = target_artists[target_name.lower()]
            target_id = target_name.lower().replace(' ', '_')
            
            # Skip self-connections
            if source_id == target_id:
                continue
            
            # Create weighted edge using comprehensive edge weighting
            edge = self.edge_weighter.create_weighted_edge(
                source_name, target_name, similarity_data
            )
            
            if edge and edge.similarity >= self.min_similarity_threshold:
                edge_data = {
                    'source': source_id,
                    'target': target_id,
                    'weight': edge.similarity,  # For network layout
                    'distance': edge.distance,  # For pathfinding
                    'confidence': edge.confidence,
                    'is_factual': edge.is_factual,
                    'fusion_method': edge.fusion_method,
                    'sources': [contrib.source for contrib in edge.contributions],
                    'source_details': {
                        contrib.source: {
                            'raw_value': contrib.raw_value,
                            'normalized_similarity': contrib.normalized_similarity,
                            'confidence': contrib.confidence
                        } for contrib in edge.contributions
                    }
                }
                edges.append(edge_data)
        
        return edges
    
    def _save_network(self, network_data: Dict, filename: str):
        """Save network data to JSON file."""
        output_path = Path(filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Network saved to: {output_path}")
    
    def get_network_statistics(self, network_data: Dict) -> Dict:
        """Generate statistics about the network."""
        nodes = network_data.get('nodes', [])
        edges = network_data.get('edges', [])
        
        if not edges:
            return {'error': 'No edges in network'}
        
        # Edge source statistics
        source_stats = {}
        fusion_method_stats = {}
        factual_edges = 0
        
        for edge in edges:
            # Sources
            for source in edge.get('sources', []):
                source_stats[source] = source_stats.get(source, 0) + 1
            
            # Fusion methods
            method = edge.get('fusion_method', 'unknown')
            fusion_method_stats[method] = fusion_method_stats.get(method, 0) + 1
            
            # Factual edges
            if edge.get('is_factual', False):
                factual_edges += 1
        
        # Calculate averages
        confidences = [edge.get('confidence', 0) for edge in edges]
        similarities = [edge.get('weight', 0) for edge in edges]
        
        stats = {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'average_confidence': sum(confidences) / len(confidences) if confidences else 0,
            'average_similarity': sum(similarities) / len(similarities) if similarities else 0,
            'factual_edges': factual_edges,
            'factual_percentage': (factual_edges / len(edges)) * 100 if edges else 0,
            'source_statistics': source_stats,
            'fusion_method_statistics': fusion_method_stats
        }
        
        return stats

def load_artists_from_spotify_data(spotify_data_file: str = "spotify_data.json") -> List[Dict]:
    """Load and aggregate artist data from Spotify JSON."""
    print(f"📊 Loading artist data from {spotify_data_file}...")
    
    try:
        with open(spotify_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Aggregate play counts by artist
        artist_counts = {}
        
        for entry in data:
            artist_name = None
            
            if 'artistName' in entry:
                artist_name = entry['artistName']
            elif 'master_metadata_album_artist_name' in entry:
                artist_name = entry['master_metadata_album_artist_name']
            
            if artist_name:
                artist_name = artist_name.strip()
                if artist_name:
                    artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
        
        # Convert to list format
        artists_data = [
            {'name': name, 'play_count': count}
            for name, count in artist_counts.items()
        ]
        
        # Sort by play count
        artists_data.sort(key=lambda x: x['play_count'], reverse=True)
        
        print(f"✅ Loaded {len(artists_data)} unique artists")
        return artists_data
        
    except Exception as e:
        print(f"❌ Error loading artist data: {e}")
        return []

def main():
    """Main function to generate integrated network."""
    print("🌐 Integrated Network Generation")
    print("=" * 35)
    
    # Load artist data
    artists_data = load_artists_from_spotify_data()
    
    if not artists_data:
        print("❌ No artist data loaded")
        return
    
    # Initialize network generator
    generator = IntegratedNetworkGenerator()
    
    # Generate comprehensive network
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"integrated_network_{timestamp}.json"
    
    network_data = generator.generate_comprehensive_network(
        artists_data, output_filename
    )
    
    # Show statistics
    stats = generator.get_network_statistics(network_data)
    
    print(f"\n📊 Network Statistics:")
    print(f"   Nodes: {stats['total_nodes']}")
    print(f"   Edges: {stats['total_edges']}")
    print(f"   Average confidence: {stats['average_confidence']:.3f}")
    print(f"   Average similarity: {stats['average_similarity']:.3f}")
    print(f"   Factual edges: {stats['factual_edges']} ({stats['factual_percentage']:.1f}%)")
    
    print(f"\n🔌 Source Statistics:")
    for source, count in stats['source_statistics'].items():
        percentage = (count / stats['total_edges']) * 100
        print(f"   {source}: {count} edges ({percentage:.1f}%)")
    
    print(f"\n⚖️  Fusion Methods:")
    for method, count in stats['fusion_method_statistics'].items():
        percentage = (count / stats['total_edges']) * 100
        print(f"   {method}: {count} ({percentage:.1f}%)")

if __name__ == "__main__":
    main()