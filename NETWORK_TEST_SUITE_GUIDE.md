# Comprehensive Network Test Suite Guide

## Overview

The Comprehensive Network Test Suite is a complete testing framework for artist similarity networks that integrates with the improved Phase A.2 artist verification system. It provides robust testing of network generation, visual properties, similarity relationships, and data persistence.

## Features

### ✨ Core Capabilities
- **Multi-API Integration**: Tests Last.fm similarity with verified artist data
- **Visual Property Validation**: Tests node colors, sizes, and glow values
- **Network Persistence**: Saves networks in JSON and GraphML formats
- **Individual Connection Analysis**: Deep-dive analysis of specific artists
- **Cross-Validation**: Tests similarity symmetry and relationship quality
- **Comprehensive Metrics**: Last.fm listeners, Spotify popularity, user engagement

### 🔧 Configuration Options
- **Highly Configurable**: All parameters customizable via code or YAML
- **Multiple Test Scenarios**: Quick tests, deep analysis, genre-focused
- **Visual Property Ranges**: Configurable node sizes, glow values, colors
- **Performance Controls**: Rate limiting, API call limits, batch sizes

### 📊 Testing Categories
1. **Artist Verification**: Uses Phase A.2 system for robust artist identification
2. **Network Generation**: Creates similarity networks with verified artists
3. **Visual Properties**: Validates node sizes, colors, and glow based on metrics
4. **Similarity Symmetry**: Checks for consistent bidirectional relationships
5. **Data Persistence**: Tests saving/loading networks in multiple formats
6. **Individual Connections**: Analyzes specific artist similarity networks

## Quick Start

### Basic Usage

```bash
# Run quick test with default configuration
python comprehensive_network_test_suite.py --quick

# Analyze connections for a specific artist
python comprehensive_network_test_suite.py --artist "YOASOBI" --connections

# Use custom configuration
python comprehensive_network_test_suite.py --config network_test_config.yaml
```

### Demo Script

```bash
# Run all demos to see capabilities
python demo_network_test_suite.py
```

## Configuration

### Code-Based Configuration

```python
from comprehensive_network_test_suite import NetworkTestConfig, ComprehensiveNetworkTestSuite

# Create configuration
config = NetworkTestConfig(
    top_n_artists=20,
    seed_artists=["YOASOBI", "IVE", "BTS"],
    similarity_threshold=0.3,
    data_path="lastfm_data.csv",
    save_networks=True
)

# Run test suite
suite = ComprehensiveNetworkTestSuite(config)
suite.run_full_suite()
```

### YAML Configuration

```yaml
# network_test_config.yaml
default_params:
  top_n_artists: 25
  similarity_threshold: 0.3
  seed_artists: ["YOASOBI", "IVE", "BTS"]
  
test_config:
  test_verification: true
  test_visual_properties: true
  save_networks: true
```

## Visual Properties

The test suite validates and generates visual properties for network nodes:

### Node Size
- **Based on**: Last.fm listeners + user play count
- **Range**: Configurable (default: 5.0 - 30.0)
- **Formula**: Combines popularity (70%) and user engagement (30%)

### Glow Value
- **Based on**: Verification confidence + popularity
- **Range**: Configurable (default: 0.1 - 1.0)
- **Formula**: High confidence + high popularity = more glow

### Node Colors
- **#FF6B6B** (Red): High personal engagement
- **#4ECDC4** (Teal): Medium engagement
- **#45B7D1** (Blue): Low engagement
- **#96CEB4** (Green): Popular but low personal engagement
- **#808080** (Gray): No user plays

## Network File Formats

### JSON Format
```json
{
  "nodes": [
    {
      "id": "YOASOBI",
      "display_name": "yoasobi", 
      "lastfm_listeners": 713328,
      "spotify_popularity": 85,
      "user_plays": 30,
      "node_size": 18.5,
      "glow_value": 0.85,
      "color": "#FF6B6B",
      "verification_confidence": 0.950,
      "verification_method": "STRONG_TRACK_MATCH"
    }
  ],
  "edges": [
    {
      "source": "YOASOBI",
      "target": "IVE",
      "similarity": 0.65,
      "source": "lastfm",
      "weight": 0.65
    }
  ],
  "metadata": {
    "generated_at": "2025-01-14T10:30:00",
    "config": {...},
    "metrics": {
      "node_count": 20,
      "edge_count": 45,
      "density": 0.237
    }
  }
}
```

### GraphML Format
- Compatible with Gephi, Cytoscape, and other network analysis tools
- Preserves all node and edge attributes
- Includes metadata as graph properties

## Individual Artist Analysis

Analyze all connections for a specific artist:

```bash
# Analyze YOASOBI's connections from saved network
python comprehensive_network_test_suite.py --artist "YOASOBI" --connections --network-file "results/network.json"

# Output shows:
# - Artist metadata (listeners, popularity, verification details)
# - All connections sorted by similarity
# - Visual properties (size, glow, color)
# - Network statistics
```

## Test Scenarios

### Quick Test (--quick)
- **Artists**: 10
- **Seeds**: ["YOASOBI", "IVE"]
- **Purpose**: Fast validation of basic functionality

### K-pop Focus
```yaml
scenarios:
  kpop_focus:
    top_n_artists: 25
    seed_artists: ["IVE", "BTS", "YOASOBI", "NewJeans"]
    similarity_threshold: 0.25
```

### Deep Analysis
```yaml
scenarios:
  deep_analysis:
    top_n_artists: 100
    seed_artists: ["Radiohead", "The Beatles", "Pink Floyd"]
    similarity_threshold: 0.15
    max_api_calls_per_artist: 20
```

## Integration with Phase A.2

The test suite leverages the improved artist verification system:

### Verification Methods Tested
- **MBID_MATCH**: Highest confidence via MusicBrainz IDs
- **STRONG_TRACK_MATCH**: High confidence via track matching
- **TRACK_BASED**: Medium confidence via track evidence
- **HEURISTIC_BASED**: Fallback using similarity heuristics

### Case-Insensitive Matching
- Handles artist name variations (*Luna vs *LUNA)
- Tests adaptive thresholds for different data sizes
- Validates robust artist identification

## Performance Features

### Rate Limiting
- Configurable delays between API calls
- Respects Last.fm API quotas
- Batch processing for efficiency

### Caching
- Leverages Last.fm cache system
- Reuses verification results
- Minimizes redundant API calls

### Error Handling
- Graceful degradation on API failures
- Detailed error reporting
- Continuation after non-critical failures

## Output and Reports

### Test Results
- Pass/fail status for each test category
- Success rates and performance metrics
- Detailed error and warning logs

### Generated Artifacts
- Network files (JSON, GraphML)
- Test reports (JSON)
- Visual property analysis
- Similarity relationship breakdowns

### Directory Structure
```
network_test_results/
├── comprehensive_network_20250114_103000.json
├── comprehensive_network_20250114_103000.graphml
├── test_report_20250114_103000.json
└── analysis_reports/
```

## Troubleshooting

### Common Issues

**No MBID data found**
- Expected for Spotify data source
- Test automatically skips MBID validation for Spotify

**Artist not found in user data**
- Check spelling and case sensitivity
- Verify artist exists in listening history
- Use case-insensitive matching

**Low similarity connections**
- Adjust similarity_threshold (try 0.2 or 0.15)
- Increase top_n_artists for more potential connections
- Check Last.fm API coverage for specific artists

**Rate limiting errors**
- Increase rate_limit_delay (try 0.3-0.5 seconds)
- Reduce max_api_calls_per_artist
- Check Last.fm API quota usage

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Extension Points

### Custom Visual Properties
Extend `_calculate_node_color()`, `_calculate_node_size()`, `_calculate_glow_value()` methods for custom visual mapping.

### Additional APIs
Add new similarity sources by extending `_add_similarity_edges()` method.

### Custom Metrics
Add business-specific metrics in node/edge attributes.

### Export Formats
Add support for additional network formats (GEXF, Pajek, etc.).

## Best Practices

1. **Start Small**: Use quick tests before running large-scale analysis
2. **Verify Artists**: Check verification results before trusting similarity data
3. **Save Networks**: Always save networks for later analysis and comparison
4. **Monitor APIs**: Watch for rate limiting and quota issues
5. **Validate Visuals**: Check that visual properties make intuitive sense
6. **Cross-Reference**: Compare results with manual Last.fm browsing

## Requirements

- Python 3.8+
- Last.fm API credentials configured
- Artist verification system (Phase A.2)
- User listening data (Last.fm CSV or Spotify JSON)
- Optional: PyYAML for configuration files

## Related Files

- `comprehensive_network_test_suite.py` - Main test suite
- `demo_network_test_suite.py` - Demo and usage examples
- `network_test_config.yaml` - Sample configuration
- `artist_verification.py` - Phase A.2 verification system
- `lastfm_utils.py` - Last.fm API integration
- `network_utils.py` - Core network analysis utilities