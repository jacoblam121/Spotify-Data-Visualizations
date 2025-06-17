# Phase 1 Testing Guide

## Quick Start

### Interactive Menu (Recommended)
```bash
source venv/bin/activate
python test_phase1_comprehensive.py
```

This will show an interactive menu with options:
- 🚀 Run All Tests (Recommended)
- ⚡ Quick Validation (Core tests only) 
- 🎯 Individual Test Selection
- 🔧 Advanced Options
- 📋 Data Source Check
- ❓ Help & Documentation

### Alternative Launchers
```bash
# Quick launcher (same as above)
python test_menu.py

# Complete test runner with data source check
./run_phase1_tests.sh
```

## Interactive Menu Features

### Main Menu Options

**🚀 Run All Tests** - Comprehensive validation (9 tests)
- Tests both data sources, all modes, edge cases, performance
- Takes 2-5 minutes depending on data size
- Recommended for complete validation

**⚡ Quick Validation** - Core tests only (3 tests)
- JSON serialization, Spotify data, Artist mode
- Takes 30-60 seconds
- Good for rapid checking

**🎯 Individual Test Selection** - Choose one specific test
- Interactive list with descriptions
- Configure verbose logging and sample saving
- Good for debugging specific issues

**🔧 Advanced Options** - Power user features
- Custom settings for all/quick tests
- Multiple test selection
- Performance analysis suite
- Data source comparison

**📋 Data Source Check** - Validate data availability
- Checks spotify_data.json and lastfm_data.csv
- Validates file format and content
- Reports configuration status

### Command Line Options (Advanced)

```bash
# Force interactive menu
python test_phase1_comprehensive.py --interactive

# Traditional command line usage
python test_phase1_comprehensive.py -v                    # All tests, verbose
python test_phase1_comprehensive.py --test spotify        # Specific test
python test_phase1_comprehensive.py --no-samples          # No sample files
```

## What Each Test Does

### Core Functionality Tests

1. **Spotify Data Extraction** - Tests with spotify_data.json
   - Loads Spotify data in tracks mode
   - Processes 5 frames with 3 bars each
   - Validates frame spec structure

2. **Last.fm Data Extraction** - Tests with lastfm_data.csv (if available)
   - Loads Last.fm CSV data in tracks mode
   - Same validation as Spotify test

3. **Artist Mode** - Tests artist visualization mode
   - Uses Spotify data in artists mode
   - Validates artist-specific display names
   - Checks entity details for artist data

### Edge Case Tests

4. **Single Bar Edge Case** - Tests with only 1 bar
   - Ensures system works with minimal data
   - Validates edge case handling

5. **No Nightingale** - Tests with nightingale chart disabled
   - Verifies system works without nightingale data
   - Checks configuration override handling

6. **Frame Aggregation** - Tests daily frame aggregation
   - Validates time-based frame grouping
   - Checks aggregated data structure

### Performance Tests

7. **Large Frame Count** - Tests with 50 frames
   - Measures performance with larger datasets
   - Validates memory usage doesn't explode
   - Performance threshold: >10 frames/second

8. **Memory Usage Analysis** - Analyzes memory consumption
   - Measures frame spec size in bytes
   - Estimates memory for 1000+ frame animations
   - Saves detailed memory analysis

### Technical Tests

9. **JSON Serialization** - Tests data type conversion
   - Validates pandas/numpy type handling
   - Tests nested data structures
   - Ensures all frame specs are JSON-serializable

## Test Configuration

The test suite automatically creates temporary configuration files with overrides:

- **MAX_FRAMES_FOR_TEST_RENDER**: Limited for faster testing
- **N_BARS**: Adjusted per test case
- **SOURCE**: Switched between spotify/lastfm
- **MODE**: Switched between tracks/artists
- **ENABLE**: Nightingale chart toggle

## Output Files

### Sample Files (phase1_test_samples/)
- `{test_name}_sample.json` - Sample frame spec for each test
- `{test_name}_metrics.json` - Performance metrics
- `memory_analysis.json` - Detailed memory usage analysis
- `serialization_test.json` - JSON serialization test results

### What to Look For

✅ **Success Indicators:**
- All tests pass (success rate ≥90%)
- Frame specs contain all required fields
- JSON serialization works for all data types
- Performance >10 frames/second
- Memory usage <100MB for test datasets

⚠️ **Warning Signs:**
- Some tests fail but core functionality works (70-89% success rate)
- Performance <10 frames/second
- Large memory usage for small datasets

❌ **Critical Issues:**
- Core tests fail (<70% success rate)
- JSON serialization failures
- Missing required frame spec fields
- Crashes or exceptions

## Troubleshooting

### Common Issues

1. **"lastfm_data.csv not found"**
   - This is normal if you only have Spotify data
   - Last.fm test will be skipped automatically

2. **"No data available"**
   - Check that your data files exist
   - Verify data source configuration
   - Run with `-v` for detailed logging

3. **"JSON serialization failed"**
   - Usually indicates pandas/numpy types not handled
   - Check the `make_json_serializable()` function
   - May need to add more type conversions

4. **Performance issues**
   - Normal for first run (no cache)
   - Check available memory
   - Consider reducing test frame counts

### Getting Help

1. Run with verbose logging: `-v`
2. Check sample files in `phase1_test_samples/`
3. Look at metrics files for performance details
4. Check the main log output for specific error messages

## Expected Results

For a working Phase 1 implementation:
- 8-9 tests should pass (9/9 if lastfm_data.csv exists)
- Frame generation should be >10 frames/second
- Memory usage should be reasonable (<1MB per frame)
- All frame specs should be JSON-serializable
- Sample files should contain complete frame data

If all tests pass, Phase 1 is ready and you can proceed to Phase 2!