#!/bin/bash

# Phase 1 Test Runner Script
# Comprehensive validation of data extraction functionality

set -e  # Exit on any error

echo "=================================================================="
echo "🧪 PHASE 1 COMPREHENSIVE TEST SUITE"
echo "=================================================================="
echo

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Set encoding
export PYTHONIOENCODING=utf-8

# Check data sources first
echo "🔍 Checking data source availability..."
python check_data_sources.py
echo

# Check exit code from data source check
if [ $? -ne 0 ]; then
    echo "❌ Data source check failed. Please fix issues before running tests."
    exit 1
fi

echo "🚀 Starting interactive test suite..."
echo

# Run the comprehensive test suite with interactive menu
python test_phase1_comprehensive.py

# Capture exit code
TEST_EXIT_CODE=$?

echo
echo "=================================================================="
echo "📊 PHASE 1 TEST RESULTS"
echo "=================================================================="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ ALL TESTS PASSED!"
    echo
    echo "🎉 Phase 1 is working correctly!"
    echo "   - Data extraction is functional"
    echo "   - Frame specifications are valid"
    echo "   - JSON serialization works"
    echo "   - Both data sources supported"
    echo
    echo "📁 Test artifacts saved to: phase1_test_samples/"
    echo
    echo "🔄 READY FOR PHASE 2!"
    echo "   Next: Implement stateless parallel rendering"
else
    echo "❌ SOME TESTS FAILED"
    echo
    echo "📋 Troubleshooting steps:"
    echo "   1. Check error messages above"
    echo "   2. Inspect sample files in phase1_test_samples/"
    echo "   3. Run specific tests: python test_phase1_comprehensive.py --test <test_name>"
    echo "   4. Run with verbose logging: python test_phase1_comprehensive.py -v"
    echo
    echo "🛠️  Fix issues before proceeding to Phase 2"
fi

echo
echo "=================================================================="

exit $TEST_EXIT_CODE