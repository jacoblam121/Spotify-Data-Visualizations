# main_animator.py
import pandas as pd
from data_processor import clean_spotify_data, prepare_data_for_bar_chart_race

import matplotlib
# matplotlib.use('Agg') # Optional: Use a non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.ticker as ticker
import numpy as np
import os # For checking ffmpeg path

# --- Configuration for Animation ---
N_BARS = 10
TARGET_FPS = 30
ANIMATION_INTERVAL = 1000 / TARGET_FPS

OUTPUT_FILENAME = "spotify_top_songs_2024_4k.mp4"
VIDEO_RESOLUTION_WIDTH = 3840
VIDEO_RESOLUTION_HEIGHT = 2160
VIDEO_DPI = 150 # Adjust this if text/elements are too small/large

# --- FFmpeg Configuration ---
# Option 1: Ensure ffmpeg is in your system's PATH.
# Option 2: Explicitly set the path to ffmpeg executable if not in PATH.
#           Uncomment and set the correct path below if needed.
# ffmpeg_path = r'C:\ffmpeg\bin\ffmpeg.exe' # Example for Windows
# ffmpeg_path = '/usr/local/bin/ffmpeg' # Example for macOS/Linux
# if 'ffmpeg_path' in locals() and os.path.exists(ffmpeg_path):
#     plt.rcParams['animation.ffmpeg_path'] = ffmpeg_path
#     print(f"Using ffmpeg from: {plt.rcParams['animation.ffmpeg_path']}")
# else:
#     # Attempt to find ffmpeg in PATH (Matplotlib will do this by default)
#     print("Attempting to use ffmpeg from system PATH.")
#     # Check if Matplotlib can find ffmpeg
#     if animation.FFMpegWriter.isAvailable():
#         print("FFMpegWriter is available.")
#     else:
#         print("WARNING: FFMpegWriter is NOT available. MP4 saving will likely fail.")
#         print("Ensure ffmpeg is installed and in your system PATH, or set 'animation.ffmpeg_path' in plt.rcParams.")


PREFERRED_FONTS = [
    'DejaVu Sans', 
    'Noto Sans JP', 
    'Noto Sans KR', 
    'Noto Sans SC', 
    'Noto Sans TC',
    'Arial Unicode MS', 
    'sans-serif' # Generic fallback
]
plt.rcParams['font.family'] = PREFERRED_FONTS


def run_data_pipeline():
    """ (No changes to this function) """
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


def create_bar_chart_race_animation(race_df, song_album_map, n_bars=N_BARS,
                                    output_filename=OUTPUT_FILENAME, interval=ANIMATION_INTERVAL,
                                    width=VIDEO_RESOLUTION_WIDTH, height=VIDEO_RESOLUTION_HEIGHT,
                                    dpi=VIDEO_DPI):
    if race_df is None or race_df.empty:
        print("Cannot create animation: race_df is empty or None.")
        return

    num_frames = len(race_df.index)
    print(f"\n--- Starting Animation Creation for {output_filename} ---")
    print(f"Resolution: {width}x{height} at {dpi} DPI")
    print(f"Number of frames to render: {num_frames}")
    print(f"Target FPS: {1000/interval:.2f}")
    print(f"Displaying top {n_bars} songs.")
    print("This will take a significant amount of time. Please be patient.")

    figsize_w = width / dpi
    figsize_h = height / dpi
    fig, ax = plt.subplots(figsize=(figsize_w, figsize_h), dpi=dpi)

    all_song_ids = race_df.columns.tolist()
    color_indices = np.linspace(0, 1, len(all_song_ids))
    song_color_map = {song_id: plt.cm.viridis(color_indices[i]) for i, song_id in enumerate(all_song_ids)}
    
    max_play_count = race_df.max().max() * 1.05

    # --- Progress Counter ---
    # We need to pass this counter to draw_frame, or make it accessible.
    # Using a list or a simple class wrapper for mutable integer.
    # Or, just use the frame_index directly.

    def draw_frame(frame_index): # frame_index is 0 to num_frames-1
        if (frame_index + 1) % 100 == 0 or frame_index == num_frames -1 : # Print every 100 frames or on the last frame
            print(f"Rendering frame {frame_index + 1}/{num_frames}...")

        current_timestamp = race_df.index[frame_index]
        ax.clear()
        current_data = race_df.iloc[frame_index]
        top_n_songs = current_data[current_data > 0].nlargest(n_bars).sort_values(ascending=True)

        if top_n_songs.empty:
            ax.text(0.5, 0.5, current_timestamp.strftime('%d %B %Y %H:%M:%S'), 
                    transform=ax.transAxes, ha='center', va='center', fontsize=20* (dpi/100), color='grey')
            ax.set_title("My Spotify Top Songs 2024", fontsize=22* (dpi/100), pad=20* (dpi/100), weight='bold')
            ax.set_xlim(0, 100 if max_play_count < 100 else max_play_count)
            ax.set_yticks([])
            return

        bar_colors = [song_color_map.get(song_id, 'grey') for song_id in top_n_songs.index]
        bars = ax.barh(top_n_songs.index, top_n_songs.values, color=bar_colors, height=0.8)

        ax.set_title("My Spotify Top Songs 2024", fontsize=22 * (dpi/100), pad=20* (dpi/100), weight='bold')
        date_str = current_timestamp.strftime('%d %B %Y %H:%M:%S')
        ax.text(0.98, 0.95, date_str, transform=ax.transAxes, 
                ha='right', va='top', fontsize=20* (dpi/100), color='dimgray', weight='bold')

        tick_label_fontsize = 11 * (dpi/100) # Adjusted for potentially higher DPI
        value_label_fontsize = 10 * (dpi/100)

        for i, bar_obj in enumerate(bars):
            width_val = bar_obj.get_width()
            ax.text(width_val + (max_play_count * 0.005), 
                    bar_obj.get_y() + bar_obj.get_height() / 2,
                    f'{int(top_n_songs.values[i])}',
                    va='center', ha='left', fontsize=value_label_fontsize)
        
        ax.set_yticks(np.arange(len(top_n_songs)))
        # Shorten y-tick labels if they are too long (this needs to be done carefully)
        y_labels = []
        max_char_len = int(60 * (150/dpi)) # Heuristic for max characters for y-labels
        for song_title in top_n_songs.index:
            if len(song_title) > max_char_len:
                y_labels.append(song_title[:max_char_len-3] + "...")
            else:
                y_labels.append(song_title)
        ax.set_yticklabels(y_labels, fontsize=tick_label_fontsize)

        ax.set_xlabel("Total Plays", fontsize=16* (dpi/100))
        ax.set_xlim(0, max_play_count if max_play_count > 0 else 100)
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        ax.xaxis.set_ticks_position('top')
        ax.xaxis.set_label_position('top')
        ax.tick_params(axis='x', labelsize=tick_label_fontsize)
        
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_linewidth(1.5 * (dpi/100))
        plt.tight_layout(pad=2.0 * (dpi/100))

    # --- Create Animation ---
    ani = animation.FuncAnimation(fig, draw_frame, frames=num_frames,
                                  interval=interval, repeat=False)

    # --- Save Animation (MP4 using explicit FFMpegWriter) ---
    print(f"Preparing to save animation to {output_filename} using FFMpegWriter...")
    print("This is the slowest part and depends on CPU, number of frames, and resolution.")
    
    # Check if FFMpegWriter is available
    if not animation.FFMpegWriter.isAvailable():
        print("ERROR: FFMpegWriter is not available. Cannot save as MP4.")
        print("Please ensure ffmpeg is installed and in your system's PATH,")
        print("or set plt.rcParams['animation.ffmpeg_path'] correctly.")
        plt.close(fig)
        return

    try:
        # Explicitly create an FFMpegWriter instance
        ffmpeg_writer = animation.FFMpegWriter(
            fps=1000 / interval,
            codec='libx264',        # Common H.264 codec
            bitrate=-1,             # Use CRF for quality-based encoding
            extra_args=[            # Pass extra arguments for ffmpeg
                '-crf', '23',       # Constant Rate Factor (18-28 is good, lower is better quality)
                '-preset', 'medium', # Encoding speed vs. compression ('ultrafast', 'medium', 'slower')
                '-pix_fmt', 'yuv420p' # Pixel format for wide compatibility
            ]
            # metadata={'artist':'Your Name', 'title':'Spotify Race'} # Optional metadata
        )
        
        # The `dpi` for saving should ideally match the `dpi` of the figure
        # `ani.save` will use the figure's DPI if not specified, but good to be explicit
        ani.save(output_filename, writer=ffmpeg_writer, dpi=dpi) 
        
        print(f"Animation successfully saved to {output_filename}")

    except FileNotFoundError: # This might be caught by isAvailable, but good to have
        print("ERROR: ffmpeg not found during save. Please install ffmpeg and ensure it's in your system's PATH.")
    except Exception as e:
        print(f"Error saving animation: {e}")
        print("Ensure ffmpeg is installed and accessible. Check Matplotlib version and ffmpeg arguments.")
    finally:
        plt.close(fig) # Always close the figure


def main():
    # Check ffmpeg availability early
    if not animation.FFMpegWriter.isAvailable():
        print("CRITICAL WARNING: FFMpegWriter is not available. MP4 output will fail.")
        print("Please install ffmpeg and ensure it is in your system's PATH,")
        print("or correctly set plt.rcParams['animation.ffmpeg_path'] at the top of this script.")
        # choice = input("Continue anyway (will likely fail or produce GIF)? (y/n): ")
        # if choice.lower() != 'y':
        #     return
    else:
        print("FFMpegWriter appears to be available.")


    race_df, song_album_map = run_data_pipeline()

    if race_df is None or race_df.empty:
        print("\nNo data available for animation. Please check your CSV file and data ranges.")
        return

    print("\n--- Data ready for High-Resolution Animation ---")
    create_bar_chart_race_animation(race_df, song_album_map)


if __name__ == "__main__":
    main()