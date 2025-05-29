# main_animator.py
import pandas as pd
from data_processor import clean_spotify_data, prepare_data_for_bar_chart_race
# Updated import: get_album_art_path now needs artist, track, album_hint
from album_art_utils import get_album_art_path, get_dominant_color 

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

# --- Configuration for Animation ---
N_BARS = 10
TARGET_FPS = 30 
ANIMATION_INTERVAL = 1000 / TARGET_FPS 

OUTPUT_FILENAME = "spotify_top_songs_2024_4k.mp4"
VIDEO_RESOLUTION_WIDTH = 3840
VIDEO_RESOLUTION_HEIGHT = 2160
VIDEO_DPI = 165 

DEBUG_ALBUM_ART_LOGIC = True # For verbose logging in pre_fetch and drawing

# --- Album Art Display Logic ---
# Show album art if play count is > (ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR * max_plays_in_chart)
# Based on 110 plays for a max_plays_in_chart of 1750
ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR = 110.0 / 1750.0 
# ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR = 0.0628 # approximately

# --- FFmpeg Configuration ---
# Option 1: Ensure ffmpeg is in your system's PATH.
# Option 2: Explicitly set the path.
# plt.rcParams['animation.ffmpeg_path'] = r'C:\path\to\your\ffmpeg.exe' 
# plt.rcParams['animation.ffmpeg_path'] = '/usr/local/bin/ffmpeg'

# --- Encoder Preference ---
# Set to True to attempt NVENC, False for CPU (libx264). Will fallback to CPU if NVENC fails.
USE_NVENC_IF_AVAILABLE = True # Set to True to try NVENC

PREFERRED_FONTS = [
    'DejaVu Sans', 
    'Noto Sans JP', 'Noto Sans KR', 'Noto Sans SC', 'Noto Sans TC', 
    'Arial Unicode MS', 
    'sans-serif' 
]
try:
    plt.rcParams['font.family'] = PREFERRED_FONTS
except Exception as e:
    print(f"Warning: Could not set preferred fonts: {e}")


# --- Global Dictionaries for Caching Art Paths and Colors within the animator ---
album_art_image_objects = {} # Cache loaded PIL.Image objects {canonical_album_name: PIL.Image}
album_bar_colors = {}        # Cache {canonical_album_name: color_tuple}


def run_data_pipeline():
    print("--- Starting Data Processing Pipeline ---")
    csv_file_path = "lastfm_data.csv" # Make sure this file exists
    # Create dummy if not exists for basic testing
    if not os.path.exists(csv_file_path):
        print(f"Warning: '{csv_file_path}' not found.")
        print("Creating a minimal dummy 'lastfm_data.csv' for this test run.")
        dummy_csv_content = """uts,utc_time,artist,artist_mbid,album,album_mbid,track,track_mbid
1704067200,"01 Jan 2024, 00:00:00","Artist A","mbid_a","Album X","mbid_ax","Song 1","mbid_s1"
1704067260,"01 Jan 2024, 00:01:00","Artist B","mbid_b","Album Y","mbid_ay","Song 2","mbid_s2"
1704067320,"01 Jan 2024, 00:02:00","Artist A","mbid_a","Album X","mbid_ax","Song 1","mbid_s1"
"""
        with open(csv_file_path, "w", encoding='utf-8') as f:
            f.write(dummy_csv_content)
        print(f"Created dummy '{csv_file_path}'.")

    print(f"\nStep 1: Cleaning data from '{csv_file_path}'...")
    cleaned_df = clean_spotify_data(csv_file_path)
    if cleaned_df is None or cleaned_df.empty: 
        print("Data cleaning resulted in no data. Exiting.")
        return None, {}
    print(f"Data cleaning successful. {len(cleaned_df)} relevant rows found.")
    
    print("\nStep 2: Preparing data for bar chart race (high-resolution timestamps)...")
    race_df, song_album_map = prepare_data_for_bar_chart_race(cleaned_df)
    if race_df is None or race_df.empty: 
        print("Data preparation for race resulted in no data. Exiting.")
        return None, song_album_map # song_album_map might exist if cleaned_df had some data
        
    print("Data preparation successful.")
    print(f"Race DataFrame shape: {race_df.shape} (Play Events, Unique Songs)")
    print(f"Number of entries in song_album_map: {len(song_album_map)}") # Maps song_id to Last.fm album name
    print("--- Data Processing Pipeline Complete ---")
    return race_df, song_album_map


def pre_fetch_album_art_and_colors(race_df, song_album_map, unique_song_ids_in_race, global_visibility_threshold):
    """
    Iterate through albums for songs that might appear with art, to fetch art and dominant colors.
    Only fetches/processes if the song's max play count meets the global_visibility_threshold.

    Args:
        race_df (pd.DataFrame): The main data frame for the race.
        song_album_map (dict): Maps song_id to Last.fm album name (album_name_hint).
        unique_song_ids_in_race (list): List of all song_ids present in race_df columns.
        global_visibility_threshold (float): Minimum play count a song needs to ever have
                                             for its album art to be considered for fetching/loading.
    """
    print(f"\n--- Pre-fetching album art and dominant colors (Visibility Threshold: >={global_visibility_threshold:.2f} plays) ---")
    
    # This set tracks processed (Artist_LastFMAlbumName) combinations to avoid redundant PIL loading for same album from Last.fm
    # The underlying Spotify cache will handle redundant API calls for the same (Artist, Track, AlbumHint).
    albums_processed_for_pil_and_color = set() 
    processed_count = 0
    skipped_due_to_threshold = 0

    for song_id in unique_song_ids_in_race:
        # song_id is "Artist - Track"
        try:
            artist_name, track_name = song_id.split(" - ", 1)
        except ValueError:
            print(f"WARNING: Could not parse artist/track from song_id: '{song_id}'. Skipping pre-fetch for this song.")
            continue

        album_name_from_lastfm = song_album_map.get(song_id)
        if not album_name_from_lastfm:
            if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH DEBUG] No album in song_album_map for '{song_id}'. Skipping.")
            continue

        # Check if this song ever reaches the visibility threshold
        max_plays_for_this_song = race_df[song_id].max()
        if max_plays_for_this_song < global_visibility_threshold:
            if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH DEBUG] Song '{song_id}' (max plays: {max_plays_for_this_song}) is below visibility threshold ({global_visibility_threshold:.2f}). Skipping art/color processing.")
            skipped_due_to_threshold += 1
            continue
        
        if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH DEBUG] Song '{song_id}' (max plays: {max_plays_for_this_song}) meets threshold. Processing album '{album_name_from_lastfm}'.")

        # Key for this session's PIL/color processing, based on Last.fm data before Spotify canonical names
        # This is to avoid re-loading PIL images for the same "album" (as perceived from Last.fm) multiple times
        # if multiple tracks from it are in the chart.
        album_processing_key = f"{artist_name}_{album_name_from_lastfm}"

        if album_processing_key in albums_processed_for_pil_and_color:
            if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH DEBUG] Already processed PIL/color for album key '{album_processing_key}' this session. Skipping redundant load.")
            continue
        
        # Robust printing for console output with Unicode
        try:
            print(f"Processing art/color for: Artist='{artist_name}', Track='{track_name}', Album (Last.fm)='{album_name_from_lastfm}'")
        except UnicodeEncodeError:
            safe_artist = artist_name.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            safe_track = track_name.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            safe_album_lastfm = album_name_from_lastfm.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            print(f"Processing art/color for: Artist='{safe_artist}', Track='{safe_track}', Album (Last.fm)='{safe_album_lastfm}'")

        # album_art_utils.get_album_art_path now uses its own disk cache for Spotify info and downloaded images.
        # It returns the local path to the (potentially newly downloaded) image.
        art_path = get_album_art_path(artist_name, track_name, album_name_from_lastfm)
        
        # The canonical album name is needed for the in-memory caches (album_art_image_objects, album_bar_colors)
        # We need to retrieve it from the spotify_info_cache if art_path was found.
        # This is a bit indirect; ideally get_album_art_path would return a dict with path and canonical name.
        # For now, we re-construct the cache key for spotify_info_cache.
        # (This part could be refactored in album_art_utils for cleaner return if we do more there)
        
        canonical_album_name_for_caching = album_name_from_lastfm # Fallback
        if art_path: # If art_path exists, spotify_info_cache should have an entry
            spotify_cache_key = f"spotify_{artist_name.lower().strip()}_{track_name.lower().strip()}_{album_name_from_lastfm.lower().strip()}"
            spotify_data = album_art_utils.spotify_info_cache.get(spotify_cache_key) # Access loaded cache
            if spotify_data and spotify_data.get("canonical_album_name"):
                canonical_album_name_for_caching = spotify_data["canonical_album_name"]
            else: # Should ideally not happen if art_path was successfully retrieved via Spotify
                 if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH WARNING] Art path '{art_path}' found, but no canonical album name in Spotify cache for key '{spotify_cache_key}'. Using Last.fm album name '{album_name_from_lastfm}'.")


        if art_path:
            # Load PIL Image into memory cache if not already there for this canonical_album_name
            if canonical_album_name_for_caching not in album_art_image_objects:
                try:
                    img = Image.open(art_path)
                    album_art_image_objects[canonical_album_name_for_caching] = img.copy() # Store a copy
                    img.close()
                    if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH DEBUG] Loaded PIL image for '{canonical_album_name_for_caching}' into memory.")
                except Exception as e:
                    print(f"Error loading image {art_path} into PIL object: {e}")
                    album_art_image_objects[canonical_album_name_for_caching] = None # Mark as failed to load
            
            # Get/calculate dominant color and store in memory cache if not already there for this canonical_album_name
            if canonical_album_name_for_caching not in album_bar_colors:
                dc = get_dominant_color(art_path) # Uses its own disk cache for dominant colors
                album_bar_colors[canonical_album_name_for_caching] = (dc[0]/255.0, dc[1]/255.0, dc[2]/255.0)
                if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH DEBUG] Calculated/loaded dominant color for '{canonical_album_name_for_caching}'.")
        else:
            # No art path found, ensure defaults are in memory cache for this canonical_album_name (which might just be album_name_from_lastfm)
            if canonical_album_name_for_caching not in album_art_image_objects:
                album_art_image_objects[canonical_album_name_for_caching] = None
            if canonical_album_name_for_caching not in album_bar_colors:
                album_bar_colors[canonical_album_name_for_caching] = (0.5, 0.5, 0.5) # Default gray
            if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH DEBUG] No art path for '{artist_name} - {track_name}'. Using defaults for '{canonical_album_name_for_caching}'.")

        albums_processed_for_pil_and_color.add(album_processing_key)
        processed_count +=1
        
    print(f"--- Pre-fetching complete ---")
    print(f"Attempted to process art/color for {processed_count} song-album groups that met threshold.")
    print(f"Skipped {skipped_due_to_threshold} song-album groups due to not meeting visibility threshold.")
    print(f"In-memory PIL images: {len(album_art_image_objects)}, In-memory bar colors: {len(album_bar_colors)}")


def create_bar_chart_race_animation(race_df, song_album_map_lastfm, n_bars=N_BARS,
                                    output_filename=OUTPUT_FILENAME, interval=ANIMATION_INTERVAL,
                                    width=VIDEO_RESOLUTION_WIDTH, height=VIDEO_RESOLUTION_HEIGHT,
                                    dpi=VIDEO_DPI, use_nvenc=USE_NVENC_IF_AVAILABLE):
    if race_df is None or race_df.empty:
        print("Cannot create animation: race_df is empty or None.")
        return

    num_frames = len(race_df.index)
    target_fps_for_video = 1000.0 / interval

    print(f"\n--- Starting Animation Creation for {output_filename} ---")
    print(f"Total frames to render: {num_frames}")
    print(f"Target video FPS: {target_fps_for_video:.2f}")
    print(f"Resolution: {width}x{height} @ {dpi} DPI")
    print(f"Attempting NVENC: {use_nvenc}")
    
    figsize_w = width / dpi
    figsize_h = height / dpi
    fig, ax = plt.subplots(figsize=(figsize_w, figsize_h), dpi=dpi)
    
    unique_song_ids_in_race = race_df.columns.tolist()

    # Determine overall max play count to calculate visibility threshold for pre-fetch
    raw_max_play_count_overall = race_df.max().max()
    if pd.isna(raw_max_play_count_overall) or raw_max_play_count_overall <= 0:
        raw_max_play_count_overall = 100 # Fallback if data is weird
    
    # This is the play count a song must achieve at least once for its art to be processed
    art_processing_min_plays_threshold = raw_max_play_count_overall * ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR
    
    # This is the play count for the X-axis limit, slightly more than max plays
    chart_xaxis_limit = raw_max_play_count_overall * 1.05 

    # This is the threshold for actually *displaying* the art on a bar in a given frame
    # It should be the same as art_processing_min_plays_threshold if we only want to show art that *could* be significant.
    art_display_min_plays_threshold = art_processing_min_plays_threshold


    print(f"Calculated Art Processing Threshold (min plays for a song to have its art processed): >={art_processing_min_plays_threshold:.2f}")
    print(f"Calculated Art Display Threshold (min plays for art to show on a bar): >={art_display_min_plays_threshold:.2f}")
    print(f"Chart X-axis limit: {chart_xaxis_limit:.2f}")

    # Pre-fetch art and colors, passing the calculated threshold
    # We need to import album_art_utils globally to access its loaded spotify_info_cache for canonical names
    global album_art_utils 
    import album_art_utils as aau_module # Import the module itself to access its globals
    album_art_utils = aau_module # Make it accessible in pre_fetch if needed for spotify_info_cache

    pre_fetch_album_art_and_colors(race_df, song_album_map_lastfm, unique_song_ids_in_race, art_processing_min_plays_threshold)
    
    # Retrieve canonical album names for songs that will be displayed
    # This map will store song_id -> canonical_album_name (from Spotify)
    song_id_to_canonical_album_map = {}
    for song_id in unique_song_ids_in_race:
        try:
            artist_name, track_name = song_id.split(" - ", 1)
            album_name_hint = song_album_map_lastfm.get(song_id, "")
            spotify_cache_key = f"spotify_{artist_name.lower().strip()}_{track_name.lower().strip()}_{album_name_hint.lower().strip()}"
            
            # Access the already loaded cache from album_art_utils module
            spotify_data = album_art_utils.spotify_info_cache.get(spotify_cache_key)
            if spotify_data and spotify_data.get("canonical_album_name"):
                song_id_to_canonical_album_map[song_id] = spotify_data["canonical_album_name"]
            else:
                song_id_to_canonical_album_map[song_id] = album_name_hint # Fallback to Last.fm name
        except ValueError:
            song_id_to_canonical_album_map[song_id] = song_album_map_lastfm.get(song_id, "Unknown Album")


    def draw_frame(frame_index):
        current_timestamp = race_df.index[frame_index]
        ax.clear()

        if (frame_index + 1) % 100 == 0 or frame_index == 0:
            print(f"Rendering frame {frame_index + 1}/{num_frames} ({current_timestamp.strftime('%Y-%m-%d %H:%M:%S')})...")

        current_data_slice = race_df.iloc[frame_index]
        # Get top N songs that have plays > 0
        top_n_songs = current_data_slice[current_data_slice > 0].nlargest(n_bars)
        
        # These are the song_ids that will actually get a bar, sorted for drawing bottom-up
        songs_to_draw = top_n_songs.sort_values(ascending=True)

        date_str = current_timestamp.strftime('%d %B %Y %H:%M:%S')
        ax.text(0.98, 0.05, date_str, transform=ax.transAxes,
                ha='right', va='bottom', fontsize=20 * (dpi/100.0), color='dimgray', weight='bold')

        ax.set_xlabel("Total Plays", fontsize=18 * (dpi/100.0), labelpad=15 * (dpi/100.0)) # Adjusted size and padding
        ax.set_xlim(0, chart_xaxis_limit)
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        ax.xaxis.set_ticks_position('top')
        ax.xaxis.set_label_position('top')
        tick_label_fontsize = 11 * (dpi/100.0)
        ax.tick_params(axis='x', labelsize=tick_label_fontsize)

        ax.set_ylim(-0.5, n_bars - 0.5) # n_bars slots from 0 to n_bars-1
        ax.set_yticks(np.arange(n_bars)) # Ticks at 0, 1, ..., n_bars-1
        
        y_tick_labels = [""] * n_bars # Initialize with empty strings
        
        # Prepare data for bars (values, colors, y_positions)
        bar_y_positions = []
        bar_widths = []
        bar_colors_list = []
        bar_song_ids = []

        # Iterate through the ranks (0 to n_bars-1 for y-axis)
        # songs_to_draw is sorted ascending, so its last element is #1
        for i, song_id in enumerate(songs_to_draw.index):
            rank_on_chart = len(songs_to_draw) - 1 - i # 0 for top bar, up to n_bars-1
            y_pos_for_bar = n_bars - 1 - rank_on_chart # maps to y-axis ticks (top bar is n_bars-1)
            
            bar_y_positions.append(y_pos_for_bar)
            bar_widths.append(songs_to_draw[song_id])
            bar_song_ids.append(song_id)

            # Get canonical album name for this song_id
            canonical_album = song_id_to_canonical_album_map.get(song_id, "Unknown Album")
            bar_colors_list.append(album_bar_colors.get(canonical_album, (0.5,0.5,0.5)))
            
            # Set y-tick label for this bar
            # Truncate song_id if too long for label
            max_char_len = int(50 * (150.0/dpi)) # Adjust char length based on DPI
            display_song_id = song_id
            if len(song_id) > max_char_len:
                display_song_id = song_id[:max_char_len-3] + "..."
            y_tick_labels[y_pos_for_bar] = display_song_id
            
        ax.set_yticklabels(y_tick_labels, fontsize=tick_label_fontsize) # Apply all labels at once

        if bar_y_positions: # If there are any songs to draw
            actual_bars = ax.barh(bar_y_positions, bar_widths, color=bar_colors_list, height=0.8, zorder=2)

            example_bar_height_data_units = 0.8 
            target_img_height_pixels = \
                (example_bar_height_data_units / n_bars) * \
                (fig.get_size_inches()[1] * dpi) * 0.35 

            value_label_fontsize = 12 * (dpi/100.0)
            # Padding for art and text relative to bar end, based on X-axis scale
            image_padding_data_units = chart_xaxis_limit * 0.005 # Tunable: space between art and bar end
            value_label_padding_data_units = chart_xaxis_limit * 0.008 # Tunable: space between text and (art or bar end)


            for i, bar_obj in enumerate(actual_bars):
                song_id_for_bar = bar_song_ids[i] # Get song_id for this bar
                current_play_count = bar_widths[i]
                
                canonical_album_for_bar = song_id_to_canonical_album_map.get(song_id_for_bar, "Unknown Album")
                pil_image = album_art_image_objects.get(canonical_album_for_bar)

                # --- Position for image and text, starting from end of bar and moving left ---
                current_x_anchor = bar_obj.get_width() # End of the bar

                # Add album art if conditions met
                if pil_image and current_play_count >= art_display_min_plays_threshold:
                    try:
                        img_orig_width, img_orig_height = pil_image.size
                        new_height_pixels = int(target_img_height_pixels)
                        new_width_pixels = 1
                        if img_orig_height > 0:
                            new_width_pixels = int(new_height_pixels * (img_orig_width / img_orig_height))
                        if new_width_pixels <= 0: new_width_pixels = int(new_height_pixels * 0.75) # Square-ish if bad ratio
                        if new_width_pixels <= 0: new_width_pixels = 1 

                        resized_pil_image = pil_image.resize((new_width_pixels, new_height_pixels), Image.Resampling.LANCZOS)
                        
                        fig_width_pixels = fig.get_size_inches()[0] * dpi
                        x_axis_range_data_units = ax.get_xlim()[1] - ax.get_xlim()[0] # chart_xaxis_limit
                        image_width_data_units = 0
                        if fig_width_pixels > 0 and x_axis_range_data_units > 0:
                             image_width_data_units = (new_width_pixels / fig_width_pixels) * x_axis_range_data_units
                        
                        # Position image: its right edge is at (current_x_anchor - image_padding_data_units)
                        # The AnnotationBbox xy is the center of the image.
                        img_center_x_pos = current_x_anchor - image_padding_data_units - (image_width_data_units / 2.0)
                        
                        # Check if image would go off-left of chart (into y-labels)
                        if img_center_x_pos - (image_width_data_units / 2.0) > chart_xaxis_limit * 0.02: # Ensure some space from y-axis
                            imagebox = OffsetImage(resized_pil_image, zoom=1.0, resample=False) # resample false as already resized
                            ab = AnnotationBbox(imagebox,
                                                (img_center_x_pos, bar_obj.get_y() + bar_obj.get_height() / 2.0),
                                                xybox=(0,0), xycoords='data', boxcoords="offset points",
                                                pad=0, frameon=False, zorder=3)
                            ax.add_artist(ab)
                            # Update current_x_anchor to be the left edge of the image
                            current_x_anchor = img_center_x_pos - (image_width_data_units / 2.0)
                        # else: image is too wide or bar too short, don't draw image to avoid y-label overlap

                    except Exception as e:
                        print(f"Error processing/adding image for {canonical_album_for_bar} (Song: {song_id_for_bar}): {e}")
                
                # Add play count text
                # Position text: its left edge is at (current_x_anchor + value_label_padding_data_units)
                # IF image was drawn, current_x_anchor is left of image.
                # IF NO image was drawn, current_x_anchor is end of bar.
                # So, we want text to be to the RIGHT of the bar end, or to the RIGHT of the image if image is on bar.
                # This logic needs refinement: text should always be to the RIGHT of the bar value.

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
        top_margin = 0.92 # Slightly adjusted for potentially taller X-axis label 
        
        try:
            fig.tight_layout(rect=[left_margin, bottom_margin, right_margin, top_margin])
            fig.align_labels() 
        except Exception as e_layout:
            if DEBUG_ALBUM_ART_LOGIC: print(f"Note: Layout adjustment warning/error: {e_layout}. Plot might not be perfectly aligned.")
            plt.subplots_adjust(left=left_margin, bottom=bottom_margin, right=right_margin, top=top_margin)


    ani = animation.FuncAnimation(fig, draw_frame, frames=num_frames,
                                  interval=interval, repeat=False)

    print(f"\nPreparing to save animation to {output_filename}...")
    
    writer_to_use = None
    if use_nvenc and animation.FFMpegWriter.isAvailable():
        print("Attempting to use NVENC (h264_nvenc) for hardware acceleration...")
        try:
            # Common NVENC args. Preset 'p6' (medium) is often a good balance. CQ for quality.
            # Full list of presets: p1 (fastest) to p7 (slowest, best quality)
            # Or older presets: default, slow, medium, fast, hq, ll, hp, bd etc.
            # Check your ffmpeg -h encoder=h264_nvenc
            # Using a constant quality mode ('-cq') is often preferred.
            nvenc_args = ['-preset', 'p6', '-tune', 'hq', '-b:v', '0', '-cq', '23', '-rc-lookahead', '20', '-pix_fmt', 'yuv420p']
            writer_nvenc = animation.FFMpegWriter(fps=target_fps_for_video, codec='h264_nvenc', bitrate=-1, extra_args=nvenc_args)
            
            # Test if nvenc is likely to work by trying to instantiate the writer (some checks happen here)
            # This isn't a foolproof check for codec availability but can catch some FFMpegWriter issues.
            _ = writer_nvenc.saving(fig, "test.mp4", dpi) # Minimal test, may not catch all codec issues
            writer_to_use = writer_nvenc
            print("NVENC writer initialized successfully.")
        except Exception as e_nvenc_init:
            print(f"WARNING: Could not initialize NVENC writer (h264_nvenc may not be supported by your ffmpeg build or driver): {e_nvenc_init}")
            print("Falling back to CPU encoder (libx264).")
            writer_to_use = None # Ensure it falls back

    if writer_to_use is None: # Fallback or CPU preference
        print("Using CPU encoder (libx264).")
        cpu_args = ['-crf', '23', '-preset', 'medium', '-pix_fmt', 'yuv420p']
        writer_to_use = animation.FFMpegWriter(fps=target_fps_for_video, codec='libx264', bitrate=-1, extra_args=cpu_args)

    try:
        ani.save(output_filename, writer=writer_to_use, dpi=dpi) 
        print(f"Animation successfully saved to {output_filename}")
    except FileNotFoundError:
        print("ERROR: ffmpeg not found. Please ensure ffmpeg is installed and in your system's PATH,")
        print("or plt.rcParams['animation.ffmpeg_path'] is set correctly.")
    except Exception as e:
        print(f"Error saving animation: {e}")
        print("If this was an NVENC attempt, try setting USE_NVENC_IF_AVAILABLE = False and re-run.")
    finally:
        plt.close(fig)


def main():
    if not animation.FFMpegWriter.isAvailable():
        print("CRITICAL WARNING: FFMpegWriter base class is not available from Matplotlib. MP4 output will likely fail.")
        print("This usually means ffmpeg itself is not found by Matplotlib.")
        print("Please install ffmpeg and ensure it is in your system's PATH,")
        print("or correctly set plt.rcParams['animation.ffmpeg_path'].")
        # return # Optionally exit early

    print("\n--------------------------------------------------------------------------------")
    print("  TIP: If you see UnicodeEncodeError in console, try setting PYTHONIOENCODING=utf-8.")
    print("  E.g., `set PYTHONIOENCODING=utf-8` (cmd) or `$env:PYTHONIOENCODING='utf-8'` (PowerShell)")
    print("--------------------------------------------------------------------------------")

    race_df, song_album_map_lastfm = run_data_pipeline()

    if race_df is None or race_df.empty:
        print("\nNo data available for animation. Please check your CSV file and data processing steps.")
        return

    print("\n--- Data ready for Animation ---")
    
    # For faster testing of animation rendering part:
    print(f"WARNING: Using a SUBSET of data for animation testing (first 300 frames).")
    test_race_df = race_df.head(300) 
    create_bar_chart_race_animation(test_race_df, song_album_map_lastfm, use_nvenc=USE_NVENC_IF_AVAILABLE)
    
    # Full run:
    # create_bar_chart_race_animation(race_df, song_album_map_lastfm, use_nvenc=USE_NVENC_IF_AVAILABLE)


if __name__ == "__main__":
    # This allows album_art_utils to be imported and its global caches to be accessed
    # if this script modifies them (though it shouldn't directly modify aau's internal caches).
    # Better to pass necessary data or access through functions if possible.
    # For now, pre_fetch_album_art_and_colors accesses album_art_utils.spotify_info_cache
    
    # This global import is a bit of a hack to make album_art_utils.spotify_info_cache
    # accessible within functions in this file after it's loaded by album_art_utils itself.
    # A cleaner way would be for album_art_utils to provide a function to get items from its cache.
    import album_art_utils as aau_module_global_access
    album_art_utils = aau_module_global_access
    
    main()