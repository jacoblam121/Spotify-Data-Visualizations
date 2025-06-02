# data_processor.py
import pandas as pd
import json
import os
import glob # For finding multiple Spotify history files

def load_spotify_data(spotify_files_pattern, min_ms_played, filter_skipped_tracks):
    """
    Loads and initially processes Spotify listening history from JSON files.
    Handles multiple StreamingHistory*.json files.
    """
    all_spotify_data = []
    
    # Find all files matching the pattern
    # Example: "StreamingHistory*.json" or a specific file "spotify_data.json"
    matching_files = glob.glob(spotify_files_pattern)
    
    if not matching_files:
        print(f"Error: No Spotify data files found matching pattern '{spotify_files_pattern}'.")
        return None

    print(f"Found Spotify data files: {matching_files}")

    for filepath in matching_files:
        print(f"Attempting to load Spotify data from: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_spotify_data.extend(data)
            print(f"Successfully loaded {len(data)} entries from {filepath}.")
        except FileNotFoundError:
            print(f"Error: The file '{filepath}' was not found (should not happen with glob).")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from '{filepath}': {e}")
            return None
        except Exception as e:
            print(f"An error occurred while loading '{filepath}': {e}")
            return None
    
    if not all_spotify_data:
        print("No data loaded from Spotify files.")
        return None

    df = pd.DataFrame(all_spotify_data)
    print(f"Total Spotify entries loaded: {len(df)}")

    # --- Column Mapping and Initial Filtering ---
    # Essential columns from Spotify data:
    # 'ts' -> timestamp
    # 'master_metadata_album_artist_name' -> artist
    # 'master_metadata_album_album_name' -> album
    # 'master_metadata_track_name' -> track
    # 'ms_played' -> for filtering
    # 'skipped' (optional) -> for filtering

    # Check for essential columns
    required_spotify_cols = ['ts', 'master_metadata_track_name', 'ms_played'] # Artist and Album can sometimes be null for podcasts/etc.
    missing_spotify_cols = [col for col in required_spotify_cols if col not in df.columns]
    if missing_spotify_cols:
        print(f"Error: Essential Spotify columns {missing_spotify_cols} are missing from the JSON data.")
        return None

    # Rename and select
    df_renamed = df.rename(columns={
        'ts': 'timestamp_str',
        'master_metadata_album_artist_name': 'artist',
        'master_metadata_album_album_name': 'album',
        'master_metadata_track_name': 'track'
    })

    # Keep only relevant columns plus ms_played and skipped for filtering
    cols_to_keep = ['timestamp_str', 'artist', 'album', 'track', 'ms_played']
    if 'skipped' in df_renamed.columns: # 'skipped' might not always be present
        cols_to_keep.append('skipped')
    
    df_selected = df_renamed[cols_to_keep].copy()

    # Convert timestamp string to datetime
    df_selected['timestamp'] = pd.to_datetime(df_selected['timestamp_str'], utc=True)
    df_selected.drop(columns=['timestamp_str'], inplace=True)
    print("Converted Spotify 'ts' to 'timestamp' datetime objects.")

    # Filter out entries that are not songs (e.g., podcasts might have null track/album/artist)
    # We are primarily interested in tracks with actual names.
    # Artist and Album might be None for some edge cases even for songs, but track name is key.
    initial_rows = len(df_selected)
    df_selected.dropna(subset=['track'], inplace=True) # Must have a track name
    if len(df_selected) < initial_rows:
        print(f"Dropped {initial_rows - len(df_selected)} rows with missing track names (e.g., podcasts, non-music audio).")

    # Filter by ms_played
    df_filtered_ms = df_selected[df_selected['ms_played'] >= min_ms_played].copy()
    if len(df_filtered_ms) < len(df_selected):
        print(f"Filtered out {len(df_selected) - len(df_filtered_ms)} tracks due to ms_played < {min_ms_played}.")
    
    # Optionally filter by 'skipped'
    if filter_skipped_tracks and 'skipped' in df_filtered_ms.columns:
        # Spotify's 'skipped' can be True, False, or sometimes None/NaN if the field isn't there or relevant.
        # We want to keep rows where 'skipped' is False.
        # If 'skipped' is boolean: keep where skipped == False
        # If 'skipped' can be None/NaN: treat None/NaN as not skipped or handle as needed.
        # Assuming 'skipped' is boolean when present.
        rows_before_skip_filter = len(df_filtered_ms)
        # Ensure 'skipped' is treated as boolean; NaNs can cause issues with direct comparison
        df_filtered_ms['skipped'] = df_filtered_ms['skipped'].fillna(False).astype(bool) 
        df_final_spotify = df_filtered_ms[df_filtered_ms['skipped'] == False].copy()
        if len(df_final_spotify) < rows_before_skip_filter:
            print(f"Filtered out {rows_before_skip_filter - len(df_final_spotify)} tracks because they were marked as skipped.")
    else:
        df_final_spotify = df_filtered_ms.copy()
        if filter_skipped_tracks and 'skipped' not in df_filtered_ms.columns:
            print("Note: 'FILTER_SKIPPED_TRACKS' is True, but 'skipped' column not found in Spotify data.")

    # Fill missing artist/album with "Unknown Artist" / "Unknown Album" if necessary
    # This is important because song_id relies on artist & track.
    df_final_spotify['artist'] = df_final_spotify['artist'].fillna('Unknown Artist')
    df_final_spotify['album'] = df_final_spotify['album'].fillna('Unknown Album')


    return df_final_spotify[['timestamp', 'artist', 'album', 'track']]


def load_lastfm_data(csv_filepath):
    """
    Loads and initially processes Last.fm listening history from CSV.
    (Adapted from original clean_spotify_data for Last.fm)
    """
    print(f"Attempting to load Last.fm data from: {csv_filepath}")
    try:
        df = pd.read_csv(csv_filepath)
        print(f"Successfully loaded {len(df)} rows from Last.fm CSV.")
    except FileNotFoundError:
        print(f"Error: The Last.fm file '{csv_filepath}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while loading the Last.fm CSV: {e}")
        return None

    if 'uts' not in df.columns: # Last.fm uses 'uts'
        print("Error: 'uts' column (Unix Timestamp Seconds) not found in Last.fm CSV. This column is required.")
        return None
        
    df['timestamp'] = pd.to_datetime(df['uts'], unit='s', utc=True)
    print("Converted Last.fm 'uts' to 'timestamp' datetime objects.")

    # Essential columns for Last.fm processing
    columns_to_keep_lastfm = ['timestamp', 'artist', 'album', 'track']
    missing_columns = [col for col in columns_to_keep_lastfm if col not in df.columns and col != 'timestamp']
    if missing_columns:
        print(f"Error: Essential Last.fm columns {missing_columns} are missing from the CSV after initial load.")
        return None
        
    df_selected = df[columns_to_keep_lastfm].copy()
    
    initial_rows = len(df_selected)
    df_selected.dropna(subset=['artist', 'album', 'track'], inplace=True)
    rows_dropped = initial_rows - len(df_selected)
    if rows_dropped > 0:
        print(f"Dropped {rows_dropped} rows from Last.fm data due to missing values in 'artist', 'album', or 'track'.")
    
    return df_selected


def clean_and_filter_data(config):
    """
    Loads data based on the source specified in config, cleans it, 
    and filters it by the specified timeframe.
    """
    data_source = config.get('DataSource', 'SOURCE', 'lastfm').lower()
    
    df_loaded = None
    if data_source == 'spotify':
        spotify_files = config.get('DataSource', 'INPUT_FILENAME_SPOTIFY', 'StreamingHistory*.json')
        min_ms = config.get_int('DataSource', 'MIN_MS_PLAYED_FOR_COUNT', 30000)
        filter_skipped = config.get_bool('DataSource', 'FILTER_SKIPPED_TRACKS', True)
        df_loaded = load_spotify_data(spotify_files, min_ms, filter_skipped)
    elif data_source == 'lastfm':
        lastfm_file = config.get('DataSource', 'INPUT_FILENAME_LASTFM', 'lastfm_data.csv')
        df_loaded = load_lastfm_data(lastfm_file)
    else:
        print(f"Error: Unsupported data source '{data_source}' specified in configuration.")
        return None

    if df_loaded is None or df_loaded.empty:
        print(f"No data loaded for source '{data_source}'.")
        return pd.DataFrame(columns=['timestamp', 'artist', 'album', 'track']) # Return empty standard df

    print(f"Successfully loaded and initially processed {len(df_loaded)} rows from '{data_source}'.")

    # --- Timeframe Filtering ---
    start_date_str = config.get('Timeframe', 'START_DATE', 'all_time')
    end_date_str = config.get('Timeframe', 'END_DATE', 'all_time')

    df_time_filtered = df_loaded.copy() # Start with all loaded data

    if start_date_str.lower() != 'all_time':
        try:
            start_date_dt = pd.to_datetime(start_date_str, utc=True)
            df_time_filtered = df_time_filtered[df_time_filtered['timestamp'] >= start_date_dt]
            print(f"Applied start date filter: >= {start_date_str}")
        except ValueError:
            print(f"Warning: Invalid START_DATE format '{start_date_str}'. Skipping start date filter.")

    if end_date_str.lower() != 'all_time':
        try:
            # Make end date inclusive of the whole day
            end_date_dt = pd.to_datetime(end_date_str, utc=True) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
            df_time_filtered = df_time_filtered[df_time_filtered['timestamp'] <= end_date_dt]
            print(f"Applied end date filter: <= {end_date_str} (inclusive)")
        except ValueError:
            print(f"Warning: Invalid END_DATE format '{end_date_str}'. Skipping end date filter.")
    
    if len(df_time_filtered) < len(df_loaded):
        print(f"Filtered down to {len(df_time_filtered)} rows after applying timeframe.")
    
    if df_time_filtered.empty:
        print(f"No data found for the specified timeframe. Returning empty DataFrame.")
        return pd.DataFrame(columns=['timestamp', 'artist', 'album', 'track'])

    print(f"Data cleaning and timeframe filtering complete. {len(df_time_filtered)} rows remaining.")
    return df_time_filtered


def prepare_data_for_bar_chart_race(cleaned_df):
    """
    Transforms cleaned data (from any source) to prepare it for a bar chart race.
    (No changes needed to this function itself, as it expects a standard DataFrame format)
    """
    if cleaned_df is None or cleaned_df.empty:
        print("Input DataFrame for 'prepare_data_for_bar_chart_race' is empty or None.")
        return None, {}

    print("\nStarting data preparation for high-resolution bar chart race...")
    df = cleaned_df.sort_values(by='timestamp').copy()

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


# This block allows testing this script directly
if __name__ == "__main__":
    print("--- Running data_processor.py directly for testing ---")
    
    # For testing, we need a config object.
    # We can mock one or try to load from a configurations.txt
    try:
        from config_loader import AppConfig # Assuming config_loader.py is in the same directory or accessible
        
        # Create a dummy configurations.txt if it doesn't exist, specifically for testing data_processor
        if not os.path.exists("configurations.txt"):
            print("Creating a dummy 'configurations.txt' for data_processor testing.")
            dummy_config_content = """
[DataSource]
SOURCE = spotify
INPUT_FILENAME_SPOTIFY = spotify_data.json
MIN_MS_PLAYED_FOR_COUNT = 10000
FILTER_SKIPPED_TRACKS = True

[Timeframe]
START_DATE = 2023-01-01
END_DATE = 2023-12-31
"""
            with open("configurations.txt", "w") as f_cfg:
                f_cfg.write(dummy_config_content)

        config = AppConfig(filepath="configurations.txt")
        print("Loaded configurations.txt for testing.")

    except ImportError:
        print("Could not import AppConfig. Mocking a simple config for testing.")
        class MockConfig:
            def get(self, section, key, fallback=None):
                if section == 'DataSource' and key == 'SOURCE': return 'spotify'
                if section == 'DataSource' and key == 'INPUT_FILENAME_SPOTIFY': return 'spotify_data.json'
                if section == 'DataSource' and key == 'MIN_MS_PLAYED_FOR_COUNT': return 10000 # Lower for test
                if section == 'DataSource' and key == 'FILTER_SKIPPED_TRACKS': return True
                if section == 'Timeframe' and key == 'START_DATE': return '2023-01-01' # Example
                if section == 'Timeframe' and key == 'END_DATE': return '2023-12-31'   # Example
                return fallback
            def get_int(self, section, key, fallback=0): return int(self.get(section, key, fallback))
            def get_bool(self, section, key, fallback=False): return self.get(section, key, fallback) in [True, 'True', 'true', '1']
        config = MockConfig()
    except FileNotFoundError:
        print("configurations.txt not found, and could not create dummy. Exiting test.")
        exit()


    # Create a dummy spotify_data.json if it doesn't exist for testing
    spotify_json_path = config.get('DataSource', 'INPUT_FILENAME_SPOTIFY')
    if not os.path.exists(spotify_json_path):
        print(f"Warning: '{spotify_json_path}' not found for testing.")
        print(f"Creating a minimal dummy '{spotify_json_path}' for this test run.")
        dummy_spotify_content = """
[
  {
    "ts": "2023-03-03T06:10:27Z", "platform": "WebPlayer", "ms_played": 180000, "conn_country": "US",
    "master_metadata_track_name": "Song Alpha", "master_metadata_album_artist_name": "Artist X", "master_metadata_album_album_name": "Album One",
    "spotify_track_uri": "uri1", "skipped": false
  },
  {
    "ts": "2023-03-03T06:15:00Z", "platform": "iOS", "ms_played": 5000, "conn_country": "US", 
    "master_metadata_track_name": "Song Beta (Skipped)", "master_metadata_album_artist_name": "Artist Y", "master_metadata_album_album_name": "Album Two",
    "spotify_track_uri": "uri2", "skipped": true
  },
  {
    "ts": "2023-03-04T10:20:00Z", "platform": "Android", "ms_played": 200000, "conn_country": "CA",
    "master_metadata_track_name": "Song Alpha", "master_metadata_album_artist_name": "Artist X", "master_metadata_album_album_name": "Album One",
    "spotify_track_uri": "uri1", "skipped": false
  },
  {
    "ts": "2023-03-05T11:00:00Z", "platform": "WebPlayer", "ms_played": 1000, "conn_country": "US",
    "master_metadata_track_name": "Song Gamma (Too Short)", "master_metadata_album_artist_name": "Artist Z", "master_metadata_album_album_name": "Album Three",
    "spotify_track_uri": "uri3", "skipped": false 
  },
  {
    "ts": "2024-01-01T00:00:00Z", "platform": "WebPlayer", "ms_played": 190000, "conn_country": "US",
    "master_metadata_track_name": "Song Outside Timeframe", "master_metadata_album_artist_name": "Artist O", "master_metadata_album_album_name": "Album O",
    "spotify_track_uri": "uri4", "skipped": false
  }
]
"""
        with open(spotify_json_path, "w", encoding='utf-8') as f_json:
            f_json.write(dummy_spotify_content)
        print(f"Created dummy '{spotify_json_path}'.")

    # Test with Spotify data
    print("\n--- Testing with Spotify Data Source ---")
    # If using the mock config, ensure DataSource:SOURCE is 'spotify' for this test
    if hasattr(config, 'config'): # If it's a real AppConfig
        config.config['DataSource']['SOURCE'] = 'spotify' 
        config.config['DataSource']['INPUT_FILENAME_SPOTIFY'] = 'spotify_data.json'
        config.config['DataSource']['MIN_MS_PLAYED_FOR_COUNT'] = '10000'
        config.config['DataSource']['FILTER_SKIPPED_TRACKS'] = 'True'
        config.config['Timeframe']['START_DATE'] = '2023-01-01'
        config.config['Timeframe']['END_DATE'] = '2023-12-31'


    cleaned_data_spotify = clean_and_filter_data(config)

    if cleaned_data_spotify is not None and not cleaned_data_spotify.empty:
        print("\n--- Cleaned Spotify Data (from data_processor.py test run) ---")
        print(cleaned_data_spotify.head())
        
        race_data_spotify, s_album_map_spotify = prepare_data_for_bar_chart_race(cleaned_data_spotify)
        
        if race_data_spotify is not None and not race_data_spotify.empty:
            print("\n--- Race Data (Spotify Source) ---")
            print(race_data_spotify.head())
            print(f"Shape of race_data: {race_data_spotify.shape}")
            print("\n--- Song Album Map (Spotify Source, first 5) ---")
            for i, (song, album) in enumerate(s_album_map_spotify.items()):
                if i >= 5: break
                print(f"'{song}': '{album}'")
        else:
            print("Spotify race data preparation resulted in empty or None DataFrame.")
    else:
        print("Spotify data cleaning resulted in empty or None DataFrame.")

    # You can add a similar test block for Last.fm by changing the config settings.
    print("\n--- Testing with Last.fm Data Source (if file exists) ---")
    if hasattr(config, 'config'): # If it's a real AppConfig
        config.config['DataSource']['SOURCE'] = 'lastfm'
        config.config['DataSource']['INPUT_FILENAME_LASTFM'] = 'lastfm_data.csv' # Ensure this exists or create dummy
        config.config['Timeframe']['START_DATE'] = '2024-01-01' # Adjust if needed for lastfm_data.csv
        config.config['Timeframe']['END_DATE'] = 'all_time'
    
    lastfm_csv_path = config.get('DataSource', 'INPUT_FILENAME_LASTFM')
    if not os.path.exists(lastfm_csv_path) and config.get('DataSource','SOURCE') == 'lastfm':
        print(f"Creating dummy '{lastfm_csv_path}' for Last.fm test.")
        dummy_lastfm_content = """uts,utc_time,artist,artist_mbid,album,album_mbid,track,track_mbid
1704067200,"01 Jan 2024, 00:00:00","Artist A","mbid_a","Album X","mbid_ax","Song 1","mbid_s1"
1704067260,"01 Jan 2024, 00:01:00","Artist B","mbid_b","Album Y","mbid_ay","Song 2","mbid_s2"
1704067320,"01 Jan 2024, 00:02:00","Artist A","mbid_a","Album X","mbid_ax","Song 1","mbid_s1"
"""
        with open(lastfm_csv_path, "w", encoding='utf-8') as f_csv:
            f_csv.write(dummy_lastfm_content)

    cleaned_data_lastfm = clean_and_filter_data(config)
    if cleaned_data_lastfm is not None and not cleaned_data_lastfm.empty:
        print("\n--- Cleaned Last.fm Data (from data_processor.py test run) ---")
        print(cleaned_data_lastfm.head())
    else:
        print("Last.fm data cleaning resulted in empty or None DataFrame (or was not configured to run).")