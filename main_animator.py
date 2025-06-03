# main_animator.py

import pandas as pd
from data_processor import clean_and_filter_data, prepare_data_for_bar_chart_race

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
import concurrent.futures # Added for parallel processing
import subprocess # Added for calling ffmpeg
import shutil # Added for directory operations

# Import the config loader
from config_loader import AppConfig

# --- Configuration (will be loaded from file) ---
config = None # Global config object

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

# --- Global Dictionaries for Caching Art Paths and Colors within the animator ---
album_art_image_objects = {}
album_bar_colors = {}

def load_configuration():
    global config, N_BARS, TARGET_FPS, OUTPUT_FILENAME_BASE, DEBUG_ALBUM_ART_LOGIC
    global ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR, USE_NVENC_IF_AVAILABLE, PREFERRED_FONTS
    global MAX_FRAMES_FOR_TEST_RENDER, LOG_FRAME_TIMES_CONFIG
    global MAX_PARALLEL_WORKERS, CLEANUP_INTERMEDIATE_FRAMES, PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG
    global LOG_PARALLEL_PROCESS_START_CONFIG

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
    PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG = config.get_int('Debugging', 'PARALLEL_LOG_COMPLETION_INTERVAL', 50)
    LOG_PARALLEL_PROCESS_START_CONFIG = config.get_bool('Debugging', 'LOG_PARALLEL_PROCESS_START', True)

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
    
    print("\nStep 2: Preparing data for bar chart race (high-resolution timestamps)...")
    race_df, song_details_map = prepare_data_for_bar_chart_race(cleaned_df)
    if race_df is None or race_df.empty: 
        print("Data preparation for race resulted in no data. Exiting.")
        return None, song_details_map
        
    print("Data preparation successful.")
    print(f"Race DataFrame shape: {race_df.shape} (Play Events, Unique Songs)")
    print(f"Number of entries in song_details_map: {len(song_details_map)}")
    print("--- Data Processing Pipeline Complete ---")
    return race_df, song_details_map


def pre_fetch_album_art_and_colors(race_df, song_details_map, unique_song_ids_in_race, global_visibility_threshold, target_img_height_pixels_for_resize, fig_dpi):
    # This function now uses album_art_utils directly, which is config-aware
    print(f"\n--- Pre-fetching album art and dominant colors (Target Img Resize Height: {target_img_height_pixels_for_resize}px, Visibility Threshold: >={global_visibility_threshold:.2f} plays) ---")
    
    # This set will now track CANONICAL album names for which PIL/color is loaded in main_animator
    # to avoid redundant PIL loading and dominant color calculation for the same canonical album.
    canonical_albums_loaded_in_animator_cache = set()
    song_id_to_animator_key_map = {} # New map to return
    
    processed_count = 0
    skipped_due_to_threshold = 0

    for song_id in unique_song_ids_in_race:
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

        # --- Visibility Threshold Check (from your original code) ---
        # Ensure race_df is available here and contains the song_id as a column
        if song_id not in race_df.columns:
            if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH DEBUG] Song ID '{song_id}' not found in race_df columns. Skipping.")
            continue # Should not happen if unique_song_ids_in_race comes from race_df.columns

        max_plays_for_this_song = race_df[song_id].max()

        # if "Kristen Bell - For the First Time in Forever" in song_id: # Temporary specific check
        #     print(f"[THRESHOLD_CHECK_DEBUG] For '{song_id}', max_plays_for_this_song = {max_plays_for_this_song}. global_visibility_threshold = {global_visibility_threshold:.2f}")
            
        if max_plays_for_this_song < global_visibility_threshold:
            if DEBUG_ALBUM_ART_LOGIC:
                print(f"[PRE-FETCH DEBUG] Song '{song_id}' (max plays: {max_plays_for_this_song}) is below visibility threshold ({global_visibility_threshold:.2f}). Skipping art/color processing.")
            skipped_due_to_threshold += 1
            song_id_to_animator_key_map[song_id] = album_name_hint_from_data # Store a fallback key
            continue
        
        if DEBUG_ALBUM_ART_LOGIC:
            print(f"[PRE-FETCH DEBUG] Song '{song_id}' (max plays: {max_plays_for_this_song}) meets threshold. Processing album hint: '{album_name_hint_from_data}'.")

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
                    img = Image.open(art_path)
                    # --- Resize image here ---
                    img_orig_width, img_orig_height = img.size
                    new_height_pixels = int(target_img_height_pixels_for_resize)
                    new_width_pixels = 1
                    if img_orig_height > 0 and new_height_pixels > 0:
                        new_width_pixels = int(new_height_pixels * (img_orig_width / img_orig_height))
                    if new_width_pixels <= 0: new_width_pixels = int(new_height_pixels * 0.75) # Fallback if aspect ratio is extreme
                    if new_width_pixels <= 0: new_width_pixels = 1 # Final fallback

                    resized_img = img.resize((new_width_pixels, new_height_pixels), Image.Resampling.LANCZOS)
                    album_art_image_objects[canonical_album_name_for_animator_cache] = resized_img
                    # No need to copy, resize returns a new image. Close original.
                    img.close() 
                    
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
                except Exception as e:
                    print(f"Error [PRE-FETCH] loading image {art_path} or getting color for canonical album '{canonical_album_name_for_animator_cache}': {e}. Using defaults.")
                    album_art_image_objects[canonical_album_name_for_animator_cache] = None
                    album_bar_colors[canonical_album_name_for_animator_cache] = (0.5, 0.5, 0.5)
                    canonical_albums_loaded_in_animator_cache.add(canonical_album_name_for_animator_cache) # Mark as processed
            # else: This canonical album's art/color is already in the animator's memory from a previous song.
            
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
    print(f"Skipped {skipped_due_to_threshold} song-album groups due to not meeting visibility threshold.")
    print(f"In-memory PIL images (animator cache): {len(album_art_image_objects)}, In-memory bar colors (animator cache): {len(album_bar_colors)}")
    return song_id_to_animator_key_map # Return the new map


def draw_and_save_single_frame(args):
    # Unpack arguments
    (frame_index, num_frames, current_timestamp, current_data_slice,
    song_id_to_canonical_album_map, album_art_image_objects_local, album_bar_colors_local,
    n_bars_local, chart_xaxis_limit, art_display_min_plays_threshold,
    output_image_path, dpi, fig_width_pixels, fig_height_pixels,
    log_frame_times_config_local, preferred_fonts_local,
    log_parallel_process_start_local) = args

    # Each process needs to set its font family if it's not inherited
    try:
        plt.rcParams['font.family'] = preferred_fonts_local
    except Exception as e_font:
        print(f"[Worker PID: {os.getpid()}] Warning: Could not set preferred fonts: {e_font}")


    frame_start_time = time.time()
    
    # Create a new figure and axes for each frame to ensure thread safety / process isolation
    figsize_w = fig_width_pixels / dpi
    figsize_h = fig_height_pixels / dpi
    fig, ax = plt.subplots(figsize=(figsize_w, figsize_h), dpi=dpi)

    try: # Ensure fig is closed even on error
        if log_parallel_process_start_local: # Condition for logging process start
            if (frame_index + 1) % 10 == 0 or frame_index == 0 or (frame_index + 1) == num_frames:
                print(f"Process {os.getpid()} starting frame {frame_index + 1}/{num_frames} ({current_timestamp.strftime('%Y-%m-%d %H:%M:%S')})...")
        # Ensure no other print statements for "Process starting frame..." exist here

        top_n_songs = current_data_slice[current_data_slice > 0].nlargest(n_bars_local)
        songs_to_draw = top_n_songs.sort_values(ascending=True)

        date_str = current_timestamp.strftime('%d %B %Y %H:%M:%S')
        ax.text(0.98, 0.05, date_str, transform=ax.transAxes,
                ha='right', va='bottom', fontsize=20 * (dpi/100.0), color='dimgray', weight='bold')

        ax.set_xlabel("Total Plays", fontsize=18 * (dpi/100.0), labelpad=15 * (dpi/100.0))
        ax.set_xlim(0, chart_xaxis_limit)
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        ax.xaxis.set_ticks_position('top')
        ax.xaxis.set_label_position('top')
        tick_label_fontsize = 11 * (dpi/100.0)
        ax.tick_params(axis='x', labelsize=tick_label_fontsize)

        ax.set_ylim(-0.5, n_bars_local - 0.5)
        ax.set_yticks(np.arange(n_bars_local))
        
        y_tick_labels = [""] * n_bars_local
        
        bar_y_positions = []
        bar_widths = []
        bar_colors_list = []
        bar_song_ids = []

        for i, song_id in enumerate(songs_to_draw.index):
            rank_on_chart = len(songs_to_draw) - 1 - i 
            y_pos_for_bar = n_bars_local - 1 - rank_on_chart
            
            bar_y_positions.append(y_pos_for_bar)
            bar_widths.append(songs_to_draw[song_id])
            bar_song_ids.append(song_id)

            # song_id_to_canonical_album_map is now song_id_to_animator_key_map
            # It maps song_id to the key used for album_art_image_objects_local and album_bar_colors_local
            animator_cache_key_for_song = song_id_to_canonical_album_map.get(song_id, "Unknown Album")
            bar_colors_list.append(album_bar_colors_local.get(animator_cache_key_for_song, (0.5,0.5,0.5)))
            
            max_char_len = int(50 * (150.0/dpi)) 
            display_song_id = song_id
            if len(song_id) > max_char_len:
                display_song_id = song_id[:max_char_len-3] + "..."
            y_tick_labels[y_pos_for_bar] = display_song_id
            
        ax.set_yticklabels(y_tick_labels, fontsize=tick_label_fontsize)

        if bar_y_positions:
            actual_bars = ax.barh(bar_y_positions, bar_widths, color=bar_colors_list, height=0.8, zorder=2)

            value_label_fontsize = 12 * (dpi/100.0)
            image_padding_data_units = chart_xaxis_limit * 0.005
            value_label_padding_data_units = chart_xaxis_limit * 0.008

            for i, bar_obj in enumerate(actual_bars):
                song_id_for_bar = bar_song_ids[i]
                current_play_count = bar_widths[i]
                
                # song_id_to_canonical_album_map is now song_id_to_animator_key_map
                animator_cache_key_for_bar = song_id_to_canonical_album_map.get(song_id_for_bar, "Unknown Album")
                pil_image = album_art_image_objects_local.get(animator_cache_key_for_bar)

                current_x_anchor = bar_obj.get_width()

                if pil_image and current_play_count >= art_display_min_plays_threshold:
                    try:
                        resized_img_width_pixels, resized_img_height_pixels = pil_image.size 
                        
                        # Recalculate fig_width_pixels for this specific figure instance if needed, or use passed
                        # fig_width_pixels_current = fig.get_size_inches()[0] * dpi # This is the actual pixel width of this fig
                        x_axis_range_data_units = ax.get_xlim()[1] - ax.get_xlim()[0]
                        image_width_data_units = 0
                        if fig_width_pixels > 0 and x_axis_range_data_units > 0: # Use passed fig_width_pixels
                             image_width_data_units = (resized_img_width_pixels / fig_width_pixels) * x_axis_range_data_units
                        
                        img_center_x_pos = current_x_anchor - image_padding_data_units - (image_width_data_units / 2.0) 
                        
                        if img_center_x_pos - (image_width_data_units / 2.0) > chart_xaxis_limit * 0.02:
                            imagebox = OffsetImage(pil_image, zoom=1.0, resample=False)
                            ab = AnnotationBbox(imagebox,
                                                (img_center_x_pos, bar_obj.get_y() + bar_obj.get_height() / 2.0),
                                                xybox=(0,0), xycoords='data', boxcoords="offset points",
                                                pad=0, frameon=False, zorder=3)
                            ax.add_artist(ab)
                            current_x_anchor = img_center_x_pos - (image_width_data_units / 2.0)
                    except Exception as e:
                        print(f"Error (PID {os.getpid()}) processing/adding image for {animator_cache_key_for_bar} (Song: {song_id_for_bar}): {e}")
                
                text_x_pos = bar_obj.get_width() + value_label_padding_data_units
                ax.text(text_x_pos,
                        bar_obj.get_y() + bar_obj.get_height() / 2.0,
                        f'{int(current_play_count)}',
                        va='center', ha='left', fontsize=value_label_fontsize, weight='bold', zorder=4)

        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_linewidth(1.5 * (dpi/100.0))
        
        left_margin = 0.08 
        right_margin = 0.90 
        bottom_margin = 0.10
        top_margin = 0.92
        
        try:
            fig.tight_layout(rect=[left_margin, bottom_margin, right_margin, top_margin])
            fig.align_labels() 
        except Exception as e_layout:
            # if DEBUG_ALBUM_ART_LOGIC: print(f"Note: Layout adjustment warning/error: {e_layout}. Plot might not be perfectly aligned.")
            # This debug var might not be available or set correctly in parallel context, simple print
            print(f"Note (PID {os.getpid()}): Layout adjustment warning/error: {e_layout}.")
            plt.subplots_adjust(left=left_margin, bottom=bottom_margin, right=right_margin, top=top_margin)
        
        fig.savefig(output_image_path)

    except Exception as e:
        print(f"Error in draw_and_save_single_frame (PID: {os.getpid()}, Frame: {frame_index}): {e}")
        # Potentially re-raise or handle by creating an empty/error frame
    finally:
        plt.close(fig) # Crucial: close the figure to free memory

    current_frame_render_time = time.time() - frame_start_time
    return frame_index, current_frame_render_time, os.getpid()


def create_bar_chart_race_animation(race_df, song_details_map): # race_df here is already potentially truncated
    if race_df is None or race_df.empty:
        print("Cannot create animation: race_df is empty or None.")
        return

    unique_song_ids_in_race = race_df.columns.tolist()
    raw_max_play_count_overall = race_df.max().max()
    if pd.isna(raw_max_play_count_overall) or raw_max_play_count_overall <= 0:
        raw_max_play_count_overall = 100 # Fallback
    
    selected_res_key = config.get('AnimationOutput', 'RESOLUTION', '4k').strip()
    res_settings = VIDEO_RESOLUTION_PRESETS.get(selected_res_key, VIDEO_RESOLUTION_PRESETS['4k'])
    dpi = res_settings['dpi']
    fig_width_pixels = res_settings['width']
    fig_height_pixels = res_settings['height']

    example_bar_height_data_units = 0.8 
    image_height_scale_factor = 0.35 
    current_n_bars_for_sizing = N_BARS if N_BARS > 0 else 10
        
    calculated_target_img_height_pixels = \
        (example_bar_height_data_units / current_n_bars_for_sizing) * \
        fig_height_pixels * image_height_scale_factor
    
    art_processing_min_plays_threshold = raw_max_play_count_overall * ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR
    print(f"[ANIMATOR_INFO] global_visibility_threshold (art_processing_min_plays_threshold) = {art_processing_min_plays_threshold:.2f}")
    print(f"[ANIMATOR_INFO] Calculated target image height for pre-resize: {calculated_target_img_height_pixels:.2f} pixels")

    art_fetch_start_time = time.time()
    # pre_fetch_album_art_and_colors now returns song_id_to_animator_key_map
    song_id_to_animator_key_map = pre_fetch_album_art_and_colors(race_df, song_details_map, unique_song_ids_in_race, art_processing_min_plays_threshold, calculated_target_img_height_pixels, dpi)
    art_fetch_end_time = time.time()
    print(f"--- Time taken for pre_fetch_album_art_and_colors: {art_fetch_end_time - art_fetch_start_time:.2f} seconds ---")

    output_filename = f"{OUTPUT_FILENAME_BASE}_{selected_res_key}.mp4"
    num_frames = len(race_df.index)
    target_fps_for_video = TARGET_FPS 

    # --- Create a temporary directory for frame images ---
    temp_frame_dir = os.path.join(os.getcwd(), f"temp_frames_{OUTPUT_FILENAME_BASE}")
    if os.path.exists(temp_frame_dir):
        shutil.rmtree(temp_frame_dir) # Clean up from previous run if any
    os.makedirs(temp_frame_dir, exist_ok=True)
    print(f"Temporary directory for frames created at: {temp_frame_dir}")

    overall_drawing_start_time = time.time()
    frame_render_times_list = []

    print(f"\n--- Starting Parallel Frame Generation ---")
    print(f"Total frames to render: {num_frames}")
    print(f"Using up to {MAX_PARALLEL_WORKERS} worker processes.")
    
    chart_xaxis_limit = raw_max_play_count_overall * 1.05
    art_display_min_plays_threshold = art_processing_min_plays_threshold 

    # song_id_to_canonical_album_map is now song_id_to_animator_key_map, built by pre_fetch
    # This map is directly passed to draw_and_save_single_frame
    # No need to rebuild it here as per the old logic:
    # song_id_to_canonical_album_map = {} # Prepare this once
    # for song_id in unique_song_ids_in_race:
    #     try:
    #         artist_name, track_name = song_id.split(" - ", 1)
    #         album_name_hint = song_album_map_lastfm.get(song_id, "") # This would be song_details_map now
    #         spotify_cache_key = f"spotify_{artist_name.lower().strip()}_{track_name.lower().strip()}_{album_name_hint.lower().strip()}" # This key might not align anymore
    #         spotify_data = album_art_utils.spotify_info_cache.get(spotify_cache_key)
    #         if spotify_data and spotify_data.get("canonical_album_name"):
    #             song_id_to_canonical_album_map[song_id] = spotify_data["canonical_album_name"]
    #         else:
    #             # Fallback to the animator key determined during pre_fetch if direct lookup here fails
    #             # This part is now handled by using the map returned from pre_fetch directly.
    #             song_id_to_canonical_album_map[song_id] = song_id_to_animator_key_map.get(song_id, album_name_hint) # Default to hint
    #     except ValueError:
    #         song_id_to_canonical_album_map[song_id] = song_id_to_animator_key_map.get(song_id, song_details_map.get(song_id, {}).get('name', "Unknown Album"))


    # Prepare arguments for each frame
    tasks_args = []
    for i in range(num_frames):
        current_timestamp = race_df.index[i]
        current_data_slice = race_df.iloc[i]
        # Frame filenames need to be sortable, e.g., frame_00001.png
        output_image_path = os.path.join(temp_frame_dir, f"frame_{i:0{len(str(num_frames))}d}.png")
        
        # Pass copies or immutable data to child processes where appropriate.
        # The large dictionaries (album_art_image_objects, album_bar_colors) will be pickled.
        tasks_args.append((
            i, num_frames, current_timestamp, current_data_slice,
            song_id_to_animator_key_map, album_art_image_objects, album_bar_colors, # Pass the new map
            N_BARS, chart_xaxis_limit, art_display_min_plays_threshold,
            output_image_path, dpi, fig_width_pixels, fig_height_pixels,
            LOG_FRAME_TIMES_CONFIG, PREFERRED_FONTS, LOG_PARALLEL_PROCESS_START_CONFIG # Pass config values needed by worker
        ))

    completed_frames = 0
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as executor:
        futures = [executor.submit(draw_and_save_single_frame, arg_tuple) for arg_tuple in tasks_args]
        for future in concurrent.futures.as_completed(futures):
            try:
                frame_idx, render_time, pid = future.result()
                frame_render_times_list.append(render_time)
                completed_frames += 1
                
                # Updated logging condition for frame completion
                should_log_completion = False
                if PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG > 0:
                    if completed_frames == 1 or completed_frames == num_frames or \
                       (completed_frames % PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG == 0):
                        should_log_completion = True
                elif PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG == 0: # Log only first and last if interval is 0
                    if completed_frames == 1 or completed_frames == num_frames:
                        should_log_completion = True

                if should_log_completion:
                    print(f"Frame {frame_idx + 1}/{num_frames} completed by PID {pid} in {render_time:.2f}s. ({completed_frames}/{num_frames} total done)")
            except Exception as exc:
                print(f'Frame generation failed: {exc}') # Handle error from worker
    
    overall_drawing_end_time = time.time()
    total_frame_rendering_cpu_time = sum(frame_render_times_list)
    print(f"--- Parallel Frame Generation Complete ---")
    print(f"Total wall-clock time for drawing {num_frames} frames: {overall_drawing_end_time - overall_drawing_start_time:.2f} seconds")
    if frame_render_times_list:
        avg_frame_render_time = total_frame_rendering_cpu_time / len(frame_render_times_list)
        print(f"Total CPU time sum for drawing frames:  {total_frame_rendering_cpu_time:.2f} seconds")
        print(f"Average time per frame (across processes): {avg_frame_render_time:.3f} seconds")


    print(f"\n--- Compiling video from frames using ffmpeg ---")
    print(f"Output video: {output_filename}")
    print(f"Target FPS: {target_fps_for_video}")

    # --- Define path for ffmpeg progress file ---
    progress_file_path = os.path.join(temp_frame_dir, "ffmpeg_progress.txt")

    # ffmpeg command construction
    base_ffmpeg_args = [
        'ffmpeg',
        '-framerate', str(target_fps_for_video),
        '-i', os.path.join(temp_frame_dir, f"frame_%0{len(str(num_frames))}d.png"), # Input pattern
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
                
                current_frame = int(progress_data.get('frame', last_reported_frame))
                speed = progress_data.get('speed', '0.0x').replace('x','')
                bitrate = progress_data.get('bitrate', 'N/A')
                # out_time_ms = int(progress_data.get('out_time_ms', '0'))
                # elapsed_seconds = out_time_ms / 1_000_000

                if current_frame > last_reported_frame or progress_data.get('progress') == 'end':
                    last_reported_frame = current_frame
                    percent_complete = (current_frame / total_frames) * 100 if total_frames > 0 else 0
                    
                    progress_line = f"Encoding: Frame {current_frame}/{total_frames} ({percent_complete:.1f}%) at {speed}x, Bitrate: {bitrate} Kbit/s"
                    
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
            monitor_ffmpeg_progress(process_nvenc, num_frames, progress_file_path)
            stdout, stderr = process_nvenc.communicate() # Wait for process to complete after monitoring

            if process_nvenc.returncode != 0:
                raise subprocess.CalledProcessError(process_nvenc.returncode, ffmpeg_cmd_nvenc, output=stdout, stderr=stderr)
            print("Video successfully compiled using NVENC.")
            
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
                monitor_ffmpeg_progress(process_cpu_fallback, num_frames, progress_file_path)
                stdout_cpu, stderr_cpu = process_cpu_fallback.communicate()

                if process_cpu_fallback.returncode != 0:
                    raise subprocess.CalledProcessError(process_cpu_fallback.returncode, ffmpeg_cmd_cpu_fallback, output=stdout_cpu, stderr=stderr_cpu)
                print("Video successfully compiled using libx264 (CPU).")
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
            monitor_ffmpeg_progress(process_cpu_direct, num_frames, progress_file_path)
            stdout, stderr = process_cpu_direct.communicate()

            if process_cpu_direct.returncode != 0:
                raise subprocess.CalledProcessError(process_cpu_direct.returncode, ffmpeg_cmd_cpu_direct, output=stdout, stderr=stderr)
            print("Video successfully compiled using libx264 (CPU).")
        except subprocess.CalledProcessError as e_cpu:
            print(f"\nERROR: ffmpeg (libx264) failed. Return code: {e_cpu.returncode}")
            if e_cpu.stdout: print(f"CPU STDOUT: {e_cpu.stdout.decode(errors='replace')}")
            if e_cpu.stderr: print(f"CPU STDERR: {e_cpu.stderr.decode(errors='replace')}")
            print("Video compilation failed.")
        except FileNotFoundError:
            print("\nERROR: ffmpeg command not found. Please ensure ffmpeg is installed and in your system's PATH.")
    
    # --- Cleanup intermediate frames and progress file ---
    if CLEANUP_INTERMEDIATE_FRAMES:
        try:
            shutil.rmtree(temp_frame_dir)
            print(f"Successfully removed temporary frame directory: {temp_frame_dir}")
        except OSError as e:
            print(f"Error removing temporary frame directory {temp_frame_dir}: {e}")
    else:
        print(f"Intermediate frames retained at: {temp_frame_dir}")
        # Still try to clean up progress file if frames are kept
        if os.path.exists(progress_file_path):
            try:
                os.remove(progress_file_path)
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
    load_configuration() # Load config first, sets up MAX_FRAMES_FOR_TEST_RENDER

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


    pipeline_start_time = time.time() # <--- ADDED TIMING
    full_race_df, song_details_map = run_data_pipeline() # Updated to receive song_details_map
    pipeline_end_time = time.time() # <--- ADDED TIMING
    print(f"--- Time taken for run_data_pipeline: {pipeline_end_time - pipeline_start_time:.2f} seconds ---") # <--- ADDED TIMING

    if full_race_df is None or full_race_df.empty:
        print("\nNo data available for animation. Please check your CSV file and data processing steps.")
        return

    print("\n--- Data ready for Animation ---")
    
    race_df_for_animation = full_race_df # Start with the full df

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
                    return # Cannot proceed with empty df
            except ValueError as e_resample:
                print(f"ERROR during aggregation with period '{aggregation_period_config}': {e_resample}.")
                print("Ensure the aggregation period is a valid pandas offset alias (e.g., 'D', 'H', 'S', 'W', 'M', '30T'). Proceeding with event-based frames.")
                race_df_for_animation = full_race_df # Fallback to original df if aggregation failed
            except Exception as e_generic_resample:
                print(f"An unexpected error occurred during aggregation: {e_generic_resample}. Proceeding with event-based frames.")
                race_df_for_animation = full_race_df # Fallback
    else:
        print("\n--- Using event-based frames (no aggregation selected or DataFrame was empty) ---")
    
    # Use MAX_FRAMES_FOR_TEST_RENDER from config
    # MAX_FRAMES_FOR_TEST_RENDER is already a global variable updated by load_configuration()
    if MAX_FRAMES_FOR_TEST_RENDER > 0 and MAX_FRAMES_FOR_TEST_RENDER < len(race_df_for_animation): # Use len(race_df_for_animation)
        print(f"WARNING: Using a SUBSET of data for animation (first {MAX_FRAMES_FOR_TEST_RENDER} frames of potentially aggregated data).")
        race_df_for_animation = race_df_for_animation.head(MAX_FRAMES_FOR_TEST_RENDER)
    elif MAX_FRAMES_FOR_TEST_RENDER > 0:
         print(f"Note: MAX_FRAMES_FOR_TEST_RENDER ({MAX_FRAMES_FOR_TEST_RENDER}) is >= total frames ({len(race_df_for_animation)}). Rendering full video (or full aggregated video).")
    
    # Now, call create_bar_chart_race_animation with the potentially truncated and/or aggregated race_df_for_animation
    # The pre_fetch logic is inside create_bar_chart_race_animation, so it will use the df passed to it.
    create_bar_chart_race_animation(race_df_for_animation, song_details_map) # Pass song_details_map


if __name__ == "__main__":
    # The global `config` will be loaded in main().
    # album_art_utils is imported, and its initialize_from_config will be called from main_animator.load_configuration()
    main()