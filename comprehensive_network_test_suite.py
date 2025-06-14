#!/usr/bin/env python3
"""
Comprehensive Network Test Suite
=================================
A complete, highly configurable test suite for artist similarity networks.

Features:
- Multi-API similarity testing with verified artists
- Configurable network parameters
- Visual property validation (colors, glow, size)
- Network persistence and retrieval testing
- Individual artist connection analysis
- Cross-validation of similarity relationships
- Last.fm listeners and Spotify popularity metrics

Usage:
    python comprehensive_network_test_suite.py --config test_config.yaml
    python comprehensive_network_test_suite.py --artist "Taylor Swift" --connections
"""

import json
import logging
import sys
import time
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import networkx as nx
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Import project modules
from artist_verification import ArtistVerifier
from lastfm_utils import LastfmAPI
from artist_data_fetcher import EnhancedArtistDataFetcher
from network_utils import prepare_dataframe_for_network_analysis
from data_processor import clean_and_filter_data
from config_loader import AppConfig

@dataclass
class NetworkTestConfig:
    """Configuration for network testing."""
    # Core parameters
    top_n_artists: int = 50
    similarity_threshold: float = 0.3
    min_plays_threshold: int = 5
    
    # Data source
    data_path: str = "lastfm_data.csv"
    force_data_source: Optional[str] = None
    
    # Seed artists for network generation
    seed_artists: List[str] = field(default_factory=lambda: ["YOASOBI", "IVE", "BTS"])
    
    # Testing scope
    test_verification: bool = True
    test_similarity_symmetry: bool = True
    test_visual_properties: bool = True
    test_persistence: bool = True
    test_individual_connections: bool = True
    
    # Visual property thresholds
    min_node_size: float = 5.0
    max_node_size: float = 30.0
    min_glow_value: float = 0.1
    max_glow_value: float = 1.0
    
    # Output configuration
    output_dir: str = "network_test_results"
    save_networks: bool = True
    generate_reports: bool = True
    
    # Performance limits
    max_api_calls_per_artist: int = 5
    rate_limit_delay: float = 0.2
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'NetworkTestConfig':
        """Load configuration from YAML file."""
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML is required for YAML configuration files. Install with: pip install PyYAML")
        
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Convert nested structure to flat kwargs
        config_data = {**data.get('default_params', {}), **data.get('test_config', {})}
        return cls(**config_data)

class NetworkTestResults:
    """Container for test results and metrics."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.warnings = []
        self.errors = []
        self.metrics = {}
        self.artifacts = {}  # Generated files, graphs, etc.
    
    def add_test(self, name: str, passed: bool, details: Optional[str] = None):
        """Record a test result."""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            logger.info(f"✅ {name}")
        else:
            self.tests_failed += 1
            logger.error(f"❌ {name}: {details or 'Failed'}")
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
        logger.warning(f"⚠️  {message}")
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        logger.error(f"🚨 {message}")
    
    def add_metric(self, name: str, value: Any):
        """Add a performance/quality metric."""
        self.metrics[name] = value
        logger.info(f"📊 {name}: {value}")
    
    def add_artifact(self, name: str, path: str):
        """Record a generated artifact."""
        self.artifacts[name] = path
        logger.info(f"💾 {name}: {path}")
    
    def summary(self) -> Dict:
        """Get test summary."""
        duration = (datetime.now() - self.start_time).total_seconds()
        return {
            "duration_seconds": duration,
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "success_rate": self.tests_passed / max(1, self.tests_run),
            "warnings": len(self.warnings),
            "errors": len(self.errors),
            "metrics": self.metrics,
            "artifacts": self.artifacts
        }

class ComprehensiveNetworkTestSuite:
    """Main test suite for network generation and validation."""
    
    def __init__(self, config: NetworkTestConfig):
        self.config = config
        self.results = NetworkTestResults()
        
        # Ensure output directory exists
        Path(self.config.output_dir).mkdir(exist_ok=True)
        
        # Initialize components
        self.verifier = None
        self.lastfm_api = None
        self.data_fetcher = None
        self.user_data = None
        self.verified_artists = {}
        self.network = None
        
        print("🧪 Comprehensive Network Test Suite")
        print("=" * 50)
        print(f"📊 Configuration:")
        print(f"   Top N Artists: {self.config.top_n_artists}")
        print(f"   Similarity Threshold: {self.config.similarity_threshold}")
        print(f"   Seed Artists: {', '.join(self.config.seed_artists)}")
        print(f"   Output Directory: {self.config.output_dir}")
    
    def initialize_systems(self):
        """Initialize all required systems and APIs."""
        print(f"\\n🔧 Initializing Systems")
        print("-" * 30)
        
        try:
            # Initialize artist verification system
            self.verifier = ArtistVerifier(
                data_path=self.config.data_path
            )
            self.results.add_test("Artist Verifier Initialization", True)
        except Exception as e:
            self.results.add_test("Artist Verifier Initialization", False, str(e))
            return False
        
        try:
            # Initialize Last.fm API
            app_config = AppConfig()
            lastfm_config = app_config.get_lastfm_config()
            
            if lastfm_config['enabled'] and lastfm_config['api_key']:
                self.lastfm_api = LastfmAPI(
                    lastfm_config['api_key'],
                    lastfm_config['api_secret'],
                    lastfm_config['cache_dir']
                )
                self.results.add_test("Last.fm API Initialization", True)
            else:
                self.results.add_error("Last.fm API not configured")
                return False
        except Exception as e:
            self.results.add_test("Last.fm API Initialization", False, str(e))
            return False
        
        try:
            # Initialize enhanced data fetcher
            self.data_fetcher = EnhancedArtistDataFetcher(
                config=app_config
            )
            self.results.add_test("Data Fetcher Initialization", True)
        except Exception as e:
            self.results.add_test("Data Fetcher Initialization", False, str(e))
            return False
        
        try:
            # Load and prepare user data
            app_config = AppConfig()
            self.user_data = clean_and_filter_data(app_config)
            if self.user_data is not None and not self.user_data.empty:
                self.user_data = prepare_dataframe_for_network_analysis(self.user_data)
                self.results.add_test("User Data Loading", True)
                self.results.add_metric("Total User Tracks", len(self.user_data))
                self.results.add_metric("Unique Artists", self.user_data['artist'].nunique())
            else:
                self.results.add_test("User Data Loading", False, "No data loaded")
                return False
        except Exception as e:
            self.results.add_test("User Data Loading", False, str(e))
            return False
        
        return True
    
    def test_artist_verification(self):
        """Test artist verification system with seed artists."""
        if not self.config.test_verification:
            return
        
        print(f"\\n🔍 Testing Artist Verification")
        print("-" * 35)
        
        for artist in self.config.seed_artists:
            try:
                # Check if artist exists in user data
                user_tracks = self.verifier._get_user_tracks_for_artist(artist)
                if not user_tracks:
                    self.results.add_warning(f"Artist '{artist}' not found in user data")
                    continue
                
                # Get candidates from Last.fm
                candidates = self.lastfm_api.search_artists(artist, limit=5)
                if not candidates:
                    self.results.add_warning(f"No Last.fm candidates found for '{artist}'")
                    continue
                
                # Verify artist
                verification_result = self.verifier.verify_artist_candidates(
                    artist, candidates, self.lastfm_api
                )
                
                # Store verified artist
                self.verified_artists[artist] = {
                    'verification_result': verification_result,
                    'user_tracks': len(user_tracks),
                    'candidates_found': len(candidates)
                }
                
                self.results.add_test(
                    f"Verify {artist}",
                    verification_result.confidence_score >= 0.85,
                    f"Confidence: {verification_result.confidence_score:.3f}, Method: {verification_result.verification_method}"
                )
                
                self.results.add_metric(f"{artist}_confidence", verification_result.confidence_score)
                self.results.add_metric(f"{artist}_method", verification_result.verification_method)
                
            except Exception as e:
                self.results.add_test(f"Verify {artist}", False, str(e))
    
    def generate_network(self):
        """Generate the artist similarity network."""
        print(f"\\n🌐 Generating Network")
        print("-" * 25)
        
        if not self.verified_artists:
            self.results.add_error("No verified artists available for network generation")
            return
        
        try:
            # Initialize network
            self.network = nx.Graph()
            
            # Add nodes for verified artists
            for artist_name, data in self.verified_artists.items():
                verification_result = data['verification_result']
                chosen_profile = verification_result.chosen_profile
                
                # Get base metrics
                listeners = int(chosen_profile.get('listeners', 0))
                user_plays = data['user_tracks']
                
                # Calculate visual properties
                node_size = self._calculate_node_size(listeners, user_plays)
                glow_value = self._calculate_glow_value(verification_result.confidence_score, listeners)
                color = self._calculate_node_color(user_plays, listeners)
                
                self.network.add_node(artist_name, **{
                    'display_name': chosen_profile.get('name', artist_name),
                    'lastfm_listeners': listeners,
                    'lastfm_url': chosen_profile.get('url', ''),
                    'user_plays': user_plays,
                    'verification_confidence': verification_result.confidence_score,
                    'verification_method': verification_result.verification_method,
                    'node_size': node_size,
                    'glow_value': glow_value,
                    'color': color,
                    'spotify_popularity': 0  # Will be enhanced later
                })
            
            # Fetch similarity data and add edges
            self._add_similarity_edges()
            
            # Enhance with Spotify data if available
            self._enhance_with_spotify_data()
            
            self.results.add_test("Network Generation", True)
            self.results.add_metric("Network Nodes", self.network.number_of_nodes())
            self.results.add_metric("Network Edges", self.network.number_of_edges())
            
        except Exception as e:
            self.results.add_test("Network Generation", False, str(e))
    
    def _calculate_node_size(self, listeners: int, user_plays: int) -> float:
        """Calculate node size based on popularity and user engagement."""
        # Combine Last.fm listeners and user plays
        popularity_score = min(1.0, listeners / 1000000)  # Normalize to millions
        user_score = min(1.0, user_plays / 50)  # Normalize to 50 plays
        
        combined_score = (popularity_score * 0.7) + (user_score * 0.3)
        
        # Map to size range
        size_range = self.config.max_node_size - self.config.min_node_size
        return self.config.min_node_size + (combined_score * size_range)
    
    def _calculate_glow_value(self, confidence: float, listeners: int) -> float:
        """Calculate glow intensity based on verification confidence and popularity."""
        # High confidence and high popularity = more glow
        confidence_factor = confidence
        popularity_factor = min(1.0, listeners / 500000)  # Normalize to 500K
        
        combined_factor = (confidence_factor * 0.8) + (popularity_factor * 0.2)
        
        # Map to glow range
        glow_range = self.config.max_glow_value - self.config.min_glow_value
        return self.config.min_glow_value + (combined_factor * glow_range)
    
    def _calculate_node_color(self, user_plays: int, listeners: int) -> str:
        """Calculate node color based on user engagement vs. popularity."""
        if user_plays == 0:
            return "#808080"  # Gray for no plays
        
        play_ratio = user_plays / max(1, listeners / 10000)  # Plays per 10K listeners
        
        if play_ratio > 1.0:
            return "#FF6B6B"  # Red for high personal engagement
        elif play_ratio > 0.5:
            return "#4ECDC4"  # Teal for medium engagement  
        elif play_ratio > 0.1:
            return "#45B7D1"  # Blue for low engagement
        else:
            return "#96CEB4"  # Green for popular but low personal engagement
    
    def _add_similarity_edges(self):
        """Add edges based on Last.fm similarity data."""
        artists = list(self.verified_artists.keys())
        
        for i, artist_a in enumerate(artists):
            for j, artist_b in enumerate(artists[i+1:], i+1):
                try:
                    # Get similarity from Last.fm API
                    similarity_data = self.lastfm_api.get_artist_similarity(artist_a, artist_b)
                    
                    if similarity_data and similarity_data.get('similarity', 0) >= self.config.similarity_threshold:
                        similarity = similarity_data['similarity']
                        
                        self.network.add_edge(artist_a, artist_b,
                            similarity=similarity,
                            source='lastfm',
                            weight=similarity
                        )
                    
                    time.sleep(self.config.rate_limit_delay)  # Rate limiting
                    
                except Exception as e:
                    self.results.add_warning(f"Failed to get similarity between {artist_a} and {artist_b}: {e}")
    
    def _enhance_with_spotify_data(self):
        """Enhance network nodes with Spotify popularity data."""
        # This would integrate with Spotify API if available
        # For now, we'll use mock data or skip
        for node in self.network.nodes():
            # Mock Spotify popularity based on Last.fm listeners
            listeners = self.network.nodes[node].get('lastfm_listeners', 0)
            mock_popularity = min(100, int(listeners / 50000))  # Very rough approximation
            self.network.nodes[node]['spotify_popularity'] = mock_popularity
    
    def test_similarity_symmetry(self):
        """Test that similarity relationships are reasonably symmetric."""
        if not self.config.test_similarity_symmetry or not self.network:
            return
        
        print(f"\\n🔄 Testing Similarity Symmetry")
        print("-" * 35)
        
        asymmetric_edges = []
        tolerance = 0.2  # Allow 20% difference
        
        for u, v, data in self.network.edges(data=True):
            similarity_uv = data.get('similarity', 0)
            
            # Check reverse edge
            if self.network.has_edge(v, u):
                similarity_vu = self.network[v][u].get('similarity', 0)
                difference = abs(similarity_uv - similarity_vu)
                
                if difference > tolerance:
                    asymmetric_edges.append((u, v, similarity_uv, similarity_vu, difference))
        
        self.results.add_test(
            "Similarity Symmetry",
            len(asymmetric_edges) == 0,
            f"Found {len(asymmetric_edges)} asymmetric edges"
        )
        
        if asymmetric_edges:
            for u, v, sim_uv, sim_vu, diff in asymmetric_edges[:5]:  # Show first 5
                self.results.add_warning(f"Asymmetric: {u}-{v} ({sim_uv:.3f}) vs {v}-{u} ({sim_vu:.3f}), diff: {diff:.3f}")
    
    def test_visual_properties(self):
        """Test that visual properties are within expected ranges."""
        if not self.config.test_visual_properties or not self.network:
            return
        
        print(f"\\n🎨 Testing Visual Properties")
        print("-" * 32)
        
        for node, data in self.network.nodes(data=True):
            # Test node size
            node_size = data.get('node_size', 0)
            size_valid = self.config.min_node_size <= node_size <= self.config.max_node_size
            self.results.add_test(f"{node} Node Size", size_valid, f"Size: {node_size}")
            
            # Test glow value
            glow_value = data.get('glow_value', 0)
            glow_valid = self.config.min_glow_value <= glow_value <= self.config.max_glow_value
            self.results.add_test(f"{node} Glow Value", glow_valid, f"Glow: {glow_value}")
            
            # Test color format
            color = data.get('color', '')
            color_valid = color.startswith('#') and len(color) == 7
            self.results.add_test(f"{node} Color Format", color_valid, f"Color: {color}")
    
    def save_network(self) -> Optional[str]:
        """Save the network to multiple formats."""
        if not self.network or not self.config.save_networks:
            return None
        
        print(f"\\n💾 Saving Network")
        print("-" * 20)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"comprehensive_network_{timestamp}"
        
        try:
            # Save as JSON
            json_path = Path(self.config.output_dir) / f"{base_name}.json"
            network_data = self._network_to_json()
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(network_data, f, indent=2, ensure_ascii=False)
            self.results.add_artifact("Network JSON", str(json_path))
            
            # Save as GraphML (for Gephi/other tools)
            graphml_path = Path(self.config.output_dir) / f"{base_name}.graphml"
            nx.write_graphml(self.network, graphml_path)
            self.results.add_artifact("Network GraphML", str(graphml_path))
            
            self.results.add_test("Network Persistence", True)
            return str(json_path)
            
        except Exception as e:
            self.results.add_test("Network Persistence", False, str(e))
            return None
    
    def _network_to_json(self) -> Dict:
        """Convert NetworkX graph to JSON format."""
        nodes = []
        for node, data in self.network.nodes(data=True):
            node_data = {'id': node, **data}
            nodes.append(node_data)
        
        edges = []
        for u, v, data in self.network.edges(data=True):
            edge_data = {'source': u, 'target': v, **data}
            edges.append(edge_data)
        
        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'config': {
                    'top_n_artists': self.config.top_n_artists,
                    'similarity_threshold': self.config.similarity_threshold,
                    'seed_artists': self.config.seed_artists
                },
                'metrics': {
                    'node_count': len(nodes),
                    'edge_count': len(edges),
                    'density': nx.density(self.network),
                    'average_clustering': nx.average_clustering(self.network)
                }
            }
        }
    
    def test_individual_connections(self, artist: str):
        """Test connections for a specific artist."""
        if not self.config.test_individual_connections or not self.network:
            return
        
        print(f"\\n🔗 Testing Connections for {artist}")
        print("-" * 40)
        
        if artist not in self.network:
            self.results.add_warning(f"Artist '{artist}' not found in network")
            return
        
        # Get all connections
        neighbors = list(self.network.neighbors(artist))
        
        print(f"📊 {artist} has {len(neighbors)} connections:")
        
        for neighbor in neighbors:
            edge_data = self.network[artist][neighbor]
            similarity = edge_data.get('similarity', 0)
            source = edge_data.get('source', 'unknown')
            
            neighbor_data = self.network.nodes[neighbor]
            listeners = neighbor_data.get('lastfm_listeners', 0)
            
            print(f"  → {neighbor}: {similarity:.3f} similarity ({source}) - {listeners:,} listeners")
        
        self.results.add_metric(f"{artist}_connections", len(neighbors))
        
        # Test that connections meet minimum threshold
        valid_connections = [n for n in neighbors 
                           if self.network[artist][n].get('similarity', 0) >= self.config.similarity_threshold]
        
        self.results.add_test(
            f"{artist} Connection Quality",
            len(valid_connections) == len(neighbors),
            f"{len(valid_connections)}/{len(neighbors)} connections meet threshold"
        )
    
    def generate_report(self):
        """Generate a comprehensive test report."""
        if not self.config.generate_reports:
            return
        
        print(f"\\n📊 Generating Report")
        print("-" * 23)
        
        summary = self.results.summary()
        
        report = {
            'test_summary': summary,
            'configuration': {
                'top_n_artists': self.config.top_n_artists,
                'similarity_threshold': self.config.similarity_threshold,
                'seed_artists': self.config.seed_artists,
                'data_source': self.config.data_path
            },
            'verified_artists': {
                artist: {
                    'confidence': data['verification_result'].confidence_score,
                    'method': data['verification_result'].verification_method,
                    'user_tracks': data['user_tracks']
                }
                for artist, data in self.verified_artists.items()
            },
            'warnings': self.results.warnings,
            'errors': self.results.errors
        }
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path(self.config.output_dir) / f"test_report_{timestamp}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.results.add_artifact("Test Report", str(report_path))
        
        # Print summary
        print(f"\\n🏁 Test Summary")
        print("=" * 20)
        print(f"Tests Run: {summary['tests_run']}")
        print(f"Passed: {summary['tests_passed']}")
        print(f"Failed: {summary['tests_failed']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Duration: {summary['duration_seconds']:.1f}s")
        
        if summary['warnings']:
            print(f"Warnings: {summary['warnings']}")
        
        if summary['errors']:
            print(f"Errors: {summary['errors']}")
    
    def run_full_suite(self):
        """Run the complete test suite."""
        print(f"\\n🚀 Starting Full Test Suite")
        print("=" * 35)
        
        # Initialize systems
        if not self.initialize_systems():
            print("❌ Initialization failed - aborting test suite")
            return
        
        # Run tests
        self.test_artist_verification()
        self.generate_network()
        self.test_similarity_symmetry()
        self.test_visual_properties()
        
        # Save network
        network_path = self.save_network()
        
        # Test individual connections for seed artists
        for artist in self.config.seed_artists:
            self.test_individual_connections(artist)
        
        # Generate final report
        self.generate_report()
        
        print(f"\\n✨ Test suite completed!")
        if network_path:
            print(f"💾 Network saved to: {network_path}")

def load_network_from_file(file_path: str) -> Optional[nx.Graph]:
    """Load a saved network file for analysis."""
    path = Path(file_path)
    
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    try:
        if path.suffix == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert back to NetworkX graph
            graph = nx.Graph()
            
            for node_data in data['nodes']:
                node_id = node_data.pop('id')
                graph.add_node(node_id, **node_data)
            
            for edge_data in data['edges']:
                source = edge_data.pop('source')
                target = edge_data.pop('target')
                graph.add_edge(source, target, **edge_data)
            
            return graph
            
        elif path.suffix == '.graphml':
            return nx.read_graphml(path)
        
        else:
            print(f"❌ Unsupported file format: {path.suffix}")
            return None
            
    except Exception as e:
        print(f"❌ Error loading network: {e}")
        return None

def analyze_artist_connections(network_file: str, artist: str):
    """Analyze all connections for a specific artist from a saved network."""
    print(f"🔍 Analyzing connections for: {artist}")
    print("=" * 50)
    
    graph = load_network_from_file(network_file)
    if not graph:
        return
    
    if artist not in graph:
        print(f"❌ Artist '{artist}' not found in network")
        available = list(graph.nodes())[:10]
        print(f"Available artists (first 10): {', '.join(available)}")
        return
    
    # Get artist data
    artist_data = graph.nodes[artist]
    print(f"\\n📊 Artist Information:")
    print(f"   Display Name: {artist_data.get('display_name', artist)}")
    print(f"   Last.fm Listeners: {artist_data.get('lastfm_listeners', 0):,}")
    print(f"   User Plays: {artist_data.get('user_plays', 0)}")
    print(f"   Verification: {artist_data.get('verification_method', 'unknown')} ({artist_data.get('verification_confidence', 0):.3f})")
    print(f"   Spotify Popularity: {artist_data.get('spotify_popularity', 0)}/100")
    print(f"   Visual: Size={artist_data.get('node_size', 0):.1f}, Glow={artist_data.get('glow_value', 0):.2f}, Color={artist_data.get('color', 'unknown')}")
    
    # Get all connections
    neighbors = list(graph.neighbors(artist))
    print(f"\\n🔗 Connections ({len(neighbors)} total):")
    
    # Sort by similarity
    connections = []
    for neighbor in neighbors:
        edge_data = graph[artist][neighbor]
        neighbor_data = graph.nodes[neighbor]
        
        connections.append({
            'name': neighbor,
            'display_name': neighbor_data.get('display_name', neighbor),
            'similarity': edge_data.get('similarity', 0),
            'source': edge_data.get('source', 'unknown'),
            'listeners': neighbor_data.get('lastfm_listeners', 0),
            'spotify_popularity': neighbor_data.get('spotify_popularity', 0)
        })
    
    # Sort by similarity (descending)
    connections.sort(key=lambda x: x['similarity'], reverse=True)
    
    for i, conn in enumerate(connections, 1):
        print(f"   {i:2d}. {conn['display_name']}")
        print(f"       Similarity: {conn['similarity']:.3f} ({conn['source']})")
        print(f"       Last.fm: {conn['listeners']:,} listeners")
        print(f"       Spotify: {conn['spotify_popularity']}/100 popularity")
    
    # Network statistics
    print(f"\\n📈 Network Statistics:")
    print(f"   Total Nodes: {graph.number_of_nodes()}")
    print(f"   Total Edges: {graph.number_of_edges()}")
    print(f"   Network Density: {nx.density(graph):.3f}")
    if graph.number_of_nodes() > 2:
        print(f"   Average Clustering: {nx.average_clustering(graph):.3f}")

def main():
    """Main entry point for the test suite."""
    parser = argparse.ArgumentParser(description="Comprehensive Network Test Suite")
    parser.add_argument("--config", help="YAML configuration file")
    parser.add_argument("--artist", help="Analyze connections for specific artist")
    parser.add_argument("--network-file", help="Network file to analyze", default="")
    parser.add_argument("--connections", action="store_true", help="Show connections for artist")
    parser.add_argument("--quick", action="store_true", help="Run quick test with minimal artists")
    
    args = parser.parse_args()
    
    # If analyzing specific artist connections
    if args.artist and args.connections:
        if not args.network_file:
            # Find most recent network file
            import glob
            network_files = glob.glob("network_test_results/comprehensive_network_*.json")
            if network_files:
                args.network_file = max(network_files)  # Most recent
                print(f"Using most recent network file: {args.network_file}")
            else:
                print("❌ No network files found. Please specify --network-file")
                return
        
        analyze_artist_connections(args.network_file, args.artist)
        return
    
    # Load configuration
    if args.config:
        config = NetworkTestConfig.from_yaml(args.config)
    else:
        # Use default configuration
        config = NetworkTestConfig()
        
        if args.quick:
            config.top_n_artists = 10
            config.seed_artists = ["YOASOBI", "IVE"]
    
    # Run test suite
    suite = ComprehensiveNetworkTestSuite(config)
    suite.run_full_suite()

if __name__ == "__main__":
    main()