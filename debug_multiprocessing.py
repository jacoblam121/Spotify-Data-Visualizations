#!/usr/bin/env python3
"""
Debug multiprocessing issue with mock configuration
"""

import os
import sys

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_mock_config_propagation():
    """Test if mock configuration properly propagates to workers"""
    print("Testing mock configuration propagation...")
    
    from test_mock_components import (
        MockConfig, set_mock_config_for_workers, mock_worker_initializer,
        mock_render_frame_from_spec, WORKER_MOCK_CONFIG
    )
    
    # Test 1: Direct function call (same process)
    print("\n1. Testing direct function call:")
    mock_config = MockConfig(
        total_frames=5,
        error_type='transient',
        error_frame_numbers=[2]
    )
    
    set_mock_config_for_workers(mock_config)
    
    # Call the worker initializer directly
    mock_worker_initializer({'test': 'config'})
    
    # Test the mock renderer directly
    test_frame = {'frame_index': 2, 'display_timestamp': '2024-01-01T12:00:00Z', 'bars': []}
    result = mock_render_frame_from_spec(test_frame)
    print(f"  Frame 2 (should error): {result['status']} - {result.get('error_type', 'no error')}")
    
    normal_frame = {'frame_index': 1, 'display_timestamp': '2024-01-01T12:00:00Z', 'bars': []}
    result = mock_render_frame_from_spec(normal_frame)
    print(f"  Frame 1 (should succeed): {result['status']}")
    
    print(f"  Worker config after init: {WORKER_MOCK_CONFIG}")
    
    # Test 2: With multiprocessing
    print("\n2. Testing with multiprocessing:")
    import concurrent.futures
    
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=1,
        initializer=mock_worker_initializer,
        initargs=({'test': 'config'},)
    ) as executor:
        # Submit tasks
        future1 = executor.submit(mock_render_frame_from_spec, normal_frame)
        future2 = executor.submit(mock_render_frame_from_spec, test_frame)
        
        result1 = future1.result()
        result2 = future2.result()
        
        print(f"  Frame 1 (should succeed): {result1['status']}")
        print(f"  Frame 2 (should error): {result2['status']} - {result2.get('error_type', 'no error')}")

if __name__ == "__main__":
    test_mock_config_propagation()