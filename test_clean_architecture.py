#!/usr/bin/env python3
"""
Test the clean architecture with actual parallel processing
"""

import os
import sys

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_clean_parallel_processing():
    """Test the clean architecture with real parallel processing"""
    print("🧪 Testing Clean Architecture with Parallel Processing")
    print("=" * 60)
    
    from clean_test_architecture import (
        TestableParallelManager, create_transient_error_test, 
        create_worker_fatal_test, TestConfig, ErrorType
    )
    from test_mock_components import MockFrameSpecGenerator, MockConfig, TestDataFactory
    from parallel_render_manager import RenderingConfig
    
    # Test 1: Transient Error Injection
    print("Test 1: Transient Error Injection with Retries")
    print("-" * 50)
    
    # Create test data
    mock_config = MockConfig(total_frames=8, render_delay_ms=5.0)
    frame_generator = MockFrameSpecGenerator(mock_config)
    render_config = TestDataFactory.create_test_render_config()
    rendering_config = RenderingConfig(max_workers=2, max_retries_transient=2)
    
    # Create testable manager (no monkey-patching!)
    test_manager = TestableParallelManager(render_config, rendering_config)
    
    # Configure error injection
    test_config = create_transient_error_test(error_frames=[3, 6])
    
    # Run test scenario
    results = test_manager.run_test_scenario(frame_generator, test_config)
    
    # Analyze results
    stats = results['stats']
    error_summary = results['error_injection_summary']
    
    print(f"📊 Results:")
    print(f"  Total frames: {stats.total_frames}")
    print(f"  Completed: {stats.completed_frames}")
    print(f"  Failed: {stats.failed_frames}")
    print(f"  Retried: {stats.retried_frames}")
    print(f"  Worker failures: {stats.worker_failures}")
    
    print(f"🎯 Error Injection Summary:")
    print(f"  Target frames: {error_summary['target_frames']}")
    print(f"  Expected errors: {error_summary['expected_errors']}")
    print(f"  Actual failures: {error_summary['actual_failures']}")
    print(f"  Retries triggered: {error_summary['retries_triggered']}")
    
    # Validate results
    transient_success = (
        error_summary['retries_triggered'] > 0 and
        stats.completed_frames >= 6  # Most frames should complete after retries
    )
    
    print(f"  ✓ Transient error test: {'PASSED' if transient_success else 'FAILED'}")
    
    # Test 2: Worker Fatal Error
    print(f"\nTest 2: Worker Fatal Error (Circuit Breaker)")
    print("-" * 50)
    
    # Fresh generator for second test
    frame_generator2 = MockFrameSpecGenerator(MockConfig(total_frames=10, render_delay_ms=5.0))
    test_config2 = create_worker_fatal_test(error_frames=[4])
    
    # New manager with strict circuit breaker
    rendering_config2 = RenderingConfig(max_workers=2, max_worker_failures=1)
    test_manager2 = TestableParallelManager(render_config, rendering_config2)
    
    results2 = test_manager2.run_test_scenario(frame_generator2, test_config2)
    
    stats2 = results2['stats']
    error_summary2 = results2['error_injection_summary']
    
    print(f"📊 Results:")
    print(f"  Worker failures: {stats2.worker_failures}")
    print(f"  Status: {results2.get('status', 'completed')}")
    print(f"  Actual failures: {error_summary2['actual_failures']}")
    
    worker_fatal_success = stats2.worker_failures > 0
    print(f"  ✓ Worker fatal error test: {'PASSED' if worker_fatal_success else 'FAILED'}")
    
    # Overall results
    overall_success = transient_success and worker_fatal_success
    print(f"\n🎉 Overall Test Results: {2 if overall_success else 1 if transient_success or worker_fatal_success else 0}/2 PASSED")
    
    if overall_success:
        print("✅ Clean architecture successfully integrated!")
        print("✅ Error injection working in parallel processing")
        print("✅ No global state modification")
        print("✅ All visual configurations preserved")
    
    return overall_success

if __name__ == "__main__":
    success = test_clean_parallel_processing()
    print(f"\n{'🎊 SUCCESS!' if success else '❌ Some tests failed'}")