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
    # spotify_track_uri is also essential for precise album art lookup
    if 'spotify_track_uri' not in df.columns:
        print("Warning: 'spotify_track_uri' column not found in Spotify JSON data. This may affect album art accuracy.")
        # Decide if this should be a critical error or allow fallback
        # For now, allow fallback to search-based lookup if URI is missing.
        # return None # Or: df['spotify_track_uri'] = None (if you want to ensure column exists)

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

    # Store original case for display before normalization
    if 'artist' in df_renamed.columns:
        df_renamed['original_artist'] = df_renamed['artist']
    else:
        df_renamed['original_artist'] = "Unknown Artist" # Fallback
    
    if 'track' in df_renamed.columns:
        df_renamed['original_track'] = df_renamed['track']
    else:
        df_renamed['original_track'] = "Unknown Track" # Fallback

    # Keep only relevant columns plus ms_played and skipped for filtering
    cols_to_keep = ['timestamp_str', 'artist', 'album', 'track', 'ms_played', 'spotify_track_uri', 'original_artist', 'original_track']
    if 'spotify_track_uri' not in df_renamed.columns: # Ensure it exists even if it was missing (will be all None)
        df_renamed['spotify_track_uri'] = None
    
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

    # --- Store original case for display before normalization ---
    df_selected['original_artist'] = df_selected['artist'].astype(str).str.strip()
    df_selected['original_track'] = df_selected['track'].astype(str).str.strip()
    
    # --- Normalize artist and track names for consistent key generation ---
    # Convert to string type to ensure .str accessor works, then lower and strip.
    # This helps ensure consistency for song_id creation.
    if 'artist' in df_selected.columns:
        df_selected['artist'] = df_selected['artist'].astype(str).str.lower().str.strip()
    if 'track' in df_selected.columns: # Should always be present due to dropna above
        df_selected['track'] = df_selected['track'].astype(str).str.lower().str.strip()
    if 'album' in df_selected.columns:
        df_selected['album'] = df_selected['album'].astype(str).str.lower().str.strip()
    print("Normalized artist, track, and album names (lowercase, stripped whitespace).")
    # --- End normalization ---

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
    df_final_spotify['artist'] = df_final_spotify['artist'].fillna('unknown artist') # Ensure consistent case
    df_final_spotify['album'] = df_final_spotify['album'].fillna('unknown album')   # Ensure consistent case
    # Ensure original_artist and original_track also have fallbacks if they were somehow missed or became NaN
    df_final_spotify['original_artist'] = df_final_spotify['original_artist'].fillna(df_final_spotify['artist'])
    df_final_spotify['original_track'] = df_final_spotify['original_track'].fillna(df_final_spotify['track'])

    return df_final_spotify[['timestamp', 'artist', 'album', 'track', 'spotify_track_uri', 'original_artist', 'original_track']] # Include URI and originals


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
    
    # Check if 'album_mbid' exists and add it if so
    if 'album_mbid' in df.columns:
        columns_to_keep_lastfm.append('album_mbid')
    else:
        print("Note: 'album_mbid' column not found in Last.fm CSV. Will proceed without it.")
        df['album_mbid'] = None # Ensure the column exists for consistent structure, filled with None
    
    # Check if 'artist_mbid' exists and add it if so
    if 'artist_mbid' in df.columns:
        columns_to_keep_lastfm.append('artist_mbid')
        print("✅ Found 'artist_mbid' column in Last.fm CSV - will enable MBID-based verification")
    else:
        print("Note: 'artist_mbid' column not found in Last.fm CSV. Will proceed without it.")
        df['artist_mbid'] = None # Ensure the column exists for consistent structure, filled with None

    missing_columns = [col for col in columns_to_keep_lastfm if col not in df.columns and col != 'timestamp' and col != 'album_mbid' and col != 'artist_mbid']
    if missing_columns:
        print(f"Error: Essential Last.fm columns {missing_columns} are missing from the CSV after initial load.")
        return None
        
    df_selected = df[columns_to_keep_lastfm].copy()
    
    initial_rows = len(df_selected)
    # Store original case for display before normalization (assuming 'artist' and 'track' cols exist)
    df_selected['original_artist'] = df_selected['artist']
    df_selected['original_track'] = df_selected['track']

    df_selected.dropna(subset=['artist', 'album', 'track'], inplace=True)
    rows_dropped = initial_rows - len(df_selected)
    if rows_dropped > 0:
        print(f"Dropped {rows_dropped} rows from Last.fm data due to missing values in 'artist', 'album', or 'track'.")
    
    # Ensure all expected columns are present before returning, even if some were added as None
    final_cols = ['timestamp', 'artist', 'album', 'track', 'album_mbid', 'artist_mbid', 'original_artist', 'original_track']
    for col in final_cols:
        if col not in df_selected.columns:
            df_selected[col] = None
            
    return df_selected[final_cols]


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
        # For Last.fm, we assume names are already reasonably consistent or we apply similar normalization
        df_raw_lastfm = load_lastfm_data(lastfm_file)
        if df_raw_lastfm is not None and not df_raw_lastfm.empty:
            df_raw_lastfm['artist'] = df_raw_lastfm['artist'].astype(str).str.lower().str.strip()
            df_raw_lastfm['track'] = df_raw_lastfm['track'].astype(str).str.lower().str.strip()
            df_raw_lastfm['album'] = df_raw_lastfm['album'].astype(str).str.lower().str.strip()
            df_raw_lastfm['artist'] = df_raw_lastfm['artist'].fillna('unknown artist')
            df_raw_lastfm['album'] = df_raw_lastfm['album'].fillna('unknown album')
            # Ensure original case columns exist (they should already be set in load_lastfm_data)
            # Don't overwrite them with lowercase versions if they already exist
            if 'original_artist' not in df_raw_lastfm.columns:
                print("Warning: original_artist column missing from Last.fm data - display names may be lowercase")
                df_raw_lastfm['original_artist'] = df_raw_lastfm['artist'] # This will be lowercase
            if 'original_track' not in df_raw_lastfm.columns:
                print("Warning: original_track column missing from Last.fm data - display names may be lowercase")
                df_raw_lastfm['original_track'] = df_raw_lastfm['track'] # This will be lowercase

            print("Normalized artist, track, and album names for Last.fm data.")
        df_loaded = df_raw_lastfm
    else:
        print(f"Error: Unsupported data source '{data_source}' specified in configuration.")
        return None

    if df_loaded is None or df_loaded.empty:
        print(f"No data loaded for source '{data_source}'.")
        # Return empty standard df with all expected columns for downstream processing
        base_cols = ['timestamp', 'artist', 'album', 'track', 'original_artist', 'original_track']
        if data_source == 'spotify':
            base_cols.append('spotify_track_uri')
        elif data_source == 'lastfm':
            base_cols.extend(['album_mbid', 'artist_mbid'])
        return pd.DataFrame(columns=base_cols)

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
        # Ensure empty DataFrame has the necessary columns based on source
        base_cols = ['timestamp', 'artist', 'album', 'track', 'original_artist', 'original_track']
        if data_source == 'spotify': # Re-check source from config as df_loaded might be empty
            base_cols.append('spotify_track_uri')
        elif config.get('DataSource', 'SOURCE', 'lastfm').lower() == 'lastfm': # Check original config source
            base_cols.append('album_mbid')
        return pd.DataFrame(columns=base_cols)

    print(f"Data cleaning and timeframe filtering complete. {len(df_time_filtered)} rows remaining.")
    return df_time_filtered


def split_artist_collaborations(artist_string):
    """
    Split artist collaborations into individual artists.
    Handles various collaboration formats: feat., ft., &, with, x, etc.
    Enhanced to handle parenthetical collaborations like "(with blackbear)".
    
    Args:
        artist_string: String containing one or more artist names
        
    Returns:
        List of individual artist names
    
    Examples:
        "BoyWithUke (with blackbear)" -> ["BoyWithUke", "blackbear"]
        "Taylor Swift feat. Ed Sheeran" -> ["Taylor Swift", "Ed Sheeran"]
        "Artist A, Artist B & Artist C" -> ["Artist A", "Artist B", "Artist C"]
    """
    if not artist_string or pd.isna(artist_string):
        return []
    
    # Convert to string and clean
    artist_str = str(artist_string).strip()
    
    # Define separators in order of priority (more specific first)
    # We'll handle case-insensitive matching for some separators
    import re
    
    # First, handle parenthetical collaborations like "(with blackbear)" or "(feat. Artist)"
    paren_collab_pattern = re.compile(r'\s*\(\s*(?:with|feat\.?|featuring)\s+([^)]+)\)', re.IGNORECASE)
    paren_matches = paren_collab_pattern.findall(artist_str)
    
    # Remove parenthetical collaborations from main string
    main_artist_str = paren_collab_pattern.sub('', artist_str).strip()
    
    # Handle case-insensitive feat/ft/featuring in the main string
    feat_pattern = re.compile(r'\s+(feat\.?|ft\.?|featuring)\s+', re.IGNORECASE)
    main_artist_str = feat_pattern.sub(' feat. ', main_artist_str)
    
    # Now use standardized separators
    separators = [
        ' feat. ', ' with ', ' With ', ' x ', ' X ', ' vs. ', ' Vs. ', ' VS ',
        ' & ', ', ', ' and ', ' And ', ' AND '
    ]
    
    # Start with the main string (parenthetical collaborations removed)
    artists = [main_artist_str] if main_artist_str else []
    
    # Iteratively split by each separator
    for separator in separators:
        new_artists = []
        for artist in artists:
            if separator in artist:
                # Split and clean each part
                parts = [part.strip() for part in artist.split(separator) if part.strip()]
                new_artists.extend(parts)
            else:
                new_artists.append(artist)
        artists = new_artists
    
    # Add artists from parenthetical collaborations
    for paren_artist in paren_matches:
        # Split parenthetical artists if they contain multiple names
        paren_split = [part.strip() for part in paren_artist.split(',') if part.strip()]
        artists.extend(paren_split)
    
    # Clean up any remaining parenthetical information (e.g., "(Korean)" or other metadata)
    cleaned_artists = []
    for artist in artists:
        if not artist or not artist.strip():
            continue
        # Remove parenthetical info that's not part of the artist name
        if '(' in artist and ')' in artist:
            # Keep common valid parentheticals like (G)I-DLE
            if artist.upper() not in ['(G)I-DLE', '(G)I-DLE ((여자)아이들)']:
                # Remove content in parentheses if it looks like metadata
                cleaned = re.sub(r'\s*\([^)]*(?:korean|k-pop|remix|official)[^)]*\)', '', artist, flags=re.IGNORECASE)
                if cleaned.strip():
                    artist = cleaned.strip()
        cleaned_artists.append(artist)
    
    # Remove duplicates while preserving order (use casefold for Unicode)
    seen = set()
    unique_artists = []
    for artist in cleaned_artists:
        if not artist or not artist.strip():
            continue
        artist_normalized = artist.strip().casefold()
        if artist_normalized not in seen:
            seen.add(artist_normalized)
            unique_artists.append(artist.strip())
    
    return unique_artists


def prepare_data_for_bar_chart_race(cleaned_df, mode="tracks"):
    """
    Transforms cleaned data (from any source) to prepare it for a bar chart race.
    Supports both tracks and artists visualization modes.
    
    Args:
        cleaned_df: DataFrame with play events
        mode: "tracks" for track-based race, "artists" for artist-based race
    
    Returns:
        tuple: (race_df, details_map) where details_map structure depends on mode
    """
    if cleaned_df is None or cleaned_df.empty:
        print(f"Input DataFrame for 'prepare_data_for_bar_chart_race' ({mode} mode) is empty or None.")
        return None, {}

    print(f"\nStarting data preparation for high-resolution bar chart race ({mode} mode)...")
    df = cleaned_df.sort_values(by='timestamp').copy()

    if mode == "tracks":
        # Original track-based logic
        df['entity_id'] = df['artist'] + " - " + df['track']
        entity_type = "songs"
        print(f"Created 'song_id'. Total unique songs found: {df['entity_id'].nunique()}")
    elif mode == "artists":
        # New artist-based logic with collaboration support
        # Split collaborations and create separate rows for each artist
        print("Splitting artist collaborations...")
        expanded_rows = []
        
        for idx, row in df.iterrows():
            # Split artists from both normalized and original artist fields
            artists_normalized = split_artist_collaborations(row['artist'])
            artists_original = split_artist_collaborations(row.get('original_artist', row['artist']))
            
            # Ensure we have the same number of artists in both lists
            if len(artists_normalized) != len(artists_original):
                # Fallback: use the normalized version for both
                artists_original = artists_normalized
            
            # Create a row for each individual artist
            for i, artist_norm in enumerate(artists_normalized):
                new_row = row.copy()
                new_row['artist'] = artist_norm.lower().strip()  # Normalized version
                new_row['original_artist'] = artists_original[i] if i < len(artists_original) else artist_norm
                new_row['entity_id'] = new_row['artist']  # Use normalized for entity_id
                expanded_rows.append(new_row)
        
        # Create new dataframe with expanded rows
        df = pd.DataFrame(expanded_rows)
        entity_type = "artists"
        print(f"Expanded {len(cleaned_df)} plays to {len(df)} artist entries after splitting collaborations")
        print(f"Created 'artist_id'. Total unique artists found: {df['entity_id'].nunique()}")
    else:
        raise ValueError(f"Unsupported mode: {mode}. Must be 'tracks' or 'artists'.")

    print(f"Total play events to process for frames: {len(df)}")

    # Create entity details map (structure depends on mode)
    entity_details_map = {}
    has_uri = 'spotify_track_uri' in df.columns
    has_mbid = 'album_mbid' in df.columns

    for _, row in df.drop_duplicates(subset=['entity_id'], keep='first').iterrows():
        entity_id = row['entity_id']
        
        if mode == "tracks":
            # Track mode: include album info and track URI for album art lookup
            details = {
                'name': row['album'], # Album name for art lookup
                'track_uri': row['spotify_track_uri'] if has_uri else None,
                'mbid': row['album_mbid'] if has_mbid else None,
                'display_artist': row['original_artist'], 
                'display_track': row['original_track']
            }
        elif mode == "artists":
            # Artist mode: store artist info for profile photo lookup
            details = {
                'display_artist': row['original_artist'],
                'normalized_artist': row['artist'],  # For consistent lookups
                # We'll add most_played_track info later for fallback album art
                'most_played_track': None,
                'most_played_album': None,
                'most_played_track_uri': None
            }
        
        entity_details_map[entity_id] = details

    # For artist mode, we need to find the most played track per artist for fallback album art
    if mode == "artists":
        for artist_id in entity_details_map.keys():
            artist_tracks = df[df['entity_id'] == artist_id]
            # Find most played track for this artist (by frequency)
            track_counts = artist_tracks['track'].value_counts()
            if not track_counts.empty:
                most_played_track_name = track_counts.index[0]
                # Get the first occurrence of this track for this artist
                track_row = artist_tracks[artist_tracks['track'] == most_played_track_name].iloc[0]
                
                # Store as dictionary for consistent access
                entity_details_map[artist_id]['most_played_track'] = {
                    'track_name': track_row['original_track'],
                    'album_name': track_row['album'],
                    'track_uri': track_row['spotify_track_uri'] if has_uri else None
                }
                # Keep backwards compatibility
                entity_details_map[artist_id]['most_played_album'] = track_row['album']
                if has_uri:
                    entity_details_map[artist_id]['most_played_track_uri'] = track_row['spotify_track_uri']

    print(f"Created {entity_type}_details_map with {len(entity_details_map)} entries including display names.")

    df['play_count_increment'] = 1
    df['cumulative_plays_for_entity_at_event'] = df.groupby('entity_id')['play_count_increment'].cumsum()
    
    race_df_sparse = df.pivot_table(index='timestamp',
                                    columns='entity_id',
                                    values='cumulative_plays_for_entity_at_event')
    print(f"Pivoted data based on individual play events. Shape: {race_df_sparse.shape}")

    race_df_filled = race_df_sparse.ffill()
    race_df = race_df_filled.fillna(0).astype(int)
    print("Filled NaN values in race_df (forward fill, then 0).")
    
    race_df = race_df.sort_index(axis=1)

    print(f"Data preparation for high-resolution race complete. Final race_df shape: {race_df.shape}")
    return race_df, entity_details_map


def calculate_rolling_window_stats(cleaned_df_for_rolling_stats, animation_frame_timestamps, mode="tracks"):
    """
    Calculates the top track/artist for a 7-day and 30-day rolling window for each animation frame timestamp.

    Args:
        cleaned_df_for_rolling_stats (pd.DataFrame): DataFrame containing all play events,
                                                     must have 'timestamp' and entity ID column.
                                                     Timestamps should be timezone-aware (UTC).
        animation_frame_timestamps (pd.DatetimeIndex or list): A list or DatetimeIndex of timestamps
                                                               for which animation frames will be generated.
                                                               These are the "current day" for each rolling window.
        mode (str): "tracks" or "artists" to determine what entity to calculate stats for.

    Returns:
        dict: A dictionary where keys are the animation_frame_timestamps and values are dicts
              containing rolling window stats for the specified mode.
    """
    mode_label = "track" if mode == "tracks" else "artist"
    entity_id_col = "song_id" if mode == "tracks" else "artist_id"
    
    print(f"\n--- Calculating Rolling Window Stats (7-day and 30-day) for {mode} mode ---")
    if cleaned_df_for_rolling_stats is None or cleaned_df_for_rolling_stats.empty:
        print(f"Warning: cleaned_df_for_rolling_stats is empty. Cannot calculate rolling window stats for {mode}.")
        return {ts: {'top_7_day': None, 'top_30_day': None} for ts in animation_frame_timestamps}

    # We need to create the entity_id column if it doesn't exist
    df_for_stats = cleaned_df_for_rolling_stats.copy()
    
    if mode == "tracks":
        if 'song_id' not in df_for_stats.columns:
            if 'artist' in df_for_stats.columns and 'track' in df_for_stats.columns:
                df_for_stats['song_id'] = df_for_stats['artist'] + " - " + df_for_stats['track']
            else:
                print("Error: Cannot create 'song_id' column. Missing 'artist' or 'track' columns.")
                return {ts: {'top_7_day': None, 'top_30_day': None} for ts in animation_frame_timestamps}
        entity_id_col = 'song_id'
    elif mode == "artists":
        if 'artist_id' not in df_for_stats.columns:
            if 'artist' in df_for_stats.columns:
                df_for_stats['artist_id'] = df_for_stats['artist']
            else:
                print("Error: Cannot create 'artist_id' column. Missing 'artist' column.")
                return {ts: {'top_7_day': None, 'top_30_day': None} for ts in animation_frame_timestamps}
        entity_id_col = 'artist_id'

    if 'timestamp' not in df_for_stats.columns or entity_id_col not in df_for_stats.columns:
        print(f"Error: 'timestamp' or '{entity_id_col}' not in df_for_stats. Cannot calculate rolling stats.")
        return {ts: {'top_7_day': None, 'top_30_day': None} for ts in animation_frame_timestamps}

    # Create a mapping from entity_id to original names for display
    entity_id_to_originals = {}
    if mode == "tracks":
        if 'original_artist' in df_for_stats.columns and 'original_track' in df_for_stats.columns:
            entity_id_to_originals = df_for_stats.drop_duplicates(subset=['song_id']) \
                                    .set_index('song_id')[['original_artist', 'original_track']].to_dict('index')
    elif mode == "artists":
        if 'original_artist' in df_for_stats.columns:
            entity_id_to_originals = df_for_stats.drop_duplicates(subset=['artist_id']) \
                                    .set_index('artist_id')[['original_artist']].to_dict('index')

    rolling_stats_by_frame_timestamp = {}
    processed_timestamps = 0

    for current_ts in animation_frame_timestamps:
        if not isinstance(current_ts, pd.Timestamp):
            try:
                current_ts_dt = pd.to_datetime(current_ts, utc=True)
            except Exception as e:
                print(f"Warning: Could not convert timestamp {current_ts} to datetime: {e}. Skipping rolling stats for this timestamp.")
                rolling_stats_by_frame_timestamp[current_ts] = {'top_7_day': None, 'top_30_day': None}
                continue
        else:
            current_ts_dt = current_ts # Already a pandas Timestamp

        # Ensure current_ts_dt is UTC if not already
        if current_ts_dt.tzinfo is None:
            current_ts_dt = current_ts_dt.tz_localize('UTC')
        elif current_ts_dt.tzinfo.utcoffset(current_ts_dt) != pd.Timedelta(0):
            current_ts_dt = current_ts_dt.tz_convert('UTC')
            
        frame_stats = {'top_7_day': None, 'top_30_day': None}

        for period_days, period_key in [(7, 'top_7_day'), (30, 'top_30_day')]:
            start_date = current_ts_dt - pd.Timedelta(days=period_days)
            
            # Filter plays within the window [start_date, current_ts_dt]
            window_df = df_for_stats[
                (df_for_stats['timestamp'] >= start_date) &
                (df_for_stats['timestamp'] <= current_ts_dt)
            ]

            if not window_df.empty:
                top_entity_in_window = window_df[entity_id_col].mode() # mode() gives most frequent
                
                if not top_entity_in_window.empty:
                    # mode() can return multiple if ties; pick the first one.
                    top_entity_id = top_entity_in_window.iloc[0] 
                    # Count plays for this specific top entity_id in the window
                    plays_count = window_df[window_df[entity_id_col] == top_entity_id].shape[0]
                    
                    if mode == "tracks":
                        original_names = entity_id_to_originals.get(top_entity_id, 
                                                                  {'original_artist': 'Unknown Artist', 'original_track': 'Unknown Track'})
                        frame_stats[period_key] = {
                            'song_id': top_entity_id,
                            'plays': plays_count,
                            'original_artist': original_names['original_artist'],
                            'original_track': original_names['original_track']
                        }
                    elif mode == "artists":
                        original_names = entity_id_to_originals.get(top_entity_id, 
                                                                  {'original_artist': 'Unknown Artist'})
                        frame_stats[period_key] = {
                            'artist_id': top_entity_id,
                            'plays': plays_count,
                            'original_artist': original_names['original_artist']
                        }
        
        rolling_stats_by_frame_timestamp[current_ts] = frame_stats
        processed_timestamps +=1
        if processed_timestamps % 100 == 0 or processed_timestamps == len(animation_frame_timestamps):
            print(f"Processed rolling stats for {processed_timestamps}/{len(animation_frame_timestamps)} animation timestamps.")

    print(f"--- Rolling Window Stats Calculation Complete for {mode} mode ---")
    return rolling_stats_by_frame_timestamp


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
        print(f"Columns in cleaned_data_spotify: {cleaned_data_spotify.columns.tolist()}") # Show columns
        
        race_data_spotify, s_details_map_spotify = prepare_data_for_bar_chart_race(cleaned_data_spotify, mode="tracks")
        
        # Test artist mode as well
        print("\n--- Testing Artist Mode Data Preparation (Spotify) ---")
        race_data_spotify_artists, artist_details_map_spotify = prepare_data_for_bar_chart_race(cleaned_data_spotify, mode="artists")
        
        if race_data_spotify is not None and not race_data_spotify.empty:
            print("\n--- Race Data (Spotify Source) ---")
            print(race_data_spotify.head())
            print(f"Shape of race_data: {race_data_spotify.shape}")
            print("\n--- Song Details Map (Spotify Source, first 2) ---")
            for i, (song, details) in enumerate(s_details_map_spotify.items()):
                if i >= 2: break
                print(f"'{song}': {details}")
                
        if race_data_spotify_artists is not None and not race_data_spotify_artists.empty:
            print("\n--- Artist Race Data (Spotify Source) ---")
            print(race_data_spotify_artists.head())
            print(f"Shape of artist race_data: {race_data_spotify_artists.shape}")
            print("\n--- Artist Details Map (Spotify Source, first 2) ---")
            for i, (artist, details) in enumerate(artist_details_map_spotify.items()):
                if i >= 2: break
                print(f"'{artist}': {details}")
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
        print(f"Columns in cleaned_data_lastfm: {cleaned_data_lastfm.columns.tolist()}") # Show columns

        race_data_lastfm, s_details_map_lastfm = prepare_data_for_bar_chart_race(cleaned_data_lastfm, mode="tracks")
        
        # Test artist mode for Last.fm as well
        print("\n--- Testing Artist Mode Data Preparation (Last.fm) ---")
        race_data_lastfm_artists, artist_details_map_lastfm = prepare_data_for_bar_chart_race(cleaned_data_lastfm, mode="artists")
        if race_data_lastfm is not None and not race_data_lastfm.empty:
            print("\n--- Race Data (Last.fm Source) ---")
            print(race_data_lastfm.head())
            print(f"Shape of race_data: {race_data_lastfm.shape}")
            print("\n--- Song Details Map (Last.fm Source, first 2) ---")
            for i, (song, details) in enumerate(s_details_map_lastfm.items()):
                if i >= 2: break
                print(f"'{song}': {details}")
                
        if race_data_lastfm_artists is not None and not race_data_lastfm_artists.empty:
            print("\n--- Artist Race Data (Last.fm Source) ---")
            print(race_data_lastfm_artists.head())
            print(f"Shape of artist race_data: {race_data_lastfm_artists.shape}")
            print("\n--- Artist Details Map (Last.fm Source, first 2) ---")
            for i, (artist, details) in enumerate(artist_details_map_lastfm.items()):
                if i >= 2: break
                print(f"'{artist}': {details}")
        else:
            print("Last.fm race data preparation resulted in empty or None DataFrame.")
    else:
        print("Last.fm data cleaning resulted in empty or None DataFrame (or was not configured to run).")