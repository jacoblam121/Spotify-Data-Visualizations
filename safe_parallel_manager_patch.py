#!/usr/bin/env python3
"""
Safe parallel manager patch that preserves all visual configurations
"""

import os
import sys

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Global test configuration for worker functions
_CURRENT_TEST_CONFIG = None

def set_test_config(test_config):
    """Set the global test configuration"""
    global _CURRENT_TEST_CONFIG
    _CURRENT_TEST_CONFIG = test_config

def safe_test_render_wrapper(frame_spec):
    """
    Module-level render wrapper that can be pickled.
    This is completely isolated and won't affect visual layout.
    """
    global _CURRENT_TEST_CONFIG
    
    frame_index = frame_spec.get('frame_index', 0)
    worker_pid = os.getpid()
    
    # Check for error injection
    if _CURRENT_TEST_CONFIG:
        error_type = _CURRENT_TEST_CONFIG.get('error_type')
        error_frame_numbers = _CURRENT_TEST_CONFIG.get('error_frame_numbers', [])
        
        if frame_index in error_frame_numbers and error_type:
            return {
                'status': 'error',
                'error_type': error_type,
                'frame_index': frame_index,
                'error': f'Simulated {error_type} error on frame {frame_index}',
                'render_time_seconds': 0.01,
                'worker_pid': worker_pid
            }
    
    # Normal processing - call the real render function
    # This preserves ALL existing visual configurations
    from stateless_renderer import render_frame_from_spec
    return render_frame_from_spec(frame_spec)

def safe_test_init_wrapper(render_config_dict):
    """
    Module-level initializer wrapper that can be pickled.
    This is completely isolated and won't affect visual layout.
    """
    # Call the real initializer to preserve all visual settings
    from stateless_renderer import initialize_render_worker
    return initialize_render_worker(render_config_dict)

class SafeParallelManagerTester:
    """
    Safe testing approach that doesn't modify any existing code or visual settings.
    Uses function replacement rather than module patching.
    """
    
    def __init__(self):
        self.original_functions = {}
    
    def test_with_error_injection(self, error_config):
        """Test parallel manager with error injection - completely safe"""
        print(f"Testing with error injection: {error_config}")
        
        from parallel_render_manager import ParallelRenderManager, RenderingConfig
        from test_mock_components import MockFrameSpecGenerator, MockConfig, TestDataFactory
        
        # Set the global test config
        set_test_config(error_config)
        
        # Create test data
        mock_config = MockConfig(
            total_frames=5,
            render_delay_ms=10.0
        )
        
        generator = MockFrameSpecGenerator(mock_config)
        render_config = TestDataFactory.create_test_render_config()
        rendering_config = RenderingConfig(max_workers=1, max_retries_transient=2)
        
        # Create a modified manager that uses our wrapper
        manager = ParallelRenderManager(render_config, rendering_config)
        
        # Store original methods
        original_render_with_executor = manager._render_with_executor
        
        def safe_render_with_executor(executor, frame_spec_generator, progress_callback):
            """
            Safe version that uses wrapper functions without affecting any visual code
            """
            import concurrent.futures
            
            # Create a new executor with our test functions
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=rendering_config.max_workers,
                initializer=safe_test_init_wrapper,
                initargs=(render_config.to_dict(),),
                max_tasks_per_child=rendering_config.maxtasksperchild
            ) as test_executor:
                
                # Copy the original logic but use our test render function
                logger = manager.__class__.__module__
                print(f"Starting frame processing pipeline with test config...")
                
                manager._pending_tasks.clear()
                max_in_flight = rendering_config.max_workers * rendering_config.backpressure_multiplier
                
                # Submit initial batch using test render function
                submitted = 0
                for _ in range(max_in_flight):
                    try:
                        frame_spec = next(frame_spec_generator)
                        from parallel_render_manager import TaskContext
                        import time
                        task_context = TaskContext(
                            frame_spec=frame_spec,
                            retry_count=0,
                            submission_time=time.time()
                        )
                        future = test_executor.submit(safe_test_render_wrapper, frame_spec)
                        task_context.future = future
                        manager._pending_tasks[future] = task_context
                        submitted += 1
                    except StopIteration:
                        break
                
                print(f"Submitted initial batch of {submitted} tasks with test config")
                
                # Process results using the existing logic
                completed_count = 0
                while manager._pending_tasks and not manager._shutdown_requested:
                    try:
                        for future in concurrent.futures.as_completed(manager._pending_tasks, timeout=1.0):
                            task_context = manager._pending_tasks.pop(future)
                            frame_index = task_context.frame_index
                            
                            # Use existing result processing logic
                            result = manager._process_completed_future(future, task_context)
                            manager._frame_results[frame_index] = result
                            
                            # Handle results using existing logic
                            if result.status.value == 'completed':
                                completed_count += 1
                                manager.stats.completed_frames += 1
                                if result.render_time_seconds:
                                    manager.stats.total_render_time += result.render_time_seconds
                            elif result.status.value == 'failed_transient':
                                # Use existing retry logic
                                if manager._should_retry_frame(frame_index, task_context.retry_count):
                                    # Create retry task with test function
                                    retry_context = TaskContext(
                                        frame_spec=task_context.frame_spec,
                                        retry_count=task_context.retry_count + 1,
                                        submission_time=time.time()
                                    )
                                    retry_future = test_executor.submit(safe_test_render_wrapper, task_context.frame_spec)
                                    retry_context.future = retry_future
                                    manager._pending_tasks[retry_future] = retry_context
                                    manager.stats.retried_frames += 1
                                    print(f"Frame {frame_index}: Retrying (attempt {retry_context.retry_count})")
                                else:
                                    from parallel_render_manager import FrameStatus
                                    result.status = FrameStatus.FAILED_MAX_RETRIES
                                    manager.stats.failed_frames += 1
                                    print(f"Frame {frame_index}: Max retries exceeded")
                            elif result.status.value in ['failed_fatal', 'failed_max_retries']:
                                manager.stats.failed_frames += 1
                                if result.error_type == 'worker_fatal':
                                    manager.stats.worker_failures += 1
                            
                            # Try to submit next task
                            try:
                                frame_spec = next(frame_spec_generator)
                                task_context = TaskContext(
                                    frame_spec=frame_spec,
                                    retry_count=0,
                                    submission_time=time.time()
                                )
                                future = test_executor.submit(safe_test_render_wrapper, frame_spec)
                                task_context.future = future
                                manager._pending_tasks[future] = task_context
                            except StopIteration:
                                pass
                            
                            # Update progress
                            if progress_callback and completed_count % rendering_config.progress_update_interval == 0:
                                progress_info = manager._create_progress_info()
                                progress_callback(progress_info)
                                
                    except concurrent.futures.TimeoutError:
                        continue
                    except Exception as e:
                        print(f"Error in processing loop: {e}")
                        break
                
                print(f"Processing complete: {manager.stats.completed_frames} completed, {manager.stats.failed_frames} failed")
                return manager._create_final_results()
        
        # Temporarily replace the method
        manager._render_with_executor = safe_render_with_executor
        
        try:
            # Run the test
            results = manager.render_frames(generator)
            
            print(f"\n📊 Test Results:")
            print(f"  Completed: {results['stats'].completed_frames}")
            print(f"  Failed: {results['stats'].failed_frames}")
            print(f"  Retried: {results['stats'].retried_frames}")
            print(f"  Worker failures: {results['stats'].worker_failures}")
            
            return results
            
        finally:
            # Restore original method
            manager._render_with_executor = original_render_with_executor

def test_safe_approach():
    """Test the safe approach"""
    print("🧪 Testing Safe Parallel Manager Approach")
    print("=" * 60)
    print("✅ This approach preserves ALL visual configurations")
    print("✅ No module patching or process start method changes")
    print("✅ Completely isolated test logic")
    print()
    
    tester = SafeParallelManagerTester()
    
    # Test 1: Transient errors
    print("Test 1: Transient Error Injection")
    print("-" * 40)
    error_config = {
        'error_type': 'transient',
        'error_frame_numbers': [2, 4]
    }
    results1 = tester.test_with_error_injection(error_config)
    
    success1 = results1['stats'].retried_frames > 0
    print(f"✓ Transient error test: {'PASSED' if success1 else 'FAILED'}")
    
    print("\nTest 2: Worker Fatal Error")
    print("-" * 40)
    error_config = {
        'error_type': 'worker_fatal',
        'error_frame_numbers': [1]
    }
    results2 = tester.test_with_error_injection(error_config)
    
    success2 = results2['stats'].worker_failures > 0
    print(f"✓ Worker fatal error test: {'PASSED' if success2 else 'FAILED'}")
    
    print(f"\n🎉 Overall result: {2 if success1 and success2 else 1 if success1 or success2 else 0}/2 tests passed")
    
    return success1 and success2

if __name__ == "__main__":
    test_safe_approach()