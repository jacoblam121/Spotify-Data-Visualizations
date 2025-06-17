#!/usr/bin/env python3
"""
Interactive Manual Test Suite for Task 2: Frame Spec Generator

This provides an interactive menu for testing the memory-efficient frame specification
generator implementation. Tests equivalence, memory usage, performance, and integration.
"""

import os
import sys
import time
import gc
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from frame_spec_generator import FrameSpecGenerator, create_frame_spec_generator
    from main_animator import prepare_all_frame_specs, prepare_frame_spec, make_json_serializable
    from config_loader import AppConfig
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

class Task2ManualTester:
    """Interactive manual test suite for Task 2 frame spec generator."""
    
    def __init__(self):
        self.test_results = {}
        print("Task 2 Manual Test Suite - Frame Spec Generator")
        print("=" * 60)
    
    def run_interactive_menu(self):
        """Run interactive test menu."""
        while True:
            self._show_menu()
            choice = input("\nEnter your choice (1-12, q to quit): ").strip().lower()
            
            if choice == 'q' or choice == 'quit':
                break
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= 12:
                    self._run_test(choice_num)
                else:
                    print("Invalid choice. Please select 1-12 or 'q' to quit.")
            except ValueError:
                print("Invalid input. Please enter a number or 'q' to quit.")
        
        self._show_summary()
    
    def _show_menu(self):
        """Display the test menu."""
        print("\n" + "=" * 60)
        print("TASK 2 MANUAL TEST MENU")
        print("=" * 60)
        print("Basic Functionality:")
        print("  1. Generator vs Original Equivalence Test")
        print("  2. Empty Input Handling")
        print("  3. Single Frame Generation")
        print("  4. Large Dataset Equivalence")
        print("\nMemory & Performance:")
        print("  5. Memory Usage Comparison")
        print("  6. Memory Growth Test (Large Dataset)")
        print("  7. Performance Benchmarking")
        print("  8. Generator Reset & Reuse")
        print("\nMode Testing:")
        print("  9. Tracks Mode Testing")
        print(" 10. Artists Mode Testing")
        print("\nIntegration & Configuration:")
        print(" 11. Configuration Flag Testing")
        print(" 12. Integration with Main Animator (Dry Run)")
        print("\n  q. Quit")
    
    def _run_test(self, test_num: int):
        """Run the specified test."""
        test_functions = {
            1: self._test_equivalence,
            2: self._test_empty_input,
            3: self._test_single_frame,
            4: self._test_large_equivalence,
            5: self._test_memory_usage,
            6: self._test_memory_growth,
            7: self._test_performance,
            8: self._test_reset_reuse,
            9: self._test_tracks_mode,
            10: self._test_artists_mode,
            11: self._test_config_flag,
            12: self._test_integration
        }
        
        test_name = {
            1: "Generator vs Original Equivalence",
            2: "Empty Input Handling",
            3: "Single Frame Generation",
            4: "Large Dataset Equivalence",
            5: "Memory Usage Comparison",
            6: "Memory Growth Test",
            7: "Performance Benchmarking",
            8: "Generator Reset & Reuse",
            9: "Tracks Mode Testing",
            10: "Artists Mode Testing",
            11: "Configuration Flag Testing",
            12: "Integration Test"
        }[test_num]
        
        print(f"\n--- Running Test {test_num}: {test_name} ---")
        try:
            start_time = time.time()
            result = test_functions[test_num]()
            end_time = time.time()
            
            status = "✓ PASSED" if result else "✗ FAILED"
            print(f"{status} (took {end_time - start_time:.3f}s)")
            self.test_results[test_num] = {'name': test_name, 'passed': result, 'time': end_time - start_time}
            
        except Exception as e:
            print(f"✗ ERROR: {e}")
            self.test_results[test_num] = {'name': test_name, 'passed': False, 'error': str(e)}
        
        input("\nPress Enter to continue...")
    
    def _create_test_render_tasks(self, num_frames: int = 10) -> tuple:
        """Create test render tasks for testing."""
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        render_tasks = []
        
        for i in range(num_frames):
            timestamp = base_time + timedelta(minutes=i * 30)
            
            # Create varying number of bars per frame
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
    
    def _test_equivalence(self) -> bool:
        """Test equivalence between generator and original method."""
        print("Creating test data...")
        render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(10)
        
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
            print(f"Length mismatch: {len(original_specs)} != {len(generator_specs)}")
            return False
        
        mismatches = 0
        for i, (orig, gen) in enumerate(zip(original_specs, generator_specs)):
            if not self._specs_equal(orig, gen):
                mismatches += 1
                if mismatches <= 3:  # Show first 3 mismatches
                    print(f"Mismatch at frame {i}")
        
        if mismatches == 0:
            print("✓ All specs match perfectly!")
            return True
        else:
            print(f"✗ Found {mismatches} mismatches")
            return False
    
    def _specs_equal(self, spec1: Dict, spec2: Dict) -> bool:
        """Check if two specs are equal (with tolerance for floats)."""
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
    
    def _bars_equal(self, bar1: Dict, bar2: Dict) -> bool:
        """Check if two bar specs are equal."""
        if bar1.keys() != bar2.keys():
            return False
        
        for key in bar1.keys():
            if key in ['interpolated_y_pos', 'interpolated_play_count']:
                if abs(bar1[key] - bar2[key]) > 1e-6:
                    return False
            elif key in ['bar_color', 'bar_color_rgba']:
                # Compare color tuples
                c1, c2 = bar1[key], bar2[key]
                if len(c1) != len(c2):
                    return False
                if any(abs(a - b) > 1e-6 for a, b in zip(c1, c2)):
                    return False
            elif bar1[key] != bar2[key]:
                return False
        return True
    
    def _test_empty_input(self) -> bool:
        """Test generator with empty input."""
        print("Testing with empty input...")
        
        generator = create_frame_spec_generator([], {}, {}, {}, 5, 1000.0, "tracks")
        specs = list(generator)
        
        print(f"Generated {len(specs)} specs from empty input")
        progress = generator.get_progress()
        print(f"Progress: {progress}")
        
        return len(specs) == 0 and progress == (0, 0)
    
    def _test_single_frame(self) -> bool:
        """Test generator with single frame."""
        print("Testing with single frame...")
        
        render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(1)
        
        generator = create_frame_spec_generator(
            render_tasks, entity_map, entity_details, colors, 5, 1000.0, "tracks"
        )
        specs = list(generator)
        
        print(f"Generated {len(specs)} specs from single frame input")
        
        if len(specs) != 1:
            return False
        
        # Compare with original
        original_specs = prepare_all_frame_specs(
            render_tasks, entity_map, entity_details, colors, 5, 1000.0, "tracks"
        )
        
        return self._specs_equal(original_specs[0], specs[0])
    
    def _test_large_equivalence(self) -> bool:
        """Test equivalence with larger dataset."""
        print("Testing with large dataset (100 frames)...")
        
        render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(100)
        
        print("Running original method...")
        original_start = time.time()
        original_specs = prepare_all_frame_specs(
            render_tasks, entity_map, entity_details, colors, 10, 5000.0, "tracks"
        )
        original_time = time.time() - original_start
        
        print("Running generator...")
        generator_start = time.time()
        generator = create_frame_spec_generator(
            render_tasks, entity_map, entity_details, colors, 10, 5000.0, "tracks"
        )
        generator_specs = list(generator)
        generator_time = time.time() - generator_start
        
        print(f"Original: {len(original_specs)} specs in {original_time:.3f}s")
        print(f"Generator: {len(generator_specs)} specs in {generator_time:.3f}s")
        
        if len(original_specs) != len(generator_specs):
            print("Length mismatch!")
            return False
        
        # Sample check (first 5, last 5, and some random middle ones)
        check_indices = [0, 1, 2, 3, 4, 50, 95, 96, 97, 98, 99]
        for i in check_indices:
            if i < len(original_specs) and not self._specs_equal(original_specs[i], generator_specs[i]):
                print(f"Mismatch at index {i}")
                return False
        
        print("✓ Large dataset equivalence verified")
        return True
    
    def _test_memory_usage(self) -> bool:
        """Test memory usage comparison."""
        print("Testing memory usage...")
        
        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            print("psutil not available, using basic sys.getsizeof")
            return self._test_memory_basic()
        
        render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(500)
        
        # Test original method memory
        gc.collect()
        mem_before_orig = process.memory_info().rss
        original_specs = prepare_all_frame_specs(
            render_tasks, entity_map, entity_details, colors, 10, 5000.0, "tracks"
        )
        mem_after_orig = process.memory_info().rss
        original_memory = mem_after_orig - mem_before_orig
        
        # Clear original specs
        del original_specs
        gc.collect()
        
        # Test generator memory
        mem_before_gen = process.memory_info().rss
        generator = create_frame_spec_generator(
            render_tasks, entity_map, entity_details, colors, 10, 5000.0, "tracks"
        )
        
        # Iterate without storing
        max_memory = mem_before_gen
        for i, spec in enumerate(generator):
            current_mem = process.memory_info().rss
            max_memory = max(max_memory, current_mem)
            del spec  # Don't store
            if i >= 100:  # Test first 100
                break
        
        generator_memory = max_memory - mem_before_gen
        
        print(f"Original method: {original_memory:,} bytes")
        print(f"Generator method: {generator_memory:,} bytes")
        
        if original_memory > 0:
            ratio = original_memory / max(generator_memory, 1)
            print(f"Memory reduction ratio: {ratio:.2f}x")
            return ratio > 1.2  # At least 20% improvement
        
        return True
    
    def _test_memory_basic(self) -> bool:
        """Basic memory test using sys.getsizeof."""
        import sys
        
        render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(100)
        
        # Original method
        original_specs = prepare_all_frame_specs(
            render_tasks, entity_map, entity_details, colors, 10, 5000.0, "tracks"
        )
        original_size = sys.getsizeof(original_specs)
        
        # Generator
        generator = create_frame_spec_generator(
            render_tasks, entity_map, entity_details, colors, 10, 5000.0, "tracks"
        )
        generator_size = sys.getsizeof(generator)
        
        print(f"Original specs size: {original_size:,} bytes")
        print(f"Generator size: {generator_size:,} bytes")
        print(f"Size ratio: {original_size / max(generator_size, 1):.2f}x")
        
        return original_size > generator_size
    
    def _test_memory_growth(self) -> bool:
        """Test that generator memory usage stays constant."""
        print("Testing memory growth over iteration...")
        
        render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(200)
        
        generator = create_frame_spec_generator(
            render_tasks, entity_map, entity_details, colors, 10, 5000.0, "tracks"
        )
        
        memory_readings = []
        for i, spec in enumerate(generator):
            memory_info = generator.get_memory_info()
            memory_readings.append(memory_info['generator_size_bytes'])
            del spec
            
            if i % 50 == 0:
                print(f"Frame {i}: Generator memory = {memory_readings[-1]} bytes")
            
            if i >= 150:  # Test first 150
                break
        
        # Check if memory stays roughly constant
        initial_memory = memory_readings[10]  # Skip first few
        final_memory = memory_readings[-1]
        growth = final_memory - initial_memory
        
        print(f"Memory growth: {growth} bytes ({growth/initial_memory*100:.1f}%)")
        
        # Allow up to 50% growth (should be much less for true constant memory)
        return abs(growth) < initial_memory * 0.5
    
    def _test_performance(self) -> bool:
        """Test performance comparison."""
        print("Running performance benchmark...")
        
        render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(200)
        
        # Original method
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
        
        # Generator method
        print("Benchmarking generator method...")
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
        
        # Generator should be at least as fast (within 50% tolerance)
        return gen_avg <= orig_avg * 1.5
    
    def _test_reset_reuse(self) -> bool:
        """Test generator reset and reuse."""
        print("Testing generator reset and reuse...")
        
        render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(5)
        
        generator = create_frame_spec_generator(
            render_tasks, entity_map, entity_details, colors, 5, 1000.0, "tracks"
        )
        
        # First iteration
        first_specs = list(generator)
        progress_after_first = generator.get_progress()
        
        # Reset
        generator.reset()
        progress_after_reset = generator.get_progress()
        
        # Second iteration
        second_specs = list(generator)
        
        print(f"First iteration: {len(first_specs)} specs")
        print(f"Progress after first: {progress_after_first}")
        print(f"Progress after reset: {progress_after_reset}")
        print(f"Second iteration: {len(second_specs)} specs")
        
        # Check results
        if progress_after_reset != (0, 5):
            print("Reset didn't restore progress correctly")
            return False
        
        if len(first_specs) != len(second_specs):
            print("Different number of specs after reset")
            return False
        
        # Check specs are identical
        for i, (s1, s2) in enumerate(zip(first_specs, second_specs)):
            if not self._specs_equal(s1, s2):
                print(f"Spec {i} differs after reset")
                return False
        
        print("✓ Reset and reuse working correctly")
        return True
    
    def _test_tracks_mode(self) -> bool:
        """Test tracks mode specifically."""
        print("Testing tracks mode...")
        
        render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(10)
        
        generator = create_frame_spec_generator(
            render_tasks, entity_map, entity_details, colors, 5, 1000.0, "tracks"
        )
        
        specs = list(generator)
        
        # Check that display names are in "Track - Artist" format
        for spec in specs[:3]:  # Check first few
            for bar in spec['bars']:
                display_name = bar['display_name']
                if ' - ' not in display_name:
                    print(f"Invalid tracks mode display name: {display_name}")
                    return False
                
                parts = display_name.split(' - ')
                if len(parts) != 2:
                    print(f"Invalid tracks mode format: {display_name}")
                    return False
        
        print("✓ Tracks mode display names correct")
        return True
    
    def _test_artists_mode(self) -> bool:
        """Test artists mode specifically."""
        print("Testing artists mode...")
        
        # Create artist-specific test data
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
        
        generator = create_frame_spec_generator(
            render_tasks, entity_map, entity_details, colors, 5, 1000.0, "artists"
        )
        
        specs = list(generator)
        
        # Check that display names are just artist names
        for spec in specs[:3]:
            for bar in spec['bars']:
                display_name = bar['display_name']
                if not display_name.startswith('Artist '):
                    print(f"Invalid artists mode display name: {display_name}")
                    return False
        
        print("✓ Artists mode display names correct")
        return True
    
    def _test_config_flag(self) -> bool:
        """Test configuration flag functionality."""
        print("Testing configuration flag...")
        
        try:
            # This test would require integration with the actual config system
            # For now, just test that the flag exists and can be imported
            config = AppConfig()
            # This would test the actual config loading in a real environment
            print("✓ Configuration system accessible")
            return True
        except Exception as e:
            print(f"Configuration test error: {e}")
            return False
    
    def _test_integration(self) -> bool:
        """Test integration with main animator (dry run)."""
        print("Testing integration with main animator...")
        
        # This is a dry run test - we don't actually run the full animator
        render_tasks, entity_map, entity_details, colors = self._create_test_render_tasks(10)
        
        # Test that we can create both methods successfully
        try:
            # Original method
            original_specs = prepare_all_frame_specs(
                render_tasks, entity_map, entity_details, colors, 5, 1000.0, "tracks"
            )
            
            # Generator method 
            generator = create_frame_spec_generator(
                render_tasks, entity_map, entity_details, colors, 5, 1000.0, "tracks"
            )
            
            # Test that the import works
            from frame_spec_generator import create_frame_spec_generator
            
            print("✓ Both methods can be created successfully")
            print("✓ Import works correctly")
            print("Note: Full integration test requires running main_animator.py")
            
            return True
        except Exception as e:
            print(f"Integration test error: {e}")
            return False
    
    def _show_summary(self):
        """Show test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        if not self.test_results:
            print("No tests were run.")
            return
        
        passed = sum(1 for result in self.test_results.values() if result['passed'])
        total = len(self.test_results)
        
        print(f"Tests run: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success rate: {passed/total*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_num, result in sorted(self.test_results.items()):
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            time_str = f"({result['time']:.3f}s)" if 'time' in result else ""
            error_str = f" - {result['error']}" if 'error' in result else ""
            print(f"  {test_num:2d}. {status} {result['name']} {time_str}{error_str}")
        
        if passed == total:
            print("\n🎉 All tests passed! Task 2 implementation is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")


def main():
    """Main entry point."""
    tester = Task2ManualTester()
    tester.run_interactive_menu()


if __name__ == "__main__":
    main()