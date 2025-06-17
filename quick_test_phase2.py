#!/usr/bin/env python3
"""
Quick Phase 2 Test - Non-Interactive

Quick validation test for the stateless renderer that can be run without user interaction.
Perfect for automated testing and CI/CD pipelines.
"""

import os
import sys
import time

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stateless_renderer import (
    RenderConfig, 
    create_render_config_from_app_config,
    initialize_render_worker, 
    render_frame_from_spec
)
from config_loader import AppConfig


def quick_test():
    """Run a quick test of the stateless renderer"""
    print("🧪 Quick Phase 2 Test - Stateless Renderer")
    print("=" * 50)
    
    # Set encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        # Test 1: Configuration loading
        print("1. Testing configuration loading...")
        if not os.path.exists('configurations.txt'):
            print("   ⚠️ configurations.txt not found, using minimal config")
            render_config = RenderConfig(
                dpi=96, fig_width_pixels=800, fig_height_pixels=600, target_fps=30,
                font_paths={}, preferred_fonts=['DejaVu Sans'],
                album_art_cache_dir='album_art_cache', album_art_visibility_threshold=0.0628,
                n_bars=5
            )
        else:
            config = AppConfig('configurations.txt')
            render_config = create_render_config_from_app_config(config)
        
        print(f"   ✓ Config loaded: {render_config.fig_width_pixels}x{render_config.fig_height_pixels}")
        
        # Test 2: Worker initialization
        print("2. Testing worker initialization...")
        initialize_render_worker(render_config.to_dict())
        print("   ✓ Worker initialized successfully")
        
        # Test 3: Single frame rendering
        print("3. Testing single frame rendering...")
        
        # Create minimal test frame spec
        frame_spec = {
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
                    'album_art_path': '',
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
            'rolling_stats': {'top_7_day': None, 'top_30_day': None},
            'nightingale_data': {},
            'dynamic_x_axis_limit': 110.0,
            'visualization_mode': 'tracks'
        }
        
        # Ensure output directory exists
        os.makedirs('frames', exist_ok=True)
        
        # Render the frame
        start_time = time.time()
        result = render_frame_from_spec(frame_spec)
        render_time = time.time() - start_time
        
        if result['status'] == 'success':
            output_path = result['output_path']
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"   ✓ Frame rendered: {output_path} ({file_size} bytes, {render_time:.3f}s)")
                
                # Verify it's a valid PNG
                with open(output_path, 'rb') as f:
                    header = f.read(8)
                    if header.startswith(b'\x89PNG\r\n\x1a\n'):
                        print("   ✓ Valid PNG format confirmed")
                    else:
                        print("   ✗ Invalid PNG format")
                        return False
            else:
                print(f"   ✗ Output file not created: {output_path}")
                return False
        else:
            print(f"   ✗ Rendering failed: {result.get('error', 'Unknown error')}")
            return False
        
        print("\n🎉 Quick test PASSED! Stateless renderer is working correctly.")
        print(f"Output saved to: {result['output_path']}")
        return True
        
    except Exception as e:
        print(f"\n💥 Quick test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)