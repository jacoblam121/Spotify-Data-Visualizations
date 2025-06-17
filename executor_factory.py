#!/usr/bin/env python3
"""
ProcessPoolExecutor Factory for Rendering Tasks

Centralizes the creation of properly initialized ProcessPoolExecutor instances
for rendering tasks. This prevents common initialization errors and ensures
consistency across the codebase.

Usage:
    from executor_factory import create_rendering_executor
    
    render_config = RenderConfig(...)
    with create_rendering_executor(render_config, max_workers=8) as executor:
        # Submit rendering tasks...
        future = executor.submit(render_function, frame_spec)
"""

import os
import sys
from concurrent.futures import ProcessPoolExecutor
from typing import Optional, Dict, Any

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_worker_helpers import top_level_test_worker_initializer
from stateless_renderer import RenderConfig


def create_rendering_executor(
    render_config: RenderConfig,
    max_workers: Optional[int] = None,
    test_config: Optional[Dict[str, Any]] = None
) -> ProcessPoolExecutor:
    """
    Creates and returns a ProcessPoolExecutor correctly initialized for rendering tasks.
    
    This factory function encapsulates the proper initialization pattern to prevent
    common mistakes like forgetting the initializer function.
    
    Args:
        render_config: The render configuration object containing settings for rendering
        max_workers: Maximum number of worker processes. If None, uses default logic
        test_config: Optional test configuration for mock/test scenarios
        
    Returns:
        ProcessPoolExecutor: Properly initialized executor ready for rendering tasks
        
    Raises:
        ValueError: If render_config is None or invalid
        TypeError: If render_config doesn't have required attributes
        
    Example:
        render_config = RenderConfig(dpi=96, fig_width_pixels=1920, ...)
        
        with create_rendering_executor(render_config, max_workers=8) as executor:
            futures = [executor.submit(render_frame, spec) for spec in frame_specs]
            results = [future.result() for future in futures]
    """
    
    # Validation
    if render_config is None:
        raise ValueError("A valid render_config must be provided")
    
    if not hasattr(render_config, 'to_dict'):
        raise TypeError(f"render_config must have 'to_dict' method, got {type(render_config)}")
    
    # Use empty dict for test config if none provided
    if test_config is None:
        test_config = {}
    
    # Create the executor with proper initialization
    return ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=top_level_test_worker_initializer,
        initargs=(render_config.to_dict(), test_config)
    )


def create_test_rendering_executor(
    render_config: RenderConfig,
    test_config: Dict[str, Any],
    max_workers: Optional[int] = None
) -> ProcessPoolExecutor:
    """
    Convenience function for creating test rendering executors with specific test config.
    
    Args:
        render_config: The render configuration object
        test_config: Test-specific configuration (e.g., MockConfig parameters)
        max_workers: Maximum number of worker processes
        
    Returns:
        ProcessPoolExecutor: Properly initialized test executor
    """
    return create_rendering_executor(
        render_config=render_config,
        max_workers=max_workers,
        test_config=test_config
    )


# Backwards compatibility - create aliases for existing patterns
create_parallel_executor = create_rendering_executor  # Alias for consistency

if __name__ == "__main__":
    # Test the factory function
    print("Testing ProcessPoolExecutor factory...")
    
    # Create a test render config
    test_config = RenderConfig(
        dpi=96,
        fig_width_pixels=1920,
        fig_height_pixels=1080,
        target_fps=30,
        font_paths={},
        preferred_fonts=["DejaVu Sans"],
        album_art_cache_dir="test_cache",
        album_art_visibility_threshold=0.0628,
        n_bars=10
    )
    
    try:
        with create_rendering_executor(test_config, max_workers=2) as executor:
            print("✅ Factory function works correctly")
            print(f"   Executor: {executor}")
            print(f"   Max workers: {executor._max_workers}")
    except Exception as e:
        print(f"❌ Factory function failed: {e}")
    
    # Test validation
    try:
        create_rendering_executor(None)
        print("❌ Validation failed - should have rejected None config")
    except ValueError:
        print("✅ Validation works - correctly rejected None config")
    
    print("Factory testing complete!")