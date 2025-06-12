# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Role & Mindset

- You are a highly skilled software engineer, not just a code generator.
- You are also a senior product manager who understand products from the end-user/customer's perspectives.
- Think critically: evaluate design patterns, edge cases, scalability, maintainability, and trade-offs.
- Treat security as a top priority; prevent vulnerabilities like SQL injection, command injection, insecure deserialization, and excessive privilege.
- If a feature becomes too diffcult to implement or reason, break down features into smaller, testable parts.
- If a problem is complex, decompose it into independent, testable components and assemble them later (like building a car).
- Be opinionated: call out smells, anti-patterns, and risks. Justify your stance.
- If you are unclear about something, always ask clarifying questions instead of guessing.

### A few other principles to follow

- KISS: Keep it simple, stupid.
- DRY: Don't repeat yourself.
- Separation of Concerns: Split responsibilities cleanly (UI, logic, data, etc.).
- Fail Fast: Test early and detect problems early. Don't spill out 500 lines of code and find out they're broken afterward.
- Graceful Degradation: Fail safely without causing cascading system crashes.
- Observability First: Prioritize logs, metrics, tracing, and monitoring. Output meaningful logs throughout the application with appropriate log levels.

## Commands

### Running the Application
```bash
# Set encoding for foreign characters (required)
export PYTHONIOENCODING=utf-8  # Linux/macOS
set PYTHONIOENCODING=utf-8     # Windows CMD
$env:PYTHONIOENCODING="utf-8"  # Windows PowerShell

# Run the main animation
python main_animator.py
```

### Dependencies
```bash
# Install required packages
pip install -r requirements.txt

# Ensure FFmpeg is installed and in PATH (required for video output)
ffmpeg -version

# Verify required environment variables for Spotify API (if using Spotify source)
echo $SPOTIFY_CLIENT_ID
echo $SPOTIFY_CLIENT_SECRET
```

### Testing Components
```bash
# Run full test suite for all functionality
python test_phases_1_2.py

# Interactive testing menu
python quick_test.py

# Test specific components
python data_processor.py
python config_loader.py
python nightingale_chart.py

# Test specific functionality via command line
python quick_test.py config          # Test configuration
python quick_test.py data            # Test data processing  
python quick_test.py artist "Taylor Swift"  # Test artist photos
python quick_test.py cache           # View cache files

# Test title positioning
python test_title_positioning.py
python test_title_config.py
python test_title_render.py
```

### Mode Switching
```bash
# Switch between visualization modes
python switch_mode.py artists        # Switch to artists mode
python switch_mode.py tracks         # Switch to tracks mode
python switch_mode.py               # Interactive mode selection
```

### Network Analysis
```bash
# Generate artist similarity networks from listening data
python network_utils.py              # Direct network analysis
python tests/test_network_analysis.py # Test network functionality
python tests/test_full_network_robust.py # Comprehensive network tests

# Test specific network features
python tests/test_similarity_visualization.py  # Test similarity visualization
python tests/manual_test_network.py          # Manual network testing
```

## Architecture

### Core Components

**main_animator.py**: Main entry point that orchestrates the entire visualization pipeline:
- Loads configuration from `configurations.txt`
- Processes data through `data_processor.py`
- Fetches album art via `album_art_utils.py`
- Generates animated bar chart race video using matplotlib

**data_processor.py**: Handles data ingestion and transformation:
- Supports both Spotify JSON and Last.fm CSV data sources
- Normalizes artist/track names for consistency
- Creates time-indexed DataFrames for smooth animation
- Generates rolling window statistics (7-day/30-day top tracks)

**config_loader.py**: Configuration management system:
- Loads settings from `configurations.txt` using ConfigParser
- Provides type-safe getters (get_int, get_bool, get_list)
- All major application behavior is configurable

**album_art_utils.py**: Album art and metadata handling:
- Spotify API integration for high-quality album covers
- Caches downloaded images and dominant colors
- Handles multiple cache layers for performance

**rolling_stats.py**: Rolling window statistics computation:
- Calculates top tracks for 7-day and 30-day windows
- Provides data-only logic (no Matplotlib dependencies) for reusability
- Supports configurable aggregation frequencies

**nightingale_chart.py**: Nightingale rose chart visualization:
- Renders animated polar charts showing listening activity over time
- Supports smooth transitions and easing animations
- Integrates with main animation pipeline

**text_utils.py**: Text rendering and typography utilities:
- Handles font selection and international character support
- Text truncation and positioning logic

**time_aggregation.py**: Time-based data aggregation:
- Frame aggregation by time periods (daily, weekly, monthly)
- Reduces computational load for long time series

**network_utils.py**: Artist similarity network analysis:
- Creates artist relationship networks based on listening patterns and Last.fm similarity data
- Calculates co-listening scores using temporal proximity of plays
- Integrates Last.fm API for artist similarity relationships
- Generates JSON network data for visualization (nodes and edges)
- Supports filtering by play count thresholds and top N artists

**lastfm_utils.py**: Last.fm API integration:
- Fetches artist similarity data from Last.fm API
- Provides caching mechanism for API responses
- Rate limiting to respect API quotas
- Supports artist metadata and similar artist lookups

### Data Flow

1. Configuration loaded from `configurations.txt`
2. Raw data ingested (Spotify JSON or Last.fm CSV)
3. Data cleaned, normalized, and filtered by timeframe
4. Album art pre-fetched for songs appearing in race
5. Time-series DataFrame created with cumulative play counts
6. Animation frames generated in parallel
7. Final video compiled using FFmpeg

### Key Configuration

All behavior is controlled through `configurations.txt`:
- **DataSource**: Choose between Spotify (`SOURCE = spotify`) or Last.fm (`SOURCE = lastfm`)
- **VisualizationMode**: Choose between tracks (`MODE = tracks`) or artists (`MODE = artists`) visualizations
- **Timeframe**: Filter data by date range
- **AnimationOutput**: Video resolution, FPS, frame aggregation
- **AlbumArtSpotify**: API credentials and caching settings
- **RollingStats**: 7/30-day window calculations
- **NightingaleChart**: Enable/disable and configure the polar chart visualization
- **RollingStatsDisplay**: Layout and styling for rolling statistics panels
- **LastfmAPI**: API credentials and configuration for artist similarity data (optional)

### Performance Features

- **Frame Aggregation**: Use `FRAME_AGGREGATION_PERIOD` to reduce frame count (D/W/M for daily/weekly/monthly)
- **Parallel Processing**: Multi-core frame generation controlled by `MAX_PARALLEL_WORKERS`
- **Multiple Cache Layers**: Album art, dominant colors, Spotify metadata, and MusicBrainz data
- **GPU Encoding**: NVENC support if available

### Font Handling

The application supports international characters through multiple font fallbacks defined in `PREFERRED_FONTS`. Font files are stored in the `fonts/` directory and include Unicode support for Japanese, Korean, and Chinese characters.

### Visualization Components

The application generates a comprehensive animated visualization with multiple elements:

- **Main Bar Chart Race**: Horizontal bars showing top tracks/artists over time with album art or artist photos
- **Rolling Statistics Panels**: Side panels displaying current 7-day and 30-day top tracks/artists
- **Nightingale Rose Chart**: Optional polar chart showing listening activity patterns over time periods
- **Timestamp Display**: Current date/time indicator synchronized with data

### Visualization Modes

The application supports two distinct visualization modes:

- **Tracks Mode**: Shows individual songs over time with album artwork and track-specific rolling statistics
- **Artists Mode**: Shows artists over time with artist profile photos (fallback to most popular track's album art) and artist-specific rolling statistics

All visualization elements are fully configurable through `configurations.txt` and support smooth animations, parallel frame generation, and multiple output formats.

### Artist Network Analysis

The application includes sophisticated network analysis capabilities for understanding artist relationships:

- **Co-listening Analysis**: Identifies artists frequently played together by analyzing temporal proximity of plays (configurable time windows)
- **Last.fm Integration**: Fetches official artist similarity scores from Last.fm API to complement listening patterns
- **Network Generation**: Creates weighted graphs combining both co-listening patterns and external similarity data
- **Export Formats**: Generates JSON network data files suitable for visualization tools (D3.js, Gephi, etc.)
- **Configurable Filtering**: Supports minimum play count thresholds, top N artist limits, and relationship strength filters

#### Network Data Structure

Generated network files contain:
- **Nodes**: Artists with play counts, rankings, and metadata
- **Edges**: Relationships with weights combining Last.fm similarity (70%) and co-listening scores (30%)
- **Metadata**: Generation timestamps, parameters used, and network statistics
- **Relationship Types**: Classified as 'lastfm_only', 'colistening_only', or 'both'

## Data Sources

### Spotify Data Format
The application expects Spotify extended streaming history in JSON format:
- Files named like `StreamingHistory*.json` or specify exact filename in config
- Each entry contains: `ts` (timestamp), `artistName`, `trackName`, `msPlayed`
- Minimum play time filtering available via `MIN_MS_PLAYED_FOR_COUNT`

### Last.fm Data Format  
Alternative data source using CSV export from Last.fm:
- File should be named `lastfm_data.csv` (UTF-8 encoded)
- Contains listening history with timestamps and track metadata
- Available from https://lastfm.ghan.nl/export/

### Last.fm API Configuration
For network analysis, Last.fm API credentials can be configured:
- API key and secret required for similarity data fetching
- Configurable cache directory (`lastfm_cache/`) with 30-day expiry
- Rate limiting (200ms between requests) to respect API quotas
- Automatic retry logic and error handling for API failures

## Common Issues & Solutions

### Character Encoding
- Always set `PYTHONIOENCODING=utf-8` before running
- Font files in `fonts/` directory support international characters
- OS-specific font loading can be enabled in config

### Performance Optimization
- Use `FRAME_AGGREGATION_PERIOD = D` (daily) or higher for long time series
- Adjust `MAX_PARALLEL_WORKERS` based on available CPU cores
- Enable `CLEANUP_INTERMEDIATE_FRAMES = True` to save disk space

### Album Art Issues
- Ensure Spotify API credentials are properly configured
- Check cache directories have write permissions
- Album art cache stored in `album_art_cache/` with multiple JSON metadata files
- Artist photos cache stored in `artist_art_cache/` directory for artists mode

### Network Analysis Issues
- **Last.fm API Limits**: API has rate limits (200 requests per hour), network generation for large artist lists may take time
- **Cache Management**: Network cache files can become large; periodically clean `lastfm_cache/` directory
- **Data Quality**: Co-listening scores depend on temporal proximity; adjust `time_window_hours` parameter for different listening patterns
- **Missing Relationships**: Not all artists have Last.fm similarity data; network will be sparser for less popular artists