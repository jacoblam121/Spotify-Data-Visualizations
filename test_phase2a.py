#!/usr/bin/env python3
"""
Phase 2A Test Suite: HTML Cache-Busting Validation
Tests that HTML files use root-relative paths with cache-busting parameters
"""

import os
import subprocess
import sys
import json
from datetime import datetime

def test_results():
    """Return test results structure"""
    return {
        "test_name": "Phase 2A HTML Cache-Busting",
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

def test_network_enhanced_html_cache_busting():
    """Test network_enhanced.html uses root-relative paths with cache-busting"""
    file_path = "/home/jacob/Spotify-Data-Visualizations/static/network_enhanced.html"
    
    if not os.path.exists(file_path):
        return False, "network_enhanced.html not found"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check for new root-relative paths
    expected_patterns = [
        'src="/static/js/genre_colors.js?v=2.5"',
        'src="/static/js/renderers/base_renderer.js?v=2.5"', 
        'src="/static/js/renderers/canvas_renderer.js?v=2.5"',
        'src="/static/js/renderers/svg_renderer.js?v=2.5"',
        'src="/static/js/network_enhanced_fixed.js?v=2.5"'
    ]
    
    missing_patterns = []
    for pattern in expected_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)
    
    # Check for old relative paths (should be gone)
    old_patterns = [
        'src="js/genre_colors.js"',
        'src="js/renderers/base_renderer.js"',
        'src="js/renderers/canvas_renderer.js"'
    ]
    
    found_old_patterns = []
    for pattern in old_patterns:
        if pattern in content:
            found_old_patterns.append(pattern)
    
    if missing_patterns:
        return False, f"Missing cache-busting patterns: {missing_patterns}"
    if found_old_patterns:
        return False, f"Still contains old relative paths: {found_old_patterns}"
    
    return True, f"All 5 script tags updated with root-relative paths and v=2.5 cache-busting"

def test_phase2_1_simple_html_cache_busting():
    """Test test_phase2_1_simple.html uses root-relative paths with cache-busting"""
    file_path = "/home/jacob/Spotify-Data-Visualizations/static/test_phase2_1_simple.html"
    
    if not os.path.exists(file_path):
        return False, "test_phase2_1_simple.html not found"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check for new root-relative paths
    expected_patterns = [
        'src="/static/js/genre_colors.js?v=2.5"',
        'src="/static/js/renderers/base_renderer.js?v=2.5"', 
        'src="/static/js/renderers/canvas_renderer.js?v=2.5"'
    ]
    
    missing_patterns = []
    for pattern in expected_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)
    
    # Check for old relative paths (should be gone)
    old_patterns = [
        'src="js/genre_colors.js"',
        'src="js/renderers/base_renderer.js"',
        'src="js/renderers/canvas_renderer.js"'
    ]
    
    found_old_patterns = []
    for pattern in old_patterns:
        if pattern in content:
            found_old_patterns.append(pattern)
    
    if missing_patterns:
        return False, f"Missing cache-busting patterns: {missing_patterns}"
    if found_old_patterns:
        return False, f"Still contains old relative paths: {found_old_patterns}"
    
    return True, f"All 3 script tags updated with root-relative paths and v=2.5 cache-busting"

def test_dev_server_cache_control():
    """Test that dev_server.py includes cache control headers"""
    dev_server_path = "/home/jacob/Spotify-Data-Visualizations/dev_server.py"
    
    if not os.path.exists(dev_server_path):
        return False, "dev_server.py not found"
    
    with open(dev_server_path, 'r') as f:
        content = f.read()
    
    # Check for cache control implementation
    cache_indicators = [
        "Cache-Control",
        "no-cache",
        "no-store", 
        "must-revalidate"
    ]
    
    found_indicators = []
    for indicator in cache_indicators:
        if indicator in content:
            found_indicators.append(indicator)
    
    if len(found_indicators) >= 2:  # At least Cache-Control + one directive
        return True, f"Cache control headers found: {found_indicators}"
    
    return False, f"Insufficient cache control implementation. Found: {found_indicators}"

def test_javascript_files_exist():
    """Test that all referenced JavaScript files exist"""
    static_dir = "/home/jacob/Spotify-Data-Visualizations/static"
    
    expected_files = [
        "js/genre_colors.js",
        "js/renderers/base_renderer.js",
        "js/renderers/canvas_renderer.js",
        "js/renderers/svg_renderer.js",
        "js/network_enhanced_fixed.js"
    ]
    
    missing_files = []
    for filename in expected_files:
        file_path = os.path.join(static_dir, filename)
        if not os.path.exists(file_path):
            missing_files.append(filename)
    
    if not missing_files:
        return True, f"All {len(expected_files)} JavaScript files exist"
    
    return False, f"Missing JavaScript files: {missing_files}"

def main():
    """Run all Phase 2A tests"""
    print("🧪 Phase 2A Test Suite: HTML Cache-Busting Validation")
    print("=" * 60)
    
    results = test_results()
    
    # Run all tests
    run_test("network_enhanced.html cache-busting", test_network_enhanced_html_cache_busting, results)
    run_test("test_phase2_1_simple.html cache-busting", test_phase2_1_simple_html_cache_busting, results) 
    run_test("dev_server.py cache control headers", test_dev_server_cache_control, results)
    run_test("All JavaScript files exist", test_javascript_files_exist, results)
    
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
    results_file = "test_phase2a_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"📝 Detailed results saved to {results_file}")
    
    return results['summary']['failed'] == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)