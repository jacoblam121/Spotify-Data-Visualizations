#!/usr/bin/env python3
"""
Phase 1B Test Suite: Server Cleanup Validation
Tests that legacy server scripts are properly deprecated and new server works
"""

import os
import subprocess
import sys
import json
from datetime import datetime

def test_results():
    """Return test results structure"""
    return {
        "test_name": "Phase 1B Server Cleanup",
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "summary": {"passed": 0, "failed": 0, "total": 0}
    }

def run_test(test_name, test_func, results):
    """Run a single test and record results"""
    print(f"🧪 Testing: {test_name}")
    try:
        success, message = test_func()
        status = "PASS" if success else "FAIL"
        print(f"   {status}: {message}")
        
        results["tests"].append({
            "name": test_name,
            "status": status,
            "message": message
        })
        
        if success:
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1
            
    except Exception as e:
        print(f"   ERROR: {str(e)}")
        results["tests"].append({
            "name": test_name,
            "status": "ERROR", 
            "message": str(e)
        })
        results["summary"]["failed"] += 1
    
    results["summary"]["total"] += 1

def test_deprecated_directory_exists():
    """Test that _deprecated directory was created"""
    deprecated_dir = "/home/jacob/Spotify-Data-Visualizations/_deprecated"
    if os.path.exists(deprecated_dir):
        return True, f"_deprecated directory exists at {deprecated_dir}"
    return False, "_deprecated directory not found"

def test_legacy_scripts_moved():
    """Test that legacy server scripts were moved to _deprecated"""
    deprecated_dir = "/home/jacob/Spotify-Data-Visualizations/_deprecated"
    expected_files = [
        "start_server.py",
        "simple_server.py", 
        "bulletproof_server.py",
        "fixed_server.py",
        "working_server.py",
        "test_server.py",
        "kill_server.py",
        "server_manager.py"
    ]
    
    missing_files = []
    for filename in expected_files:
        file_path = os.path.join(deprecated_dir, filename)
        if not os.path.exists(file_path):
            missing_files.append(filename)
    
    if not missing_files:
        return True, f"All {len(expected_files)} legacy scripts moved to _deprecated"
    return False, f"Missing files in _deprecated: {missing_files}"

def test_legacy_scripts_not_in_original_locations():
    """Test that legacy scripts no longer exist in original locations"""
    project_root = "/home/jacob/Spotify-Data-Visualizations"
    static_dir = os.path.join(project_root, "static")
    
    original_locations = [
        os.path.join(project_root, "start_server.py"),
        os.path.join(static_dir, "simple_server.py"),
        os.path.join(static_dir, "bulletproof_server.py"),
        os.path.join(static_dir, "fixed_server.py"),
        os.path.join(static_dir, "working_server.py"),
        os.path.join(static_dir, "test_server.py"),
        os.path.join(static_dir, "kill_server.py"),
        os.path.join(static_dir, "server_manager.py")
    ]
    
    still_existing = []
    for file_path in original_locations:
        if os.path.exists(file_path):
            still_existing.append(file_path)
    
    if not still_existing:
        return True, "All legacy scripts removed from original locations"
    return False, f"Scripts still in original locations: {still_existing}"

def test_dev_server_still_exists():
    """Test that dev_server.py still exists and is functional"""
    dev_server_path = "/home/jacob/Spotify-Data-Visualizations/dev_server.py"
    if not os.path.exists(dev_server_path):
        return False, "dev_server.py not found"
        
    # Quick syntax check
    try:
        subprocess.run([sys.executable, "-m", "py_compile", dev_server_path], 
                      check=True, capture_output=True)
        return True, "dev_server.py exists and compiles successfully"
    except subprocess.CalledProcessError as e:
        return False, f"dev_server.py has syntax errors: {e.stderr.decode()}"

def test_deprecated_readme_exists():
    """Test that README.md exists in _deprecated directory"""
    readme_path = "/home/jacob/Spotify-Data-Visualizations/_deprecated/README.md"
    if os.path.exists(readme_path):
        with open(readme_path, 'r') as f:
            content = f.read()
            if "deprecated" in content.lower() and "dev_server.py" in content:
                return True, "Deprecation README exists with proper content"
            return False, "Deprecation README missing key content"
    return False, "_deprecated/README.md not found"

def test_documentation_updated():
    """Test that UTF8_DEBUG_TEST.md was updated to reference dev_server.py"""
    utf8_test_path = "/home/jacob/Spotify-Data-Visualizations/static/UTF8_DEBUG_TEST.md"
    if os.path.exists(utf8_test_path):
        with open(utf8_test_path, 'r') as f:
            content = f.read()
            if "dev_server.py" in content and "test_server.py" not in content:
                return True, "UTF8_DEBUG_TEST.md updated to use dev_server.py"
            elif "test_server.py" in content:
                return False, "UTF8_DEBUG_TEST.md still references old test_server.py"
            else:
                return True, "UTF8_DEBUG_TEST.md has no server references"
    return False, "UTF8_DEBUG_TEST.md not found"

def main():
    """Run all Phase 1B tests"""
    print("🧪 Phase 1B Test Suite: Server Cleanup Validation")
    print("=" * 60)
    
    results = test_results()
    
    # Run all tests
    run_test("Deprecated directory exists", test_deprecated_directory_exists, results)
    run_test("Legacy scripts moved to _deprecated", test_legacy_scripts_moved, results) 
    run_test("Legacy scripts removed from original locations", test_legacy_scripts_not_in_original_locations, results)
    run_test("dev_server.py still exists and compiles", test_dev_server_still_exists, results)
    run_test("Deprecation README exists", test_deprecated_readme_exists, results)
    run_test("Documentation updated", test_documentation_updated, results)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 Test Summary: {results['summary']['passed']}/{results['summary']['total']} passed")
    
    if results['summary']['failed'] > 0:
        print("❌ FAILED TESTS:")
        for test in results['tests']:
            if test['status'] in ['FAIL', 'ERROR']:
                print(f"   - {test['name']}: {test['message']}")
    else:
        print("✅ All tests passed!")
    
    # Save detailed results
    results_file = "test_phase1b_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"📝 Detailed results saved to {results_file}")
    
    return results['summary']['failed'] == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)