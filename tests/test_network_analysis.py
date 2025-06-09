"""
Test suite for network analysis functionality.
Tests co-listening calculations, network creation, and data structures.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import pandas as pd
import json
import shutil
from datetime import datetime, timedelta
from network_utils import ArtistNetworkAnalyzer, initialize_network_analyzer
from config_loader import AppConfig


class TestNetworkAnalysis(unittest.TestCase):
    """Test network analysis functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.test_cache_dir = "test_network_cache"
        
        # Create sample listening data
        cls.sample_data = cls._create_sample_data()
        
    def setUp(self):
        """Set up each test."""
        # Clean test cache
        if os.path.exists(self.test_cache_dir):
            shutil.rmtree(self.test_cache_dir)
            
        # Mock config for testing
        self.config = self._create_test_config()
        self.analyzer = ArtistNetworkAnalyzer(self.config)
        
    def tearDown(self):
        """Clean up after each test."""
        if os.path.exists(self.test_cache_dir):
            shutil.rmtree(self.test_cache_dir)
        
        # Clean up any test files
        test_files = ['test_network.json', 'artist_network.json']
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)
    
    @staticmethod
    def _create_sample_data():
        """Create sample listening data for testing."""
        # Create sample data spanning several days with artist clusters
        data = []
        artists = ['Taylor Swift', 'Paramore', 'IU', 'BLACKPINK', 'BTS']
        
        base_time = datetime(2024, 1, 1, 10, 0, 0)
        
        # Create listening sessions with some co-listening patterns
        for day in range(7):
            day_start = base_time + timedelta(days=day)
            
            # Morning session: Taylor Swift and Paramore (similar genres)
            for i in range(5):
                data.append({
                    'timestamp': day_start + timedelta(minutes=i*4),
                    'artist': 'Taylor Swift' if i % 2 == 0 else 'Paramore'
                })
            
            # Afternoon session: K-pop cluster
            afternoon = day_start + timedelta(hours=6)
            for i in range(8):
                artist = ['IU', 'BLACKPINK', 'BTS'][i % 3]
                data.append({
                    'timestamp': afternoon + timedelta(minutes=i*3),
                    'artist': artist
                })
            
            # Evening: Mixed listening
            evening = day_start + timedelta(hours=20)
            for i, artist in enumerate(artists):
                data.append({
                    'timestamp': evening + timedelta(minutes=i*10),
                    'artist': artist
                })
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def _create_test_config(self):
        """Create a mock config for testing."""
        test_cache_dir = self.test_cache_dir  # Capture in local variable
        
        class MockConfig:
            def get_lastfm_config(self):
                return {
                    'enabled': False,  # Disable for most tests
                    'api_key': '',
                    'api_secret': '',
                    'cache_dir': test_cache_dir
                }
            
            def get(self, section, key, fallback=None):
                return fallback
        
        return MockConfig()
    
    def test_analyzer_initialization(self):
        """Test that analyzer initializes correctly."""
        self.assertIsInstance(self.analyzer, ArtistNetworkAnalyzer)
        self.assertIsNone(self.analyzer.lastfm_api)  # Disabled in test config
        
    def test_co_listening_calculation_basic(self):
        """Test basic co-listening score calculation."""
        scores = self.analyzer.calculate_co_listening_scores(
            self.sample_data, 
            time_window_hours=1,
            min_co_occurrences=1
        )
        
        self.assertIsInstance(scores, dict)
        self.assertGreater(len(scores), 0)
        
        # Check that scores are between 0 and 1
        for score in scores.values():
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
        
        # Should find Taylor Swift - Paramore connection (they're played together)
        taylor_paramore_key = tuple(sorted(['Taylor Swift', 'Paramore']))
        self.assertIn(taylor_paramore_key, scores)
        
    def test_co_listening_time_window_sensitivity(self):
        """Test that time window affects co-listening detection."""
        # Short window
        scores_short = self.analyzer.calculate_co_listening_scores(
            self.sample_data, 
            time_window_hours=0.1  # 6 minutes
        )
        
        # Long window
        scores_long = self.analyzer.calculate_co_listening_scores(
            self.sample_data, 
            time_window_hours=12  # 12 hours
        )
        
        # Long window should detect more relationships
        self.assertGreaterEqual(len(scores_long), len(scores_short))
        
    def test_co_listening_empty_data(self):
        """Test co-listening with empty data."""
        empty_df = pd.DataFrame(columns=['artist'])
        empty_df.index = pd.DatetimeIndex([])
        
        scores = self.analyzer.calculate_co_listening_scores(empty_df)
        self.assertEqual(len(scores), 0)
        
    def test_co_listening_invalid_data(self):
        """Test co-listening with invalid data."""
        # DataFrame without datetime index
        invalid_df = pd.DataFrame({
            'artist': ['Taylor Swift', 'Paramore'],
            'other_col': [1, 2]
        })
        
        scores = self.analyzer.calculate_co_listening_scores(invalid_df)
        self.assertEqual(len(scores), 0)
        
    def test_network_data_creation_basic(self):
        """Test basic network data creation."""
        network_data = self.analyzer.create_network_data(
            self.sample_data,
            top_n_artists=5,
            include_lastfm=False,  # Only co-listening
            include_colistening=True
        )
        
        self.assertIn('nodes', network_data)
        self.assertIn('edges', network_data)
        self.assertIn('metadata', network_data)
        
        nodes = network_data['nodes']
        edges = network_data['edges']
        
        # Should have nodes for all artists
        self.assertEqual(len(nodes), 5)
        
        # Check node structure
        first_node = nodes[0]
        required_fields = ['id', 'name', 'play_count', 'rank', 'size', 'in_library']
        for field in required_fields:
            self.assertIn(field, first_node)
        
        # Should have some edges
        self.assertGreater(len(edges), 0)
        
        # Check edge structure
        if edges:
            first_edge = edges[0]
            required_edge_fields = ['source', 'target', 'weight', 'relationship_type']
            for field in required_edge_fields:
                self.assertIn(field, first_edge)
            
            # Weight should be valid
            self.assertGreaterEqual(first_edge['weight'], 0.0)
            self.assertLessEqual(first_edge['weight'], 1.0)
        
    def test_network_data_empty_input(self):
        """Test network creation with empty data."""
        empty_df = pd.DataFrame(columns=['artist'])
        empty_df.index = pd.DatetimeIndex([])
        
        network_data = self.analyzer.create_network_data(empty_df)
        
        self.assertEqual(len(network_data['nodes']), 0)
        self.assertEqual(len(network_data['edges']), 0)
        
    def test_network_data_filtering(self):
        """Test that network creation filters by play count."""
        # Set high threshold
        network_data = self.analyzer.create_network_data(
            self.sample_data,
            min_plays_threshold=20,  # High threshold
            include_lastfm=False
        )
        
        # Should have fewer or no nodes
        self.assertLessEqual(len(network_data['nodes']), 5)
        
        # All included artists should meet threshold
        for node in network_data['nodes']:
            self.assertGreaterEqual(node['play_count'], 20)
        
    def test_relationship_classification(self):
        """Test relationship type classification."""
        # Test different score combinations
        test_cases = [
            (0.8, 0.0, 'lastfm_only'),
            (0.0, 0.8, 'colistening_only'),
            (0.8, 0.8, 'both'),
            (0.05, 0.05, 'weak')
        ]
        
        for lastfm_score, colistening_score, expected_type in test_cases:
            result = self.analyzer._classify_relationship(lastfm_score, colistening_score)
            self.assertEqual(result, expected_type)
    
    def test_network_statistics(self):
        """Test network statistics calculation."""
        network_data = self.analyzer.create_network_data(
            self.sample_data,
            include_lastfm=False
        )
        
        stats = self.analyzer.get_network_statistics(network_data)
        
        required_stats = ['node_count', 'edge_count', 'density', 'avg_degree']
        for stat in required_stats:
            self.assertIn(stat, stats)
            self.assertIsInstance(stats[stat], (int, float))
        
        # Density should be between 0 and 1
        self.assertGreaterEqual(stats['density'], 0.0)
        self.assertLessEqual(stats['density'], 1.0)
        
    def test_save_and_load_network_data(self):
        """Test saving and loading network data."""
        network_data = self.analyzer.create_network_data(
            self.sample_data,
            include_lastfm=False
        )
        
        # Save data
        filepath = self.analyzer.save_network_data(network_data, 'test_network.json')
        self.assertTrue(os.path.exists(filepath))
        
        # Load and verify
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(len(loaded_data['nodes']), len(network_data['nodes']))
        self.assertEqual(len(loaded_data['edges']), len(network_data['edges']))
        
    def test_convenience_functions(self):
        """Test module-level convenience functions."""
        # Test analyzer initialization
        try:
            from config_loader import AppConfig
            config = AppConfig('configurations.txt')
            analyzer = initialize_network_analyzer('configurations.txt')
            self.assertIsInstance(analyzer, ArtistNetworkAnalyzer)
        except FileNotFoundError:
            # Skip if config file doesn't exist
            pass
    
    def test_large_dataset_performance(self):
        """Test performance with larger dataset."""
        # Create larger sample data
        large_data = []
        artists = ['Artist' + str(i) for i in range(20)]
        base_time = datetime(2024, 1, 1)
        
        for i in range(1000):  # 1000 plays
            timestamp = base_time + timedelta(minutes=i)
            artist = artists[i % len(artists)]
            large_data.append({'timestamp': timestamp, 'artist': artist})
        
        large_df = pd.DataFrame(large_data)
        large_df['timestamp'] = pd.to_datetime(large_df['timestamp'])
        large_df.set_index('timestamp', inplace=True)
        
        # Should complete without timeout
        import time
        start_time = time.time()
        
        scores = self.analyzer.calculate_co_listening_scores(large_df, time_window_hours=1)
        
        end_time = time.time()
        
        # Should complete in reasonable time (less than 30 seconds)
        self.assertLess(end_time - start_time, 30)
        self.assertIsInstance(scores, dict)


class TestNetworkDataStructure(unittest.TestCase):
    """Test the structure and validity of network data."""
    
    def test_node_data_completeness(self):
        """Test that nodes have all required fields."""
        sample_data = TestNetworkAnalysis._create_sample_data()
        
        # Create mock config directly
        test_cache_dir = "test_network_cache"
        class MockConfig:
            def get_lastfm_config(self):
                return {
                    'enabled': False,
                    'api_key': '',
                    'api_secret': '',
                    'cache_dir': test_cache_dir
                }
            def get(self, section, key, fallback=None):
                return fallback
        
        config = MockConfig()
        analyzer = ArtistNetworkAnalyzer(config)
        
        network_data = analyzer.create_network_data(sample_data, include_lastfm=False)
        
        required_node_fields = ['id', 'name', 'play_count', 'rank', 'size', 'in_library']
        
        for node in network_data['nodes']:
            for field in required_node_fields:
                self.assertIn(field, node, f"Node missing field: {field}")
                
            # Check data types
            self.assertIsInstance(node['play_count'], int)
            self.assertIsInstance(node['rank'], int)
            self.assertIsInstance(node['in_library'], bool)
    
    def test_edge_data_completeness(self):
        """Test that edges have all required fields."""
        sample_data = TestNetworkAnalysis._create_sample_data()
        
        # Create mock config directly
        test_cache_dir = "test_network_cache"
        class MockConfig:
            def get_lastfm_config(self):
                return {
                    'enabled': False,
                    'api_key': '',
                    'api_secret': '',
                    'cache_dir': test_cache_dir
                }
            def get(self, section, key, fallback=None):
                return fallback
        
        config = MockConfig()
        analyzer = ArtistNetworkAnalyzer(config)
        
        network_data = analyzer.create_network_data(sample_data, include_lastfm=False)
        
        required_edge_fields = ['source', 'target', 'weight', 'relationship_type']
        
        for edge in network_data['edges']:
            for field in required_edge_fields:
                self.assertIn(field, edge, f"Edge missing field: {field}")
                
            # Check data types and values
            self.assertIsInstance(edge['weight'], (int, float))
            self.assertGreaterEqual(edge['weight'], 0.0)
            self.assertLessEqual(edge['weight'], 1.0)
            self.assertIn(edge['relationship_type'], 
                         ['lastfm_only', 'colistening_only', 'both', 'weak'])


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)