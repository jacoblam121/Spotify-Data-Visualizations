#!/usr/bin/env python3
"""
Basic validation test for Task 3 parallel render manager.
Tests import, configuration, and basic functionality.
"""

import os
import sys

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports...")
    
    try:
        from parallel_render_manager import (
            ParallelRenderManager,
            RenderingConfig, 
            TaskContext,
            FrameResult,
            FrameStatus,
            ProgressInfo,
            parallel_render_frames
        )
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration objects"""
    print("\nTesting configuration...")
    
    try:
        from parallel_render_manager import RenderingConfig
        
        # Test default configuration
        config = RenderingConfig()
        print(f"✓ Default config: {config.max_workers} workers, {config.maxtasksperchild} max tasks")
        
        # Test custom configuration
        custom_config = RenderingConfig(
            max_workers=2,
            max_retries_transient=1,
            maxtasksperchild=500
        )
        print(f"✓ Custom config: {custom_config.max_workers} workers, {custom_config.maxtasksperchild} max tasks")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_task_context():
    """Test TaskContext class"""
    print("\nTesting TaskContext...")
    
    try:
        from parallel_render_manager import TaskContext
        
        # Create test frame spec
        frame_spec = {
            'frame_index': 42,
            'display_timestamp': '2024-01-01T12:00:00Z',
            'bars': []
        }
        
        # Create TaskContext
        context = TaskContext(frame_spec=frame_spec, retry_count=1)
        
        print(f"✓ TaskContext created: frame {context.frame_index}, {context.retry_count} retries")
        
        # Test property
        assert context.frame_index == 42
        print("✓ frame_index property works")
        
        return True
    except Exception as e:
        print(f"✗ TaskContext test failed: {e}")
        return False

def test_manager_creation():
    """Test ParallelRenderManager creation"""
    print("\nTesting ParallelRenderManager creation...")
    
    try:
        from parallel_render_manager import ParallelRenderManager, RenderingConfig
        from stateless_renderer import RenderConfig
        
        # Create minimal render config
        render_config = RenderConfig(
            dpi=96,
            fig_width_pixels=1920,
            fig_height_pixels=1080,
            target_fps=30,
            font_paths={},
            preferred_fonts=['DejaVu Sans'],
            album_art_cache_dir='album_art_cache',
            album_art_visibility_threshold=0.0628,
            n_bars=10
        )
        
        # Create rendering config
        rendering_config = RenderingConfig(max_workers=2)
        
        # Create manager
        manager = ParallelRenderManager(render_config, rendering_config)
        print("✓ ParallelRenderManager created successfully")
        
        return True
    except Exception as e:
        print(f"✗ Manager creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all basic tests"""
    print("=" * 50)
    print("Task 3 Basic Validation Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_task_context,
        test_manager_creation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Test Results:")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)