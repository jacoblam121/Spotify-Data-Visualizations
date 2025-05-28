# data_processor.py
import pandas as pd

def clean_spotify_data(csv_filepath):
    """
    Loads Spotify listening history, cleans it, and filters for the year 2024.
    (No changes to this function from the previous version, included for completeness)
    """
    print(f"Attempting to load data from: {csv_filepath}")
    try:
        df = pd.read_csv(csv_filepath)
        print(f"Successfully loaded {len(df)} rows from CSV.")
    except FileNotFoundError:
        print(f"Error: The file '{csv_filepath}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while loading the CSV: {e}")
        return None

    if 'uts' not in df.columns:
        print("Error: 'uts' column (Unix Timestamp Seconds) not found in CSV. This column is required.")
        return None
        
    df['timestamp'] = pd.to_datetime(df['uts'], unit='s', utc=True)
    print("Converted 'uts' to 'timestamp' datetime objects.")

    df_2024 = df[df['timestamp'].dt.year == 2024].copy()
    print(f"Filtered down to {len(df_2024)} rows for the year 2024.")

    if df_2024.empty:
        print("No data found for the year 2024. Returning empty DataFrame.")
        return pd.DataFrame(columns=['timestamp', 'artist', 'album', 'track'])

    columns_to_keep = ['timestamp', 'artist', 'album', 'track']
    missing_columns = [col for col in columns_to_keep if col not in df_2024.columns and col != 'timestamp']
    if missing_columns:
        print(f"Error: Essential columns {missing_columns} are missing from the CSV after initial load.")
        return None
        
    df_cleaned = df_2024[columns_to_keep].copy()
    
    initial_rows = len(df_cleaned)
    df_cleaned.dropna(subset=['artist', 'album', 'track'], inplace=True)
    rows_dropped = initial_rows - len(df_cleaned)
    if rows_dropped > 0:
        print(f"Dropped {rows_dropped} rows due to missing values in 'artist', 'album', or 'track'.")
    
    print(f"Data cleaning complete. {len(df_cleaned)} rows remaining.")
    return df_cleaned


def prepare_data_for_bar_chart_race(cleaned_df):
    """
    Transforms cleaned Spotify data to prepare it for a bar chart race,
    with frames corresponding to each play event for maximum smoothness.

    Args:
        cleaned_df (pd.DataFrame): DataFrame from the clean_spotify_data function.
                                   Expected columns: ['timestamp', 'artist', 'album', 'track']

    Returns:
        tuple: (race_df, song_album_map)
            - race_df (pd.DataFrame): DataFrame ready for animation.
                Index: Timestamps of each play event (sorted).
                Columns: Unique song_ids.
                Values: Cumulative play counts *at that exact timestamp*.
            - song_album_map (dict): A dictionary mapping song_id to album name.
    """
    if cleaned_df is None or cleaned_df.empty:
        print("Input DataFrame for 'prepare_data_for_bar_chart_race' is empty or None.")
        return None, {}

    print("\nStarting data preparation for high-resolution bar chart race...")
    # Sort by timestamp first, as this is the basis of our "time"
    df = cleaned_df.sort_values(by='timestamp').copy()

    # --- 1. Create a unique 'song_id' (Artist - Track) ---
    df['song_id'] = df['artist'] + " - " + df['track']
    print(f"Created 'song_id'. Total unique songs found: {df['song_id'].nunique()}")
    print(f"Total play events to process for frames: {len(df)}")

    # --- 2. Create a mapping from song_id to album ---
    song_album_map = df.groupby('song_id')['album'].first().to_dict()
    print(f"Created song_album_map with {len(song_album_map)} entries.")

    # --- 3. For each play event (row), calculate cumulative plays up to that point ---
    # We need to know, for each row (play event), what the cumulative count of *that song* is.
    # A simple way is to assign a 'play_count_increment' of 1 for each row,
    # then group by 'song_id' and calculate cumsum on this increment, sorted by timestamp.
    df['play_count_increment'] = 1
    df['cumulative_plays_for_song_at_event'] = df.groupby('song_id')['play_count_increment'].cumsum()

    # --- 4. Pivot the table to get timestamps as rows, songs as columns ---
    # The index will be the timestamp of each play event.
    # The columns will be song_ids.
    # The values will be the 'cumulative_plays_for_song_at_event' for the specific song_id of that row.
    # All other song_ids for that timestamp row will be NaN initially.
    
    # Create the pivot table with the specific song's cumulative count at its play event
    # This results in a very sparse matrix where only one song has a value per row.
    race_df_sparse = df.pivot_table(index='timestamp',
                                    columns='song_id',
                                    values='cumulative_plays_for_song_at_event')
    
    print(f"Pivoted data based on individual play events. Shape: {race_df_sparse.shape}")

    # --- 5. Fill NaN values ---
    # For each song column, forward-fill its cumulative count.
    # This means if Song A was played at T1 (count 5) and then T3 (count 6),
    # at T2 (if T2 is another song's play event), Song A's count should still be 5.
    race_df_filled = race_df_sparse.ffill()

    # Any NaNs remaining at the beginning (before a song's first play) should be 0.
    race_df = race_df_filled.fillna(0).astype(int)
    print("Filled NaN values in race_df (forward fill, then 0).")
    
    # Ensure columns (song_ids) are sorted alphabetically for consistent ordering if desired
    race_df = race_df.sort_index(axis=1)

    # The index (timestamps) should already be sorted because we sorted `df` by 'timestamp' initially.
    # df.pivot_table also preserves the order of the index values.

    print(f"Data preparation for high-resolution race complete. Final race_df shape: {race_df.shape}")
    return race_df, song_album_map


# This block allows testing this script directly
if __name__ == "__main__":
    print("--- Running data_processor.py directly for testing (high-resolution mode) ---")
    
    input_csv_file = "lastfm_data.csv" 

    import os
    if not os.path.exists(input_csv_file):
        print(f"Warning: '{input_csv_file}' not found for testing.")
        print("Creating a minimal dummy 'lastfm_data.csv' for this test run.")
        dummy_csv_content = """uts,utc_time,artist,artist_mbid,album,album_mbid,track,track_mbid
1704067200,"01 Jan 2024, 00:00:00","Artist A","mbid_a","Album X","mbid_ax","Song 1","mbid_s1"
1704067260,"01 Jan 2024, 00:01:00","Artist B","mbid_b","Album Y","mbid_ay","Song 2","mbid_s2"
1704067320,"01 Jan 2024, 00:02:00","Artist A","mbid_a","Album X","mbid_ax","Song 1","mbid_s1"
1704067380,"01 Jan 2024, 00:03:00","Artist C","mbid_c","Album Z","mbid_az","Song 3","mbid_s3"
1704067440,"01 Jan 2024, 00:04:00","Artist A","mbid_a","Album X","mbid_ax","Song 1","mbid_s1"
"""
        with open(input_csv_file, "w") as f:
            f.write(dummy_csv_content)
        print(f"Created dummy '{input_csv_file}'.")

    cleaned_data = clean_spotify_data(input_csv_file)

    if cleaned_data is not None and not cleaned_data.empty:
        print("\n--- Cleaned Data (from data_processor.py test run) ---")
        print(cleaned_data.head())
        
        race_data, s_album_map = prepare_data_for_bar_chart_race(cleaned_data)
        
        if race_data is not None and not race_data.empty:
            print("\n--- Race Data (from data_processor.py test run) ---")
            print(race_data.head())
            print(f"\nShape of race_data: {race_data.shape}") # Expect more rows now
            
            print("\n--- Song Album Map (from data_processor.py test run, first 5 entries) ---")
            count = 0
            for song, album in s_album_map.items():
                print(f"'{song}': '{album}'")
                count += 1
                if count >= 5:
                    break
        else:
            print("Race data preparation resulted in empty or None DataFrame in test run.")
    else:
        print("Data cleaning resulted in empty or None DataFrame in test run.")