#!/usr/bin/env python3
"""
Test Main Animator Integration

This script tests the integration of our ProcessPoolExecutor factory pattern
with the main_animator.py to validate that the fix works with real application
patterns, not just mocks.

The test simulates the same parallel processing pattern used in main_animator.py
but with our improved executor factory initialization.
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variable to simulate WORKER_RENDER_CONFIG pattern
WORKER_RENDER_CONFIG = None

def init_main_animator_worker(render_config_dict: Dict[str, Any]):
    """
    Worker initialization function that simulates the pattern needed for main_animator.py
    This sets up the global WORKER_RENDER_CONFIG that workers will use.
    """
    global WORKER_RENDER_CONFIG
    
    # Convert dict back to RenderConfig object (or just use dict directly)
    WORKER_RENDER_CONFIG = render_config_dict
    
    worker_pid = os.getpid()
    logger.info(f"Main animator worker {worker_pid} initialized with config")

def draw_and_save_single_frame_simulated(frame_data: Dict[str, Any]) -> Tuple[int, float, int]:
    """
    Simulated version of the main_animator.py draw_and_save_single_frame function.
    
    This tests the pattern where workers use global WORKER_RENDER_CONFIG instead
    of receiving configuration as parameters.
    
    Args:
        frame_data: Frame-specific data (the only thing that should be serialized per task)
        
    Returns:
        Tuple of (frame_index, render_time, worker_pid)
    """
    global WORKER_RENDER_CONFIG
    
    start_time = time.time()
    worker_pid = os.getpid()
    frame_index = frame_data.get('frame_index', 0)
    
    # Validate that worker initialization worked
    if WORKER_RENDER_CONFIG is None:
        raise RuntimeError(f"Worker {worker_pid}: WORKER_RENDER_CONFIG is None - initialization failed")
    
    # Access configuration that would normally be passed as parameters
    dpi = WORKER_RENDER_CONFIG.get('dpi', 96)
    fig_width = WORKER_RENDER_CONFIG.get('fig_width_pixels', 1920)
    fig_height = WORKER_RENDER_CONFIG.get('fig_height_pixels', 1080)
    
    # Simulate frame rendering work
    # In real main_animator.py this would be complex matplotlib operations
    processing_time = 0.01  # Simulate 10ms of work
    time.sleep(processing_time)
    
    # Log successful access to configuration
    logger.debug(f"Frame {frame_index}: Worker {worker_pid} accessed config (dpi={dpi}, size={fig_width}x{fig_height})")
    
    render_time = time.time() - start_time
    return (frame_index, render_time, worker_pid)

class MainAnimatorIntegrationTest:
    """Test class for validating main_animator.py integration patterns"""
    
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
    
    def test_old_pattern_simulation(self) -> Dict[str, Any]:
        """
        Simulate the old main_animator.py pattern where configuration is passed
        with every task (performance anti-pattern)
        """
        print("\n🔍 Testing OLD pattern (config passed with every task)")
        print("=" * 60)
        
        num_frames = 20
        max_workers = 4
        
        # Create frame data
        frame_tasks = []
        for i in range(num_frames):
            # In old pattern, configuration would be included in every task tuple
            frame_data = {
                'frame_index': i,
                'timestamp': f"2023-01-{i+1:02d}",
                'bars': [{'name': f'track_{j}', 'value': j*10} for j in range(5)]
            }
            
            # This simulates the anti-pattern: large config object with every task
            task_tuple = (frame_data, self.render_config.to_dict())
            frame_tasks.append(task_tuple)
        
        start_time = time.time()
        
        # This simulates the old pattern: no initializer, config passed as parameter
        with create_rendering_executor(self.render_config, max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._old_pattern_worker, task_tuple) 
                for task_tuple in frame_tasks
            ]
            
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=10)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Old pattern task failed: {e}")
                    results.append(None)
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r is not None)
        
        print(f"✅ Old pattern: {successful}/{num_frames} frames, {total_time:.2f}s")
        return {
            'pattern': 'old',
            'successful_frames': successful,
            'total_frames': num_frames,
            'total_time': total_time,
            'frames_per_second': num_frames / total_time if total_time > 0 else 0
        }
    
    def _old_pattern_worker(self, task_tuple: Tuple) -> Tuple[int, float, int]:
        """Worker function for old pattern (receives config as parameter)"""
        frame_data, config_dict = task_tuple
        start_time = time.time()
        
        # Access config from parameter (old pattern)
        dpi = config_dict.get('dpi', 96)
        
        # Simulate work
        time.sleep(0.01)
        
        render_time = time.time() - start_time
        return (frame_data['frame_index'], render_time, os.getpid())
    
    def test_new_pattern_with_factory(self) -> Dict[str, Any]:
        """
        Test the new pattern using our executor factory with proper worker initialization
        """
        print("\n🚀 Testing NEW pattern (config initialized once per worker)")
        print("=" * 60)
        
        num_frames = 20
        max_workers = 4
        
        # Create frame data (only frame-specific data, no config)
        frame_tasks = []
        for i in range(num_frames):
            frame_data = {
                'frame_index': i,
                'timestamp': f"2023-01-{i+1:02d}",
                'bars': [{'name': f'track_{j}', 'value': j*10} for j in range(5)]
            }
            frame_tasks.append(frame_data)
        
        start_time = time.time()
        
        # New pattern: executor factory handles initialization, only frame data per task
        with create_rendering_executor(
            self.render_config, 
            max_workers=max_workers,
            initializer_func=init_main_animator_worker
        ) as executor:
            futures = [
                executor.submit(draw_and_save_single_frame_simulated, frame_data) 
                for frame_data in frame_tasks
            ]
            
            results = []
            worker_pids = set()
            for future in futures:
                try:
                    result = future.result(timeout=10)
                    results.append(result)
                    if result:
                        worker_pids.add(result[2])  # Track worker PIDs
                except Exception as e:
                    logger.error(f"New pattern task failed: {e}")
                    results.append(None)
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r is not None)
        
        print(f"✅ New pattern: {successful}/{num_frames} frames, {total_time:.2f}s")
        print(f"📊 Used {len(worker_pids)} unique worker processes")
        
        return {
            'pattern': 'new',
            'successful_frames': successful,
            'total_frames': num_frames,
            'total_time': total_time,
            'frames_per_second': num_frames / total_time if total_time > 0 else 0,
            'unique_workers': len(worker_pids)
        }
    
    def run_integration_test(self) -> Dict[str, Any]:
        """Run comprehensive integration test comparing old vs new patterns"""
        print("🎯 MAIN ANIMATOR INTEGRATION TEST")
        print("=" * 60)
        print("Testing integration patterns for main_animator.py parallel processing")
        print()
        
        # Test both patterns
        old_results = self.test_old_pattern_simulation()
        new_results = self.test_new_pattern_with_factory()
        
        # Compare results
        print(f"\n📊 INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        old_fps = old_results['frames_per_second']
        new_fps = new_results['frames_per_second']
        performance_improvement = (new_fps - old_fps) / old_fps * 100 if old_fps > 0 else 0
        
        print(f"Old pattern performance: {old_fps:.1f} fps")
        print(f"New pattern performance: {new_fps:.1f} fps")
        print(f"Performance improvement: {performance_improvement:+.1f}%")
        
        success = (
            old_results['successful_frames'] == old_results['total_frames'] and
            new_results['successful_frames'] == new_results['total_frames'] and
            new_results['frames_per_second'] >= old_results['frames_per_second']
        )
        
        print(f"✅ Integration test success: {success}")
        
        return {
            'success': success,
            'old_pattern': old_results,
            'new_pattern': new_results,
            'performance_improvement_percent': performance_improvement
        }

def main():
    """Run the main animator integration test"""
    test = MainAnimatorIntegrationTest()
    results = test.run_integration_test()
    
    if results['success']:
        print(f"\n🎉 INTEGRATION TEST PASSED!")
        print(f"Ready to integrate factory pattern into main_animator.py")
        return 0
    else:
        print(f"\n❌ INTEGRATION TEST FAILED!")
        print(f"Issues detected with factory pattern integration")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)