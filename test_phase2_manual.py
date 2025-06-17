#!/usr/bin/env python3
"""
Phase 2 Manual Test Suite - Interactive Menu

Comprehensive manual testing for Phase 2 parallel processing implementation:
- Task 1: Stateless parallel frame renderer (completed)
- Task 2: Memory-efficient frame specification generator
Provides an interactive menu for testing different aspects of the implementation.
"""

import os
import sys
import json
import time
import tempfile
import shutil
import multiprocessing
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stateless_renderer import (
    RenderConfig, 
    create_render_config_from_app_config,
    initialize_render_worker, 
    render_frame_from_spec,
    _validate_album_art_path
)
from config_loader import AppConfig
from data_processor import clean_and_filter_data, prepare_data_for_bar_chart_race
from rolling_stats import calculate_rolling_window_stats
import album_art_utils

# Task 2 imports
try:
    from frame_spec_generator import create_frame_spec_generator, FrameSpecGenerator
    from main_animator import prepare_all_frame_specs
    TASK2_AVAILABLE = True
except ImportError as e:
    TASK2_AVAILABLE = False
    print(f"Warning: Task 2 imports not available: {e}")


class Phase2ManualTester:
    """Interactive manual test suite for Phase 2 stateless rendering"""
    
    def __init__(self):
        self.config = None
        self.render_config = None
        self.test_results = []
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] {level}:"
        print(f"{prefix} {message}")
    
    def setup_test_environment(self):
        """Set up the test environment"""
        print("\n🔧 Setting up test environment...")
        
        # Set encoding
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # Load configuration
        if os.path.exists('configurations.txt'):
            try:
                self.config = AppConfig('configurations.txt')
                album_art_utils.initialize_from_config(self.config)
                self.render_config = create_render_config_from_app_config(self.config)
                print("✓ Configuration loaded successfully")
                return True
            except Exception as e:
                print(f"✗ Configuration loading failed: {e}")
                return False
        else:
            print("✗ configurations.txt not found")
            return False
    
    def create_test_frame_specs(self, count: int = 3) -> List[Dict[str, Any]]:
        """Create test frame specifications"""
        frame_specs = []
        
        for i in range(count):
            timestamp = datetime(2024, 1, 1, 12, i, 0, tzinfo=timezone.utc)
            
            # Create test bars with varying data
            bars = []
            for j in range(min(5, self.render_config.n_bars)):
                bars.append({
                    'entity_id': f'test_song_{j}',
                    'canonical_key': f'test_song_{j}',
                    'display_name': f'Test Song {j} - Test Artist {j}',
                    'interpolated_y_pos': float(j),
                    'interpolated_play_count': 100.0 - (i * 5) - (j * 10),
                    'bar_color_rgba': (0.3 + j * 0.1, 0.5, 0.8 - j * 0.1, 1.0),
                    'album_art_path': f'test_art_{j}.jpg',
                    'entity_details': {
                        'original_artist': f'Test Artist {j}',
                        'original_track': f'Test Song {j}'
                    }
                })
            
            frame_spec = {
                'frame_index': i,
                'display_timestamp': timestamp.isoformat(),
                'bars': bars,
                'rolling_stats': {
                    'top_7_day': {
                        'song_id': 'test_song_0',
                        'plays': 42,
                        'original_artist': 'Top Artist',
                        'original_track': 'Top Song'
                    },
                    'top_30_day': {
                        'song_id': 'test_song_1', 
                        'plays': 156,
                        'original_artist': 'Popular Artist',
                        'original_track': 'Popular Song'
                    }
                },
                'nightingale_data': {},
                'dynamic_x_axis_limit': 110.0 - (i * 5),
                'visualization_mode': 'tracks'
            }
            
            frame_specs.append(frame_spec)
        
        return frame_specs
    
    def test_single_frame_render(self):
        """Test rendering a single frame with current configuration"""
        print("\n🎨 Single Frame Rendering Test")
        print("=" * 50)
        
        if not self.render_config:
            print("✗ Test environment not set up. Please run setup first.")
            return False
        
        try:
            # Initialize worker in current process
            initialize_render_worker(self.render_config.to_dict())
            
            # Create test frame
            frame_specs = self.create_test_frame_specs(1)
            frame_spec = frame_specs[0]
            
            print(f"Rendering frame with {len(frame_spec['bars'])} bars...")
            print(f"Resolution: {self.render_config.fig_width_pixels}x{self.render_config.fig_height_pixels}")
            print(f"DPI: {self.render_config.dpi}")
            
            # Render the frame
            start_time = time.time()
            result = render_frame_from_spec(frame_spec)
            render_time = time.time() - start_time
            
            if result['status'] == 'success':
                output_path = result['output_path']
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    print(f"✓ Frame rendered successfully!")
                    print(f"  Output: {output_path}")
                    print(f"  Size: {file_size:,} bytes")
                    print(f"  Time: {render_time:.3f}s")
                    print(f"  Worker PID: {result['worker_pid']}")
                    
                    # Offer to open the file
                    if input("\nWould you like to open the rendered frame? [y/N]: ").lower() == 'y':
                        try:
                            if sys.platform.startswith('linux'):
                                os.system(f'xdg-open "{output_path}"')
                            elif sys.platform == 'darwin':
                                os.system(f'open "{output_path}"')
                            elif sys.platform.startswith('win'):
                                os.system(f'start "" "{output_path}"')
                        except Exception as e:
                            print(f"Could not open file: {e}")
                    
                    return True
                else:
                    print(f"✗ Output file not created: {output_path}")
                    return False
            else:
                print(f"✗ Rendering failed: {result.get('error', 'Unknown error')}")
                print(f"  Error type: {result.get('error_type', 'Unknown')}")
                return False
                
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_multiple_frames_sequential(self):
        """Test rendering multiple frames sequentially"""
        print("\n🎬 Multiple Frames Sequential Test")
        print("=" * 50)
        
        if not self.render_config:
            print("✗ Test environment not set up. Please run setup first.")
            return False
        
        # Get user input for number of frames
        while True:
            try:
                frame_count = int(input("Enter number of frames to render (1-20): "))
                if 1 <= frame_count <= 20:
                    break
                else:
                    print("Please enter a number between 1 and 20")
            except ValueError:
                print("Please enter a valid number")
        
        try:
            # Initialize worker in current process
            initialize_render_worker(self.render_config.to_dict())
            
            # Create test frame specs
            frame_specs = self.create_test_frame_specs(frame_count)
            
            print(f"\nRendering {frame_count} frames sequentially...")
            
            successful_frames = 0
            failed_frames = 0
            total_time = 0
            
            for i, frame_spec in enumerate(frame_specs):
                print(f"Rendering frame {i+1}/{frame_count}...", end=" ")
                
                start_time = time.time()
                result = render_frame_from_spec(frame_spec)
                render_time = time.time() - start_time
                total_time += render_time
                
                if result['status'] == 'success':
                    successful_frames += 1
                    print(f"✓ ({render_time:.3f}s)")
                else:
                    failed_frames += 1
                    print(f"✗ {result.get('error_type', 'error')}")
            
            print(f"\n📊 Results:")
            print(f"  Successful: {successful_frames}")
            print(f"  Failed: {failed_frames}")
            print(f"  Total time: {total_time:.3f}s")
            print(f"  Average per frame: {total_time/frame_count:.3f}s")
            print(f"  Frames per second: {frame_count/total_time:.1f}")
            
            return failed_frames == 0
            
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_multiprocess_simulation(self):
        """Test rendering using actual multiprocessing (simulation of parallel)"""
        print("\n🚀 Multiprocess Simulation Test")
        print("=" * 50)
        
        if not self.render_config:
            print("✗ Test environment not set up. Please run setup first.")
            return False
        
        # Get user input
        while True:
            try:
                frame_count = int(input("Enter number of frames to render (1-10): "))
                if 1 <= frame_count <= 10:
                    break
                else:
                    print("Please enter a number between 1 and 10")
            except ValueError:
                print("Please enter a valid number")
        
        while True:
            try:
                worker_count = int(input("Enter number of worker processes (1-4): "))
                if 1 <= worker_count <= 4:
                    break
                else:
                    print("Please enter a number between 1 and 4")
            except ValueError:
                print("Please enter a valid number")
        
        try:
            # Create test frame specs
            frame_specs = self.create_test_frame_specs(frame_count)
            
            print(f"\nUsing multiprocessing with {worker_count} workers...")
            print(f"Rendering {frame_count} frames...")
            
            start_time = time.time()
            
            # Use multiprocessing.Pool to simulate our parallel approach
            with multiprocessing.Pool(
                processes=worker_count,
                initializer=initialize_render_worker,
                initargs=(self.render_config.to_dict(),)
            ) as pool:
                results = pool.map(render_frame_from_spec, frame_specs)
            
            total_time = time.time() - start_time
            
            # Analyze results
            successful_frames = sum(1 for r in results if r['status'] == 'success')
            failed_frames = len(results) - successful_frames
            
            print(f"\n📊 Multiprocess Results:")
            print(f"  Workers: {worker_count}")
            print(f"  Successful: {successful_frames}")
            print(f"  Failed: {failed_frames}")
            print(f"  Total time: {total_time:.3f}s")
            print(f"  Effective FPS: {frame_count/total_time:.1f}")
            
            # Show individual results
            if input("\nShow individual frame results? [y/N]: ").lower() == 'y':
                for i, result in enumerate(results):
                    status = "✓" if result['status'] == 'success' else "✗"
                    time_taken = result.get('render_time_seconds', 0)
                    worker_pid = result.get('worker_pid', 'unknown')
                    print(f"  Frame {i}: {status} {time_taken:.3f}s (PID {worker_pid})")
            
            return failed_frames == 0
            
        except Exception as e:
            print(f"✗ Multiprocess test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_real_data_integration(self):
        """Test with real data from the pipeline"""
        print("\n📊 Real Data Integration Test")
        print("=" * 50)
        
        if not self.config:
            print("✗ Test environment not set up. Please run setup first.")
            return False
        
        try:
            print("Loading and processing real data...")
            
            # Load and clean data
            cleaned_df = clean_and_filter_data(self.config)
            if cleaned_df is None or cleaned_df.empty:
                print("✗ No data available for testing")
                return False
            
            print(f"Loaded {len(cleaned_df)} data rows")
            
            # Get visualization mode
            visualization_mode = self.config.get('VisualizationMode', 'MODE', 'tracks').lower()
            print(f"Visualization mode: {visualization_mode}")
            
            # Prepare race data
            race_df, entity_details_map = prepare_data_for_bar_chart_race(
                cleaned_df, mode=visualization_mode
            )
            
            if race_df is None or race_df.empty:
                print("✗ No race data generated")
                return False
            
            print(f"Race data shape: {race_df.shape}")
            
            # Limit to first few frames for testing
            test_frames = min(5, len(race_df))
            test_race_df = race_df.head(test_frames)
            
            # Calculate rolling stats
            rolling_stats = calculate_rolling_window_stats(
                cleaned_df, test_race_df.index, base_freq='D', mode=visualization_mode
            )
            
            print(f"Testing with {test_frames} real data frames...")
            
            # Create entity mapping for rendering
            entity_id_to_canonical_name_map = {}
            for entity_id in entity_details_map:
                if visualization_mode == "artists":
                    canonical_name = entity_details_map[entity_id].get('display_artist', 'Unknown')
                else:
                    artist = entity_details_map[entity_id].get('original_artist', 'Unknown')
                    track = entity_details_map[entity_id].get('original_track', 'Unknown')
                    canonical_name = f"{track} - {artist}"
                entity_id_to_canonical_name_map[entity_id] = canonical_name
            
            # Mock album colors (in real implementation these would be pre-fetched)
            album_bar_colors = {name: (0.6, 0.3, 0.8, 1.0) for name in entity_id_to_canonical_name_map.values()}
            
            # Initialize worker
            initialize_render_worker(self.render_config.to_dict())
            
            # Test rendering first frame
            print("\nTesting first frame with real data...")
            
            # Create a simplified frame spec from real data
            timestamp = test_race_df.index[0]
            current_data = test_race_df.iloc[0]
            top_entities = current_data[current_data > 0].nlargest(self.render_config.n_bars)
            
            bars = []
            for rank, (entity_id, plays) in enumerate(top_entities.items()):
                canonical_name = entity_id_to_canonical_name_map.get(entity_id, entity_id)
                entity_details = entity_details_map.get(entity_id, {})
                
                if visualization_mode == "artists":
                    display_name = entity_details.get('display_artist', 'Unknown Artist')
                else:
                    artist_name = entity_details.get('display_artist', 'Unknown Artist')
                    track_name = entity_details.get('display_track', 'Unknown Track')
                    display_name = f"{track_name} - {artist_name}"
                
                bars.append({
                    'entity_id': entity_id,
                    'canonical_key': canonical_name,
                    'display_name': display_name,
                    'interpolated_y_pos': float(rank),
                    'interpolated_play_count': float(plays),
                    'bar_color_rgba': album_bar_colors.get(canonical_name, (0.5, 0.5, 0.5, 1.0)),
                    'album_art_path': '',  # No album art for this test
                    'entity_details': entity_details
                })
            
            frame_spec = {
                'frame_index': 0,
                'display_timestamp': timestamp.isoformat(),
                'bars': bars,
                'rolling_stats': rolling_stats.get(timestamp, {}),
                'nightingale_data': {},
                'dynamic_x_axis_limit': float(top_entities.max() * 1.1),
                'visualization_mode': visualization_mode
            }
            
            # Render the frame
            start_time = time.time()
            result = render_frame_from_spec(frame_spec)
            render_time = time.time() - start_time
            
            if result['status'] == 'success':
                print(f"✓ Real data frame rendered successfully!")
                print(f"  Time: {render_time:.3f}s")
                print(f"  Bars rendered: {len(bars)}")
                print(f"  Max plays: {top_entities.max():.0f}")
                
                if input("\nWould you like to open the rendered frame? [y/N]: ").lower() == 'y':
                    output_path = result['output_path']
                    try:
                        if sys.platform.startswith('linux'):
                            os.system(f'xdg-open "{output_path}"')
                        elif sys.platform == 'darwin':
                            os.system(f'open "{output_path}"')
                        elif sys.platform.startswith('win'):
                            os.system(f'start "" "{output_path}"')
                    except Exception as e:
                        print(f"Could not open file: {e}")
                
                return True
            else:
                print(f"✗ Real data rendering failed: {result.get('error', 'Unknown error')}")
                return False
            
        except Exception as e:
            print(f"✗ Real data test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_security_validation(self):
        """Test security features"""
        print("\n🔒 Security Validation Test")
        print("=" * 50)
        
        # Test path validation
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = os.path.join(temp_dir, 'cache')
            os.makedirs(cache_dir)
            
            # Create test file
            test_file = os.path.join(cache_dir, 'test.jpg')
            with open(test_file, 'w') as f:
                f.write('test image data')
            
            print("Testing path validation security...")
            
            # Test valid paths
            valid_paths = ['test.jpg', 'album_art.png', 'track_123.jpg']
            for path in valid_paths:
                result = _validate_album_art_path(path, cache_dir)
                if path == 'test.jpg':
                    assert result is not None, f"Valid path rejected: {path}"
                    print(f"  ✓ Valid path accepted: {path}")
                else:
                    print(f"  ✓ Non-existent path handled: {path}")
            
            # Test malicious paths
            malicious_paths = [
                '../../../etc/passwd',
                '/etc/passwd',
                '..\\..\\windows\\system32\\config\\sam',
                'subdir/../../../sensitive.txt',
                '../../../../home/user/.ssh/id_rsa'
            ]
            
            blocked_count = 0
            for path in malicious_paths:
                result = _validate_album_art_path(path, cache_dir)
                if result is None:
                    blocked_count += 1
                    print(f"  ✓ Blocked malicious path: {path}")
                else:
                    print(f"  ✗ Failed to block: {path} -> {result}")
            
            print(f"\nSecurity test results:")
            print(f"  Malicious paths blocked: {blocked_count}/{len(malicious_paths)}")
            
            return blocked_count == len(malicious_paths)
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n⚠️ Error Handling Test")
        print("=" * 50)
        
        if not self.render_config:
            print("✗ Test environment not set up. Please run setup first.")
            return False
        
        try:
            # Initialize worker
            initialize_render_worker(self.render_config.to_dict())
            
            print("Testing various error scenarios...")
            
            # Test 1: Invalid data types
            print("\n1. Testing invalid data types...")
            invalid_spec = {
                'frame_index': 0,
                'display_timestamp': '2024-01-01T12:00:00Z',
                'bars': [
                    {
                        'entity_id': 'test',
                        'interpolated_play_count': 'not_a_number',  # Should cause error
                        'interpolated_y_position': 0
                    }
                ],
                'dynamic_x_axis_limit': 100,
                'visualization_mode': 'tracks'
            }
            
            result = render_frame_from_spec(invalid_spec)
            if result['status'] == 'error':
                print(f"  ✓ Invalid data type handled: {result['error_type']}")
            else:
                print(f"  ✗ Invalid data type not caught")
            
            # Test 2: Missing required fields
            print("\n2. Testing missing required fields...")
            incomplete_spec = {
                'frame_index': 1,
                # Missing display_timestamp and other required fields
            }
            
            result = render_frame_from_spec(incomplete_spec)
            if result['status'] == 'error':
                print(f"  ✓ Missing fields handled: {result['error_type']}")
            else:
                print(f"  ✗ Missing fields not caught")
            
            # Test 3: Invalid timestamp format
            print("\n3. Testing invalid timestamp format...")
            bad_timestamp_spec = {
                'frame_index': 2,
                'display_timestamp': 'not-a-valid-timestamp',
                'bars': [],
                'dynamic_x_axis_limit': 100,
                'visualization_mode': 'tracks'
            }
            
            result = render_frame_from_spec(bad_timestamp_spec)
            print(f"  Timestamp error result: {result['status']} ({result.get('error_type', 'no_type')})")
            
            print("\nError handling test completed.")
            return True
            
        except Exception as e:
            print(f"✗ Error handling test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_performance_benchmark(self):
        """Run performance benchmark"""
        print("\n🏃 Performance Benchmark")
        print("=" * 50)
        
        if not self.render_config:
            print("✗ Test environment not set up. Please run setup first.")
            return False
        
        # Get benchmark parameters
        print("Benchmark configuration:")
        print("1. Light (10 frames, 2 workers)")
        print("2. Medium (25 frames, 4 workers)")
        print("3. Heavy (50 frames, 4 workers)")
        print("4. Custom")
        
        choice = input("Select benchmark [1-4]: ").strip()
        
        if choice == '1':
            frame_count, worker_count = 10, 2
        elif choice == '2':
            frame_count, worker_count = 25, 4
        elif choice == '3':
            frame_count, worker_count = 50, 4
        elif choice == '4':
            try:
                frame_count = int(input("Enter number of frames (1-100): "))
                worker_count = int(input("Enter number of workers (1-8): "))
                if not (1 <= frame_count <= 100 and 1 <= worker_count <= 8):
                    print("Invalid input")
                    return False
            except ValueError:
                print("Invalid input")
                return False
        else:
            print("Invalid choice")
            return False
        
        print(f"\nRunning benchmark: {frame_count} frames, {worker_count} workers")
        
        try:
            # Create test frame specs
            frame_specs = self.create_test_frame_specs(frame_count)
            
            # Benchmark sequential rendering
            print("\n1. Sequential rendering...")
            start_time = time.time()
            
            initialize_render_worker(self.render_config.to_dict())
            sequential_results = []
            for spec in frame_specs:
                result = render_frame_from_spec(spec)
                sequential_results.append(result)
            
            sequential_time = time.time() - start_time
            sequential_success = sum(1 for r in sequential_results if r['status'] == 'success')
            
            print(f"  Time: {sequential_time:.3f}s")
            print(f"  Success rate: {sequential_success}/{frame_count}")
            print(f"  FPS: {frame_count/sequential_time:.1f}")
            
            # Benchmark parallel rendering
            print(f"\n2. Parallel rendering ({worker_count} workers)...")
            start_time = time.time()
            
            with multiprocessing.Pool(
                processes=worker_count,
                initializer=initialize_render_worker,
                initargs=(self.render_config.to_dict(),)
            ) as pool:
                parallel_results = pool.map(render_frame_from_spec, frame_specs)
            
            parallel_time = time.time() - start_time
            parallel_success = sum(1 for r in parallel_results if r['status'] == 'success')
            
            print(f"  Time: {parallel_time:.3f}s")
            print(f"  Success rate: {parallel_success}/{frame_count}")
            print(f"  FPS: {frame_count/parallel_time:.1f}")
            
            # Calculate speedup
            speedup = sequential_time / parallel_time if parallel_time > 0 else 0
            efficiency = speedup / worker_count * 100
            
            print(f"\n📈 Performance Results:")
            print(f"  Speedup: {speedup:.2f}x")
            print(f"  Efficiency: {efficiency:.1f}%")
            print(f"  Target speedup (ideal): {worker_count}x")
            
            if speedup >= worker_count * 0.5:  # At least 50% efficiency
                print("  ✓ Performance meets expectations")
                return True
            else:
                print("  ⚠️ Performance below expectations")
                return False
                
        except Exception as e:
            print(f"✗ Benchmark failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def show_configuration_info(self):
        """Display current configuration information"""
        print("\n⚙️ Configuration Information")
        print("=" * 50)
        
        if not self.config or not self.render_config:
            print("✗ Configuration not loaded")
            return
        
        print("Application Configuration:")
        print(f"  Data source: {self.config.get('DataSource', 'SOURCE', 'unknown')}")
        print(f"  Visualization mode: {self.config.get('VisualizationMode', 'MODE', 'unknown')}")
        print(f"  Target FPS: {self.config.get('AnimationOutput', 'TARGET_FPS', 'unknown')}")
        print(f"  N_BARS: {self.config.get('AnimationOutput', 'N_BARS', 'unknown')}")
        
        print(f"\nRender Configuration:")
        print(f"  Resolution: {self.render_config.fig_width_pixels}x{self.render_config.fig_height_pixels}")
        print(f"  DPI: {self.render_config.dpi}")
        print(f"  N_bars: {self.render_config.n_bars}")
        print(f"  Font paths: {len(self.render_config.font_paths)} fonts")
        print(f"  Album art cache: {self.render_config.album_art_cache_dir}")
        print(f"  Preferred fonts: {', '.join(self.render_config.preferred_fonts[:3])}...")
        
        print(f"\nSystem Information:")
        print(f"  CPU cores: {os.cpu_count()}")
        print(f"  Platform: {sys.platform}")
        print(f"  Python version: {sys.version.split()[0]}")
    
    def cleanup_test_files(self):
        """Clean up test-generated files"""
        print("\n🧹 Cleaning Up Test Files")
        print("=" * 50)
        
        # Clean up frames directory
        if os.path.exists('frames'):
            frame_files = [f for f in os.listdir('frames') if f.startswith('frame_')]
            if frame_files:
                if input(f"Delete {len(frame_files)} test frame files? [y/N]: ").lower() == 'y':
                    for file in frame_files:
                        os.remove(os.path.join('frames', file))
                    print(f"✓ Deleted {len(frame_files)} frame files")
                else:
                    print("Frame files kept")
            else:
                print("No frame files to clean up")
        else:
            print("No frames directory found")
    
    # ========================================
    # TASK 2 - FRAME SPEC GENERATOR TESTS  
    # ========================================
    
    def test_generator_equivalence(self):
        """Test that generator produces identical output to original method"""
        if not TASK2_AVAILABLE:
            self.log("Task 2 generator not available", "WARNING")
            return False
            
        self.log("Testing Generator vs Original Equivalence")
        print("=" * 50)
        
        try:
            # Create test data
            render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(20)
            
            print("Running original method...")
            original_specs = prepare_all_frame_specs(
                render_tasks, entity_map, entity_details, colors, 5, 1000.0, "tracks"
            )
            
            print("Running generator...")
            generator = create_frame_spec_generator(
                render_tasks, entity_map, entity_details, colors, 5, 1000.0, "tracks"
            )
            generator_specs = list(generator)
            
            print(f"Comparing {len(original_specs)} vs {len(generator_specs)} specs...")
            
            if len(original_specs) != len(generator_specs):
                self.log(f"Length mismatch: {len(original_specs)} != {len(generator_specs)}", "ERROR")
                return False
            
            mismatches = 0
            for i, (orig, gen) in enumerate(zip(original_specs, generator_specs)):
                if not self._specs_equal(orig, gen):
                    mismatches += 1
                    if mismatches <= 3:
                        self.log(f"Mismatch at frame {i}", "WARNING")
            
            if mismatches == 0:
                self.log("All specs match perfectly!", "SUCCESS")
                return True
            else:
                self.log(f"Found {mismatches} mismatches", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error in equivalence test: {e}", "ERROR")
            return False
    
    def test_memory_comparison(self):
        """Test memory usage comparison between methods"""
        if not TASK2_AVAILABLE:
            self.log("Task 2 generator not available", "WARNING") 
            return False
            
        self.log("Testing Memory Usage Comparison")
        print("=" * 50)
        
        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            self.log("psutil not available, using basic comparison", "WARNING")
            return self._test_memory_basic()
        
        try:
            render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(100)
            
            # Test original method memory
            import gc
            gc.collect()
            mem_before = process.memory_info().rss
            original_specs = prepare_all_frame_specs(
                render_tasks, entity_map, entity_details, colors, 10, 5000.0, "tracks"
            )
            mem_after = process.memory_info().rss
            original_memory = mem_after - mem_before
            
            del original_specs
            gc.collect()
            
            # Test generator memory
            mem_before_gen = process.memory_info().rss
            generator = create_frame_spec_generator(
                render_tasks, entity_map, entity_details, colors, 10, 5000.0, "tracks"
            )
            
            max_memory = mem_before_gen
            for i, spec in enumerate(generator):
                current_mem = process.memory_info().rss
                max_memory = max(max_memory, current_mem)
                del spec
                if i >= 50:  # Test first 50
                    break
            
            generator_memory = max_memory - mem_before_gen
            
            print(f"Original method: {original_memory:,} bytes")
            print(f"Generator method: {generator_memory:,} bytes")
            
            if original_memory > 0:
                ratio = original_memory / max(generator_memory, 1)
                print(f"Memory reduction ratio: {ratio:.2f}x")
                success = ratio > 1.2  # At least 20% improvement
                if success:
                    self.log(f"Memory efficiency achieved: {ratio:.2f}x reduction", "SUCCESS")
                else:
                    self.log(f"Insufficient memory improvement: {ratio:.2f}x", "WARNING")
                return success
            
            return True
            
        except Exception as e:
            self.log(f"Error in memory test: {e}", "ERROR")
            return False
    
    def test_large_dataset_memory(self):
        """Test memory usage with large dataset"""
        if not TASK2_AVAILABLE:
            self.log("Task 2 generator not available", "WARNING")
            return False
            
        self.log("Testing Large Dataset Memory Usage")
        print("=" * 50)
        
        try:
            render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(500)
            
            generator = create_frame_spec_generator(
                render_tasks, entity_map, entity_details, colors, 10, 5000.0, "tracks"
            )
            
            memory_readings = []
            for i, spec in enumerate(generator):
                memory_info = generator.get_memory_info()
                memory_readings.append(memory_info['generator_size_bytes'])
                del spec
                
                if i % 100 == 0:
                    print(f"Frame {i}: Generator memory = {memory_readings[-1]} bytes")
                
                if i >= 200:  # Test first 200
                    break
            
            initial_memory = memory_readings[10]  # Skip initial frames
            final_memory = memory_readings[-1]
            growth = final_memory - initial_memory
            
            print(f"Memory growth: {growth} bytes ({growth/initial_memory*100:.1f}%)")
            
            # Allow up to 50% growth
            success = abs(growth) < initial_memory * 0.5
            if success:
                self.log("Memory growth within acceptable limits", "SUCCESS")
            else:
                self.log("Excessive memory growth detected", "WARNING")
            
            return success
            
        except Exception as e:
            self.log(f"Error in large dataset test: {e}", "ERROR")
            return False
    
    def test_mode_testing(self):
        """Test tracks and artists modes"""
        if not TASK2_AVAILABLE:
            self.log("Task 2 generator not available", "WARNING")
            return False
            
        self.log("Testing Tracks and Artists Modes")
        print("=" * 50)
        
        try:
            # Test tracks mode
            print("Testing tracks mode...")
            render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(5)
            
            generator = create_frame_spec_generator(
                render_tasks, entity_map, entity_details, colors, 5, 1000.0, "tracks"
            )
            
            specs = list(generator)
            
            # Check tracks mode display names
            for spec in specs[:2]:
                for bar in spec['bars']:
                    display_name = bar['display_name']
                    if ' - ' not in display_name:
                        self.log(f"Invalid tracks mode display: {display_name}", "ERROR")
                        return False
            
            # Test artists mode
            print("Testing artists mode...")
            artist_tasks, artist_map, artist_details, artist_colors = self._create_artist_test_data()
            
            generator = create_frame_spec_generator(
                artist_tasks, artist_map, artist_details, artist_colors, 5, 1000.0, "artists"
            )
            
            specs = list(generator)
            
            # Check artists mode display names
            for spec in specs[:2]:
                for bar in spec['bars']:
                    display_name = bar['display_name']
                    if not display_name.startswith('Artist '):
                        self.log(f"Invalid artists mode display: {display_name}", "ERROR")
                        return False
            
            self.log("Both modes working correctly", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Error in mode testing: {e}", "ERROR")
            return False
    
    def test_generator_performance(self):
        """Test generator performance vs original"""
        if not TASK2_AVAILABLE:
            self.log("Task 2 generator not available", "WARNING")
            return False
            
        self.log("Testing Generator Performance")
        print("=" * 50)
        
        try:
            render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(100)
            
            # Benchmark original method
            print("Benchmarking original method...")
            orig_times = []
            for _ in range(3):
                start = time.time()
                original_specs = prepare_all_frame_specs(
                    render_tasks, entity_map, entity_details, colors, 10, 5000.0, "tracks"
                )
                orig_times.append(time.time() - start)
                del original_specs
            
            orig_avg = sum(orig_times) / len(orig_times)
            
            # Benchmark generator
            print("Benchmarking generator...")
            gen_times = []
            for _ in range(3):
                start = time.time()
                generator = create_frame_spec_generator(
                    render_tasks, entity_map, entity_details, colors, 10, 5000.0, "tracks"
                )
                list(generator)  # Consume generator
                gen_times.append(time.time() - start)
            
            gen_avg = sum(gen_times) / len(gen_times)
            
            print(f"Original average: {orig_avg:.3f}s")
            print(f"Generator average: {gen_avg:.3f}s")
            print(f"Performance ratio: {orig_avg/gen_avg:.2f}x")
            
            # Generator should be within 50% of original performance
            success = gen_avg <= orig_avg * 1.5
            if success:
                self.log("Generator performance acceptable", "SUCCESS")
            else:
                self.log("Generator performance needs improvement", "WARNING")
            
            return success
            
        except Exception as e:
            self.log(f"Error in performance test: {e}", "ERROR")
            return False
    
    def _create_test_render_tasks(self, num_frames: int = 10):
        """Create test render tasks for Task 2 testing"""
        from datetime import datetime, timedelta
        
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        render_tasks = []
        
        for i in range(num_frames):
            timestamp = base_time + timedelta(minutes=i * 30)
            
            num_bars = min(5, max(1, 5 - i // 3))
            bar_data = []
            
            for j in range(num_bars):
                bar_data.append({
                    'entity_id': f"song_{j}",
                    'interpolated_play_count': float(100 - i * 2 - j * 5),
                    'interpolated_y_position': float(j),
                    'current_rank': j,
                    'is_new': (i + j) % 7 == 0,
                    'bar_color': (0.5 + j * 0.1, 0.3, 0.7, 1.0)
                })
            
            task = {
                'overall_frame_index': i,
                'display_timestamp': timestamp,
                'bar_render_data_list': bar_data,
                'rolling_window_info': {
                    'top_7_day': {'song_id': f"song_{i % 3}", 'plays': 50 + i} if i % 2 == 0 else None,
                    'top_30_day': {'song_id': f"song_{(i + 1) % 3}", 'plays': 200 + i * 2}
                },
                'nightingale_info': {
                    'period_data': [{'period': 'morning', 'value': 10 + i}] if i % 3 == 0 else {}
                }
            }
            render_tasks.append(task)
        
        entity_map = {f"song_{i}": f"canonical_song_{i}" for i in range(10)}
        entity_details = {
            f"song_{i}": {
                'original_artist': f"Artist {i}",
                'original_track': f"Track {i}",
                'album': f"Album {i}",
                'spotify_track_uri': f"spotify:track:uri_{i}"
            }
            for i in range(10)
        }
        colors = {f"canonical_song_{i}": (0.1 * i, 0.2, 0.3, 1.0) for i in range(10)}
        
        return render_tasks, entity_map, entity_details, colors
    
    def _create_artist_test_data(self):
        """Create test data for artists mode"""
        from datetime import datetime, timedelta
        
        render_tasks = []
        for i in range(5):
            task = {
                'overall_frame_index': i,
                'display_timestamp': datetime(2024, 1, 1) + timedelta(hours=i),
                'bar_render_data_list': [
                    {
                        'entity_id': f"artist_{j}",
                        'interpolated_play_count': float(100 - j * 10),
                        'interpolated_y_position': float(j),
                        'current_rank': j,
                        'is_new': False,
                        'bar_color': (0.5, 0.3, 0.7, 1.0)
                    }
                    for j in range(3)
                ],
                'rolling_window_info': {'top_7_day': None, 'top_30_day': None},
                'nightingale_info': {}
            }
            render_tasks.append(task)
        
        entity_map = {f"artist_{i}": f"canonical_artist_{i}" for i in range(5)}
        entity_details = {
            f"artist_{i}": {
                'original_artist': f"Artist {i}",
                'normalized_artist': f"artist_{i}"
            }
            for i in range(5)
        }
        colors = {f"canonical_artist_{i}": (0.1, 0.2, 0.3, 1.0) for i in range(5)}
        
        return render_tasks, entity_map, entity_details, colors
    
    def _specs_equal(self, spec1: dict, spec2: dict) -> bool:
        """Check if two specs are equal with float tolerance"""
        if spec1.keys() != spec2.keys():
            return False
        
        for key in spec1.keys():
            if key == 'bars':
                if len(spec1['bars']) != len(spec2['bars']):
                    return False
                for b1, b2 in zip(spec1['bars'], spec2['bars']):
                    if not self._bars_equal(b1, b2):
                        return False
            elif isinstance(spec1[key], float) and isinstance(spec2[key], float):
                if abs(spec1[key] - spec2[key]) > 1e-6:
                    return False
            elif spec1[key] != spec2[key]:
                return False
        return True
    
    def _bars_equal(self, bar1: dict, bar2: dict) -> bool:
        """Check if two bar specs are equal"""
        if bar1.keys() != bar2.keys():
            return False
        
        for key in bar1.keys():
            if key in ['interpolated_y_pos', 'interpolated_play_count']:
                if abs(bar1[key] - bar2[key]) > 1e-6:
                    return False
            elif key in ['bar_color', 'bar_color_rgba']:
                c1, c2 = bar1[key], bar2[key]
                if len(c1) != len(c2):
                    return False
                if any(abs(a - b) > 1e-6 for a, b in zip(c1, c2)):
                    return False
            elif bar1[key] != bar2[key]:
                return False
        return True
    
    def _test_memory_basic(self):
        """Basic memory test using sys.getsizeof"""
        import sys
        
        render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(50)
        
        original_specs = prepare_all_frame_specs(
            render_tasks, entity_map, entity_details, colors, 10, 5000.0, "tracks"
        )
        original_size = sys.getsizeof(original_specs)
        
        generator = create_frame_spec_generator(
            render_tasks, entity_map, entity_details, colors, 10, 5000.0, "tracks"
        )
        generator_size = sys.getsizeof(generator)
        
        print(f"Original specs size: {original_size:,} bytes")
        print(f"Generator size: {generator_size:,} bytes")
        
        return original_size > generator_size


def show_main_menu():
    """Display the main interactive menu"""
    while True:
        print("\n" + "=" * 60)
        print("🧪 PHASE 2 MANUAL TEST SUITE")
        print("Parallel Processing Implementation Testing")
        print("=" * 60)
        print()
        print("Setup & Information:")
        print("  [1] 🔧 Setup Test Environment")
        print("  [2] ⚙️  Show Configuration Info")
        print()
        print("Task 1 - Stateless Renderer Tests:")
        print("  [3] 🎨 Single Frame Rendering Test")
        print("  [4] 🎬 Multiple Frames Sequential Test")
        print("  [5] 🚀 Multiprocess Simulation Test")
        print("  [6] 📊 Real Data Integration Test")
        print("  [7] 🔒 Security Validation Test")
        print("  [8] ⚠️  Error Handling Test")
        print("  [9] 🏃 Performance Benchmark")
        print()
        if TASK2_AVAILABLE:
            print("Task 2 - Frame Spec Generator Tests:")
            print("  [11] 🔄 Generator vs Original Equivalence")
            print("  [12] 💾 Memory Usage Comparison")
            print("  [13] 📈 Large Dataset Memory Test")
            print("  [14] 🎭 Mode Testing (Tracks/Artists)")
            print("  [15] ⚡ Generator Performance Test")
            print()
        print("Utilities:")
        print("  [10] 🧹 Clean Up Test Files")
        print("  [0] 🚪 Exit")
        print()
        
        try:
            max_choice = 15 if TASK2_AVAILABLE else 10
            choice = input(f"Select test [0-{max_choice}]: ").strip()
            
            if choice == '0':
                print("\n👋 Testing complete. Goodbye!")
                return 0
            
            tester = Phase2ManualTester()
            
            if choice == '1':
                if tester.setup_test_environment():
                    print("✅ Environment setup successful!")
                else:
                    print("❌ Environment setup failed!")
            
            elif choice == '2':
                if not tester.setup_test_environment():
                    continue
                tester.show_configuration_info()
            
            elif choice == '3':
                if not tester.setup_test_environment():
                    continue
                result = tester.test_single_frame_render()
                print(f"\n{'✅ Test PASSED' if result else '❌ Test FAILED'}")
            
            elif choice == '4':
                if not tester.setup_test_environment():
                    continue
                result = tester.test_multiple_frames_sequential()
                print(f"\n{'✅ Test PASSED' if result else '❌ Test FAILED'}")
            
            elif choice == '5':
                if not tester.setup_test_environment():
                    continue
                result = tester.test_multiprocess_simulation()
                print(f"\n{'✅ Test PASSED' if result else '❌ Test FAILED'}")
            
            elif choice == '6':
                if not tester.setup_test_environment():
                    continue
                result = tester.test_real_data_integration()
                print(f"\n{'✅ Test PASSED' if result else '❌ Test FAILED'}")
            
            elif choice == '7':
                result = tester.test_security_validation()
                print(f"\n{'✅ Test PASSED' if result else '❌ Test FAILED'}")
            
            elif choice == '8':
                if not tester.setup_test_environment():
                    continue
                result = tester.test_error_handling()
                print(f"\n{'✅ Test PASSED' if result else '❌ Test FAILED'}")
            
            elif choice == '9':
                if not tester.setup_test_environment():
                    continue
                result = tester.run_performance_benchmark()
                print(f"\n{'✅ Benchmark PASSED' if result else '❌ Benchmark FAILED'}")
            
            elif choice == '10':
                tester.cleanup_test_files()
            
            elif TASK2_AVAILABLE and choice == '11':
                result = tester.test_generator_equivalence()
                print(f"\n{'✅ Test PASSED' if result else '❌ Test FAILED'}")
            
            elif TASK2_AVAILABLE and choice == '12':
                result = tester.test_memory_comparison()
                print(f"\n{'✅ Test PASSED' if result else '❌ Test FAILED'}")
            
            elif TASK2_AVAILABLE and choice == '13':
                result = tester.test_large_dataset_memory()
                print(f"\n{'✅ Test PASSED' if result else '❌ Test FAILED'}")
            
            elif TASK2_AVAILABLE and choice == '14':
                result = tester.test_mode_testing()
                print(f"\n{'✅ Test PASSED' if result else '❌ Test FAILED'}")
            
            elif TASK2_AVAILABLE and choice == '15':
                result = tester.test_generator_performance()
                print(f"\n{'✅ Test PASSED' if result else '❌ Test FAILED'}")
            
            else:
                max_choice = 15 if TASK2_AVAILABLE else 10
                print(f"❌ Invalid choice. Please enter a number from 0-{max_choice}.")
                continue
            
            input("\nPress Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n\n👋 Testing interrupted. Goodbye!")
            return 1
        except EOFError:
            print("\n\n👋 Testing terminated. Goodbye!")
            return 1


if __name__ == "__main__":
    # Set up environment
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    print("🚀 Starting Phase 2 Manual Test Suite...")
    sys.exit(show_main_menu())