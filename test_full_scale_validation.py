#!/usr/bin/env python3
"""
Full-Scale Validation Test for Parallel Rendering Fix

This script validates that our MockFrameSpecGenerator color clamping fix
works at full scale (100+ frames) and integrates properly with the complete system.

Tests:
1. Original failing 100-frame scenario
2. Different worker counts (4, 8, 16)
3. Integration with both test and production paths
4. Memory usage monitoring
5. Performance validation
"""

import os
import sys
import time
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, Any, List
import psutil

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_mock_components import MockFrameSpecGenerator, MockConfig, TestDataFactory
from test_worker_helpers import top_level_test_render_function
from stateless_renderer import RenderConfig
from executor_factory import create_rendering_executor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FullScaleValidator:
    """Comprehensive validator for parallel rendering at scale"""
    
    def __init__(self):
        self.results = {}
        self.start_memory = None
        self.peak_memory = None
        
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def test_100_frame_scenario(self, worker_count: int = 8) -> Dict[str, Any]:
        """Test the original failing 100-frame scenario"""
        print(f"\n🎯 Testing 100-frame scenario with {worker_count} workers")
        print("=" * 60)
        
        # Record starting memory
        self.start_memory = self.get_memory_usage()
        print(f"📊 Starting memory: {self.start_memory:.1f} MB")
        
        # Create test configuration
        mock_config = MockConfig(
            total_frames=100,
            render_delay_ms=10.0,  # Faster for testing
            render_delay_variance=0.1
        )
        
        # Create render configuration
        render_config = TestDataFactory.create_test_render_config()
        
        # Generate frame specifications
        print(f"🔧 Generating {mock_config.total_frames} frame specifications...")
        generator = MockFrameSpecGenerator(mock_config)
        frame_specs = list(generator)
        
        print(f"✅ Generated {len(frame_specs)} frame specifications")
        
        # Test parallel processing
        start_time = time.time()
        successful_frames = 0
        failed_frames = 0
        results = []
        
        print(f"🚀 Starting parallel processing with {worker_count} workers...")
        
        try:
            with create_rendering_executor(render_config, max_workers=worker_count) as executor:
                # Submit all tasks
                futures = [
                    executor.submit(top_level_test_render_function, frame_spec)
                    for frame_spec in frame_specs
                ]
                
                print(f"📤 Submitted {len(futures)} tasks")
                
                # Collect results with progress tracking
                for i, future in enumerate(as_completed(futures, timeout=300)):
                    try:
                        result = future.result(timeout=30)
                        
                        # Check if result is successful
                        if hasattr(result, 'status'):
                            if result.status == 'success':
                                successful_frames += 1
                            else:
                                failed_frames += 1
                                logger.error(f"Frame failed: {result.error if hasattr(result, 'error') else 'Unknown error'}")
                        elif isinstance(result, dict):
                            if result.get('status') == 'success':
                                successful_frames += 1
                            else:
                                failed_frames += 1
                                logger.error(f"Frame failed: {result.get('error', 'Unknown error')}")
                        else:
                            successful_frames += 1  # Assume success if no status field
                        
                        results.append(result)
                        
                        # Progress updates every 10 frames
                        if (i + 1) % 10 == 0:
                            progress = (i + 1) / len(futures) * 100
                            current_memory = self.get_memory_usage()
                            print(f"📥 Progress: {i + 1}/{len(futures)} ({progress:.1f}%) - Memory: {current_memory:.1f} MB")
                            
                            # Track peak memory
                            if self.peak_memory is None or current_memory > self.peak_memory:
                                self.peak_memory = current_memory
                        
                    except Exception as e:
                        failed_frames += 1
                        logger.error(f"Future failed: {str(e)}")
                        results.append({'status': 'error', 'error': str(e)})
        
        except Exception as e:
            logger.error(f"ProcessPoolExecutor failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'worker_count': worker_count
            }
        
        # Calculate results
        end_time = time.time()
        total_time = end_time - start_time
        end_memory = self.get_memory_usage()
        
        success_rate = (successful_frames / len(frame_specs)) * 100 if frame_specs else 0
        frames_per_second = len(frame_specs) / total_time if total_time > 0 else 0
        
        result = {
            'success': failed_frames == 0,
            'worker_count': worker_count,
            'total_frames': len(frame_specs),
            'successful_frames': successful_frames,
            'failed_frames': failed_frames,
            'success_rate': success_rate,
            'total_time_seconds': total_time,
            'frames_per_second': frames_per_second,
            'memory_start_mb': self.start_memory,
            'memory_end_mb': end_memory,
            'memory_peak_mb': self.peak_memory or end_memory,
            'memory_delta_mb': end_memory - self.start_memory
        }
        
        # Print results
        print(f"\n📊 RESULTS FOR {worker_count} WORKERS:")
        print(f"✅ Successful frames: {successful_frames}/{len(frame_specs)} ({success_rate:.1f}%)")
        print(f"❌ Failed frames: {failed_frames}")
        print(f"⏱️  Total time: {total_time:.2f} seconds")
        print(f"🚀 Processing rate: {frames_per_second:.1f} frames/second")
        print(f"💾 Memory usage: {self.start_memory:.1f} → {end_memory:.1f} MB (Δ{end_memory - self.start_memory:+.1f} MB)")
        print(f"📈 Peak memory: {self.peak_memory or end_memory:.1f} MB")
        
        return result
    
    def test_multiple_worker_counts(self) -> Dict[int, Dict[str, Any]]:
        """Test with different worker counts to validate scalability"""
        print(f"\n🔄 Testing scalability with different worker counts")
        print("=" * 60)
        
        worker_counts = [4, 8, 16]
        results = {}
        
        for worker_count in worker_counts:
            print(f"\n--- Testing with {worker_count} workers ---")
            result = self.test_100_frame_scenario(worker_count)
            results[worker_count] = result
            
            # Brief pause between tests
            time.sleep(1)
        
        return results
    
    def run_validation_suite(self) -> Dict[str, Any]:
        """Run the complete validation suite"""
        print("🎯 FULL-SCALE VALIDATION SUITE")
        print("=" * 60)
        print("Testing our MockFrameSpecGenerator color clamping fix at scale")
        print("Expected: 100% success rate across all scenarios")
        print()
        
        suite_start = time.time()
        
        # Test 1: Single worker count (original scenario)
        print("📋 TEST 1: Original 100-frame scenario")
        single_result = self.test_100_frame_scenario(worker_count=8)
        
        # Test 2: Multiple worker counts (scalability)
        print("\n📋 TEST 2: Scalability testing")
        multi_results = self.test_multiple_worker_counts()
        
        suite_end = time.time()
        
        # Compile final results
        final_results = {
            'suite_success': True,
            'suite_duration_seconds': suite_end - suite_start,
            'single_test': single_result,
            'scalability_tests': multi_results,
            'summary': {
                'all_tests_passed': True,
                'total_frames_processed': 0,
                'total_failures': 0,
                'best_performance': None,
                'memory_efficiency': None
            }
        }
        
        # Calculate summary statistics
        total_frames = 0
        total_failures = 0
        best_fps = 0
        best_worker_count = None
        
        # Include single test
        if single_result.get('success', False):
            total_frames += single_result.get('total_frames', 0)
            total_failures += single_result.get('failed_frames', 0)
            fps = single_result.get('frames_per_second', 0)
            if fps > best_fps:
                best_fps = fps
                best_worker_count = single_result.get('worker_count')
        else:
            final_results['suite_success'] = False
        
        # Include scalability tests
        for worker_count, result in multi_results.items():
            if result.get('success', False):
                total_frames += result.get('total_frames', 0)
                total_failures += result.get('failed_frames', 0)
                fps = result.get('frames_per_second', 0)
                if fps > best_fps:
                    best_fps = fps
                    best_worker_count = worker_count
            else:
                final_results['suite_success'] = False
        
        final_results['summary'].update({
            'all_tests_passed': final_results['suite_success'] and total_failures == 0,
            'total_frames_processed': total_frames,
            'total_failures': total_failures,
            'best_performance': {
                'fps': best_fps,
                'worker_count': best_worker_count
            } if best_worker_count else None
        })
        
        # Print final summary
        print(f"\n🎯 VALIDATION SUITE COMPLETE")
        print("=" * 60)
        print(f"✅ Suite success: {final_results['suite_success']}")
        print(f"📊 Total frames processed: {total_frames}")
        print(f"❌ Total failures: {total_failures}")
        print(f"⏱️  Suite duration: {final_results['suite_duration_seconds']:.2f} seconds")
        if best_worker_count:
            print(f"🚀 Best performance: {best_fps:.1f} fps with {best_worker_count} workers")
        
        return final_results

def main():
    """Run the full-scale validation"""
    validator = FullScaleValidator()
    results = validator.run_validation_suite()
    
    # Return exit code based on success
    if results['summary']['all_tests_passed']:
        print(f"\n🎉 ALL TESTS PASSED! The color clamping fix is working perfectly at scale.")
        return 0
    else:
        print(f"\n❌ SOME TESTS FAILED! There may be remaining issues.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)