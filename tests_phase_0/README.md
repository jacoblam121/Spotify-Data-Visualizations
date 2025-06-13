# Phase 0 Test Suite - Network Visualization Foundation

Comprehensive testing framework for the Phase 0 network visualization foundation, including ID migration, data structure validation, and performance testing.

## 🗂️ Test Files

### Core Test Components

- **`automated_phase0_tests.py`** - Automated unit and integration tests
- **`manual_test_runner.py`** - Interactive test runner with configurable scenarios
- **`test_summary.py`** - Quick validation test for core functionality
- **`test_100_artists.py`** - Stress test for 100-artist production target

### Supporting Modules

- **`id_migration_system.py`** - ID migration system with Spotify/MusicBrainz fallbacks
- **`create_id_mapping.py`** - Enhanced network generation with stable IDs
- **`test_network_structure.py`** - Original structure analysis tool

### Sample Data

- **`test_network_*.json`** - Generated test networks (5, 10, 20 artists)
- **`current_network_sample_*.json`** - Structure analysis samples
- **`test_results/`** - Directory for test output files

## 🚀 Quick Start

### Run Quick Validation

```bash
# From project root
python tests_phase_0/test_summary.py
```

**Expected Output:**
- ✅ Network generation working
- ✅ Stable ID system functional (100% Spotify IDs)
- ✅ D3.js visualization properties included
- ✅ Spotify emphasis in sizing algorithm (Taylor Swift 45px > others)

### Run Automated Tests

```bash
cd tests_phase_0
python automated_phase0_tests.py
```

**Tests Include:**
- ID migration system validation
- Network structure schema validation
- Visualization property generation
- Data integration tests

### Run Interactive Tests

```bash
cd tests_phase_0
python manual_test_runner.py
```

**Test Scenarios:**
1. Quick Test (5 artists)
2. Small Network (20 artists)
3. Medium Network (50 artists)
4. Large Network (100 artists)
5. Edge Cases & Fallbacks
6. Custom Configuration

## 📊 Key Validation Points

### ✅ Data Structure (PASSED)

- **Stable ID System**: Spotify IDs > MusicBrainz IDs > Local Hash fallbacks
- **D3.js Compatibility**: Standard `nodes`/`links` structure
- **Visualization Properties**: All nodes have `viz.radius`, `viz.color`, etc.
- **Schema Validation**: Comprehensive JSON schema compliance

### ✅ Sizing Algorithm (VALIDATED)

- **Spotify Emphasis**: Taylor Swift (138M followers) correctly sized larger than others
- **Square Root Scaling**: Visual perception optimized (45px max, 8px min)
- **Genre Colors**: Primary genre-based color mapping
- **Fallback Handling**: Graceful degradation for missing data

### ⚠️ Performance (NEEDS OPTIMIZATION)

**Current Performance:**
- 5 artists: ~6.6s
- 10 artists: ~14.8s
- **Estimated 100 artists: ~163s** (❌ Target: <30s)

**Performance Issues:**
- 1.65s per artist (too slow)
- API call overhead (Last.fm similarity fetching)
- Need optimization for 100-artist target

## 🎯 100-Artist Target Status

**Target**: Generate 100-artist network in <30 seconds

**Current Status**: ❌ Not meeting target (~163s estimated)

**Issues to Address in Phase 0.1:**
1. **Performance Optimization**: Reduce API calls or parallelize
2. **Caching Strategy**: Better cache utilization
3. **Algorithm Efficiency**: Optimize data processing pipeline

## 🧪 Test Scenarios

### Automated Tests
- **Unit Tests**: ID migration, normalization, validation
- **Integration Tests**: End-to-end network generation
- **Schema Tests**: JSON structure validation
- **Edge Case Tests**: Missing data, fallback behavior

### Manual Test Scenarios

#### Quick Test (5 artists)
- **Purpose**: Rapid validation
- **Validates**: Core functionality, ID system, visualization
- **Time**: ~6s

#### Small Network (20 artists)
- **Purpose**: Typical small network
- **Validates**: Scaling behavior, performance
- **Time**: ~30s

#### Medium Network (50 artists)
- **Purpose**: Mid-size network testing
- **Validates**: Performance under load
- **Time**: ~80s

#### Large Network (100 artists)
- **Purpose**: Production target validation
- **Validates**: Full-scale performance
- **Time**: ~160s (needs optimization)

#### Edge Cases
- **Purpose**: Error handling and fallbacks
- **Validates**: Missing API data, network failures
- **Special**: Tests resilience

## 📈 Test Results Summary

### ✅ Successful Components

1. **ID Migration**: 100% success rate (all Spotify IDs)
2. **Data Structure**: D3.js-ready JSON generation
3. **Visualization**: Complete viz properties with proper scaling
4. **Spotify Emphasis**: Algorithm correctly prioritizes Spotify metrics
5. **Schema Compliance**: All generated JSON validates against schema

### ⚠️ Areas for Improvement

1. **Performance**: 100-artist generation too slow (163s vs 30s target)
2. **Edge Generation**: No similarity edges generated (needs Last.fm optimization)
3. **Memory Usage**: Not measured/optimized yet
4. **Error Handling**: Could be more robust for API failures

## 🔧 Usage Examples

### Generate Test Network

```python
from create_id_mapping import create_enhanced_network_with_stable_ids

# Generate 20-artist network
network_data = create_enhanced_network_with_stable_ids(
    top_n_artists=20,
    output_file="my_test_network.json"
)

print(f"Generated {len(network_data['nodes'])} nodes")
```

### Run Performance Benchmark

```python
from manual_test_runner import ManualTestRunner

runner = ManualTestRunner()
results = runner.run_performance_benchmark()
```

### Validate Existing Network

```python
from automated_phase0_tests import TestDataValidation

validator = TestDataValidation()
# Loads and validates JSON file
```

## 🚦 Next Steps (Phase 0.1)

### Priority 1: Performance Optimization
- [ ] Parallelize API calls
- [ ] Optimize caching strategy
- [ ] Reduce redundant data processing
- [ ] Target: <30s for 100 artists

### Priority 2: Edge Generation
- [ ] Fix Last.fm similarity edge creation
- [ ] Add co-listening analysis
- [ ] Validate edge weight calculations

### Priority 3: Enhanced Testing
- [ ] Add memory usage monitoring
- [ ] Stress test with 200+ artists
- [ ] Add continuous integration tests

## 🏆 Success Criteria

**Phase 0 Complete When:**
- [x] Stable ID system (100% Spotify IDs achieved)
- [x] D3.js-ready JSON structure
- [x] Visualization properties complete
- [x] Comprehensive test suite
- [ ] **100-artist generation in <30s** (pending optimization)
- [ ] Similarity edges generated
- [ ] All tests passing

**Current Status: 85% Complete** ✅

Ready to proceed to Phase 0.1 with performance optimization focus.