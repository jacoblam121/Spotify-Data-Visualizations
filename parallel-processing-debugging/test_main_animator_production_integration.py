#!/usr/bin/env python3
"""
Test Main Animator Production Integration

This script tests the production integration of our ProcessPoolExecutor optimization
with the real main_animator.py patterns. It validates that our solution works with
actual configuration and data structures from the main application.

Run this test to validate that the integration works before modifying main_animator.py.

Usage:
    python test_main_animator_production_integration.py

Expected: 100% success rate with significant performance improvement over old pattern.
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
from main_animator_production_worker import (
    init_main_animator_production_worker, 
    draw_and_save_single_frame_production,
    draw_and_save_single_frame_legacy_wrapper
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MainAnimatorProductionIntegrationTest:
    """Test the production integration with realistic main_animator.py data structures"""
    
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
    
    def _create_realistic_static_context(self) -> Dict[str, Any]:
        """Create static context that matches real main_animator.py structure"""
        # Simulate realistic data sizes like real application
        num_entities = 200
        num_albums = 100
        
        return {
            # Core data and config (matches main_animator.py exactly)
            'num_total_output_frames': 100,
            'entity_id_to_animator_key_map': {f'track_{i}': f'canonical_track_{i}' for i in range(num_entities)},
            'entity_details_map': {
                f'track_{i}': {
                    'name': f'Track {i}', 
                    'artist': f'Artist {i}', 
                    'album': f'Album {i%10}',
                    'play_count': 100 + i*5
                } for i in range(num_entities)
            },
            'album_art_image_objects': {f'album_{i}': f'small_image_data_{i}' for i in range(num_albums)},
            'album_art_image_objects_highres': {f'album_hr_{i}': f'highres_image_data_{i}' for i in range(num_albums)},
            'album_bar_colors': {f'color_{i}': (0.1 + i*0.01, 0.2 + i*0.01, 0.3 + i*0.01, 1.0) for i in range(num_albums)},
            'N_BARS': 10,
            'chart_xaxis_limit': 1000.0,
            
            # Display configuration
            'dpi': 96,
            'fig_width_pixels': 1920,
            'fig_height_pixels': 1080,
            
            # Logging configuration
            'LOG_FRAME_TIMES_CONFIG': True,
            'PREFERRED_FONTS': ["DejaVu Sans", "Arial", "sans-serif"],
            'LOG_PARALLEL_PROCESS_START_CONFIG': True,
            
            # Rolling stats display configuration (13 parameters - exact from main_animator.py)
            'ROLLING_PANEL_AREA_LEFT_FIG': 0.03,
            'ROLLING_PANEL_AREA_RIGHT_FIG': 0.25,
            'ROLLING_PANEL_TITLE_Y_FROM_TOP_FIG': 0.02,
            'ROLLING_TITLE_TO_CONTENT_GAP_FIG': 0.01,
            'ROLLING_TITLE_FONT_SIZE': 11.0,
            'ROLLING_SONG_ARTIST_FONT_SIZE': 9.0,
            'ROLLING_PLAYS_FONT_SIZE': 8.0,
            'ROLLING_ART_HEIGHT_FIG': 0.07,
            'ROLLING_ART_ASPECT_RATIO': 1.0,
            'ROLLING_ART_MAX_WIDTH_FIG': 0.07,
            'ROLLING_ART_PADDING_RIGHT_FIG': 0.005,
            'ROLLING_TEXT_PADDING_LEFT_FIG': 0.005,
            'ROLLING_TEXT_TO_ART_HORIZONTAL_GAP_FIG': 0.005,
            'ROLLING_TEXT_LINE_VERTICAL_SPACING_FIG': 0.02,
            'ROLLING_SONG_ARTIST_TO_PLAYS_VERTICAL_GAP_FIG': 0.025,
            'ROLLING_INTER_PANEL_VERTICAL_SPACING_FIG': 0.04,
            
            # Position configuration (4 parameters - exact from main_animator.py)
            'ROLLING_PANEL_TITLE_X_FIG': -1.0,  # Centered
            'ROLLING_TEXT_TRUNCATION_ADJUST_PX': 0,
            'MAIN_TIMESTAMP_X_FIG': -1.0,  # Auto/centered
            'MAIN_TIMESTAMP_Y_FIG': 0.04,
            
            # Mode information
            'VISUALIZATION_MODE': 'tracks'
        }
    
    def _create_realistic_frame_tasks(self, num_frames: int) -> List[Dict[str, Any]]:
        """Create frame tasks that match real main_animator.py structure"""
        frame_tasks = []
        
        for i in range(num_frames):
            # Create realistic render task structure (matches main_animator.py)
            task = {
                'overall_frame_index': i,
                'display_timestamp': f'2023-01-{(i%30)+1:02d}',  # Simulate month progression
                'bar_render_data_list': [
                    {
                        'entity_id': f'track_{j + (i*2)%10}',  # Simulate changing top tracks
                        'canonical_name': f'Track {j + (i*2)%10}',
                        'display_name': f'Track {j + (i*2)%10}',
                        'artist_name': f'Artist {j + (i*2)%10}',
                        'y_pos': float(j),
                        'play_count': 100.0 + (i * 5) + (j * 20),
                        'bar_color': (0.2 + j*0.1, 0.4, 0.8 - j*0.05, 1.0),
                        'album_art_path': f'album_{j + (i%5)}.jpg'
                    }
                    for j in range(5)  # Top 5 tracks for this frame
                ],
                'is_keyframe_end_frame': i == num_frames - 1
            }
            
            # Create frame data structure (matches what our optimized function expects)
            frame_data = {
                'task': task,
                'output_image_path': f'test_frames/frame_{i:06d}.png'
            }
            
            frame_tasks.append(frame_data)
        
        return frame_tasks
    
    def _create_legacy_frame_tasks(self, num_frames: int, static_context: Dict[str, Any]) -> List[Tuple]:
        """Create legacy 37-parameter tuples for performance comparison"""
        legacy_tasks = []
        
        for i in range(num_frames):
            # Create the task
            task = {
                'overall_frame_index': i,
                'display_timestamp': f'2023-01-{(i%30)+1:02d}',
                'bar_render_data_list': [
                    {'entity_id': f'track_{j}', 'play_count': j*10 + i*2}
                    for j in range(5)
                ],
                'is_keyframe_end_frame': False
            }
            
            # Create the massive 37-parameter tuple (original pattern)
            legacy_tuple = (
                task,  # 1
                static_context['num_total_output_frames'],  # 2
                static_context['entity_id_to_animator_key_map'],  # 3
                static_context['entity_details_map'],  # 4
                static_context['album_art_image_objects'],  # 5
                static_context['album_art_image_objects_highres'],  # 6
                static_context['album_bar_colors'],  # 7
                static_context['N_BARS'],  # 8
                static_context['chart_xaxis_limit'],  # 9
                f'test_frames/frame_{i:06d}.png',  # 10 - output_image_path
                static_context['dpi'],  # 11
                static_context['fig_width_pixels'],  # 12
                static_context['fig_height_pixels'],  # 13
                static_context['LOG_FRAME_TIMES_CONFIG'],  # 14
                static_context['PREFERRED_FONTS'],  # 15
                static_context['LOG_PARALLEL_PROCESS_START_CONFIG'],  # 16
                # Rolling stats display configs (13 parameters: 17-29)
                static_context['ROLLING_PANEL_AREA_LEFT_FIG'],  # 17
                static_context['ROLLING_PANEL_AREA_RIGHT_FIG'],  # 18
                static_context['ROLLING_PANEL_TITLE_Y_FROM_TOP_FIG'],  # 19
                static_context['ROLLING_TITLE_TO_CONTENT_GAP_FIG'],  # 20
                static_context['ROLLING_TITLE_FONT_SIZE'],  # 21
                static_context['ROLLING_SONG_ARTIST_FONT_SIZE'],  # 22
                static_context['ROLLING_PLAYS_FONT_SIZE'],  # 23
                static_context['ROLLING_ART_HEIGHT_FIG'],  # 24
                static_context['ROLLING_ART_ASPECT_RATIO'],  # 25
                static_context['ROLLING_ART_MAX_WIDTH_FIG'],  # 26
                static_context['ROLLING_ART_PADDING_RIGHT_FIG'],  # 27
                static_context['ROLLING_TEXT_PADDING_LEFT_FIG'],  # 28
                static_context['ROLLING_TEXT_TO_ART_HORIZONTAL_GAP_FIG'],  # 29
                static_context['ROLLING_TEXT_LINE_VERTICAL_SPACING_FIG'],  # 30
                static_context['ROLLING_SONG_ARTIST_TO_PLAYS_VERTICAL_GAP_FIG'],  # 31
                static_context['ROLLING_INTER_PANEL_VERTICAL_SPACING_FIG'],  # 32
                # Position configs (4 parameters: 33-36)
                static_context['ROLLING_PANEL_TITLE_X_FIG'],  # 33
                static_context['ROLLING_TEXT_TRUNCATION_ADJUST_PX'],  # 34
                static_context['MAIN_TIMESTAMP_X_FIG'],  # 35
                static_context['MAIN_TIMESTAMP_Y_FIG'],  # 36
                # Mode information (1 parameter: 37)
                static_context['VISUALIZATION_MODE']  # 37
            )
            
            legacy_tasks.append(legacy_tuple)
        
        return legacy_tasks
    
    def test_legacy_pattern(self, num_frames: int = 30) -> Dict[str, Any]:
        """Test the legacy 37-parameter pattern for comparison"""
        print(f"\\n🔍 Testing LEGACY pattern (37 parameters with every task)")
        print("=" * 60)
        
        max_workers = min(4, os.cpu_count() or 4)
        static_context = self._create_realistic_static_context()
        legacy_tasks = self._create_legacy_frame_tasks(num_frames, static_context)
        
        start_time = time.time()
        
        # Use standard executor (no initializer, massive serialization)
        with create_rendering_executor(self.render_config, max_workers=max_workers) as executor:
            futures = [
                executor.submit(draw_and_save_single_frame_legacy_wrapper, task_tuple)
                for task_tuple in legacy_tasks
            ]
            
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Legacy pattern task failed: {e}")
                    results.append(None)
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r is not None)
        
        print(f"✅ Legacy pattern: {successful}/{num_frames} frames, {total_time:.2f}s")
        
        return {
            'pattern': 'legacy_37_params',
            'successful_frames': successful,
            'total_frames': num_frames,
            'total_time': total_time,
            'frames_per_second': num_frames / total_time if total_time > 0 else 0
        }
    
    def test_optimized_pattern(self, num_frames: int = 30) -> Dict[str, Any]:
        """Test the optimized pattern with global worker context"""
        print(f"\\n🚀 Testing OPTIMIZED pattern (config initialized once per worker)")
        print("=" * 60)
        
        max_workers = min(4, os.cpu_count() or 4)
        static_context = self._create_realistic_static_context()
        frame_tasks = self._create_realistic_frame_tasks(num_frames)
        
        start_time = time.time()
        
        # Use executor with custom initializer and static context
        with create_rendering_executor(
            self.render_config,
            max_workers=max_workers,
            initializer_func=init_main_animator_production_worker,
            initializer_args=(static_context,)
        ) as executor:
            futures = [
                executor.submit(draw_and_save_single_frame_production, frame_data)
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
    
    def run_production_integration_test(self, num_frames: int = 50) -> Dict[str, Any]:
        """Run comprehensive production integration test"""
        print("🎯 MAIN ANIMATOR PRODUCTION INTEGRATION TEST")
        print("=" * 60)
        print(f"Testing production integration with {num_frames} frames")
        print("Using realistic main_animator.py data structures and configuration")
        print()
        
        # Test both patterns
        legacy_results = self.test_legacy_pattern(num_frames)
        optimized_results = self.test_optimized_pattern(num_frames)
        
        # Compare results
        print(f"\\n📊 PRODUCTION INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        legacy_fps = legacy_results['frames_per_second']
        optimized_fps = optimized_results['frames_per_second']
        performance_improvement = (optimized_fps - legacy_fps) / legacy_fps * 100 if legacy_fps > 0 else 0
        
        print(f"Legacy pattern (37 params): {legacy_fps:.1f} fps")
        print(f"Optimized pattern (global context): {optimized_fps:.1f} fps")
        print(f"Performance improvement: {performance_improvement:+.1f}%")
        
        # Calculate serialization savings estimate
        static_context_size = len(str(self._create_realistic_static_context()))
        serialization_savings = static_context_size * (num_frames - 1)  # Save (n-1) serializations
        print(f"Estimated serialization savings: ~{serialization_savings:,} characters")
        
        # Validate results
        both_successful = (
            legacy_results['successful_frames'] == legacy_results['total_frames'] and
            optimized_results['successful_frames'] == optimized_results['total_frames']
        )
        
        performance_improved = performance_improvement > 0
        
        success = both_successful and performance_improved
        
        print(f"\\n✅ Production integration test success: {success}")
        print(f"   - All frames completed: {both_successful}")
        print(f"   - Performance improved: {performance_improved} ({performance_improvement:+.1f}%)")
        
        if success:
            print(f"\\n🎉 READY FOR PRODUCTION INTEGRATION!")
            print(f"   The optimization is validated and ready to integrate into main_animator.py")
            print(f"   Expected performance improvement: {performance_improvement:.0f}%")
        else:
            print(f"\\n❌ INTEGRATION VALIDATION FAILED!")
            print(f"   Issues detected that need to be resolved before production integration")
        
        return {
            'success': success,
            'legacy_pattern': legacy_results,
            'optimized_pattern': optimized_results,
            'performance_improvement_percent': performance_improvement,
            'serialization_savings_estimate': serialization_savings,
            'both_patterns_successful': both_successful,
            'performance_improved': performance_improved
        }

def main():
    """Run the production integration test"""
    test = MainAnimatorProductionIntegrationTest()
    results = test.run_production_integration_test(num_frames=75)  # Test with substantial frame count
    
    if results['success']:
        improvement = results['performance_improvement_percent']
        print(f"\\n🎉 PRODUCTION INTEGRATION TEST PASSED!")
        print(f"Ready to implement {improvement:.0f}% performance improvement in main_animator.py")
        return 0
    else:
        print(f"\\n❌ PRODUCTION INTEGRATION TEST FAILED!")
        print(f"Issues detected with production integration approach")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)