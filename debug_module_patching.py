#!/usr/bin/env python3
"""
Debug module patching approach
"""

import os
import sys

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_module_patching():
    """Test different patching approaches"""
    print("Testing module patching approaches...")
    
    # Enable debug logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    from parallel_render_manager import ParallelRenderManager, RenderingConfig
    from test_mock_components import (
        MockFrameSpecGenerator, MockConfig, TestDataFactory,
        set_mock_config_for_workers, mock_worker_initializer, mock_render_frame_from_spec
    )
    
    # Setup mock configuration with transient errors
    mock_config = MockConfig(
        total_frames=3,
        render_delay_ms=1.0,
        error_type='transient',
        error_frame_numbers=[1]  # Error on frame 1
    )
    
    # Create components
    generator = MockFrameSpecGenerator(mock_config)
    render_config = TestDataFactory.create_test_render_config()
    rendering_config = RenderingConfig(max_workers=1, max_retries_transient=1)
    manager = ParallelRenderManager(render_config, rendering_config)
    
    # Set up mock config
    set_mock_config_for_workers(mock_config)
    
    # Try patching at the module level directly
    import parallel_render_manager
    import stateless_renderer
    
    print("\n1. Before patching:")
    print(f"  stateless_renderer.render_frame_from_spec: {stateless_renderer.render_frame_from_spec}")
    
    # Store original functions 
    original_stateless_render = stateless_renderer.render_frame_from_spec
    original_stateless_init = stateless_renderer.initialize_render_worker
    original_parallel_init = parallel_render_manager.initialize_render_worker
    
    # Patch the stateless_renderer module (this is what the parallel manager uses now)
    stateless_renderer.render_frame_from_spec = mock_render_frame_from_spec
    stateless_renderer.initialize_render_worker = mock_worker_initializer
    parallel_render_manager.initialize_render_worker = mock_worker_initializer
    
    print("\n2. After patching:")
    print(f"  stateless_renderer.render_frame_from_spec: {stateless_renderer.render_frame_from_spec}")
    
    # Test by directly importing 
    from stateless_renderer import render_frame_from_spec as test_import
    print(f"  Dynamic import result: {test_import}")
    print(f"  Is it the mock? {test_import is mock_render_frame_from_spec}")
    
    # Test direct call
    test_frame = {'frame_index': 1, 'display_timestamp': '2024-01-01T12:00:00Z', 'bars': []}
    result = test_import(test_frame)
    print(f"  Direct call result: {result['status']} - {result.get('error_type', 'none')}")
    
    try:
        # Test with parallel manager
        print("\n3. Testing with parallel manager...")
        results = manager.render_frames(generator)
        
        print(f"  Completed: {results['stats'].completed_frames}")
        print(f"  Failed: {results['stats'].failed_frames}")
        print(f"  Retried: {results['stats'].retried_frames}")
        
        # Check individual frame results
        for frame_idx, frame_result in results['frame_results'].items():
            print(f"  Frame {frame_idx}: {frame_result.status}")
    
    finally:
        # Restore functions
        stateless_renderer.render_frame_from_spec = original_stateless_render
        stateless_renderer.initialize_render_worker = original_stateless_init
        parallel_render_manager.initialize_render_worker = original_parallel_init

if __name__ == "__main__":
    test_module_patching()