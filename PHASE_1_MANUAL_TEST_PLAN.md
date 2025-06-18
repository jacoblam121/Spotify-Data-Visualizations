# Phase 1.1 Manual Test Plan - Foundation Verification

## Overview
This test plan validates that the basic infrastructure is working before moving to Phase 1.1 (Multi-Genre Artist Support) implementation.

## Pre-Test Setup

1. **Environment Check**:
   ```bash
   # Verify Python environment
   python --version
   
   # Check required files exist
   ls -la comprehensive_similarity_test_suite.py
   ls -la ultimate_similarity_system.py
   ls -la comprehensive_edge_weighting_system.py
   ls -la configurations.txt
   ```

2. **Dependencies Check**:
   ```bash
   # Verify imports work
   python -c "import json, time; print('Basic imports OK')"
   python -c "from dataclasses import dataclass; print('Dataclasses OK')"
   ```

## Test Suite 1: Syntax and Import Validation

### Test 1.1: File Compilation
**Command to run:**
```bash
python -m py_compile comprehensive_similarity_test_suite.py
echo "Exit code: $?"
```

**Expected result:** 
- No output, exit code 0
- File compiles without syntax errors

**If this fails:** Report the exact error message

### Test 1.2: Basic Import Test
**Command to run:**
```bash
python -c "
try:
    from comprehensive_similarity_test_suite import ComprehensiveSimilarityTestSuite
    print('✓ Main class imports successfully')
except ImportError as e:
    print(f'✗ Import failed: {e}')
except Exception as e:
    print(f'✗ Other error: {e}')
"
```

**Expected result:** 
- "✓ Main class imports successfully"

**If this fails:** Report the exact error message and which dependencies are missing

## Test Suite 2: Component Initialization

### Test 2.1: Basic Initialization
**Command to run:**
```bash
python -c "
from comprehensive_similarity_test_suite import ComprehensiveSimilarityTestSuite
try:
    suite = ComprehensiveSimilarityTestSuite()
    print('✓ Test suite initialized')
    print(f'  - Artists to test: {len(suite.test_artists)}')
    print(f'  - Similarity system: {\"Available\" if suite.similarity_system else \"Not available\"}')
    print(f'  - Edge weighter: {\"Available\" if suite.edge_weighter else \"Not available\"}')
    print(f'  - Cache manager: {\"Available\" if suite.cache_manager else \"Not available\"}')
except Exception as e:
    print(f'✗ Initialization failed: {e}')
    import traceback
    traceback.print_exc()
"
```

**Expected result:**
- "✓ Test suite initialized"
- Shows count of test artists (should be 8)
- Shows which components are available (at least similarity system should be available)

**If this fails:** Report which components failed to initialize and the error messages

### Test 2.2: Configuration Loading
**Command to run:**
```bash
python -c "
from comprehensive_similarity_test_suite import ComprehensiveSimilarityTestSuite
suite = ComprehensiveSimilarityTestSuite()
if suite.config:
    print('✓ Configuration loaded successfully')
    print(f'  - Config type: {type(suite.config)}')
else:
    print('⚠ Configuration not loaded (using defaults)')
"
```

**Expected result:**
- Either "✓ Configuration loaded" or "⚠ Configuration not loaded (using defaults)"
- Both are acceptable for testing

## Test Suite 3: Single Artist Test

### Test 3.1: Single Artist Similarity Test
**Command to run:**
```bash
python -c "
from comprehensive_similarity_test_suite import ComprehensiveSimilarityTestSuite
suite = ComprehensiveSimilarityTestSuite()

if suite.similarity_system:
    print('Testing with Taylor Swift...')
    try:
        test_result = suite._test_single_artist('Taylor Swift')
        print(f'✓ Test completed: {\"PASS\" if test_result.success else \"FAIL\"}')
        print(f'  - Execution time: {test_result.execution_time:.2f}s')
        print(f'  - API coverage: {test_result.api_coverage}')
        print(f'  - Edge weights: {len(test_result.edge_weights)}')
        print(f'  - Issues: {len(test_result.issues)}')
        if test_result.issues:
            print('  - First few issues:')
            for issue in test_result.issues[:3]:
                print(f'    - {issue}')
    except Exception as e:
        print(f'✗ Single artist test failed: {e}')
        import traceback
        traceback.print_exc()
else:
    print('✗ Cannot test: similarity_system not available')
"
```

**Expected result:**
- Either "✓ Test completed: PASS" or "✓ Test completed: FAIL" 
- Some API coverage results (even if 0)
- Execution time under 30 seconds
- If FAIL, should show issues explaining why

**If this fails completely:** Report the full error and traceback

## Test Suite 4: Edge Weighting Test

### Test 4.1: Edge Weighting Component Test
**Command to run:**
```bash
python -c "
from comprehensive_similarity_test_suite import ComprehensiveSimilarityTestSuite
suite = ComprehensiveSimilarityTestSuite()

# Test with mock data
mock_api_data = {
    'lastfm': [{'name': 'Artist A', 'match': 0.9}],
    'deezer': [{'name': 'Artist B', 'match': 0.8}]
}

if suite.edge_weighter:
    print('Testing edge weighting...')
    try:
        result = suite._test_edge_weighting_for_artist('Test Artist', mock_api_data)
        print(f'✓ Edge weighting test completed')
        print(f'  - Weights created: {len(result[\"weights\"])}')
        print(f'  - Issues: {len(result[\"issues\"])}')
        if result['issues']:
            print('  - Issues found:')
            for issue in result['issues']:
                print(f'    - {issue}')
    except Exception as e:
        print(f'✗ Edge weighting test failed: {e}')
else:
    print('⚠ Edge weighter not available - skipping test')
"
```

**Expected result:**
- "✓ Edge weighting test completed" OR "⚠ Edge weighter not available"
- Some indication of weights created or issues found

## Test Suite 5: Cache System Test

### Test 5.1: Cache System Verification
**Command to run:**
```bash
python -c "
import os
print('Cache directory status:')
cache_dirs = ['lastfm_cache', 'album_art_cache', 'artist_art_cache']
for cache_dir in cache_dirs:
    if os.path.exists(cache_dir):
        file_count = len([f for f in os.listdir(cache_dir) if os.path.isfile(os.path.join(cache_dir, f))])
        print(f'  - {cache_dir}: EXISTS ({file_count} files)')
    else:
        print(f'  - {cache_dir}: NOT FOUND')
"
```

**Expected result:**
- Shows status of cache directories
- May show existing cache files if you've run the system before

## Reporting Instructions

For each test, please report:

1. **Test number and name**
2. **Command you ran**  
3. **Actual output** (copy-paste the complete output)
4. **Status**: ✓ PASS / ✗ FAIL / ⚠ WARNING
5. **Any error messages or unexpected behavior**

## Success Criteria for Phase 1.1 Readiness

To proceed to Phase 1.1 implementation, we need:

- ✅ Test 1.1: File compiles without syntax errors
- ✅ Test 1.2: Main class imports successfully  
- ✅ Test 2.1: Test suite initializes (similarity_system available)
- ✅ Test 3.1: Single artist test runs (PASS or FAIL with clear issues)
- ✅ Test 4.1: Edge weighting test runs without crashing

Cache and configuration tests are helpful but not blocking.

---

**Next Steps After Testing:**
Once these tests pass, we'll proceed with Phase 1.1: Multi-Genre Artist Support integration, starting with examining `multi_genre_solution.py` and planning the integration approach.