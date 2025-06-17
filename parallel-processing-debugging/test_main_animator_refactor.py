#!/usr/bin/env python3
"""
Test Main Animator Refactor

This script tests the refactored main_animator.py pattern to ensure
the optimization works correctly before implementing in production code.

It simulates the actual 37-parameter pattern used in main_animator.py
and validates that our optimization approach works safely.
"""

import os
import sys
import time
from typing import Dict, Any, List, Tuple
import logging

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from executor_factory import create_rendering_executor
from stateless_renderer import RenderConfig
from main_animator_worker import init_main_animator_worker, draw_and_save_single_frame_optimized

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MainAnimatorRefactorTest:
    """Test the main_animator.py refactoring with realistic 37-parameter simulation"""
    
    def __init__(self):
        self.render_config = self._create_test_render_config()
        
    def _create_test_render_config(self) -> RenderConfig:
        """Create a test render configuration"""
        return RenderConfig(
            dpi=96,
            fig_width_pixels=1920,
            fig_height_pixels=1080,
            target_fps=30,
            font_paths={"DejaVuSans": "fonts/DejaVuSans.ttf"} if os.path.exists("fonts/DejaVuSans.ttf") else {},
            preferred_fonts=["DejaVu Sans", "Arial"],
            album_art_cache_dir="album_art_cache",
            album_art_visibility_threshold=0.0628,
            n_bars=10
        )
    
    def _create_static_context(self) -> Dict[str, Any]:
        """Create the static context that represents the 37 parameters"""
        return {
            # Data maps and caches (large objects)
            'entity_id_to_canonical_name_map': {f'entity_{i}': f'canonical_{i}' for i in range(100)},
            'entity_details_map_main': {f'entity_{i}': {'name': f'Track {i}', 'artist': f'Artist {i}'} for i in range(100)},
            'album_art_image_objects_local': {f'art_{i}': f'image_data_{i}' for i in range(50)},  # Simulate image cache
            'album_art_image_objects_highres_local': {f'art_hr_{i}': f'highres_image_data_{i}' for i in range(50)},
            'album_bar_colors_local': {f'color_{i}': (0.1*i, 0.2*i, 0.3*i, 1.0) for i in range(50)},
            
            # Display configuration
            'n_bars_local': 10,
            'chart_xaxis_limit_overall_scale': 1000.0,
            'dpi': 96,
            'fig_width_pixels': 1920,
            'fig_height_pixels': 1080,
            
            # Logging configuration
            'log_frame_times_config_local': True,
            'preferred_fonts_local': ["DejaVu Sans", "Arial"],
            'log_parallel_process_start_local': True,
            
            # Rolling stats display configuration (15 parameters)
            'rs_panel_area_left_fig': 0.02,
            'rs_panel_area_right_fig': 0.25,
            'rs_panel_title_y_from_top_fig': 0.05,
            'rs_title_to_content_gap_fig': 0.02,
            'rs_title_font_size': 14,
            'rs_song_artist_font_size': 11,
            'rs_plays_font_size': 9,
            'rs_art_height_fig': 0.06,
            'rs_art_aspect_ratio': 1.0,
            'rs_art_max_width_fig': 0.08,
            'rs_art_padding_right_fig': 0.01,
            'rs_text_padding_left_fig': 0.005,
            'rs_text_to_art_horizontal_gap_fig': 0.01,
            'rs_text_line_vertical_spacing_fig': 0.015,
            'rs_song_artist_to_plays_gap_fig': 0.005,
            'rs_inter_panel_vertical_spacing_fig': 0.05,
            
            # Position configuration
            'rs_panel_title_x_fig_config': 0.02,
            'rs_text_truncation_adjust_px_config': 5,
            'main_timestamp_x_fig_config': 0.5,
            'main_timestamp_y_fig_config': 0.02,
            
            # Mode information
            'visualization_mode_local': 'tracks'
        }
    
    def _create_frame_tasks(self, num_frames: int) -> List[Dict[str, Any]]:
        """Create frame tasks with only dynamic data"""
        frame_tasks = []
        for i in range(num_frames):
            frame_data = {
                'render_task': {
                    'overall_frame_index': i,
                    'display_timestamp': f"2023-01-{i+1:02d}",
                    'bar_render_data_list': [
                        {
                            'entity_id': f'track_{j}',
                            'y_pos': float(j),
                            'play_count': 100.0 + (i * 5) + (j * 10),
                            'bar_color': (0.2, 0.4, 0.8, 1.0),
                            'album_art_path': f'art_{j}.jpg'
                        }
                        for j in range(5)
                    ]
                },
                'num_total_output_frames': num_frames,
                'output_image_path': f'test_frames/frame_{i:06d}.png'
            }
            frame_tasks.append(frame_data)
        return frame_tasks
    
    def test_original_pattern_simulation(self, num_frames: int = 50) -> Dict[str, Any]:
        """Simulate the original 37-parameter pattern for performance comparison"""
        print(f"\n🔍 Testing ORIGINAL pattern (37 parameters with every task)")
        print("=" * 60)
        
        max_workers = 4
        static_context = self._create_static_context()
        
        # Create 37-parameter tuples (simulating original pattern)
        original_tasks = []
        for i in range(num_frames):
            # This simulates the massive tuple from main_animator.py
            render_task = {
                'overall_frame_index': i,
                'display_timestamp': f"2023-01-{i+1:02d}",
                'bar_render_data_list': [{'track': f'track_{j}', 'plays': j*10} for j in range(5)]
            }
            
            # Create the 37-parameter tuple (like original code)
            task_tuple = (
                render_task, num_frames,
                static_context['entity_id_to_canonical_name_map'],
                static_context['entity_details_map_main'],
                static_context['album_art_image_objects_local'],
                static_context['album_art_image_objects_highres_local'],
                static_context['album_bar_colors_local'],
                static_context['n_bars_local'],
                static_context['chart_xaxis_limit_overall_scale'],
                f'test_frames/frame_{i:06d}.png',  # output_image_path
                static_context['dpi'],
                static_context['fig_width_pixels'],
                static_context['fig_height_pixels'],
                static_context['log_frame_times_config_local'],
                static_context['preferred_fonts_local'],
                static_context['log_parallel_process_start_local'],
                static_context['rs_panel_area_left_fig'],
                static_context['rs_panel_area_right_fig'],
                static_context['rs_panel_title_y_from_top_fig'],
                static_context['rs_title_to_content_gap_fig'],
                static_context['rs_title_font_size'],
                static_context['rs_song_artist_font_size'],
                static_context['rs_plays_font_size'],
                static_context['rs_art_height_fig'],
                static_context['rs_art_aspect_ratio'],
                static_context['rs_art_max_width_fig'],
                static_context['rs_art_padding_right_fig'],
                static_context['rs_text_padding_left_fig'],
                static_context['rs_text_to_art_horizontal_gap_fig'],
                static_context['rs_text_line_vertical_spacing_fig'],
                static_context['rs_song_artist_to_plays_gap_fig'],
                static_context['rs_inter_panel_vertical_spacing_fig'],
                static_context['rs_panel_title_x_fig_config'],
                static_context['rs_text_truncation_adjust_px_config'],
                static_context['main_timestamp_x_fig_config'],
                static_context['main_timestamp_y_fig_config'],
                static_context['visualization_mode_local']
            )
            original_tasks.append(task_tuple)
        
        start_time = time.time()
        
        # Use standard executor (no initializer, massive serialization)
        with create_rendering_executor(self.render_config, max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._original_pattern_worker, task_tuple)
                for task_tuple in original_tasks
            ]
            
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Original pattern task failed: {e}")
                    results.append(None)
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r is not None)
        
        print(f"✅ Original pattern: {successful}/{num_frames} frames, {total_time:.2f}s")
        
        return {
            'pattern': 'original_37_params',
            'successful_frames': successful,
            'total_frames': num_frames,
            'total_time': total_time,
            'frames_per_second': num_frames / total_time if total_time > 0 else 0
        }
    
    def _original_pattern_worker(self, task_tuple: Tuple) -> Tuple[int, float, int]:
        """Worker function that processes the original 37-parameter tuple"""
        start_time = time.time()
        
        # Unpack just the first few parameters we need
        render_task, num_total_frames = task_tuple[0], task_tuple[1]
        frame_index = render_task.get('overall_frame_index', 0)
        
        # Simulate processing time
        time.sleep(0.01)
        
        render_time = time.time() - start_time
        return (frame_index, render_time, os.getpid())
    
    def test_optimized_pattern(self, num_frames: int = 50) -> Dict[str, Any]:
        """Test the optimized pattern with global worker context"""
        print(f"\n🚀 Testing OPTIMIZED pattern (config initialized once per worker)")
        print("=" * 60)
        
        max_workers = 4
        static_context = self._create_static_context()
        frame_tasks = self._create_frame_tasks(num_frames)
        
        start_time = time.time()
        
        # Use executor with custom initializer and static context
        with create_rendering_executor(
            self.render_config,
            max_workers=max_workers,
            initializer_func=init_main_animator_worker,
            initializer_args=(static_context,)
        ) as executor:
            # Pass static context to initializer, submit only dynamic data
            futures = [
                executor.submit(draw_and_save_single_frame_optimized, frame_data)
                for frame_data in frame_tasks
            ]
            
            results = []
            worker_pids = set()
            for future in futures:
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                    if result:
                        worker_pids.add(result[2])
                except Exception as e:
                    logger.error(f"Optimized pattern task failed: {e}")
                    results.append(None)
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r is not None)
        
        print(f"✅ Optimized pattern: {successful}/{num_frames} frames, {total_time:.2f}s")
        print(f"📊 Used {len(worker_pids)} unique worker processes")
        
        return {
            'pattern': 'optimized_global_context',
            'successful_frames': successful,
            'total_frames': num_frames,
            'total_time': total_time,
            'frames_per_second': num_frames / total_time if total_time > 0 else 0,
            'unique_workers': len(worker_pids)
        }
    
    def run_refactor_test(self, num_frames: int = 50) -> Dict[str, Any]:
        """Run comprehensive refactor test"""
        print("🎯 MAIN ANIMATOR REFACTOR TEST")
        print("=" * 60)
        print(f"Testing main_animator.py refactoring with {num_frames} frames")
        print("Simulating actual 37-parameter pattern vs optimized approach")
        print()
        
        # Test both patterns
        original_results = self.test_original_pattern_simulation(num_frames)
        optimized_results = self.test_optimized_pattern(num_frames)
        
        # Compare results
        print(f"\n📊 REFACTOR TEST RESULTS")
        print("=" * 60)
        
        original_fps = original_results['frames_per_second']
        optimized_fps = optimized_results['frames_per_second']
        performance_improvement = (optimized_fps - original_fps) / original_fps * 100 if original_fps > 0 else 0
        
        print(f"Original pattern (37 params): {original_fps:.1f} fps")
        print(f"Optimized pattern (global context): {optimized_fps:.1f} fps")
        print(f"Performance improvement: {performance_improvement:+.1f}%")
        
        # Calculate data serialization savings
        context_size_estimate = len(str(self._create_static_context()))
        serialization_savings = context_size_estimate * (num_frames - 1)  # Save (n-1) serializations
        print(f"Estimated serialization savings: ~{serialization_savings:,} characters")
        
        success = (
            original_results['successful_frames'] == original_results['total_frames'] and
            optimized_results['successful_frames'] == optimized_results['total_frames'] and
            performance_improvement > 0
        )
        
        print(f"✅ Refactor test success: {success}")
        
        return {
            'success': success,
            'original_pattern': original_results,
            'optimized_pattern': optimized_results,
            'performance_improvement_percent': performance_improvement,
            'serialization_savings_estimate': serialization_savings
        }

def main():
    """Run the main animator refactor test"""
    test = MainAnimatorRefactorTest()
    results = test.run_refactor_test(num_frames=100)  # Test with more frames
    
    if results['success']:
        improvement = results['performance_improvement_percent']
        print(f"\n🎉 REFACTOR TEST PASSED!")
        print(f"Ready to implement {improvement:.0f}% performance improvement in main_animator.py")
        return 0
    else:
        print(f"\n❌ REFACTOR TEST FAILED!")
        print(f"Issues detected with optimization approach")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)