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

# --- Global Dictionaries for Caching Art Paths and Colors within the animator ---
album_art_image_objects = {}
album_bar_colors = {}

def load_configuration():
    global config, N_BARS, TARGET_FPS, OUTPUT_FILENAME_BASE, DEBUG_ALBUM_ART_LOGIC
    global ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR, USE_NVENC_IF_AVAILABLE, PREFERRED_FONTS
    global MAX_FRAMES_FOR_TEST_RENDER, LOG_FRAME_TIMES_CONFIG

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
    race_df, song_album_map = prepare_data_for_bar_chart_race(cleaned_df)
    if race_df is None or race_df.empty: 
        print("Data preparation for race resulted in no data. Exiting.")
        return None, song_album_map
        
    print("Data preparation successful.")
    print(f"Race DataFrame shape: {race_df.shape} (Play Events, Unique Songs)")
    print(f"Number of entries in song_album_map: {len(song_album_map)}")
    print("--- Data Processing Pipeline Complete ---")
    return race_df, song_album_map


def pre_fetch_album_art_and_colors(race_df, song_album_map, unique_song_ids_in_race, global_visibility_threshold, target_img_height_pixels_for_resize, fig_dpi):
    # This function now uses album_art_utils directly, which is config-aware
    print(f"\n--- Pre-fetching album art and dominant colors (Target Img Resize Height: {target_img_height_pixels_for_resize}px, Visibility Threshold: >={global_visibility_threshold:.2f} plays) ---")
    
    # This set will now track CANONICAL album names for which PIL/color is loaded in main_animator
    # to avoid redundant PIL loading and dominant color calculation for the same canonical album.
    canonical_albums_loaded_in_animator_cache = set()
    
    processed_count = 0
    skipped_due_to_threshold = 0

    for song_id in unique_song_ids_in_race:
        try:
            artist_name, track_name = song_id.split(" - ", 1)
        except ValueError:
            # This warning was already in your code, good to keep.
            print(f"WARNING: Could not parse artist/track from song_id: '{song_id}'. Skipping pre-fetch for this song.")
            continue

        album_name_from_lastfm = song_album_map.get(song_id)
        if not album_name_from_lastfm:
            if DEBUG_ALBUM_ART_LOGIC: # DEBUG_ALBUM_ART_LOGIC is your global from config
                print(f"[PRE-FETCH DEBUG] No album in song_album_map for '{song_id}'. Skipping art/color processing.")
            continue

        # --- Visibility Threshold Check (from your original code) ---
        # Ensure race_df is available here and contains the song_id as a column
        if song_id not in race_df.columns:
            if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH DEBUG] Song ID '{song_id}' not found in race_df columns. Skipping.")
            continue # Should not happen if unique_song_ids_in_race comes from race_df.columns

        max_plays_for_this_song = race_df[song_id].max()

        max_plays_for_this_song = race_df[song_id].max()

        # if "Kristen Bell - For the First Time in Forever" in song_id: # Temporary specific check
        #     print(f"[THRESHOLD_CHECK_DEBUG] For '{song_id}', max_plays_for_this_song = {max_plays_for_this_song}. global_visibility_threshold = {global_visibility_threshold:.2f}")
            
        if max_plays_for_this_song < global_visibility_threshold:
            if DEBUG_ALBUM_ART_LOGIC:
                print(f"[PRE-FETCH DEBUG] Song '{song_id}' (max plays: {max_plays_for_this_song}) is below visibility threshold ({global_visibility_threshold:.2f}). Skipping art/color processing.")
            skipped_due_to_threshold += 1
            continue
        
        if DEBUG_ALBUM_ART_LOGIC:
            print(f"[PRE-FETCH DEBUG] Song '{song_id}' (max plays: {max_plays_for_this_song}) meets threshold. Processing album hint: '{album_name_from_lastfm}'.")

        # --- Call album_art_utils to get path and Spotify info ---
        # album_art_utils.py handles its own internal caching (spotify_info_cache, image file cache, dominant_color_cache)
        # to avoid redundant API calls and downloads.
        
        # Original print for user feedback on what's being processed
        try:
            print(f"Processing art/color for: Artist='{artist_name}', Track='{track_name}', Album (Hint)='{album_name_from_lastfm}'")
        except UnicodeEncodeError: # Handle potential encoding issues in print
            safe_artist = artist_name.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            safe_track = track_name.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            safe_album_lastfm = album_name_from_lastfm.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            print(f"Processing art/color for: Artist='{safe_artist}', Track='{safe_track}', Album (Hint)='{safe_album_lastfm}'")

        # This call now happens for every song that meets the threshold.
        art_path = album_art_utils.get_album_art_path(artist_name, track_name, album_name_from_lastfm)
        
        # --- Determine the canonical_album_name_from_spotify ---
        # We need this to key the animator's local PIL image and color caches correctly.
        canonical_album_name_for_animator_cache = album_name_from_lastfm # Fallback to hint
        
        # Access the populated spotify_info_cache from album_art_utils
        # This cache was populated (or hit) during the get_album_art_path call.
        _spotify_cache_key = f"spotify_{artist_name.lower().strip()}_{track_name.lower().strip()}_{album_name_from_lastfm.lower().strip()}"
        spotify_info_entry = album_art_utils.spotify_info_cache.get(_spotify_cache_key)
        
        if spotify_info_entry and spotify_info_entry.get("canonical_album_name"):
            canonical_album_name_for_animator_cache = spotify_info_entry["canonical_album_name"]
            if DEBUG_ALBUM_ART_LOGIC and canonical_album_name_for_animator_cache != album_name_from_lastfm:
                print(f"[PRE-FETCH DEBUG] Canonical album for '{song_id}' is '{canonical_album_name_for_animator_cache}' (hint was '{album_name_from_lastfm}').")
        elif DEBUG_ALBUM_ART_LOGIC:
             print(f"[PRE-FETCH DEBUG] Could not find canonical album name in spotify_info_cache for key '{_spotify_cache_key}'. Using hint '{album_name_from_lastfm}' for animator cache key.")


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
                print(f"[PRE-FETCH DEBUG] No art path returned by album_art_utils for '{song_id}' (Hint: '{album_name_from_lastfm}').")
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


def create_bar_chart_race_animation(race_df, song_album_map_lastfm): # race_df here is already potentially truncated
    if race_df is None or race_df.empty:
        print("Cannot create animation: race_df is empty or None.")
        return

    # ... (setup for resolution, filename, interval as before) ...
    # num_frames will be len(race_df.index), which is correct for the truncated df

    # This unique_song_ids_in_race will be from the (potentially) truncated race_df
    unique_song_ids_in_race = race_df.columns.tolist()

    # This max play count will be from the (potentially) truncated race_df
    raw_max_play_count_overall = race_df.max().max()
    if pd.isna(raw_max_play_count_overall) or raw_max_play_count_overall <= 0:
        raw_max_play_count_overall = 100 # Fallback
    
    # --- Calculate target_img_height_pixels before pre_fetch ---
    # This logic is moved from draw_frame to here
    selected_res_key = config.get('AnimationOutput', 'RESOLUTION', '4k').strip()
    res_settings = VIDEO_RESOLUTION_PRESETS.get(selected_res_key, VIDEO_RESOLUTION_PRESETS['4k'])
    dpi = res_settings['dpi']
    fig_height_pixels = res_settings['height'] # Directly use configured height in pixels

    # Constants from draw_frame's image scaling logic
    example_bar_height_data_units = 0.8 
    image_height_scale_factor = 0.35 # This was part of target_img_height_pixels calculation

    # Ensure N_BARS is positive to avoid division by zero
    if N_BARS <= 0:
        print(f"ERROR: N_BARS is {N_BARS}, which is invalid. Defaulting to 10 for image sizing.")
        current_n_bars_for_sizing = 10 # Use a local var for sizing to avoid changing global N_BARS for actual drawing
    else:
        current_n_bars_for_sizing = N_BARS
        
    # This is the target display height of the image on the plot in pixels
    calculated_target_img_height_pixels = \
        (example_bar_height_data_units / current_n_bars_for_sizing) * \
        fig_height_pixels * image_height_scale_factor
    
    art_processing_min_plays_threshold = raw_max_play_count_overall * ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR
    print(f"[ANIMATOR_INFO] global_visibility_threshold (art_processing_min_plays_threshold) = {art_processing_min_plays_threshold:.2f}")
    print(f"[ANIMATOR_INFO] Based on raw_max_play_count_overall = {raw_max_play_count_overall} and ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR = {ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR}")
    print(f"[ANIMATOR_INFO] Calculated target image height for pre-resize: {calculated_target_img_height_pixels:.2f} pixels (based on {selected_res_key} output resolution height {fig_height_pixels}px)")

    art_fetch_start_time = time.time() # <--- ADDED TIMING
    pre_fetch_album_art_and_colors(race_df, song_album_map_lastfm, unique_song_ids_in_race, art_processing_min_plays_threshold, calculated_target_img_height_pixels, dpi)
    art_fetch_end_time = time.time() # <--- ADDED TIMING
    print(f"--- Time taken for pre_fetch_album_art_and_colors: {art_fetch_end_time - art_fetch_start_time:.2f} seconds ---") # <--- ADDED TIMING

    # Get animation parameters from global config (already loaded)
    # selected_res_key, res_settings, dpi already fetched above for image sizing
    # config = AppConfig() # This would reload config, not needed. Config is global.
    
    width = res_settings['width']
    height = res_settings['height']
    # dpi already set
    
    output_filename = f"{OUTPUT_FILENAME_BASE}_{selected_res_key}.mp4"
    interval = 1000 / TARGET_FPS # TARGET_FPS from config

    num_frames = len(race_df.index)
    target_fps_for_video = 1000.0 / interval

    # For frame timing
    frame_render_times_list = []
    overall_animation_start_time = time.time() # For overall timing including save

    print(f"\n--- Starting Animation Creation for {output_filename} ---")
    print(f"Total frames to render: {num_frames}")
    print(f"Target video FPS: {target_fps_for_video:.2f}")
    print(f"Resolution: {width}x{height} @ {dpi} DPI")
    print(f"Attempting NVENC: {USE_NVENC_IF_AVAILABLE}") # USE_NVENC_IF_AVAILABLE from config
    
    figsize_w = width / dpi
    figsize_h = height / dpi
    fig, ax = plt.subplots(figsize=(figsize_w, figsize_h), dpi=dpi)
    
    unique_song_ids_in_race = race_df.columns.tolist()

    raw_max_play_count_overall = race_df.max().max()
    if pd.isna(raw_max_play_count_overall) or raw_max_play_count_overall <= 0:
        raw_max_play_count_overall = 100
    
    art_processing_min_plays_threshold = raw_max_play_count_overall * ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR # from config
    chart_xaxis_limit = raw_max_play_count_overall * 1.05
    art_display_min_plays_threshold = art_processing_min_plays_threshold

    print(f"Calculated Art Processing Threshold (min plays for a song to have its art processed): >={art_processing_min_plays_threshold:.2f}")
    print(f"Calculated Art Display Threshold (min plays for art to show on a bar): >={art_display_min_plays_threshold:.2f}")
    print(f"Chart X-axis limit: {chart_xaxis_limit:.2f}")

    # pre_fetch_album_art_and_colors called earlier with calculated_target_img_height_pixels
    # pre_fetch_album_art_and_colors(race_df, song_album_map_lastfm, unique_song_ids_in_race, art_processing_min_plays_threshold)
    
    song_id_to_canonical_album_map = {}
    for song_id in unique_song_ids_in_race:
        try:
            artist_name, track_name = song_id.split(" - ", 1)
            album_name_hint = song_album_map_lastfm.get(song_id, "")
            spotify_cache_key = f"spotify_{artist_name.lower().strip()}_{track_name.lower().strip()}_{album_name_hint.lower().strip()}"
            
            # Access the cache from the initialized album_art_utils module
            spotify_data = album_art_utils.spotify_info_cache.get(spotify_cache_key)
            if spotify_data and spotify_data.get("canonical_album_name"):
                song_id_to_canonical_album_map[song_id] = spotify_data["canonical_album_name"]
            else:
                song_id_to_canonical_album_map[song_id] = album_name_hint
        except ValueError:
            song_id_to_canonical_album_map[song_id] = song_album_map_lastfm.get(song_id, "Unknown Album")

    # --- draw_frame function ---
    # (Keep draw_frame as is, but ensure N_BARS used inside it is the one from config)
    # ... (your existing draw_frame function, ensuring it uses the global N_BARS)
    # Inside draw_frame, replace hardcoded `n_bars` with the global `N_BARS` (from config).
    def draw_frame(frame_index):
        nonlocal frame_render_times_list # Added for timing
        frame_start_time = time.time() # Added for timing

        current_timestamp = race_df.index[frame_index]
        ax.clear()

        # Modified print statement for frame timing
        if LOG_FRAME_TIMES_CONFIG:
            if (frame_index + 1) % 10 == 0 or frame_index == 0 or (frame_index + 1) == num_frames:
                log_message_parts = [f"Rendering frame {frame_index + 1}/{num_frames} ({current_timestamp.strftime('%Y-%m-%d %H:%M:%S')})."]
                
                # Calculate running average FPS for logging purposes based on *completed* frames
                if frame_render_times_list: # If there are completed frames
                    current_total_render_time_completed = sum(frame_render_times_list)
                    avg_fps_completed = len(frame_render_times_list) / current_total_render_time_completed if current_total_render_time_completed > 0 else float('inf')
                    log_message_parts.append(f"Last frame: {frame_render_times_list[-1]:.3f}s.")
                    log_message_parts.append(f"Avg FPS (rendered): {avg_fps_completed:.2f}")
                else: # No frames completed yet (this is the first frame being processed)
                    log_message_parts.append("Avg FPS (rendered): Starting...")
                print(" ".join(log_message_parts))
        elif (frame_index + 1) % 100 == 0 or frame_index == 0: # Original conditional print
            print(f"Rendering frame {frame_index + 1}/{num_frames} ({current_timestamp.strftime('%Y-%m-%d %H:%M:%S')})...")

        current_data_slice = race_df.iloc[frame_index]
        top_n_songs = current_data_slice[current_data_slice > 0].nlargest(N_BARS) # N_BARS from config
        
        songs_to_draw = top_n_songs.sort_values(ascending=True)

        date_str = current_timestamp.strftime('%d %B %Y %H:%M:%S')
        ax.text(0.98, 0.05, date_str, transform=ax.transAxes,
                ha='right', va='bottom', fontsize=20 * (dpi/100.0), color='dimgray', weight='bold') # Font size might need scaling factor from config for 1080p vs 4k

        ax.set_xlabel("Total Plays", fontsize=18 * (dpi/100.0), labelpad=15 * (dpi/100.0))
        ax.set_xlim(0, chart_xaxis_limit)
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        ax.xaxis.set_ticks_position('top')
        ax.xaxis.set_label_position('top')
        tick_label_fontsize = 11 * (dpi/100.0)
        ax.tick_params(axis='x', labelsize=tick_label_fontsize)

        ax.set_ylim(-0.5, N_BARS - 0.5) # N_BARS from config
        ax.set_yticks(np.arange(N_BARS)) # N_BARS from config
        
        y_tick_labels = [""] * N_BARS # N_BARS from config
        
        bar_y_positions = []
        bar_widths = []
        bar_colors_list = []
        bar_song_ids = []

        for i, song_id in enumerate(songs_to_draw.index):
            rank_on_chart = len(songs_to_draw) - 1 - i 
            y_pos_for_bar = N_BARS - 1 - rank_on_chart # N_BARS from config
            
            bar_y_positions.append(y_pos_for_bar)
            bar_widths.append(songs_to_draw[song_id])
            bar_song_ids.append(song_id)

            canonical_album = song_id_to_canonical_album_map.get(song_id, "Unknown Album")
            bar_colors_list.append(album_bar_colors.get(canonical_album, (0.5,0.5,0.5)))
            
            max_char_len = int(50 * (150.0/dpi)) 
            display_song_id = song_id
            if len(song_id) > max_char_len:
                display_song_id = song_id[:max_char_len-3] + "..."
            y_tick_labels[y_pos_for_bar] = display_song_id
            
        ax.set_yticklabels(y_tick_labels, fontsize=tick_label_fontsize)

        if bar_y_positions:
            actual_bars = ax.barh(bar_y_positions, bar_widths, color=bar_colors_list, height=0.8, zorder=2)

            # example_bar_height_data_units = 0.8 # Used for target_img_height_pixels calculation, now done before pre_fetch_album_art_and_colors
            # target_img_height_pixels calculation is now done *before* pre_fetch_album_art_and_colors
            # The value used for pre-sizing was calculated_target_img_height_pixels

            value_label_fontsize = 12 * (dpi/100.0)
            image_padding_data_units = chart_xaxis_limit * 0.005
            value_label_padding_data_units = chart_xaxis_limit * 0.008

            for i, bar_obj in enumerate(actual_bars):
                song_id_for_bar = bar_song_ids[i]
                current_play_count = bar_widths[i]
                
                canonical_album_for_bar = song_id_to_canonical_album_map.get(song_id_for_bar, "Unknown Album")
                pil_image = album_art_image_objects.get(canonical_album_for_bar)

                # --- Position for image and text, starting from end of bar and moving left ---
                current_x_anchor = bar_obj.get_width() # << इंश्योर THIS LINE IS PRESENT AND ACTIVE

                # Add album art if conditions met
                if pil_image and current_play_count >= art_display_min_plays_threshold:
                    try:
                        # ... (image processing logic that READS current_x_anchor) ...
                        # Image is now pre-resized. Get its dimensions.
                        resized_img_width_pixels, resized_img_height_pixels = pil_image.size 
                        
                        fig_width_pixels = fig.get_size_inches()[0] * dpi
                        x_axis_range_data_units = ax.get_xlim()[1] - ax.get_xlim()[0] # chart_xaxis_limit
                        image_width_data_units = 0
                        if fig_width_pixels > 0 and x_axis_range_data_units > 0:
                             image_width_data_units = (resized_img_width_pixels / fig_width_pixels) * x_axis_range_data_units
                        
                        # Position image: its right edge is at (current_x_anchor - image_padding_data_units)
                        img_center_x_pos = current_x_anchor - image_padding_data_units - (image_width_data_units / 2.0) 
                        
                        if img_center_x_pos - (image_width_data_units / 2.0) > chart_xaxis_limit * 0.02: # Ensure some space from y-axis
                            imagebox = OffsetImage(pil_image, zoom=1.0, resample=False) # Use pre-resized pil_image directly
                            ab = AnnotationBbox(imagebox,
                                                (img_center_x_pos, bar_obj.get_y() + bar_obj.get_height() / 2.0),
                                                xybox=(0,0), xycoords='data', boxcoords="offset points",
                                                pad=0, frameon=False, zorder=3)
                            ax.add_artist(ab)
                            # Update current_x_anchor to be the left edge of the image
                            # THIS LINE ASSIGNS/UPDATES current_x_anchor:
                            current_x_anchor = img_center_x_pos - (image_width_data_units / 2.0)
                        # else: image is too wide or bar too short, current_x_anchor remains bar_obj.get_width()

                    except Exception as e:
                        # The error message in your screenshot is exactly this one.
                        print(f"Error processing/adding image for {canonical_album_for_bar} (Song: {song_id_for_bar}): {e}")
                
                # Add play count text (this part seems fine as it doesn't use current_x_anchor for its primary positioning)
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
            if DEBUG_ALBUM_ART_LOGIC: print(f"Note: Layout adjustment warning/error: {e_layout}. Plot might not be perfectly aligned.")
            plt.subplots_adjust(left=left_margin, bottom=bottom_margin, right=right_margin, top=top_margin)
        
        # Record frame render time
        current_frame_render_time = time.time() - frame_start_time
        frame_render_times_list.append(current_frame_render_time)
    # --- End of draw_frame ---

    ani = animation.FuncAnimation(fig, draw_frame, frames=num_frames,
                                  interval=interval, repeat=False)

    print(f"\nPreparing to save animation to {output_filename}...")
    
    writer_to_use = None
    if USE_NVENC_IF_AVAILABLE and animation.FFMpegWriter.isAvailable(): # USE_NVENC from config
        # ... (NVENC writer logic remains same) ...
        print("Attempting to use NVENC (h264_nvenc) for hardware acceleration...")
        try:
            nvenc_args = ['-preset', 'p6', '-tune', 'hq', '-b:v', '0', '-cq', '23', '-rc-lookahead', '20', '-pix_fmt', 'yuv420p']
            writer_nvenc = animation.FFMpegWriter(fps=target_fps_for_video, codec='h264_nvenc', bitrate=-1, extra_args=nvenc_args)
            _ = writer_nvenc.saving(fig, "test.mp4", dpi) # Test call to ensure it can initialize
            writer_to_use = writer_nvenc
            print("NVENC writer initialized successfully.")
        except Exception as e_nvenc_init:
            print(f"WARNING: Could not initialize NVENC writer: {e_nvenc_init}")
            print("Falling back to CPU encoder (libx264).")
            writer_to_use = None # Ensure fallback

    if writer_to_use is None: # Fallback if NVENC not available or failed to init
        print("Using CPU encoder (libx264).")
        cpu_args = ['-crf', '23', '-preset', 'medium', '-pix_fmt', 'yuv420p']
        writer_to_use = animation.FFMpegWriter(fps=target_fps_for_video, codec='libx264', bitrate=-1, extra_args=cpu_args)

    try:
        animation_save_start_time = time.time()
        ani.save(output_filename, writer=writer_to_use, dpi=dpi)
        animation_save_end_time = time.time()
        print(f"Animation successfully saved to {output_filename}")

        # --- Frame Timing Summary ---
        overall_animation_end_time = time.time()
        if LOG_FRAME_TIMES_CONFIG and frame_render_times_list:
            total_frame_rendering_cpu_time = sum(frame_render_times_list)
            avg_frame_render_time = total_frame_rendering_cpu_time / len(frame_render_times_list) if frame_render_times_list else 0
            overall_avg_fps_cpu = 1.0 / avg_frame_render_time if avg_frame_render_time > 0 else float('inf')
            min_render_time = min(frame_render_times_list) if frame_render_times_list else 0
            max_render_time = max(frame_render_times_list) if frame_render_times_list else 0
            # For median, we need numpy or to sort the list
            sorted_times = sorted(frame_render_times_list)
            median_render_time = sorted_times[len(sorted_times) // 2] if sorted_times else 0

            total_wall_clock_time = overall_animation_end_time - overall_animation_start_time
            video_saving_time = animation_save_end_time - animation_save_start_time

            print("\n--- Animation Rendering Summary ---")
            print(f"Total wall-clock time (incl. save): {total_wall_clock_time:.2f} seconds")
            print(f"  Estimated video saving time:        {video_saving_time:.2f} seconds")
            print(f"  Total CPU time for drawing frames:  {total_frame_rendering_cpu_time:.2f} seconds")
            print(f"  Number of frames rendered:          {len(frame_render_times_list)}")
            print(f"  Average FPS (CPU frame drawing):    {overall_avg_fps_cpu:.2f}")
            print(f"  Frame render times (seconds):")
            print(f"    Min:    {min_render_time:.3f}")
            print(f"    Max:    {max_render_time:.3f}")
            print(f"    Median: {median_render_time:.3f}")
            print(f"    Avg:    {avg_frame_render_time:.3f}")

    except FileNotFoundError: # This usually means ffmpeg itself is not found
        print("ERROR: ffmpeg not found. Please ensure ffmpeg is installed and in your system's PATH.")
    except Exception as e: # Re-adding the general exception for ani.save
        print(f"Error saving animation: {e}")
    finally:
        plt.close(fig) # Ensure figure is closed


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
    full_race_df, song_album_map_lastfm = run_data_pipeline()
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
    create_bar_chart_race_animation(race_df_for_animation, song_album_map_lastfm)


if __name__ == "__main__":
    # The global `config` will be loaded in main().
    # album_art_utils is imported, and its initialize_from_config will be called from main_animator.load_configuration()
    main()