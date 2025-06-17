#!/usr/bin/env python3
"""
Debug function override in parallel manager
"""

import os
import sys

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_function_override():
    """Test if function override works correctly"""
    print("Testing function override...")
    
    from test_mock_components import mock_render_frame_from_spec
    
    # Test direct import
    from stateless_renderer import render_frame_from_spec as original_render
    
    print("1. Testing direct function calls:")
    test_frame = {'frame_index': 1, 'display_timestamp': '2024-01-01T12:00:00Z', 'bars': []}
    
    # Call original
    try:
        original_result = original_render(test_frame)
        print(f"  Original function: Success (or error)")
    except Exception as e:
        print(f"  Original function: Error - {e}")
    
    # Call mock
    mock_result = mock_render_frame_from_spec(test_frame)
    print(f"  Mock function: {mock_result['status']}")
    
    print("\n2. Testing module override:")
    import parallel_render_manager
    
    # Check what function is being used
    print(f"  Current function: {parallel_render_manager.render_frame_from_spec}")
    
    # Override
    original_func = parallel_render_manager.render_frame_from_spec
    parallel_render_manager.render_frame_from_spec = mock_render_frame_from_spec
    
    print(f"  After override: {parallel_render_manager.render_frame_from_spec}")
    
    # Test the override
    override_result = parallel_render_manager.render_frame_from_spec(test_frame)
    print(f"  Override result: {override_result['status']}")
    
    # Restore
    parallel_render_manager.render_frame_from_spec = original_func
    
    print("\n3. Testing with ProcessPoolExecutor:")
    import concurrent.futures
    from test_mock_components import (
        MockConfig, set_mock_config_for_workers, mock_worker_initializer
    )
    
    # Setup mock config
    mock_config = MockConfig(
        error_type='transient',
        error_frame_numbers=[1]
    )
    set_mock_config_for_workers(mock_config)
    
    # Test with executor
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=1,
        initializer=mock_worker_initializer,
        initargs=({},)
    ) as executor:
        # Submit using the mock function directly
        future = executor.submit(mock_render_frame_from_spec, test_frame)
        executor_result = future.result()
        print(f"  Executor with mock: {executor_result['status']} - {executor_result.get('error_type', 'none')}")
        
        # Submit using the module function (this should show if the override works)
        future2 = executor.submit(parallel_render_manager.render_frame_from_spec, test_frame)
        module_result = future2.result()
        print(f"  Executor with module: {module_result['status']} - {module_result.get('error_type', 'none')}")

if __name__ == "__main__":
    test_function_override()