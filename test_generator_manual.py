#!/usr/bin/env python3
"""
Manual test to verify the frame spec generator works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from frame_spec_generator import create_frame_spec_generator
from main_animator import prepare_all_frame_specs
from datetime import datetime, timedelta

def create_test_data():
    """Create minimal test data."""
    # Create 3 sample render tasks
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    render_tasks = []
    
    for i in range(3):
        task = {
            'overall_frame_index': i,
            'display_timestamp': base_time + timedelta(minutes=i * 30),
            'bar_render_data_list': [
                {
                    'entity_id': 'song_1',
                    'interpolated_play_count': float(100 - i * 10),
                    'interpolated_y_position': 0.0,
                    'current_rank': 0,
                    'is_new': False,
                    'bar_color': (0.5, 0.3, 0.7, 1.0)
                },
                {
                    'entity_id': 'song_2', 
                    'interpolated_play_count': float(80 - i * 8),
                    'interpolated_y_position': 1.0,
                    'current_rank': 1,
                    'is_new': False,
                    'bar_color': (0.3, 0.6, 0.9, 1.0)
                }
            ],
            'rolling_window_info': {
                'top_7_day': {'song_id': 'song_1', 'plays': 50},
                'top_30_day': {'song_id': 'song_2', 'plays': 200}
            },
            'nightingale_info': {}
        }
        render_tasks.append(task)
    
    entity_map = {'song_1': 'canonical_song_1', 'song_2': 'canonical_song_2'}
    entity_details = {
        'song_1': {'original_artist': 'Artist 1', 'original_track': 'Track 1'},
        'song_2': {'original_artist': 'Artist 2', 'original_track': 'Track 2'}
    }
    colors = {'canonical_song_1': (0.8, 0.2, 0.2, 1.0), 'canonical_song_2': (0.2, 0.8, 0.2, 1.0)}
    
    return render_tasks, entity_map, entity_details, colors

def test_generator():
    """Test the generator manually."""
    print("Testing FrameSpecGenerator...")
    
    render_tasks, entity_map, entity_details, colors = create_test_data()
    
    # Test original method
    print("\n1. Testing original method:")
    original_specs = prepare_all_frame_specs(
        render_tasks, entity_map, entity_details, colors, 5, 1000.0, "tracks"
    )
    print(f"Original method produced {len(original_specs)} specs")
    
    # Test generator
    print("\n2. Testing generator:")
    generator = create_frame_spec_generator(
        render_tasks, entity_map, entity_details, colors, 5, 1000.0, "tracks"
    )
    print(f"Generator created for {generator.total_frames} frames")
    
    # Generate specs using generator
    generator_specs = list(generator)
    print(f"Generator produced {len(generator_specs)} specs")
    
    # Compare
    print(f"\n3. Comparing outputs:")
    print(f"Lengths match: {len(original_specs) == len(generator_specs)}")
    
    if len(original_specs) == len(generator_specs):
        all_match = True
        for i, (orig, gen) in enumerate(zip(original_specs, generator_specs)):
            if orig['frame_index'] != gen['frame_index']:
                print(f"Frame {i}: frame_index mismatch")
                all_match = False
            if len(orig['bars']) != len(gen['bars']):
                print(f"Frame {i}: different number of bars")
                all_match = False
        
        print(f"All specs match: {all_match}")
        
        if all_match:
            print("\n✓ Generator produces identical output to original method!")
        else:
            print("\n✗ Generator output differs from original method")
            
    # Test memory info
    print(f"\n4. Memory info:")
    memory_info = generator.get_memory_info()
    for key, value in memory_info.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    test_generator()