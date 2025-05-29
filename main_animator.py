# main_animator.py
import pandas as pd
from data_processor import clean_spotify_data, prepare_data_for_bar_chart_race, calculate_rolling_top_tracks # Added calculate_rolling_top_tracks
from album_art_utils import get_album_art_path, get_dominant_color 

import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image, ImageDraw, ImageFont # Added ImageDraw, ImageFont for text on PIL images if needed
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

DEBUG_ALBUM_ART_LOGIC = True 
ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR = 110.0 / 1750.0 
USE_NVENC_IF_AVAILABLE = True

PREFERRED_FONTS = [
    'DejaVu Sans', 'Noto Sans JP', 'Noto Sans KR', 'Noto Sans SC', 'Noto Sans TC', 
    'Arial Unicode MS', 'sans-serif' 
]
try:
    plt.rcParams['font.family'] = PREFERRED_FONTS
    # Attempt to find a common system font for the side panel text if specific ones aren't available
    # This is a very basic check; a more robust solution would iterate through a list.
    # For PIL text rendering, we might need to specify font paths directly.
    try:
        SIDE_PANEL_FONT_PATH = ImageFont.truetype("arial.ttf", size=int(28 * (VIDEO_DPI/100.0)))
    except IOError:
        try:
            SIDE_PANEL_FONT_PATH = ImageFont.truetype("DejaVuSans.ttf", size=int(28 * (VIDEO_DPI/100.0)))
        except IOError:
            SIDE_PANEL_FONT_PATH = ImageFont.load_default() # Fallback
            print("Warning: Arial/DejaVuSans font not found for side panel. Using default PIL font.")

except Exception as e:
    print(f"Warning: Could not set preferred fonts: {e}")
    SIDE_PANEL_FONT_PATH = ImageFont.load_default()


# --- Global Dictionaries for Caching Art Paths and Colors within the animator ---
album_art_image_objects = {} 
album_bar_colors = {}        
song_id_to_canonical_album_map = {} # Moved to global for access in pre_fetch and draw_frame

# Import album_art_utils module to access its loaded caches (like spotify_info_cache)
import album_art_utils as aau_module
album_art_utils = aau_module # Make it globally accessible in this file


def run_full_data_pipeline(): # Renamed to reflect it does more now
    print("--- Starting Full Data Processing Pipeline ---")
    csv_file_path = "lastfm_data.csv"
    if not os.path.exists(csv_file_path):
        print(f"Warning: '{csv_file_path}' not found. Creating dummy CSV.")
        # ... (dummy CSV creation logic - kept from previous version) ...
        dummy_data_list = []
        start_uts = 1704067200 # 01 Jan 2024 00:00:00
        for i in range(600): # More data for better rolling top test
            uts = start_uts + (i * 3600 * 2) # Play every 2 hours
            day_of_year = pd.to_datetime(uts, unit='s').dayofyear
            artist = f"Artist {(i % 10)}" 
            track = f"Song {(i % 7)}"   
            album = f"Album {(i % 5)}"
            if 0 <= day_of_year < 15: artist, track, album = "Artist Early", "Dominant Song Early", "Album Early"
            elif 15 <= day_of_year < 35: artist, track, album = "Artist Mid", "Popular Song Mid", "Album Mid"
            elif 35 <= day_of_year < 60: artist, track, album = "Artist Late", "Hit Song Late", "Album Late"
            utc_time_str = pd.to_datetime(uts, unit='s', utc=True).strftime("%d %b %Y, %H:%M:%S")
            dummy_data_list.append(f'{uts},"{utc_time_str}","{artist}","mbid_a","{album}","mbid_ax","{track}","mbid_s1"')
        dummy_csv_content = "uts,utc_time,artist,artist_mbid,album,album_mbid,track,track_mbid\n" + "\n".join(dummy_data_list)
        with open(csv_file_path, "w", encoding='utf-8') as f: f.write(dummy_csv_content)
        print(f"Created dummy '{csv_file_path}'.")

    print(f"\nStep 1: Cleaning data from '{csv_file_path}'...")
    cleaned_df = clean_spotify_data(csv_file_path)
    if cleaned_df is None or cleaned_df.empty: 
        print("Data cleaning resulted in no data. Exiting.")
        return None, {}, None # Added None for rolling_top_tracks_df
    print(f"Data cleaning successful. {len(cleaned_df)} relevant rows found.")
    
    print("\nStep 2: Preparing data for bar chart race...")
    # Ensure cleaned_df is sorted before passing if prepare_data expects it or doesn't sort itself
    cleaned_df_sorted = cleaned_df.sort_values(by='timestamp').copy()
    race_df, song_album_map_lastfm = prepare_data_for_bar_chart_race(cleaned_df_sorted)
    if race_df is None or race_df.empty: 
        print("Data preparation for race resulted in no data. Exiting.")
        return None, song_album_map_lastfm, None

    print("\nStep 3: Calculating rolling top tracks...")
    # Pass original cleaned_df (which has 'timestamp', 'artist', 'track' columns)
    # calculate_rolling_top_tracks handles internal sorting and indexing as needed
    rolling_top_tracks_df = calculate_rolling_top_tracks(cleaned_df, race_df.index)
    if rolling_top_tracks_df is None or rolling_top_tracks_df.empty:
        print("Rolling top tracks calculation resulted in no data. Continuing without side panels.")
        # Create an empty placeholder if needed by later code, or handle its absence
        rolling_top_tracks_df = pd.DataFrame(index=race_df.index) # Empty DF with same index

    print("--- Full Data Processing Pipeline Complete ---")
    return race_df, song_album_map_lastfm, rolling_top_tracks_df


def pre_fetch_album_art_and_colors(race_df, song_album_map_lastfm, rolling_top_tracks_df, global_visibility_threshold):
    print(f"\n--- Pre-fetching album art and dominant colors (Visibility Threshold: >={global_visibility_threshold:.2f} plays) ---")
    
    albums_processed_for_pil_and_color = set()
    processed_count = 0
    skipped_due_to_threshold = 0

    # Gather all unique song_ids that might need art
    unique_song_ids_to_consider = set(race_df.columns.tolist())
    if 'top_7_day_song_id' in rolling_top_tracks_df.columns:
        unique_song_ids_to_consider.update(rolling_top_tracks_df['top_7_day_song_id'].unique())
    if 'top_30_day_song_id' in rolling_top_tracks_df.columns:
        unique_song_ids_to_consider.update(rolling_top_tracks_df['top_30_day_song_id'].unique())
    
    # Remove "N/A" or None if they are present from rolling tracks
    unique_song_ids_to_consider.discard("N/A")
    unique_song_ids_to_consider.discard(None)

    print(f"Total unique song IDs to consider for art pre-fetch: {len(unique_song_ids_to_consider)}")

    for song_id in unique_song_ids_to_consider:
        if not isinstance(song_id, str) or " - " not in song_id: # Basic check for valid song_id format
            if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH DEBUG] Invalid or unparseable song_id '{song_id}'. Skipping.")
            continue
        try:
            artist_name, track_name = song_id.split(" - ", 1)
        except ValueError:
            if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH DEBUG] Could not parse artist/track from song_id: '{song_id}'. Skipping.")
            continue

        album_name_from_lastfm = song_album_map_lastfm.get(song_id)
        if not album_name_from_lastfm: # If song_id from rolling tops isn't in main map, need a fallback
            album_name_from_lastfm = track_name # Fallback: use track name as album hint
            if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH DEBUG] No album in song_album_map for '{song_id}'. Using track name '{track_name}' as album hint.")

        # Conditional processing based on play count (only for songs in race_df)
        # For songs *only* in rolling_tops, we might always want to fetch art if they appear.
        is_in_race_df = song_id in race_df.columns
        max_plays_for_this_song = race_df[song_id].max() if is_in_race_df else 0

        # Fetch art if:
        # 1. It's a song in the main race AND meets its play count threshold OR
        # 2. It's a song that appears as a rolling top track (assume we always want art for these if they show up)
        should_process_art = False
        if is_in_race_df and max_plays_for_this_song >= global_visibility_threshold:
            should_process_art = True
            if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH DEBUG] Song '{song_id}' (in race, max plays: {max_plays_for_this_song}) meets threshold. Processing.")
        elif not is_in_race_df and song_id in unique_song_ids_to_consider: # Song is from rolling tops, not main race
             should_process_art = True # Always try for rolling top songs
             if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH DEBUG] Song '{song_id}' (from rolling tops) will be processed.")
        
        if not should_process_art:
            if DEBUG_ALBUM_ART_LOGIC: print(f"[PRE-FETCH DEBUG] Song '{song_id}' (max plays: {max_plays_for_this_song}) does not meet criteria for art processing. Skipping.")
            skipped_due_to_threshold +=1 # Counting all skips here
            continue
        
        album_processing_key = f"{artist_name}_{album_name_from_lastfm}"
        if album_processing_key in albums_processed_for_pil_and_color:
            continue # Already loaded PIL/color for this combination this session
        
        # ... (print fetching message) ...
        try:
            print(f"Processing art/color for: Artist='{artist_name}', Track='{track_name}', Album (Hint)='{album_name_from_lastfm}'")
        except UnicodeEncodeError: # Handle non-ASCII characters in print
            safe_artist = artist_name.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            safe_track = track_name.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            safe_album_hint = album_name_from_lastfm.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            print(f"Processing art/color for: Artist='{safe_artist}', Track='{safe_track}', Album (Hint)='{safe_album_hint}'")

        art_path = get_album_art_path(artist_name, track_name, album_name_from_lastfm)
        
        canonical_album_name_for_caching = album_name_from_lastfm # Fallback
        spotify_cache_key = f"spotify_{artist_name.lower().strip()}_{track_name.lower().strip()}_{album_name_from_lastfm.lower().strip()}"
        spotify_data = album_art_utils.spotify_info_cache.get(spotify_cache_key)
        
        if spotify_data and spotify_data.get("canonical_album_name"):
            canonical_album_name_for_caching = spotify_data["canonical_album_name"]
        
        # Update global song_id_to_canonical_album_map
        song_id_to_canonical_album_map[song_id] = canonical_album_name_for_caching

        if art_path:
            if canonical_album_name_for_caching not in album_art_image_objects:
                try:
                    img = Image.open(art_path)
                    album_art_image_objects[canonical_album_name_for_caching] = img.copy()
                    img.close()
                except Exception as e:
                    album_art_image_objects[canonical_album_name_for_caching] = None
            if canonical_album_name_for_caching not in album_bar_colors:
                dc = get_dominant_color(art_path)
                album_bar_colors[canonical_album_name_for_caching] = (dc[0]/255.0, dc[1]/255.0, dc[2]/255.0)
        else:
            album_art_image_objects.setdefault(canonical_album_name_for_caching, None)
            album_bar_colors.setdefault(canonical_album_name_for_caching, (0.5, 0.5, 0.5))

        albums_processed_for_pil_and_color.add(album_processing_key)
        processed_count +=1
        
    print(f"--- Pre-fetching complete ---")
    print(f"Attempted to process art/color for {processed_count} song-album groups that met criteria.")
    # ... (other print statements)


def create_bar_chart_race_animation(race_df, song_album_map_lastfm, rolling_top_tracks_df, # Added rolling_top_tracks_df
                                    n_bars=N_BARS, output_filename=OUTPUT_FILENAME, interval=ANIMATION_INTERVAL,
                                    width=VIDEO_RESOLUTION_WIDTH, height=VIDEO_RESOLUTION_HEIGHT,
                                    dpi=VIDEO_DPI, use_nvenc=USE_NVENC_IF_AVAILABLE):
    if race_df is None or race_df.empty: # ... (checks remain) ...
        print("Cannot create animation: race_df is empty or None.")
        return

    num_frames = len(race_df.index)
    target_fps_for_video = 1000.0 / interval
    # ... (print statements for config) ...

    # --- Figure and Axes Setup ---
    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    
    # Define layout: [left, bottom, width, height] in figure normalized coords (0-1)
    # Left panel for rolling tops: 20% width
    # Main race chart: 75% width, with some padding
    # Gaps: 5% total horizontal
    
    left_panel_width = 0.22
    main_chart_width = 0.73 # Adjusted to fit
    gap = (1.0 - left_panel_width - main_chart_width) / 2 # Small gap

    # Axes for 30-day top track (top-left)
    ax_top30_art = fig.add_axes([0.02, 0.65, left_panel_width * 0.8, left_panel_width * 0.8]) # Square for art
    ax_top30_text = fig.add_axes([0.02, 0.58, left_panel_width * 0.8, 0.06]) # For text below art
    
    # Axes for 7-day top track (bottom-left)
    ax_top7_art = fig.add_axes([0.02, 0.25, left_panel_width * 0.8, left_panel_width * 0.8]) # Square for art
    ax_top7_text = fig.add_axes([0.02, 0.18, left_panel_width * 0.8, 0.06]) # For text below art

    # Main race chart axes
    ax_race = fig.add_axes([left_panel_width + gap, 0.08, main_chart_width, 0.87]) # y:0.08, h:0.87 to use vertical space

    for ax_side in [ax_top30_art, ax_top30_text, ax_top7_art, ax_top7_text]:
        ax_side.axis('off') # Turn off spines and ticks for side panel axes

    # --- End Figure and Axes Setup ---

    raw_max_play_count_overall = race_df.max().max()
    if pd.isna(raw_max_play_count_overall) or raw_max_play_count_overall <= 0: raw_max_play_count_overall = 100
    art_processing_min_plays_threshold = raw_max_play_count_overall * ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR
    chart_xaxis_limit = raw_max_play_count_overall * 1.05 
    art_display_min_plays_threshold = art_processing_min_plays_threshold

    pre_fetch_album_art_and_colors(race_df, song_album_map_lastfm, rolling_top_tracks_df, art_processing_min_plays_threshold)
    
    # song_id_to_canonical_album_map is now global and populated by pre_fetch

    def draw_frame(frame_index):
        current_timestamp = race_df.index[frame_index]
        
        # Clear main race axes
        ax_race.clear()
        # Clear side panel text axes (art axes will be overwritten by imshow)
        ax_top30_text.clear()
        ax_top7_text.clear()
        ax_top30_art.clear() # Clear art axes too to prevent old art if new one is None
        
        for ax_side in [ax_top30_art, ax_top30_text, ax_top7_art, ax_top7_text]: # Re-hide axes after clear
            ax_side.axis('off')


        if (frame_index + 1) % 5 == 0 or frame_index == 0:
            print(f"Rendering frame {frame_index + 1}/{num_frames} ({current_timestamp.strftime('%Y-%m-%d %H:%M:%S')})...")

        # --- Draw Main Bar Chart Race on ax_race ---
        current_data_slice = race_df.iloc[frame_index]
        top_n_songs = current_data_slice[current_data_slice > 0].nlargest(n_bars)
        songs_to_draw = top_n_songs.sort_values(ascending=True)

        date_str = current_timestamp.strftime('%d %B %Y %H:%M:%S')
        # Position date on the main race chart area (ax_race)
        ax_race.text(0.98, 0.02, date_str, transform=ax_race.transAxes, #transform to ax_race
                     ha='right', va='bottom', fontsize=20 * (dpi/100.0), color='dimgray', weight='bold')

        ax_race.set_xlabel("Total Plays", fontsize=18 * (dpi/100.0), labelpad=15 * (dpi/100.0))
        ax_race.set_xlim(0, chart_xaxis_limit)
        ax_race.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        ax_race.xaxis.set_ticks_position('top')
        ax_race.xaxis.set_label_position('top')
        tick_label_fontsize = 11 * (dpi/100.0)
        ax_race.tick_params(axis='x', labelsize=tick_label_fontsize)
        ax_race.set_ylim(-0.5, n_bars - 0.5)
        ax_race.set_yticks(np.arange(n_bars))
        
        y_tick_labels = [""] * n_bars
        bar_y_positions, bar_widths, bar_colors_list, bar_song_ids = [], [], [], []

        for i, song_id in enumerate(songs_to_draw.index):
            rank_on_chart = len(songs_to_draw) - 1 - i
            y_pos_for_bar = n_bars - 1 - rank_on_chart
            bar_y_positions.append(y_pos_for_bar)
            bar_widths.append(songs_to_draw[song_id])
            bar_song_ids.append(song_id)
            canonical_album = song_id_to_canonical_album_map.get(song_id, "Unknown Album")
            bar_colors_list.append(album_bar_colors.get(canonical_album, (0.5,0.5,0.5)))
            max_char_len = int(45 * (150.0/dpi) * (main_chart_width / 0.75)) # Adjust for narrower chart
            display_song_id = song_id
            if len(song_id) > max_char_len: display_song_id = song_id[:max_char_len-3] + "..."
            y_tick_labels[y_pos_for_bar] = display_song_id
            
        ax_race.set_yticklabels(y_tick_labels, fontsize=tick_label_fontsize)

        if bar_y_positions:
            actual_bars = ax_race.barh(bar_y_positions, bar_widths, color=bar_colors_list, height=0.8, zorder=2)
            
            example_bar_height_data_units = 0.8 
            target_img_height_pixels_main_chart = \
                (example_bar_height_data_units / n_bars) * \
                (ax_race.get_window_extent().height) * 0.35 

            value_label_fontsize = 12 * (dpi/100.0)
            image_padding_data_units = chart_xaxis_limit * 0.005 
            value_label_padding_data_units = chart_xaxis_limit * 0.008 

            for i, bar_obj in enumerate(actual_bars):
                song_id_for_bar = bar_song_ids[i] 
                current_play_count = bar_widths[i]
                
                canonical_album_for_bar = song_id_to_canonical_album_map.get(song_id_for_bar, "Unknown Album")
                
                pil_image = None # <--- Initialize pil_image to None here
                if canonical_album_for_bar != "Unknown Album": # Only try to get if album is known
                    pil_image = album_art_image_objects.get(canonical_album_for_bar)

                # current_x_anchor should be defined regardless of image, start at bar end
                # This variable was only used if an image was drawn, let's ensure it's always set
                # Actually, current_x_anchor was used to determine image placement,
                # and then updated. The text positioning is simpler: relative to bar_obj.get_width().

                if pil_image is not None and current_play_count >= art_display_min_plays_threshold:
                    try:
                        img_orig_width, img_orig_height = pil_image.size
                        new_height_pixels = int(target_img_height_pixels_main_chart)
                        new_width_pixels = 1
                        if img_orig_height > 0: new_width_pixels = int(new_height_pixels * (img_orig_width / img_orig_height))
                        if new_width_pixels <= 0: new_width_pixels = int(new_height_pixels * 0.75)
                        if new_width_pixels <= 0: new_width_pixels = 1 
                        resized_pil_image = pil_image.resize((new_width_pixels, new_height_pixels), Image.Resampling.LANCZOS)
                        
                        fig_width_pixels_race_ax = ax_race.get_window_extent().width
                        x_axis_range_data_units = ax_race.get_xlim()[1] - ax_race.get_xlim()[0]
                        image_width_data_units = 0
                        if fig_width_pixels_race_ax > 0 and x_axis_range_data_units > 0:
                             image_width_data_units = (new_width_pixels / fig_width_pixels_race_ax) * x_axis_range_data_units
                        
                        # Position image so its right edge is (bar_obj.get_width() - image_padding_data_units)
                        img_center_x_pos = bar_obj.get_width() - image_padding_data_units - (image_width_data_units / 2.0)
                        
                        if img_center_x_pos - (image_width_data_units / 2.0) > chart_xaxis_limit * 0.02: # Check against left boundary
                            imagebox = OffsetImage(resized_pil_image, zoom=1.0, resample=False)
                            ab = AnnotationBbox(imagebox,
                                                (img_center_x_pos, bar_obj.get_y() + bar_obj.get_height() / 2.0),
                                                xybox=(0,0), xycoords='data', boxcoords="offset points",
                                                pad=0, frameon=False, zorder=3) 
                            ax_race.add_artist(ab)
                            # The image is on the bar, no need to update current_x_anchor for text here
                            # Text will always be to the right of the bar value.
                    except Exception as e: 
                        print(f"Error processing/adding image for bar {canonical_album_for_bar} (Song: {song_id_for_bar}): {e}")
                
                # Text always to the right of the bar end
                text_x_pos = bar_obj.get_width() + value_label_padding_data_units
                ax_race.text(text_x_pos,
                        bar_obj.get_y() + bar_obj.get_height() / 2.0,
                        f'{int(current_play_count)}',
                        va='center', ha='left', fontsize=value_label_fontsize, weight='bold', zorder=4)

        ax_race.spines['right'].set_visible(False)
        ax_race.spines['bottom'].set_visible(False)
        ax_race.spines['left'].set_linewidth(1.5 * (dpi/100.0))
        # --- End Main Bar Chart Race ---

        # --- Draw Rolling Top Tracks ---
        if rolling_top_tracks_df is not None and not rolling_top_tracks_df.empty and current_timestamp in rolling_top_tracks_df.index:
            current_rolling_data = rolling_top_tracks_df.loc[current_timestamp]
            
            # 30-Day
            top_30_song = current_rolling_data.get('top_30_day_song_id', "N/A")
            top_30_plays = current_rolling_data.get('top_30_day_plays', 0)
            if top_30_song != "N/A":
                album_30 = song_id_to_canonical_album_map.get(top_30_song)
                pil_img_30 = album_art_image_objects.get(album_30)
                if pil_img_30:
                    ax_top30_art.imshow(pil_img_30)
                ax_top30_text.text(0.5, 0.9, "Top Track - Last 30 Days", ha='center', va='top', fontsize=11*(dpi/100), weight='bold', wrap=True)
                ax_top30_text.text(0.5, 0.5, f"{top_30_song}", ha='center', va='top', fontsize=10*(dpi/100), wrap=True)
                ax_top30_text.text(0.5, 0.1, f"({top_30_plays} plays)", ha='center', va='top', fontsize=9*(dpi/100), wrap=True)

            # 7-Day
            top_7_song = current_rolling_data.get('top_7_day_song_id', "N/A")
            top_7_plays = current_rolling_data.get('top_7_day_plays', 0)
            if top_7_song != "N/A":
                album_7 = song_id_to_canonical_album_map.get(top_7_song)
                pil_img_7 = album_art_image_objects.get(album_7)
                if pil_img_7:
                    ax_top7_art.imshow(pil_img_7)
                ax_top7_text.text(0.5, 0.9, "Top Track - Last 7 Days", ha='center', va='top', fontsize=11*(dpi/100), weight='bold', wrap=True)
                ax_top7_text.text(0.5, 0.5, f"{top_7_song}", ha='center', va='top', fontsize=10*(dpi/100), wrap=True)
                ax_top7_text.text(0.5, 0.1, f"({top_7_plays} plays)", ha='center', va='top', fontsize=9*(dpi/100), wrap=True)
        # --- End Rolling Top Tracks ---
        
        # Overall figure adjustments (tight_layout might be tricky with add_axes)
        # fig.tight_layout() # Often conflicts with add_axes. Manual adjustments are better.
        # plt.subplots_adjust can be used if not using add_axes for everything.
        # For add_axes, the positions are absolute, so less need for tight_layout on the fig.

    # ... (Animation creation and saving logic - largely unchanged, ensure target_fps_for_video is used) ...
    ani = animation.FuncAnimation(fig, draw_frame, frames=num_frames,
                                  interval=interval, repeat=False)
    print(f"\nPreparing to save animation to {output_filename}...")
    # ... (rest of saving logic as before) ...
    writer_to_use = None
    if use_nvenc and animation.FFMpegWriter.isAvailable():
        print("Attempting to use NVENC (h264_nvenc) for hardware acceleration...")
        try:
            nvenc_args = ['-preset', 'p6', '-tune', 'hq', '-b:v', '0', '-cq', '23', '-rc-lookahead', '20', '-pix_fmt', 'yuv420p']
            writer_nvenc = animation.FFMpegWriter(fps=target_fps_for_video, codec='h264_nvenc', bitrate=-1, extra_args=nvenc_args)
            _ = writer_nvenc.saving(fig, "test.mp4", dpi) 
            writer_to_use = writer_nvenc
            print("NVENC writer initialized successfully.")
        except Exception as e_nvenc_init:
            print(f"WARNING: Could not initialize NVENC writer: {e_nvenc_init}")
            print("Falling back to CPU encoder (libx264).")
            writer_to_use = None 

    if writer_to_use is None: 
        print("Using CPU encoder (libx264).")
        cpu_args = ['-crf', '23', '-preset', 'medium', '-pix_fmt', 'yuv420p']
        writer_to_use = animation.FFMpegWriter(fps=target_fps_for_video, codec='libx264', bitrate=-1, extra_args=cpu_args)

    try:
        ani.save(output_filename, writer=writer_to_use, dpi=dpi) 
        print(f"Animation successfully saved to {output_filename}")
    except FileNotFoundError: print("ERROR: ffmpeg not found...")
    except Exception as e: print(f"Error saving animation: {e}")
    finally: plt.close(fig)


def main():
    # ... (FFMpegWriter check and PYTHONIOENCODING tip remain) ...
    if not animation.FFMpegWriter.isAvailable():
        print("CRITICAL WARNING: FFMpegWriter base class is not available from Matplotlib...")
    print("\n--------------------------------------------------------------------------------")
    print("  TIP: If you see UnicodeEncodeError in console, try setting PYTHONIOENCODING=utf-8.")
    print("--------------------------------------------------------------------------------")


    race_df, song_album_map_lastfm, rolling_top_tracks_df = run_full_data_pipeline() # Updated call

    if race_df is None or race_df.empty:
        print("\nNo data available for animation. Please check your CSV file and data processing steps.")
        return

    print("\n--- Data ready for Animation (including rolling tops) ---")
    if rolling_top_tracks_df is not None and not rolling_top_tracks_df.empty:
        print(f"Rolling top tracks DF shape: {rolling_top_tracks_df.shape}")
    else:
        print("Rolling top tracks DF is empty or None.")
    
    # For faster testing:
    test_frames = 100
    print(f"WARNING: Using a SUBSET of data for animation testing (first {test_frames} frames).")
    test_race_df = race_df.head(test_frames) 
    test_rolling_df = rolling_top_tracks_df.head(test_frames) if rolling_top_tracks_df is not None else None
    create_bar_chart_race_animation(test_race_df, song_album_map_lastfm, test_rolling_df, use_nvenc=USE_NVENC_IF_AVAILABLE)
    
    # Full run:
    # create_bar_chart_race_animation(race_df, song_album_map_lastfm, rolling_top_tracks_df, use_nvenc=USE_NVENC_IF_AVAILABLE)

if __name__ == "__main__":
    main()