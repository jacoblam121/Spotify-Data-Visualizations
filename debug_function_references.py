#!/usr/bin/env python3
"""
Debug function references to understand import vs module attribute
"""

import os
import sys

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_function_references():
    """Check different function references"""
    print("Checking function references...")
    
    # Import the modules
    import parallel_render_manager
    import stateless_renderer
    from test_mock_components import mock_render_frame_from_spec
    
    print("\n1. Original function references:")
    print(f"  stateless_renderer.render_frame_from_spec: {stateless_renderer.render_frame_from_spec}")
    print(f"  parallel_render_manager.render_frame_from_spec: {parallel_render_manager.render_frame_from_spec}")
    print(f"  Are they the same object? {stateless_renderer.render_frame_from_spec is parallel_render_manager.render_frame_from_spec}")
    
    # Check the imported render_frame_from_spec inside parallel_render_manager
    from parallel_render_manager import render_frame_from_spec as imported_render
    print(f"  imported render_frame_from_spec: {imported_render}")
    print(f"  Is imported same as stateless? {imported_render is stateless_renderer.render_frame_from_spec}")
    print(f"  Is imported same as module attr? {imported_render is parallel_render_manager.render_frame_from_spec}")
    
    print("\n2. After overriding parallel_render_manager.render_frame_from_spec:")
    parallel_render_manager.render_frame_from_spec = mock_render_frame_from_spec
    print(f"  stateless_renderer.render_frame_from_spec: {stateless_renderer.render_frame_from_spec}")
    print(f"  parallel_render_manager.render_frame_from_spec: {parallel_render_manager.render_frame_from_spec}")
    print(f"  imported render_frame_from_spec: {imported_render}")
    
    print("\n3. After overriding stateless_renderer.render_frame_from_spec:")
    stateless_renderer.render_frame_from_spec = mock_render_frame_from_spec
    print(f"  stateless_renderer.render_frame_from_spec: {stateless_renderer.render_frame_from_spec}")
    print(f"  parallel_render_manager.render_frame_from_spec: {parallel_render_manager.render_frame_from_spec}")
    print(f"  imported render_frame_from_spec: {imported_render}")
    print(f"  Is imported same as stateless now? {imported_render is stateless_renderer.render_frame_from_spec}")

if __name__ == "__main__":
    test_function_references()