#!/usr/bin/env python3
"""
Manual Test Script for Bug Fix Validation
==========================================

Tests the fix for the critical 37% failure rate in parallel rendering.

The bug was caused by runtime import race conditions in test frame detection logic.
This script validates that the fix (moving test logic to worker initialization) works.

Usage:
    python test_bug_fix_manual.py

Expected Result:
    - 100/100 frames should complete successfully (100% success rate)
    - No more "3 out of 8 workers failing" pattern
    - Consistent worker initialization across all processes
"""

import os
import sys
import time
from datetime import datetime

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import core components
from parallel_render_manager import ParallelRenderManager, RenderingConfig
from stateless_renderer import RenderConfig
from test_mock_components import MockFrameSpecGenerator, MockConfig
from clean_test_architecture_v2 import CleanTestableParallelManager, TestConfig


def test_basic_parallel_rendering():
    """
    Test basic parallel rendering with the bug fix.
    
    This reproduces the exact scenario that was failing with 37% failure rate.
    """
    print("🧪 Testing Bug Fix: Basic Parallel Rendering")
    print("=" * 60)
    
    # Configuration that reproduces the original failing scenario
    workers = 8  # Same as user's test
    frames = 100  # Same as user's test
    render_delay = 0.0  # No artificial delay - focus on core logic
    
    print(f"Configuration:")
    print(f"  Workers: {workers}")
    print(f"  Frames: {frames}")
    print(f"  Render delay: {render_delay}ms")
    print()
    
    try:
        # Create test render configuration with correct parameters and available fonts
        font_paths = {}
        available_fonts = []
        
        # Check for available fonts in the fonts directory
        if os.path.exists("fonts/DejaVuSans.ttf"):
            font_paths["DejaVuSans"] = "fonts/DejaVuSans.ttf"
            available_fonts.append("DejaVu Sans")
        
        if os.path.exists("fonts/Arial-Unicode-MS.ttf"):
            font_paths["ArialUnicodeMS"] = "fonts/Arial-Unicode-MS.ttf"
            available_fonts.append("Arial Unicode MS")
        
        if os.path.exists("fonts/NotoSansJP-Regular.ttf"):
            font_paths["NotoSansJP"] = "fonts/NotoSansJP-Regular.ttf"
            available_fonts.append("Noto Sans JP")
        
        # Fallback to system fonts if no custom fonts available
        if not available_fonts:
            available_fonts = ["sans-serif"]
        
        render_config = RenderConfig(
            dpi=96,
            fig_width_pixels=1920,
            fig_height_pixels=1080,
            target_fps=30,
            font_paths=font_paths,
            preferred_fonts=available_fonts,
            album_art_cache_dir="album_art_cache",
            album_art_visibility_threshold=0.0628,
            n_bars=10
        )
        
        # Create mock frame generator
        mock_config = MockConfig(
            total_frames=frames,
            render_delay_ms=render_delay
        )
        generator = MockFrameSpecGenerator(mock_config)
        
        # Setup rendering configuration
        rendering_config = RenderingConfig(max_workers=workers)
        
        # Create DI manager with NO ERROR INJECTION (basic test)
        di_manager = CleanTestableParallelManager(render_config, rendering_config)
        
        # Create empty test configuration (no errors)
        test_config = TestConfig()  # Empty = no test behavior
        
        # Progress tracking
        progress_updates = []
        def progress_callback(progress):
            progress_updates.append({
                'completed': progress.frames_completed,
                'failed': progress.frames_failed,
                'success_rate': progress.success_rate,
                'timestamp': time.time()
            })
            if len(progress_updates) % 10 == 0 or progress.frames_completed >= frames:
                print(f"  Progress: {progress.frames_completed}/{progress.frames_total} "
                      f"({progress.success_rate:.1%} success) "
                      f"[{progress.current_fps:.1f} FPS]")
        
        # Run the test
        print("🚀 Starting parallel rendering...")
        start_time = time.time()
        
        results = di_manager.run_test_scenario(generator, test_config, progress_callback)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Analyze results
        completed = results['stats'].completed_frames
        failed = results['stats'].failed_frames
        total_processed = completed + failed
        
        print(f"\n📊 Results:")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  Completed frames: {completed}")
        print(f"  Failed frames: {failed}")
        print(f"  Total processed: {total_processed}")
        
        if total_processed > 0:
            success_rate = completed / total_processed
            print(f"  Success rate: {success_rate:.1%}")
            fps = completed / duration if duration > 0 else 0.0
            print(f"  Average FPS: {fps:.1f}")
        
        # Show detailed error analysis if there were failures
        if failed > 0:
            print(f"\n💥 DETAILED ERROR ANALYSIS:")
            failed_frames = results.get('failed_frames', [])
            worker_errors = {}
            exception_types = {}
            
            for frame_result in failed_frames:
                # Handle both dict and FrameResult object formats
                if hasattr(frame_result, 'worker_pid'):
                    # FrameResult object
                    worker_pid = frame_result.worker_pid or 'unknown'
                    error_type = frame_result.error_type or 'unknown'
                    frame_index = frame_result.frame_index
                else:
                    # Dictionary format
                    worker_pid = frame_result.get('worker_pid', 'unknown')
                    error_type = frame_result.get('exception_type', frame_result.get('error_type', 'unknown'))
                    frame_index = frame_result.get('frame_index', 'unknown')
                
                # Group by worker
                if worker_pid not in worker_errors:
                    worker_errors[worker_pid] = []
                worker_errors[worker_pid].append((frame_index, error_type))
                
                # Count exception types
                exception_types[error_type] = exception_types.get(error_type, 0) + 1
            
            print(f"  Failed workers: {len(worker_errors)} out of 8")
            print(f"  Exception types: {dict(exception_types)}")
            print(f"  Worker failure breakdown:")
            for worker_pid, errors in worker_errors.items():
                print(f"    Worker {worker_pid}: {len(errors)} failures")
            
            # Show first few detailed errors with full context
            print(f"\n  🔍 Sample Error Details:")
            for i, frame_result in enumerate(failed_frames[:2]):  # First 2 errors
                # Handle both dict and FrameResult object formats
                if hasattr(frame_result, 'worker_pid'):
                    # FrameResult object
                    frame_idx = frame_result.frame_index
                    worker_pid = frame_result.worker_pid or 'unknown'
                    error = frame_result.error_message or 'No error message'
                    exception_type = frame_result.error_type or 'Unknown'
                    traceback_data = getattr(frame_result, 'traceback', None)
                else:
                    # Dictionary format
                    frame_idx = frame_result.get('frame_index', 'unknown')
                    worker_pid = frame_result.get('worker_pid', 'unknown')
                    error = frame_result.get('error', 'No error message')
                    exception_type = frame_result.get('exception_type', 'Unknown')
                    traceback_data = frame_result.get('traceback')
                
                print(f"\n    Error {i+1} - Frame {frame_idx} (Worker {worker_pid}):")
                print(f"      Exception: {exception_type}")
                print(f"      Message: {error}")
                
                # Show key traceback lines if available
                if traceback_data:
                    print(f"      Key traceback lines:")
                    traceback_lines = traceback_data.split('\n')
                    relevant_lines = [line for line in traceback_lines if any(keyword in line.lower() 
                                    for keyword in ['error', 'exception', 'failed', 'stateless_renderer', 'render_frame'])]
                    for line in relevant_lines[:3]:  # Show first 3 relevant lines
                        if line.strip():
                            print(f"        {line.strip()}")
            
            if len(failed_frames) > 2:
                print(f"\n    ... and {len(failed_frames)-2} more errors (check logs for details)")
        
        # Check for the specific bug pattern
        print(f"\n🔍 Bug Pattern Analysis:")
        if failed == 0 and completed == frames:
            print(f"  ✅ SUCCESS: All {frames} frames completed successfully!")
            print(f"  ✅ Bug fix confirmed: No more 37% failure rate")
            return True
        elif failed > 0:
            failure_rate = failed / total_processed if total_processed > 0 else 0
            print(f"  ❌ FAILURE: {failed} frames failed ({failure_rate:.1%} failure rate)")
            
            # Check if it's the old bug pattern
            if abs(failure_rate - 0.375) < 0.05:  # ~37.5% = 3/8 workers
                print(f"  🚨 OLD BUG STILL PRESENT: 3/8 worker failure pattern detected")
                print(f"  🔍 Root cause hypothesis was INCORRECT - need deeper analysis")
            else:
                print(f"  ⚠️  Different failure pattern - may be new issue or different root cause")
            return False
        else:
            print(f"  ⚠️  Unexpected result: {completed} completed, {failed} failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_worker_initialization_logging():
    """
    Test that worker initialization is working correctly.
    
    This should show all 8 workers initializing successfully.
    """
    print("\n🔧 Testing Worker Initialization Logging")
    print("=" * 60)
    
    try:
        # Create minimal test to check worker init with available fonts
        font_paths = {}
        available_fonts = []
        
        # Check for available fonts in the fonts directory
        if os.path.exists("fonts/DejaVuSans.ttf"):
            font_paths["DejaVuSans"] = "fonts/DejaVuSans.ttf"
            available_fonts.append("DejaVu Sans")
        
        if os.path.exists("fonts/Arial-Unicode-MS.ttf"):
            font_paths["ArialUnicodeMS"] = "fonts/Arial-Unicode-MS.ttf"
            available_fonts.append("Arial Unicode MS")
        
        # Fallback to system fonts if no custom fonts available
        if not available_fonts:
            available_fonts = ["sans-serif"]
        
        render_config = RenderConfig(
            dpi=96,
            fig_width_pixels=1920,
            fig_height_pixels=1080,
            target_fps=30,
            font_paths=font_paths,
            preferred_fonts=available_fonts,
            album_art_cache_dir="album_art_cache",
            album_art_visibility_threshold=0.0628,
            n_bars=10
        )
        
        mock_config = MockConfig(total_frames=16, render_delay_ms=10.0)  # 2 frames per worker
        generator = MockFrameSpecGenerator(mock_config)
        
        rendering_config = RenderingConfig(max_workers=8)
        di_manager = CleanTestableParallelManager(render_config, rendering_config)
        test_config = TestConfig()
        
        print("📝 Worker initialization messages should appear below:")
        print("    Look for '[Worker PID: XXXX] Initialized successfully' messages")
        print()
        
        results = di_manager.run_test_scenario(generator, test_config)
        
        completed = results['stats'].completed_frames
        failed = results['stats'].failed_frames
        
        print(f"\n📊 Worker Init Test Results:")
        print(f"  Completed: {completed}, Failed: {failed}")
        
        if failed == 0:
            print(f"  ✅ All workers initialized successfully")
            return True
        else:
            print(f"  ❌ {failed} frames failed - worker init issues detected")
            return False
            
    except Exception as e:
        print(f"❌ Worker init test failed: {e}")
        return False


def main():
    """Run the manual test suite"""
    print("🏥 Manual Bug Fix Validation Suite")
    print("=" * 80)
    print("Testing fix for critical 37% failure rate in parallel rendering")
    print("Original issue: Runtime import race conditions in test frame detection")
    print("Fix: Move test logic to worker initialization phase")
    print()
    
    # Set up environment
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Create output directory if needed
    os.makedirs("test_frames", exist_ok=True)
    
    # Run tests
    test_results = []
    
    # Test 1: Basic parallel rendering (the failing scenario)
    result1 = test_basic_parallel_rendering()
    test_results.append(("Basic Parallel Rendering", result1))
    
    # Test 2: Worker initialization logging
    result2 = test_worker_initialization_logging()
    test_results.append(("Worker Initialization", result2))
    
    # Summary
    print("\n" + "=" * 80)
    print("🏁 MANUAL TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Bug fix is successful - 37% failure rate eliminated")
        print("🚀 Ready for integration into main test suite")
    else:
        print(f"\n❌ {total - passed} TESTS FAILED")
        print("🚨 Bug fix needs further investigation")
        print("💡 Check worker initialization and import issues")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)