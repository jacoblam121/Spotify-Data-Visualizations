# Spotify Data Visualizations

(Yes, this is AI generated). I'll manually update with more specific instructions and more detailed explanations of how it works later when I finish the full project. 
Create stunning animated bar chart "race" videos from your Spotify or Last.fm listening history. Watch your top tracks or artists compete over time with beautiful album artwork and artist photos.

## ✨ Features

### Dual Visualization Modes
- **Tracks Mode**: Animated bar chart race of your top songs with album covers
- **Artists Mode**: Animated bar chart race of your top artists with profile photos
- **Seamless Mode Switching**: Switch between modes with a simple command

### Data Sources
- **Spotify Extended Streaming History**: Direct JSON import from Spotify data export
- **Last.fm Data**: CSV export from Last.fm listening history
- **Flexible Time Filtering**: Analyze any date range or your entire listening history

### Rich Visual Elements
- **High-Quality Artwork**: Album covers and artist profile photos via Spotify API
- **Rolling Statistics Panels**: Live 7-day and 30-day top tracks/artists
- **Nightingale Rose Chart**: Optional polar chart showing monthly listening patterns
- **Dynamic Timestamp Display**: Real-time date progression during animation

### Performance & Quality
- **Multiple Resolutions**: 1080p and 4K output options
- **Frame Aggregation**: Reduce render time with daily/weekly/monthly sampling
- **Parallel Processing**: Multi-core frame generation for faster rendering
- **GPU Encoding**: NVENC support for hardware-accelerated video encoding
- **Smart Caching**: Multiple cache layers for artwork, metadata, and colors

### International Support
- **Unicode Text Rendering**: Full support for Japanese, Korean, Chinese, and other international characters
- **Multiple Font Fallbacks**: Automatic font selection for optimal character display
- **UTF-8 Encoding**: Proper handling of international artist and track names

## 🚀 Quick Start

### Prerequisites

1. **FFmpeg** (required for video output)
   ```bash
   # Install FFmpeg and add to PATH
   # Download from https://ffmpeg.org
   ffmpeg -version  # Verify installation
   ```

2. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Spotify API Credentials** (for artwork fetching)
   - Get credentials from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Add to `configurations.txt` or set as environment variables:
     ```bash
     export SPOTIFY_CLIENT_ID="your_client_id"
     export SPOTIFY_CLIENT_SECRET="your_client_secret"
     ```

### Data Preparation

#### Option 1: Spotify Data
1. Request your [Spotify Extended Streaming History](https://www.spotify.com/account/privacy/)
2. Place JSON file(s) in project directory (e.g., `StreamingHistory0.json`)
3. Update `INPUT_FILENAME_SPOTIFY` in `configurations.txt`

#### Option 2: Last.fm Data
1. Export your data from [Last.fm Export Tool](https://lastfm.ghan.nl/export/)
2. Save as `lastfm_data.csv` in project directory
3. Set `SOURCE = lastfm` in `configurations.txt`

### Running the Application

```bash
# Set encoding for international characters (required)
export PYTHONIOENCODING=utf-8  # Linux/macOS
set PYTHONIOENCODING=utf-8     # Windows CMD
$env:PYTHONIOENCODING="utf-8"  # Windows PowerShell

# Run the main animation
python main_animator.py
```

## 📁 Project Structure

```
Spotify-Data-Visualizations/
├── 📄 Core Application Files
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
├── 🧪 Testing & Utilities
│   ├── tests/
│   │   ├── test_phases_1_2.py        # Full test suite
│   │   ├── quick_test.py             # Interactive testing
│   │   ├── test_*.py                 # Component-specific tests
│   │   └── TESTING_GUIDE.md          # Comprehensive testing guide
│   └── summaries/                    # Implementation summaries
│
├── ⚙️ Configuration & Data
│   ├── configurations.txt            # Main configuration file
│   ├── requirements.txt              # Python dependencies
│   ├── spotify_data.json             # Your Spotify data (not included)
│   ├── lastfm_data.csv              # Your Last.fm data (not included)
│   └── CLAUDE.md                     # Development guidance
│
├── 🎨 Assets & Cache
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
├── 🎬 Output & Temporary Files
│   ├── *.mp4                         # Generated video files
│   │   ├── spotify_top_songs_race_4k.mp4
│   │   └── spotify_top_artists_race_4k.mp4
│   ├── temp_frames_*/                # Intermediate frame images
│   │   └── frame_*.png               # Individual animation frames
│   └── venv/                         # Python virtual environment
│
└── 📚 Documentation
    ├── README.md                     # This file
    └── bashrc                        # Shell configuration example
```

### Key Directories Explained

#### 🎨 **Cache Directories**
- **album_art_cache/**: Stores downloaded album artwork, metadata, and color analysis
- **artist_art_cache/**: Stores artist profile photos and artist-specific metadata
- **Multiple JSON files**: Cache API responses to avoid re-fetching and respect rate limits

#### 🎬 **Output Files**
- **Video files**: Final MP4 outputs named based on mode and resolution
- **temp_frames_*/**: Intermediate PNG frames (auto-cleaned unless debugging)
- **Parallel safe**: Multiple workers can generate frames simultaneously

#### 🧪 **Testing Infrastructure**
- **Comprehensive test suite**: Full functionality validation
- **Interactive testing**: Menu-driven component testing
- **Component tests**: Individual module validation
- **Performance testing**: Frame rendering and animation speed

#### ⚙️ **Configuration System**
- **Single config file**: All settings in `configurations.txt`
- **Type-safe loading**: Automatic validation and type conversion
- **Mode switching**: Easy transition between tracks/artists visualization

## 🎛️ Configuration

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

## 🔧 Mode Switching

Switch between visualization modes easily:

```bash
# Switch to tracks mode
python switch_mode.py tracks

# Switch to artists mode  
python switch_mode.py artists

# Interactive mode selection
python switch_mode.py
```

## 🧪 Testing

### Quick Testing
```bash
# Run full test suite
python test_phases_1_2.py

# Interactive testing menu
python quick_test.py

# Test specific components
python quick_test.py config                    # Configuration
python quick_test.py data                      # Data processing
python quick_test.py artist "Taylor Swift"     # Artist photos
python quick_test.py cache                     # View cache files
```

### Component Testing
```bash
# Test individual components
python data_processor.py           # Data processing
python config_loader.py           # Configuration loading
python nightingale_chart.py       # Rose chart rendering
```

## 🏗️ Architecture

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

1. **Configuration Loading**: Settings loaded from `configurations.txt`
2. **Data Ingestion**: Raw data processed from Spotify JSON or Last.fm CSV
3. **Data Transformation**: Cleaning, normalization, and time-series creation
4. **Artwork Pre-fetching**: Album covers and artist photos downloaded via Spotify API
5. **Frame Generation**: Parallel creation of animation frames with all visual elements
6. **Video Compilation**: FFmpeg assembly of final MP4 with optional GPU acceleration

### Cache Architecture

- **album_art_cache/**: Album artwork, dominant colors, and track metadata
- **artist_art_cache/**: Artist profile photos and artist metadata  
- **Multiple JSON caches**: Spotify API responses, failed searches, MusicBrainz data
- **Intelligent caching**: Avoids re-fetching and respects API rate limits

## 🎨 Visual Components

### Main Animation
- **Bar Chart Race**: Smooth animated bars with artwork
- **Dynamic Scaling**: Automatic Y-axis adjustment as values change
- **Color Coordination**: Bars colored using dominant artwork colors
- **Overtake Animations**: Optional smooth transitions during rank changes

### Side Panels
- **Rolling Statistics**: Real-time 7-day and 30-day top tracks/artists
- **Live Updates**: Statistics update as animation progresses
- **Artwork Integration**: Miniature album covers and artist photos
- **Smart Text Truncation**: Handles long international track/artist names

### Nightingale Rose Chart
- **Monthly Distribution**: Polar chart showing listening patterns by month
- **Smooth Animations**: Gradual transitions as data changes over time
- **High/Low Tracking**: Displays peak and valley listening periods
- **Configurable Display**: Enable/disable and customize appearance

## 📊 Data Format Requirements

### Spotify Extended Streaming History
```json
{
  "ts": "2024-01-01T00:00:00Z",
  "artistName": "Artist Name",
  "trackName": "Track Name", 
  "msPlayed": 240000
}
```

### Last.fm CSV Export
```csv
uts,utc_time,artist,artist_mbid,album,album_mbid,track,track_mbid
1704067200,01 Jan 2024 00:00,Artist Name,,Album Name,,Track Name,
```

## 🌍 International Support

### Character Encoding
- **Required**: Set `PYTHONIOENCODING=utf-8` before running
- **Font Support**: Japanese, Korean, Chinese, Arabic, and other Unicode scripts
- **Fallback Fonts**: Automatic selection from available system fonts

### Font Configuration
```ini
[FontPreferences]
PREFERRED_FONTS = DejaVu Sans, Noto Sans JP, Noto Sans KR, Noto Sans SC, Noto Sans TC, Arial Unicode MS
OS_SPECIFIC_FONT_LOADING = True
CUSTOM_FONT_DIR = fonts
```

## 🔍 Troubleshooting

### Common Issues

1. **"No data available"**
   - Verify data file exists and path is correct in `configurations.txt`
   - Check file encoding is UTF-8
   - Ensure date range contains data

2. **"Failed to get Spotify access token"**
   - Verify Spotify API credentials in `configurations.txt` or environment variables
   - Check credentials are active and not expired

3. **Character encoding errors**
   - Always set `PYTHONIOENCODING=utf-8` before running
   - Verify data files are UTF-8 encoded
   - Check font files exist in `fonts/` directory

4. **Performance issues**
   - Use `FRAME_AGGREGATION_PERIOD = W` or `M` for long time series
   - Adjust `MAX_PARALLEL_WORKERS` based on available CPU cores
   - Enable `CLEANUP_INTERMEDIATE_FRAMES = True` to save disk space

### Debug Options
```ini
[Debugging]
DEBUG_CACHE_ALBUM_ART_UTILS = True     # Detailed cache logging
LOG_FRAME_TIMES = True                 # Frame rendering performance
PARALLEL_LOG_COMPLETION_INTERVAL = 100 # Parallel processing updates
```

## 📈 Performance Tips

- **Frame Aggregation**: Use weekly (`W`) or monthly (`M`) aggregation for datasets with >10,000 plays
- **Parallel Processing**: Set `MAX_PARALLEL_WORKERS` to your CPU core count
- **GPU Encoding**: Enable `USE_NVENC_IF_AVAILABLE = True` if you have an NVIDIA GPU
- **Test Renders**: Use `MAX_FRAMES_FOR_TEST_RENDER = 100` for quick previews
- **Cache Management**: Keep cache directories for faster subsequent runs

## 🎯 Output Examples

### Generated Files
- `spotify_top_songs_race_4k.mp4` (tracks mode)
- `spotify_top_artists_race_4k.mp4` (artists mode)
- Cache directories with artwork and metadata
- Optional intermediate frames for debugging
