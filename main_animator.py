# main_animator.py
import pandas as pd
from data_processor import clean_spotify_data, prepare_data_for_bar_chart_race
from album_art_utils import get_album_art_path, get_dominant_color

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import os # For checking ffmpeg path
import sys # To access sys.stdout for more robust printing

# --- Configuration for Animation ---
N_BARS = 10  # Number of bars to display
TARGET_FPS = 30 # Desired frames per second for the output video
ANIMATION_INTERVAL = 1000 / TARGET_FPS # Milliseconds between frames

OUTPUT_FILENAME = "spotify_top_songs_2024_4k.mp4"
VIDEO_RESOLUTION_WIDTH = 3840
VIDEO_RESOLUTION_HEIGHT = 2160
VIDEO_DPI = 165 # Dots Per Inch for the plot rendering, affects text size relative to plot

DEBUG_CACHE = True

# --- FFmpeg Configuration ---
# Option 1: Ensure ffmpeg is in your system's PATH. This is preferred.
# Option 2: Explicitly set the path to ffmpeg executable if not in PATH.
#           Uncomment and set the correct path below if needed.
# plt.rcParams['animation.ffmpeg_path'] = r'C:\path\to\your\ffmpeg.exe' # Example for Windows
# plt.rcParams['animation.ffmpeg_path'] = '/usr/local/bin/ffmpeg' # Example for macOS/Linux


PREFERRED_FONTS = [
    'DejaVu Sans', 
    'Noto Sans JP', 'Noto Sans KR', 'Noto Sans SC', 'Noto Sans TC', # Noto CJK fonts
    'Arial Unicode MS', # Often available on Windows if Office is installed
    'sans-serif' # Generic fallback
]
plt.rcParams['font.family'] = PREFERRED_FONTS


# --- Global Dictionaries for Caching Art Paths and Colors within the animator ---
# This is for the duration of one run, complementing the file cache in album_art_utils
album_art_image_objects = {} # Cache loaded PIL.Image objects for art
album_bar_colors = {} # Cache {album_name: color_tuple}


def run_data_pipeline():
    """
    Runs the full data processing pipeline: cleaning and preparation for the race.
    Returns the race-ready DataFrame and the song-to-album map.
    """
    print("--- Starting Data Processing Pipeline ---")
    csv_file_path = "lastfm_data.csv"
    print(f"\nStep 1: Cleaning data from '{csv_file_path}'...")
    cleaned_df = clean_spotify_data(csv_file_path)
    if cleaned_df is None: return None, {}
    if cleaned_df.empty: return pd.DataFrame(), {}
    print(f"Data cleaning successful. {len(cleaned_df)} relevant rows found.")
    print("\nStep 2: Preparing data for bar chart race (high-resolution timestamps)...")
    race_df, song_album_map = prepare_data_for_bar_chart_race(cleaned_df)
    if race_df is None: return None, song_album_map
    if race_df.empty and not song_album_map: return pd.DataFrame(), {}
    print("Data preparation successful.")
    print(f"Race DataFrame shape: {race_df.shape} (Play Events, Unique Songs)")
    print(f"Number of entries in song_album_map: {len(song_album_map)}")
    print("--- Data Processing Pipeline Complete ---")
    return race_df, song_album_map


def pre_fetch_album_art_and_colors(race_df, song_album_map, unique_song_ids_in_race, fetch_threshold=50):
    """
    Iterate through albums to fetch art and dominant colors.
    Optimized to fetch more selectively.

    Args:
        race_df (pd.DataFrame): The main data frame for the race.
        song_album_map (dict): Maps song_id to album_name.
        unique_song_ids_in_race (list): List of all song_ids present in race_df columns.
        fetch_threshold (int): Minimum max play count for a song (after Jan) to fetch its art.
    """
    print("\n--- Pre-fetching album art and dominant colors (optimized) ---")
    albums_processed = set()

    # Get max play count for each song across the entire race_df period
    max_plays_per_song = race_df.max() # This is a Series: index=song_id, value=max_plays

    # Identify songs played in January (first month, assuming 2024 data)
    # Get timestamps for January
    january_timestamps = [ts for ts in race_df.index if ts.month == 1]
    songs_played_in_january = set()
    if january_timestamps:
        # Consider songs that had any play in January
        # race_df.loc[january_timestamps] gives rows for Jan.
        # .any() checks if any value in a column is > 0 for those rows.
        january_plays_df = race_df.loc[january_timestamps]
        for song_id in unique_song_ids_in_race:
            if song_id in january_plays_df.columns and (january_plays_df[song_id] > 0).any():
                songs_played_in_january.add(song_id)
    
    print(f"Identified {len(songs_played_in_january)} unique songs played in January.")

    for song_id in unique_song_ids_in_race:
        album_name = song_album_map.get(song_id)
        if not album_name:
            continue

        # --- Optimization Logic ---
        should_fetch = False
        if song_id in songs_played_in_january:
            should_fetch = True
            if DEBUG_CACHE: print(f"[PRE-FETCH DEBUG] Song '{song_id}' played in Jan, will fetch art.")
        elif song_id in max_plays_per_song and max_plays_per_song[song_id] >= fetch_threshold:
            should_fetch = True
            if DEBUG_CACHE: print(f"[PRE-FETCH DEBUG] Song '{song_id}' max plays ({max_plays_per_song[song_id]}) >= threshold ({fetch_threshold}), will fetch art.")
        else:
            if DEBUG_CACHE:
                max_p = max_plays_per_song.get(song_id, 0)
                print(f"[PRE-FETCH DEBUG] Song '{song_id}' max plays ({max_p}) < threshold ({fetch_threshold}) and not in Jan. Skipping art fetch for now.")
        
        if not should_fetch:
            continue
        # --- End Optimization Logic ---

        try:
            artist_name = song_id.split(" - ", 1)[0]
        except:
            artist_name = "Unknown Artist"
            print(f"WARNING: Could not parse artist from song_id: '{song_id}'. Using 'Unknown Artist'.")

        album_key = f"{artist_name}_{album_name}"
        if album_key in albums_processed:
            continue
        
        # Robust printing for console output with Unicode
        try:
            print(f"Fetching art/color for: '{artist_name}' - '{album_name}'")
        except UnicodeEncodeError:
            print(f"Fetching art/color for: '{artist_name.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)}' - '{album_name.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)}'")

        art_path = get_album_art_path(artist_name, album_name)
        
        if art_path:
            if album_name not in album_art_image_objects or album_art_image_objects[album_name] is None:
                try:
                    img = Image.open(art_path)
                    album_art_image_objects[album_name] = img.copy()
                    img.close()
                except Exception as e:
                    print(f"Error loading image {art_path} for animator: {e}. Defaulting to None.")
                    album_art_image_objects[album_name] = None
            
            if album_name not in album_bar_colors:
                dc = get_dominant_color(art_path)
                album_bar_colors[album_name] = (dc[0]/255, dc[1]/255, dc[2]/255)
        else:
            album_art_image_objects[album_name] = None
            if album_name not in album_bar_colors:
                album_bar_colors[album_name] = (0.5, 0.5, 0.5)
        
        albums_processed.add(album_key)
        
    print(f"--- Pre-fetching complete (processed {len(albums_processed)} unique albums based on criteria) ---")


def create_bar_chart_race_animation(race_df, song_album_map, n_bars=N_BARS,
                                    output_filename=OUTPUT_FILENAME, interval=ANIMATION_INTERVAL,
                                    width=VIDEO_RESOLUTION_WIDTH, height=VIDEO_RESOLUTION_HEIGHT,
                                    dpi=VIDEO_DPI):
    if race_df is None or race_df.empty:
        print("Cannot create animation: race_df is empty or None.")
        return

    num_frames = len(race_df.index)
    print(f"\n--- Starting Animation Creation for {output_filename} ---")
    # ... (print messages) ...

    # --- Define fig and ax HERE ---
    figsize_w = width / dpi
    figsize_h = height / dpi
    fig, ax = plt.subplots(figsize=(figsize_w, figsize_h), dpi=dpi)
    # --- End definition ---

    unique_song_ids_in_race = race_df.columns.tolist()
    pre_fetch_album_art_and_colors(race_df, song_album_map, unique_song_ids_in_race)
    
    max_play_count = race_df.max().max() * 1.05 
    if pd.isna(max_play_count) or max_play_count <=0 : max_play_count = 100


    def draw_frame(frame_index):
        # ... (progress printout, current_timestamp, ax.clear()) ...

        current_timestamp = race_df.index[frame_index] # Define current_timestamp here
        ax.clear() # It's good practice to clear the axes at the start of each frame draw

        if (frame_index + 1) % 100 == 0:
            print(f"Rendered frame {frame_index + 1}/{num_frames}...")

        current_data = race_df.iloc[frame_index]
        top_n_data = current_data.nlargest(n_bars)
        songs_with_plays = top_n_data[top_n_data > 0].sort_values(ascending=True)
        potential_top_n_song_ids = top_n_data.index.tolist()

        # --- Title and Time Counter ---
        # ax.set_title("My Spotify Top Songs 2024", fontsize=22 * (dpi/100), pad=20* (dpi/100), weight='bold') # Title removed
        date_str = current_timestamp.strftime('%d %B %Y %H:%M:%S')
        ax.text(0.98, 0.05, date_str, transform=ax.transAxes,
                ha='right', va='bottom', fontsize=20* (dpi/100), color='dimgray', weight='bold')

        # --- X-axis setup ---
        ax.set_xlabel("Total Plays", fontsize=16* (dpi/100))
        ax.set_xlim(0, max_play_count)
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        ax.xaxis.set_ticks_position('top')
        ax.xaxis.set_label_position('top')
        tick_label_fontsize = 11 * (dpi/100)
        ax.tick_params(axis='x', labelsize=tick_label_fontsize)

        # --- Y-axis setup for N_BARS slots ---
        ax.set_ylim(-0.5, n_bars - 0.5)
        ax.set_yticks(np.arange(n_bars))
        
        display_slot_labels = [""] * n_bars
        max_char_len = int(50 * (150/dpi))
        for i in range(n_bars):
            if i < len(potential_top_n_song_ids):
                song_title = potential_top_n_song_ids[i]
                if len(song_title) > max_char_len:
                    display_slot_labels[n_bars - 1 - i] = song_title[:max_char_len-3] + "..."
                else:
                    display_slot_labels[n_bars - 1 - i] = song_title
            # else: display_slot_labels[n_bars - 1 - i] remains ""
        ax.set_yticklabels(display_slot_labels, fontsize=tick_label_fontsize)

        if songs_with_plays.empty:
            pass # Axes and title are set, no bars to draw
        else:
            y_positions_for_actual_bars = []
            values_for_actual_bars = []
            colors_for_actual_bars = []
            song_ids_for_actual_bars = []

            for rank, song_id in enumerate(potential_top_n_song_ids):
                if rank < n_bars and song_id in songs_with_plays.index:
                    y_pos = n_bars - 1 - rank
                    y_positions_for_actual_bars.append(y_pos)
                    values_for_actual_bars.append(songs_with_plays[song_id])
                    album_name = song_album_map.get(song_id)
                    if album_name and album_name in album_bar_colors:
                        colors_for_actual_bars.append(album_bar_colors[album_name])
                    else:
                        colors_for_actual_bars.append((0.5,0.5,0.5))
                    song_ids_for_actual_bars.append(song_id)

            if y_positions_for_actual_bars:
                bars = ax.barh(y_positions_for_actual_bars, values_for_actual_bars, 
                               color=colors_for_actual_bars, height=0.8)

                # --- Calculate target image height pixels HERE, now that ax and fig are fully set up for the frame ---
                example_bar_height_data_units = 0.8 # from barh height parameter
                # y_axis_data_range is n_bars (because of set_ylim)
                # fig.get_size_inches()[1] is figure height in inches
                target_img_height_pixels = \
                    (example_bar_height_data_units / n_bars) * \
                    (fig.get_size_inches()[1] * dpi) * 0.35 # Target ~35% of bar height

                value_label_fontsize = 12 * (dpi/100)
                image_padding_data_units = max_play_count * 0.010
                value_label_padding_data_units = max_play_count * 0.035

                for i, bar_obj in enumerate(bars):
                    song_id_for_bar = song_ids_for_actual_bars[i]
                    album_name_for_bar = song_album_map.get(song_id_for_bar)
                    bar_width_data_units = bar_obj.get_width()
                    
                    pil_image = album_art_image_objects.get(album_name_for_bar) if album_name_for_bar else None

                    current_x_pos = bar_width_data_units

                    # Only show album art if available AND play count is 8 or more
                    if pil_image and values_for_actual_bars[i] >= 110:
                        try:
                            img_orig_width, img_orig_height = pil_image.size
                            new_height_pixels = int(target_img_height_pixels)
                            new_width_pixels = 1
                            if img_orig_height > 0:
                                new_width_pixels = int(new_height_pixels * (img_orig_width / img_orig_height))
                            if new_width_pixels <= 0: new_width_pixels = int(new_height_pixels * 0.75)
                            if new_width_pixels <=0 : new_width_pixels = 1 # Final fallback

                            resized_pil_image = pil_image.resize((new_width_pixels, new_height_pixels), Image.Resampling.LANCZOS)
                            imagebox = OffsetImage(resized_pil_image, zoom=1.0)

                            fig_width_pixels = fig.get_size_inches()[0] * dpi
                            x_axis_range_data_units = ax.get_xlim()[1] - ax.get_xlim()[0]
                            image_width_data_units = 0
                            if fig_width_pixels > 0 and x_axis_range_data_units > 0:
                                 image_width_data_units = (new_width_pixels / fig_width_pixels) * x_axis_range_data_units
                            
                            # Position image so its right edge is slightly to the left of the bar's end
                            img_display_x_pos = current_x_pos - (image_width_data_units / 2) - (image_padding_data_units * 2.0)
                            
                            ab = AnnotationBbox(imagebox,
                                                (img_display_x_pos, bar_obj.get_y() + bar_obj.get_height() / 2),
                                                xybox=(0,0), xycoords='data', boxcoords="offset points",
                                                pad=0, frameon=False)
                            ax.add_artist(ab)
                            current_x_pos = img_display_x_pos + (image_width_data_units / 2)
                        except Exception as e:
                            print(f"Error adding image for {album_name_for_bar}: {e}")
                    
                    ax.text(current_x_pos + value_label_padding_data_units,
                            bar_obj.get_y() + bar_obj.get_height() / 2,
                            f'{int(values_for_actual_bars[i])}',
                            va='center', ha='left', fontsize=value_label_fontsize, weight='bold')

        # --- Spines ---
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_linewidth(1.5 * (dpi/100))
        
        # --- Layout Adjustments ---
        left_margin = 0.08 # Reduced further from 0.15
        right_margin = 0.90 # Increased slightly from 0.88
        bottom_margin = 0.10
        top_margin = 0.95 # Increased from 0.90 to use space from removed title
        
        try:
            fig.align_labels() 
        except AttributeError: pass
            
        try:
            # Using plt.tight_layout() might be better than fig.tight_layout() if fig.align_labels() isn't used or available
            plt.tight_layout(rect=[left_margin, bottom_margin, right_margin, top_margin]) 
        except UserWarning:
            print("Caught UserWarning from tight_layout. Trying plt.subplots_adjust...")
            plt.subplots_adjust(left=left_margin, bottom=bottom_margin, right=right_margin, top=top_margin, wspace=0.2, hspace=0.2)
        except Exception as e:
            print(f"Error during layout adjustment: {e}")

    # --- Create Animation ---
    ani = animation.FuncAnimation(fig, draw_frame, frames=num_frames,
                                  interval=interval, repeat=False)

    # --- Save Animation (MP4 using explicit FFMpegWriter) ---
    # ... (saving logic remains the same) ...
    print(f"Preparing to save animation to {output_filename} using FFMpegWriter...")
    # ... (rest of saving logic) ...
    try:
        ffmpeg_writer = animation.FFMpegWriter(fps=1000 / interval, codec='libx264', bitrate=-1, extra_args=['-crf', '23', '-preset', 'medium', '-pix_fmt', 'yuv420p'])
        ani.save(output_filename, writer=ffmpeg_writer, dpi=dpi) 
        print(f"Animation successfully saved to {output_filename}")
    except FileNotFoundError: print("ERROR: ffmpeg not found...")
    except Exception as e: print(f"Error saving animation: {e}")
    finally: plt.close(fig)


def main():
    if not animation.FFMpegWriter.isAvailable():
        print("CRITICAL WARNING: FFMpegWriter is not available. MP4 output will fail.")
        print("Please install ffmpeg and ensure it is in your system's PATH,")
        print("or correctly set plt.rcParams['animation.ffmpeg_path'] at the top of this script.")

    print("\n--------------------------------------------------------------------------------")
    print("  TIP: If you see UnicodeEncodeError, set PYTHONIOENCODING=utf-8 in your terminal.")
    print("  E.g., `set PYTHONIOENCODING=utf-8` (cmd) or `$env:PYTHONIOENCODING='utf-8'` (powershell)")
    print("--------------------------------------------------------------------------------")

    race_df, song_album_map = run_data_pipeline()

    if race_df is None or race_df.empty:
        print("\nNo data available for animation. Please check your CSV file and data ranges.")
        return

    print("\n--- Data ready for High-Resolution Animation ---")
    
    # ---- For faster testing: Uncomment and adjust the slice as needed ----
    # print(f"WARNING: Running with a SUBSET of data for testing. Full render will take longer.")
    # test_race_df = race_df.head(500) # Process only the first 500 play events for testing
    # create_bar_chart_race_animation(test_race_df, song_album_map)
    # ---------------------------------------------

    # Full run (uncomment this line for the full animation after testing)
    create_bar_chart_race_animation(race_df, song_album_map)


if __name__ == "__main__":
    main()