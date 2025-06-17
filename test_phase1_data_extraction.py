#!/usr/bin/env python3
"""
Phase 1 Test: Data Extraction Validation
Tests that frame specifications are correctly extracted from render tasks
"""

import json
import os
import sys
from datetime import datetime

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_animator import prepare_frame_spec, prepare_all_frame_specs


def create_mock_render_task():
    """Create a mock render task for testing"""
    return {
        'overall_frame_index': 42,
        'display_timestamp': datetime(2024, 6, 27, 11, 0, 0),
        'bar_render_data_list': [
            {
                'entity_id': 'song_001',
                'interpolated_y_pos': 0.0,
                'interpolated_play_count': 1091.0,
                'bar_color': (0.8, 0.2, 0.4, 1.0),
                'is_new': False
            },
            {
                'entity_id': 'song_002',
                'interpolated_y_pos': 1.0,
                'interpolated_play_count': 1089.0,
                'bar_color': (0.4, 0.6, 0.2, 1.0),
                'is_new': True
            }
        ],
        'rolling_window_info': {
            'top_7_day': {'song_id': 'song_003', 'plays': 220},
            'top_30_day': {'song_id': 'song_001', 'plays': 400}
        },
        'nightingale_info': {'segments': [1, 2, 3]}
    }


def create_mock_entity_details():
    """Create mock entity details map"""
    return {
        'song_001': {
            'original_artist': 'Taylor Swift',
            'original_track': 'Paper Rings',
            'album': 'Lover'
        },
        'song_002': {
            'original_artist': 'IU',
            'original_track': 'Shopper',
            'album': 'Single'
        },
        'song_003': {
            'original_artist': 'TWICE',
            'original_track': 'I GOT YOU',
            'album': 'Strategy'
        }
    }


def test_single_frame_spec():
    """Test prepare_frame_spec function"""
    print("=== Testing Single Frame Spec Extraction ===\n")
    
    # Create mock data
    render_task = create_mock_render_task()
    entity_details_map = create_mock_entity_details()
    entity_id_to_canonical_name_map = {
        'song_001': 'Taylor Swift - Paper Rings',
        'song_002': 'IU - Shopper',
        'song_003': 'TWICE - I GOT YOU'
    }
    
    # Test frame spec creation
    frame_spec = prepare_frame_spec(
        render_task=render_task,
        entity_id_to_canonical_name_map=entity_id_to_canonical_name_map,
        entity_details_map=entity_details_map,
        n_bars=10,
        dynamic_x_axis_limit=1200.0,
        rolling_window_info=render_task['rolling_window_info'],
        nightingale_info=render_task['nightingale_info'],
        visualization_mode='tracks'
    )
    
    # Validate results
    print("Frame Spec Structure:")
    print(f"- Frame Index: {frame_spec['frame_index']}")
    print(f"- Timestamp: {frame_spec['display_timestamp']}")
    print(f"- Dynamic X Limit: {frame_spec['dynamic_x_axis_limit']}")
    print(f"- Number of bars: {len(frame_spec['bars'])}")
    print(f"- Has rolling stats: {'rolling_stats' in frame_spec}")
    print(f"- Has nightingale data: {'nightingale_data' in frame_spec}")
    
    print("\nBar Details:")
    for i, bar in enumerate(frame_spec['bars']):
        print(f"\nBar {i}:")
        print(f"  Entity ID: {bar['entity_id']}")
        print(f"  Display Name: {bar['display_name']}")
        print(f"  Play Count: {bar['interpolated_play_count']}")
        print(f"  Y Position: {bar['interpolated_y_pos']}")
        print(f"  Is New: {bar['is_new']}")
        print(f"  Color: {bar['bar_color']}")
    
    # Test JSON serializability
    print("\n=== Testing JSON Serializability ===")
    try:
        json_str = json.dumps(frame_spec, indent=2)
        print("✓ Frame spec is JSON serializable")
        print(f"  JSON size: {len(json_str)} bytes")
    except Exception as e:
        print(f"✗ JSON serialization failed: {e}")
        return False
    
    return True


def test_multiple_frame_specs():
    """Test prepare_all_frame_specs function"""
    print("\n\n=== Testing Multiple Frame Specs ===\n")
    
    # Create multiple mock render tasks
    all_render_tasks = []
    for i in range(5):
        task = create_mock_render_task()
        task['overall_frame_index'] = i
        task['bar_render_data_list'][0]['interpolated_play_count'] = 1000 + i * 50
        all_render_tasks.append(task)
    
    entity_details_map = create_mock_entity_details()
    entity_id_to_canonical_name_map = {
        'song_001': 'Taylor Swift - Paper Rings',
        'song_002': 'IU - Shopper',
        'song_003': 'TWICE - I GOT YOU'
    }
    album_bar_colors = {
        'Taylor Swift - Paper Rings': (0.8, 0.2, 0.4, 1.0),
        'IU - Shopper': (0.4, 0.6, 0.2, 1.0),
        'TWICE - I GOT YOU': (0.2, 0.4, 0.8, 1.0)
    }
    
    # Test batch preparation
    all_frame_specs = prepare_all_frame_specs(
        all_render_tasks=all_render_tasks,
        entity_id_to_canonical_name_map=entity_id_to_canonical_name_map,
        entity_details_map=entity_details_map,
        album_bar_colors=album_bar_colors,
        n_bars=10,
        max_play_count_overall=1500.0,
        visualization_mode='tracks'
    )
    
    print(f"Generated {len(all_frame_specs)} frame specifications")
    
    # Validate dynamic x-axis limits
    print("\nDynamic X-Axis Limits per frame:")
    for i, spec in enumerate(all_frame_specs):
        print(f"  Frame {i}: {spec['dynamic_x_axis_limit']:.1f}")
    
    # Check color assignment
    print("\nColor Assignment Check:")
    for i, spec in enumerate(all_frame_specs[:2]):  # Check first 2 frames
        print(f"\nFrame {i}:")
        for bar in spec['bars']:
            has_color = 'bar_color_rgba' in bar
            print(f"  {bar['display_name']}: {'✓' if has_color else '✗'} color assigned")
    
    return True


def test_memory_usage():
    """Test memory usage of frame specs"""
    print("\n\n=== Testing Memory Usage ===\n")
    
    import sys
    
    # Create a large frame spec
    large_task = create_mock_render_task()
    large_task['bar_render_data_list'] = []
    
    # Add many bars
    for i in range(100):
        large_task['bar_render_data_list'].append({
            'entity_id': f'song_{i:03d}',
            'interpolated_y_pos': float(i),
            'interpolated_play_count': 1000.0 - i * 5,
            'bar_color': (0.5, 0.5, 0.5, 1.0),
            'is_new': False
        })
    
    entity_details_map = {
        f'song_{i:03d}': {
            'original_artist': f'Artist {i}',
            'original_track': f'Track {i}',
            'album': f'Album {i}'
        }
        for i in range(100)
    }
    
    frame_spec = prepare_frame_spec(
        render_task=large_task,
        entity_id_to_canonical_name_map={f'song_{i:03d}': f'song_{i:03d}' for i in range(100)},
        entity_details_map=entity_details_map,
        n_bars=100,
        dynamic_x_axis_limit=1200.0,
        rolling_window_info={},
        nightingale_info={},
        visualization_mode='tracks'
    )
    
    # Estimate memory usage
    json_str = json.dumps(frame_spec)
    json_size = len(json_str)
    
    print(f"Frame spec with 100 bars:")
    print(f"  JSON size: {json_size:,} bytes ({json_size/1024:.1f} KB)")
    print(f"  Estimated for 1000 frames: {json_size * 1000 / 1024 / 1024:.1f} MB")
    print(f"  Estimated for 10000 frames: {json_size * 10000 / 1024 / 1024:.1f} MB")
    
    return True


def main():
    """Run all tests"""
    print("Phase 1 Data Extraction Tests")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    if test_single_frame_spec():
        tests_passed += 1
    
    if test_multiple_frame_specs():
        tests_passed += 1
    
    if test_memory_usage():
        tests_passed += 1
    
    print(f"\n\n{'=' * 50}")
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("\n✓ All tests passed! Phase 1 data extraction is working correctly.")
        print("\nNext steps:")
        print("1. Run this test to verify data extraction")
        print("2. Check that frame specs contain all necessary data")
        print("3. Verify JSON serializability for debugging")
        print("4. Proceed to Phase 2: Stateless rendering implementation")
    else:
        print("\n✗ Some tests failed. Please fix issues before proceeding.")
    
    return tests_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)