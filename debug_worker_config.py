#!/usr/bin/env python3
"""
Debug worker configuration propagation
"""

import os
import sys
import concurrent.futures

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_worker_config():
    """Test if worker config is properly set"""
    
    from test_mock_components import (
        MockConfig, set_mock_config_for_workers, mock_worker_initializer,
        mock_render_frame_from_spec, WORKER_MOCK_CONFIG
    )
    
    # Setup mock configuration with transient errors
    mock_config = MockConfig(
        total_frames=5,
        render_delay_ms=10.0,
        error_type='transient',
        error_frame_numbers=[2]  # Error on frame 2
    )
    
    print(f"Main process config: {mock_config}")
    set_mock_config_for_workers(mock_config)
    
    # Test 1: Direct call in main process
    print("\n1. Direct call in main process:")
    test_frame = {'frame_index': 2, 'display_timestamp': '2024-01-01T12:00:00Z', 'bars': []}
    
    # Initialize worker in main process 
    mock_worker_initializer({'test': 'config'})
    print(f"  Worker config after init: {WORKER_MOCK_CONFIG}")
    
    result = mock_render_frame_from_spec(test_frame)
    print(f"  Frame 2 result: {result['status']} - {result.get('error_type', 'none')}")
    
    # Test 2: Worker subprocess  
    print("\n2. Worker subprocess test:")
    
    # Create a test function that checks worker config
    def debug_worker_function(frame_spec):
        import os
        from test_mock_components import WORKER_MOCK_CONFIG, mock_render_frame_from_spec
        
        pid = os.getpid()
        print(f"  Worker PID {pid}: WORKER_MOCK_CONFIG = {WORKER_MOCK_CONFIG}")
        
        if WORKER_MOCK_CONFIG:
            print(f"  Worker PID {pid}: error_frame_numbers = {WORKER_MOCK_CONFIG.error_frame_numbers}")
            print(f"  Worker PID {pid}: error_type = {WORKER_MOCK_CONFIG.error_type}")
        
        result = mock_render_frame_from_spec(frame_spec)
        print(f"  Worker PID {pid}: Frame {frame_spec['frame_index']} result = {result['status']} - {result.get('error_type', 'none')}")
        return result
    
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=1,
        initializer=mock_worker_initializer,
        initargs=({'test': 'config'},)
    ) as executor:
        
        # Test multiple frames including the error frame
        frames = [
            {'frame_index': 1, 'display_timestamp': '2024-01-01T12:00:00Z', 'bars': []},
            {'frame_index': 2, 'display_timestamp': '2024-01-01T12:00:00Z', 'bars': []},  # Should error
            {'frame_index': 3, 'display_timestamp': '2024-01-01T12:00:00Z', 'bars': []}
        ]
        
        for frame in frames:
            future = executor.submit(debug_worker_function, frame)
            result = future.result()

if __name__ == "__main__":
    test_worker_config()