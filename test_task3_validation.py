#!/usr/bin/env python3
"""
Non-interactive validation for Task 3 comprehensive test suite.
Tests the core functionality without requiring user input.
"""

import os
import sys

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_comprehensive_suite_imports():
    """Test that comprehensive test suite imports work"""
    print("Testing comprehensive test suite imports...")
    
    try:
        from test_task3_comprehensive import Task3ComprehensiveTester
        print("✓ Task3ComprehensiveTester imported successfully")
        
        from test_mock_components import (
            MockFrameSpecGenerator,
            MockConfig,
            TestDataFactory,
            mock_render_frame_from_spec
        )
        print("✓ Mock components imported successfully")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_mock_components():
    """Test mock components functionality"""
    print("\nTesting mock components...")
    
    try:
        from test_mock_components import MockFrameSpecGenerator, MockConfig, TestDataFactory
        
        # Test mock config presets
        config = TestDataFactory.create_mock_config_preset("basic")
        print(f"✓ Mock config preset: {config.total_frames} frames")
        
        # Test mock generator
        generator = MockFrameSpecGenerator(config)
        frame_count = 0
        for frame_spec in generator:
            frame_count += 1
            if frame_count >= 3:  # Just test first few frames
                break
        
        print(f"✓ Mock generator produced {frame_count} frames")
        
        # Test mock renderer
        from test_mock_components import mock_render_frame_from_spec, set_global_mock_config
        
        test_config = MockConfig(render_delay_ms=1.0)
        set_global_mock_config(test_config)
        
        test_frame = {
            'frame_index': 1,
            'display_timestamp': '2024-01-01T12:00:00Z',
            'bars': []
        }
        
        result = mock_render_frame_from_spec(test_frame)
        print(f"✓ Mock renderer returned: {result['status']}")
        
        return True
    except Exception as e:
        print(f"✗ Mock components test failed: {e}")
        return False

def test_basic_parallel_rendering():
    """Test basic parallel rendering functionality"""
    print("\nTesting basic parallel rendering...")
    
    try:
        from parallel_render_manager import ParallelRenderManager, RenderingConfig
        from test_mock_components import (
            MockFrameSpecGenerator, MockConfig, TestDataFactory,
            mock_render_frame_from_spec, mock_initialize_render_worker,
            set_global_mock_config
        )
        
        # Setup mock configuration
        mock_config = MockConfig(total_frames=5, render_delay_ms=10.0)
        set_global_mock_config(mock_config)
        
        # Create components
        generator = MockFrameSpecGenerator(mock_config)
        render_config = TestDataFactory.create_test_render_config()
        rendering_config = RenderingConfig(max_workers=2)
        manager = ParallelRenderManager(render_config, rendering_config)
        
        # Override with mock functions
        import parallel_render_manager
            import stateless_renderer
        original_initialize = parallel_render_manager.initialize_render_worker
        original_render = parallel_render_manager.render_frame_from_spec
            original_stateless_render = stateless_renderer.render_frame_from_spec
        
        parallel_render_manager.initialize_render_worker = mock_initialize_render_worker
        parallel_render_manager.render_frame_from_spec = mock_render_frame_from_spec
            stateless_renderer.render_frame_from_spec = mock_render_frame_from_spec
        
        # Run rendering
        print("Running parallel rendering with 5 frames...")
        results = manager.render_frames(generator)
        
        # Restore original functions
        parallel_render_manager.initialize_render_worker = original_initialize
        parallel_render_manager.render_frame_from_spec = original_render
            stateless_renderer.render_frame_from_spec = original_stateless_render
        
        # Check results
        completed = results['stats'].completed_frames
        failed = results['stats'].failed_frames
        
        print(f"✓ Completed: {completed}, Failed: {failed}")
        
        success = completed == 5 and failed == 0
        print(f"✓ Basic parallel rendering: {'PASSED' if success else 'FAILED'}")
        
        return success
    except Exception as e:
        print(f"✗ Basic parallel rendering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_injection():
    """Test error injection functionality"""
    print("\nTesting error injection...")
    
    try:
        from test_mock_components import MockConfig, mock_render_frame_from_spec, set_global_mock_config
        
        # Test transient error injection
        error_config = MockConfig(
            total_frames=10,
            render_delay_ms=5.0,
            error_type='transient',
            error_frame_numbers=[3]
        )
        set_global_mock_config(error_config)
        
        # Test frame that should cause error
        error_frame = {
            'frame_index': 3,
            'display_timestamp': '2024-01-01T12:00:00Z',
            'bars': []
        }
        
        result = mock_render_frame_from_spec(error_frame)
        print(f"✓ Error injection result: {result['status']} ({result.get('error_type', 'none')})")
        
        # Test normal frame
        normal_frame = {
            'frame_index': 1,
            'display_timestamp': '2024-01-01T12:00:00Z',
            'bars': []
        }
        
        result = mock_render_frame_from_spec(normal_frame)
        print(f"✓ Normal frame result: {result['status']}")
        
        return True
    except Exception as e:
        print(f"✗ Error injection test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("=" * 60)
    print("Task 3 Comprehensive Test Suite Validation")
    print("=" * 60)
    
    tests = [
        test_comprehensive_suite_imports,
        test_mock_components,
        test_basic_parallel_rendering,
        test_error_injection
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Validation Results:")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All validation tests passed!")
        print("\n📋 Interactive Test Suite Ready:")
        print("   Run: python test_task3_comprehensive.py")
        print("   Features:")
        print("   - 20+ test scenarios")
        print("   - Interactive menu interface")
        print("   - Error injection capabilities")
        print("   - Memory monitoring (with psutil)")
        print("   - Signal handling tests")
        print("   - Performance benchmarking")
        return True
    else:
        print("❌ Some validation tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)