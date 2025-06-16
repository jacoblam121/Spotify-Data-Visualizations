# main_animator.py
import pandas as pd
import numpy as np
from data_processor import clean_and_filter_data, prepare_data_for_bar_chart_race
from rolling_stats import calculate_rolling_window_stats
from time_aggregation import calculate_nightingale_time_data, determine_aggregation_type
from nightingale_chart import prepare_nightingale_animation_data, draw_nightingale_chart

import album_art_utils # Import the module
# from album_art_utils import get_album_art_path, get_dominant_color # Can keep these specific imports

import matplotlib
matplotlib.use('Agg') # Use Agg backend for non-interactive plotting
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import os
import sys
import time # Added for timing
import platform # Added for OS detection
import concurrent.futures # Added for parallel processing
import subprocess # Added for calling ffmpeg
import shutil # Added for directory operations
import matplotlib.patheffects as path_effects # For text outlining
import matplotlib.patches as patches # For the text background rectangle
import matplotlib.font_manager as fm  # Needed for precise text width measurement
import argparse # Added for command line argument parsing
from text_utils import truncate_to_fit  # Helper for dynamic truncation

# Import the config loader
from config_loader import AppConfig

# --- Configuration (will be loaded from file) ---
config = None # Global config object
args = None # Global CLI arguments object
VISUALIZATION_MODE = "tracks" # Default mode - will be loaded from config

# --- Default values that might be overridden by config ---
N_BARS = 10
TARGET_FPS = 30
# ANIMATION_INTERVAL will be calculated from TARGET_FPS

OUTPUT_FILENAME_BASE = "spotify_top_songs_race" # Base, resolution and .mp4 added later
VIDEO_RESOLUTION_PRESETS = {
    "1080p": {"width": 1920, "height": 1080, "dpi": 96}, # DPI might need tuning
    "4k": {"width": 3840, "height": 2160, "dpi": 165}
}
# VIDEO_RESOLUTION_WIDTH, VIDEO_RESOLUTION_HEIGHT, VIDEO_DPI will be set from preset

DEBUG_ALBUM_ART_LOGIC = True
ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR = 0.0628
USE_NVENC_IF_AVAILABLE = True
PREFERRED_FONTS = ['DejaVu Sans', 'Noto Sans JP', 'Noto Sans KR', 'Noto Sans SC', 'Noto Sans TC', 'Arial Unicode MS', 'sans-serif']
MAX_FRAMES_FOR_TEST_RENDER = 0 # 0 or -1 for full render
LOG_FRAME_TIMES_CONFIG = False # Will be loaded from config
MAX_PARALLEL_WORKERS = os.cpu_count() # Default to number of CPU cores, will be loaded from config
CLEANUP_INTERMEDIATE_FRAMES = True # Will be loaded from config
PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG = 50 # Default, will be loaded from config
LOG_PARALLEL_PROCESS_START_CONFIG = True # Default, will be loaded from config
ANIMATION_TRANSITION_DURATION_SECONDS = 0.3 # Default, will be loaded from config
ENABLE_OVERTAKE_ANIMATIONS_CONFIG = True # Default, will be loaded from config
SONG_TEXT_RIGHT_GAP_FRACTION = 0.1  # Fraction of x-axis width to leave as a gap after song text

# --- Global Dictionaries for Caching Art Paths and Colors within the animator ---
album_art_image_objects = {}
album_bar_colors = {}
# High-resolution album art specifically for the rolling-stats panel (original size)
album_art_image_objects_highres = {}

# --- Rolling Stats Display Configuration (loaded from file) ---
ROLLING_PANEL_AREA_LEFT_FIG = 0.03
ROLLING_PANEL_AREA_RIGHT_FIG = 0.25
ROLLING_PANEL_TITLE_Y_FROM_TOP_FIG = 0.02
ROLLING_TITLE_TO_CONTENT_GAP_FIG = 0.01
ROLLING_TITLE_FONT_SIZE = 11.0
ROLLING_SONG_ARTIST_FONT_SIZE = 9.0
ROLLING_PLAYS_FONT_SIZE = 8.0
ROLLING_ART_HEIGHT_FIG = 0.07
ROLLING_ART_ASPECT_RATIO = 1.0
ROLLING_ART_MAX_WIDTH_FIG = 0.07
ROLLING_ART_PADDING_RIGHT_FIG = 0.005
ROLLING_TEXT_PADDING_LEFT_FIG = 0.005
ROLLING_TEXT_TO_ART_HORIZONTAL_GAP_FIG = 0.005
ROLLING_TEXT_LINE_VERTICAL_SPACING_FIG = 0.02
ROLLING_SONG_ARTIST_TO_PLAYS_VERTICAL_GAP_FIG = 0.025
ROLLING_INTER_PANEL_VERTICAL_SPACING_FIG = 0.04
# New globals for additional display configurations
ROLLING_PANEL_TITLE_X_FIG = -1.0 # Default to -1.0, indicating centered
ROLLING_TEXT_TRUNCATION_ADJUST_PX = 0 # Default to 0 pixels adjustment
MAIN_TIMESTAMP_X_FIG = -1.0 # Default to -1.0, indicating auto/ax_center
MAIN_TIMESTAMP_Y_FIG = 0.04 # Default y position
# --- End Rolling Stats Display Configuration ---

# --- Nightingale Chart Configuration ---
ENABLE_NIGHTINGALE = True
NIGHTINGALE_CENTER_X_FIG = 0.15
NIGHTINGALE_CENTER_Y_FIG = 0.20
NIGHTINGALE_RADIUS_FIG = 0.08
NIGHTINGALE_CHART_WIDTH_FIG = 0.16
NIGHTINGALE_CHART_HEIGHT_FIG = 0.16
NIGHTINGALE_CHART_PADDING_FIG = 0.02
NIGHTINGALE_SHOW_PERIOD_LABELS = True
NIGHTINGALE_LABEL_RADIUS_RATIO = 1.15
NIGHTINGALE_LABEL_FONT_COLOR = 'black'
NIGHTINGALE_LABEL_FONT_WEIGHT = 'normal'
NIGHTINGALE_SHOW_HIGH_LOW_INFO = True
NIGHTINGALE_HIGH_LOW_Y_OFFSET_FIG = -0.12
NIGHTINGALE_HIGH_LOW_SPACING_FIG = 0.025
NIGHTINGALE_ENABLE_SMOOTH_TRANSITIONS = True
NIGHTINGALE_TRANSITION_DURATION_SECONDS = 0.3
NIGHTINGALE_LABEL_FONT_SIZE = 10
NIGHTINGALE_HIGH_LOW_FONT_SIZE = 9
NIGHTINGALE_MIN_LABEL_RADIUS_RATIO = 0.3
NIGHTINGALE_AGGREGATION_TYPE = 'auto'
NIGHTINGALE_SAMPLING_RATE = 'D'  # Default to daily sampling
NIGHTINGALE_TITLE_POSITION_ABOVE_CHART = 0.02  # Default title position
NIGHTINGALE_DEBUG = False
# New setting for boundary circle
NIGHTINGALE_SHOW_BOUNDARY_CIRCLE = True
# --- End Nightingale Chart Configuration ---

# --- Global for tracking worker process startup logging ---
worker_pids_reported = set()

def find_ffmpeg_executable():
    """Find the correct ffmpeg executable for the current system"""
    # Try standard system ffmpeg first
    if shutil.which('ffmpeg'):
        return 'ffmpeg'
    
    # For WSL systems, check for Windows ffmpeg
    if platform.system() == 'Linux':
        # Check for Windows FFmpeg in common WSL mount locations
        windows_ffmpeg_paths = [
            '/mnt/c/ffmpeg-2025-06-11-git-f019dd69f0-full_build/ffmpeg-2025-06-11-git-f019dd69f0-full_build/bin/ffmpeg.exe',
            '/mnt/c/ffmpeg/bin/ffmpeg.exe',
            '/mnt/c/Program Files/ffmpeg/bin/ffmpeg.exe'
        ]
        
        for path in windows_ffmpeg_paths:
            if os.path.exists(path):
                print(f"Found Windows FFmpeg at: {path}")
                return path
    
    # If nothing found, return 'ffmpeg' and let the error happen with better message
    return 'ffmpeg'

def setup_fonts():
    """Setup fonts based on OS and configuration"""
    global config, PREFERRED_FONTS
    
    if config is None:
        print("Warning: Config not loaded in setup_fonts()")
        return
    
    # Check if OS-specific font loading is enabled
    os_specific_loading = config.get_bool('FontPreferences', 'OS_SPECIFIC_FONT_LOADING', True)
    custom_font_dir = config.get('FontPreferences', 'CUSTOM_FONT_DIR', 'fonts')
    
    if os_specific_loading and platform.system() == 'Linux':
        print("Setting up fonts for Linux...")
        
        # Get absolute path to fonts directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fonts_dir = os.path.join(script_dir, custom_font_dir)
        
        if os.path.exists(fonts_dir):
            print(f"Looking for fonts in: {fonts_dir}")
            
            # Register each font file with matplotlib
            registered_fonts = []
            for font_file in os.listdir(fonts_dir):
                if font_file.endswith(('.ttf', '.otf')):
                    font_path = os.path.join(fonts_dir, font_file)
                    try:
                        fm.fontManager.addfont(font_path)
                        
                        # Get the actual font family name
                        font_props = fm.FontProperties(fname=font_path)
                        family_name = font_props.get_name()
                        registered_fonts.append(family_name)
                        print(f"Registered font: {font_file} -> '{family_name}'")
                    except Exception as e:
                        print(f"Warning: Could not register font {font_file}: {e}")
            
            # Force matplotlib to rebuild its font cache completely
            try:
                # Clear the font cache directory if it exists
                import matplotlib as mpl
                cache_dir = mpl.get_cachedir()
                font_cache_files = ['fontlist-v330.json', 'fontlist-v300.json', 'fontList.cache']
                for cache_file in font_cache_files:
                    cache_path = os.path.join(cache_dir, cache_file)
                    if os.path.exists(cache_path):
                        os.remove(cache_path)
                        print(f"Removed font cache file: {cache_file}")
                
                # Force reload of font manager
                fm._load_fontmanager(try_read_cache=False)
                print("Font cache completely rebuilt")
                
                # Verify fonts are available
                print("Verifying registered fonts:")
                for family_name in registered_fonts:
                    try:
                        font_prop = fm.FontProperties(family=family_name)
                        found_path = fm.findfont(font_prop)
                        if fonts_dir in found_path:
                            print(f"  ✓ {family_name}: Available")
                        else:
                            print(f"  ⚠ {family_name}: Found but using system font at {found_path}")
                    except Exception as e:
                        print(f"  ✗ {family_name}: Not available - {e}")
                        
            except Exception as e:
                print(f"Warning: Error rebuilding font cache: {e}")
        else:
            print(f"Warning: Fonts directory not found: {fonts_dir}")
    
    # Set font preferences
    try:
        plt.rcParams['font.family'] = PREFERRED_FONTS
        print(f"Font preferences set: {PREFERRED_FONTS}")
    except Exception as e:
        print(f"Warning: Could not set preferred fonts: {e}. Using Matplotlib defaults.")

def load_configuration():
    global config, VISUALIZATION_MODE, N_BARS, TARGET_FPS, OUTPUT_FILENAME_BASE, DEBUG_ALBUM_ART_LOGIC
    global ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR, USE_NVENC_IF_AVAILABLE, PREFERRED_FONTS
    global MAX_FRAMES_FOR_TEST_RENDER, LOG_FRAME_TIMES_CONFIG
    global MAX_PARALLEL_WORKERS, CLEANUP_INTERMEDIATE_FRAMES, PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG
    global LOG_PARALLEL_PROCESS_START_CONFIG, ANIMATION_TRANSITION_DURATION_SECONDS
    global ENABLE_OVERTAKE_ANIMATIONS_CONFIG, SONG_TEXT_RIGHT_GAP_FRACTION
    global FORCE_PARALLEL_WORKERS, MEMORY_DEBUG_CONFIG, SERIAL_MODE_CONFIG, MAX_TASKS_PER_CHILD
    # Rolling Stats Display Globals
    global ROLLING_PANEL_AREA_LEFT_FIG, ROLLING_PANEL_AREA_RIGHT_FIG, ROLLING_PANEL_TITLE_Y_FROM_TOP_FIG
    global ROLLING_TITLE_TO_CONTENT_GAP_FIG, ROLLING_TITLE_FONT_SIZE, ROLLING_SONG_ARTIST_FONT_SIZE
    global ROLLING_PLAYS_FONT_SIZE, ROLLING_ART_HEIGHT_FIG, ROLLING_ART_ASPECT_RATIO, ROLLING_ART_MAX_WIDTH_FIG
    global ROLLING_ART_PADDING_RIGHT_FIG, ROLLING_TEXT_PADDING_LEFT_FIG, ROLLING_TEXT_TO_ART_HORIZONTAL_GAP_FIG
    global ROLLING_TEXT_LINE_VERTICAL_SPACING_FIG, ROLLING_SONG_ARTIST_TO_PLAYS_VERTICAL_GAP_FIG, ROLLING_INTER_PANEL_VERTICAL_SPACING_FIG
    # New globals for additional display control
    global ROLLING_PANEL_TITLE_X_FIG, ROLLING_TEXT_TRUNCATION_ADJUST_PX 
    global MAIN_TIMESTAMP_X_FIG, MAIN_TIMESTAMP_Y_FIG
    # Nightingale Chart Globals - Consolidating all into one block for clarity
    global ENABLE_NIGHTINGALE, NIGHTINGALE_CENTER_X_FIG, NIGHTINGALE_CENTER_Y_FIG, NIGHTINGALE_RADIUS_FIG
    global NIGHTINGALE_CHART_WIDTH_FIG, NIGHTINGALE_CHART_HEIGHT_FIG, NIGHTINGALE_CHART_PADDING_FIG
    global NIGHTINGALE_SHOW_PERIOD_LABELS, NIGHTINGALE_LABEL_RADIUS_RATIO, NIGHTINGALE_LABEL_FONT_COLOR, NIGHTINGALE_LABEL_FONT_WEIGHT
    global NIGHTINGALE_SHOW_HIGH_LOW_INFO, NIGHTINGALE_HIGH_LOW_Y_OFFSET_FIG, NIGHTINGALE_HIGH_LOW_SPACING_FIG
    global NIGHTINGALE_LABEL_FONT_SIZE, NIGHTINGALE_HIGH_LOW_FONT_SIZE, NIGHTINGALE_MIN_LABEL_RADIUS_RATIO
    global NIGHTINGALE_ENABLE_SMOOTH_TRANSITIONS, NIGHTINGALE_TRANSITION_DURATION_SECONDS
    global NIGHTINGALE_AGGREGATION_TYPE, NIGHTINGALE_SAMPLING_RATE, NIGHTINGALE_DEBUG
    global NIGHTINGALE_TITLE_FONT_SIZE, NIGHTINGALE_TITLE_FONT_WEIGHT, NIGHTINGALE_TITLE_COLOR, NIGHTINGALE_TITLE_POSITION_ABOVE_CHART
    global NIGHTINGALE_HIGH_PERIOD_COLOR, NIGHTINGALE_LOW_PERIOD_COLOR
    global NIGHTINGALE_SHOW_BOUNDARY_CIRCLE, NIGHTINGALE_OUTER_CIRCLE_COLOR, NIGHTINGALE_OUTER_CIRCLE_LINESTYLE, NIGHTINGALE_OUTER_CIRCLE_LINEWIDTH
    global NIGHTINGALE_ANIMATION_EASING_FUNCTION

    try:
        config = AppConfig() # Assumes configurations.txt is in the same directory
        print("Configuration loaded successfully.")
    except FileNotFoundError as e:
        print(f"CRITICAL ERROR: {e}. Please ensure 'configurations.txt' exists.")
        sys.exit(1)
    except Exception as e:
        print(f"CRITICAL ERROR loading configuration: {e}")
        sys.exit(1)

    # Initialize album_art_utils with the loaded config
    album_art_utils.initialize_from_config(config)

    # Load visualization mode and validate it
    VISUALIZATION_MODE = config.get('VisualizationMode', 'MODE', VISUALIZATION_MODE).lower()
    if VISUALIZATION_MODE not in ['tracks', 'artists']:
        print(f"WARNING: Invalid MODE '{VISUALIZATION_MODE}' in configuration. Defaulting to 'tracks'.")
        VISUALIZATION_MODE = 'tracks'
    print(f"Visualization mode: {VISUALIZATION_MODE}")

    # Override defaults with values from config
    N_BARS = config.get_int('AnimationOutput', 'N_BARS', N_BARS)
    TARGET_FPS = config.get_int('AnimationOutput', 'TARGET_FPS', TARGET_FPS)
    OUTPUT_FILENAME_BASE = config.get('AnimationOutput', 'FILENAME_BASE', OUTPUT_FILENAME_BASE)
    
    DEBUG_ALBUM_ART_LOGIC = config.get_bool('Debugging', 'DEBUG_ALBUM_ART_LOGIC_ANIMATOR', DEBUG_ALBUM_ART_LOGIC)
    ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR = config.get_float('AlbumArtSpotify', 'ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR', ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR)
    USE_NVENC_IF_AVAILABLE = config.get_bool('AnimationOutput', 'USE_NVENC_IF_AVAILABLE', USE_NVENC_IF_AVAILABLE)
    PREFERRED_FONTS = config.get_list('FontPreferences', 'PREFERRED_FONTS', fallback=PREFERRED_FONTS)
    MAX_FRAMES_FOR_TEST_RENDER = config.get_int('AnimationOutput', 'MAX_FRAMES_FOR_TEST_RENDER', MAX_FRAMES_FOR_TEST_RENDER)
    LOG_FRAME_TIMES_CONFIG = config.get_bool('Debugging', 'LOG_FRAME_TIMES', LOG_FRAME_TIMES_CONFIG)
    ANIMATION_TRANSITION_DURATION_SECONDS = config.get_float('AnimationOutput', 'ANIMATION_TRANSITION_DURATION_SECONDS', ANIMATION_TRANSITION_DURATION_SECONDS)
    ENABLE_OVERTAKE_ANIMATIONS_CONFIG = config.get_bool('AnimationOutput', 'ENABLE_OVERTAKE_ANIMATIONS', ENABLE_OVERTAKE_ANIMATIONS_CONFIG)
    # Load from AlbumArtSpotify section where user has it in configurations.txt
    SONG_TEXT_RIGHT_GAP_FRACTION = config.get_float('AlbumArtSpotify', 'SONG_TEXT_RIGHT_GAP_FRACTION', SONG_TEXT_RIGHT_GAP_FRACTION)
    
    # New config options for parallel processing
    # MAX_PARALLEL_WORKERS = config.get_int('AnimationOutput', 'MAX_PARALLEL_WORKERS', os.cpu_count() or 1) # Ensure at least 1
    # Corrected logic for MAX_PARALLEL_WORKERS:
    # If the user sets it to 0 or it's not found, default to CPU count.
    # The fallback in get_int is for when the key is missing or value is not int.
    # We also need to handle the case where user explicitly sets 0.
    workers_from_config = config.get_int('AnimationOutput', 'MAX_PARALLEL_WORKERS', -1) # Use -1 as sentinel for not found/default
    if workers_from_config <= 0: # If 0, negative, or not found (which get_int might map to its own fallback if not -1)
        MAX_PARALLEL_WORKERS = os.cpu_count() or 1 # Default to CPU count (ensure at least 1)
    else:
        MAX_PARALLEL_WORKERS = workers_from_config
        
    CLEANUP_INTERMEDIATE_FRAMES = config.get_bool('AnimationOutput', 'CLEANUP_INTERMEDIATE_FRAMES', True)
    
    # New configuration options for enhanced parallel processing control
    FORCE_PARALLEL_WORKERS = config.get_int('AnimationOutput', 'FORCE_PARALLEL_WORKERS', 0)
    MEMORY_DEBUG_CONFIG = config.get_bool('AnimationOutput', 'MEMORY_DEBUG', False)
    SERIAL_MODE_CONFIG = config.get_bool('AnimationOutput', 'SERIAL_MODE', False)
    MAX_TASKS_PER_CHILD = config.get_int('AnimationOutput', 'MAX_TASKS_PER_CHILD', 100)
    
    PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG = config.get_int('Debugging', 'PARALLEL_LOG_COMPLETION_INTERVAL', 50)
    LOG_PARALLEL_PROCESS_START_CONFIG = config.get_bool('Debugging', 'LOG_PARALLEL_PROCESS_START', True)

    ROLLING_PANEL_AREA_LEFT_FIG = config.get_float('RollingStatsDisplay', 'PANEL_AREA_LEFT_FIG', ROLLING_PANEL_AREA_LEFT_FIG)
    ROLLING_PANEL_AREA_RIGHT_FIG = config.get_float('RollingStatsDisplay', 'PANEL_AREA_RIGHT_FIG', ROLLING_PANEL_AREA_RIGHT_FIG)
    ROLLING_PANEL_TITLE_Y_FROM_TOP_FIG = config.get_float('RollingStatsDisplay', 'PANEL_TITLE_Y_FROM_TOP_FIG', ROLLING_PANEL_TITLE_Y_FROM_TOP_FIG)
    ROLLING_TITLE_TO_CONTENT_GAP_FIG = config.get_float('RollingStatsDisplay', 'TITLE_TO_CONTENT_GAP_FIG', ROLLING_TITLE_TO_CONTENT_GAP_FIG)
    ROLLING_TITLE_FONT_SIZE = config.get_float('RollingStatsDisplay', 'TITLE_FONT_SIZE', ROLLING_TITLE_FONT_SIZE)
    ROLLING_SONG_ARTIST_FONT_SIZE = config.get_float('RollingStatsDisplay', 'SONG_ARTIST_FONT_SIZE', ROLLING_SONG_ARTIST_FONT_SIZE)
    ROLLING_PLAYS_FONT_SIZE = config.get_float('RollingStatsDisplay', 'PLAYS_FONT_SIZE', ROLLING_PLAYS_FONT_SIZE)
    ROLLING_ART_HEIGHT_FIG = config.get_float('RollingStatsDisplay', 'ART_HEIGHT_FIG', ROLLING_ART_HEIGHT_FIG)
    ROLLING_ART_ASPECT_RATIO = config.get_float('RollingStatsDisplay', 'ART_ASPECT_RATIO', ROLLING_ART_ASPECT_RATIO)
    ROLLING_ART_MAX_WIDTH_FIG = config.get_float('RollingStatsDisplay', 'ART_MAX_WIDTH_FIG', ROLLING_ART_MAX_WIDTH_FIG)
    ROLLING_ART_PADDING_RIGHT_FIG = config.get_float('RollingStatsDisplay', 'ART_PADDING_RIGHT_FIG', ROLLING_ART_PADDING_RIGHT_FIG)
    ROLLING_TEXT_PADDING_LEFT_FIG = config.get_float('RollingStatsDisplay', 'TEXT_PADDING_LEFT_FIG', ROLLING_TEXT_PADDING_LEFT_FIG)
    ROLLING_TEXT_TO_ART_HORIZONTAL_GAP_FIG = config.get_float('RollingStatsDisplay', 'TEXT_TO_ART_HORIZONTAL_GAP_FIG', ROLLING_TEXT_TO_ART_HORIZONTAL_GAP_FIG)
    ROLLING_TEXT_LINE_VERTICAL_SPACING_FIG = config.get_float('RollingStatsDisplay', 'TEXT_LINE_VERTICAL_SPACING_FIG', ROLLING_TEXT_LINE_VERTICAL_SPACING_FIG)
    ROLLING_SONG_ARTIST_TO_PLAYS_VERTICAL_GAP_FIG = config.get_float('RollingStatsDisplay', 'SONG_ARTIST_TO_PLAYS_VERTICAL_GAP_FIG', ROLLING_SONG_ARTIST_TO_PLAYS_VERTICAL_GAP_FIG)
    ROLLING_INTER_PANEL_VERTICAL_SPACING_FIG = config.get_float('RollingStatsDisplay', 'INTER_PANEL_VERTICAL_SPACING_FIG', ROLLING_INTER_PANEL_VERTICAL_SPACING_FIG)
    # Load new display configurations
    ROLLING_PANEL_TITLE_X_FIG = config.get_float('RollingStatsDisplay', 'PANEL_TITLE_X_FIG', ROLLING_PANEL_TITLE_X_FIG)
    ROLLING_TEXT_TRUNCATION_ADJUST_PX = config.get_int('RollingStatsDisplay', 'ROLLING_TEXT_TRUNCATION_ADJUST_PX', ROLLING_TEXT_TRUNCATION_ADJUST_PX)
    
    MAIN_TIMESTAMP_X_FIG = config.get_float('TimestampDisplay', 'TIMESTAMP_X_FIG', MAIN_TIMESTAMP_X_FIG)
    MAIN_TIMESTAMP_Y_FIG = config.get_float('TimestampDisplay', 'TIMESTAMP_Y_FIG', MAIN_TIMESTAMP_Y_FIG)
    
    # Nightingale Chart Configuration Loading (Simplified)
    ENABLE_NIGHTINGALE = config.get_bool('NightingaleChart', 'ENABLE', ENABLE_NIGHTINGALE)
    
    # Chart Position & Size
    NIGHTINGALE_CENTER_X_FIG = config.get_float('NightingaleChart', 'CHART_X', NIGHTINGALE_CENTER_X_FIG)
    NIGHTINGALE_CENTER_Y_FIG = config.get_float('NightingaleChart', 'CHART_Y', NIGHTINGALE_CENTER_Y_FIG)
    NIGHTINGALE_RADIUS_FIG = config.get_float('NightingaleChart', 'CHART_RADIUS', NIGHTINGALE_RADIUS_FIG)
    
    # Month Labels
    NIGHTINGALE_SHOW_PERIOD_LABELS = config.get_bool('NightingaleChart', 'SHOW_MONTH_LABELS', NIGHTINGALE_SHOW_PERIOD_LABELS)
    NIGHTINGALE_LABEL_RADIUS_RATIO = config.get_float('NightingaleChart', 'MONTH_LABEL_DISTANCE', NIGHTINGALE_LABEL_RADIUS_RATIO)
    NIGHTINGALE_LABEL_FONT_SIZE = config.get_int('NightingaleChart', 'MONTH_LABEL_FONT_SIZE', NIGHTINGALE_LABEL_FONT_SIZE)
    NIGHTINGALE_LABEL_FONT_COLOR = config.get('NightingaleChart', 'MONTH_LABEL_COLOR', NIGHTINGALE_LABEL_FONT_COLOR)
    NIGHTINGALE_LABEL_FONT_WEIGHT = config.get('NightingaleChart', 'MONTH_LABEL_FONT_WEIGHT', NIGHTINGALE_LABEL_FONT_WEIGHT)
    
    # Title
    NIGHTINGALE_TITLE_FONT_SIZE = config.get_int('NightingaleChart', 'TITLE_FONT_SIZE', 12)
    NIGHTINGALE_TITLE_FONT_WEIGHT = config.get('NightingaleChart', 'TITLE_FONT_WEIGHT', 'bold')
    NIGHTINGALE_TITLE_COLOR = config.get('NightingaleChart', 'TITLE_COLOR', 'black')
    NIGHTINGALE_TITLE_POSITION_ABOVE_CHART = config.get_float('NightingaleChart', 'TITLE_POSITION_ABOVE_CHART', 0.02)
    
    # High/Low Tracker
    NIGHTINGALE_SHOW_HIGH_LOW_INFO = config.get_bool('NightingaleChart', 'SHOW_HIGH_LOW', NIGHTINGALE_SHOW_HIGH_LOW_INFO)
    NIGHTINGALE_HIGH_LOW_FONT_SIZE = config.get_int('NightingaleChart', 'HIGH_LOW_FONT_SIZE', NIGHTINGALE_HIGH_LOW_FONT_SIZE)
    NIGHTINGALE_HIGH_LOW_Y_OFFSET_FIG = config.get_float('NightingaleChart', 'HIGH_LOW_POSITION_BELOW_CHART', NIGHTINGALE_HIGH_LOW_Y_OFFSET_FIG)
    NIGHTINGALE_HIGH_LOW_SPACING_FIG = config.get_float('NightingaleChart', 'HIGH_LOW_SPACING', NIGHTINGALE_HIGH_LOW_SPACING_FIG)
    NIGHTINGALE_HIGH_PERIOD_COLOR = config.get('NightingaleChart', 'HIGH_PERIOD_COLOR', 'darkgreen')
    NIGHTINGALE_LOW_PERIOD_COLOR = config.get('NightingaleChart', 'LOW_PERIOD_COLOR', 'darkred')
    
    # Advanced Options
    NIGHTINGALE_SHOW_BOUNDARY_CIRCLE = config.get_bool('NightingaleChart', 'SHOW_BOUNDARY_CIRCLE', NIGHTINGALE_SHOW_BOUNDARY_CIRCLE)
    NIGHTINGALE_OUTER_CIRCLE_COLOR = config.get('NightingaleChart', 'BOUNDARY_CIRCLE_COLOR', 'gray')
    NIGHTINGALE_OUTER_CIRCLE_LINESTYLE = config.get('NightingaleChart', 'BOUNDARY_CIRCLE_STYLE', '--')
    NIGHTINGALE_OUTER_CIRCLE_LINEWIDTH = config.get_float('NightingaleChart', 'BOUNDARY_CIRCLE_WIDTH', 1.0)
    NIGHTINGALE_AGGREGATION_TYPE = config.get('NightingaleChart', 'TIME_AGGREGATION', NIGHTINGALE_AGGREGATION_TYPE).lower()
    NIGHTINGALE_ENABLE_SMOOTH_TRANSITIONS = config.get_bool('NightingaleChart', 'SMOOTH_TRANSITIONS', NIGHTINGALE_ENABLE_SMOOTH_TRANSITIONS)
    NIGHTINGALE_TRANSITION_DURATION_SECONDS = config.get_float('NightingaleChart', 'TRANSITION_DURATION', NIGHTINGALE_TRANSITION_DURATION_SECONDS)
    NIGHTINGALE_ANIMATION_EASING_FUNCTION = config.get('NightingaleChart', 'ANIMATION_STYLE', 'cubic')
    NIGHTINGALE_SAMPLING_RATE = config.get('NightingaleChart', 'SAMPLING_RATE', 'D')
    NIGHTINGALE_DEBUG = config.get_bool('NightingaleChart', 'DEBUG_MODE', NIGHTINGALE_DEBUG)
    
    # Removed redundant settings: CHART_WIDTH_FIG, CHART_HEIGHT_FIG, CHART_PADDING_FIG, MIN_LABEL_RADIUS_RATIO

    # Debug output for nightingale configuration
    print(f"=== NIGHTINGALE CONFIG DEBUG ===")
    print(f"CHART_Y loaded: {NIGHTINGALE_CENTER_Y_FIG}")
    print(f"CHART_X loaded: {NIGHTINGALE_CENTER_X_FIG}")
    print(f"CHART_RADIUS loaded: {NIGHTINGALE_RADIUS_FIG}")
    print(f"DEBUG_MODE: {NIGHTINGALE_DEBUG}")
    print(f"=================================")

    try:
        plt.rcParams['font.family'] = PREFERRED_FONTS
    except Exception as e:
        print(f"Warning: Could not set preferred fonts from config: {e}. Using Matplotlib defaults.")

def run_data_pipeline(): # Removed csv_file_path argument
    print("--- Starting Data Processing Pipeline ---")
    # The global `config` object should already be loaded by load_configuration() in main()
    
    if config is None:
        print("CRITICAL: Configuration not loaded in run_data_pipeline. Exiting.")
        sys.exit(1) # Or handle error appropriately

    print(f"\nStep 1: Cleaning and filtering data based on configuration (Source: {config.get('DataSource', 'SOURCE')})...")
    # clean_and_filter_data now takes the config object
    cleaned_df = clean_and_filter_data(config) 
    
    if cleaned_df is None or cleaned_df.empty: 
        print("Data cleaning and filtering resulted in no data. Exiting.")
        return None, {} # Return empty song_album_map as well
    # ... rest of run_data_pipeline remains the same ...
    print(f"Data cleaning successful. {len(cleaned_df)} relevant rows found.")
    
    print(f"\nStep 2: Preparing data for bar chart race (high-resolution timestamps) in {VISUALIZATION_MODE} mode...")
    race_df, entity_details_map = prepare_data_for_bar_chart_race(cleaned_df, mode=VISUALIZATION_MODE)
    if race_df is None or race_df.empty: 
        print("Data preparation for race resulted in no data. Exiting.")
        return None, entity_details_map
        
    print("Data preparation successful.")
    entity_type = "songs" if VISUALIZATION_MODE == "tracks" else "artists"
    print(f"Race DataFrame shape: {race_df.shape} (Play Events, Unique {entity_type.title()})")
    print(f"Number of entries in entity_details_map: {len(entity_details_map)}")
    print("--- Data Processing Pipeline Complete ---")
    return race_df, entity_details_map


def pre_fetch_album_art_and_colors(song_details_map, song_ids_to_fetch_art_for, target_img_height_pixels_for_resize, fig_dpi):
    # This function now uses album_art_utils directly, which is config-aware
    print(f"\n--- Pre-fetching album art and dominant colors for songs that appear on chart (Target Img Resize Height: {target_img_height_pixels_for_resize}px) ---")
    
    # This set will now track CANONICAL album names for which PIL/color is loaded in main_animator
    # to avoid redundant PIL loading and dominant color calculation for the same canonical album.
    canonical_albums_loaded_in_animator_cache = set()
    song_id_to_animator_key_map = {} # New map to return
    
    processed_count = 0

    for song_id in song_ids_to_fetch_art_for: # Iterate over songs that will appear on chart
        try:
            artist_name, track_name = song_id.split(" - ", 1)
        except ValueError:
            # This warning was already in your code, good to keep.
            print(f"WARNING: Could not parse artist/track from song_id: '{song_id}'. Skipping pre-fetch for this song.")
            continue

        song_specific_details = song_details_map.get(song_id)
        if not song_specific_details:
            if DEBUG_ALBUM_ART_LOGIC:
                print(f"[PRE-FETCH DEBUG] No details in song_details_map for '{song_id}'. Skipping art/color processing.")
            continue
        
        album_name_hint_from_data = song_specific_details.get('name', "Unknown Album")
        album_mbid_from_data = song_specific_details.get('mbid')
        track_uri_from_data = song_specific_details.get('track_uri')

        if DEBUG_ALBUM_ART_LOGIC:
            print(f"[PRE-FETCH DEBUG] Processing song '{song_id}' (it appears on chart). Album hint: '{album_name_hint_from_data}'.")

        # --- Call album_art_utils to get path and Spotify info ---
        try:
            print(f"Processing art/color for: Artist='{artist_name}', Track='{track_name}', Album (Hint)='{album_name_hint_from_data}', MBID='{album_mbid_from_data}', URI='{track_uri_from_data}'")
        except UnicodeEncodeError: # Handle potential encoding issues in print
            safe_artist = artist_name.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            safe_track = track_name.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            safe_album_hint = album_name_hint_from_data.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            safe_mbid = str(album_mbid_from_data).encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            safe_uri = str(track_uri_from_data).encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            print(f"Processing art/color for: Artist='{safe_artist}', Track='{safe_track}', Album (Hint)='{safe_album_hint}', MBID='{safe_mbid}', URI='{safe_uri}'")

        identifier_info = {
            "album_name_hint": album_name_hint_from_data,
            "album_mbid": album_mbid_from_data,
            "track_uri": track_uri_from_data,
            "source_data_type": config.get('DataSource', 'SOURCE').lower()
        }
        art_path, spotify_info = album_art_utils.get_album_art_path_and_spotify_info(artist_name, track_name, identifier_info)
        
        # --- Determine the canonical_album_name_for_animator_cache --- 
        canonical_album_name_for_animator_cache = album_name_hint_from_data # Fallback to original hint
        if spotify_info and spotify_info.get("canonical_album_name"):
            canonical_album_name_for_animator_cache = spotify_info["canonical_album_name"]
            if DEBUG_ALBUM_ART_LOGIC and canonical_album_name_for_animator_cache != album_name_hint_from_data:
                print(f"[PRE-FETCH DEBUG] Canonical album for '{song_id}' is '{canonical_album_name_for_animator_cache}' (hint was '{album_name_hint_from_data}', source: {spotify_info.get('source')}).")
        elif DEBUG_ALBUM_ART_LOGIC:
             print(f"[PRE-FETCH DEBUG] Could not find canonical album name from spotify_info for '{song_id}'. Using hint '{album_name_hint_from_data}' for animator cache key.")

        song_id_to_animator_key_map[song_id] = canonical_album_name_for_animator_cache # Store mapping

        # --- Load PIL image and dominant color into animator's memory if not already done for this CANONICAL album ---
        if art_path: # If an art path was successfully found/downloaded
            if canonical_album_name_for_animator_cache not in canonical_albums_loaded_in_animator_cache:
                try:
                    # Load image once and keep an RGB copy in memory at original size.
                    with Image.open(art_path) as _img_tmp:
                        _img_tmp = _img_tmp.convert('RGB')
                        full_res_img = _img_tmp.copy()  # Keep for rolling panel

                        # --- Resize image here for BAR-CHART usage ---
                        img_orig_width, img_orig_height = _img_tmp.size
                    new_height_pixels = int(target_img_height_pixels_for_resize)
                    new_width_pixels = 1
                    if img_orig_height > 0 and new_height_pixels > 0:
                        new_width_pixels = int(new_height_pixels * (img_orig_width / img_orig_height))
                    if new_width_pixels <= 0: new_width_pixels = int(new_height_pixels * 0.75) # Fallback if aspect ratio is extreme
                    if new_width_pixels <= 0: new_width_pixels = 1 # Final fallback

                    resized_img = _img_tmp.resize((new_width_pixels, new_height_pixels), Image.Resampling.LANCZOS)

                    # Ensure the resized image is in RGB mode for Matplotlib compatibility
                    if resized_img.mode != 'RGB':
                        resized_img = resized_img.convert('RGB')

                    album_art_image_objects[canonical_album_name_for_animator_cache] = resized_img

                    # Store the full-resolution copy for rolling-stats panel usage
                    album_art_image_objects_highres[canonical_album_name_for_animator_cache] = full_res_img
                    
                    # Get dominant color (this also uses its own cache in album_art_utils)
                    dc = album_art_utils.get_dominant_color(art_path) 
                    album_bar_colors[canonical_album_name_for_animator_cache] = (dc[0]/255.0, dc[1]/255.0, dc[2]/255.0)
                    
                    canonical_albums_loaded_in_animator_cache.add(canonical_album_name_for_animator_cache)
                    if DEBUG_ALBUM_ART_LOGIC:
                        print(f"[PRE-FETCH DEBUG] Loaded PIL & color into animator cache for CANONICAL album: '{canonical_album_name_for_animator_cache}'.")
                except FileNotFoundError:
                    print(f"Error [PRE-FETCH]: Image file not found at path: {art_path} for canonical album '{canonical_album_name_for_animator_cache}'. Using defaults.")
                    album_art_image_objects[canonical_album_name_for_animator_cache] = None
                    album_bar_colors[canonical_album_name_for_animator_cache] = (0.5, 0.5, 0.5)
                    canonical_albums_loaded_in_animator_cache.add(canonical_album_name_for_animator_cache) # Mark as processed
                    # Also mark hi-res cache with None so we do not attempt to re-load every frame
                    album_art_image_objects_highres[canonical_album_name_for_animator_cache] = None
                except Exception as e:
                    print(f"Error [PRE-FETCH] loading image {art_path} or getting color for canonical album '{canonical_album_name_for_animator_cache}': {e}. Using defaults.")
                    album_art_image_objects[canonical_album_name_for_animator_cache] = None
                    album_bar_colors[canonical_album_name_for_animator_cache] = (0.5, 0.5, 0.5)
                    canonical_albums_loaded_in_animator_cache.add(canonical_album_name_for_animator_cache) # Mark as processed
                    album_art_image_objects_highres[canonical_album_name_for_animator_cache] = None
        else: # No art_path was found by album_art_utils
            if DEBUG_ALBUM_ART_LOGIC:
                print(f"[PRE-FETCH DEBUG] No art path returned by album_art_utils for '{song_id}' (Hint: '{album_name_hint_from_data}').")
            # Still need to populate animator cache with defaults for this canonical album if it's the first time seeing it
            if canonical_album_name_for_animator_cache not in canonical_albums_loaded_in_animator_cache:
                album_art_image_objects[canonical_album_name_for_animator_cache] = None
                album_bar_colors[canonical_album_name_for_animator_cache] = (0.5, 0.5, 0.5) # Default color
                canonical_albums_loaded_in_animator_cache.add(canonical_album_name_for_animator_cache)
                if DEBUG_ALBUM_ART_LOGIC:
                    print(f"[PRE-FETCH DEBUG] Using default art/color in animator cache for CANONICAL album: '{canonical_album_name_for_animator_cache}'.")

        processed_count += 1
        
    print(f"--- Pre-fetching complete ---")
    print(f"Attempted to process art/color for {processed_count} song-album groups that met threshold.")
    print(f"Skipped count based on meeting visibility threshold is no longer applicable here.")
    print(f"In-memory PIL images (animator cache): {len(album_art_image_objects)}, In-memory bar colors (animator cache): {len(album_bar_colors)}")
    return song_id_to_animator_key_map # Return the new map


def pre_fetch_artist_photos_and_colors(entity_details_map, entity_ids_to_fetch_art_for, target_img_height_pixels_for_resize, fig_dpi):
    """
    Pre-fetch artist profile photos and dominant colors for artists that appear on chart.
    This is the artist mode equivalent of pre_fetch_album_art_and_colors().
    """
    print(f"\n--- Pre-fetching artist profile photos and dominant colors for artists that appear on chart (Target Img Resize Height: {target_img_height_pixels_for_resize}px) ---")
    
    # This set will track CANONICAL artist names for which PIL/color is loaded in main_animator
    canonical_artists_loaded_in_animator_cache = set()
    entity_id_to_animator_key_map = {} # Map entity IDs to cache keys
    
    processed_count = 0

    for entity_id in entity_ids_to_fetch_art_for: # Iterate over entities that will appear on chart
        artist_name = entity_id  # In artist mode, entity_id is the artist name
        
        entity_specific_details = entity_details_map.get(entity_id)
        if not entity_specific_details:
            if DEBUG_ALBUM_ART_LOGIC:
                print(f"[ARTIST PRE-FETCH DEBUG] No details in entity_details_map for '{entity_id}'. Skipping photo/color processing.")
            continue
        
        # Extract fallback track info and artist MBID for Last.fm data
        fallback_track_info = None
        artist_mbid = entity_specific_details.get('artist_mbid')
        
        # Get the most played track info for fallback
        most_played_track = entity_specific_details.get('most_played_track', {})
        if most_played_track:
            fallback_track_info = {
                "track_name": most_played_track.get('track_name', "Unknown Track"),
                "album_name": most_played_track.get('album_name', "Unknown Album"),
                "track_uri": most_played_track.get('track_uri')
            }

        if DEBUG_ALBUM_ART_LOGIC:
            print(f"[ARTIST PRE-FETCH DEBUG] Processing artist '{entity_id}' (it appears on chart). MBID: '{artist_mbid}'.")

        # --- Call album_art_utils to get artist photo path and info ---
        try:
            print(f"Processing artist photo/color for: Artist='{artist_name}', MBID='{artist_mbid}'")
        except UnicodeEncodeError: # Handle potential encoding issues in print
            safe_artist = artist_name.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            safe_mbid = str(artist_mbid).encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            print(f"Processing artist photo/color for: Artist='{safe_artist}', MBID='{safe_mbid}'")

        photo_path, artist_info = album_art_utils.get_artist_profile_photo_and_spotify_info(
            artist_name, 
            fallback_track_info=fallback_track_info,
            artist_mbid=artist_mbid
        )
        
        # --- Determine the canonical_artist_name_for_animator_cache --- 
        canonical_artist_name_for_animator_cache = artist_name # Fallback to original name
        if artist_info and artist_info.get("canonical_artist_name"):
            canonical_artist_name_for_animator_cache = artist_info["canonical_artist_name"]
            if DEBUG_ALBUM_ART_LOGIC and canonical_artist_name_for_animator_cache != artist_name:
                print(f"[ARTIST PRE-FETCH DEBUG] Canonical artist for '{entity_id}' is '{canonical_artist_name_for_animator_cache}' (original was '{artist_name}', source: {artist_info.get('source')}).")
        elif DEBUG_ALBUM_ART_LOGIC:
             print(f"[ARTIST PRE-FETCH DEBUG] Could not find canonical artist name from artist_info for '{entity_id}'. Using original name '{artist_name}' for animator cache key.")

        entity_id_to_animator_key_map[entity_id] = canonical_artist_name_for_animator_cache # Store mapping

        # --- Load PIL image and dominant color into animator's memory if not already done for this CANONICAL artist ---
        if photo_path: # If a photo path was successfully found/downloaded
            if canonical_artist_name_for_animator_cache not in canonical_artists_loaded_in_animator_cache:
                try:
                    # Load image once and keep an RGB copy in memory at original size.
                    with Image.open(photo_path) as _img_tmp:
                        _img_tmp = _img_tmp.convert('RGB')
                        full_res_img = _img_tmp.copy()  # Keep for rolling panel

                        # --- Resize image here for BAR-CHART usage ---
                        img_orig_width, img_orig_height = _img_tmp.size
                    new_height_pixels = int(target_img_height_pixels_for_resize)
                    new_width_pixels = 1
                    if img_orig_height > 0 and new_height_pixels > 0:
                        new_width_pixels = int(new_height_pixels * (img_orig_width / img_orig_height))
                    if new_width_pixels <= 0: new_width_pixels = int(new_height_pixels * 0.75) # Fallback if aspect ratio is extreme
                    if new_width_pixels <= 0: new_width_pixels = 1 # Final fallback

                    resized_img = _img_tmp.resize((new_width_pixels, new_height_pixels), Image.Resampling.LANCZOS)

                    # Ensure the resized image is in RGB mode for Matplotlib compatibility
                    if resized_img.mode != 'RGB':
                        resized_img = resized_img.convert('RGB')

                    album_art_image_objects[canonical_artist_name_for_animator_cache] = resized_img

                    # Store the full-resolution copy for rolling-stats panel usage
                    album_art_image_objects_highres[canonical_artist_name_for_animator_cache] = full_res_img
                    
                    # Get dominant color using artist-specific function
                    dc = album_art_utils.get_artist_dominant_color(photo_path) 
                    album_bar_colors[canonical_artist_name_for_animator_cache] = (dc[0]/255.0, dc[1]/255.0, dc[2]/255.0)
                    
                    canonical_artists_loaded_in_animator_cache.add(canonical_artist_name_for_animator_cache)
                    if DEBUG_ALBUM_ART_LOGIC:
                        print(f"[ARTIST PRE-FETCH DEBUG] Loaded PIL & color into animator cache for CANONICAL artist: '{canonical_artist_name_for_animator_cache}'.")
                except FileNotFoundError:
                    print(f"Error [ARTIST PRE-FETCH]: Image file not found at path: {photo_path} for canonical artist '{canonical_artist_name_for_animator_cache}'. Using defaults.")
                    album_art_image_objects[canonical_artist_name_for_animator_cache] = None
                    album_bar_colors[canonical_artist_name_for_animator_cache] = (0.5, 0.5, 0.5)
                    canonical_artists_loaded_in_animator_cache.add(canonical_artist_name_for_animator_cache) # Mark as processed
                    # Also mark hi-res cache with None so we do not attempt to re-load every frame
                    album_art_image_objects_highres[canonical_artist_name_for_animator_cache] = None
                except Exception as e:
                    print(f"Error [ARTIST PRE-FETCH] loading image {photo_path} or getting color for canonical artist '{canonical_artist_name_for_animator_cache}': {e}. Using defaults.")
                    album_art_image_objects[canonical_artist_name_for_animator_cache] = None
                    album_bar_colors[canonical_artist_name_for_animator_cache] = (0.5, 0.5, 0.5)
                    canonical_artists_loaded_in_animator_cache.add(canonical_artist_name_for_animator_cache) # Mark as processed
                    album_art_image_objects_highres[canonical_artist_name_for_animator_cache] = None
        else: # No photo_path was found by album_art_utils
            if DEBUG_ALBUM_ART_LOGIC:
                print(f"[ARTIST PRE-FETCH DEBUG] No photo path returned by album_art_utils for '{entity_id}'.")
            # Still need to populate animator cache with defaults for this canonical artist if it's the first time seeing it
            if canonical_artist_name_for_animator_cache not in canonical_artists_loaded_in_animator_cache:
                album_art_image_objects[canonical_artist_name_for_animator_cache] = None
                album_bar_colors[canonical_artist_name_for_animator_cache] = (0.5, 0.5, 0.5) # Default color
                canonical_artists_loaded_in_animator_cache.add(canonical_artist_name_for_animator_cache)
                if DEBUG_ALBUM_ART_LOGIC:
                    print(f"[ARTIST PRE-FETCH DEBUG] Using default photo/color in animator cache for CANONICAL artist: '{canonical_artist_name_for_animator_cache}'.")

        processed_count += 1
        
    print(f"--- Artist photo pre-fetching complete ---")
    print(f"Attempted to process photo/color for {processed_count} artist groups that met threshold.")
    print(f"In-memory PIL images (animator cache): {len(album_art_image_objects)}, In-memory bar colors (animator cache): {len(album_bar_colors)}")
    return entity_id_to_animator_key_map # Return the new map


def generate_render_tasks(race_df_for_animation, n_bars_config, target_fps_config, transition_duration_seconds_config, rolling_stats_data, nightingale_data=None):
    """
    Generates a list of render tasks, including intermediate frames for smooth animations.
    Each task details what to draw for a single output image frame.
    """
    render_tasks = []
    overall_frame_index_counter = 0

    # Store the state of the previous keyframe (play counts and y_positions)
    # y_positions will be 0 (top) to n_bars_config - 1 (bottom)
    previous_keyframe_render_data = {} # song_id: {"plays": count, "y_pos": position_float}

    # Calculate how many intermediate "tween" frames per transition
    num_tween_frames = 0
    if ENABLE_OVERTAKE_ANIMATIONS_CONFIG: # Check the global config flag first
        if transition_duration_seconds_config > 0 and target_fps_config > 0:
            num_tween_frames = int(transition_duration_seconds_config * target_fps_config)
    # If ENABLE_OVERTAKE_ANIMATIONS_CONFIG is False, num_tween_frames remains 0

    print(f"Generating render tasks. Overtake animations enabled: {ENABLE_OVERTAKE_ANIMATIONS_CONFIG}. Tween frames per transition: {num_tween_frames}")

    for keyframe_idx, (timestamp, current_keyframe_series) in enumerate(race_df_for_animation.iterrows()):
        # --- Determine current keyframe's top N entities and their target y_positions ---
        current_top_n_entities = current_keyframe_series[current_keyframe_series > 0].nlargest(n_bars_config)
        
        # Target state for entities in this keyframe
        current_keyframe_target_render_data = {} # entity_id: {"plays": count, "y_pos": position_float, "rank": rank}
        
        # Sort by play count descending to determine rank and initial target y_pos
        # We need to handle ties in play counts correctly for stable ranking if possible,
        # but for y_pos, the actual sorted order is what matters.
        sorted_current_entities = current_top_n_entities.sort_values(ascending=False)
        
        for rank, (entity_id, plays) in enumerate(sorted_current_entities.items()):
            current_keyframe_target_render_data[entity_id] = {
                "plays": float(plays),
                "y_pos": float(rank), # Target y_pos is its rank (0 for top, n_bars_config-1 for bottom)
                "rank": rank 
            }

        if keyframe_idx == 0:
            # For the very first keyframe, no animation. Just display the state.
            bar_render_data_list_for_frame = []
            for entity_id, data in current_keyframe_target_render_data.items():
                if data["rank"] < n_bars_config: # Ensure it's within the N bars to draw
                    bar_render_data_list_for_frame.append({
                        "entity_id": entity_id,
                        "interpolated_play_count": data["plays"],
                        "interpolated_y_position": data["y_pos"],
                        "current_rank": data["rank"] # The rank in *this* keyframe
                    })
            
            render_tasks.append({
                "overall_frame_index": overall_frame_index_counter,
                "display_timestamp": timestamp,
                "bar_render_data_list": bar_render_data_list_for_frame,
                "is_keyframe_end_frame": True,
                "rolling_window_info": rolling_stats_data.get(timestamp, {'top_7_day': None, 'top_30_day': None}),
                "nightingale_info": nightingale_data.get(timestamp, {}) if nightingale_data else {}
            })
            overall_frame_index_counter += 1
        else:
            # This is a subsequent keyframe, so we need to interpolate from previous_keyframe_render_data
            
            # --- Identify all unique entities involved in the transition ---
            # These are entities present in the top N of the previous OR current keyframe
            all_involved_entity_ids = set(previous_keyframe_render_data.keys()) | set(current_keyframe_target_render_data.keys())

            # --- Generate Tween Frames ---
            for tween_idx in range(num_tween_frames):
                progress = (tween_idx + 1) / num_tween_frames # Progress from 0 (exclusive) to 1 (inclusive)
                
                # Apply an easing function to progress for smoother animation (optional, but nice)
                # Example: ease-in-out sine
                # progress = 0.5 * (1 - np.cos(progress * np.pi))

                bar_render_data_list_for_tween_frame = []

                for entity_id in all_involved_entity_ids:
                    prev_data = previous_keyframe_render_data.get(entity_id)
                    curr_data = current_keyframe_target_render_data.get(entity_id)

                    # --- Determine start and end values for interpolation ---
                    # Start plays and y_pos:
                    # If song was in previous top N, use its data.
                    # If song is NEW (not in prev top N), it "animates in".
                    # For animating in, start plays at 0 (or a very small value).
                    # Start y_pos could be just below the chart (e.g., n_bars_config) or from a previous rank if it was > N_BARS
                    start_plays = prev_data["plays"] if prev_data else 0.0
                    # If new, animate from bottom; if was present, use its old y_pos
                    start_y_pos = prev_data["y_pos"] if prev_data else float(n_bars_config) 

                    # End plays and y_pos:
                    # If song is in current top N, use its data.
                    # If song is DROPPING OUT (not in current top N), it "animates out".
                    # For animating out, end plays at 0 (or a very small value).
                    # End y_pos could be just below the chart (e.g., n_bars_config).
                    end_plays = curr_data["plays"] if curr_data else 0.0
                     # If dropping out, animate to bottom; if present, use its new y_pos
                    end_y_pos = curr_data["y_pos"] if curr_data else float(n_bars_config)
                    
                    # Current rank for art/color lookup should be its rank in the TARGET keyframe if it exists there,
                    # otherwise, its rank in the PREVIOUS keyframe if it's animating out.
                    # This helps keep art stable for items moving towards their final position.
                    # If it's a new item animating in, it doesn't have a previous rank to use for art.
                    # If it's an old item animating out, it doesn't have a current rank for art.
                    # We need a consistent "current_rank_for_art_lookup_during_tween"
                    # Let's use the target rank if available, else previous rank.
                    # If a song is only in one of the frames, its rank is effectively its position there.
                    
                    target_rank_in_current_keyframe = curr_data["rank"] if curr_data else n_bars_config 
                    # rank_for_art_lookup = curr_data.get("rank") if curr_data else (prev_data.get("rank") if prev_data else n_bars_config)


                    # Interpolate
                    interpolated_plays = start_plays + (end_plays - start_plays) * progress
                    interpolated_y = start_y_pos + (end_y_pos - start_y_pos) * progress
                    
                    # Only add to render list if it's potentially visible (e.g., y_pos is somewhat on screen)
                    # and plays are > 0 (or a tiny epsilon if you want to see bars shrink completely)
                    # A song is "active" if it was in prev or is in current.
                    # We want to draw it if its interpolated_y is roughly within chart bounds.
                    if interpolated_y < n_bars_config + 1 and interpolated_y > -2: # Allow slight over/undershoot for effect
                        bar_render_data_list_for_tween_frame.append({
                            "entity_id": entity_id,
                            "interpolated_play_count": interpolated_plays,
                            "interpolated_y_position": interpolated_y,
                            "current_rank": target_rank_in_current_keyframe # Use target rank for consistency
                        })
                
                # Sort bars for this tween frame by their current interpolated_y_position before adding to task
                # This ensures that if bars cross, they are drawn in the correct z-order if matplotlib respects drawing order (it usually does)
                bar_render_data_list_for_tween_frame.sort(key=lambda x: x["interpolated_y_position"])

                render_tasks.append({
                    "overall_frame_index": overall_frame_index_counter,
                    "display_timestamp": timestamp, # Display timestamp of the TARGET keyframe
                    "bar_render_data_list": bar_render_data_list_for_tween_frame,
                    "is_keyframe_end_frame": False,
                    "rolling_window_info": rolling_stats_data.get(timestamp, {'top_7_day': None, 'top_30_day': None}),
                "nightingale_info": nightingale_data.get(timestamp, {}) if nightingale_data else {}
                })
                overall_frame_index_counter += 1

            # --- Add the final keyframe state (end of transition) ---
            bar_render_data_list_for_keyframe_end = []
            for entity_id, data in current_keyframe_target_render_data.items():
                 if data["rank"] < n_bars_config:
                    bar_render_data_list_for_keyframe_end.append({
                        "entity_id": entity_id,
                        "interpolated_play_count": data["plays"],
                        "interpolated_y_position": data["y_pos"],
                        "current_rank": data["rank"]
                    })
            # Sort final keyframe bars by their y_position (rank)
            bar_render_data_list_for_keyframe_end.sort(key=lambda x: x["interpolated_y_position"])

            render_tasks.append({
                "overall_frame_index": overall_frame_index_counter,
                "display_timestamp": timestamp,
                "bar_render_data_list": bar_render_data_list_for_keyframe_end,
                "is_keyframe_end_frame": True,
                "rolling_window_info": rolling_stats_data.get(timestamp, {'top_7_day': None, 'top_30_day': None}),
                "nightingale_info": nightingale_data.get(timestamp, {}) if nightingale_data else {}
            })
            overall_frame_index_counter += 1

        # Update previous_keyframe_render_data for the next iteration
        # It should store the state of *all* songs that were in the top N of the current_keyframe_series,
        # not just what was drawn if N_BARS was smaller.
        # For songs that dropped out, they won't be in current_keyframe_target_render_data.
        # For entities that are new, they will be.
        previous_keyframe_render_data.clear()
        for entity_id, data in current_keyframe_target_render_data.items():
             previous_keyframe_render_data[entity_id] = {"plays": data["plays"], "y_pos": data["y_pos"], "rank": data["rank"]}
        
    print(f"Generated {len(render_tasks)} total render tasks (frames).")
    return render_tasks

def draw_and_save_single_frame(args):
    # Unpack arguments
    # The first argument is now the 'render_task' dictionary
    global worker_pids_reported
    (render_task, num_total_output_frames,
    entity_id_to_canonical_name_map, # Maps entity_id -> canonical_name (for art/color cache keys)
    entity_details_map_main,          # The main entity_details_map with display info
    album_art_image_objects_local, album_art_image_objects_highres_local, album_bar_colors_local,
    n_bars_local, chart_xaxis_limit_overall_scale, 
    output_image_path, dpi, fig_width_pixels, fig_height_pixels,
    log_frame_times_config_local, preferred_fonts_local,
    log_parallel_process_start_local,
    # Rolling stats display configs
    rs_panel_area_left_fig, rs_panel_area_right_fig, rs_panel_title_y_from_top_fig,
    rs_title_to_content_gap_fig, rs_title_font_size, rs_song_artist_font_size,
    rs_plays_font_size, rs_art_height_fig, rs_art_aspect_ratio, rs_art_max_width_fig,
    rs_art_padding_right_fig, rs_text_padding_left_fig, rs_text_to_art_horizontal_gap_fig,
    rs_text_line_vertical_spacing_fig, rs_song_artist_to_plays_gap_fig, rs_inter_panel_vertical_spacing_fig,
    # New args for panel title x and truncation adjustment
    rs_panel_title_x_fig_config, rs_text_truncation_adjust_px_config,
    # New args for main timestamp position
    main_timestamp_x_fig_config, main_timestamp_y_fig_config,
    # Mode information
    visualization_mode_local,
    # Debug flags
    memory_debug_local
    ) = args

    # Extract data from render_task
    overall_frame_idx = render_task['overall_frame_index']
    display_timestamp = render_task['display_timestamp']
    bar_render_data_list = render_task['bar_render_data_list']
    rolling_window_info_for_frame = render_task.get('rolling_window_info', {'top_7_day': None, 'top_30_day': None})
    nightingale_info_for_frame = render_task.get('nightingale_info', {})

    # Each process needs to ensure matplotlib backend and font family are set correctly
    try:
        # Ensure Agg backend is set in worker process (critical for multiprocessing)
        import matplotlib
        current_backend = matplotlib.get_backend()
        if current_backend != 'Agg':
            matplotlib.use('Agg')
            print(f"[Worker PID: {os.getpid()}] Set matplotlib backend to Agg (was {current_backend})")
        
        plt.rcParams['font.family'] = preferred_fonts_local
    except Exception as e_setup:
        print(f"[Worker PID: {os.getpid()}] Warning: Worker setup error: {e_setup}")

    frame_start_time = time.monotonic()
    
    # Memory monitoring for debugging worker process issues
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_before_mb = process.memory_info().rss / 1024**2
        if memory_debug_local:  # Only log if memory debug is enabled
            print(f"[Worker PID: {os.getpid()}] Frame {overall_frame_idx} starting. Memory: {mem_before_mb:.1f} MB")
    except ImportError:
        mem_before_mb = None  # psutil not available
    except Exception:
        mem_before_mb = None  # Other error
    
    figsize_w = fig_width_pixels / dpi
    figsize_h = fig_height_pixels / dpi
    fig, ax = plt.subplots(figsize=(figsize_w, figsize_h), dpi=dpi)

    try: # Ensure fig is closed even on error
        # --- Define margins for the main chart area (ax) BEFORE drawing ---
        # These values will be used for both text truncation calculation and final layout.
        left_margin_ax = 0.28  # Space on the left for the rolling stats panel
        right_margin_ax = 0.985 # Small gap on the right
        bottom_margin_ax = 0.08 # Space at the bottom for the main timestamp
        top_margin_ax = 0.98    # Space at the top for x-axis labels/title

        # --- Worker Process Startup Message ---
        if log_parallel_process_start_local:
            worker_pid = os.getpid()
            if worker_pid not in worker_pids_reported:
                print(f"--- Worker process with PID {worker_pid} has started and is processing frames. ---")
                worker_pids_reported.add(worker_pid)

        # --- Main Chart Area (ax) ---
        date_str = display_timestamp.strftime('%d %B %Y %H:%M:%S')
        # ax.text(0.98, 0.05, date_str, transform=ax.transAxes, # Removed from here
        #         ha='right', va='bottom', fontsize=20 * (dpi/100.0), color='dimgray', weight='bold')

        ax.set_xlabel("Total Plays", fontsize=18 * (dpi/100.0), labelpad=15 * (dpi/100.0))
        
        # --- Dynamic X-axis Limit Calculation (based on current frame's max plays) ---
        current_frame_max_play_count = 0
        if bar_render_data_list:
            # Get max play count from the songs *actually being rendered* in this frame
            # This is important because bar_render_data_list might contain songs animating out with small values
            # or songs animating in. We want the x-axis to adapt to the visible maximum.
            visible_play_counts = [item['interpolated_play_count'] for item in bar_render_data_list if item['interpolated_play_count'] > 0.1] # Consider only somewhat visible bars
            if visible_play_counts:
                current_frame_max_play_count = max(visible_play_counts)
        
        # If all current plays are 0 (or very small), default to a small limit
        dynamic_x_axis_limit = max(10, current_frame_max_play_count) * 1.10 # 10% padding, min limit 10
        ax.set_xlim(0, dynamic_x_axis_limit)
        
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        ax.xaxis.set_ticks_position('top')
        ax.xaxis.set_label_position('top')
        tick_label_fontsize = 11 * (dpi/100.0)
        ax.tick_params(axis='x', labelsize=tick_label_fontsize)

        # --- Y-Axis setup ---
        ax.set_ylim(n_bars_local - 0.5, -0.5) # Inverted: 0 is top, n_bars_local-1 is bottom
        ax.set_yticks(np.arange(n_bars_local)) 
        ax.set_yticklabels([]) 
        ax.tick_params(axis='y', length=0)

        max_char_len_song_name = int(50 * (150.0/dpi)) 
        value_label_fontsize = 12 * (dpi/100.0)
        song_name_fontsize = tick_label_fontsize
        
        image_padding_data_units = dynamic_x_axis_limit * 0.005 
        value_label_padding_data_units = dynamic_x_axis_limit * 0.008
        song_name_padding_from_left_spine_data_units = dynamic_x_axis_limit * 0.005


        for bar_item_data in bar_render_data_list:
            entity_id = bar_item_data['entity_id']
            interpolated_plays = bar_item_data['interpolated_play_count']
            interpolated_y_pos = bar_item_data['interpolated_y_position']

            if interpolated_plays < 0.01: 
                continue

            entity_master_details = entity_details_map_main.get(entity_id, {})
            
            # Mode-aware text display
            if visualization_mode_local == "artists":
                # In artist mode, entity_id is the artist name
                display_artist_name = entity_master_details.get('display_artist', entity_id)
                full_display_name = display_artist_name  # Just show artist name
            else:
                # In tracks mode, show track - artist format
                display_artist_name = entity_master_details.get('display_artist')
                display_track_name = entity_master_details.get('display_track')
                
                if display_artist_name is None: display_artist_name = entity_id.split(' - ')[0] if ' - ' in entity_id else entity_id
                if display_track_name is None: display_track_name = entity_id.split(' - ')[1] if ' - ' in entity_id else ''

                full_display_name = f"{display_track_name} - {display_artist_name}" # Song - Artist
                if not display_track_name and display_artist_name: full_display_name = display_artist_name
                elif not display_artist_name and display_track_name: full_display_name = display_track_name
                elif not display_track_name and not display_artist_name: full_display_name = entity_id # Fallback to entity_id

            art_color_cache_key = entity_id_to_canonical_name_map.get(entity_id, "Unknown")
            bar_color = album_bar_colors_local.get(art_color_cache_key, (0.5,0.5,0.5))
            pil_image = album_art_image_objects_local.get(art_color_cache_key)

            actual_bar = ax.barh(interpolated_y_pos, interpolated_plays, color=bar_color, height=0.8, zorder=2, align='center')
            
            # Define text properties first, to use them in subsequent calculations
            text_bbox_props = dict(boxstyle="round,pad=0.2,rounding_size=0.1", facecolor="#333333", alpha=0.5, edgecolor="none")

            # --- Dynamically compute available width for the song label and truncate if needed ---
            start_x_data = song_name_padding_from_left_spine_data_units

            # Determine the data-coordinate x where text must stop
            right_gap_units = dynamic_x_axis_limit * SONG_TEXT_RIGHT_GAP_FRACTION
            if pil_image:
                resized_img_w_pix, _ = pil_image.size
                image_width_units = (resized_img_w_pix / fig_width_pixels) * dynamic_x_axis_limit if fig_width_pixels > 0 else 0
                # Account for the horizontal nudge factor that shifts art left
                art_nudge_units = dynamic_x_axis_limit * 0.0175  # matches art_horizontal_nudge_factor below
                art_left_edge = interpolated_plays - image_width_units - art_nudge_units
                end_x_data = art_left_edge - right_gap_units
            else:
                end_x_data = interpolated_plays - value_label_padding_data_units - right_gap_units

            # --- CORRECTED: Convert available data range to pixels using actual axis width ---
            available_px = 0
            if end_x_data > start_x_data:
                # Calculate the pixel width of the main chart axes
                ax_width_in_fig_coords = right_margin_ax - left_margin_ax
                ax_width_pixels = ax_width_in_fig_coords * fig_width_pixels
                
                # Convert the available width from data coordinates to pixels
                available_px = (end_x_data - start_x_data) / dynamic_x_axis_limit * ax_width_pixels

                # --- CORRECTED: Account for the padding of the text's bounding box ---
                # The 'pad' in boxstyle is a multiplier for the font size.
                bbox_pad_multiplier = 0.2 # As defined in text_bbox_props
                # Total horizontal padding (left + right) in points. song_name_fontsize is in points.
                bbox_horizontal_padding_points = 2 * bbox_pad_multiplier * song_name_fontsize
                # Convert padding from points to pixels. 1 point = 1/72 inch.
                bbox_horizontal_padding_pixels = bbox_horizontal_padding_points * (dpi / 72.0)
                
                available_px -= bbox_horizontal_padding_pixels

            font_props = fm.FontProperties(size=song_name_fontsize)
            renderer = fig.canvas.get_renderer()
            text_to_display_for_song = truncate_to_fit(full_display_name, font_props, renderer, max(0, available_px))

            song_text_obj = ax.text(
                song_name_padding_from_left_spine_data_units,
                interpolated_y_pos,
                text_to_display_for_song,
                va="center",
                ha="left",
                fontsize=song_name_fontsize,
                color="white",
                zorder=5,
                bbox=text_bbox_props,
            )

            current_x_anchor_for_art = interpolated_plays 
            if pil_image:
                try:
                    resized_img_width_pixels, resized_img_height_pixels = pil_image.size 
                    x_axis_range_data_units = dynamic_x_axis_limit 
                    image_width_data_units = 0
                    if fig_width_pixels > 0 and x_axis_range_data_units > 0: 
                         image_width_data_units = (resized_img_width_pixels / fig_width_pixels) * x_axis_range_data_units
                    
                    # To manually nudge the art: >0 shifts art left, <0 shifts art right from the bar's end.
                    art_horizontal_nudge_factor = 0.0175 # YOU CAN TWEAK THIS. Example: 0.001 to shift slightly left.
                    img_center_x_pos = interpolated_plays - (image_width_data_units / 2.0) - (dynamic_x_axis_limit * art_horizontal_nudge_factor)
                    
                    min_x_for_image_start = dynamic_x_axis_limit * 0.02
                    if img_center_x_pos - (image_width_data_units / 2.0) > min_x_for_image_start:
                        imagebox = OffsetImage(pil_image, zoom=1.0, resample=False)
                        ab = AnnotationBbox(imagebox, (img_center_x_pos, interpolated_y_pos), 
                                            xybox=(0,0), xycoords='data', boxcoords="offset points",
                                            pad=0, frameon=False, zorder=3)
                        ax.add_artist(ab)
                except Exception as e_img:
                    print(f"Error (PID {os.getpid()}) adding image for {art_color_cache_key} (Entity: {entity_id}): {e_img}")

            # --- Numeric play-count label ---
            text_x_pos_for_value = interpolated_plays + value_label_padding_data_units
            ax.text(
                text_x_pos_for_value,
                interpolated_y_pos,
                f"{int(round(interpolated_plays))}",
                va="center",
                ha="left",
                fontsize=value_label_fontsize,
                weight="bold",
                zorder=4,
            )

        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_linewidth(1.5 * (dpi/100.0))
        ax.grid(True, axis='y', linestyle=':', color='lightgray', alpha=0.7, zorder=0)
        
        # --- Layout Adjustment for ax BEFORE adding other figure elements ---
        # The margin values are now defined at the top of the function's try block.
        try:
            # Apply tight_layout to the main axes (ax) first, considering the rect.
            # This adjusts 'ax' to fit nicely within the defined margins.
            fig.tight_layout(rect=[left_margin_ax, bottom_margin_ax, right_margin_ax, top_margin_ax])
        except Exception as e_layout:
            print(f"Note (PID {os.getpid()}): Layout adjustment warning/error for main ax: {e_layout}.")
            # Fallback if tight_layout fails for ax
            plt.subplots_adjust(left=left_margin_ax, bottom=bottom_margin_ax, right=right_margin_ax, top=top_margin_ax, wspace=0, hspace=0)

        # --- Rolling Window Stats Display (Left Panel) ---
        # This section uses fig.text and fig.add_axes for placement in figure coordinates
        
        # Define areas for 7-day and 30-day stats
        # Positions are (left, bottom, width, height) in figure-normalized coords (0-1)
        # These are approximate and will need refinement.
        
        # Common font size for rolling stats text
        # rolling_text_fontsize = 10 * (dpi / 100.0) # Old
        # rolling_title_fontsize = 12 * (dpi / 100.0) # Old

        # Helper function to draw a single rolling stat panel
        def draw_rolling_stat_panel(fig, panel_data, panel_title_text,
                                    panel_y_top_fig_boundary, # Top Y boundary for this panel's content
                                    song_id_map, art_objects,
                                    rs_config_params):
            
            if not panel_data:
                return panel_y_top_fig_boundary # Return current Y boundary if no data to draw

            # Unpack rs_config_params (could also pass them individually)
            # For brevity, accessing them directly from the outer scope as they are now args to draw_and_save_single_frame
            
            # Mode-aware text formatting
            if visualization_mode_local == "artists":
                # For artist mode: show just the artist name
                song_artist_text = panel_data.get('original_artist', 'Unknown Artist')
            else:
                # For tracks mode: show "Track - Artist" format
                display_artist = panel_data.get('original_artist', 'Unknown Artist')
                display_track = panel_data.get('original_track', 'Unknown Track')
                song_artist_text = f"{display_track} - {display_artist}"
            
            plays_text = f"{panel_data['plays']} plays"

            # Font properties for truncation
            renderer = fig.canvas.get_renderer()
            song_artist_font_props = fm.FontProperties(family=preferred_fonts_local, size=rs_song_artist_font_size)
            
            # --- Calculate panel content dimensions and positions ---
            # Panel horizontal boundaries
            panel_x_start_abs = rs_panel_area_left_fig
            panel_x_end_abs = rs_panel_area_right_fig

            # Art dimensions - mode-aware key access
            entity_key = "artist_id" if visualization_mode_local == "artists" else "song_id"
            art_key = song_id_map.get(panel_data[entity_key], "Unknown Album")
            art_obj = album_art_image_objects_highres_local.get(art_key)
            if art_obj is None:
                # Fallback to the smaller image if hi-res is unavailable.
                art_obj = album_art_image_objects_local.get(art_key)
            actual_art_height_fig = rs_art_height_fig
            actual_art_width_fig = 0
            if art_obj:
                img_aspect = art_obj.width / art_obj.height if art_obj.height > 0 else (rs_art_aspect_ratio if rs_art_aspect_ratio > 0 else 1.0)
                actual_art_width_fig = actual_art_height_fig * img_aspect
                if rs_art_max_width_fig > 0 and actual_art_width_fig > rs_art_max_width_fig:
                    actual_art_width_fig = rs_art_max_width_fig
                    if img_aspect > 0: # Recalculate height if width is capped
                         actual_art_height_fig = actual_art_width_fig / img_aspect
            else: # No art, use configured aspect ratio if > 0, else square
                img_aspect = rs_art_aspect_ratio if rs_art_aspect_ratio > 0 else 1.0
                actual_art_width_fig = actual_art_height_fig * img_aspect
                if rs_art_max_width_fig > 0 and actual_art_width_fig > rs_art_max_width_fig:
                    actual_art_width_fig = rs_art_max_width_fig
                    if img_aspect > 0:
                        actual_art_height_fig = actual_art_width_fig / img_aspect
            
            # Art position (right-aligned within its allocated space in panel)
            art_x_fig = panel_x_end_abs - rs_art_padding_right_fig - actual_art_width_fig

            # Text X position (left-aligned within panel)
            # text_x_fig = panel_x_start_abs + rs_text_padding_left_fig # Old: for left align

            # --- New: Calculate boundaries for text centering ---
            text_x_left_boundary_fig = panel_x_start_abs + rs_text_padding_left_fig
            text_x_right_boundary_fig = art_x_fig - rs_text_to_art_horizontal_gap_fig
            # Ensure right boundary is not to the left of left boundary
            if text_x_right_boundary_fig < text_x_left_boundary_fig:
                text_x_right_boundary_fig = text_x_left_boundary_fig
            
            centered_text_x_fig = text_x_left_boundary_fig + (text_x_right_boundary_fig - text_x_left_boundary_fig) / 2.0


            # Available width for song/artist text (for truncation)
            # This is the space between the start of the text and the left edge of the art, minus a gap.
            available_text_width_fig = text_x_right_boundary_fig - text_x_left_boundary_fig # Max available width for centered text
            max_width_px_for_song_text = (available_text_width_fig * fig_width_pixels) + rs_text_truncation_adjust_px_config # Added adjustment
            
            truncated_song_artist_text = truncate_to_fit(song_artist_text, song_artist_font_props, renderer, max_width_px_for_song_text if max_width_px_for_song_text > 0 else 0)

            # --- Vertical positioning (centering text block with art) ---
            # Y coordinates are from bottom of the figure (0.0 to 1.0)
            # panel_y_top_fig_boundary is the upper Y limit for this panel's drawing operations.
            
            # Draw Panel Title – centred horizontally within the panel area.
            title_center_x_fig = (panel_x_start_abs + panel_x_end_abs) / 2.0
            # Use configured X if provided, otherwise use calculated center
            actual_title_x_fig = rs_panel_title_x_fig_config if rs_panel_title_x_fig_config != -1.0 else title_center_x_fig
            title_y_fig = panel_y_top_fig_boundary  # y-position (from bottom) for the top-aligned title text

            fig.text(actual_title_x_fig, title_y_fig, panel_title_text,
                     fontsize=rs_title_font_size, color='black', # Changed color, removed bold
                     ha='center', va='top', transform=fig.transFigure) # Remains centered on its x-coordinate

            # Content area starts below the title
            # Estimate title height based on font size (very approximate, or use a fixed fig unit)
            # A simpler approach: fixed gap after title baseline.
            # Assume title_y_fig is baseline. Content starts below.
            # For va='top', title_y_fig is top. Content area starts below its effective height.
            # Let's use a fixed fig unit for text line height estimate based on font points.
            # Example: 1 point = 1/72 inch. fig_height_inches = fig_height_pixels / dpi.
            # font_size_in_fig_units_y = (font_size_points / 72) / (fig_height_pixels / dpi)
            title_font_height_approx_fig = (rs_title_font_size / 72) / (fig_height_pixels / dpi) # Approx height
            
            content_top_y_fig = title_y_fig - title_font_height_approx_fig - rs_title_to_content_gap_fig


            # Determine vertical center for art and text block
            # Art will be vertically centered in its available height `actual_art_height_fig`
            # Text lines (Song/Artist, Plays) will form a block. This block is centered with art.
            art_center_y_fig = content_top_y_fig - (actual_art_height_fig / 2.0)
            art_y_bottom_fig = art_center_y_fig - (actual_art_height_fig / 2.0)

            # Place album art
            if art_obj:
                art_ax = fig.add_axes([art_x_fig, art_y_bottom_fig, actual_art_width_fig, actual_art_height_fig])
                art_ax.imshow(art_obj)
                art_ax.axis('off')

            # Text lines (Song/Artist, Plays) centered with art_center_y_fig
            # The two lines (Song/Artist, Plays) are stacked.
            # Let their combined logical height including spacing be H.
            # Song/Artist line center_y = art_center_y_fig + (spacing / 2)
            # Plays line center_y = art_center_y_fig - (spacing / 2)
            
            # song_artist_line_y_fig = art_center_y_fig + (rs_text_line_vertical_spacing_fig / 2.0) # Old
            # plays_line_y_fig = art_center_y_fig - (rs_text_line_vertical_spacing_fig / 2.0) # Old

            # --- New vertical positioning for Song/Artist and Plays using rs_song_artist_to_plays_gap_fig ---
            # Approximate text heights in figure units to help position them around the gap
            song_artist_text_height_fig = (rs_song_artist_font_size / 72) / (fig_height_pixels / dpi) if fig_height_pixels > 0 and dpi > 0 else 0.01
            plays_text_height_fig = (rs_plays_font_size / 72) / (fig_height_pixels / dpi) if fig_height_pixels > 0 and dpi > 0 else 0.01

            # The rs_song_artist_to_plays_gap_fig is the distance between the baseline of song/artist
            # and baseline of plays. For va='center', we adjust.
            # To make rs_song_artist_to_plays_gap_fig the visual space between the two blocks of text:
            song_artist_line_y_fig = art_center_y_fig + (rs_song_artist_to_plays_gap_fig / 2.0) + (plays_text_height_fig / 2.0)
            plays_line_y_fig       = art_center_y_fig - (rs_song_artist_to_plays_gap_fig / 2.0) - (song_artist_text_height_fig / 2.0)


            # Draw Song/Artist text
            fig.text(centered_text_x_fig, song_artist_line_y_fig, truncated_song_artist_text,
                     fontsize=rs_song_artist_font_size, color='black', # Using black for now
                     ha='center', va='center', transform=fig.transFigure) # Changed to ha='center' and new x
            
            # Draw Plays text
            fig.text(centered_text_x_fig, plays_line_y_fig, plays_text,
                     fontsize=rs_plays_font_size, color='dimgray',
                     ha='center', va='center', transform=fig.transFigure) # Changed to ha='center' and new x
            
            # Calculate bottom Y of this panel for stacking next one
            # Bottom is min of (art bottom, plays text bottom)
            # Estimate text height for plays line:
            # plays_font_height_approx_fig = (rs_plays_font_size / 72) / (fig_height_pixels / dpi) # Already calculated as plays_text_height_fig
            plays_text_baseline_approx_y_fig = plays_line_y_fig - (plays_text_height_fig / 2.0) # Approximate bottom of plays text
            
            panel_bottom_y_fig = min(art_y_bottom_fig, plays_text_baseline_approx_y_fig)
            return panel_bottom_y_fig


        # --- Draw 7-Day Stats Panel ---
        current_y_top_boundary = 1.0 - rs_panel_title_y_from_top_fig # Convert "from top" to "from bottom" for text
        
        stats_7_day_data = rolling_window_info_for_frame.get('top_7_day')
        # Mode-aware panel title
        panel_title_7_day = "Top Artist - Last 7 Days" if visualization_mode_local == "artists" else "Top Tracks - Last 7 Days"
        panel_7_day_bottom_y = draw_rolling_stat_panel(fig, stats_7_day_data, panel_title_7_day,
                                                       current_y_top_boundary,
                                                       entity_id_to_canonical_name_map, 
                                                       album_art_image_objects_local,
                                                       (rs_panel_title_x_fig_config, rs_text_truncation_adjust_px_config) 
                                                       ) 

        # --- Draw 30-Day Stats Panel ---
        # Position below the 7-day panel
        if panel_7_day_bottom_y is not None: # If 7-day panel was drawn
             # Estimate title height for calculating where the next title starts
            title_font_height_approx_fig_next = (rs_title_font_size / 72) / (fig_height_pixels / dpi)
            y_top_for_30_day_title = panel_7_day_bottom_y - rs_inter_panel_vertical_spacing_fig - title_font_height_approx_fig_next
        else: # If 7-day panel was not drawn, 30-day panel starts where 7-day would have.
            y_top_for_30_day_title = current_y_top_boundary 

        stats_30_day_data = rolling_window_info_for_frame.get('top_30_day')
        # Mode-aware panel title
        panel_title_30_day = "Top Artist - Last 30 Days" if visualization_mode_local == "artists" else "Top Tracks - Last 30 Days"
        draw_rolling_stat_panel(fig, stats_30_day_data, panel_title_30_day,
                                y_top_for_30_day_title, # This is the Y for the title's top
                                entity_id_to_canonical_name_map,
                                album_art_image_objects_local, # This should be album_art_image_objects_highres_local for consistency
                                # Pass None for rs_config_params as they are accessed from outer scope
                                # but we need to pass the new specific configs
                                (rs_panel_title_x_fig_config, rs_text_truncation_adjust_px_config)
                                )
        
        # --- Draw Nightingale Chart (if enabled and data available) ---
        if ENABLE_NIGHTINGALE and nightingale_info_for_frame:
            nightingale_config = {
                # Chart Position & Size (Simplified)
                'center_x': NIGHTINGALE_CENTER_X_FIG,
                'center_y': NIGHTINGALE_CENTER_Y_FIG,
                'radius': NIGHTINGALE_RADIUS_FIG,
                
                # Month Labels (Simplified)
                'show_labels': NIGHTINGALE_SHOW_PERIOD_LABELS,
                'label_radius_ratio': NIGHTINGALE_LABEL_RADIUS_RATIO,
                'label_font_size': NIGHTINGALE_LABEL_FONT_SIZE,
                'label_font_color': NIGHTINGALE_LABEL_FONT_COLOR,
                'label_font_weight': NIGHTINGALE_LABEL_FONT_WEIGHT,
                
                # Title (Simplified)
                'title_font_size': NIGHTINGALE_TITLE_FONT_SIZE,
                'title_font_weight': NIGHTINGALE_TITLE_FONT_WEIGHT,
                'title_color': NIGHTINGALE_TITLE_COLOR,
                'title_y_offset_fig': NIGHTINGALE_TITLE_POSITION_ABOVE_CHART,
                
                # High/Low Tracker (Simplified)
                'show_high_low': NIGHTINGALE_SHOW_HIGH_LOW_INFO,
                'high_low_font_size': NIGHTINGALE_HIGH_LOW_FONT_SIZE,
                'high_low_y_offset_fig': NIGHTINGALE_HIGH_LOW_Y_OFFSET_FIG,
                'high_low_spacing_fig': NIGHTINGALE_HIGH_LOW_SPACING_FIG,
                'high_period_color': NIGHTINGALE_HIGH_PERIOD_COLOR,
                'low_period_color': NIGHTINGALE_LOW_PERIOD_COLOR,
                
                # Advanced Options (Simplified)
                'show_boundary_circle': NIGHTINGALE_SHOW_BOUNDARY_CIRCLE,
                'outer_circle_color': NIGHTINGALE_OUTER_CIRCLE_COLOR,
                'outer_circle_linestyle': NIGHTINGALE_OUTER_CIRCLE_LINESTYLE,
                'outer_circle_linewidth': NIGHTINGALE_OUTER_CIRCLE_LINEWIDTH,
                'enable_smooth_transitions': NIGHTINGALE_ENABLE_SMOOTH_TRANSITIONS,
                'transition_duration_seconds': NIGHTINGALE_TRANSITION_DURATION_SECONDS,
                'animation_easing_function': NIGHTINGALE_ANIMATION_EASING_FUNCTION,
                'debug': NIGHTINGALE_DEBUG
            }
            
            try:
                if NIGHTINGALE_DEBUG:
                    print(f"[DEBUG] Calling draw_nightingale_chart with center_y: {nightingale_config['center_y']}")
                draw_nightingale_chart(fig, nightingale_info_for_frame, nightingale_config)
            except Exception as e_nightingale:
                print(f"Warning: Error drawing nightingale chart for frame {overall_frame_idx}: {e_nightingale}")
                # Continue without nightingale chart if there's an error


        # --- Timestamp Display (Below Chart) ---
        # Manual controls for timestamp position (in figure-normalized coordinates 0-1)
        # timestamp_y_fig_coord = 0.04  # YOU CAN TWEAK THIS: Vertical position from bottom (e.g., 0.04 is 4% from bottom)
        # Use configured Y position
        actual_timestamp_y_fig = main_timestamp_y_fig_config
        
        # Calculate x-coordinate to align with the center of the main chart axes (ax)
        # ax spans from left_margin (defined below before fig.tight_layout) to right_margin in figure coordinates.
        # Need to use the actual margin values that will be used for the current frame's layout.
        current_left_margin_for_ax = left_margin_ax # Use the same left margin as ax
        current_right_margin_for_ax = right_margin_ax # Use the same right margin as ax
        ax_center_x_fig_coord = current_left_margin_for_ax + (current_right_margin_for_ax - current_left_margin_for_ax) / 2.0
        # Use configured X if provided, otherwise use calculated ax center
        actual_timestamp_x_fig = main_timestamp_x_fig_config if main_timestamp_x_fig_config != -1.0 else ax_center_x_fig_coord
        # timestamp_x_fig_coord = ax_center_x_fig_coord # Align timestamp center with ax center

        fig.text(actual_timestamp_x_fig, actual_timestamp_y_fig, date_str, 
                 fontsize=20 * (dpi/100.0), color='dimgray', weight='bold', 
                 ha='center', va='center', transform=fig.transFigure)

        # --- Layout Adjustment ---
        # left_margin = 0.18 # Original
        # left_margin = 0.25 # Adjusted to make space for left panel
        # right_margin = 0.98
        # bottom_margin = 0.10 # Original
        # bottom_margin = 0.08 # Adjusted to make space for timestamp below ax
        # top_margin = 0.98
        
        # The main tight_layout call for 'ax' has been moved earlier.
        # No further global tight_layout or subplots_adjust needed here,
        # as other elements (rolling stats, timestamp) are manually placed.
        # try:
            # Apply tight_layout to the main axes (ax) first, considering the rect.
            # The fig.text and fig.add_axes for rolling stats are placed in figure coordinates
            # and are not directly affected by ax.tight_layout, but the rect defines ax's space.
        #    fig.tight_layout(rect=[left_margin, bottom_margin, right_margin, top_margin])
        # except Exception as e_layout:
        #    print(f"Note (PID {os.getpid()}): Layout adjustment warning/error: {e_layout}.")
            # Fallback if tight_layout fails
        #    plt.subplots_adjust(left=left_margin, bottom=bottom_margin, right=right_margin, top=top_margin, wspace=0, hspace=0)
        
        fig.savefig(output_image_path)

    except Exception as e:
        import traceback
        pid = os.getpid()
        error_log_path = f"error_worker_pid_{pid}_frame_{overall_frame_idx}.log"
        
        # Print to console for immediate visibility
        print(f"ERROR in draw_and_save_single_frame (PID: {pid}, Frame: {overall_frame_idx}): {e}")
        print(f"Full traceback written to: {error_log_path}")
        
        # Write detailed error log to file
        try:
            with open(error_log_path, "w", encoding='utf-8') as f:
                f.write(f"Worker Process Error Report\n")
                f.write(f"========================\n")
                f.write(f"PID: {pid}\n")
                f.write(f"Frame Index: {overall_frame_idx}\n")
                f.write(f"Output Path: {output_image_path}\n")
                f.write(f"Error: {e}\n")
                f.write(f"Error Type: {type(e).__name__}\n")
                f.write(f"\nFull Traceback:\n")
                traceback.print_exc(file=f)
                f.write(f"\nPython Version: {sys.version}\n")
                f.write(f"Matplotlib Version: {matplotlib.__version__}\n")
        except Exception as log_error:
            print(f"Failed to write error log: {log_error}")
        
        # Re-raise the exception so it's caught by the ProcessPoolExecutor
        raise
    finally:
        # Critical: Close the specific figure and clear all matplotlib state
        plt.close(fig)
        # Additional safety: Clear any remaining matplotlib figures and state
        plt.close('all')
        # Force garbage collection to release memory immediately  
        import gc
        gc.collect()

    current_frame_render_time = time.monotonic() - frame_start_time
    
    # Memory monitoring - log memory usage after cleanup
    if mem_before_mb is not None and memory_debug_local:
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_after_mb = process.memory_info().rss / 1024**2
            mem_delta = mem_after_mb - mem_before_mb
            print(f"[Worker PID: {os.getpid()}] Frame {overall_frame_idx} completed. Memory: {mem_after_mb:.1f} MB (Δ{mem_delta:+.1f} MB)")
        except Exception:
            pass  # Ignore memory monitoring errors
    
    # Return overall_frame_idx for logging in the main process
    return overall_frame_idx, current_frame_render_time, os.getpid()


def create_bar_chart_race_animation(race_df, entity_details_map, rolling_stats_data, nightingale_data=None, use_serial_mode=False, max_workers_override=None, memory_debug=False): # race_df here is already potentially truncated
    if race_df is None or race_df.empty:
        print("Cannot create animation: race_df is empty or None.")
        return

    # unique_song_ids_in_race = race_df.columns.tolist() # This is ALL songs in race_df
    raw_max_play_count_overall = race_df.max().max()
    if pd.isna(raw_max_play_count_overall) or raw_max_play_count_overall <= 0:
        raw_max_play_count_overall = 100 # Fallback
    
    selected_res_key = config.get('AnimationOutput', 'RESOLUTION', '4k').strip()
    res_settings = VIDEO_RESOLUTION_PRESETS.get(selected_res_key, VIDEO_RESOLUTION_PRESETS['4k'])
    dpi = res_settings['dpi']
    fig_width_pixels = res_settings['width']
    fig_height_pixels = res_settings['height']

    example_bar_height_data_units = 0.8 
    # image_height_scale_factor = 0.35 # Old factor, to be replaced
    current_n_bars_for_sizing = N_BARS if N_BARS > 0 else 10
        
    # New calculation for target image height to match bar height
    # These margin values MUST MATCH the bottom_margin and top_margin used for 'ax' in draw_and_save_single_frame
    frame_render_ax_bottom_margin_fig_coords = 0.08 # Updated to match draw_and_save_single_frame
    frame_render_ax_top_margin_fig_coords = 0.95   # Updated to match draw_and_save_single_frame
    ax_height_in_figure_coords = frame_render_ax_top_margin_fig_coords - frame_render_ax_bottom_margin_fig_coords

    # Fraction of the ax y-axis height that one bar (data height 0.8) takes up
    bar_height_fraction_of_ax_y_axis = example_bar_height_data_units / current_n_bars_for_sizing
    
    calculated_target_img_height_pixels = (
        bar_height_fraction_of_ax_y_axis * \
        ax_height_in_figure_coords * \
        fig_height_pixels
    )
    # Optional: apply a slight scaling factor if direct match is too tight, e.g., 0.95 for 95% of bar height
    # User found 0.42 factor was needed with previous margin calculation.
    # This factor may need re-tuning after margin correction above.
    calculated_target_img_height_pixels *= 0.40 # Keep user's current factor for now
    
    # --- DEPRECATED: ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR is no longer used to gate art display ---
    # art_processing_min_plays_threshold = raw_max_play_count_overall * ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR
    # print(f"[ANIMATOR_INFO] global_visibility_threshold (art_processing_min_plays_threshold) = {art_processing_min_plays_threshold:.2f}") 
    # --- End DEPRECATED ---
    print(f"[ANIMATOR_INFO] Calculated target image height for pre-resize: {calculated_target_img_height_pixels:.2f} pixels")

    art_fetch_start_time = time.time()
    
    # --- Determine songs that will actually appear on the chart ---
    song_ids_ever_on_chart = set()
    current_n_bars = config.get_int('AnimationOutput', 'N_BARS', N_BARS) # Ensure we use the correct N_BARS
    print(f"[ANIMATOR_INFO] Determining songs that appear in top {current_n_bars} bars...")
    for timestamp, frame_data in race_df.iterrows():  # race_df here is the one passed for animation
        top_n_in_frame = frame_data[frame_data > 0].nlargest(current_n_bars)
        song_ids_ever_on_chart.update(top_n_in_frame.index.tolist())
    
    print(f"[ANIMATOR_INFO] Found {len(song_ids_ever_on_chart)} unique songs that will appear in the top {current_n_bars} bars.")
    
    # Also ensure entities that *only* appear in the rolling 7-/30-day panels have art.
    for stats_dict in rolling_stats_data.values():
        for key in ("top_7_day", "top_30_day"):
            entry = stats_dict.get(key)
            if entry:
                # Mode-aware key access
                entity_key = "artist_id" if VISUALIZATION_MODE == "artists" else "song_id"
                if entry.get(entity_key):
                    song_ids_ever_on_chart.add(entry[entity_key])
    
    # Update call to prepare_nightingale_animation_data to pass easing function
    album_art_utils.nightingale_animation_easing_function = NIGHTINGALE_ANIMATION_EASING_FUNCTION

    # Mode-aware pre-fetching: use appropriate function based on visualization mode
    if VISUALIZATION_MODE == "artists":
        entity_id_to_animator_key_map = pre_fetch_artist_photos_and_colors(
            entity_details_map, 
            list(song_ids_ever_on_chart), # Pass the list of entities that appear
            calculated_target_img_height_pixels, 
            dpi
        )
        fetch_type = "artist photos"
    else:
        entity_id_to_animator_key_map = pre_fetch_album_art_and_colors(
            entity_details_map, 
            list(song_ids_ever_on_chart), # Pass the list of songs that appear
            calculated_target_img_height_pixels, 
            dpi
        )
        fetch_type = "album art"
    
    art_fetch_end_time = time.time()
    print(f"--- Time taken for pre_fetch_{fetch_type.replace(' ', '_')}_and_colors: {art_fetch_end_time - art_fetch_start_time:.2f} seconds ---")

    # Generate mode-aware filename
    mode_suffix = "artists" if VISUALIZATION_MODE == "artists" else "songs"
    base_filename = OUTPUT_FILENAME_BASE.replace("songs", mode_suffix) if "songs" in OUTPUT_FILENAME_BASE else f"{OUTPUT_FILENAME_BASE}_{mode_suffix}"
    output_filename = f"{base_filename}_{selected_res_key}.mp4"
    # num_frames = len(race_df.index) # Replaced by render_tasks
    target_fps_for_video = TARGET_FPS 

    # --- Create a temporary directory for frame images ---
    temp_frame_dir = os.path.join(os.getcwd(), f"temp_frames_{base_filename}")
    if os.path.exists(temp_frame_dir):
        shutil.rmtree(temp_frame_dir) # Clean up from previous run if any
    os.makedirs(temp_frame_dir, exist_ok=True)
    print(f"Temporary directory for frames created at: {temp_frame_dir}")

    overall_drawing_start_time = time.time()
    frame_render_times_list = []

    print(f"\n--- Generating Render Tasks for Animation (including transitions) ---")
    # race_df here is race_df_for_animation, which might be aggregated/truncated
    all_render_tasks = generate_render_tasks(
        race_df, # This is the potentially aggregated/truncated race_df
        N_BARS,  # Use the global N_BARS from config
        TARGET_FPS, # Use the global TARGET_FPS from config
        ANIMATION_TRANSITION_DURATION_SECONDS, # Use the global transition duration
        rolling_stats_data, # Pass the rolling stats data
        nightingale_data # Pass nightingale data
    )

    if not all_render_tasks:
        print("ERROR: generate_render_tasks returned no tasks. Cannot create animation.")
        # Clean up temp directory if it was created
        if CLEANUP_INTERMEDIATE_FRAMES and os.path.exists(temp_frame_dir):
            try:
                shutil.rmtree(temp_frame_dir)
                print(f"Successfully removed temporary frame directory due to no render tasks: {temp_frame_dir}")
            except OSError as e:
                print(f"Error removing temporary frame directory {temp_frame_dir} after no render tasks: {e}")
        return

    # Apply frame limit AFTER transitions are calculated (user's intended behavior)  
    original_task_count = len(all_render_tasks)
    if MAX_FRAMES_FOR_TEST_RENDER > 0 and MAX_FRAMES_FOR_TEST_RENDER < len(all_render_tasks):
        print(f"📊 FRAME LIMITING: Taking first {MAX_FRAMES_FOR_TEST_RENDER} frames from {original_task_count} total frames (including transitions)")
        print(f"   ⚠️  NOTE: This may cut off the animation mid-transition for a test render")
        all_render_tasks = all_render_tasks[:MAX_FRAMES_FOR_TEST_RENDER]
    elif MAX_FRAMES_FOR_TEST_RENDER > 0:
        print(f"📊 FRAME LIMITING: MAX_FRAMES_FOR_TEST_RENDER ({MAX_FRAMES_FOR_TEST_RENDER}) >= total frames ({original_task_count}), rendering all frames")

    num_total_output_frames = len(all_render_tasks)
    print(f"Total output frames to render (including transitions): {num_total_output_frames}")


    print(f"\n--- Starting Parallel Frame Generation ---")
    print(f"Total output frames to render: {num_total_output_frames}")
    print(f"Using up to {MAX_PARALLEL_WORKERS} worker processes.")
    
    chart_xaxis_limit = raw_max_play_count_overall * 1.05 
    # song_id_to_canonical_album_map is already song_id_to_animator_key_map, which is correct.

    # Prepare arguments for each frame to be rendered by draw_and_save_single_frame
    tasks_args = [] 
    for task in all_render_tasks:
        # task contains: "overall_frame_index", "display_timestamp", "bar_render_data_list", "is_keyframe_end_frame"
        
        frame_num_digits = len(str(num_total_output_frames -1)) if num_total_output_frames > 0 else 1
        output_image_path = os.path.join(temp_frame_dir, f"frame_{task['overall_frame_index']:0{frame_num_digits}d}.png")

        tasks_args.append((
            task, # Pass the whole render task dictionary
            num_total_output_frames, # Total frames for logging purposes in worker
            entity_id_to_animator_key_map, # For art/color lookup (maps entity_id to canonical name)
            entity_details_map, # The main map with display info
            album_art_image_objects,          # Pre-fetched small art (bar chart)
            album_art_image_objects_highres,  # Full-res art for rolling panel
            album_bar_colors,                 # Pre-fetched colors
            N_BARS,                      # For things like y-axis range, bar height aspect
            chart_xaxis_limit,           # Overall scale for some relative calculations, not the dynamic x-lim for drawing
            output_image_path,
            dpi, fig_width_pixels, fig_height_pixels,
            LOG_FRAME_TIMES_CONFIG, PREFERRED_FONTS, LOG_PARALLEL_PROCESS_START_CONFIG,
            # Rolling stats display configs
            ROLLING_PANEL_AREA_LEFT_FIG, ROLLING_PANEL_AREA_RIGHT_FIG, ROLLING_PANEL_TITLE_Y_FROM_TOP_FIG,
            ROLLING_TITLE_TO_CONTENT_GAP_FIG, ROLLING_TITLE_FONT_SIZE, ROLLING_SONG_ARTIST_FONT_SIZE,
            ROLLING_PLAYS_FONT_SIZE, ROLLING_ART_HEIGHT_FIG, ROLLING_ART_ASPECT_RATIO, ROLLING_ART_MAX_WIDTH_FIG,
            ROLLING_ART_PADDING_RIGHT_FIG, ROLLING_TEXT_PADDING_LEFT_FIG, ROLLING_TEXT_TO_ART_HORIZONTAL_GAP_FIG,
            ROLLING_TEXT_LINE_VERTICAL_SPACING_FIG, ROLLING_SONG_ARTIST_TO_PLAYS_VERTICAL_GAP_FIG, ROLLING_INTER_PANEL_VERTICAL_SPACING_FIG,
            # New args for title X, truncation adjust, and main timestamp X, Y
            ROLLING_PANEL_TITLE_X_FIG, ROLLING_TEXT_TRUNCATION_ADJUST_PX,
            MAIN_TIMESTAMP_X_FIG, MAIN_TIMESTAMP_Y_FIG,
            # Mode information
            VISUALIZATION_MODE,
            # Debug flags
            memory_debug
        ))

    # Determine the number of workers to use with intelligent scaling for memory-intensive tasks
    actual_max_workers = MAX_PARALLEL_WORKERS
    if max_workers_override is not None:
        actual_max_workers = max_workers_override
    
    # Fix ProcessPoolExecutor initialization - never pass 0 directly
    if actual_max_workers <= 0:
        actual_max_workers = os.cpu_count() or 1
    
    # Intelligent worker count reduction for memory-intensive matplotlib tasks
    # Each worker will handle multiple high-resolution frames with complex plotting
    total_frames = len(tasks_args)
    avg_frames_per_worker = total_frames / actual_max_workers if actual_max_workers > 0 else 1
    
    # Apply memory-aware scaling: reduce workers for large workloads
    # But skip this if user explicitly forced a worker count
    is_forced_workers = (max_workers_override is not None and max_workers_override > 0) or FORCE_PARALLEL_WORKERS > 0
    
    if not is_forced_workers and total_frames > 100 and avg_frames_per_worker > 10:
        # For large renders (>100 frames), limit workers to prevent memory exhaustion
        recommended_workers = min(actual_max_workers, max(1, (os.cpu_count() or 4) // 2))
        if actual_max_workers > recommended_workers:
            print(f"🧠 MEMORY OPTIMIZATION: Reducing workers from {actual_max_workers} to {recommended_workers}")
            print(f"   Reason: Large workload ({total_frames} frames, ~{avg_frames_per_worker:.1f} frames/worker)")
            print(f"   This prevents memory exhaustion and worker process crashes")
            print(f"   💡 Override with FORCE_PARALLEL_WORKERS={actual_max_workers} in config or --workers {actual_max_workers}")
            actual_max_workers = recommended_workers
    elif is_forced_workers and total_frames > 100 and avg_frames_per_worker > 10:
        print(f"⚠️  FORCED WORKERS: Using {actual_max_workers} workers for large workload ({total_frames} frames)")
        print(f"   Each worker will handle ~{avg_frames_per_worker:.1f} frames - monitor memory usage!")
    
    completed_frames = 0
    reported_pids = set()
    
    if use_serial_mode:
        print("--- SERIAL MODE: Processing frames sequentially for debugging ---")
        for i, arg_tuple in enumerate(tasks_args):
            try:
                frame_idx, render_time, pid = draw_and_save_single_frame(arg_tuple)
                frame_render_times_list.append(render_time)
                completed_frames += 1
                
                # Log progress in serial mode too
                if completed_frames == 1 or completed_frames == num_total_output_frames or \
                   (PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG > 0 and completed_frames % PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG == 0):
                    print(f"Frame {frame_idx + 1}/{num_total_output_frames} completed in {render_time:.2f}s. ({completed_frames}/{num_total_output_frames} total done)")
            except Exception as exc:
                print(f'SERIAL MODE - Frame generation failed on frame {i}: {exc}')
                raise  # Re-raise to stop execution and see the full traceback
    else:
        print(f"--- PARALLEL MODE: Using {actual_max_workers} worker processes ---")
        
        # Keep using fork mode since our code relies heavily on globals
        import multiprocessing
        print(f"Using multiprocessing start method: '{multiprocessing.get_start_method()}'")
        
        # Use multiprocessing.Pool with maxtasksperchild for better memory management
        import multiprocessing as mp
        
        # Configure pool parameters
        pool_kwargs = {'processes': actual_max_workers}
        if MAX_TASKS_PER_CHILD > 0:
            pool_kwargs['maxtasksperchild'] = MAX_TASKS_PER_CHILD
            print(f"🔄 Worker recycling enabled: workers restart after {MAX_TASKS_PER_CHILD} tasks")
        
        print(f"🔍 DEBUG: Creating pool with {actual_max_workers} workers...")
        
        try:
            with mp.Pool(**pool_kwargs) as pool:
                print(f"✅ Pool created successfully")
                
                # Use imap_unordered for better performance (results come back as completed)
                print(f"🔍 DEBUG: Starting imap_unordered with {len(tasks_args)} tasks...")
                results = pool.imap_unordered(draw_and_save_single_frame, tasks_args, chunksize=1)
                
                print(f"🔍 DEBUG: Beginning result collection loop...")
                # Add timeout to catch hanging workers
                import signal
                
                def timeout_handler(signum, frame):
                    print(f"\n⚠️  TIMEOUT: Worker processing appears to be stuck!")
                    print(f"   Completed {completed_frames}/{num_total_output_frames} frames before hang")
                    print(f"   Consider using SERIAL_MODE = True in configurations.txt for debugging")
                    raise TimeoutError("Worker processing timeout")
                
                # Set a generous timeout (5 seconds per frame should be plenty)
                signal.signal(signal.SIGALRM, timeout_handler)
                
                for result in results:
                    # Reset timeout for each frame (5 seconds)
                    signal.alarm(5)
                try:
                    frame_idx, render_time, pid = result
                    # Cancel the timeout - frame completed successfully
                    signal.alarm(0)

                    # Log a startup message for each worker process exactly once
                    if LOG_PARALLEL_PROCESS_START_CONFIG:
                        if pid not in reported_pids:
                            print(f"--- Worker process with PID {pid} has started and is processing frames. ---")
                            reported_pids.add(pid)

                    frame_render_times_list.append(render_time)
                    completed_frames += 1
                    
                    # Updated logging condition for frame completion
                    should_log_completion = False
                    if PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG > 0:
                        if completed_frames == 1 or completed_frames == num_total_output_frames or \
                           (completed_frames % PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG == 0):
                            should_log_completion = True
                    elif PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG == 0: # Log only first and last if interval is 0
                        if completed_frames == 1 or completed_frames == num_total_output_frames:
                            should_log_completion = True

                    if should_log_completion:
                        print(f"Frame {frame_idx + 1}/{num_total_output_frames} completed by PID {pid} in {render_time:.2f}s. ({completed_frames}/{num_total_output_frames} total done)")
                except Exception as exc:
                    signal.alarm(0)  # Cancel timeout on exception too
                    print(f'PARALLEL MODE - Frame generation failed: {exc}')
                    print(f'Check error_worker_pid_*.log files for detailed traceback')
                    # Continue processing other frames
        except (TimeoutError, Exception) as e:
            print(f"\n❌ CRITICAL ERROR in parallel processing: {e}")
            print(f"   Switching to SERIAL_MODE may help diagnose the issue")
            signal.alarm(0)  # Cancel any pending timeout
    
    overall_drawing_end_time = time.time()
    total_frame_rendering_cpu_time = sum(frame_render_times_list)
    print(f"--- Parallel Frame Generation Complete ---")
    print(f"Total wall-clock time for drawing frames: {overall_drawing_end_time - overall_drawing_start_time:.2f} seconds")
    if frame_render_times_list:
        avg_frame_render_time = total_frame_rendering_cpu_time / len(frame_render_times_list)
        print(f"Total CPU time sum for drawing frames:  {total_frame_rendering_cpu_time:.2f} seconds")
        print(f"Average time per frame (across processes): {avg_frame_render_time:.3f} seconds")


    print(f"\n--- Compiling video from frames using ffmpeg ---")
    print(f"Output video: {output_filename}")
    print(f"Target FPS: {target_fps_for_video}")

    # --- Pre-flight check: Verify frame files exist ---
    frame_pattern = f"frame_%0{len(str(num_total_output_frames))}d.png"
    expected_first_frame = os.path.join(temp_frame_dir, f"frame_{0:0{len(str(num_total_output_frames))}d}.png")
    expected_last_frame = os.path.join(temp_frame_dir, f"frame_{num_total_output_frames-1:0{len(str(num_total_output_frames))}d}.png")
    
    print(f"🔍 PRE-FLIGHT CHECK: Verifying frame files...")
    print(f"   Expected pattern: {frame_pattern}")
    print(f"   First frame: {expected_first_frame}")
    print(f"   Last frame: {expected_last_frame}")
    
    if not os.path.exists(expected_first_frame):
        print(f"❌ CRITICAL ERROR: First frame missing: {expected_first_frame}")
        print(f"   Temp directory contents:")
        try:
            temp_files = sorted(os.listdir(temp_frame_dir))[:10]  # Show first 10 files
            for f in temp_files:
                print(f"     {f}")
            if len(os.listdir(temp_frame_dir)) > 10:
                print(f"     ... and {len(os.listdir(temp_frame_dir)) - 10} more files")
        except Exception as e:
            print(f"     Error listing directory: {e}")
        return  # Exit early to preserve files for debugging
    
    if not os.path.exists(expected_last_frame):
        print(f"⚠️  WARNING: Last frame missing: {expected_last_frame}")
    else:
        print(f"✅ Frame files verified - first and last frames exist")

    # --- Define path for ffmpeg progress file ---
    progress_file_path = os.path.join(temp_frame_dir, "ffmpeg_progress.txt")

    # Detect the correct ffmpeg executable for this system
    ffmpeg_executable = find_ffmpeg_executable()
    print(f"Using FFmpeg executable: {ffmpeg_executable}")

    # ffmpeg command construction
    base_ffmpeg_args = [
        ffmpeg_executable,
        '-framerate', str(target_fps_for_video),
        '-i', os.path.join(temp_frame_dir, frame_pattern), # Input pattern
    ]
    
    common_ffmpeg_output_args = [
        '-pix_fmt', 'yuv420p',
        '-y', # Overwrite output file if it exists
        '-progress', progress_file_path, # Output progress to a file
        '-nostats', # Disable default stats output to stderr
        '-loglevel', 'error' # Only log errors to stderr
    ]

    def monitor_ffmpeg_progress(process, total_frames, progress_filepath):
        print("Monitoring ffmpeg progress...")
        # Ensure progress file exists briefly before ffmpeg writes to it, to avoid initial read error
        # time.sleep(0.5) # Small delay, ffmpeg might take a moment to create it.
                        # Alternatively, handle FileNotFoundError initially in the loop.
        
        # Ensure the file is created so that the initial read doesn't fail
        try:
            with open(progress_filepath, 'w') as pf:
                pf.write('') # Create/truncate the file
        except IOError:
            pass # If it fails, ffmpeg will create it

        last_reported_frame = 0
        last_progress_output = ""

        while True:
            if process.poll() is not None: # Process has terminated
                break

            try:
                progress_data = {}
                with open(progress_filepath, 'r') as pf:
                    for line in pf:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            progress_data[key] = value
                
                current_frame_from_ffmpeg = int(progress_data.get('frame', last_reported_frame))
                speed = progress_data.get('speed', '0.0x').replace('x','')
                bitrate = progress_data.get('bitrate', 'N/A')
                # out_time_ms = int(progress_data.get('out_time_ms', '0'))
                # elapsed_seconds = out_time_ms / 1_000_000

                if current_frame_from_ffmpeg > last_reported_frame or progress_data.get('progress') == 'end':
                    last_reported_frame = current_frame_from_ffmpeg
                    percent_complete = (current_frame_from_ffmpeg / total_frames) * 100 if total_frames > 0 else 0
                    
                    progress_line = f"Encoding: Frame {current_frame_from_ffmpeg}/{total_frames} ({percent_complete:.1f}%) at {speed}x, Bitrate: {bitrate} Kbit/s"
                    
                    # Overwrite previous line
                    sys.stdout.write('\r' + ' ' * len(last_progress_output) + '\r') # Clear previous
                    sys.stdout.write(progress_line)
                    sys.stdout.flush()
                    last_progress_output = progress_line

                if progress_data.get('progress') == 'end':
                    break
            
            except FileNotFoundError:
                # Progress file might not be created immediately by ffmpeg
                # print("\rWaiting for ffmpeg progress file...", end="")
                sys.stdout.write("\rWaiting for ffmpeg progress file..." + " "*20) # Pad to clear previous
                sys.stdout.flush()
            except Exception as e:
                # print(f"\rError reading/parsing progress file: {e}"+ " "*20)
                # Avoid flooding console with rapid error messages if file is problematic
                # Instead, just indicate an issue and let ffmpeg error out if it's fatal.
                sys.stdout.write(f"\rProblem with progress file (will proceed): {e}"+ " "*20)
                sys.stdout.flush()


            time.sleep(0.25) # Check progress file periodically

        # Final newline after progress is done
        sys.stdout.write('\r' + ' ' * len(last_progress_output) + '\r') # Clear final progress line
        sys.stdout.flush()
        print(f"FFmpeg processing finished. Status: {'Completed' if process.returncode == 0 else f'Error (code {process.returncode})'}")


    # Track FFmpeg success for cleanup decisions
    ffmpeg_successful = False
    
    if USE_NVENC_IF_AVAILABLE:
        print("Attempting to use NVENC (h264_nvenc) for hardware acceleration...")
        nvenc_args = ['-preset', 'p6', '-tune', 'hq', '-b:v', '0', '-cq', '23', '-rc-lookahead', '20']
        ffmpeg_cmd_nvenc = [
            *base_ffmpeg_args,
            '-c:v', 'h264_nvenc',
            *nvenc_args,
            *common_ffmpeg_output_args,
            output_filename
        ]
        process_nvenc = None
        try:
            print(f"NVENC Command: {' '.join(ffmpeg_cmd_nvenc)}")
            process_nvenc = subprocess.Popen(ffmpeg_cmd_nvenc, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            monitor_ffmpeg_progress(process_nvenc, num_total_output_frames, progress_file_path) # Use num_total_output_frames
            stdout, stderr = process_nvenc.communicate() # Wait for process to complete after monitoring

            if process_nvenc.returncode != 0:
                raise subprocess.CalledProcessError(process_nvenc.returncode, ffmpeg_cmd_nvenc, output=stdout, stderr=stderr)
            print("Video successfully compiled using NVENC.")
            ffmpeg_successful = True
            
        except PermissionError as e_perm:
            print(f"\nERROR: Permission denied when trying to execute FFmpeg: {e_perm}")
            print(f"FFmpeg executable: {ffmpeg_executable}")
            print("Possible solutions:")
            print("1. Install FFmpeg: sudo apt install ffmpeg")
            print("2. Or install via snap: sudo snap install ffmpeg")
            print("3. Make sure FFmpeg is in your PATH")
            raise e_perm
        except subprocess.CalledProcessError as e_nvenc:
            print(f"\nWARNING: ffmpeg (NVENC) failed. Return code: {e_nvenc.returncode}")
            if e_nvenc.stdout: print(f"NVENC STDOUT: {e_nvenc.stdout.decode(errors='replace')}")
            if e_nvenc.stderr: print(f"NVENC STDERR: {e_nvenc.stderr.decode(errors='replace')}")
            print("Falling back to CPU encoder (libx264).")
            
            # Fallback to libx264
            cpu_args = ['-crf', '23', '-preset', 'medium']
            ffmpeg_cmd_cpu_fallback = [
                *base_ffmpeg_args,
                '-c:v', 'libx264',
                *cpu_args,
                *common_ffmpeg_output_args,
                output_filename
            ]
            process_cpu_fallback = None
            try:
                print(f"CPU Fallback Command: {' '.join(ffmpeg_cmd_cpu_fallback)}")
                process_cpu_fallback = subprocess.Popen(ffmpeg_cmd_cpu_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                monitor_ffmpeg_progress(process_cpu_fallback, num_total_output_frames, progress_file_path) # Use num_total_output_frames
                stdout_cpu, stderr_cpu = process_cpu_fallback.communicate()

                if process_cpu_fallback.returncode != 0:
                    raise subprocess.CalledProcessError(process_cpu_fallback.returncode, ffmpeg_cmd_cpu_fallback, output=stdout_cpu, stderr=stderr_cpu)
                print("Video successfully compiled using libx264 (CPU).")
                ffmpeg_successful = True
            except subprocess.CalledProcessError as e_cpu_fallback:
                print(f"\nERROR: ffmpeg (libx264 fallback) also failed. Return code: {e_cpu_fallback.returncode}")
                if e_cpu_fallback.stdout: print(f"CPU STDOUT: {e_cpu_fallback.stdout.decode(errors='replace')}")
                if e_cpu_fallback.stderr: print(f"CPU STDERR: {e_cpu_fallback.stderr.decode(errors='replace')}")
                print("Video compilation failed.")
            except FileNotFoundError:
                 print("\nERROR: ffmpeg command not found. Please ensure ffmpeg is installed and in your system's PATH.")
        except FileNotFoundError:
             print("\nERROR: ffmpeg command not found. Please ensure ffmpeg is installed and in your system's PATH.")
    else: # Not using NVENC, proceed with libx264
        print("Using CPU encoder (libx264).")
        cpu_args = ['-crf', '23', '-preset', 'medium']
        ffmpeg_cmd_cpu_direct = [
            *base_ffmpeg_args,
            '-c:v', 'libx264',
            *cpu_args,
            *common_ffmpeg_output_args,
            output_filename
        ]
        process_cpu_direct = None
        try:
            print(f"CPU Command: {' '.join(ffmpeg_cmd_cpu_direct)}")
            process_cpu_direct = subprocess.Popen(ffmpeg_cmd_cpu_direct, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            monitor_ffmpeg_progress(process_cpu_direct, num_total_output_frames, progress_file_path) # Use num_total_output_frames
            stdout, stderr = process_cpu_direct.communicate()

            if process_cpu_direct.returncode != 0:
                raise subprocess.CalledProcessError(process_cpu_direct.returncode, ffmpeg_cmd_cpu_direct, output=stdout, stderr=stderr)
            print("Video successfully compiled using libx264 (CPU).")
            ffmpeg_successful = True
        except subprocess.CalledProcessError as e_cpu:
            print(f"\nERROR: ffmpeg (libx264) failed. Return code: {e_cpu.returncode}")
            if e_cpu.stdout: print(f"CPU STDOUT: {e_cpu.stdout.decode(errors='replace')}")
            if e_cpu.stderr: print(f"CPU STDERR: {e_cpu.stderr.decode(errors='replace')}")
            print("Video compilation failed.")
        except FileNotFoundError:
            print("\nERROR: ffmpeg command not found. Please ensure ffmpeg is installed and in your system's PATH.")
    
    # --- Cleanup intermediate frames and progress file ---
    if CLEANUP_INTERMEDIATE_FRAMES and ffmpeg_successful:
        try:
            shutil.rmtree(temp_frame_dir)
            print(f"Successfully removed temporary frame directory: {temp_frame_dir}")
        except OSError as e:
            print(f"Error removing temporary frame directory {temp_frame_dir}: {e}")
    elif not ffmpeg_successful:
        print(f"🔍 DEBUGGING: FFmpeg failed - preserving frames for inspection at: {temp_frame_dir}")
        print(f"   You can manually inspect the files and delete the directory when done.")
    else:
        print(f"Intermediate frames retained at: {temp_frame_dir}")
        
    # Clean up progress file regardless (it's not useful for debugging)
    if os.path.exists(progress_file_path):
        try:
            os.remove(progress_file_path)
            if ffmpeg_successful:
                print(f"Successfully removed progress file: {progress_file_path}")
        except OSError as e:
            print(f"Error removing progress file {progress_file_path}: {e}")


    # --- Frame Timing Summary (simplified for parallel generation) ---
    overall_animation_end_time = time.time() # This would need to be redefined if main() changes
    if LOG_FRAME_TIMES_CONFIG and frame_render_times_list:
        # total_frame_rendering_cpu_time and avg_frame_render_time already calculated
        min_render_time = min(frame_render_times_list) if frame_render_times_list else 0
        max_render_time = max(frame_render_times_list) if frame_render_times_list else 0
        sorted_times = sorted(frame_render_times_list)
        median_render_time = sorted_times[len(sorted_times) // 2] if sorted_times else 0
        
        # Note: total_wall_clock_time would be better measured in main() around this function call
        # video_saving_time is now part of the ffmpeg subprocess call, harder to isolate precisely without more timing

        print("\n--- Animation Rendering Summary (Parallel) ---")
        # print(f"Total wall-clock time (incl. save): {total_wall_clock_time:.2f} seconds") # Needs to be from main
        print(f"  Total wall-clock time for drawing frames: {overall_drawing_end_time - overall_drawing_start_time:.2f} seconds")
        print(f"  Total CPU time sum for drawing frames:  {total_frame_rendering_cpu_time:.2f} seconds")
        print(f"  Number of frames rendered:          {len(frame_render_times_list)}")
        print(f"  Frame render times (seconds, per process):")
        print(f"    Min:    {min_render_time:.3f}")
        print(f"    Max:    {max_render_time:.3f}")
        print(f"    Median: {median_render_time:.3f}")
        print(f"    Avg:    {avg_frame_render_time:.3f}")

    # No plt.close(fig) here as figures are created/closed in worker processes.
    # The original ani.save() and writer logic is now replaced by direct ffmpeg call.

def main():
    global args
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate animated bar chart race from Spotify/Last.fm data')
    parser.add_argument('--serial', action='store_true', 
                        help='Use serial processing instead of parallel (for debugging)')
    parser.add_argument('--workers', type=int, 
                        help='Override MAX_PARALLEL_WORKERS setting (0 = use all cores)')
    parser.add_argument('--memory-debug', action='store_true',
                        help='Enable detailed memory monitoring in worker processes')
    args = parser.parse_args()
    
    load_configuration() # Load config first, sets up MAX_FRAMES_FOR_TEST_RENDER
    setup_fonts() # Setup fonts after config is loaded but before any matplotlib operations
    
    # Print diagnostic information
    if args.serial:
        print(f"🐛 DEBUG MODE: Serial processing enabled (--serial flag)")
    if args.workers is not None:
        print(f"⚙️  Worker override: {args.workers} workers (--workers flag)")
    if args.memory_debug:
        print(f"🔍 Memory debugging enabled (--memory-debug flag)")
    
    print(f"🐍 Python: {sys.version}")
    print(f"📊 Matplotlib: {matplotlib.__version__}")
    import multiprocessing
    print(f"🔧 Multiprocessing start method: {multiprocessing.get_start_method()}")
    print(f"💻 CPU cores available: {os.cpu_count()}")
    print(f"⚙️  MAX_PARALLEL_WORKERS (from config): {MAX_PARALLEL_WORKERS}")
    
    # Check for psutil for memory monitoring
    try:
        import psutil
        total_mem_gb = psutil.virtual_memory().total / 1024**3
        print(f"💾 Total system memory: {total_mem_gb:.1f} GB")
    except ImportError:
        if args.memory_debug:
            print("⚠️  psutil not available - memory monitoring disabled")

    # Check for PYTHONIOENCODING_WARNING from config
    if config.get_bool('General', 'PYTHONIOENCODING_WARNING', True):
        # Check if PYTHONIOENCODING is set to UTF-8
        python_io_encoding = os.environ.get('PYTHONIOENCODING', None)
        if python_io_encoding is None or python_io_encoding.lower() != 'utf-8':
            print("Hint: For best compatibility with non-ASCII characters in song titles/artists,")
            print("      consider setting the environment variable PYTHONIOENCODING=UTF-8")
            print("      You can disable this message by setting PYTHONIOENCODING_WARNING = False in configurations.txt")

    if not animation.FFMpegWriter.isAvailable():
        print("WARNING: FFMpegWriter is not available. Animation saving will likely fail.")
        print("Please ensure ffmpeg is installed and accessible in your system's PATH.")
    else:
        print("FFMpegWriter is available.")

    # Check if we're in "both" mode
    original_mode = config.get('VisualizationMode', 'MODE', 'tracks').lower()
    
    if original_mode == 'both':
        print("\n=== BOTH MODE ENABLED ===")
        print("Will generate both track and artist visualizations sequentially...")
        modes_to_run = ['tracks', 'artists']
    else:
        modes_to_run = [original_mode]
    
    # Run the pipeline for each mode
    for mode_index, current_mode in enumerate(modes_to_run):
        if len(modes_to_run) > 1:
            print(f"\n{'='*50}")
            print(f"RUNNING MODE {mode_index + 1} of {len(modes_to_run)}: {current_mode.upper()}")
            print(f"{'='*50}")
        
        # Set the global VISUALIZATION_MODE for this iteration
        global VISUALIZATION_MODE
        VISUALIZATION_MODE = current_mode
        
        pipeline_start_time = time.time() # <--- ADDED TIMING
        
        # --- Step 1: Clean and filter data ---
        print(f"\nStep 1: Cleaning and filtering data based on configuration (Source: {config.get('DataSource', 'SOURCE')})...")
        cleaned_df = clean_and_filter_data(config)
        
        if cleaned_df is None or cleaned_df.empty: 
            print("Data cleaning and filtering resulted in no data. Exiting.")
            return
        print(f"Data cleaning successful. {len(cleaned_df)} relevant rows found.")

        # --- Step 2: Prepare data for bar chart race (high-resolution timestamps) ---
        print(f"\nStep 2: Preparing data for bar chart race (high-resolution timestamps) in {VISUALIZATION_MODE} mode...")
        full_race_df, entity_details_map = prepare_data_for_bar_chart_race(cleaned_df, mode=VISUALIZATION_MODE) # Use cleaned_df from above
        
        if full_race_df is None or full_race_df.empty:
            print("\nNo data available for animation after race preparation. Please check your data and processing steps.")
            continue # Skip to next mode if data is empty
            
        print("Data preparation for race successful.")
        entity_type = "songs" if VISUALIZATION_MODE == "tracks" else "artists"
        print(f"Race DataFrame shape: {full_race_df.shape} (Play Events, Unique {entity_type.title()})")
        print(f"Number of entries in entity_details_map: {len(entity_details_map)}")

        pipeline_end_time = time.time() # <--- ADDED TIMING
        print(f"--- Time taken for data processing (Steps 1 & 2): {pipeline_end_time - pipeline_start_time:.2f} seconds ---") # <--- ADDED TIMING


        print("\n--- Data ready for Animation ---")
        
        race_df_for_animation = full_race_df.copy() # Start with the full df, copy to avoid modifying original full_race_df

        # --- Apply FRAME_AGGREGATION_PERIOD ---    
        aggregation_period_config = config.get('AnimationOutput', 'FRAME_AGGREGATION_PERIOD', 'event').strip() # Keep case for freq strings like '30T'
        is_event_based = aggregation_period_config.upper() == 'EVENT' # Check against upper for 'event'

        if not is_event_based and not race_df_for_animation.empty:
            print(f"\n--- Applying Frame Aggregation ({aggregation_period_config}) ---")
            # Ensure index is datetime for resampling
            if not pd.api.types.is_datetime64_any_dtype(race_df_for_animation.index):
                try:
                    race_df_for_animation.index = pd.to_datetime(race_df_for_animation.index, utc=True)
                    print("Converted race_df index to datetime for resampling.")
                except Exception as e_dt_convert:
                    print(f"ERROR converting race_df index to datetime: {e_dt_convert}. Cannot apply time-based aggregation. Proceeding with event-based frames.")
                    is_event_based = True # Fallback to event-based

            if not is_event_based: # Re-check after potential fallback
                try:
                    # Group by the desired aggregation period, using the original event timestamps.
                    # For each period that has events, pick the *last event's data* from that period.
                    # The index of the resulting df will be the timestamp of that last event.
                    # This ensures that only periods with activity are included, and the timestamp is accurate.
                    aggregated_df = race_df_for_animation.groupby(pd.Grouper(freq=aggregation_period_config)).last()

                    # Drop rows that might have become all NaN if a period had no events
                    # (Grouper with .last() should only produce rows for periods that had data,
                    # but an explicit dropna ensures cleanliness).
                    aggregated_df.dropna(how='all', inplace=True)
                    
                    # Ensure remaining NaNs (e.g. for songs that weren't present in a last event) are 0 and type is int
                    race_df_for_animation = aggregated_df.fillna(0).astype(int)
                    
                    print(f"Aggregated race_df by '{aggregation_period_config}', keeping last event in each period. New shape: {race_df_for_animation.shape}")
                    if race_df_for_animation.empty:
                        print("Warning: Aggregation resulted in an empty DataFrame. Check aggregation period and data density.")
                        continue # Skip to next mode if aggregation fails
                except ValueError as e_resample:
                    print(f"ERROR during aggregation with period '{aggregation_period_config}': {e_resample}.")
                    print("Ensure the aggregation period is a valid pandas offset alias (e.g., 'D', 'H', 'S', 'W', 'M', '30T'). Proceeding with event-based frames.")
                    race_df_for_animation = full_race_df # Fallback to original df if aggregation failed
                except Exception as e_generic_resample:
                    print(f"An unexpected error occurred during aggregation: {e_generic_resample}. Proceeding with event-based frames.")
                    race_df_for_animation = full_race_df # Fallback
        else:
            print("\n--- Using event-based frames (no aggregation selected or DataFrame was empty) ---")
        
        # Note: MAX_FRAMES_FOR_TEST_RENDER is applied AFTER transition frames are generated
        # in create_bar_chart_race_animation(), not here on the base data
        
        # --- Step 3: Calculate Rolling Window Stats ---
        if race_df_for_animation.empty:
            print("\nrace_df_for_animation is empty before calculating rolling stats. Skipping this mode.")
            continue
            
        animation_frame_timestamps = race_df_for_animation.index
        # Rolling base frequency allows users to control granularity (e.g. 'D', 'H', '15T').
        rolling_base_freq_cfg = config.get('RollingStats', 'BASE_FREQUENCY', 'D').strip() or 'D'
        rolling_stats = calculate_rolling_window_stats(
            cleaned_df,
            animation_frame_timestamps,
            base_freq=rolling_base_freq_cfg,
            mode=VISUALIZATION_MODE
        )
        
        # --- Step 4: Calculate Nightingale Chart Data (if enabled) ---
        nightingale_data = {}
        if ENABLE_NIGHTINGALE:
            print("\nStep 4: Calculating nightingale rose chart data...")
            
            # Determine aggregation type
            agg_type = NIGHTINGALE_AGGREGATION_TYPE
            if agg_type == 'auto':
                start_date = cleaned_df['timestamp'].min()
                end_date = cleaned_df['timestamp'].max()
                agg_type = determine_aggregation_type(start_date, end_date)
                print(f"Auto-determined aggregation type: {agg_type}")
            
            # Apply sampling rate for performance optimization
            if NIGHTINGALE_SAMPLING_RATE.upper() in ['W', 'M']:
                print(f"Applying nightingale sampling rate: {NIGHTINGALE_SAMPLING_RATE}")
                # Sample frame timestamps for faster computation
                sampled_timestamps = animation_frame_timestamps[::7] if NIGHTINGALE_SAMPLING_RATE.upper() == 'W' else animation_frame_timestamps[::30]
                # Always include first and last timestamps
                if sampled_timestamps[0] != animation_frame_timestamps[0]:
                    sampled_timestamps = pd.Index([animation_frame_timestamps[0]]).union(sampled_timestamps)
                if sampled_timestamps[-1] != animation_frame_timestamps[-1]:
                    sampled_timestamps = sampled_timestamps.union(pd.Index([animation_frame_timestamps[-1]]))
                print(f"Reduced nightingale frames: {len(animation_frame_timestamps)} → {len(sampled_timestamps)}")
            else:
                sampled_timestamps = animation_frame_timestamps
            
            # Calculate raw nightingale time data (using sampled timestamps for performance)
            nightingale_time_data = calculate_nightingale_time_data(
                cleaned_df,
                sampled_timestamps.tolist(),
                aggregation_type=agg_type
            )
            
            # Prepare animation data with smooth transitions (interpolate for all frames)
            nightingale_data = prepare_nightingale_animation_data(
                nightingale_time_data,
                animation_frame_timestamps.tolist(),  # Always use all frames for smooth animation
                enable_smooth_transitions=NIGHTINGALE_ENABLE_SMOOTH_TRANSITIONS,
                transition_duration_seconds=NIGHTINGALE_TRANSITION_DURATION_SECONDS,
                target_fps=TARGET_FPS,
                easing_function=NIGHTINGALE_ANIMATION_EASING_FUNCTION
            )
            
            print(f"Nightingale data calculated for {len(nightingale_data)} frames")
        else:
            print("\nNightingale chart disabled in configuration, skipping calculation")

        # Now, call create_bar_chart_race_animation with the potentially truncated and/or aggregated race_df_for_animation
        # The pre_fetch logic is inside create_bar_chart_race_animation, so it will use the df passed to it.
        # Merge CLI args with config settings (CLI takes precedence)
        use_serial_mode = args.serial or SERIAL_MODE_CONFIG
        max_workers_override = args.workers if args.workers is not None else (FORCE_PARALLEL_WORKERS if FORCE_PARALLEL_WORKERS > 0 else None)
        memory_debug = args.memory_debug or MEMORY_DEBUG_CONFIG
        
        create_bar_chart_race_animation(race_df_for_animation, entity_details_map, rolling_stats, nightingale_data, 
                                        use_serial_mode=use_serial_mode, max_workers_override=max_workers_override, 
                                        memory_debug=memory_debug) # Pass nightingale_data and CLI args
        
        if len(modes_to_run) > 1:
            print(f"\n✓ Completed {current_mode.upper()} mode visualization")
    
    if len(modes_to_run) > 1:
        print(f"\n{'='*50}")
        print("✓ BOTH MODE COMPLETE - All visualizations generated successfully!")
        print(f"{'='*50}")


if __name__ == "__main__":
    # The global `config` will be loaded in main().
    # album_art_utils is imported, and its initialize_from_config will be called from main_animator.load_configuration()
    main()