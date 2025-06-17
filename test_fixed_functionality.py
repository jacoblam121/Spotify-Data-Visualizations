#!/usr/bin/env python3
"""
Test the fixed error injection and memory monitoring functionality.
"""

import os
import sys

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_transient_error_injection():
    """Test that transient error injection now works"""
    print("Testing fixed transient error injection...")
    
    try:
        from parallel_render_manager import ParallelRenderManager, RenderingConfig
        from test_mock_components import (
            MockFrameSpecGenerator, MockConfig, TestDataFactory,
            set_mock_config_for_workers, mock_worker_initializer, mock_render_frame_from_spec
        )
        
        # Setup mock configuration with transient errors
        mock_config = MockConfig(
            total_frames=10,
            render_delay_ms=10.0,
            error_type='transient',
            error_frame_numbers=[3, 7]
        )
        
        # Create components
        generator = MockFrameSpecGenerator(mock_config)
        render_config = TestDataFactory.create_test_render_config()
        rendering_config = RenderingConfig(max_workers=2, max_retries_transient=2)
        manager = ParallelRenderManager(render_config, rendering_config)
        
        # Override with mock functions using proper worker initialization
        import parallel_render_manager
        import stateless_renderer
        original_parallel_init = parallel_render_manager.initialize_render_worker
        original_parallel_render = parallel_render_manager.render_frame_from_spec
        original_stateless_init = stateless_renderer.initialize_render_worker
        original_stateless_render = stateless_renderer.render_frame_from_spec
        
        # Use the new mock worker initializer pattern
        set_mock_config_for_workers(mock_config)
        # Override both modules since parallel manager uses dynamic imports
        parallel_render_manager.initialize_render_worker = mock_worker_initializer
        parallel_render_manager.render_frame_from_spec = mock_render_frame_from_spec
        stateless_renderer.initialize_render_worker = mock_worker_initializer
        stateless_renderer.render_frame_from_spec = mock_render_frame_from_spec
        
        # Run test
        print("  Running rendering with error injection on frames [3, 7]...")
        results = manager.render_frames(generator)
        
        # Restore functions
        parallel_render_manager.initialize_render_worker = original_parallel_init
        parallel_render_manager.render_frame_from_spec = original_parallel_render
        stateless_renderer.initialize_render_worker = original_stateless_init
        stateless_renderer.render_frame_from_spec = original_stateless_render
        
        # Analyze results
        completed = results['stats'].completed_frames
        failed = results['stats'].failed_frames
        retried = results['stats'].retried_frames
        
        print(f"  Completed: {completed}, Failed: {failed}, Retried: {retried}")
        
        # Check that retries occurred
        success = retried > 0 and completed >= 8  # Should complete most frames after retries
        print(f"  ✓ Error injection and retry: {'PASSED' if success else 'FAILED'}")
        
        return success
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_worker_fatal_error():
    """Test that worker fatal error injection works"""
    print("\nTesting fixed worker fatal error injection...")
    
    try:
        from parallel_render_manager import ParallelRenderManager, RenderingConfig
        from test_mock_components import (
            MockFrameSpecGenerator, MockConfig, TestDataFactory,
            set_mock_config_for_workers, mock_worker_initializer, mock_render_frame_from_spec
        )
        
        # Setup mock configuration with worker fatal error
        mock_config = MockConfig(
            total_frames=15,
            render_delay_ms=10.0,
            error_type='worker_fatal',
            error_frame_numbers=[8]
        )
        
        # Create components
        generator = MockFrameSpecGenerator(mock_config)
        render_config = TestDataFactory.create_test_render_config()
        rendering_config = RenderingConfig(max_workers=2, max_worker_failures=1)
        manager = ParallelRenderManager(render_config, rendering_config)
        
        # Override with mock functions
        import parallel_render_manager
        import stateless_renderer
        original_parallel_init = parallel_render_manager.initialize_render_worker
        original_parallel_render = parallel_render_manager.render_frame_from_spec
        original_stateless_init = stateless_renderer.initialize_render_worker
        original_stateless_render = stateless_renderer.render_frame_from_spec
        
        set_mock_config_for_workers(mock_config)
        # Override both modules since parallel manager uses dynamic imports
        parallel_render_manager.initialize_render_worker = mock_worker_initializer
        parallel_render_manager.render_frame_from_spec = mock_render_frame_from_spec
        stateless_renderer.initialize_render_worker = mock_worker_initializer
        stateless_renderer.render_frame_from_spec = mock_render_frame_from_spec
        
        # Run test
        print("  Running rendering with worker fatal error on frame 8...")
        results = manager.render_frames(generator)
        
        # Restore functions
        parallel_render_manager.initialize_render_worker = original_parallel_init
        parallel_render_manager.render_frame_from_spec = original_parallel_render
        stateless_renderer.initialize_render_worker = original_stateless_init
        stateless_renderer.render_frame_from_spec = original_stateless_render
        
        # Analyze results
        worker_failures = results['stats'].worker_failures
        status = results.get('status', 'unknown')
        
        print(f"  Worker failures: {worker_failures}, Status: {status}")
        
        # Check that worker failure was detected
        success = worker_failures > 0
        print(f"  ✓ Worker fatal error detection: {'PASSED' if success else 'FAILED'}")
        
        return success
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_leak_simulation():
    """Test that memory leak simulation works"""
    print("\nTesting fixed memory leak simulation...")
    
    try:
        from parallel_render_manager import ParallelRenderManager, RenderingConfig
        from test_mock_components import (
            MockFrameSpecGenerator, MockConfig, TestDataFactory,
            set_mock_config_for_workers, mock_worker_initializer, mock_render_frame_from_spec
        )
        
        # Setup mock configuration with memory leak
        mock_config = MockConfig(
            total_frames=20,
            render_delay_ms=5.0,
            simulate_memory_leak=True,
            memory_leak_per_frame_mb=0.5  # 0.5MB per frame
        )
        
        # Create components
        generator = MockFrameSpecGenerator(mock_config)
        render_config = TestDataFactory.create_test_render_config()
        rendering_config = RenderingConfig(max_workers=2)
        manager = ParallelRenderManager(render_config, rendering_config)
        
        # Override with mock functions
        import parallel_render_manager
        import stateless_renderer
        original_parallel_init = parallel_render_manager.initialize_render_worker
        original_parallel_render = parallel_render_manager.render_frame_from_spec
        original_stateless_init = stateless_renderer.initialize_render_worker
        original_stateless_render = stateless_renderer.render_frame_from_spec
        
        set_mock_config_for_workers(mock_config)
        # Override both modules since parallel manager uses dynamic imports
        parallel_render_manager.initialize_render_worker = mock_worker_initializer
        parallel_render_manager.render_frame_from_spec = mock_render_frame_from_spec
        stateless_renderer.initialize_render_worker = mock_worker_initializer
        stateless_renderer.render_frame_from_spec = mock_render_frame_from_spec
        
        # Run test
        print("  Running rendering with memory leak simulation...")
        results = manager.render_frames(generator)
        
        # Restore functions
        parallel_render_manager.initialize_render_worker = original_parallel_init
        parallel_render_manager.render_frame_from_spec = original_parallel_render
        stateless_renderer.initialize_render_worker = original_stateless_init
        stateless_renderer.render_frame_from_spec = original_stateless_render
        
        # Analyze worker-reported memory deltas
        worker_memory_deltas = []
        if 'frame_results' in results:
            for frame_idx, frame_result in results['frame_results'].items():
                if hasattr(frame_result, 'memory_delta_bytes') and frame_result.memory_delta_bytes:
                    worker_memory_deltas.append(frame_result.memory_delta_bytes / (1024 * 1024))
        
        total_worker_memory_delta = sum(worker_memory_deltas) if worker_memory_deltas else 0
        expected_leak = 20 * 0.5  # 20 frames * 0.5MB each = 10MB
        
        print(f"  Worker memory deltas collected: {len(worker_memory_deltas)}")
        print(f"  Total worker memory delta: {total_worker_memory_delta:.1f} MB")
        print(f"  Expected leak: ~{expected_leak:.1f} MB")
        
        # Check that memory leak was detected
        success = total_worker_memory_delta > expected_leak * 0.3  # Allow for variance
        print(f"  ✓ Memory leak detection: {'PASSED' if success else 'FAILED'}")
        
        return success
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all fixed functionality tests"""
    print("=" * 60)
    print("Testing Fixed Error Injection and Memory Monitoring")
    print("=" * 60)
    
    tests = [
        test_transient_error_injection,
        test_worker_fatal_error,
        test_memory_leak_simulation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Results:")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All fixed functionality tests passed!")
        print("\n✅ The multiprocessing isolation issues have been resolved!")
        print("✅ Error injection now works correctly across worker processes")
        print("✅ Memory leak simulation is properly detected")
        return True
    else:
        print("❌ Some tests still failing - need further debugging")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)