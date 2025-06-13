#!/usr/bin/env python3
"""
Automated Test Suite for Phase 0 - Network Visualization Foundation
Comprehensive tests for ID migration, data structure, and enhancement systems.
"""

import unittest
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from id_migration_system import IDMigrationSystem, IDType, ArtistID
from create_id_mapping import create_enhanced_network_with_stable_ids, add_d3js_visualization_properties

class TestIDMigrationSystem(unittest.TestCase):
    """Test the ID migration system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.migration_system = IDMigrationSystem()
        
    def test_normalize_artist_name(self):
        """Test artist name normalization."""
        # Test basic normalization
        self.assertEqual(
            self.migration_system.normalize_artist_name("Taylor Swift"),
            "taylor swift"
        )
        
        # Test parenthetical removal
        self.assertEqual(
            self.migration_system.normalize_artist_name("TWICE (트와이스)"),
            "twice"
        )
        
        # Test "The" prefix removal
        self.assertEqual(
            self.migration_system.normalize_artist_name("The Killers"),
            "killers"
        )
        
        # Test special character handling
        normalized = self.migration_system.normalize_artist_name("Sigur Rós")
        # Should remove diacritics and normalize
        self.assertIn("sigur", normalized.lower())
        self.assertNotIn("ó", normalized)
        
    def test_create_local_hash(self):
        """Test local hash ID creation."""
        hash1 = self.migration_system.create_local_hash("Taylor Swift")
        hash2 = self.migration_system.create_local_hash("taylor swift")
        hash3 = self.migration_system.create_local_hash("Different Artist")
        
        # Same normalized name should produce same hash
        self.assertEqual(hash1, hash2)
        
        # Different names should produce different hashes
        self.assertNotEqual(hash1, hash3)
        
        # Hash should be 16 characters
        self.assertEqual(len(hash1), 16)
        
    def test_extract_spotify_id(self):
        """Test Spotify ID extraction."""
        # Test successful extraction
        artist_data = {
            'artist_name': 'Taylor Swift',
            'spotify_data': {
                'spotify_artist_id': '06HL4z0CvFAxyc27GXpf02',
                'name': 'Taylor Swift',
                'popularity': 98
            }
        }
        
        result = self.migration_system.extract_spotify_id(artist_data)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, '06HL4z0CvFAxyc27GXpf02')
        self.assertEqual(result.type, IDType.SPOTIFY)
        self.assertEqual(result.confidence, 0.9)
        
        # Test missing Spotify data
        artist_data_no_spotify = {
            'artist_name': 'Unknown Artist',
            'spotify_data': None
        }
        
        result = self.migration_system.extract_spotify_id(artist_data_no_spotify)
        self.assertIsNone(result)
        
    def test_migrate_network_data(self):
        """Test full network migration."""
        sample_network = {
            'nodes': [
                {
                    'id': 'taylor swift',
                    'name': 'Taylor Swift',
                    'spotify_id': '06HL4z0CvFAxyc27GXpf02',
                    'spotify_popularity': 98,
                    'lastfm_listeners': 5160232
                },
                {
                    'id': 'unknown artist',
                    'name': 'Unknown Artist',
                    'lastfm_listeners': 1000
                }
            ],
            'edges': [
                {
                    'source': 'taylor swift',
                    'target': 'unknown artist',
                    'weight': 0.5
                }
            ],
            'metadata': {}
        }
        
        migrated = self.migration_system.migrate_network_data(sample_network)
        
        # Check nodes migrated
        self.assertEqual(len(migrated['nodes']), 2)
        
        # Check first node has Spotify ID
        taylor_node = migrated['nodes'][0]
        self.assertTrue(taylor_node['id'].startswith('spotify:'))
        self.assertEqual(taylor_node['id_type'], 'spotify')
        self.assertEqual(taylor_node['id_confidence'], 0.9)
        
        # Check second node has local hash
        unknown_node = migrated['nodes'][1]
        self.assertTrue(unknown_node['id'].startswith('local:'))
        self.assertEqual(unknown_node['id_type'], 'local')
        
        # Check edges updated
        self.assertEqual(len(migrated['edges']), 1)
        edge = migrated['edges'][0]
        self.assertTrue(edge['source'].startswith('spotify:'))
        self.assertTrue(edge['target'].startswith('local:'))
        
        # Check metadata
        self.assertIn('id_migration', migrated['metadata'])
        migration_info = migrated['metadata']['id_migration']
        self.assertEqual(migration_info['id_types']['spotify'], 1)
        self.assertEqual(migration_info['id_types']['local_hash'], 1)

class TestVisualizationProperties(unittest.TestCase):
    """Test D3.js visualization property enhancement."""
    
    def test_add_visualization_properties(self):
        """Test adding visualization properties to network data."""
        network_data = {
            'nodes': [
                {
                    'id': 'spotify:06HL4z0CvFAxyc27GXpf02',
                    'name': 'Taylor Swift',
                    'spotify_followers': 138794730,
                    'spotify_popularity': 98,
                    'lastfm_listeners': 5160232,
                    'play_count': 5216,
                    'genres_spotify': ['pop'],
                    'photo_url': 'https://example.com/taylor.jpg'
                },
                {
                    'id': 'spotify:74XFHRwlV6OrjEM0A2NCMF',
                    'name': 'Paramore',
                    'spotify_followers': 9466054,
                    'spotify_popularity': 82,
                    'lastfm_listeners': 4779115,
                    'play_count': 3460,
                    'genres_spotify': ['pop punk'],
                    'photo_url': 'https://example.com/paramore.jpg'
                }
            ],
            'edges': [],
            'metadata': {}
        }
        
        enhanced = add_d3js_visualization_properties(network_data)
        
        # Check visualization properties added
        for node in enhanced['nodes']:
            self.assertIn('viz', node)
            viz = node['viz']
            
            # Check required viz properties
            self.assertIn('radius', viz)
            self.assertIn('size_score', viz)
            self.assertIn('color', viz)
            self.assertIn('primary_genre', viz)
            self.assertIn('image_url', viz)
            self.assertIn('sizing_metric', viz)
            self.assertIn('sizing_value', viz)
            
            # Check radius is reasonable
            self.assertGreaterEqual(viz['radius'], 8)  # MIN_RADIUS
            self.assertLessEqual(viz['radius'], 45)    # MAX_RADIUS
            
            # Check size_score is normalized
            self.assertGreaterEqual(viz['size_score'], 0.0)
            self.assertLessEqual(viz['size_score'], 1.0)
            
            # Check color is hex
            self.assertTrue(viz['color'].startswith('#'))
            self.assertEqual(len(viz['color']), 7)
        
        # Taylor Swift should have larger radius than Paramore (more followers)
        taylor_radius = enhanced['nodes'][0]['viz']['radius']
        paramore_radius = enhanced['nodes'][1]['viz']['radius']
        self.assertGreater(taylor_radius, paramore_radius)
        
        # Check metadata
        self.assertIn('visualization', enhanced['metadata'])
        viz_meta = enhanced['metadata']['visualization']
        self.assertIn('enhanced_date', viz_meta)
        self.assertIn('size_range', viz_meta)
        self.assertIn('sizing_algorithm', viz_meta)

class TestNetworkGeneration(unittest.TestCase):
    """Test end-to-end network generation (requires real data)."""
    
    def setUp(self):
        """Check if we can run these tests."""
        self.can_test_real_data = True
        try:
            from data_processor import clean_and_filter_data
            from config_loader import AppConfig
            
            # Try to load config from parent directory
            config_path = os.path.join(os.path.dirname(os.getcwd()), 'configurations.txt')
            if os.path.exists(config_path):
                config = AppConfig(config_path)
                self.config = config
            else:
                raise FileNotFoundError("Configuration file not found")
        except Exception as e:
            self.can_test_real_data = False
            self.skipTest(f"Cannot test with real data: {e}")
    
    def test_small_network_generation(self):
        """Test generating a small network (5 artists)."""
        if not self.can_test_real_data:
            self.skipTest("Real data not available")
        
        # This is an integration test that requires the full pipeline
        try:
            # Change to parent directory for proper imports
            original_cwd = os.getcwd()
            os.chdir(os.path.dirname(os.getcwd()))
            
            result = create_enhanced_network_with_stable_ids(
                top_n_artists=5,
                output_file='test_integration_5artists.json'
            )
            
            # Change back
            os.chdir(original_cwd)
            
            self.assertIsNotNone(result)
            self.assertIn('nodes', result)
            self.assertIn('edges', result)
            self.assertIn('metadata', result)
            
            # Check that we got nodes
            self.assertGreater(len(result['nodes']), 0)
            
            # Check nodes have required properties
            for node in result['nodes']:
                self.assertIn('id', node)
                self.assertIn('viz', node)
                self.assertIn('id_type', node)
                self.assertIn('id_confidence', node)
                
                # Check stable ID format
                self.assertTrue(
                    node['id'].startswith('spotify:') or 
                    node['id'].startswith('mbid:') or 
                    node['id'].startswith('local:')
                )
            
            # Cleanup
            cleanup_files = ['test_integration_5artists.json', 'tests_phase_0/test_integration_5artists.json']
            for file_path in cleanup_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                
        except Exception as e:
            self.fail(f"Network generation failed: {e}")

class TestDataValidation(unittest.TestCase):
    """Test data validation and quality checks."""
    
    def test_spotify_id_format(self):
        """Test Spotify ID format validation."""
        valid_ids = [
            'spotify:06HL4z0CvFAxyc27GXpf02',
            'mbid:a761d515-341a-4543-94a7-c67319974f33',
            'local:3641ffe8a220d6d2'
        ]
        
        invalid_ids = [
            'invalid_format',
            'spotify:',
            'mbid:',
            'local:',
            '06HL4z0CvFAxyc27GXpf02'  # Missing prefix
        ]
        
        def is_valid_id(id_str):
            return (
                id_str.startswith('spotify:') and len(id_str) > 8 or
                id_str.startswith('mbid:') and len(id_str) > 5 or
                id_str.startswith('local:') and len(id_str) > 6
            )
        
        for valid_id in valid_ids:
            self.assertTrue(is_valid_id(valid_id), f"Should be valid: {valid_id}")
        
        for invalid_id in invalid_ids:
            self.assertFalse(is_valid_id(invalid_id), f"Should be invalid: {invalid_id}")
    
    def test_network_schema_validation(self):
        """Test network data schema validation."""
        valid_network = {
            'nodes': [
                {
                    'id': 'spotify:06HL4z0CvFAxyc27GXpf02',
                    'name': 'Taylor Swift',
                    'id_type': 'spotify',
                    'id_confidence': 0.9,
                    'canonical_name': 'Taylor Swift',
                    'viz': {
                        'radius': 45.0,
                        'size_score': 1.0,
                        'color': '#DDA0DD',
                        'primary_genre': 'pop',
                        'image_url': 'https://example.com/image.jpg',
                        'sizing_metric': 'spotify_followers',
                        'sizing_value': 138794730
                    }
                }
            ],
            'edges': [],
            'metadata': {
                'id_migration': {
                    'total_artists': 1,
                    'id_types': {
                        'spotify': 1,
                        'musicbrainz': 0,
                        'local_hash': 0
                    }
                },
                'visualization': {
                    'enhanced_date': '2024-12-06T18:00:00',
                    'sizing_algorithm': 'spotify_emphasis_sqrt'
                }
            }
        }
        
        # Test schema validation function
        def validate_network_schema(network):
            errors = []
            
            # Check top-level structure
            required_keys = ['nodes', 'edges', 'metadata']
            for key in required_keys:
                if key not in network:
                    errors.append(f"Missing required key: {key}")
            
            # Check nodes
            if 'nodes' in network:
                for i, node in enumerate(network['nodes']):
                    required_node_keys = ['id', 'name', 'id_type', 'viz']
                    for key in required_node_keys:
                        if key not in node:
                            errors.append(f"Node {i} missing required key: {key}")
                    
                    # Check viz properties
                    if 'viz' in node:
                        required_viz_keys = ['radius', 'size_score', 'color']
                        for key in required_viz_keys:
                            if key not in node['viz']:
                                errors.append(f"Node {i} viz missing key: {key}")
            
            return errors
        
        errors = validate_network_schema(valid_network)
        self.assertEqual(len(errors), 0, f"Valid network should have no errors: {errors}")
        
        # Test invalid network
        invalid_network = {'nodes': [{'id': 'test'}]}  # Missing required fields
        errors = validate_network_schema(invalid_network)
        self.assertGreater(len(errors), 0, "Invalid network should have errors")

def run_automated_tests():
    """Run all automated tests and return results."""
    print("🧪 Running Automated Phase 0 Tests")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestIDMigrationSystem,
        TestVisualizationProperties,
        TestNetworkGeneration,
        TestDataValidation
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Summary
    print(f"\\n📊 Test Results:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback.split('\\n')[-2]}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print(f"\\n✅ All automated tests passed!")
    else:
        print(f"\\n❌ Some tests failed - check issues above")
    
    return success

if __name__ == "__main__":
    success = run_automated_tests()
    sys.exit(0 if success else 1)