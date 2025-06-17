#!/usr/bin/env python3
"""
Direct test of multiprocessing worker configuration
"""

import os
import sys
import concurrent.futures

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_worker_function(frame_spec):
    """Test function that checks worker state"""
    import os
    from test_mock_components import WORKER_MOCK_CONFIG, mock_render_frame_from_spec
    
    pid = os.getpid()
    frame_index = frame_spec['frame_index']
    
    # Check worker config state
    print(f"Worker PID {pid}: Processing frame {frame_index}")
    print(f"Worker PID {pid}: WORKER_MOCK_CONFIG = {WORKER_MOCK_CONFIG}")
    
    if WORKER_MOCK_CONFIG:
        print(f"Worker PID {pid}: error_frame_numbers = {WORKER_MOCK_CONFIG.error_frame_numbers}")
        print(f"Worker PID {pid}: error_type = {WORKER_MOCK_CONFIG.error_type}")
    
    # Test the mock render function
    result = mock_render_frame_from_spec(frame_spec)
    print(f"Worker PID {pid}: Result = {result['status']} - {result.get('error_type', 'none')}")
    
    return {
        'frame_index': frame_index,
        'worker_pid': pid,
        'config_present': WORKER_MOCK_CONFIG is not None,
        'result_status': result['status'],
        'result_error_type': result.get('error_type')
    }

def test_direct_multiprocessing():
    """Test multiprocessing worker configuration directly"""
    print("Testing direct multiprocessing worker configuration...")
    
    from test_mock_components import (
        MockConfig, set_mock_config_for_workers, mock_worker_initializer
    )
    
    # Setup mock configuration with transient errors
    mock_config = MockConfig(
        total_frames=5,
        render_delay_ms=1.0,
        error_type='transient',
        error_frame_numbers=[2]  # Error on frame 2
    )
    
    print(f"Main process config: {mock_config}")
    set_mock_config_for_workers(mock_config)
    
    # Test with ProcessPoolExecutor
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=1,
        initializer=mock_worker_initializer,
        initargs=({'test': 'config'},)
    ) as executor:
        
        print("\nSubmitting tasks to worker...")
        
        # Test frames including the error frame
        test_frames = [
            {'frame_index': 1, 'display_timestamp': '2024-01-01T12:00:00Z', 'bars': []},
            {'frame_index': 2, 'display_timestamp': '2024-01-01T12:00:00Z', 'bars': []},  # Should error
            {'frame_index': 3, 'display_timestamp': '2024-01-01T12:00:00Z', 'bars': []}
        ]
        
        futures = []
        for frame in test_frames:
            future = executor.submit(test_worker_function, frame)
            futures.append(future)
        
        print("\nWaiting for results...")
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                print(f"\nResult summary:")
                print(f"  Frame: {result['frame_index']}")
                print(f"  Worker PID: {result['worker_pid']}")
                print(f"  Config present: {result['config_present']}")
                print(f"  Status: {result['result_status']}")
                print(f"  Error type: {result['result_error_type']}")
            except Exception as e:
                print(f"  Exception: {e}")

if __name__ == "__main__":
    test_direct_multiprocessing()