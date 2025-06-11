# Spotify Data Visualizations

I'll manually update with more specific instructions and more detailed explanations of how it works later when I finish the full project. 
This program creates animated bar chart "race" videos from your Spotify or Last.fm listening history. 


## Top Tracks Demo
[![Top Tracks](https://img.youtube.com/vi/M-diXuEgmPo/hqdefault.jpg)](https://www.youtube.com/watch?v=M-diXuEgmPo)
## Top Artists Demo
[![Top Artists](https://img.youtube.com/vi/jVZtuSqZK3Q/hqdefault.jpg)](https://www.youtube.com/watch?v=jVZtuSqZK3Q)

## Features

### Two Bar Graph Modes
- **Tracks Mode**: Animated bar chart race of your top songs with album covers
- **Artists Mode**: Animated bar chart race of your top artists with profile photos
  
### Flexible Data Sources
- **Spotify Extended Streaming History**: Direct JSON import from Spotify data export
- **Last.fm Data**: CSV export from Last.fm listening history
- **Flexible Time Filtering**: Analyze any date range or your entire listening history

### Multiple Visual Elements
- **Rolling Statistics Panels**: Live 7-day and 30-day top tracks/artists
- **Nightingale Rose Chart**: Optional polar chart showing monthly listening patterns
- **Dynamic Timestamp Display**: Real-time date progression during animation

### Performance & Quality
- **Multiple Resolutions**: 1080p and 4K output options (1080p currently bugged, use 4k)
- **Frame Aggregation (Sampling Rate)**: Reduce render time with daily/weekly/monthly sampling
- **Parallel Processing**: Multi-core frame generation for faster rendering
- **GPU Encoding**: NVENC support for hardware-accelerated video encoding
- **Smart Caching**: Multiple cache layers for artwork, metadata, and colors

### Prerequisites/Requirements

1. **FFmpeg** (required for video output)
   ```bash
   # Install FFmpeg and add to PATH
   # Download from https://ffmpeg.org
   
2. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Spotify API Credentials** (for artwork fetching)
   - My API key is currently in here, but you should get your own API key and add to `configurations.txt`

### Data Preparation

#### Option 1: Spotify Data
1. Request your [Spotify Extended Streaming History](https://www.spotify.com/account/privacy/) (Make sure to request extended streaming history, not the 1 year one)
2. Merge json files into one file, and add to project directory (name it spotify_data.json)
   You can use this script I've made here https://github.com/jacoblam121/merge-json

#### Option 2: Last.fm Data
1. Export your data from [Last.fm Export Tool](https://lastfm.ghan.nl/export/)
2. Add to project directory (name it lastfm_data.csv)

### Running the Application

```bash
# Set encoding for international characters (required)
export PYTHONIOENCODING=utf-8  # Linux/macOS
set PYTHONIOENCODING=utf-8     # Windows CMD
$env:PYTHONIOENCODING="utf-8"  # Windows PowerShell

# Run the main animation
python main_animator.py
```

## Project Structure

```
Spotify-Data-Visualizations/
├── Core Application Files
│   ├── main_animator.py              # Main application entry point
│   ├── data_processor.py             # Data ingestion and transformation
│   ├── config_loader.py              # Configuration management
│   ├── album_art_utils.py            # Spotify API integration & artwork
│   ├── rolling_stats.py              # Rolling window statistics
│   ├── nightingale_chart.py          # Polar chart visualization
│   ├── text_utils.py                 # Text rendering and fonts
│   ├── time_aggregation.py           # Frame aggregation logic
│   └── switch_mode.py                # Mode switching utility
│
├── Testing
│   ├── tests/
│   │   ├── test_phases_1_2.py        # Full test suite
│   │   ├── quick_test.py             # Interactive testing
│   │   ├── test_*.py                 # Component-specific tests
│   │   └── TESTING_GUIDE.md          # Comprehensive testing guide
│   └── summaries/                    # Implementation summaries
│
├── Configuration & Data
│   ├── configurations.txt            # Main configuration file
│   ├── requirements.txt              # Python dependencies
│   ├── spotify_data.json             # Your Spotify data (not included)
│   ├── lastfm_data.csv              # Your Last.fm data (not included)
│   └── CLAUDE.md                     # Development guidance
│
├── Assets & Cache
│   ├── fonts/                        # International font files
│   │   ├── DejaVuSans.ttf
│   │   ├── NotoSansJP-Regular.ttf    # Japanese support
│   │   ├── NotoSansKR-Regular.ttf    # Korean support
│   │   └── ...                       # Other Unicode fonts
│   ├── album_art_cache/              # Album artwork cache
│   │   ├── *.jpg                     # Downloaded album covers
│   │   ├── spotify_info_cache.json   # Track/album metadata
│   │   ├── dominant_color_cache.json # Artwork color analysis
│   │   └── negative_cache.json       # Failed searches
│   └── artist_art_cache/             # Artist photos cache
│       ├── artist_*.jpg              # Artist profile photos
│       ├── spotify_artist_cache.json # Artist metadata
│       └── artist_dominant_color_cache.json
│
├── Output & Temporary Files
│   ├── *.mp4                         # Generated video files
│   │   ├── spotify_top_songs_race_4k.mp4
│   │   └── spotify_top_artists_race_4k.mp4
│   ├── temp_frames_*/                # Intermediate frame images
│   │   └── frame_*.png               # Individual animation frames
│   └── venv/                         # Python virtual environment
│
└── Documentation
    ├── README.md                     # This file
    └── bashrc                        # Shell configuration example
```

## Configuration

All settings are controlled through `configurations.txt`:

### Essential Settings
```ini
[DataSource]
SOURCE = spotify                    # "spotify" or "lastfm"
INPUT_FILENAME_SPOTIFY = spotify_data.json

[VisualizationMode]
MODE = tracks                       # "tracks", "artists", or "both"

[Timeframe]
START_DATE = 2024-01-01            # YYYY-MM-DD or "all_time"
END_DATE = 2024-12-31              # YYYY-MM-DD or "all_time"

[AnimationOutput]
RESOLUTION = 4k                     # "1080p" or "4k"
N_BARS = 10                        # Number of tracks/artists to show
TARGET_FPS = 30                    # Video frame rate
FRAME_AGGREGATION_PERIOD = W       # D/W/M for daily/weekly/monthly
```

### Performance Optimization
```ini
[AnimationOutput]
MAX_PARALLEL_WORKERS = 0           # 0 = auto-detect CPU cores
CLEANUP_INTERMEDIATE_FRAMES = True # Save disk space
USE_NVENC_IF_AVAILABLE = True      # GPU encoding

# Frame aggregation reduces render time significantly:
# 'event' = Every play event (original, slowest)
# 'D' = Daily (fast)
# 'W' = Weekly (faster)  
# 'M' = Monthly (fastest)
FRAME_AGGREGATION_PERIOD = W
```

## Mode Switching

```bash
# Switch to tracks mode
python switch_mode.py tracks

# Switch to artists mode  
python switch_mode.py artists

# Interactive mode selection
python switch_mode.py
```

### Core Components

- **main_animator.py**: Main application orchestrating the visualization pipeline
- **data_processor.py**: Data ingestion, cleaning, and transformation for both Spotify and Last.fm
- **config_loader.py**: Configuration management with type-safe getters
- **album_art_utils.py**: Spotify API integration for artwork and metadata
- **rolling_stats.py**: Rolling window statistics (7-day/30-day top tracks/artists)
- **nightingale_chart.py**: Animated polar chart for monthly listening patterns
- **text_utils.py**: International text rendering and font handling
- **time_aggregation.py**: Frame aggregation for performance optimization

### Data Flow

1. Settings loaded from `configurations.txt`
2. Raw data processed from Spotify JSON or Last.fm CSV
3. Cleaning, normalization, and time-series creation
4. Album covers and artist photos downloaded via Spotify API
5. Parallel creation of animation frames with all visual elements
6. FFmpeg rendering of final MP4 with optional GPU acceleration (only NVIDIA supported through NVENC)

### Cache

- **album_art_cache/**: Album artwork, dominant colors, and track metadata
- **artist_art_cache/**: Artist profile photos and artist metadata  
- **Multiple JSON caches**: Spotify API responses, failed searches, MusicBrainz data
- **Intelligent caching**: Avoids re-fetching and respects API rate limits

## Visual Elements

### Main Animation
- Smooth animated bars with artwork
-  Automatic X-axis adjustment as values change
- Bars colored using dominant artwork colors
- Smooth transitions during rank changes

### Side Panels
- 7-day and 30-day top tracks/artists
- Miniature album covers and artist photos
- Handles long international track/artist names

### Nightingale Rose Chart
- Polar chart showing listening patterns by month
- Gradual transitions as data changes over time
- Displays high and low listening periods

### Font Configuration
```ini
[FontPreferences]
PREFERRED_FONTS = DejaVu Sans, Noto Sans JP, Noto Sans KR, Noto Sans SC, Noto Sans TC, Arial Unicode MS
OS_SPECIFIC_FONT_LOADING = True
CUSTOM_FONT_DIR = fonts
```
- May have to download fonts to your computer, have not tested yet on a fresh machine

### Debug Options
```ini
[Debugging]
DEBUG_CACHE_ALBUM_ART_UTILS = True     # Detailed cache logging
LOG_FRAME_TIMES = True                 # Frame rendering performance
PARALLEL_LOG_COMPLETION_INTERVAL = 100 # Parallel processing updates
```

