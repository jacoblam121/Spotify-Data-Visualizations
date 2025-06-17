#!/usr/bin/env python3
"""
Debug error format returned by mock renderer
"""

import os
import sys

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_error_format():
    """Test the exact format of errors returned by mock renderer"""
    print("Testing error format...")
    
    from test_mock_components import (
        MockConfig, set_mock_config_for_workers, mock_worker_initializer,
        mock_render_frame_from_spec
    )
    
    # Setup mock configuration with errors
    mock_config = MockConfig(
        total_frames=5,
        error_type='transient',
        error_frame_numbers=[2],
        render_delay_ms=1.0
    )
    
    set_mock_config_for_workers(mock_config)
    mock_worker_initializer({'test': 'config'})
    
    # Test different frame types
    frames_to_test = [
        {'frame_index': 1, 'display_timestamp': '2024-01-01T12:00:00Z', 'bars': []},  # Normal
        {'frame_index': 2, 'display_timestamp': '2024-01-01T12:00:00Z', 'bars': []},  # Should error
        {'frame_index': 3, 'display_timestamp': '2024-01-01T12:00:00Z', 'bars': []},  # Normal
    ]
    
    for frame in frames_to_test:
        result = mock_render_frame_from_spec(frame)
        print(f"\nFrame {frame['frame_index']}:")
        print(f"  Status: {result['status']}")
        print(f"  Error type: {result.get('error_type', 'none')}")
        print(f"  Error message: {result.get('error', 'none')}")
        print(f"  Full result keys: {list(result.keys())}")

def test_with_parallel_manager():
    """Test with a minimal parallel manager setup"""
    print("\n" + "="*50)
    print("Testing with parallel manager...")
    
    from parallel_render_manager import ParallelRenderManager, RenderingConfig
    from test_mock_components import (
        MockFrameSpecGenerator, MockConfig, TestDataFactory,
        set_mock_config_for_workers, mock_worker_initializer, mock_render_frame_from_spec
    )
    
    # Setup mock configuration with a single error
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
    
    # Enable debug logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        print("Running parallel rendering...")
        results = manager.render_frames(generator)
        
        print(f"\nResults:")
        print(f"  Completed: {results['stats'].completed_frames}")
        print(f"  Failed: {results['stats'].failed_frames}")
        print(f"  Retried: {results['stats'].retried_frames}")
        print(f"  Worker failures: {results['stats'].worker_failures}")
        
        # Print individual frame results
        if 'frame_results' in results:
            print(f"\nFrame results:")
            for frame_idx, frame_result in results['frame_results'].items():
                print(f"  Frame {frame_idx}: {frame_result.status} (retries: {frame_result.retry_count})")
        
    finally:
        # Restore functions
        parallel_render_manager.initialize_render_worker = original_initialize
        parallel_render_manager.render_frame_from_spec = original_render
        stateless_renderer.render_frame_from_spec = original_stateless_render

if __name__ == "__main__":
    test_error_format()
    test_with_parallel_manager()