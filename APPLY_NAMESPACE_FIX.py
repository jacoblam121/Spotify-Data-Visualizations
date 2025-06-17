#!/usr/bin/env python3
"""
NAMESPACE FIX - Correct Module Global Variable Injection

This fixes the module namespace issue identified by Gemini where globals().update()
only affects the current module but we need to inject variables into main_animator's namespace.

ROOT CAUSE: Cross-module global variable access in multiprocessing
SOLUTION: Use setattr(main_animator, key, value) to inject into correct namespace
"""

import os
import re

def apply_namespace_fix():
    """Apply the correct namespace fix to main_animator_ENHANCED_FIX.py"""
    
    enhanced_fix_file = "/home/jacob/Spotify-Data-Visualizations/main_animator_ENHANCED_FIX.py"
    
    print("🔧 APPLYING NAMESPACE FIX")
    print("=" * 50)
    print("Fixing module namespace issue with setattr approach")
    
    with open(enhanced_fix_file, 'r') as f:
        content = f.read()
    
    # Find and replace the incorrect globals().update() approach
    old_init_worker = '''def init_enhanced_worker(enhanced_globals: Dict[str, Any]):
    """
    Enhanced worker initializer that injects ALL relevant globals including 
    configuration-loaded variables that were missing in the original approach.
    """
    global ENHANCED_WORKER_CONTEXT
    ENHANCED_WORKER_CONTEXT = enhanced_globals
    
    # Inject all globals into this worker's namespace
    globals().update(enhanced_globals)
    
    worker_pid = os.getpid()
    print(f"[WORKER {worker_pid}] Enhanced worker initialized with {len(enhanced_globals)} globals")
    print(f"[WORKER {worker_pid}] NIGHTINGALE_TITLE_FONT_SIZE = {enhanced_globals.get('NIGHTINGALE_TITLE_FONT_SIZE', 'MISSING')}")'''
    
    new_init_worker = '''def init_enhanced_worker(enhanced_globals: Dict[str, Any]):
    """
    Enhanced worker initializer that injects ALL relevant globals including 
    configuration-loaded variables that were missing in the original approach.
    
    FIXED: Uses setattr(main_animator, key, value) to inject variables into 
    main_animator's module namespace, not the current module's namespace.
    """
    global ENHANCED_WORKER_CONTEXT
    ENHANCED_WORKER_CONTEXT = enhanced_globals
    
    # Import main_animator to access its module namespace
    import main_animator
    
    # CORRECT APPROACH: Inject globals into main_animator's module namespace
    # This fixes the cross-module namespace issue identified by Gemini
    for key, value in enhanced_globals.items():
        setattr(main_animator, key, value)
    
    worker_pid = os.getpid()
    print(f"[WORKER {worker_pid}] Enhanced worker initialized with {len(enhanced_globals)} globals")
    print(f"[WORKER {worker_pid}] NIGHTINGALE_TITLE_FONT_SIZE = {enhanced_globals.get('NIGHTINGALE_TITLE_FONT_SIZE', 'MISSING')}")
    print(f"[WORKER {worker_pid}] Injected into main_animator module namespace: {hasattr(main_animator, 'NIGHTINGALE_TITLE_FONT_SIZE')}")'''
    
    if old_init_worker in content:
        content = content.replace(old_init_worker, new_init_worker)
        print("✅ Fixed init_enhanced_worker function with setattr approach")
    else:
        print("⚠️  Could not find exact init_enhanced_worker function to replace")
        print("    Looking for alternative patterns...")
        
        # Try to find and replace the globals().update line specifically
        globals_update_pattern = r'(\s+)# Inject all globals into this worker\'s namespace\s*\n\s+globals\(\)\.update\(enhanced_globals\)'
        replacement = r'\1# CORRECT APPROACH: Inject globals into main_animator\'s module namespace\n\1# This fixes the cross-module namespace issue identified by Gemini\n\1import main_animator\n\1for key, value in enhanced_globals.items():\n\1    setattr(main_animator, key, value)'
        
        if re.search(globals_update_pattern, content):
            content = re.sub(globals_update_pattern, replacement, content)
            print("✅ Fixed globals().update() line with setattr approach")
        else:
            print("❌ Could not find globals().update() pattern to replace")
            return False
    
    # Write the corrected file
    with open(enhanced_fix_file, 'w') as f:
        f.write(content)
    
    print("\n🎉 NAMESPACE FIX APPLIED!")
    print("=" * 50)
    print("✅ Variables now injected into main_animator module namespace")
    print("✅ Cross-module global access issue resolved")
    print("✅ NIGHTINGALE_TITLE_FONT_SIZE should now be accessible")
    print("\nREADY FOR TESTING:")
    print("python main_animator.py")
    
    return True

def verify_fix():
    """Verify the namespace fix was applied correctly"""
    enhanced_fix_file = "/home/jacob/Spotify-Data-Visualizations/main_animator_ENHANCED_FIX.py"
    
    with open(enhanced_fix_file, 'r') as f:
        content = f.read()
    
    # Check if the fix was applied
    if 'setattr(main_animator, key, value)' in content:
        print("✅ Verification: setattr approach found in enhanced fix")
        return True
    else:
        print("❌ Verification: setattr approach NOT found in enhanced fix")
        return False

def main():
    """Apply and verify the namespace fix"""
    print("🎯 NAMESPACE FIX - Module Global Variable Injection")
    print("=" * 60)
    print("Root Cause: globals().update() affects wrong module namespace")
    print("Solution: Use setattr(main_animator, key, value) for correct injection")
    print()
    
    if apply_namespace_fix():
        if verify_fix():
            print("\n🚀 READY FOR TESTING!")
            print("The namespace issue should now be resolved.")
        else:
            print("\n⚠️  Fix applied but verification failed")
    else:
        print("\n❌ Failed to apply namespace fix")

if __name__ == "__main__":
    main()