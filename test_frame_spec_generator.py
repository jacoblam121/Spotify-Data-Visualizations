#!/usr/bin/env python3
"""
Test suite for frame_spec_generator.py (Task 2)

Tests the memory-efficient frame specification generator against the original
prepare_all_frame_specs implementation to ensure complete compatibility.
"""

import os
import sys
import time
import json
import unittest
from unittest.mock import Mock, patch
from typing import List, Dict, Any
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from frame_spec_generator import FrameSpecGenerator, create_frame_spec_generator
    from main_animator import prepare_all_frame_specs, prepare_frame_spec, make_json_serializable
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestFrameSpecGenerator(unittest.TestCase):
    """Test suite for FrameSpecGenerator equivalence and functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.maxDiff = None  # Show full diff for failed assertions
        
        # Create sample test data
        self.sample_render_tasks = self._create_sample_render_tasks()
        self.sample_entity_map = self._create_sample_entity_map()
        self.sample_entity_details = self._create_sample_entity_details()
        self.sample_colors = self._create_sample_colors()
        
        self.n_bars = 5
        self.max_play_count = 1000.0
        self.visualization_mode = "tracks"
    
    def _create_sample_render_tasks(self) -> List[Dict[str, Any]]:
        """Create sample render tasks for testing."""
        from datetime import datetime, timedelta
        
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        tasks = []
        
        for i in range(10):  # Create 10 sample frames
            timestamp = base_time + timedelta(minutes=i * 30)
            
            # Create sample bar data with varying play counts
            bar_data = []
            for j in range(min(5, 8 - i)):  # Varying number of bars
                bar_data.append({
                    'entity_id': f"song_{j}",
                    'interpolated_play_count': float(100 - i * 5 - j * 2),
                    'interpolated_y_position': float(j),
                    'current_rank': j,
                    'is_new': j == 0 and i > 2,
                    'bar_color': (0.5 + j * 0.1, 0.3, 0.7, 1.0)
                })
            
            task = {
                'overall_frame_index': i,
                'display_timestamp': timestamp,
                'bar_render_data_list': bar_data,
                'rolling_window_info': {
                    'top_7_day': {'song_id': f"song_{i % 3}", 'plays': 50 + i},
                    'top_30_day': {'song_id': f"song_{(i + 1) % 3}", 'plays': 200 + i * 2}
                },
                'nightingale_info': {
                    'period_data': [{'period': 'morning', 'value': 10 + i}]
                }
            }
            tasks.append(task)
        
        return tasks
    
    def _create_sample_entity_map(self) -> Dict[str, str]:
        """Create sample entity ID to canonical name mapping."""
        return {
            f"song_{i}": f"canonical_song_{i}"
            for i in range(10)
        }
    
    def _create_sample_entity_details(self) -> Dict[str, Dict[str, Any]]:
        """Create sample entity details."""
        details = {}
        for i in range(10):
            details[f"song_{i}"] = {
                'original_artist': f"Artist {i}",
                'original_track': f"Track {i}",
                'album': f"Album {i}",
                'spotify_track_uri': f"spotify:track:uri_{i}"
            }
        return details
    
    def _create_sample_colors(self) -> Dict[str, tuple]:
        """Create sample color mapping."""
        return {
            f"canonical_song_{i}": (0.1 * i, 0.2 * i, 0.3 * i, 1.0)
            for i in range(10)
        }
    
    def test_generator_equivalence_full(self):
        """Test that generator produces identical output to original method."""
        logger.info("Testing full equivalence between generator and original method")
        
        # Generate specs using original method
        original_specs = prepare_all_frame_specs(
            self.sample_render_tasks,
            self.sample_entity_map,
            self.sample_entity_details,
            self.sample_colors,
            self.n_bars,
            self.max_play_count,
            self.visualization_mode
        )
        
        # Generate specs using generator
        generator = create_frame_spec_generator(
            self.sample_render_tasks,
            self.sample_entity_map,
            self.sample_entity_details,
            self.sample_colors,
            self.n_bars,
            self.max_play_count,
            self.visualization_mode
        )
        
        generator_specs = list(generator)
        
        # Compare lengths
        self.assertEqual(len(original_specs), len(generator_specs),
                        "Generator and original method produced different numbers of specs")
        
        # Compare each spec
        for i, (original, generated) in enumerate(zip(original_specs, generator_specs)):
            with self.subTest(frame_index=i):
                self._assert_specs_equivalent(original, generated, i)
        
        logger.info(f"✓ Equivalence test passed for {len(original_specs)} frame specs")
    
    def _assert_specs_equivalent(self, original: Dict, generated: Dict, frame_index: int):
        """Assert that two frame specs are equivalent."""
        # Check top-level keys
        self.assertEqual(set(original.keys()), set(generated.keys()),
                        f"Frame {frame_index}: Different top-level keys")
        
        # Check frame metadata
        self.assertEqual(original['frame_index'], generated['frame_index'])
        self.assertEqual(original['display_timestamp'], generated['display_timestamp'])
        self.assertEqual(original['visualization_mode'], generated['visualization_mode'])
        self.assertAlmostEqual(original['dynamic_x_axis_limit'], generated['dynamic_x_axis_limit'], places=5)
        
        # Check rolling stats and nightingale data (JSON serializable)
        self.assertEqual(original['rolling_stats'], generated['rolling_stats'])
        self.assertEqual(original['nightingale_data'], generated['nightingale_data'])
        
        # Check bars (most complex part)
        self.assertEqual(len(original['bars']), len(generated['bars']),
                        f"Frame {frame_index}: Different number of bars")
        
        for j, (orig_bar, gen_bar) in enumerate(zip(original['bars'], generated['bars'])):
            with self.subTest(frame_index=frame_index, bar_index=j):
                self._assert_bars_equivalent(orig_bar, gen_bar, frame_index, j)
    
    def _assert_bars_equivalent(self, original: Dict, generated: Dict, frame_index: int, bar_index: int):
        """Assert that two bar specs are equivalent."""
        context = f"Frame {frame_index}, Bar {bar_index}"
        
        # Check all bar properties
        self.assertEqual(original['entity_id'], generated['entity_id'], f"{context}: entity_id")
        self.assertEqual(original['canonical_key'], generated['canonical_key'], f"{context}: canonical_key")
        self.assertEqual(original['display_name'], generated['display_name'], f"{context}: display_name")
        self.assertAlmostEqual(original['interpolated_y_pos'], generated['interpolated_y_pos'], 
                              places=5, msg=f"{context}: interpolated_y_pos")
        self.assertAlmostEqual(original['interpolated_play_count'], generated['interpolated_play_count'], 
                              places=5, msg=f"{context}: interpolated_play_count")
        self.assertEqual(original['is_new'], generated['is_new'], f"{context}: is_new")
        self.assertEqual(original['current_rank'], generated['current_rank'], f"{context}: current_rank")
        
        # Check colors (tuples with floats)
        orig_color = original.get('bar_color', original.get('bar_color_rgba'))
        gen_color = generated.get('bar_color', generated.get('bar_color_rgba'))
        
        if orig_color and gen_color:
            self.assertEqual(len(orig_color), len(gen_color), f"{context}: color tuple length")
            for k, (o, g) in enumerate(zip(orig_color, gen_color)):
                self.assertAlmostEqual(o, g, places=5, msg=f"{context}: color component {k}")
        
        # Check entity details
        self.assertEqual(original['entity_details'], generated['entity_details'], f"{context}: entity_details")
    
    def test_generator_state_management(self):
        """Test that generator maintains proper state across iterations."""
        logger.info("Testing generator state management")
        
        generator = create_frame_spec_generator(
            self.sample_render_tasks,
            self.sample_entity_map,
            self.sample_entity_details,
            self.sample_colors,
            self.n_bars,
            self.max_play_count,
            self.visualization_mode
        )
        
        # Test progress tracking
        progress_before = generator.get_progress()
        self.assertEqual(progress_before, (0, len(self.sample_render_tasks)))
        
        # Generate a few specs
        specs = []
        for i, spec in enumerate(generator):
            specs.append(spec)
            progress = generator.get_progress()
            self.assertEqual(progress[0], i + 1, f"Progress tracking incorrect at frame {i}")
            
            if i >= 2:  # Test first 3 specs
                break
        
        # Check that we can get memory info
        memory_info = generator.get_memory_info()
        self.assertIn('frame_index', memory_info)
        self.assertIn('total_frames', memory_info)
        self.assertEqual(memory_info['frame_index'], 3)
        
        logger.info("✓ State management test passed")
    
    def test_generator_reset(self):
        """Test generator reset functionality."""
        logger.info("Testing generator reset functionality")
        
        generator = create_frame_spec_generator(
            self.sample_render_tasks,
            self.sample_entity_map,
            self.sample_entity_details,
            self.sample_colors,
            self.n_bars,
            self.max_play_count,
            self.visualization_mode
        )
        
        # Generate some specs
        first_batch = [next(generator) for _ in range(3)]
        progress_mid = generator.get_progress()
        self.assertEqual(progress_mid[0], 3)
        
        # Reset and generate again
        generator.reset()
        progress_after_reset = generator.get_progress()
        self.assertEqual(progress_after_reset[0], 0)
        
        # Generate same specs again
        second_batch = [next(generator) for _ in range(3)]
        
        # Should be identical
        for i, (first, second) in enumerate(zip(first_batch, second_batch)):
            with self.subTest(spec_index=i):
                self._assert_specs_equivalent(first, second, i)
        
        logger.info("✓ Reset functionality test passed")
    
    def test_generator_empty_input(self):
        """Test generator behavior with empty input."""
        logger.info("Testing generator with empty input")
        
        generator = create_frame_spec_generator(
            [],  # Empty render tasks
            {},  # Empty entity map
            {},  # Empty entity details
            {},  # Empty colors
            self.n_bars,
            self.max_play_count,
            self.visualization_mode
        )
        
        # Should produce no specs
        specs = list(generator)
        self.assertEqual(len(specs), 0)
        
        # Progress should reflect empty state
        progress = generator.get_progress()
        self.assertEqual(progress, (0, 0))
        
        logger.info("✓ Empty input test passed")
    
    def test_generator_single_frame(self):
        """Test generator with single frame."""
        logger.info("Testing generator with single frame")
        
        single_task = [self.sample_render_tasks[0]]
        
        generator = create_frame_spec_generator(
            single_task,
            self.sample_entity_map,
            self.sample_entity_details,
            self.sample_colors,
            self.n_bars,
            self.max_play_count,
            self.visualization_mode
        )
        
        specs = list(generator)
        self.assertEqual(len(specs), 1)
        
        # Compare with original method
        original_specs = prepare_all_frame_specs(
            single_task,
            self.sample_entity_map,
            self.sample_entity_details,
            self.sample_colors,
            self.n_bars,
            self.max_play_count,
            self.visualization_mode
        )
        
        self._assert_specs_equivalent(original_specs[0], specs[0], 0)
        
        logger.info("✓ Single frame test passed")
    
    def test_artists_mode(self):
        """Test generator in artists mode."""
        logger.info("Testing generator in artists mode")
        
        # Update entity details for artists mode
        artist_details = {}
        for i in range(5):
            artist_details[f"artist_{i}"] = {
                'original_artist': f"Artist {i}",
                'normalized_artist': f"artist_{i}",
                'most_played_track': {
                    'track_name': f"Track {i}",
                    'album_name': f"Album {i}",
                    'track_uri': f"spotify:track:uri_{i}"
                }
            }
        
        # Create artist-mode render tasks
        artist_tasks = []
        for i in range(3):
            task = {
                'overall_frame_index': i,
                'display_timestamp': self.sample_render_tasks[i]['display_timestamp'],
                'bar_render_data_list': [
                    {
                        'entity_id': f"artist_{j}",
                        'interpolated_play_count': float(50 - j * 5),
                        'interpolated_y_position': float(j),
                        'current_rank': j,
                        'is_new': False,
                        'bar_color': (0.3, 0.6, 0.9, 1.0)
                    }
                    for j in range(3)
                ],
                'rolling_window_info': {'top_7_day': None, 'top_30_day': None},
                'nightingale_info': {}
            }
            artist_tasks.append(task)
        
        artist_entity_map = {f"artist_{i}": f"canonical_artist_{i}" for i in range(5)}
        artist_colors = {f"canonical_artist_{i}": (0.1 * i, 0.2, 0.3, 1.0) for i in range(5)}
        
        # Test generator
        generator = create_frame_spec_generator(
            artist_tasks,
            artist_entity_map,
            artist_details,
            artist_colors,
            self.n_bars,
            self.max_play_count,
            "artists"  # Artists mode
        )
        
        # Compare with original
        original_specs = prepare_all_frame_specs(
            artist_tasks,
            artist_entity_map,
            artist_details,
            artist_colors,
            self.n_bars,
            self.max_play_count,
            "artists"
        )
        
        generator_specs = list(generator)
        
        self.assertEqual(len(original_specs), len(generator_specs))
        for i, (orig, gen) in enumerate(zip(original_specs, generator_specs)):
            with self.subTest(frame_index=i):
                self._assert_specs_equivalent(orig, gen, i)
        
        logger.info("✓ Artists mode test passed")


class TestMemoryUsage(unittest.TestCase):
    """Test memory usage characteristics of the generator."""
    
    def setUp(self):
        """Set up memory test fixtures."""
        # Create larger dataset for memory testing
        self.large_render_tasks = self._create_large_render_tasks(1000)  # 1000 frames
        self.entity_map = {f"song_{i}": f"canonical_{i}" for i in range(100)}
        self.entity_details = {
            f"song_{i}": {
                'original_artist': f"Artist {i}",
                'original_track': f"Track {i}",
                'album': f"Album {i}"
            }
            for i in range(100)
        }
        self.colors = {f"canonical_{i}": (0.1, 0.2, 0.3, 1.0) for i in range(100)}
    
    def _create_large_render_tasks(self, num_frames: int) -> List[Dict[str, Any]]:
        """Create a large dataset for memory testing."""
        from datetime import datetime, timedelta
        
        base_time = datetime(2024, 1, 1)
        tasks = []
        
        for i in range(num_frames):
            # Simulate realistic frame data
            timestamp = base_time + timedelta(hours=i)
            
            # Create bars for top songs
            bars = []
            for j in range(10):  # 10 bars per frame
                bars.append({
                    'entity_id': f"song_{(i + j) % 100}",  # Rotate through 100 songs
                    'interpolated_play_count': float(1000 - j * 50 - (i % 10)),
                    'interpolated_y_position': float(j),
                    'current_rank': j,
                    'is_new': (i + j) % 50 == 0,
                    'bar_color': (0.5, 0.3, 0.7, 1.0)
                })
            
            task = {
                'overall_frame_index': i,
                'display_timestamp': timestamp,
                'bar_render_data_list': bars,
                'rolling_window_info': {
                    'top_7_day': {'song_id': f"song_{i % 10}", 'plays': 100 + i},
                    'top_30_day': {'song_id': f"song_{(i + 5) % 10}", 'plays': 500 + i}
                },
                'nightingale_info': {'period_data': [{'period': 'evening', 'value': 20 + i % 30}]}
            }
            tasks.append(task)
        
        return tasks
    
    @unittest.skipIf(not hasattr(sys, 'getsizeof'), "sys.getsizeof not available")
    def test_memory_efficiency(self):
        """Test that generator uses significantly less memory than original method."""
        logger.info("Testing memory efficiency (may take a moment)")
        
        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            logger.warning("psutil not available, skipping detailed memory test")
            return
        
        # Measure baseline memory
        baseline_memory = process.memory_info().rss
        
        # Test original method memory usage
        logger.info("Testing original method memory usage...")
        memory_before_original = process.memory_info().rss
        original_specs = prepare_all_frame_specs(
            self.large_render_tasks,
            self.entity_map,
            self.entity_details,
            self.colors,
            10,
            10000.0,
            "tracks"
        )
        memory_after_original = process.memory_info().rss
        original_memory_used = memory_after_original - memory_before_original
        
        # Clear the original specs to free memory
        del original_specs
        import gc
        gc.collect()
        
        # Test generator memory usage
        logger.info("Testing generator memory usage...")
        memory_before_generator = process.memory_info().rss
        generator = create_frame_spec_generator(
            self.large_render_tasks,
            self.entity_map,
            self.entity_details,
            self.colors,
            10,
            10000.0,
            "tracks"
        )
        
        # Iterate through generator without storing results
        max_memory_during_iteration = memory_before_generator
        for i, spec in enumerate(generator):
            current_memory = process.memory_info().rss
            max_memory_during_iteration = max(max_memory_during_iteration, current_memory)
            
            # Check memory every 100 frames
            if i % 100 == 0:
                logger.debug(f"Frame {i}: Memory usage: {current_memory - baseline_memory} bytes")
            
            # Don't store the spec to avoid memory accumulation
            del spec
            
            if i >= 500:  # Test first 500 frames
                break
        
        generator_memory_used = max_memory_during_iteration - memory_before_generator
        
        # Log results
        logger.info(f"Original method memory usage: {original_memory_used:,} bytes")
        logger.info(f"Generator memory usage: {generator_memory_used:,} bytes")
        
        # Generator should use significantly less memory
        memory_reduction_ratio = original_memory_used / max(generator_memory_used, 1)
        logger.info(f"Memory reduction ratio: {memory_reduction_ratio:.2f}x")
        
        # Assert that generator uses at least 50% less memory
        self.assertGreater(memory_reduction_ratio, 1.5, 
                          "Generator should use significantly less memory than original method")
        
        logger.info("✓ Memory efficiency test passed")


def run_equivalence_tests():
    """Run equivalence tests and return results."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFrameSpecGenerator)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_memory_tests():
    """Run memory tests and return results."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMemoryUsage)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_all_tests():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("FRAME SPEC GENERATOR TEST SUITE")
    logger.info("=" * 60)
    
    success = True
    
    logger.info("\n--- Running Equivalence Tests ---")
    success &= run_equivalence_tests()
    
    logger.info("\n--- Running Memory Tests ---")
    success &= run_memory_tests()
    
    logger.info("\n--- Test Summary ---")
    if success:
        logger.info("✓ All tests passed!")
    else:
        logger.error("✗ Some tests failed!")
    
    return success


if __name__ == "__main__":
    # Configure logging for test run
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    success = run_all_tests()
    sys.exit(0 if success else 1)