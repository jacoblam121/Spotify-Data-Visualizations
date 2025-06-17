#!/usr/bin/env python3
"""
Test Suite for Stateless Renderer

This script tests the stateless frame rendering functionality to ensure
it works correctly before integrating with the parallel processing pipeline.
"""

import os
import sys
import json
import time
import tempfile
import shutil
from datetime import datetime, timezone

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stateless_renderer import (
    RenderConfig, 
    create_render_config_from_app_config,
    initialize_render_worker, 
    render_frame_from_spec,
    _validate_album_art_path
)
from config_loader import AppConfig


def test_render_config():
    """Test RenderConfig serialization and creation"""
    print("\n=== Testing RenderConfig ===")
    
    # Test basic config creation
    config = RenderConfig(
        dpi=96, fig_width_pixels=1920, fig_height_pixels=1080, target_fps=30,
        font_paths={}, preferred_fonts=['DejaVu Sans'],
        album_art_cache_dir='test_cache', album_art_visibility_threshold=0.0628,
        n_bars=10
    )
    
    # Test serialization
    config_dict = config.to_dict()
    print(f"✓ Config serialization: {len(config_dict)} fields")
    
    # Test deserialization
    config_restored = RenderConfig.from_dict(config_dict)
    assert config_restored.dpi == config.dpi
    assert config_restored.n_bars == config.n_bars
    print("✓ Config deserialization works")
    
    # Test DPI scaling
    scaled_font = config.get_scaled_fontsize(12.0)
    expected = 12.0 * (96 / 100.0)
    assert abs(scaled_font - expected) < 0.01
    print(f"✓ DPI scaling: 12.0 -> {scaled_font}")
    
    return config


def test_path_validation():
    """Test album art path validation security"""
    print("\n=== Testing Path Validation ===")
    
    # Create temporary test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = os.path.join(temp_dir, 'cache')
        os.makedirs(cache_dir)
        
        # Create test file
        test_file = os.path.join(cache_dir, 'test.jpg')
        with open(test_file, 'w') as f:
            f.write('test image data')
        
        # Test valid path
        valid_path = _validate_album_art_path('test.jpg', cache_dir)
        assert valid_path == test_file
        print("✓ Valid path accepted")
        
        # Test path traversal attempts
        invalid_paths = [
            '../../../etc/passwd',
            '/etc/passwd',
            '..\\..\\windows\\system32\\config\\sam',
            'subdir/../../../sensitive.txt'
        ]
        
        blocked_count = 0
        for invalid_path in invalid_paths:
            result = _validate_album_art_path(invalid_path, cache_dir)
            if result is None:
                blocked_count += 1
            else:
                print(f"✗ Path traversal not blocked: {invalid_path} -> {result}")
                return False
            
        print(f"✓ {blocked_count}/{len(invalid_paths)} path traversal attempts blocked")
        return True


def test_worker_initialization():
    """Test worker initialization in a subprocess"""
    print("\n=== Testing Worker Initialization ===")
    
    # Create test config
    config = RenderConfig(
        dpi=96, fig_width_pixels=800, fig_height_pixels=600, target_fps=30,
        font_paths={}, preferred_fonts=['DejaVu Sans'],
        album_art_cache_dir='album_art_cache', album_art_visibility_threshold=0.0628,
        n_bars=5
    )
    
    try:
        # Test initialization
        initialize_render_worker(config.to_dict())
        print("✓ Worker initialization successful")
        
        # Verify global state is set
        from stateless_renderer import WORKER_RENDER_CONFIG
        assert WORKER_RENDER_CONFIG is not None
        assert WORKER_RENDER_CONFIG.dpi == 96
        print("✓ Worker config loaded correctly")
        
    except Exception as e:
        print(f"✗ Worker initialization failed: {e}")
        return False
    
    return True


def create_test_frame_spec():
    """Create a minimal test frame specification"""
    return {
        'frame_index': 0,
        'display_timestamp': '2024-01-01T12:00:00Z',
        'bars': [
            {
                'entity_id': 'test_song_1',
                'canonical_key': 'test_song_1',
                'display_name': 'Test Song - Test Artist',
                'interpolated_y_pos': 0.0,
                'interpolated_play_count': 100.0,
                'bar_color_rgba': (0.6, 0.3, 0.8, 1.0),
                'album_art_path': '',  # No album art for this test
                'entity_details': {
                    'original_artist': 'Test Artist',
                    'original_track': 'Test Song'
                }
            },
            {
                'entity_id': 'test_song_2',
                'canonical_key': 'test_song_2', 
                'display_name': 'Another Song - Another Artist',
                'interpolated_y_pos': 1.0,
                'interpolated_play_count': 75.0,
                'bar_color_rgba': (0.3, 0.6, 0.4, 1.0),
                'album_art_path': '',
                'entity_details': {
                    'original_artist': 'Another Artist',
                    'original_track': 'Another Song'
                }
            }
        ],
        'rolling_stats': {
            'top_7_day': None,
            'top_30_day': None
        },
        'nightingale_data': {},
        'dynamic_x_axis_limit': 110.0,
        'visualization_mode': 'tracks'
    }


def test_single_frame_rendering():
    """Test rendering a single frame"""
    print("\n=== Testing Single Frame Rendering ===")
    
    # Ensure worker is initialized
    if not test_worker_initialization():
        return False
    
    # Create test frame spec
    frame_spec = create_test_frame_spec()
    
    # Ensure output directory exists
    os.makedirs('frames', exist_ok=True)
    
    try:
        # Render the frame
        start_time = time.time()
        result = render_frame_from_spec(frame_spec)
        render_time = time.time() - start_time
        
        print(f"Render result: {result['status']}")
        print(f"Render time: {render_time:.3f}s")
        
        if result['status'] == 'success':
            output_path = result['output_path']
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"✓ Frame rendered successfully: {output_path} ({file_size} bytes)")
                
                # Basic validation that it's a PNG file
                with open(output_path, 'rb') as f:
                    header = f.read(8)
                    if header.startswith(b'\x89PNG\r\n\x1a\n'):
                        print("✓ Output is valid PNG format")
                    else:
                        print("✗ Output is not valid PNG format")
                        return False
                        
                return True
            else:
                print(f"✗ Output file not created: {output_path}")
                return False
        else:
            print(f"✗ Rendering failed: {result.get('error', 'Unknown error')}")
            print(f"Error type: {result.get('error_type', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"✗ Exception during rendering: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling with invalid frame specs"""
    print("\n=== Testing Error Handling ===")
    
    if not test_worker_initialization():
        return False
    
    # Test with invalid frame spec that should cause a specific error
    invalid_spec = {
        'frame_index': 999,
        'display_timestamp': 'invalid-date-format-should-cause-error',
        'bars': [
            {
                'entity_id': 'test',
                'interpolated_play_count': 'not_a_number',  # This should cause an error
                'interpolated_y_position': 0
            }
        ],
        'dynamic_x_axis_limit': 100,
        'visualization_mode': 'tracks'
    }
    
    result = render_frame_from_spec(invalid_spec)
    
    if result['status'] == 'error':
        print(f"✓ Error handling works: {result['error_type']}")
        print(f"  Error message: {result['error']}")
        return True
    else:
        print("✗ Expected error but rendering succeeded")
        print(f"  Result: {result}")
        return False


def test_config_from_app_config():
    """Test creating RenderConfig from AppConfig"""
    print("\n=== Testing Config Creation from AppConfig ===")
    
    # Check if configurations.txt exists
    if not os.path.exists('configurations.txt'):
        print("⚠ configurations.txt not found, skipping AppConfig test")
        return True
    
    try:
        app_config = AppConfig('configurations.txt')
        render_config = create_render_config_from_app_config(app_config)
        
        print(f"✓ RenderConfig created from AppConfig")
        print(f"  Resolution: {render_config.fig_width_pixels}x{render_config.fig_height_pixels}")
        print(f"  DPI: {render_config.dpi}")
        print(f"  N_bars: {render_config.n_bars}")
        print(f"  Fonts: {len(render_config.font_paths)} font files")
        
        return True
        
    except Exception as e:
        print(f"✗ AppConfig conversion failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Stateless Renderer Test Suite")
    print("=" * 50)
    
    tests = [
        ("RenderConfig", test_render_config),
        ("Path Validation", test_path_validation),
        ("Worker Initialization", test_worker_initialization),
        ("Single Frame Rendering", test_single_frame_rendering),
        ("Error Handling", test_error_handling),
        ("Config from AppConfig", test_config_from_app_config),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"💥 {test_name} CRASHED: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Stateless renderer is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix issues before proceeding.")
        return 1


if __name__ == "__main__":
    # Set encoding for international characters
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    sys.exit(main())