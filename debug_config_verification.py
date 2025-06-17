#!/usr/bin/env python3
"""
Verify mock configuration is being set correctly
"""

import os
import sys

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_verification():
    """Verify mock configuration"""
    print("Testing mock configuration...")
    
    from test_mock_components import (
        MockConfig, set_mock_config_for_workers, mock_worker_initializer,
        mock_render_frame_from_spec, WORKER_MOCK_CONFIG
    )
    
    # Setup mock configuration with transient errors
    mock_config = MockConfig(
        total_frames=3,
        render_delay_ms=1.0,
        error_type='transient',
        error_frame_numbers=[1]  # Error on frame 1
    )
    
    print(f"Original config: {mock_config}")
    
    # Set config for workers
    set_mock_config_for_workers(mock_config)
    
    print(f"WORKER_MOCK_CONFIG before init: {WORKER_MOCK_CONFIG}")
    
    # Initialize worker
    mock_worker_initializer({'test': 'config'})
    
    print(f"WORKER_MOCK_CONFIG after init: {WORKER_MOCK_CONFIG}")
    
    # Test frame
    test_frame = {'frame_index': 1, 'display_timestamp': '2024-01-01T12:00:00Z', 'bars': []}
    result = mock_render_frame_from_spec(test_frame)
    print(f"Frame 1 result: {result['status']} - {result.get('error_type', 'none')}")

if __name__ == "__main__":
    test_config_verification()