#!/usr/bin/env python3
"""
Fix function override patterns in test files to override both modules
"""

import re
import os

def fix_test_file(file_path):
    """Fix function overrides in a test file"""
    print(f"Fixing {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern 1: Override setup - add stateless_renderer import and override
    pattern1 = r'(\s+import parallel_render_manager\n)(\s+original_initialize = parallel_render_manager\.initialize_render_worker\n)(\s+original_render = parallel_render_manager\.render_frame_from_spec\n)'
    replacement1 = r'\1            import stateless_renderer\n\2\3            original_stateless_render = stateless_renderer.render_frame_from_spec\n'
    
    content = re.sub(pattern1, replacement1, content)
    
    # Pattern 2: Function override - add stateless_renderer override
    pattern2 = r'(\s+parallel_render_manager\.render_frame_from_spec = mock_render_frame_from_spec\n)'
    replacement2 = r'\1            stateless_renderer.render_frame_from_spec = mock_render_frame_from_spec\n'
    
    content = re.sub(pattern2, replacement2, content)
    
    # Pattern 3: Restore - add stateless_renderer restore
    pattern3 = r'(\s+parallel_render_manager\.render_frame_from_spec = original_render\n)'
    replacement3 = r'\1            stateless_renderer.render_frame_from_spec = original_stateless_render\n'
    
    content = re.sub(pattern3, replacement3, content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    # Fix test files
    test_files = [
        "test_task3_comprehensive.py",
        "test_task3_validation.py", 
        "test_fixed_functionality.py",
        "debug_error_format.py"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            fix_test_file(file_path)
        else:
            print(f"File not found: {file_path}")
    
    print("All files fixed!")