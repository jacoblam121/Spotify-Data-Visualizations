print("!!!!!!!!!! RUNNING MODIFIED ALBUM_ART_UTILS.PY !!!!!!!!!!!")

import requests
import json
import re
import os
from PIL import Image, ImageOps
from io import BytesIO
import time
from urllib.parse import quote
import base64

# --- Configuration Variables (will be initialized) ---
DEBUG_CACHE = True
USER_AGENT = "SpotifyRaceChart/1.0 default_email@example.com"
ART_CACHE_DIR = "album_art_cache" # Default, can be overridden
SPOTIFY_CLIENT_ID = "eaf67929214947d19e34182fb20e96bc" # Default, can be overridden
SPOTIFY_CLIENT_SECRET = "822e6e3f9d1149d4ad5520237d8385a3" # Default, can be overridden
NEGATIVE_CACHE_HOURS = 24 # Default, can be overridden

# --- Spotify API Configuration (mostly static, client ID/Secret can change) ---
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1/"

# --- Cache Files & Global Caches (paths will be dynamic based on ART_CACHE_DIR) ---
mbid_cache_file = None
dominant_color_cache_file = None
spotify_info_cache_file = None
negative_cache_file = None

mbid_cache = {}
dominant_color_cache = {}
spotify_info_cache = {}
negative_cache = {}  # Cache for failed searches with timestamp

_spotify_access_token_cache = {
    "token": None,
    "expires_at": 0
}

# --- Initialization Function ---
_config_initialized = False

def initialize_from_config(config):
    global DEBUG_CACHE, USER_AGENT, ART_CACHE_DIR
    global SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, NEGATIVE_CACHE_HOURS
    global mbid_cache_file, dominant_color_cache_file, spotify_info_cache_file, negative_cache_file
    global mbid_cache, dominant_color_cache, spotify_info_cache, negative_cache
    global _config_initialized

    if _config_initialized:
        if DEBUG_CACHE: print("[CACHE DEBUG] album_art_utils config already initialized.")
        return

    DEBUG_CACHE = config.get_bool('Debugging', 'DEBUG_CACHE_ALBUM_ART_UTILS', True)
    USER_AGENT = config.get('General', 'USER_AGENT', USER_AGENT) # Use existing as fallback
    ART_CACHE_DIR = config.get('AlbumArtSpotify', 'ART_CACHE_DIR', ART_CACHE_DIR)
    NEGATIVE_CACHE_HOURS = config.get_int('AlbumArtSpotify', 'NEGATIVE_CACHE_HOURS', NEGATIVE_CACHE_HOURS)

    # Spotify Credentials: Env Var -> Config File -> Hardcoded Default
    env_client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    env_client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    config_client_id = config.get('AlbumArtSpotify', 'SPOTIFY_CLIENT_ID', None)
    config_client_secret = config.get('AlbumArtSpotify', 'SPOTIFY_CLIENT_SECRET', None)

    SPOTIFY_CLIENT_ID = env_client_id or config_client_id or SPOTIFY_CLIENT_ID
    SPOTIFY_CLIENT_SECRET = env_client_secret or config_client_secret or SPOTIFY_CLIENT_SECRET
    
    if DEBUG_CACHE:
        print(f"[CONFIG DEBUG album_art_utils] Using SPOTIFY_CLIENT_ID: {'Loaded from Env/Config' if env_client_id or config_client_id else 'Using Default'}")
        print(f"[CONFIG DEBUG album_art_utils] NEGATIVE_CACHE_HOURS set to: {NEGATIVE_CACHE_HOURS}")

    if not os.path.exists(ART_CACHE_DIR):
        os.makedirs(ART_CACHE_DIR)
        if DEBUG_CACHE: print(f"[CACHE DEBUG] Created ART_CACHE_DIR: {ART_CACHE_DIR}")

    # Update cache file paths
    mbid_cache_file = os.path.join(ART_CACHE_DIR, "mbid_cache.json")
    dominant_color_cache_file = os.path.join(ART_CACHE_DIR, "dominant_color_cache.json")
    spotify_info_cache_file = os.path.join(ART_CACHE_DIR, "spotify_info_cache.json")
    negative_cache_file = os.path.join(ART_CACHE_DIR, "negative_cache.json")

    # Load caches (after paths are set)
    mbid_cache = load_json_cache(mbid_cache_file)
    dominant_color_cache = load_json_cache(dominant_color_cache_file)
    spotify_info_cache = load_json_cache(spotify_info_cache_file)
    negative_cache = load_json_cache(negative_cache_file)
    
    _config_initialized = True
    if DEBUG_CACHE: print("[CACHE DEBUG] album_art_utils configuration initialized.")


def load_json_cache(filepath):
    # DEBUG_CACHE might not be set correctly if this is called before initialize_from_config
    # So, we'll rely on its value at the time of calling.
    # Or, pass DEBUG_CACHE as an argument if it's critical before full init.
    # For now, let's assume initialize_from_config runs early enough.
    if DEBUG_CACHE: print(f"[CACHE DEBUG] Attempting to load cache from: {filepath}")
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if DEBUG_CACHE: print(f"[CACHE DEBUG] Loaded {len(data)} items from {filepath}")
                return data
        except json.JSONDecodeError:
            if DEBUG_CACHE: print(f"[CACHE DEBUG] JSONDecodeError for {filepath}. Returning empty cache.")
            return {}
    if DEBUG_CACHE: print(f"[CACHE DEBUG] Cache file {filepath} not found. Returning empty cache.")
    return {}

def save_json_cache(data, filepath):
    if DEBUG_CACHE: print(f"[CACHE DEBUG] Saving {len(data)} items to cache: {filepath}")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def is_negative_cache_valid(cache_key, hours_to_cache=None):
    """
    Check if a negative cache entry is still valid.
    Returns True if the entry exists and hasn't expired.
    """
    if hours_to_cache is None:
        hours_to_cache = NEGATIVE_CACHE_HOURS
        
    if cache_key not in negative_cache:
        return False
    
    cached_time = negative_cache[cache_key].get('timestamp', 0)
    current_time = time.time()
    expiry_time = cached_time + (hours_to_cache * 3600)
    
    if current_time > expiry_time:
        # Cache entry has expired, remove it
        if DEBUG_CACHE: print(f"[NEGATIVE CACHE DEBUG] Entry for '{cache_key}' has expired. Removing.")
        del negative_cache[cache_key]
        save_json_cache(negative_cache, negative_cache_file)
        return False
    
    if DEBUG_CACHE: print(f"[NEGATIVE CACHE DEBUG] Valid negative cache entry found for '{cache_key}'.")
    return True


def add_to_negative_cache(cache_key, reason="no_results"):
    """
    Add a failed search to the negative cache with current timestamp.
    """
    negative_cache[cache_key] = {
        'timestamp': time.time(),
        'reason': reason
    }
    save_json_cache(negative_cache, negative_cache_file)
    if DEBUG_CACHE: print(f"[NEGATIVE CACHE DEBUG] Added '{cache_key}' to negative cache. Reason: {reason}")


def _get_spotify_access_token():
    """
    Retrieves a Spotify API access token using Client Credentials Flow.
    Caches the token to minimize requests.
    """
    global _spotify_access_token_cache
    current_time = time.time()

    if _spotify_access_token_cache["token"] and _spotify_access_token_cache["expires_at"] > current_time:
        if DEBUG_CACHE: print("[SPOTIFY AUTH DEBUG] Using cached Spotify access token.")
        return _spotify_access_token_cache["token"]

    if DEBUG_CACHE: print("[SPOTIFY AUTH DEBUG] Requesting new Spotify access token.")
    
    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode('utf-8')).decode('utf-8')
    headers = {
        'Authorization': f"Basic {auth_header}",
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    payload = {
        'grant_type': 'client_credentials'
    }
    
    try:
        response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        
        _spotify_access_token_cache["token"] = token_data['access_token']
        _spotify_access_token_cache["expires_at"] = current_time + token_data['expires_in'] - 300 # 5 min buffer
        if DEBUG_CACHE: print(f"[SPOTIFY AUTH DEBUG] New token obtained. Expires in approx {token_data['expires_in']/60:.0f} minutes.")
        return _spotify_access_token_cache["token"]
    except requests.exceptions.RequestException as e:
        print(f"Error obtaining Spotify access token: {e}")
        return None
    except KeyError:
        print("Error parsing Spotify token response.")
        return None

def clean_artist_name_for_search(artist_name):
    """
    Clean artist names for better Spotify search compatibility.
    Handles quotes, special characters, and common variations.
    """
    import re  # Import at function level to avoid issues
    
    if not artist_name:
        return artist_name
        
    cleaned = artist_name
    
    # Remove escaped quotes and normalize quotes
    cleaned = cleaned.replace('\\"', '"').replace('"', '').replace('"', '').replace('"', '')
    
    # Handle common nickname patterns
    # "Joe "Bean" Esposito" -> "Joe Bean Esposito" and "Joe Esposito"
    variations = [cleaned]
    
    # If there are quotes around a nickname, create variations
    if '"' in artist_name:
        # Remove the quoted nickname entirely
        no_nickname = re.sub(r'\s*"[^"]*"\s*', ' ', cleaned).strip()
        variations.append(no_nickname)
    
    # Clean up extra spaces
    variations = [re.sub(r'\s+', ' ', v).strip() for v in variations]
    
    # Remove duplicates while preserving order
    unique_variations = []
    for v in variations:
        if v and v not in unique_variations:
            unique_variations.append(v)
    
    return unique_variations

def get_spotify_track_album_info(artist_name, track_name, album_name_hint):
    """
    Searches Spotify for a track and returns its album art URL, canonical album name,
    Spotify album ID, and Spotify artist IDs.
    Uses album_name_hint to disambiguate if multiple album versions exist.
    Tries simplified searches if the initial detailed search fails.
    """
    original_track_name = track_name 
    original_album_hint = album_name_hint
    
    # Sanitize artist name just once for internal use if it has extraneous quotes
    # This is a light sanitization; Spotify usually handles artist names well.
    # Keep original artist_name for display/logging if needed.
    internal_artist_name = artist_name.strip('"')

    # Generate cache key using CLEANED artist name for consistency
    artist_variations_for_cache = clean_artist_name_for_search(internal_artist_name)
    primary_clean_artist = artist_variations_for_cache[0] if artist_variations_for_cache else internal_artist_name

    cache_key = f"spotify_{primary_clean_artist.lower().strip()}_{original_track_name.lower().strip()}_{original_album_hint.lower().strip()}"
    
    print(f"\n--- [SPOTIFY_TRACE] Entering get_spotify_track_album_info ---")
    print(f"[SPOTIFY_TRACE] Called with (Original):")
    print(f"[SPOTIFY_TRACE]   Artist (original): '{artist_name}' (Using internally: '{internal_artist_name}')")
    print(f"[SPOTIFY_TRACE]   Track: '{original_track_name}'")
    print(f"[SPOTIFY_TRACE]   Album Hint: '{original_album_hint}'")
    print(f"[SPOTIFY_TRACE] Cache key generated (using cleaned artist '{primary_clean_artist}'): '{cache_key}'")

    force_api_call_for_this_song = False
    # # --- FOR DEBUGGING SPECIFIC TRACKS: UNCOMMENT AND MODIFY AS NEEDED ---
    # # if "kristen bell" in artist_name.lower() and "for the first time in forever" in original_track_name.lower():
    # #     print(f"[SPOTIFY_TRACE_FORCE] Matched criteria for '{artist_name} - {original_track_name}'. Forcing API call.")
    # #     force_api_call_for_this_song = True
    # # ---

    if not force_api_call_for_this_song:
        if DEBUG_CACHE: 
            print(f"[CACHE DEBUG] Spotify info check for key: '{cache_key}' (using cleaned artist name)")
        if cache_key in spotify_info_cache:
            cached_value = spotify_info_cache[cache_key]
            if DEBUG_CACHE: print(f"[CACHE DEBUG] Spotify Info Cache HIT. Value: {cached_value}")
            print(f"[SPOTIFY_TRACE] Cache HIT. Returning cached: {json.dumps(cached_value, indent=2, ensure_ascii=False) if cached_value is not None else 'None'}")
            print(f"--- [SPOTIFY_TRACE] Exiting get_spotify_track_album_info (from cache) ---\n")
            return cached_value
        
        # Check negative cache to avoid repeated failed API calls
        if is_negative_cache_valid(cache_key):
            print(f"[SPOTIFY_TRACE] Negative cache HIT. This search failed recently. Skipping API calls.")
            print(f"--- [SPOTIFY_TRACE] Exiting get_spotify_track_album_info (from negative cache) ---\n")
            spotify_info_cache[cache_key] = None  # Also cache as None in regular cache
            save_json_cache(spotify_info_cache, spotify_info_cache_file)
            return None
        else:
            if DEBUG_CACHE: print(f"[CACHE DEBUG] Spotify Info Cache MISS. Querying API.")
            print(f"[SPOTIFY_TRACE] Cache MISS. Proceeding to query API.")
    else:
        print(f"[SPOTIFY_TRACE_FORCE] Proceeding to query Spotify API (cache check bypassed).")

    access_token = _get_spotify_access_token()
    if not access_token:
        print(f"[SPOTIFY_TRACE] Failed to get Spotify access token. Caching None.")
        spotify_info_cache[cache_key] = None
        save_json_cache(spotify_info_cache, spotify_info_cache_file)
        print(f"--- [SPOTIFY_TRACE] Exiting (no access token, cached None) ---\n")
        return None

    # --- Build comprehensive search strategy ---
    search_queries_to_try = []
    
    # Clean artist names - get multiple variations (reuse the ones we calculated above)
    artist_variations = artist_variations_for_cache
    if DEBUG_CACHE:
        print(f"[ARTIST VARIATIONS] Original: '{internal_artist_name}' -> Variations: {artist_variations}")
    
    # --- Strategy 1: Precise Search with all artist variations ---
    for artist_var in artist_variations:
        search_queries_to_try.append((original_track_name, original_album_hint, artist_var, f"Precise Search (Artist: {artist_var})"))

    # --- Strategy 2: Enhanced Simplified Track Name Search ---
    # Expanded suffix patterns for better soundtrack/orchestral/instrumental coverage
    simplified_track_name = original_track_name
    common_suffixes = [
        " - from", " (from", " - soundtrack", " (soundtrack", 
        " - original motion picture soundtrack", " version",
        " - instrumental", " (instrumental", " - orchestral", " (orchestral",
        " - theme", " (theme", " - main theme", " (main theme",
        " - score", " (score", " - original score", " (original score",
        " - film version", " (film version", " - movie version", " (movie version)",
        " - extended", " (extended", " - reprise", " (reprise"
    ]
    
    for suffix in common_suffixes:
        if suffix.lower() in simplified_track_name.lower():
            simplified_track_name = simplified_track_name.lower().split(suffix.lower())[0].strip()
            # Attempt to restore original casing for the simplified part if possible (heuristic)
            if original_track_name.lower().startswith(simplified_track_name):
                 simplified_track_name = original_track_name[:len(simplified_track_name)]
            break # Take the first simplification that applies

    if simplified_track_name.lower() != original_track_name.lower():
        print(f"[SPOTIFY_TRACE] Original track name '{original_track_name}' was complex. Adding simplified track search for '{simplified_track_name}'.")
        for artist_var in artist_variations:
            search_queries_to_try.append((simplified_track_name, original_album_hint, artist_var, f"Simplified Track Search (Artist: {artist_var})"))

    # --- Strategy 3: Enhanced Soundtrack-specific strategies ---
    is_soundtrack = any(keyword in original_album_hint.lower() for keyword in [
        "soundtrack", "motion picture", "film", "movie", "original score", "theme"
    ])
    
    if is_soundtrack:
        print(f"[SPOTIFY_TRACE] Detected soundtrack album '{original_album_hint}'. Adding comprehensive soundtrack-specific searches.")
        
        # Try with simplified album name
        simplified_album = original_album_hint
        album_simplifiers = [
            " - original motion picture soundtrack", " (original motion picture soundtrack)",
            " - soundtrack", " (soundtrack)", " - original soundtrack", " (original soundtrack)",
            " - film soundtrack", " (film soundtrack)", " - movie soundtrack", " (movie soundtrack)",
            " - original score", " (original score)", " - score", " (score)"
        ]
        
        for simplifier in album_simplifiers:
            if simplifier.lower() in simplified_album.lower():
                simplified_album = simplified_album.lower().split(simplifier.lower())[0].strip()
                if original_album_hint.lower().startswith(simplified_album):
                    simplified_album = original_album_hint[:len(simplified_album)]
                break
        
        # Extract core movie/show title (e.g., "The Karate Kid" from "The Karate Kid: The Original Motion Picture Soundtrack")
        core_title = simplified_album
        if ":" in core_title:
            core_title = core_title.split(":")[0].strip()
        
        # Strategy 3A: Simplified album with original artists
        if simplified_album.lower() != original_album_hint.lower():
            for artist_var in artist_variations:
                search_queries_to_try.append((simplified_track_name, simplified_album, artist_var, f"Simplified Soundtrack Search (Artist: {artist_var})"))
        
        # Strategy 3B: Core movie title with original artists  
        if core_title.lower() != simplified_album.lower():
            for artist_var in artist_variations:
                search_queries_to_try.append((simplified_track_name, core_title, artist_var, f"Core Title Search (Artist: {artist_var})"))
        
        # Strategy 3C: Various Artists approach (common for soundtracks)
        search_queries_to_try.append((simplified_track_name, simplified_album, "Various Artists", "Soundtrack Various Artists Search"))
        search_queries_to_try.append((simplified_track_name, core_title, "Various Artists", "Core Title Various Artists Search"))
        
        # Strategy 3D: No artist specified, album-focused search
        search_queries_to_try.append((simplified_track_name, simplified_album, "", "Album-Focused Soundtrack Search"))
        search_queries_to_try.append((simplified_track_name, core_title, "", "Core Title Album-Focused Search"))
        
        # Strategy 3E: Track + movie title only (very broad)
        search_queries_to_try.append((simplified_track_name, "", "", f"Track-Only Search"))

    # --- Strategy 4: Aggressive Fallback Searches ---
    # Extract just the core track name (remove everything after first dash or parenthesis)
    basic_track_name = simplified_track_name
    if " - " in basic_track_name:
        basic_track_name = basic_track_name.split(" - ")[0].strip()
    elif " (" in basic_track_name:
        basic_track_name = basic_track_name.split(" (")[0].strip()
    
    if basic_track_name.lower() != simplified_track_name.lower():
        # Try basic track name with all artist variations
        for artist_var in artist_variations:
            search_queries_to_try.append((basic_track_name, original_album_hint, artist_var, f"Basic Core Search (Artist: {artist_var})"))
        
        # Try basic track name with no artist (very broad)
        search_queries_to_try.append((basic_track_name, "", "", "Basic Track-Only Search"))

    final_result_from_api = None

    for current_track_to_search, current_album_hint_to_use, current_artist_to_use, search_type_label in search_queries_to_try:
        print(f"\n[SPOTIFY_TRACE] --- Attempting {search_type_label} ---")
        print(f"[SPOTIFY_TRACE] Using Track for search: '{current_track_to_search}'")
        print(f"[SPOTIFY_TRACE] Using Album Hint for matching: '{current_album_hint_to_use}'")
        print(f"[SPOTIFY_TRACE] Using Artist for search: '{current_artist_to_use}'")

        # Build query - use artist if provided, otherwise search more broadly
        if current_artist_to_use:
            query_params = f'track:"{quote(current_track_to_search)}" artist:"{quote(current_artist_to_use)}"'
        else:
            query_params = f'track:"{quote(current_track_to_search)}"'
            if current_album_hint_to_use:
                query_params += f' album:"{quote(current_album_hint_to_use)}"'
        
        url = f"{SPOTIFY_API_BASE_URL}search?q={query_params}&type=track&limit=10"
        
        print(f"[SPOTIFY_TRACE] Constructed Spotify API URL ({search_type_label}): {url}")
        headers = {'Authorization': f"Bearer {access_token}", 'User-Agent': USER_AGENT}
        print(f"Spotify API call ({search_type_label}) for: Artist='{current_artist_to_use}', Track='{current_track_to_search}', Album Hint='{current_album_hint_to_use}'")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            print(f"[SPOTIFY_TRACE] Spotify API call successful ({search_type_label}, HTTP Status: {response.status_code}).")
            if data.get('tracks') and data['tracks'].get('items'):
                 print(f"[SPOTIFY_TRACE] Raw Response (Tracks Items, {search_type_label}): {json.dumps(data['tracks']['items'], indent=2, ensure_ascii=False)}")
            # ... (other raw response prints if needed) ...

            if data.get('tracks') and data['tracks'].get('items'):
                items = data['tracks']['items']
                best_match = None
                normalized_album_hint = current_album_hint_to_use.lower().strip() if current_album_hint_to_use else ""
                
                for i, item in enumerate(items):
                    spotify_album_name_original = item.get('album', {}).get('name', '')
                    spotify_album_name_lower = spotify_album_name_original.lower().strip()
                    
                    # Enhanced matching logic for soundtracks
                    if normalized_album_hint:
                        # Direct match
                        if normalized_album_hint in spotify_album_name_lower or spotify_album_name_lower in normalized_album_hint:
                            best_match = item
                            print(f"[SPOTIFY_TRACE] ({search_type_label}) MATCHED Item {i} based on album hint. Selected.")
                            break
                        # Soundtrack-specific matching (more flexible)
                        elif is_soundtrack:
                            # Check if core album names match (ignoring soundtrack suffixes)
                            album_core = normalized_album_hint.replace("soundtrack", "").replace("original motion picture", "").strip()
                            spotify_core = spotify_album_name_lower.replace("soundtrack", "").replace("original motion picture", "").strip()
                            if album_core and spotify_core and (album_core in spotify_core or spotify_core in album_core):
                                best_match = item
                                print(f"[SPOTIFY_TRACE] ({search_type_label}) MATCHED Item {i} based on core album name similarity. Selected.")
                                break
                
                if not best_match and items:
                    best_match = items[0] # Fallback to first item if no hint match
                    print(f"[SPOTIFY_TRACE] ({search_type_label}) No album hint match. Taking first result.")

                if best_match:
                    album_info = best_match.get('album', {})
                    art_url = album_info.get('images', [{}])[0].get('url') if album_info.get('images') else None
                    
                    if art_url: # Found art with this search query!
                        print(f"[SPOTIFY_TRACE] ({search_type_label}) SUCCESS! Found art_url: {art_url}")
                        final_result_from_api = {
                            "art_url": art_url,
                            "canonical_album_name": album_info.get('name'),
                            "spotify_album_id": album_info.get('id'),
                            "spotify_artist_ids": [a['id'] for a in best_match.get('artists', []) if a.get('id')],
                            "source": f"spotify ({search_type_label})"
                        }
                        break # Exit the loop of search_queries_to_try, we found a good result
                    else:
                        print(f"[SPOTIFY_TRACE] ({search_type_label}) Found a best_match, but it has no art_url.")
            else: # No items in response
                print(f"[SPOTIFY_TRACE] ({search_type_label}) No 'items' in Spotify response.")
        
        except requests.exceptions.RequestException as e:
            print(f"[SPOTIFY_TRACE] ({search_type_label}) RequestException: {e}")
            # Potentially break or continue to next search type depending on error
        except json.JSONDecodeError as e_json:
            print(f"[SPOTIFY_TRACE] ({search_type_label}) JSONDecodeError: {e_json}")
        
        time.sleep(0.2) # Respect API limits between different search attempts for the same track

    # After trying all search queries:
    if final_result_from_api:
        print(f"Found Spotify info via {final_result_from_api['source']}: Album='{final_result_from_api['canonical_album_name']}', Art URL: {'Yes' if final_result_from_api['art_url'] else 'No'}")
        print(f"[SPOTIFY_TRACE] Caching and returning result (from {final_result_from_api['source']}): {json.dumps(final_result_from_api, indent=2, ensure_ascii=False)}")
    else:
        print(f"No suitable track found on Spotify after all attempts for: Original Track='{original_track_name}', Artist='{artist_name}'")
        print(f"[SPOTIFY_TRACE] Caching None after all search attempts failed.")
        # Add to negative cache to avoid repeated failed searches
        add_to_negative_cache(cache_key, f"no_spotify_results_after_{len(search_queries_to_try)}_attempts")
    
    spotify_info_cache[cache_key] = final_result_from_api # Cache the final result (or None) under the original key
    save_json_cache(spotify_info_cache, spotify_info_cache_file)
    print(f"--- [SPOTIFY_TRACE] Exiting get_spotify_track_album_info (after API attempt(s)) ---\n")
    return final_result_from_api

# --- MusicBrainz Functions (Now Legacy/Fallback - Commented out primary usage) ---
def get_release_mbid(artist_name, album_name):
    # This function is now effectively deprecated for primary use.
    # Kept for reference or potential future fallback.
    # If called, it will still use its own mbid_cache.
    # Consider adding a warning or always returning None if you fully deprecate.
    if DEBUG_CACHE: print(f"[MBID DEPRECATED] get_release_mbid called for '{artist_name} - {album_name}'. Spotify is primary.")
    
    # --- Original MBID logic ---
    cache_key = f"{artist_name.lower().strip()}_{album_name.lower().strip()}"
    if DEBUG_CACHE: print(f"[CACHE DEBUG] MBID check for key: '{cache_key}' (Artist: '{artist_name}', Album: '{album_name}')")
    
    if cache_key in mbid_cache:
        if DEBUG_CACHE: print(f"[CACHE DEBUG] MBID Cache HIT for key: '{cache_key}'. Value: {mbid_cache[cache_key]}")
        return mbid_cache[cache_key]
    
    if DEBUG_CACHE: print(f"[CACHE DEBUG] MBID Cache MISS for key: '{cache_key}'. Querying API.")
    print(f"MBID API call for: {artist_name} - {album_name}")
    search_query = f'artist:"{quote(artist_name)}" AND release:"{quote(album_name)}"'
    url = f"https://musicbrainz.org/ws/2/release/?query={search_query}&fmt=json"
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() 
        data = response.json()
        if data.get('releases') and len(data['releases']) > 0:
            releases = sorted(data['releases'], 
                              key=lambda r: (
                                  r.get('status', '').lower() != 'official', 
                                  r.get('release-group', {}).get('primary-type', '').lower() != 'album', 
                                  -r.get('score', 0) 
                                ))
            best_release = releases[0]
            release_mbid = best_release['id']
            mbid_cache[cache_key] = release_mbid 
            save_json_cache(mbid_cache, mbid_cache_file) 
            print(f"Found MBID: {release_mbid} for {artist_name} - {album_name}")
            time.sleep(1) 
            return release_mbid
        else:
            print(f"No MBID found for {artist_name} - {album_name}")
            mbid_cache[cache_key] = None 
            save_json_cache(mbid_cache, mbid_cache_file)
            time.sleep(1)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching MBID for {artist_name} - {album_name}: {e}")
        time.sleep(1)
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON response for MBID of {artist_name} - {album_name}")
        time.sleep(1)
        return None

def get_album_art_url(release_mbid):
    # This function is now effectively deprecated for primary use.
    # Kept for reference or potential future fallback.
    if DEBUG_CACHE: print(f"[CAA DEPRECATED] get_album_art_url called for MBID '{release_mbid}'. Spotify is primary.")
    
    # --- Original CAA logic ---
    if not release_mbid: return None
    print(f"CAA API call for MBID: {release_mbid}")
    url = f"https://coverartarchive.org/release/{release_mbid}"
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 404:
            print(f"No cover art found on CAA for MBID: {release_mbid}")
            return None
        response.raise_for_status()
        data = response.json()
        for image in data.get('images', []):
            if image.get('front', False) and image.get('thumbnails'):
                # Prefer 'small' for consistency with previous, but 'image' is full res
                return image['thumbnails'].get('small', image.get('image')) 
        print(f"No 'front' image URL found for MBID: {release_mbid}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching album art URL for MBID {release_mbid}: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON response for cover art of MBID {release_mbid}")
        return None
# --- End MusicBrainz/CAA Legacy ---


def download_image_to_cache(image_url, album_name_for_file, artist_name_for_file):
    """
    Downloads an image from image_url and saves it to the ART_CACHE_DIR.
    Uses album_name_for_file and artist_name_for_file to create a unique filename.
    Returns the local path to the downloaded image, or None on failure.
    """
    if not image_url:
        return None

    # Sanitize names for filename (using provided names, ideally canonical from Spotify)
    safe_album_name = "".join(c if c.isalnum() or c in " .-_" else "_" for c in str(album_name_for_file).strip())[:50]
    safe_artist_name = "".join(c if c.isalnum() or c in " .-_" else "_" for c in str(artist_name_for_file).strip())[:50]
    
    filename_base = f"{safe_artist_name}_{safe_album_name}"
    try:
        # Attempt to get extension from URL, fallback to .jpg
        extension = os.path.splitext(image_url.split('?')[0])[-1].lower()
        if not extension or len(extension) > 5 or len(extension) < 2 or not extension.startswith('.'):
            extension = ".jpg"
    except:
        extension = ".jpg"

    cached_image_path = os.path.join(ART_CACHE_DIR, filename_base + extension)
    if DEBUG_CACHE: print(f"[CACHE DEBUG] Image check for path: '{cached_image_path}' (URL: {image_url})")

    if os.path.exists(cached_image_path):
        if DEBUG_CACHE: print(f"[CACHE DEBUG] Image Cache HIT: '{cached_image_path}'")
        return cached_image_path
    
    if DEBUG_CACHE: print(f"[CACHE DEBUG] Image Cache MISS: '{cached_image_path}'. Downloading image.")
    print(f"Downloading image: {image_url} to {cached_image_path}")
    headers = {'User-Agent': USER_AGENT} # Some image hosts might check User-Agent
    try:
        response = requests.get(image_url, headers=headers, stream=True, timeout=15)
        response.raise_for_status()
        with open(cached_image_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return cached_image_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image {image_url}: {e}")
        if os.path.exists(cached_image_path): # Clean up partial download
            try:
                os.remove(cached_image_path)
            except OSError as oe:
                print(f"Error removing partially downloaded file {cached_image_path}: {oe}")
        return None

def get_dominant_color(image_path, palette_size=1):
    # This function remains largely unchanged, but ensure its cache key is robust
    # It uses the basename of the image_path, which should be fine as download_image_to_cache creates unique names
    cache_key = os.path.basename(image_path)
    if DEBUG_CACHE: print(f"[CACHE DEBUG] Dominant color check for key: '{cache_key}'")

    if cache_key in dominant_color_cache:
        if DEBUG_CACHE: print(f"[CACHE DEBUG] Dominant Color Cache HIT for '{cache_key}'. Value: {dominant_color_cache[cache_key]}")
        # Ensure it returns a tuple, as cache stores a list
        return tuple(dominant_color_cache[cache_key])

    if DEBUG_CACHE: print(f"[CACHE DEBUG] Dominant Color Cache MISS for '{cache_key}'. Calculating color.")
    if not image_path or not os.path.exists(image_path):
        # Default color if no image or path issue
        dominant_color_cache[cache_key] = [128, 128, 128] 
        save_json_cache(dominant_color_cache, dominant_color_cache_file)
        return (128, 128, 128) 
    try:
        img = Image.open(image_path).convert('RGB')
        # Resize for faster processing, MEDIANCUT is good for dominant color
        img.thumbnail((100, 100)) 
        # Using a slightly larger palette size for quantize can sometimes yield better representative colors
        paletted = img.quantize(colors=palette_size * 5, method=Image.Quantize.MEDIANCUT) # Or Image.Quantize.FASTOCTREE
        palette = paletted.getpalette() # Palette is flattened list: [R1,G1,B1, R2,G2,B2, ...]
        
        color_counts = sorted(paletted.getcolors(), reverse=True) # List of (count, index)
        
        if not color_counts: # Should not happen with RGB image but good check
            dominant_color_cache[cache_key] = [128, 128, 128]
            save_json_cache(dominant_color_cache, dominant_color_cache_file)
            return (128, 128, 128)

        dominant_color_index = color_counts[0][1] # Index in the palette
        
        # Extract RGB from palette
        r = palette[dominant_color_index * 3]
        g = palette[dominant_color_index * 3 + 1]
        b = palette[dominant_color_index * 3 + 2]
        
        dominant_rgb = (r, g, b)
        dominant_color_cache[cache_key] = list(dominant_rgb) # Store as list in JSON
        save_json_cache(dominant_color_cache, dominant_color_cache_file)
        return dominant_rgb
    except Exception as e:
        print(f"Error getting dominant color for {image_path}: {e}")
        # Cache default color on error to avoid re-processing problematic image
        dominant_color_cache[cache_key] = [128, 128, 128]
        save_json_cache(dominant_color_cache, dominant_color_cache_file)
        return (128, 128, 128)


def get_album_art_path(artist_name, track_name, album_name_from_lastfm):
    """
    Main function to get local album art path.
    Uses Spotify API first.
    artist_name: From Last.fm data
    track_name: From Last.fm data
    album_name_from_lastfm: Album name as reported by Last.fm (used as a hint for Spotify)
    """
    print(f"Attempting to get art path for: Artist='{artist_name}', Track='{track_name}', Album (Last.fm)='{album_name_from_lastfm}'")
    
    spotify_data = get_spotify_track_album_info(artist_name, track_name, album_name_from_lastfm)

    if spotify_data and spotify_data.get("art_url"):
        art_url = spotify_data["art_url"]
        # Use canonical album name from Spotify for file naming if available, else fallback to Last.fm's
        album_name_for_file = spotify_data.get("canonical_album_name", album_name_from_lastfm)
        # Could also use a primary artist name from Spotify if we fetched it
        artist_name_for_file = artist_name 
        
        return download_image_to_cache(art_url, album_name_for_file, artist_name_for_file)
    else:
        if spotify_data: # Spotify responded but no art URL
            print(f"Spotify found info for '{artist_name} - {track_name}' but no art URL.")
        else: # Spotify API call failed or found no match
            print(f"No Spotify info or art URL found for '{artist_name} - {track_name}'.")
        
        # ---- START: Optional Fallback to MusicBrainz (currently disabled by commenting out calls) ----
        # print(f"Attempting fallback to MusicBrainz for: {artist_name} - {album_name_from_lastfm}")
        # release_mbid = get_release_mbid(artist_name, album_name_from_lastfm) # Uses original album name for MB
        # if not release_mbid:
        #     print(f"Fallback: No MBID for {artist_name} - {album_name_from_lastfm}")
        #     return None
        # art_url_mb = get_album_art_url(release_mbid)
        # if not art_url_mb:
        #     print(f"Fallback: No art URL from CAA for {artist_name} - {album_name_from_lastfm}")
        #     return None
        # print(f"Fallback: Using MusicBrainz/CAA art for {artist_name} - {album_name_from_lastfm}")
        # return download_image_to_cache(art_url_mb, album_name_from_lastfm, artist_name) # Use original names for MB path
        # ---- END: Optional Fallback ----
        
        return None


if __name__ == "__main__":
    # To test album_art_utils.py standalone, we need to load the configuration first.
    # This requires config_loader.py to be in the same directory or accessible via Python's path.
    print("--- Testing album_art_utils.py Standalone ---")
    
    # Attempt to import AppConfig and initialize
    try:
        from config_loader import AppConfig
        print("Imported AppConfig from config_loader.")
        
        # Create a config object. Assumes configurations.txt is in the parent directory 
        # or the same directory if you copy it for testing.
        # If album_art_utils.py is in a subdirectory, you might need to adjust path to configurations.txt
        # For simplicity, let's assume configurations.txt is accessible.
        try:
            config = AppConfig(filepath="configurations.txt") # Adjust path if necessary
            print("AppConfig instance created. Initializing album_art_utils...")
            initialize_from_config(config) # This is crucial
            print("album_art_utils initialized with configuration.")
        except FileNotFoundError:
            print("CRITICAL: configurations.txt not found. Cannot run standalone test effectively.")
            print("Please ensure configurations.txt is in the correct location (e.g., project root).")
            exit()
        except Exception as e:
            print(f"Error initializing AppConfig or album_art_utils: {e}")
            exit()

    except ImportError:
        print("CRITICAL: Could not import AppConfig from config_loader.py.")
        print("Ensure config_loader.py is in the same directory or Python's sys.path.")
        exit()
    except Exception as e:
        print(f"An unexpected error occurred during setup: {e}")
        exit()

    print(f"\nConfiguration check within album_art_utils:")
    print(f"DEBUG_CACHE set to: {DEBUG_CACHE}")
    print(f"USER_AGENT set to: {USER_AGENT}")
    print(f"ART_CACHE_DIR set to: {ART_CACHE_DIR}")
    print(f"SPOTIFY_CLIENT_ID seems: {'Set (from env/config)' if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_ID not in ['YOUR_CLIENT_ID', 'eaf67929214947d19e34182fb20e96bc'] else 'Likely Default/Placeholder'}")


    # --- Test Cases ---
    # These are similar to your original test cases but will now use the config-driven settings.
    
    # Test 1: A well-known track
    test_artist_1 = "Taylor Swift"
    test_track_1 = "Cruel Summer"
    test_album_1_hint = "Lover"
    print(f"\n[STANDALONE TEST 1] With: {test_artist_1} - {test_track_1} (Album Hint: {test_album_1_hint})")
    
    # The function get_album_art_path is what main_animator calls.
    # It internally calls get_spotify_track_album_info and download_image_to_cache.
    art_path_data_1 = get_album_art_path(test_artist_1, test_track_1, test_album_1_hint)
    
    art_path_1 = None
    if isinstance(art_path_data_1, str) and art_path_data_1:
        art_path_1 = art_path_data_1
    elif isinstance(art_path_data_1, dict) and art_path_data_1.get("art_path"): # If you update get_album_art_path later
        art_path_1 = art_path_data_1["art_path"]
        print(f"Canonical album name from Spotify: {art_path_data_1.get('canonical_album_name')}")

    print(f"Art path for {test_track_1}: {art_path_1}")
    if art_path_1 and os.path.exists(art_path_1):
        dom_color_1 = get_dominant_color(art_path_1)
        print(f"Dominant color for {test_track_1} (RGB): {dom_color_1}")
    elif art_path_1:
        print(f"Warning: Art path {art_path_1} was returned but file does not exist.")

    # Test 2: A track that might have multiple album versions
    test_artist_2 = "Paramore"
    test_track_2 = "Misery Business"
    test_album_2_hint = "Riot!"
    print(f"\n[STANDALONE TEST 2] With: {test_artist_2} - {test_track_2} (Album Hint: {test_album_2_hint})")
    art_path_data_2 = get_album_art_path(test_artist_2, test_track_2, test_album_2_hint)
    
    art_path_2 = None
    if isinstance(art_path_data_2, str) and art_path_data_2:
        art_path_2 = art_path_data_2
    elif isinstance(art_path_data_2, dict) and art_path_data_2.get("art_path"):
        art_path_2 = art_path_data_2["art_path"]

    print(f"Art path for {test_track_2}: {art_path_2}")
    if art_path_2 and os.path.exists(art_path_2):
        dom_color_2 = get_dominant_color(art_path_2)
        print(f"Dominant color for {test_track_2} (RGB): {dom_color_2}")

    # Test 3: Potentially problematic (non-Latin characters)
    test_artist_3 = "ヨルシカ"
    test_track_3 = "晴る"
    test_album_3_hint = "幻燈"
    print(f"\n[STANDALONE TEST 3] With: {test_artist_3} - {test_track_3} (Album Hint: {test_album_3_hint})")
    art_path_data_3 = get_album_art_path(test_artist_3, test_track_3, test_album_3_hint)

    art_path_3 = None
    if isinstance(art_path_data_3, str) and art_path_data_3:
        art_path_3 = art_path_data_3
    elif isinstance(art_path_data_3, dict) and art_path_data_3.get("art_path"):
        art_path_3 = art_path_data_3["art_path"]

    print(f"Art path for {test_track_3} by {test_artist_3}: {art_path_3}")
    if art_path_3 and os.path.exists(art_path_3):
        dom_color_3 = get_dominant_color(art_path_3)
        print(f"Dominant color for {test_track_3} (RGB): {dom_color_3}")

    # Test 4: Cache hit test (re-run Test 1)
    print(f"\n[STANDALONE TEST 4] Cache Re-Test for: {test_artist_1} - {test_track_1}")
    art_path_data_1_again = get_album_art_path(test_artist_1, test_track_1, test_album_1_hint)
    
    art_path_1_again_val = None
    if isinstance(art_path_data_1_again, str) and art_path_data_1_again:
         art_path_1_again_val = art_path_data_1_again
    elif isinstance(art_path_data_1_again, dict) and art_path_data_1_again.get("art_path"):
        art_path_1_again_val = art_path_data_1_again["art_path"]

    print(f"Art path (2nd call): {art_path_1_again_val}")
    if art_path_1_again_val and os.path.exists(art_path_1_again_val):
        dom_color_1_again = get_dominant_color(art_path_1_again_val) # Should hit dominant color cache
        print(f"Dominant color (2nd call): {dom_color_1_again}")


    print("\n--- Standalone Test Complete ---")
    print(f"Check the '{ART_CACHE_DIR}' folder for new images and JSON cache files.")
    print("Review console output for [CACHE DEBUG], [SPOTIFY AUTH DEBUG], etc., messages.")
    print("Ensure these messages respect the DEBUG_CACHE_ALBUM_ART_UTILS setting in configurations.txt.")