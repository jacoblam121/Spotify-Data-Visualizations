# Phase A.2 Comprehensive Manual Test Suite Guide

## Overview

The comprehensive test suite validates all aspects of the Phase A.2 artist verification system with extensive configuration options for different testing scenarios.

## Quick Start

```bash
# Basic full test suite
python manual_test_suite_a2.py

# Quick validation (3 core test categories)
python manual_test_suite_a2.py --quick

# List all test categories
python manual_test_suite_a2.py --list-categories
```

## Test Categories

| Category | Description | Tests |
|----------|-------------|-------|
| `mbid` | MBID matching system | Perfect matches, fallback behavior, wrong MBID rejection |
| `track` | Track-based verification | Perfect/similar/no matches, evidence gathering |
| `unicode` | International character handling | Japanese characters, K-pop names, normalization |
| `edge` | Edge cases & error conditions | Empty data, malformed input, long names, special chars |
| `performance` | Performance characteristics | Single/batch verification speed, timing thresholds |
| `data` | Data source handling | Last.fm vs Spotify detection, MBID availability |
| `confidence` | Confidence threshold logic | MBID/track/heuristic confidence levels |
| `real` | Real problematic artists | Original problem cases (*LUNA, YOASOBI, etc.) |

## Configuration Parameters

### Data Source Configuration
```bash
--data-path PATH              # Custom data file path (default: lastfm_data.csv)
--force-source {lastfm,spotify}  # Override automatic source detection
```

### Performance Testing
```bash
--perf-iterations N           # Performance test iterations (default: 5)
--max-time SECONDS           # Max verification time threshold (default: 0.5s)
--batch-time SECONDS         # Max batch time per artist (default: 1.0s)
--sample-size N              # Performance test sample size (default: 10)
```

### Confidence Thresholds
```bash
--mbid-confidence FLOAT      # Minimum MBID confidence (default: 0.95)
--track-confidence FLOAT     # Minimum track confidence (default: 0.85)
--improvement-threshold FLOAT # Improvement over heuristics (default: 0.75)
```

### Test Selection
```bash
--skip-slow                  # Skip time-consuming tests
--skip-api                   # Skip API-dependent tests (use mock data)
--skip-performance           # Skip performance benchmarks
--category CATEGORY          # Run only specific category
```

### Quality Requirements
```bash
--min-pass-rate PERCENT      # Minimum pass rate for success (default: 75%)
--max-failures N             # Maximum allowed failures (default: 5)
```

### Output Configuration
```bash
--quiet                      # Reduce verbosity
--no-progress               # Disable progress indicators
--no-save                   # Don't save results to file
--results-file FILENAME     # Custom results filename
```

### Custom Test Data
```bash
--problematic-artists LIST  # Comma-separated artist list for real tests
--max-candidates N          # Max candidates per test (default: 5)
```

## Example Usage Scenarios

### 1. Development Testing (Fast)
```bash
# Quick validation during development
python manual_test_suite_a2.py --quick --skip-api --quiet
```

### 2. Performance Validation
```bash
# Strict performance requirements
python manual_test_suite_a2.py --category performance \
  --perf-iterations 10 --max-time 0.3 --batch-time 0.5
```

### 3. Production Readiness Check
```bash
# High-quality standards for production
python manual_test_suite_a2.py \
  --min-pass-rate 95 --max-failures 2 \
  --mbid-confidence 0.98 --track-confidence 0.90
```

### 4. API-Free Testing
```bash
# Testing without external dependencies
python manual_test_suite_a2.py --skip-api --skip-slow
```

### 5. Custom Artist Testing
```bash
# Test specific problematic artists
python manual_test_suite_a2.py --category real \
  --problematic-artists "*LUNA,YOASOBI,NewJeans,BTS,Taylor Swift"
```

### 6. Edge Case Focus
```bash
# Focus on robustness and error handling
python manual_test_suite_a2.py --category edge \
  --max-time 2.0  # Allow more time for edge cases
```

### 7. Unicode/International Testing
```bash
# Focus on international character handling
python manual_test_suite_a2.py --category unicode --verbose
```

## Understanding Results

### Pass Rate Assessment
- **95%+**: Excellent - Production ready
- **90-94%**: Very Good - Minor issues only
- **75-89%**: Good - Meets default threshold
- **60-74%**: Moderate - Below threshold, review needed
- **<60%**: Poor - Major issues requiring fixes

### Confidence Score Interpretation
- **0.95-1.00**: MBID matches (definitive)
- **0.85-0.94**: Strong track evidence
- **0.70-0.84**: Track-based verification
- **0.50-0.69**: Weak heuristic matches
- **<0.50**: Poor matches (problematic)

### Verification Methods
- **MBID_MATCH**: Perfect identification via MusicBrainz ID
- **STRONG_TRACK_MATCH**: High confidence from track evidence
- **TRACK_BASED**: Moderate confidence from track matching
- **HEURISTIC_BASED**: Fallback to name/listener heuristics

## Output Files

### Results File Structure
```json
{
  "config": {
    "data_path": "lastfm_data.csv",
    "mbid_min_confidence": 0.95,
    "track_strong_min_confidence": 0.85,
    // ... all configuration parameters
  },
  "results": {
    "passed": 45,
    "failed": 2,
    "skipped": 3,
    "details": [
      {
        "test": "Perfect MBID Match",
        "passed": true,
        "error": null
      }
      // ... individual test results
    ]
  }
}
```

## Troubleshooting

### Common Issues

#### "No candidates found"
- Check API connectivity with `--skip-api` to use mock data
- Verify artist names exist in your dataset

#### Performance test failures
- Adjust thresholds: `--max-time 1.0 --batch-time 2.0`
- Check system load during testing

#### Unicode test failures
- Ensure data file encoding is UTF-8
- Check font support for international characters

#### Low confidence scores
- Review `--improvement-threshold` setting
- Check if artists exist in your listening history

### Debug Mode
```bash
# Verbose output with progress tracking
python manual_test_suite_a2.py --category track --no-quiet --show-progress
```

## Best Practices

1. **Start with Quick Tests**: Use `--quick` for rapid validation
2. **Iterative Testing**: Test individual categories during development
3. **Baseline Performance**: Run performance tests on clean system
4. **Save Results**: Keep results files for regression testing
5. **Custom Thresholds**: Adjust confidence thresholds based on your data quality
6. **API Management**: Use `--skip-api` during development to avoid rate limits

## Integration with CI/CD

```bash
# Automated testing script
#!/bin/bash
set -e

echo "Running Phase A.2 Verification Tests..."

# Quick smoke test
python manual_test_suite_a2.py --quick --skip-api --min-pass-rate 90

# Performance regression test  
python manual_test_suite_a2.py --category performance --max-time 0.5

# Full test suite (if time allows)
if [ "$FULL_TEST" = "true" ]; then
  python manual_test_suite_a2.py --min-pass-rate 85
fi

echo "All tests passed!"
```

This comprehensive test suite ensures your Phase A.2 artist verification system is robust, performant, and ready for production use.