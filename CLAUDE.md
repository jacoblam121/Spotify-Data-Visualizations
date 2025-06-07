# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
# Test data processing
python data_processor.py

# Test configuration loading
python config_loader.py

# Test nightingale chart rendering
python nightingale_chart.py

# Test specific title positioning
python test_title_positioning.py
python test_title_config.py
python test_title_render.py
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
- **Timeframe**: Filter data by date range
- **AnimationOutput**: Video resolution, FPS, frame aggregation
- **AlbumArtSpotify**: API credentials and caching settings
- **RollingStats**: 7/30-day window calculations
- **NightingaleChart**: Enable/disable and configure the polar chart visualization
- **RollingStatsDisplay**: Layout and styling for rolling statistics panels

### Performance Features

- **Frame Aggregation**: Use `FRAME_AGGREGATION_PERIOD` to reduce frame count (D/W/M for daily/weekly/monthly)
- **Parallel Processing**: Multi-core frame generation controlled by `MAX_PARALLEL_WORKERS`
- **Multiple Cache Layers**: Album art, dominant colors, Spotify metadata, and MusicBrainz data
- **GPU Encoding**: NVENC support if available

### Font Handling

The application supports international characters through multiple font fallbacks defined in `PREFERRED_FONTS`. Font files are stored in the `fonts/` directory and include Unicode support for Japanese, Korean, and Chinese characters.

### Visualization Components

The application generates a comprehensive animated visualization with multiple elements:

- **Main Bar Chart Race**: Horizontal bars showing top tracks over time with album art
- **Rolling Statistics Panels**: Side panels displaying current 7-day and 30-day top tracks
- **Nightingale Rose Chart**: Optional polar chart showing listening activity patterns over time periods
- **Timestamp Display**: Current date/time indicator synchronized with data

All visualization elements are fully configurable through `configurations.txt` and support smooth animations, parallel frame generation, and multiple output formats.

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