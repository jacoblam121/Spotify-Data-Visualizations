#!/usr/bin/env python3
"""
Comprehensive Phase 1 Test Suite
Tests data extraction with both Spotify and Last.fm data sources,
including edge cases and configuration variations.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timedelta
import traceback

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from config_loader import AppConfig
from data_processor import clean_and_filter_data, prepare_data_for_bar_chart_race
from rolling_stats import calculate_rolling_window_stats
from time_aggregation import calculate_nightingale_time_data, determine_aggregation_type
from nightingale_chart import prepare_nightingale_animation_data
import album_art_utils
from main_animator import generate_render_tasks, prepare_all_frame_specs, make_json_serializable


class TestConfiguration:
    """Test configuration management"""
    
    def __init__(self, test_name, **kwargs):
        self.test_name = test_name
        self.config_overrides = kwargs
        
    def apply_to_config(self, config_file_path):
        """Create a temporary config with overrides"""
        # Read original config
        with open(config_file_path, 'r') as f:
            original_content = f.read()
        
        # Apply overrides
        modified_content = original_content
        for section_key, value in self.config_overrides.items():
            if '.' in section_key:
                section, key = section_key.split('.', 1)
                # Simple replacement - look for existing line and replace it
                import re
                pattern = rf'^{key}\s*=.*$'
                replacement = f'{key} = {value}'
                
                # Find the section and replace within it
                section_start = modified_content.find(f'[{section}]')
                if section_start != -1:
                    next_section = modified_content.find('[', section_start + 1)
                    section_content = modified_content[section_start:next_section] if next_section != -1 else modified_content[section_start:]
                    
                    if re.search(pattern, section_content, re.MULTILINE):
                        section_content = re.sub(pattern, replacement, section_content, flags=re.MULTILINE)
                    else:
                        # Add the setting if it doesn't exist
                        section_content += f'\n{replacement}'
                    
                    if next_section != -1:
                        modified_content = modified_content[:section_start] + section_content + modified_content[next_section:]
                    else:
                        modified_content = modified_content[:section_start] + section_content
        
        # Write temporary config
        temp_config_path = f'test_config_{self.test_name}.txt'
        with open(temp_config_path, 'w') as f:
            f.write(modified_content)
        
        return temp_config_path


class Phase1TestSuite:
    """Comprehensive test suite for Phase 1 data extraction"""
    
    def __init__(self, verbose=False, save_samples=True):
        self.verbose = verbose
        self.save_samples = save_samples
        self.test_results = []
        self.samples_dir = "phase1_test_samples"
        
        if self.save_samples:
            os.makedirs(self.samples_dir, exist_ok=True)
    
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] {level}:"
        print(f"{prefix} {message}")
    
    def verbose_log(self, message):
        """Log only if verbose mode is enabled"""
        if self.verbose:
            self.log(message, "DEBUG")
    
    def run_test(self, test_name, test_func, *args, **kwargs):
        """Run a single test and track results"""
        self.log(f"Running test: {test_name}")
        start_time = time.time()
        
        try:
            result = test_func(*args, **kwargs)
            duration = time.time() - start_time
            
            if result:
                self.log(f"✓ {test_name} PASSED ({duration:.3f}s)", "PASS")
                self.test_results.append({"name": test_name, "status": "PASS", "duration": duration})
                return True
            else:
                self.log(f"✗ {test_name} FAILED ({duration:.3f}s)", "FAIL")
                self.test_results.append({"name": test_name, "status": "FAIL", "duration": duration})
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log(f"✗ {test_name} ERROR: {e} ({duration:.3f}s)", "ERROR")
            if self.verbose:
                traceback.print_exc()
            self.test_results.append({"name": test_name, "status": "ERROR", "duration": duration, "error": str(e)})
            return False
    
    def test_spotify_data_extraction(self):
        """Test data extraction with Spotify data source"""
        self.verbose_log("Testing Spotify data extraction...")
        
        config = TestConfiguration("spotify", **{
            'DataSource.SOURCE': 'spotify',
            'VisualizationMode.MODE': 'tracks',
            'AnimationOutput.MAX_FRAMES_FOR_TEST_RENDER': '5',
            'AnimationOutput.N_BARS': '3'
        })
        
        return self._test_data_source(config, "spotify")
    
    def test_lastfm_data_extraction(self):
        """Test data extraction with Last.fm data source"""
        self.verbose_log("Testing Last.fm data extraction...")
        
        # Check if Last.fm data file exists
        if not os.path.exists('lastfm_data.csv'):
            self.log("Skipping Last.fm test - lastfm_data.csv not found", "SKIP")
            return True  # Not a failure, just skipped
        
        config = TestConfiguration("lastfm", **{
            'DataSource.SOURCE': 'lastfm',
            'VisualizationMode.MODE': 'tracks',
            'AnimationOutput.MAX_FRAMES_FOR_TEST_RENDER': '5',
            'AnimationOutput.N_BARS': '3'
        })
        
        return self._test_data_source(config, "lastfm")
    
    def test_artist_mode_extraction(self):
        """Test data extraction in artist mode"""
        self.verbose_log("Testing artist mode extraction...")
        
        config = TestConfiguration("artist_mode", **{
            'DataSource.SOURCE': 'spotify',
            'VisualizationMode.MODE': 'artists',
            'AnimationOutput.MAX_FRAMES_FOR_TEST_RENDER': '3',
            'AnimationOutput.N_BARS': '5'
        })
        
        return self._test_data_source(config, "artist_mode")
    
    def test_large_frame_count(self):
        """Test with larger number of frames"""
        self.verbose_log("Testing with larger frame count...")
        
        config = TestConfiguration("large_frames", **{
            'DataSource.SOURCE': 'spotify',
            'VisualizationMode.MODE': 'tracks',
            'AnimationOutput.MAX_FRAMES_FOR_TEST_RENDER': '50',
            'AnimationOutput.N_BARS': '10'
        })
        
        return self._test_data_source(config, "large_frames", check_performance=True)
    
    def test_edge_case_single_bar(self):
        """Test edge case with only 1 bar"""
        self.verbose_log("Testing edge case: single bar...")
        
        config = TestConfiguration("single_bar", **{
            'DataSource.SOURCE': 'spotify',
            'VisualizationMode.MODE': 'tracks',
            'AnimationOutput.MAX_FRAMES_FOR_TEST_RENDER': '3',
            'AnimationOutput.N_BARS': '1'
        })
        
        return self._test_data_source(config, "single_bar")
    
    def test_edge_case_no_nightingale(self):
        """Test with nightingale chart disabled"""
        self.verbose_log("Testing with nightingale disabled...")
        
        config = TestConfiguration("no_nightingale", **{
            'DataSource.SOURCE': 'spotify',
            'VisualizationMode.MODE': 'tracks',
            'AnimationOutput.MAX_FRAMES_FOR_TEST_RENDER': '3',
            'NightingaleChart.ENABLE': 'False'
        })
        
        return self._test_data_source(config, "no_nightingale")
    
    def test_frame_aggregation(self):
        """Test with frame aggregation enabled"""
        self.verbose_log("Testing frame aggregation...")
        
        config = TestConfiguration("aggregation", **{
            'DataSource.SOURCE': 'spotify',
            'VisualizationMode.MODE': 'tracks',
            'AnimationOutput.MAX_FRAMES_FOR_TEST_RENDER': '10',
            'AnimationOutput.FRAME_AGGREGATION_PERIOD': 'D'
        })
        
        return self._test_data_source(config, "aggregation")
    
    def test_json_serialization_comprehensive(self):
        """Comprehensive JSON serialization test with various data types"""
        self.verbose_log("Testing comprehensive JSON serialization...")
        
        # Test various numpy/pandas types
        import pandas as pd
        import numpy as np
        
        test_data = {
            'timestamp': pd.Timestamp('2024-01-01 12:00:00+00:00'),
            'numpy_int': np.int64(42),
            'numpy_float': np.float64(3.14159),
            'numpy_array': np.array([1, 2, 3]),
            'pandas_series': pd.Series([1, 2, 3]),
            'nested_dict': {
                'inner_timestamp': pd.Timestamp('2024-06-27'),
                'inner_array': np.array([4.0, 5.0, 6.0])
            },
            'list_with_types': [np.int32(1), np.float32(2.5), pd.Timestamp('2024-01-01')]
        }
        
        try:
            serialized = make_json_serializable(test_data)
            json_str = json.dumps(serialized, indent=2)
            
            # Verify we can load it back
            loaded = json.loads(json_str)
            
            self.verbose_log(f"Successfully serialized {len(json_str)} characters")
            
            if self.save_samples:
                with open(os.path.join(self.samples_dir, "serialization_test.json"), 'w') as f:
                    f.write(json_str)
            
            return True
            
        except Exception as e:
            self.log(f"JSON serialization failed: {e}", "ERROR")
            return False
    
    def test_memory_usage_analysis(self):
        """Analyze memory usage of frame specs"""
        self.verbose_log("Analyzing memory usage...")
        
        config = TestConfiguration("memory_test", **{
            'DataSource.SOURCE': 'spotify',
            'VisualizationMode.MODE': 'tracks',
            'AnimationOutput.MAX_FRAMES_FOR_TEST_RENDER': '10',
            'AnimationOutput.N_BARS': '20'
        })
        
        temp_config_path = config.apply_to_config('configurations.txt')
        
        try:
            # Load configuration
            app_config = AppConfig(temp_config_path)
            album_art_utils.initialize_from_config(app_config)
            
            # Process data
            cleaned_df = clean_and_filter_data(app_config)
            if cleaned_df is None or cleaned_df.empty:
                return False
            
            race_df, entity_details_map = prepare_data_for_bar_chart_race(
                cleaned_df, mode='tracks'
            )
            
            # Calculate stats
            rolling_stats = calculate_rolling_window_stats(
                cleaned_df, race_df.index[:10], base_freq='D', mode='tracks'
            )
            
            # Generate render tasks
            render_tasks = generate_render_tasks(
                race_df.head(10), 20, 30, 0.3, rolling_stats, {}
            )
            
            # Mock data for memory test
            entity_id_to_canonical_name_map = {eid: f"track_{eid}" for eid in entity_details_map.keys()}
            album_bar_colors = {name: (0.5, 0.5, 0.5, 1.0) for name in entity_id_to_canonical_name_map.values()}
            
            # Prepare frame specs
            frame_specs = prepare_all_frame_specs(
                render_tasks, entity_id_to_canonical_name_map, entity_details_map,
                album_bar_colors, 20, 1000.0, 'tracks'
            )
            
            # Analyze memory usage
            if frame_specs:
                sample_spec = frame_specs[0]
                json_str = json.dumps(sample_spec)
                size_per_frame = len(json_str)
                
                total_size_mb = (size_per_frame * len(frame_specs)) / (1024 * 1024)
                
                self.log(f"Memory analysis results:")
                self.log(f"  - Frames processed: {len(frame_specs)}")
                self.log(f"  - Size per frame: {size_per_frame:,} bytes")
                self.log(f"  - Total size: {total_size_mb:.2f} MB")
                self.log(f"  - Estimated for 1000 frames: {(size_per_frame * 1000) / (1024 * 1024):.1f} MB")
                
                # Save analysis
                analysis = {
                    'frames_processed': len(frame_specs),
                    'size_per_frame_bytes': size_per_frame,
                    'total_size_mb': total_size_mb,
                    'estimated_1000_frames_mb': (size_per_frame * 1000) / (1024 * 1024)
                }
                
                if self.save_samples:
                    with open(os.path.join(self.samples_dir, "memory_analysis.json"), 'w') as f:
                        json.dump(analysis, f, indent=2)
                
                return total_size_mb < 100  # Reasonable threshold
            
            return False
            
        finally:
            if os.path.exists(temp_config_path):
                os.remove(temp_config_path)
    
    def _test_data_source(self, config, test_id, check_performance=False):
        """Helper method to test a specific data source configuration"""
        temp_config_path = config.apply_to_config('configurations.txt')
        
        try:
            # Load configuration
            app_config = AppConfig(temp_config_path)
            album_art_utils.initialize_from_config(app_config)
            
            # Get settings
            visualization_mode = app_config.get('VisualizationMode', 'MODE', 'tracks').lower()
            max_frames = app_config.get_int('AnimationOutput', 'MAX_FRAMES_FOR_TEST_RENDER', 5)
            n_bars = app_config.get_int('AnimationOutput', 'N_BARS', 10)
            
            self.verbose_log(f"Config: mode={visualization_mode}, max_frames={max_frames}, n_bars={n_bars}")
            
            # Load and clean data
            start_time = time.time()
            cleaned_df = clean_and_filter_data(app_config)
            
            if cleaned_df is None or cleaned_df.empty:
                self.log(f"No data available for {test_id}", "ERROR")
                return False
            
            data_load_time = time.time() - start_time
            self.verbose_log(f"Data loaded and cleaned: {len(cleaned_df)} rows in {data_load_time:.3f}s")
            
            # Prepare race data
            start_time = time.time()
            race_df, entity_details_map = prepare_data_for_bar_chart_race(
                cleaned_df, mode=visualization_mode
            )
            
            if race_df is None or race_df.empty:
                self.log(f"No race data for {test_id}", "ERROR")
                return False
            
            # Limit frames for testing
            test_race_df = race_df.head(max_frames)
            race_prep_time = time.time() - start_time
            
            self.verbose_log(f"Race data prepared: {test_race_df.shape} in {race_prep_time:.3f}s")
            
            # Calculate rolling stats
            start_time = time.time()
            rolling_stats = calculate_rolling_window_stats(
                cleaned_df, test_race_df.index, base_freq='D', mode=visualization_mode
            )
            rolling_time = time.time() - start_time
            
            # Calculate nightingale data (if enabled)
            nightingale_data = {}
            nightingale_time = 0
            if app_config.get_bool('NightingaleChart', 'ENABLE', True):
                start_time = time.time()
                agg_type = determine_aggregation_type(
                    cleaned_df['timestamp'].min(),
                    cleaned_df['timestamp'].max()
                )
                nightingale_time_data = calculate_nightingale_time_data(
                    cleaned_df, test_race_df.index.tolist(), aggregation_type=agg_type
                )
                nightingale_data = prepare_nightingale_animation_data(
                    nightingale_time_data, test_race_df.index.tolist(),
                    enable_smooth_transitions=True, transition_duration_seconds=0.3, target_fps=30
                )
                nightingale_time = time.time() - start_time
            
            # Generate render tasks
            start_time = time.time()
            render_tasks = generate_render_tasks(
                test_race_df, n_bars, 30, 0.3, rolling_stats, nightingale_data
            )
            
            if not render_tasks:
                self.log(f"No render tasks generated for {test_id}", "ERROR")
                return False
            
            render_task_time = time.time() - start_time
            
            # Create mock mappings
            entity_id_to_canonical_name_map = {}
            album_bar_colors = {}
            
            for entity_id in entity_details_map:
                if visualization_mode == "artists":
                    canonical_name = entity_details_map[entity_id].get('display_artist', 'Unknown')
                else:
                    artist = entity_details_map[entity_id].get('original_artist', 'Unknown')
                    track = entity_details_map[entity_id].get('original_track', 'Unknown')
                    canonical_name = f"{track} - {artist}"
                
                entity_id_to_canonical_name_map[entity_id] = canonical_name
                album_bar_colors[canonical_name] = (0.5, 0.5, 0.5, 1.0)
            
            # Test frame spec preparation
            start_time = time.time()
            frame_specs = prepare_all_frame_specs(
                render_tasks, entity_id_to_canonical_name_map, entity_details_map,
                album_bar_colors, n_bars, race_df.max().max(), visualization_mode
            )
            frame_spec_time = time.time() - start_time
            
            if not frame_specs:
                self.log(f"No frame specs generated for {test_id}", "ERROR")
                return False
            
            # Validate frame specs
            for i, spec in enumerate(frame_specs[:3]):  # Check first 3
                if not self._validate_frame_spec(spec, visualization_mode):
                    self.log(f"Frame spec {i} validation failed for {test_id}", "ERROR")
                    return False
            
            # Test JSON serialization
            try:
                json_str = json.dumps(frame_specs[0])
                json_size = len(json_str)
            except Exception as e:
                self.log(f"JSON serialization failed for {test_id}: {e}", "ERROR")
                return False
            
            # Save sample if requested
            if self.save_samples:
                sample_file = os.path.join(self.samples_dir, f"{test_id}_sample.json")
                with open(sample_file, 'w') as f:
                    json.dump(frame_specs[0], f, indent=2)
                
                # Save performance metrics
                metrics = {
                    'test_id': test_id,
                    'data_load_time': data_load_time,
                    'race_prep_time': race_prep_time,
                    'rolling_time': rolling_time,
                    'nightingale_time': nightingale_time,
                    'render_task_time': render_task_time,
                    'frame_spec_time': frame_spec_time,
                    'total_frames': len(frame_specs),
                    'json_size_bytes': json_size,
                    'frames_per_second': len(frame_specs) / frame_spec_time if frame_spec_time > 0 else 0
                }
                
                metrics_file = os.path.join(self.samples_dir, f"{test_id}_metrics.json")
                with open(metrics_file, 'w') as f:
                    json.dump(metrics, f, indent=2)
            
            # Log results
            self.log(f"{test_id} results:")
            self.log(f"  - Processed {len(frame_specs)} frame specs in {frame_spec_time:.3f}s")
            self.log(f"  - Performance: {len(frame_specs) / frame_spec_time:.1f} frames/sec")
            self.log(f"  - JSON size: {json_size:,} bytes")
            
            # Performance check
            if check_performance:
                frames_per_sec = len(frame_specs) / frame_spec_time if frame_spec_time > 0 else 0
                if frames_per_sec < 10:  # Should process at least 10 frames per second
                    self.log(f"Performance warning: {frames_per_sec:.1f} frames/sec is slow", "WARN")
            
            return True
            
        finally:
            if os.path.exists(temp_config_path):
                os.remove(temp_config_path)
    
    def _validate_frame_spec(self, spec, visualization_mode):
        """Validate a frame specification"""
        required_fields = [
            'frame_index', 'display_timestamp', 'bars', 'rolling_stats',
            'nightingale_data', 'dynamic_x_axis_limit', 'visualization_mode'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in spec:
                self.log(f"Missing required field: {field}", "ERROR")
                return False
        
        # Check visualization mode matches
        if spec['visualization_mode'] != visualization_mode:
            self.log(f"Visualization mode mismatch: {spec['visualization_mode']} != {visualization_mode}", "ERROR")
            return False
        
        # Check bars structure
        if not isinstance(spec['bars'], list):
            self.log("Bars field must be a list", "ERROR")
            return False
        
        for i, bar in enumerate(spec['bars']):
            bar_required = ['entity_id', 'display_name', 'interpolated_y_pos', 'interpolated_play_count']
            for field in bar_required:
                if field not in bar:
                    self.log(f"Bar {i} missing field: {field}", "ERROR")
                    return False
        
        # Check timestamp format
        try:
            datetime.fromisoformat(spec['display_timestamp'].replace('Z', '+00:00'))
        except ValueError:
            self.log(f"Invalid timestamp format: {spec['display_timestamp']}", "ERROR")
            return False
        
        return True
    
    def run_all_tests(self):
        """Run the complete test suite"""
        self.log("=" * 60)
        self.log("PHASE 1 COMPREHENSIVE TEST SUITE")
        self.log("=" * 60)
        
        tests = [
            ("JSON Serialization", self.test_json_serialization_comprehensive),
            ("Spotify Data Extraction", self.test_spotify_data_extraction),
            ("Last.fm Data Extraction", self.test_lastfm_data_extraction),
            ("Artist Mode", self.test_artist_mode_extraction),
            ("Single Bar Edge Case", self.test_edge_case_single_bar),
            ("No Nightingale", self.test_edge_case_no_nightingale),
            ("Frame Aggregation", self.test_frame_aggregation),
            ("Large Frame Count", self.test_large_frame_count),
            ("Memory Usage Analysis", self.test_memory_usage_analysis),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
            print()  # Add spacing between tests
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        self.log("=" * 60)
        self.log("TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        errors = sum(1 for r in self.test_results if r['status'] == 'ERROR')
        
        self.log(f"Total tests: {len(self.test_results)}")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {failed}")
        self.log(f"Errors: {errors}")
        
        if failed > 0 or errors > 0:
            self.log("\nFailed/Error tests:")
            for result in self.test_results:
                if result['status'] in ['FAIL', 'ERROR']:
                    error_info = f" - {result.get('error', '')}" if 'error' in result else ""
                    self.log(f"  ✗ {result['name']}: {result['status']}{error_info}")
        
        total_time = sum(r['duration'] for r in self.test_results)
        self.log(f"\nTotal execution time: {total_time:.3f}s")
        
        if self.save_samples:
            self.log(f"\nSample files saved to: {self.samples_dir}/")
        
        success_rate = (passed / len(self.test_results)) * 100 if self.test_results else 0
        self.log(f"\nSuccess rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            self.log("\n🎉 Phase 1 is working well! Ready for Phase 2.", "SUCCESS")
        elif success_rate >= 70:
            self.log("\n⚠️  Phase 1 has some issues but is mostly working.", "WARNING")
        else:
            self.log("\n❌ Phase 1 has significant issues that need fixing.", "ERROR")


def show_interactive_menu():
    """Display interactive test menu and get user selection"""
    while True:
        print("\n" + "=" * 60)
        print("🧪 PHASE 1 COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print()
        print("Select test mode:")
        print()
        print("  [1] 🚀 Run All Tests (Recommended)")
        print("  [2] ⚡ Quick Validation (Core tests only)")
        print("  [3] 🎯 Individual Test Selection")
        print("  [4] 🔧 Advanced Options")
        print("  [5] 📋 Data Source Check")
        print("  [6] ❓ Help & Documentation")
        print("  [0] 🚪 Exit")
        print()
        
        try:
            choice = input("Enter your choice [0-6]: ").strip()
            
            if choice == '0':
                print("\n👋 Goodbye!")
                return None, {}
            elif choice == '1':
                return 'all', {}
            elif choice == '2':
                return 'quick', {}
            elif choice == '3':
                return interactive_individual_tests()
            elif choice == '4':
                return interactive_advanced_options()
            elif choice == '5':
                return 'data_check', {}
            elif choice == '6':
                show_help()
                continue
            else:
                print("❌ Invalid choice. Please enter a number from 0-6.")
                continue
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            return None, {}
        except EOFError:
            print("\n\n👋 Goodbye!")
            return None, {}


def interactive_individual_tests():
    """Interactive individual test selection"""
    tests = [
        ("spotify", "🎵 Spotify Data Extraction", "Test with spotify_data.json"),
        ("lastfm", "🎶 Last.fm Data Extraction", "Test with lastfm_data.csv"),
        ("artist", "👨‍🎤 Artist Mode", "Test artist visualization mode"),
        ("large", "📊 Large Frame Count", "Performance test with 50 frames"),
        ("single", "🎯 Single Bar Edge Case", "Test with minimal data (1 bar)"),
        ("no-nightingale", "🚫 No Nightingale Chart", "Test with nightingale disabled"),
        ("aggregation", "📅 Frame Aggregation", "Test daily frame grouping"),
        ("json", "🔧 JSON Serialization", "Test data type conversion"),
        ("memory", "💾 Memory Usage Analysis", "Analyze memory consumption"),
    ]
    
    while True:
        print("\n" + "=" * 60)
        print("🎯 INDIVIDUAL TEST SELECTION")
        print("=" * 60)
        print()
        
        for i, (test_id, name, desc) in enumerate(tests, 1):
            print(f"  [{i:2}] {name}")
            print(f"      {desc}")
            print()
        
        print(f"  [ 0] ← Back to main menu")
        print()
        
        try:
            choice = input(f"Select test [0-{len(tests)}]: ").strip()
            
            if choice == '0':
                return show_interactive_menu()
            
            try:
                test_idx = int(choice) - 1
                if 0 <= test_idx < len(tests):
                    test_id = tests[test_idx][0]
                    test_name = tests[test_idx][1]
                    
                    print(f"\n✅ Selected: {test_name}")
                    
                    # Ask for options
                    verbose = input("Enable verbose logging? [y/N]: ").strip().lower() in ['y', 'yes']
                    save_samples = input("Save sample files? [Y/n]: ").strip().lower() not in ['n', 'no']
                    
                    return 'individual', {
                        'test': test_id,
                        'verbose': verbose,
                        'save_samples': save_samples
                    }
                else:
                    print("❌ Invalid selection.")
                    continue
                    
            except ValueError:
                print("❌ Please enter a valid number.")
                continue
                
        except KeyboardInterrupt:
            return None, {}


def interactive_advanced_options():
    """Interactive advanced options menu"""
    while True:
        print("\n" + "=" * 60)
        print("🔧 ADVANCED OPTIONS")
        print("=" * 60)
        print()
        print("  [1] 🚀 All Tests with Custom Settings")
        print("  [2] ⚡ Quick Tests with Custom Settings")
        print("  [3] 🎯 Multiple Specific Tests")
        print("  [4] 📊 Performance Analysis Suite")
        print("  [5] 🧪 Data Source Comparison")
        print("  [0] ← Back to main menu")
        print()
        
        try:
            choice = input("Select option [0-5]: ").strip()
            
            if choice == '0':
                return show_interactive_menu()
            elif choice == '1':
                verbose = input("Enable verbose logging? [y/N]: ").strip().lower() in ['y', 'yes']
                save_samples = input("Save sample files? [Y/n]: ").strip().lower() not in ['n', 'no']
                return 'all', {'verbose': verbose, 'save_samples': save_samples}
            elif choice == '2':
                verbose = input("Enable verbose logging? [y/N]: ").strip().lower() in ['y', 'yes']
                save_samples = input("Save sample files? [Y/n]: ").strip().lower() not in ['n', 'no']
                return 'quick', {'verbose': verbose, 'save_samples': save_samples}
            elif choice == '3':
                return interactive_multiple_tests()
            elif choice == '4':
                return 'performance', {}
            elif choice == '5':
                return 'comparison', {}
            else:
                print("❌ Invalid choice.")
                continue
                
        except KeyboardInterrupt:
            return None, {}


def interactive_multiple_tests():
    """Select multiple tests to run"""
    tests = [
        ("spotify", "🎵 Spotify Data"),
        ("lastfm", "🎶 Last.fm Data"),
        ("artist", "👨‍🎤 Artist Mode"),
        ("large", "📊 Large Frames"),
        ("single", "🎯 Single Bar"),
        ("no-nightingale", "🚫 No Nightingale"),
        ("aggregation", "📅 Aggregation"),
        ("json", "🔧 JSON"),
        ("memory", "💾 Memory"),
    ]
    
    print("\n" + "=" * 60)
    print("🎯 MULTIPLE TEST SELECTION")
    print("=" * 60)
    print()
    print("Select tests to run (space-separated numbers):")
    print()
    
    for i, (test_id, name) in enumerate(tests, 1):
        print(f"  [{i}] {name}")
    
    print()
    print("Examples:")
    print("  1 2 3    - Run Spotify, Last.fm, and Artist tests")
    print("  1 4 8    - Run Spotify, Large frames, and JSON tests")
    print("  all      - Run all tests")
    print()
    
    try:
        selection = input("Enter selection: ").strip()
        
        if selection.lower() == 'all':
            selected_tests = [test[0] for test in tests]
        else:
            indices = [int(x) - 1 for x in selection.split()]
            selected_tests = [tests[i][0] for i in indices if 0 <= i < len(tests)]
        
        if not selected_tests:
            print("❌ No valid tests selected.")
            return interactive_multiple_tests()
        
        print(f"\n✅ Selected {len(selected_tests)} tests")
        verbose = input("Enable verbose logging? [y/N]: ").strip().lower() in ['y', 'yes']
        save_samples = input("Save sample files? [Y/n]: ").strip().lower() not in ['n', 'no']
        
        return 'multiple', {
            'tests': selected_tests,
            'verbose': verbose,
            'save_samples': save_samples
        }
        
    except (ValueError, IndexError):
        print("❌ Invalid selection format.")
        return interactive_multiple_tests()
    except KeyboardInterrupt:
        return None, {}


def show_help():
    """Show help information"""
    print("\n" + "=" * 60)
    print("❓ HELP & DOCUMENTATION")
    print("=" * 60)
    print()
    print("📖 About the Test Suite:")
    print("   This comprehensive test suite validates that Phase 1 (data extraction)")
    print("   is working correctly with both Spotify and Last.fm data sources.")
    print()
    print("🎯 Test Categories:")
    print("   • Core Functionality: Spotify/Last.fm data extraction, Artist mode")
    print("   • Edge Cases: Single bar, No nightingale, Frame aggregation")
    print("   • Performance: Large frame counts, Memory analysis")
    print("   • Technical: JSON serialization validation")
    print()
    print("📊 What Gets Tested:")
    print("   • Data loading and processing")
    print("   • Frame specification generation")
    print("   • JSON serialization compatibility")
    print("   • Performance and memory usage")
    print("   • Configuration handling")
    print()
    print("📁 Output Files:")
    print("   • phase1_test_samples/ - Sample frame specs and metrics")
    print("   • Detailed JSON files for inspection and debugging")
    print()
    print("🚀 Recommendations:")
    print("   • Start with 'Run All Tests' for comprehensive validation")
    print("   • Use 'Quick Validation' for faster checking")
    print("   • Check individual tests if issues found")
    print()
    print("📋 Requirements:")
    print("   • Virtual environment activated")
    print("   • Data files: spotify_data.json or lastfm_data.csv")
    print("   • All dependencies installed (pip install -r requirements.txt)")
    print()
    
    input("Press Enter to continue...")


def main():
    """Main test runner with interactive menu"""
    parser = argparse.ArgumentParser(description="Phase 1 Comprehensive Test Suite")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--no-samples", action="store_true", help="Don't save sample files")
    parser.add_argument("--test", type=str, help="Run specific test by name")
    parser.add_argument("--interactive", "-i", action="store_true", help="Use interactive menu")
    parser.add_argument("--menu", action="store_true", help="Show interactive menu (default if no args)")
    
    args = parser.parse_args()
    
    # Set up environment
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Determine if we should show interactive menu
    show_menu = (args.interactive or args.menu or 
                 (not args.test and not args.verbose and not args.no_samples and len(sys.argv) == 1))
    
    if show_menu:
        # Interactive mode
        try:
            selection, options = show_interactive_menu()
            
            if selection is None:
                return 0
            
            # Apply options
            verbose = options.get('verbose', False)
            save_samples = options.get('save_samples', True)
            
            suite = Phase1TestSuite(verbose=verbose, save_samples=save_samples)
            
            if selection == 'data_check':
                # Run data source check
                from check_data_sources import main as check_main
                return check_main()
            
            elif selection == 'all':
                suite.run_all_tests()
                
            elif selection == 'quick':
                # Run core tests only
                quick_tests = [
                    ("JSON Serialization", suite.test_json_serialization_comprehensive),
                    ("Spotify Data Extraction", suite.test_spotify_data_extraction),
                    ("Artist Mode", suite.test_artist_mode_extraction),
                ]
                
                for test_name, test_func in quick_tests:
                    suite.run_test(test_name, test_func)
                    print()
                    
            elif selection == 'individual':
                test_id = options['test']
                test_methods = {
                    'spotify': suite.test_spotify_data_extraction,
                    'lastfm': suite.test_lastfm_data_extraction,
                    'artist': suite.test_artist_mode_extraction,
                    'large': suite.test_large_frame_count,
                    'single': suite.test_edge_case_single_bar,
                    'no-nightingale': suite.test_edge_case_no_nightingale,
                    'aggregation': suite.test_frame_aggregation,
                    'json': suite.test_json_serialization_comprehensive,
                    'memory': suite.test_memory_usage_analysis,
                }
                
                if test_id in test_methods:
                    suite.run_test(test_id, test_methods[test_id])
                    
            elif selection == 'multiple':
                test_ids = options['tests']
                test_methods = {
                    'spotify': ("Spotify Data Extraction", suite.test_spotify_data_extraction),
                    'lastfm': ("Last.fm Data Extraction", suite.test_lastfm_data_extraction),
                    'artist': ("Artist Mode", suite.test_artist_mode_extraction),
                    'large': ("Large Frame Count", suite.test_large_frame_count),
                    'single': ("Single Bar Edge Case", suite.test_edge_case_single_bar),
                    'no-nightingale': ("No Nightingale", suite.test_edge_case_no_nightingale),
                    'aggregation': ("Frame Aggregation", suite.test_frame_aggregation),
                    'json': ("JSON Serialization", suite.test_json_serialization_comprehensive),
                    'memory': ("Memory Usage Analysis", suite.test_memory_usage_analysis),
                }
                
                for test_id in test_ids:
                    if test_id in test_methods:
                        test_name, test_func = test_methods[test_id]
                        suite.run_test(test_name, test_func)
                        print()
                        
            elif selection == 'performance':
                # Performance-focused tests
                perf_tests = [
                    ("Large Frame Count", suite.test_large_frame_count),
                    ("Memory Usage Analysis", suite.test_memory_usage_analysis),
                    ("JSON Serialization", suite.test_json_serialization_comprehensive),
                ]
                
                for test_name, test_func in perf_tests:
                    suite.run_test(test_name, test_func)
                    print()
                    
            elif selection == 'comparison':
                # Compare data sources
                comparison_tests = [
                    ("Spotify Data Extraction", suite.test_spotify_data_extraction),
                    ("Last.fm Data Extraction", suite.test_lastfm_data_extraction),
                ]
                
                for test_name, test_func in comparison_tests:
                    suite.run_test(test_name, test_func)
                    print()
            
            suite.print_summary()
            failed = sum(1 for r in suite.test_results if r['status'] in ['FAIL', 'ERROR'])
            return 0 if failed == 0 else 1
            
        except KeyboardInterrupt:
            print("\n\n👋 Test interrupted by user.")
            return 1
    else:
        # Command line mode (original behavior)
        suite = Phase1TestSuite(verbose=args.verbose, save_samples=not args.no_samples)
        
        if args.test:
            # Run specific test
            test_methods = {
                'spotify': suite.test_spotify_data_extraction,
                'lastfm': suite.test_lastfm_data_extraction,
                'artist': suite.test_artist_mode_extraction,
                'large': suite.test_large_frame_count,
                'single': suite.test_edge_case_single_bar,
                'no-nightingale': suite.test_edge_case_no_nightingale,
                'aggregation': suite.test_frame_aggregation,
                'json': suite.test_json_serialization_comprehensive,
                'memory': suite.test_memory_usage_analysis,
            }
            
            if args.test in test_methods:
                success = suite.run_test(args.test, test_methods[args.test])
                suite.print_summary()
                return 0 if success else 1
            else:
                print(f"Unknown test: {args.test}")
                print(f"Available tests: {', '.join(test_methods.keys())}")
                return 1
        else:
            # Run all tests
            suite.run_all_tests()
            
            # Return appropriate exit code
            failed = sum(1 for r in suite.test_results if r['status'] in ['FAIL', 'ERROR'])
            return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())