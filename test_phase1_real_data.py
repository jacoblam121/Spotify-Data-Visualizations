#!/usr/bin/env python3
"""
Phase 1 Test: Real Data Integration Test
Tests the data extraction with actual animation data
"""

import os
import sys
import json
import time
from datetime import datetime

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from config_loader import AppConfig
from data_processor import clean_and_filter_data, prepare_data_for_bar_chart_race
from rolling_stats import calculate_rolling_window_stats
from time_aggregation import calculate_nightingale_time_data, determine_aggregation_type
from nightingale_chart import prepare_nightingale_animation_data
import album_art_utils


def test_real_data_extraction():
    """Test data extraction with real data from the pipeline"""
    print("=== Testing Phase 1 with Real Data ===\n")
    
    # Load configuration
    print("1. Loading configuration...")
    config = AppConfig('configurations.txt')
    album_art_utils.initialize_from_config(config)
    
    # Get visualization mode
    visualization_mode = config.get('VisualizationMode', 'MODE', 'tracks').lower()
    if visualization_mode == 'both':
        visualization_mode = 'tracks'  # Just test tracks mode
    
    print(f"   Mode: {visualization_mode}")
    print(f"   Data source: {config.get('DataSource', 'SOURCE')}")
    
    # Load and prepare data
    print("\n2. Loading and preparing data...")
    cleaned_df = clean_and_filter_data(config)
    if cleaned_df is None or cleaned_df.empty:
        print("   ERROR: No data after cleaning")
        return False
    
    print(f"   Cleaned data: {len(cleaned_df)} rows")
    
    # Prepare for bar chart race
    print("\n3. Preparing bar chart race data...")
    full_race_df, entity_details_map = prepare_data_for_bar_chart_race(
        cleaned_df, mode=visualization_mode
    )
    
    if full_race_df is None or full_race_df.empty:
        print("   ERROR: No race data")
        return False
    
    print(f"   Race data shape: {full_race_df.shape}")
    print(f"   Entity details: {len(entity_details_map)} entries")
    
    # Limit to first 10 frames for testing
    test_race_df = full_race_df.head(10)
    print(f"\n4. Testing with first {len(test_race_df)} frames")
    
    # Calculate rolling stats
    print("\n5. Calculating rolling window stats...")
    rolling_stats = calculate_rolling_window_stats(
        cleaned_df,
        test_race_df.index,
        base_freq='D',
        mode=visualization_mode
    )
    print(f"   Rolling stats calculated for {len(rolling_stats)} timestamps")
    
    # Prepare nightingale data (if enabled)
    nightingale_data = {}
    if config.get_bool('NightingaleChart', 'ENABLE', True):
        print("\n6. Calculating nightingale chart data...")
        agg_type = determine_aggregation_type(
            cleaned_df['timestamp'].min(),
            cleaned_df['timestamp'].max()
        )
        nightingale_time_data = calculate_nightingale_time_data(
            cleaned_df,
            test_race_df.index.tolist(),
            aggregation_type=agg_type
        )
        nightingale_data = prepare_nightingale_animation_data(
            nightingale_time_data,
            test_race_df.index.tolist(),
            enable_smooth_transitions=True,
            transition_duration_seconds=0.3,
            target_fps=30
        )
        print(f"   Nightingale data calculated for {len(nightingale_data)} frames")
    
    # Import functions to test
    print("\n7. Testing data extraction functions...")
    from main_animator import generate_render_tasks, prepare_all_frame_specs
    
    # Generate render tasks
    all_render_tasks = generate_render_tasks(
        test_race_df,
        config.get_int('AnimationOutput', 'N_BARS', 10),
        config.get_int('AnimationOutput', 'TARGET_FPS', 30),
        config.get_float('AnimationOutput', 'ANIMATION_TRANSITION_DURATION_SECONDS', 0.3),
        rolling_stats,
        nightingale_data
    )
    
    print(f"   Generated {len(all_render_tasks)} render tasks")
    
    # Create mock mappings (in real run, these come from pre_fetch functions)
    entity_id_to_canonical_name_map = {}
    album_bar_colors = {}
    
    # Populate with some data
    for entity_id in entity_details_map:
        if visualization_mode == "artists":
            canonical_name = entity_details_map[entity_id].get('original_artist', 'Unknown')
        else:
            artist = entity_details_map[entity_id].get('original_artist', 'Unknown')
            track = entity_details_map[entity_id].get('original_track', 'Unknown')
            canonical_name = f"{track} - {artist}"
        entity_id_to_canonical_name_map[entity_id] = canonical_name
        # Mock color
        album_bar_colors[canonical_name] = (0.5, 0.5, 0.5, 1.0)
    
    # Test frame spec preparation
    print("\n8. Preparing frame specifications...")
    start_time = time.time()
    
    all_frame_specs = prepare_all_frame_specs(
        all_render_tasks,
        entity_id_to_canonical_name_map,
        entity_details_map,
        album_bar_colors,
        config.get_int('AnimationOutput', 'N_BARS', 10),
        full_race_df.max().max(),
        visualization_mode
    )
    
    prep_time = time.time() - start_time
    print(f"   Prepared {len(all_frame_specs)} frame specs in {prep_time:.3f} seconds")
    
    # Analyze first frame spec
    if all_frame_specs:
        print("\n9. Analyzing first frame specification:")
        first_spec = all_frame_specs[0]
        
        print(f"   Frame index: {first_spec['frame_index']}")
        print(f"   Timestamp: {first_spec['display_timestamp']}")
        print(f"   Number of bars: {len(first_spec['bars'])}")
        print(f"   Dynamic X limit: {first_spec['dynamic_x_axis_limit']:.1f}")
        
        if first_spec['bars']:
            print("\n   First bar details:")
            bar = first_spec['bars'][0]
            print(f"     Display name: {bar['display_name']}")
            print(f"     Play count: {bar['interpolated_play_count']:.1f}")
            print(f"     Y position: {bar['interpolated_y_pos']:.2f}")
            print(f"     Has color: {'bar_color_rgba' in bar}")
        
        # Test JSON serialization
        print("\n10. Testing JSON serialization...")
        try:
            json_str = json.dumps(first_spec)
            print(f"    ✓ Successfully serialized (size: {len(json_str):,} bytes)")
            
            # Save sample for inspection
            sample_file = "phase1_sample_frame_spec.json"
            with open(sample_file, 'w') as f:
                json.dump(first_spec, f, indent=2)
            print(f"    ✓ Saved sample to {sample_file}")
            
        except Exception as e:
            print(f"    ✗ Serialization failed: {e}")
            return False
    
    print("\n✓ Phase 1 real data test completed successfully!")
    return True


def main():
    """Run the real data test"""
    print("Phase 1 Real Data Integration Test")
    print("=" * 50)
    
    try:
        success = test_real_data_extraction()
        
        if success:
            print("\n" + "=" * 50)
            print("✓ Success! Data extraction is working with real data.")
            print("\nYou can now:")
            print("1. Inspect phase1_sample_frame_spec.json to see the extracted data")
            print("2. Verify all necessary information is present")
            print("3. Proceed to Phase 2: Stateless rendering implementation")
        else:
            print("\n✗ Test failed. Please check the errors above.")
            
        return success
        
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)