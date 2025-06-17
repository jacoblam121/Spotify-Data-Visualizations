# Phase 1 Manual Test Suite

## Overview

I've created a comprehensive manual test suite that you can run to validate that Phase 1 (data extraction) is working correctly with both Spotify and Last.fm data sources. The test suite covers normal operation, edge cases, and performance validation.

## Quick Start

```bash
# Activate environment and run all tests
source venv/bin/activate
./run_phase1_tests.sh
```

This will:
1. Check data source availability
2. Run comprehensive test suite with verbose output
3. Generate sample files for inspection
4. Provide clear pass/fail results

## Test Files Created

### Main Test Scripts
- **`test_phase1_comprehensive.py`** - Main test suite with 9 different test scenarios
- **`check_data_sources.py`** - Validates that data files are present and readable
- **`run_phase1_tests.sh`** - Convenient shell script to run everything

### Documentation
- **`TESTING_GUIDE.md`** - Detailed guide on how to run tests and interpret results
- **`MANUAL_TEST_SUITE.md`** - This file

## Test Coverage

### Core Functionality (Both Data Sources)
1. **Spotify Data Extraction** - Tests with `spotify_data.json`
2. **Last.fm Data Extraction** - Tests with `lastfm_data.csv` (if available)
3. **Artist Mode** - Tests artist visualization mode vs tracks mode

### Edge Cases
4. **Single Bar** - Tests with only 1 bar (minimal data scenario)
5. **No Nightingale** - Tests with nightingale chart disabled
6. **Frame Aggregation** - Tests daily frame aggregation (time-based grouping)

### Performance & Scalability
7. **Large Frame Count** - Tests with 50 frames to check performance
8. **Memory Usage Analysis** - Measures memory consumption and estimates scaling

### Technical Validation
9. **JSON Serialization** - Tests conversion of pandas/numpy types to JSON

## What Each Test Validates

### Data Processing
- ✅ Configuration loading works correctly
- ✅ Data sources are read and processed
- ✅ Race data preparation works
- ✅ Rolling statistics calculation works
- ✅ Nightingale chart data preparation works
- ✅ Render tasks are generated correctly

### Frame Specification Creation
- ✅ Frame specs contain all required fields
- ✅ Bar data is correctly extracted and positioned
- ✅ Display names are correct for both modes
- ✅ Colors and metadata are preserved
- ✅ Rolling stats and nightingale data are included

### JSON Compatibility
- ✅ All frame specs are JSON-serializable
- ✅ Pandas timestamps are converted to ISO strings
- ✅ Numpy arrays and types are converted to Python natives
- ✅ Nested data structures work correctly

### Performance & Memory
- ✅ Frame generation performance (target: >10 frames/second)
- ✅ Memory usage is reasonable (<1MB per frame for typical data)
- ✅ Large frame counts don't cause memory explosion

## Running Specific Tests

```bash
# Check data availability first
python check_data_sources.py

# Run specific test categories
python test_phase1_comprehensive.py --test spotify      # Spotify data
python test_phase1_comprehensive.py --test lastfm       # Last.fm data
python test_phase1_comprehensive.py --test artist       # Artist mode
python test_phase1_comprehensive.py --test large        # Performance test
python test_phase1_comprehensive.py --test memory       # Memory analysis

# Run with verbose logging
python test_phase1_comprehensive.py -v

# Run without saving sample files
python test_phase1_comprehensive.py --no-samples
```

## Expected Results

### Success Criteria
- **8-9 tests pass** (9 if both data sources available)
- **Performance >10 frames/second** for frame spec generation
- **Memory usage <100MB** for test datasets
- **All frame specs JSON-serializable**
- **Sample files contain complete data**

### Output Files
The test suite creates `phase1_test_samples/` directory with:
- `{test_name}_sample.json` - Sample frame spec for each test
- `{test_name}_metrics.json` - Performance metrics
- `memory_analysis.json` - Memory usage analysis
- `serialization_test.json` - JSON type conversion test

### Sample Frame Spec Structure
```json
{
  "frame_index": 0,
  "display_timestamp": "2017-03-03T06:14:24+00:00",
  "bars": [...],                    // Bar positions and data
  "rolling_stats": {...},           // 7-day and 30-day top items
  "nightingale_data": {...},        // Rose chart segments
  "dynamic_x_axis_limit": 11.0,     // Calculated axis maximum
  "visualization_mode": "artists"    // tracks or artists
}
```

## Troubleshooting

### Common Issues

**"No data available"**
- Run `python check_data_sources.py` to verify data files
- Check that `spotify_data.json` or `lastfm_data.csv` exists
- Verify file format matches expected structure

**"JSON serialization failed"**
- Usually indicates pandas/numpy types not handled
- Check `make_json_serializable()` function coverage
- Look at error details for specific type causing issue

**Performance warnings**
- Normal for first run (no caching)
- Check available system memory
- Consider reducing test frame counts if system is constrained

### Getting Detailed Information

```bash
# Verbose logging shows all processing steps
python test_phase1_comprehensive.py -v

# Check specific test results
cat phase1_test_samples/spotify_metrics.json
cat phase1_test_samples/memory_analysis.json

# Inspect sample frame specification
cat phase1_test_samples/spotify_sample.json | jq .
```

## Data Source Support

### Spotify Data (`spotify_data.json`)
- ✅ **New format** - `master_metadata_*` fields (your current file)
- ✅ **Old format** - `artistName`, `trackName`, `msPlayed` fields
- ✅ **Both tracks and artists mode**
- ✅ **Full feature support**

### Last.fm Data (`lastfm_data.csv`)
- ✅ **CSV export format** from lastfm.ghan.nl/export/
- ✅ **Both tracks and artists mode**
- ✅ **Full feature support**
- ⚠️ **Optional** - tests skip if file not present

## Integration with Existing Code

The test suite:
- ✅ **Preserves all existing logic** - no visual changes
- ✅ **Uses real configuration** - tests actual settings
- ✅ **Tests actual data pipeline** - not just mock data
- ✅ **Validates frame specs** - ensures all necessary data present
- ✅ **Measures real performance** - actual timing metrics

## Next Steps After Testing

If tests pass:
1. **✅ Phase 1 Complete** - Data extraction is working
2. **🔄 Ready for Phase 2** - Stateless parallel rendering
3. **📊 Use metrics** - Performance baselines established
4. **🔍 Inspect samples** - Verify frame spec completeness

If tests fail:
1. **🔍 Check error messages** - Specific failure details
2. **📊 Review metrics** - Performance or memory issues
3. **🛠️ Fix issues** - Update code based on test results
4. **🔄 Re-run tests** - Validate fixes work

## Test Suite Features

- **🔄 Configurable** - Works with both data sources
- **📊 Comprehensive** - Covers normal operation and edge cases
- **⚡ Fast** - Limited frame counts for quick validation
- **📈 Performance-aware** - Measures timing and memory
- **🔍 Detailed** - Verbose logging and sample file generation
- **🛡️ Robust** - Handles missing files and configuration errors
- **📱 User-friendly** - Clear output and troubleshooting guidance

Run the tests and let me know the results! The test suite will tell you exactly what's working and what needs attention before moving to Phase 2.