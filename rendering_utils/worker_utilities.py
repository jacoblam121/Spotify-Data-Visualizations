#!/usr/bin/env python3
"""
Worker helper functions for multiprocessing-safe test execution.

This module provides utilities for setting up test mocks and patches 
in worker processes while respecting pickling constraints.
"""

import os
import sys
import time
from typing import List, Tuple, Any, Dict, Optional, Callable
from unittest.mock import patch, MagicMock

# Global storage for active patches to prevent garbage collection
__active_patches = []


def generic_worker_patcher(patches_to_apply: List[Tuple[str, Any]]) -> None:
    """
    Applies patches to modules or objects within a worker process.
    
    This function is designed to be pickled and sent to a worker process
    as part of its initializer. It circumvents the issue of not being able
    to pickle patch objects or mock objects directly. Instead, it takes a
    list of string-based targets and the values to patch them with,
    performing the patch operation within the worker's memory space.
    
    Why this pattern is necessary:
    - Mock objects and patches cannot be pickled for multiprocessing
    - Worker processes have separate memory spaces
    - Patches must be applied within each worker process individually
    - This function recreates mocks/patches from picklable specifications
    
    Args:
        patches_to_apply: List of tuples where each tuple contains:
            - target (str): The target to patch (e.g., 'module.submodule.function')
            - new_spec (Any): The value/specification to patch it with:
                * Simple value (int, str, etc.) for direct replacement
                * Tuple ('MagicMock', kwargs_dict) for creating MagicMock
                * Tuple ('function', callable) for function replacement
    
    Note:
        This function must be defined at module level to be picklable.
        Patches remain active for the lifetime of the worker process.
    """
    global __active_patches
    __active_patches = []
    
    for target, new_spec in patches_to_apply:
        # Handle different types of mock specifications
        if isinstance(new_spec, tuple):
            if new_spec[0] == 'MagicMock':
                # Create MagicMock with provided kwargs
                _, mock_kwargs = new_spec
                new_obj = MagicMock(**mock_kwargs)
            elif new_spec[0] == 'function':
                # Use provided function
                _, new_obj = new_spec
            else:
                # Treat as simple value
                new_obj = new_spec
        else:
            # Simple value replacement
            new_obj = new_spec
        
        # Apply the patch
        patcher = patch(target, new=new_obj)
        patcher.start()
        __active_patches.append(patcher)
    
    # Note: We don't call patcher.stop(). The patch lasts for the
    # lifetime of the worker process, which is what we want for testing.


def create_error_injection_patcher(error_config: Dict[str, Any]) -> List[Tuple[str, Any]]:
    """
    Create patch specifications for error injection testing.
    
    Args:
        error_config: Dictionary containing error configuration:
                     - error_type: 'transient', 'worker_fatal', 'frame_fatal'
                     - error_frames: List of frame indices to inject errors
                     - memory_leak_mb: Memory leak simulation amount
                     - render_delay_ms: Render delay simulation
    
    Returns:
        List of patch specifications for generic_worker_patcher
    """
    patches = []
    
    # Example: Mock memory monitoring
    if error_config.get('memory_leak_mb', 0) > 0:
        fake_memory_mb = error_config['memory_leak_mb'] * 1024 * 1024  # Convert to bytes
        patches.append((
            'psutil.Process.memory_info',
            ('MagicMock', {'return_value.rss': fake_memory_mb})
        ))
    
    # Example: Mock time functions for delay simulation
    if error_config.get('render_delay_ms', 0) > 0:
        # This would require more sophisticated time mocking
        # For now, we can mock the delay function itself
        pass
    
    return patches


def safe_worker_initializer_with_config(render_config_dict: Dict[str, Any]) -> None:
    """
    Safe worker initializer that preserves all visual settings.
    This is the production initializer wrapped for testing.
    """
    try:
        from stateless_renderer import initialize_render_worker
        initialize_render_worker(render_config_dict)
    except ImportError:
        # Graceful fallback for testing environments
        pass


def create_test_worker_initializer(render_config_dict: Dict[str, Any], 
                                  patches_to_apply: List[Tuple[str, Any]]) -> None:
    """
    Combined initializer that sets up both production config and test patches.
    
    This function must be defined at module level to be picklable.
    
    Args:
        render_config_dict: Production render configuration
        patches_to_apply: Test patches to apply
    """
    # First, initialize the production worker
    safe_worker_initializer_with_config(render_config_dict)
    
    # Then apply test patches
    generic_worker_patcher(patches_to_apply)


# Convenience function factories for common test scenarios
def create_transient_error_worker_init(render_config_dict: Dict[str, Any], 
                                      error_frames: List[int]) -> Tuple[Any, Tuple]:
    """
    Create worker initializer for transient error testing.
    
    Returns:
        Tuple of (initializer_function, initargs) ready for ProcessPoolExecutor
    """
    patches = [
        # Example: Mock the render function to inject errors on specific frames
        ('stateless_renderer.render_frame_from_spec', 
         ('function', lambda spec: _inject_transient_error(spec, error_frames)))
    ]
    
    # Return function reference and arguments tuple
    import functools
    bound_init = functools.partial(create_test_worker_initializer, 
                                  render_config_dict, patches)
    return bound_init, ()


def create_memory_leak_worker_init(render_config_dict: Dict[str, Any], 
                                  leak_mb_per_frame: float) -> Tuple[Any, Tuple]:
    """
    Create worker initializer for memory leak testing.
    
    Returns:
        Tuple of (initializer_function, initargs) ready for ProcessPoolExecutor
    """
    patches = create_error_injection_patcher({
        'memory_leak_mb': leak_mb_per_frame
    })
    
    import functools
    bound_init = functools.partial(create_test_worker_initializer, 
                                  render_config_dict, patches)
    return bound_init, ()


def top_level_test_render_function(frame_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified render function with comprehensive exception capturing for debugging.
    
    Uses worker-global state set during initialization to determine behavior,
    eliminating runtime imports and race conditions.
    
    Args:
        frame_spec: Frame specification dictionary
        
    Returns:
        Render result dictionary with full error details
    """
    global _worker_test_config, _worker_is_test_mode
    
    frame_index = frame_spec.get('frame_index', 0)
    worker_pid = os.getpid()
    start_time = time.time()
    
    try:
        # Debug logging for state inspection
        print(f"[Worker PID: {worker_pid}] Processing frame {frame_index}, test_mode: {_worker_is_test_mode}")
        
        # Check worker state health
        try:
            from stateless_renderer import WORKER_RENDER_CONFIG
            if WORKER_RENDER_CONFIG is None:
                raise RuntimeError(f"Worker {worker_pid}: WORKER_RENDER_CONFIG is None - initialization failed")
            print(f"[Worker PID: {worker_pid}] WORKER_RENDER_CONFIG available: dpi={WORKER_RENDER_CONFIG.dpi}")
        except ImportError as ie:
            raise ImportError(f"Worker {worker_pid}: Cannot import stateless_renderer: {ie}")
        
        # Log font state for debugging double initialization issue
        try:
            import matplotlib.font_manager as fm
            font_count = len(fm.fontManager.ttflist)
            available_fonts = [f.name for f in fm.fontManager.ttflist[:3]]  # First 3 fonts
            print(f"[Worker PID: {worker_pid}] Font state: {font_count} total fonts, first 3: {available_fonts}")
        except Exception as font_error:
            print(f"[Worker PID: {worker_pid}] Font check failed: {font_error}")
        
        # If not in test mode, use production rendering
        if not _worker_is_test_mode:
            print(f"[Worker PID: {worker_pid}] Using production rendering path")
            from stateless_renderer import render_frame_from_spec
            result = render_frame_from_spec(frame_spec)
            print(f"[Worker PID: {worker_pid}] Frame {frame_index} completed successfully via production path")
            return result
        
        # Test mode: use worker-global test config instead of frame_spec
        print(f"[Worker PID: {worker_pid}] Using test mode rendering path")
        test_config_dict = _worker_test_config or {}
        
        # Memory leak simulation (safe - no real allocation)
        memory_leak_mb = test_config_dict.get('memory_leak_mb_per_frame', 0.0)
        if memory_leak_mb > 0:
            # Mock the memory monitoring instead of actually allocating
            pass
        
        # Render delay simulation
        render_delay_ms = test_config_dict.get('render_delay_override_ms')
        if render_delay_ms is not None:
            time.sleep(min(render_delay_ms / 1000.0, 0.1))
        
        # Error injection logic - use worker config, not frame config
        error_type = test_config_dict.get('error_type')
        error_frame_numbers = test_config_dict.get('error_frame_numbers', [])
        
        if error_type and frame_index in error_frame_numbers:
            error_msg = f"Test-injected {error_type} error on frame {frame_index}"
            render_time = time.time() - start_time
            print(f"[Worker PID: {worker_pid}] Injecting test error for frame {frame_index}")
            return {
                'status': 'error',
                'error_type': error_type,
                'frame_index': frame_index,
                'error': error_msg,
                'render_time_seconds': render_time,
                'worker_pid': worker_pid
            }
        
        # Normal processing - call the real render function
        from stateless_renderer import render_frame_from_spec
        result = render_frame_from_spec(frame_spec)
        print(f"[Worker PID: {worker_pid}] Frame {frame_index} completed successfully via test path")
        return result
        
    except Exception as e:
        # CRITICAL: Capture full exception details for debugging
        import traceback
        render_time = time.time() - start_time
        error_details = {
            'status': 'error',
            'error_type': 'worker_exception',
            'frame_index': frame_index,
            'error': str(e),
            'exception_type': type(e).__name__,
            'traceback': traceback.format_exc(),
            'render_time_seconds': render_time,
            'worker_pid': worker_pid,
            'worker_test_mode': _worker_is_test_mode,
            'worker_config_available': _worker_test_config is not None
        }
        
        # Print detailed error for immediate visibility
        print(f"[Worker PID: {worker_pid}] ❌ FRAME {frame_index} FAILED:")
        print(f"  Exception: {type(e).__name__}: {e}")
        print(f"  Worker state: test_mode={_worker_is_test_mode}, config_available={_worker_test_config is not None}")
        print(f"  Traceback:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                print(f"    {line}")
        
        return error_details


# Global worker state - set once during initialization
_worker_test_config = None
_worker_is_test_mode = False

def top_level_test_worker_initializer(render_config_dict: Dict[str, Any], 
                                     test_config_dict: Dict[str, Any]) -> None:
    """
    A picklable, top-level worker initializer function for dependency injection.
    
    This function is designed to be passed to ProcessPoolExecutor.initializer
    and can be properly pickled for multiprocessing.
    
    Args:
        render_config_dict: Production render configuration
        test_config_dict: Test configuration as a dictionary (picklable)
    """
    global _worker_test_config, _worker_is_test_mode
    
    try:
        # First, initialize the production worker
        safe_worker_initializer_with_config(render_config_dict)
        
        # Store test configuration globally in worker
        _worker_test_config = test_config_dict
        _worker_is_test_mode = bool(test_config_dict.get('error_type') or 
                                   test_config_dict.get('memory_leak_mb_per_frame', 0) > 0 or
                                   test_config_dict.get('render_delay_override_ms'))
        
        print(f"[Worker PID: {os.getpid()}] Initialized successfully. Test mode: {_worker_is_test_mode}")
        
        # Create patches based on test configuration
        patches_to_apply = []
        
        # Memory monitoring patches
        memory_leak_mb = test_config_dict.get('memory_leak_mb_per_frame', 0.0)
        if memory_leak_mb > 0:
            fake_memory_bytes = int(memory_leak_mb * 1024 * 1024)
            patches_to_apply.append((
                'psutil.Process.memory_info',
                ('MagicMock', {'return_value.rss': fake_memory_bytes})
            ))
        
        # Apply patches if any
        if patches_to_apply:
            generic_worker_patcher(patches_to_apply)
            
    except Exception as e:
        print(f"[Worker PID: {os.getpid()}] FAILED to initialize: {e}")
        raise


def _inject_transient_error(frame_spec: Dict[str, Any], error_frames: List[int]) -> Dict[str, Any]:
    """
    Helper function to inject transient errors in specific frames.
    This function will be used by the worker process.
    """
    frame_index = frame_spec.get('frame_index', 0)
    
    if frame_index in error_frames:
        return {
            'status': 'error',
            'error_type': 'transient',
            'frame_index': frame_index,
            'error': f'Test-injected transient error on frame {frame_index}',
            'render_time_seconds': 0.1,
            'worker_pid': os.getpid()
        }
    
    # Call the real render function for non-error frames
    try:
        from stateless_renderer import render_frame_from_spec
        return render_frame_from_spec(frame_spec)
    except ImportError:
        # Graceful fallback for testing environments
        return {
            'status': 'success',
            'frame_index': frame_index,
            'output_path': f'mock_frames/frame_{frame_index:06d}.png',
            'render_time_seconds': 0.05,
            'worker_pid': os.getpid()
        }