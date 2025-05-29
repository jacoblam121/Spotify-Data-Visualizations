# data_processor.py
import pandas as pd
from tqdm import tqdm
import numpy as np

# ... clean_spotify_data and prepare_data_for_bar_chart_race remain unchanged ...
def clean_spotify_data(csv_filepath):
    # ... (existing code for clean_spotify_data - no changes here) ...
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
        
    df['timestamp'] = pd.to_datetime(df['uts'], unit='s', utc=True) # Timestamp is UTC
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
    # ... (existing code for prepare_data_for_bar_chart_race - no changes here) ...
    if cleaned_df is None or cleaned_df.empty:
        print("Input DataFrame for 'prepare_data_for_bar_chart_race' is empty or None.")
        return None, {}

    print("\nStarting data preparation for high-resolution bar chart race...")
    df = cleaned_df.sort_values(by='timestamp').copy() # Ensure sorted by timestamp

    df['song_id'] = df['artist'] + " - " + df['track']
    print(f"Created 'song_id'. Total unique songs found: {df['song_id'].nunique()}")
    print(f"Total play events to process for frames: {len(df)}")

    song_album_map = df.groupby('song_id')['album'].first().to_dict()
    print(f"Created song_album_map with {len(song_album_map)} entries.")

    df['play_count_increment'] = 1
    df['cumulative_plays_for_song_at_event'] = df.groupby('song_id')['play_count_increment'].cumsum()

    race_df_sparse = df.pivot_table(index='timestamp',
                                    columns='song_id',
                                    values='cumulative_plays_for_song_at_event')
    
    print(f"Pivoted data based on individual play events. Shape: {race_df_sparse.shape}")

    race_df_filled = race_df_sparse.ffill()
    race_df = race_df_filled.fillna(0).astype(int)
    print("Filled NaN values in race_df (forward fill, then 0).")
    
    race_df = race_df.sort_index(axis=1)

    print(f"Data preparation for high-resolution race complete. Final race_df shape: {race_df.shape}")
    return race_df, song_album_map


def calculate_rolling_top_tracks(cleaned_df_input, race_df_timestamps):
    if cleaned_df_input is None or cleaned_df_input.empty:
        print("Warning: cleaned_df_input for calculate_rolling_top_tracks is empty. Returning empty results.")
        return pd.DataFrame(index=race_df_timestamps, columns=[
            'top_7_day_song_id', 'top_7_day_plays',
            'top_30_day_song_id', 'top_30_day_plays'
        ]).fillna({'top_7_day_plays': 0, 'top_30_day_plays': 0, 'top_7_day_song_id': "N/A", 'top_30_day_song_id': "N/A"})

    cleaned_df = cleaned_df_input.copy()

    if 'song_id' not in cleaned_df.columns:
        if 'artist' in cleaned_df.columns and 'track' in cleaned_df.columns:
            print("Creating 'song_id' in calculate_rolling_top_tracks.")
            cleaned_df['song_id'] = cleaned_df['artist'] + " - " + cleaned_df['track']
        else:
            raise ValueError("cleaned_df_input must have 'song_id' or 'artist' and 'track' columns.")

    if 'timestamp' not in cleaned_df.columns:
        raise ValueError("cleaned_df needs a 'timestamp' column for rolling calculations.")
    
    # Ensure 'timestamp' column is datetime and sorted
    cleaned_df['timestamp'] = pd.to_datetime(cleaned_df['timestamp']) # Ensure it's datetime
    if not cleaned_df['timestamp'].dt.tz:
         print("Warning: cleaned_df 'timestamp' column is timezone-naive in calculate_rolling_top_tracks. Assuming UTC for consistency.")
         cleaned_df['timestamp'] = cleaned_df['timestamp'].dt.tz_localize('UTC')


    cleaned_df = cleaned_df.sort_values('timestamp')
    temp_cleaned_df_with_ts_index = cleaned_df.set_index('timestamp', drop=False) # Index is now UTC-aware

    seven_days = pd.Timedelta(days=7)
    thirty_days = pd.Timedelta(days=30)

    # race_df_timestamps should also be UTC-aware if coming from race_df.index
    # which was derived from cleaned_df['timestamp']
    if race_df_timestamps.tz is None:
        print("Warning: race_df_timestamps are timezone-naive. Localizing to UTC.")
        race_df_timestamps = race_df_timestamps.tz_localize('UTC')
        # If it's already localized but to something else, convert:
        # elif race_df_timestamps.tz != pytz.UTC: # Requires import pytz
        #    race_df_timestamps = race_df_timestamps.tz_convert('UTC')


    unique_days_to_calculate = pd.to_datetime(race_df_timestamps.date).unique() # .date makes it naive date objects
    unique_days_to_calculate = unique_days_to_calculate.sort_values() 
    daily_results = {}

    print("Calculating rolling top tracks (this may take a while)...")
    for day_ts_start_of_day in tqdm(unique_days_to_calculate, desc="Processing days for rolling tops"):
        # Create target_ts_for_day_end as UTC-aware
        # day_ts_start_of_day is a naive date object from .date.unique()
        # So, create a Timestamp, then localize, then replace time components.
        target_ts_for_day_end = pd.Timestamp(day_ts_start_of_day).tz_localize('UTC').replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        # A slightly more robust way if day_ts_start_of_day was already a Timestamp:
        # target_ts_for_day_end = pd.Timestamp(day_ts_start_of_day, tz='UTC').replace(...)

        window_7_day_df = temp_cleaned_df_with_ts_index[
            (temp_cleaned_df_with_ts_index.index <= target_ts_for_day_end) &
            (temp_cleaned_df_with_ts_index.index > target_ts_for_day_end - seven_days)
        ]
        top_7_song_id, top_7_plays = ("N/A", 0)
        if not window_7_day_df.empty:
            counts_7_day = window_7_day_df['song_id'].value_counts()
            if not counts_7_day.empty:
                top_7_song_id = counts_7_day.index[0]
                top_7_plays = counts_7_day.iloc[0]

        window_30_day_df = temp_cleaned_df_with_ts_index[
            (temp_cleaned_df_with_ts_index.index <= target_ts_for_day_end) &
            (temp_cleaned_df_with_ts_index.index > target_ts_for_day_end - thirty_days)
        ]
        top_30_song_id, top_30_plays = ("N/A", 0)
        if not window_30_day_df.empty:
            counts_30_day = window_30_day_df['song_id'].value_counts()
            if not counts_30_day.empty:
                top_30_song_id = counts_30_day.index[0]
                top_30_plays = counts_30_day.iloc[0]
        
        # daily_results key should be tz-aware if we want to merge on it later with tz-aware index
        # However, we merge on final_results_df['day_key'] which is normalized (naive date).
        # So, day_ts_start_of_day (which is a naive date from .date.unique()) is fine as a key here.
        daily_results[day_ts_start_of_day] = {
            'top_7_day_song_id': top_7_song_id, 'top_7_day_plays': int(top_7_plays),
            'top_30_day_song_id': top_30_song_id, 'top_30_day_plays': int(top_30_plays)
        }
    
    if not daily_results:
        print("Warning: No daily results for rolling top tracks. Returning empty.")
        # Ensure index of returned DF matches tz-awareness of race_df_timestamps
        return pd.DataFrame(index=race_df_timestamps, columns=[
            'top_7_day_song_id', 'top_7_day_plays',
            'top_30_day_song_id', 'top_30_day_plays'
        ]).fillna({'top_7_day_plays': 0, 'top_30_day_plays': 0, 'top_7_day_song_id': "N/A", 'top_30_day_song_id': "N/A"})

    daily_results_df = pd.DataFrame.from_dict(daily_results, orient='index')
    # daily_results_df.index is now naive (from day_ts_start_of_day which is date object)
    
    # final_results_df index will be race_df_timestamps (which should be UTC)
    final_results_df = pd.DataFrame(index=race_df_timestamps)
    # final_results_df.index.normalize() would make it naive if it was aware.
    # We need the 'day_key' to be naive to match daily_results_df.index.
    final_results_df['day_key'] = pd.to_datetime(final_results_df.index.date) # .date makes it naive
    
    final_results_df = final_results_df.merge(daily_results_df, left_on='day_key', right_index=True, how='left')
    final_results_df.drop(columns=['day_key'], inplace=True)
    
    final_results_df.ffill(inplace=True)
    final_results_df.fillna({
        'top_7_day_song_id': "N/A", 'top_7_day_plays': 0,
        'top_30_day_song_id': "N/A", 'top_30_day_plays': 0
    }, inplace=True)
    final_results_df['top_7_day_plays'] = final_results_df['top_7_day_plays'].astype(int)
    final_results_df['top_30_day_plays'] = final_results_df['top_30_day_plays'].astype(int)

    print("Finished calculating rolling top tracks.")
    return final_results_df


# ... rest of data_processor.py (if __name__ == "__main__": block) remains the same ...
if __name__ == "__main__":
    print("--- Running data_processor.py directly for testing ---")
    
    input_csv_file = "lastfm_data.csv" 

    import os
    if not os.path.exists(input_csv_file):
        print(f"Warning: '{input_csv_file}' not found for testing.")
        print("Creating a minimal dummy 'lastfm_data.csv' for this test run.")
        dummy_data_list = []
        start_uts = 1704067200 # 01 Jan 2024 00:00:00
        for i in range(200): 
            uts = start_uts + (i * 3600 * 5) 
            day_of_year = pd.to_datetime(uts, unit='s').dayofyear # Naive datetime then .dayofyear
            
            artist = f"Artist {(i % 5)}" 
            track = f"Song {(i % 3)}"   
            album = f"Album {(i % 2)}"
            
            if day_of_year <= 10: 
                artist, track, album = "Artist Early", "Dominant Song Early", "Album Early"
            elif 10 < day_of_year <= 20: 
                artist, track, album = "Artist Mid", "Popular Song Mid", "Album Mid"
            
            # Create UTC string for dummy CSV for consistency, though clean_spotify_data forces UTC on load
            utc_time_str = pd.to_datetime(uts, unit='s', utc=True).strftime("%d %b %Y, %H:%M:%S")
            dummy_data_list.append(f'{uts},"{utc_time_str}","{artist}","mbid_a","{album}","mbid_ax","{track}","mbid_s1"')
        
        dummy_csv_content = "uts,utc_time,artist,artist_mbid,album,album_mbid,track,track_mbid\n" + "\n".join(dummy_data_list)

        with open(input_csv_file, "w", encoding='utf-8') as f:
            f.write(dummy_csv_content)
        print(f"Created dummy '{input_csv_file}' with more varied data.")

    cleaned_data = clean_spotify_data(input_csv_file) # cleaned_data['timestamp'] is UTC

    if cleaned_data is not None and not cleaned_data.empty:
        print("\n--- Cleaned Data (from data_processor.py test run) ---")
        print(cleaned_data.head())
        
        # cleaned_data_sorted is not strictly needed as prepare_data... sorts, but good practice
        cleaned_data_sorted = cleaned_data.sort_values(by='timestamp').copy() 
        
        race_data, s_album_map = prepare_data_for_bar_chart_race(cleaned_data_sorted) # race_data.index is UTC
        
        if race_data is not None and not race_data.empty:
            print("\n--- Race Data (from data_processor.py test run) ---")
            print(race_data.head())
            print(f"\nShape of race_data: {race_data.shape}")
            print(f"Race data index timezone: {race_data.index.tz}") # Should be UTC
            
            print("\n--- Testing Rolling Top Tracks Calculation ---")
            # cleaned_data['timestamp'] is UTC. race_data.index is UTC.
            rolling_tops = calculate_rolling_top_tracks(cleaned_data, race_data.index)
            if rolling_tops is not None and not rolling_tops.empty:
                print("\n--- Rolling Top Tracks Data (Sample) ---")
                print(rolling_tops.head())
                print("...")
                print(rolling_tops.tail())
                print(f"Shape of rolling_tops: {rolling_tops.shape}")
                print(f"Rolling tops index timezone: {rolling_tops.index.tz}") # Should match race_data.index.tz

                print("\n--- Rolling Top Tracks Value Counts (Top 5 for 7-day song_id) ---")
                print(rolling_tops['top_7_day_song_id'].value_counts().nlargest(5))
                print("\n--- Rolling Top Tracks Value Counts (Top 5 for 30-day song_id) ---")
                print(rolling_tops['top_30_day_song_id'].value_counts().nlargest(5))

            else:
                print("Rolling top tracks calculation resulted in empty or None DataFrame.")
        else:
            print("Race data preparation resulted in empty or None DataFrame in test run.")
    else:
        print("Data cleaning resulted in empty or None DataFrame in test run.")