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
```

### Testing Components
```bash
# Test data processing
python data_processor.py

# Test configuration loading
python config_loader.py
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

### Performance Features

- **Frame Aggregation**: Use `FRAME_AGGREGATION_PERIOD` to reduce frame count (D/W/M for daily/weekly/monthly)
- **Parallel Processing**: Multi-core frame generation controlled by `MAX_PARALLEL_WORKERS`
- **Multiple Cache Layers**: Album art, dominant colors, Spotify metadata, and MusicBrainz data
- **GPU Encoding**: NVENC support if available

### Font Handling

The application supports international characters through multiple font fallbacks defined in `PREFERRED_FONTS`. Font files are stored in the `fonts/` directory and include Unicode support for Japanese, Korean, and Chinese characters.