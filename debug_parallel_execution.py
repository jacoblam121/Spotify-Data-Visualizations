#!/usr/bin/env python3
"""
Debug parallel execution with detailed logging
"""

import os
import sys
import logging

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_parallel_execution_debug():
    """Debug what's actually happening in parallel execution"""
    print("Testing parallel execution with detailed logging...")
    
    # Setup detailed logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    from parallel_render_manager import ParallelRenderManager, RenderingConfig
    from test_mock_components import (
        MockFrameSpecGenerator, MockConfig, TestDataFactory,
        set_mock_config_for_workers, mock_worker_initializer, mock_render_frame_from_spec
    )
    
    # Setup mock configuration with transient errors
    mock_config = MockConfig(
        total_frames=5,
        render_delay_ms=10.0,
        error_type='transient',
        error_frame_numbers=[2]  # Error on frame 2
    )
    
    # Create components
    generator = MockFrameSpecGenerator(mock_config)
    render_config = TestDataFactory.create_test_render_config()
    rendering_config = RenderingConfig(max_workers=1, max_retries_transient=2)  # Single worker for easier debugging
    manager = ParallelRenderManager(render_config, rendering_config)
    
    # Override with mock functions
    import parallel_render_manager
    import stateless_renderer
    original_initialize = parallel_render_manager.initialize_render_worker
    original_render = parallel_render_manager.render_frame_from_spec
    original_stateless_render = stateless_renderer.render_frame_from_spec
    
    set_mock_config_for_workers(mock_config)
    parallel_render_manager.initialize_render_worker = mock_worker_initializer
    parallel_render_manager.render_frame_from_spec = mock_render_frame_from_spec
    stateless_renderer.render_frame_from_spec = mock_render_frame_from_spec
    
    # Add custom result processor to see what the worker returns
    original_process_future = manager._process_completed_future
    
    def debug_process_future(future, task_context):
        frame_index = task_context.frame_index
        print(f"\n🔍 Processing frame {frame_index}:")
        
        try:
            worker_result = future.result()
            print(f"  Worker result: {worker_result}")
            print(f"  Status: {worker_result.get('status', 'missing')}")
            print(f"  Error type: {worker_result.get('error_type', 'none')}")
            print(f"  Error message: {worker_result.get('error', 'none')}")
            
            # Call original processor
            result = original_process_future(future, task_context)
            print(f"  Final status: {result.status}")
            print(f"  Retry count: {result.retry_count}")
            return result
        except Exception as e:
            print(f"  Exception: {e}")
            return original_process_future(future, task_context)
    
    manager._process_completed_future = debug_process_future
    
    try:
        print("Running parallel rendering with debug logging...")
        results = manager.render_frames(generator)
        
        print(f"\n📊 Final Results:")
        print(f"  Completed: {results['stats'].completed_frames}")
        print(f"  Failed: {results['stats'].failed_frames}")
        print(f"  Retried: {results['stats'].retried_frames}")
        print(f"  Worker failures: {results['stats'].worker_failures}")
        
    finally:
        # Restore functions
        parallel_render_manager.initialize_render_worker = original_initialize
        parallel_render_manager.render_frame_from_spec = original_render
        stateless_renderer.render_frame_from_spec = original_stateless_render
        manager._process_completed_future = original_process_future

if __name__ == "__main__":
    test_parallel_execution_debug()