#!/usr/bin/env python3
"""
Phase 2 Manual Test Suite - Interactive Menu

Comprehensive manual testing for the stateless parallel frame renderer.
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


def show_main_menu():
    """Display the main interactive menu"""
    while True:
        print("\n" + "=" * 60)
        print("🧪 PHASE 2 MANUAL TEST SUITE")
        print("Stateless Parallel Frame Renderer Testing")
        print("=" * 60)
        print()
        print("Setup & Information:")
        print("  [1] 🔧 Setup Test Environment")
        print("  [2] ⚙️  Show Configuration Info")
        print()
        print("Core Functionality Tests:")
        print("  [3] 🎨 Single Frame Rendering Test")
        print("  [4] 🎬 Multiple Frames Sequential Test")
        print("  [5] 🚀 Multiprocess Simulation Test")
        print("  [6] 📊 Real Data Integration Test")
        print()
        print("Advanced Tests:")
        print("  [7] 🔒 Security Validation Test")
        print("  [8] ⚠️  Error Handling Test")
        print("  [9] 🏃 Performance Benchmark")
        print()
        print("Utilities:")
        print("  [10] 🧹 Clean Up Test Files")
        print("  [0] 🚪 Exit")
        print()
        
        try:
            choice = input("Select test [0-10]: ").strip()
            
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
            
            else:
                print("❌ Invalid choice. Please enter a number from 0-10.")
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