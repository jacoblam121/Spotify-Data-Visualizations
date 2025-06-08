# Debug printing helper controlled by DEBUG_CACHE
DEBUG_CACHE = False

def _debug_print(*args, **kwargs):
    if DEBUG_CACHE:
        print(*args, **kwargs)

_debug_print("Running one instance")

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
DEBUG_CACHE = False
USER_AGENT = "SpotifyRaceChart/1.0 default_email@example.com"
ART_CACHE_DIR = "album_art_cache" # Default, can be overridden
ARTIST_ART_CACHE_DIR = "artist_art_cache" # Default, can be overridden
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
spotify_artist_cache_file = None  # New cache file for Spotify artist info
negative_cache_file = None
mb_album_info_cache_file = None # New cache file for MB album info

mbid_cache = {}
dominant_color_cache = {}
spotify_info_cache = {}
spotify_artist_cache = {}  # New cache for Spotify artist info
negative_cache = {}  # Cache for failed searches with timestamp
mb_album_info_cache = {} # New cache for MB album info

_spotify_access_token_cache = {
    "token": None,
    "expires_at": 0
}

# --- Initialization Function ---
_config_initialized = False

def initialize_from_config(config):
    global DEBUG_CACHE, USER_AGENT, ART_CACHE_DIR, ARTIST_ART_CACHE_DIR
    global SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, NEGATIVE_CACHE_HOURS
    global mbid_cache_file, dominant_color_cache_file, spotify_info_cache_file, spotify_artist_cache_file, negative_cache_file, mb_album_info_cache_file
    global mbid_cache, dominant_color_cache, spotify_info_cache, spotify_artist_cache, negative_cache, mb_album_info_cache
    global _config_initialized

    if _config_initialized:
        if DEBUG_CACHE: print("[CACHE DEBUG] album_art_utils config already initialized.")
        return

    DEBUG_CACHE = config.get_bool('Debugging', 'DEBUG_CACHE_ALBUM_ART_UTILS', DEBUG_CACHE)
    USER_AGENT = config.get('General', 'USER_AGENT', USER_AGENT) # Use existing as fallback
    ART_CACHE_DIR = config.get('AlbumArtSpotify', 'ART_CACHE_DIR', ART_CACHE_DIR)
    ARTIST_ART_CACHE_DIR = config.get('AlbumArtSpotify', 'ARTIST_ART_CACHE_DIR', ARTIST_ART_CACHE_DIR)
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

    # Create both cache directories
    if not os.path.exists(ART_CACHE_DIR):
        os.makedirs(ART_CACHE_DIR)
        if DEBUG_CACHE: print(f"[CACHE DEBUG] Created ART_CACHE_DIR: {ART_CACHE_DIR}")
    
    if not os.path.exists(ARTIST_ART_CACHE_DIR):
        os.makedirs(ARTIST_ART_CACHE_DIR)
        if DEBUG_CACHE: print(f"[CACHE DEBUG] Created ARTIST_ART_CACHE_DIR: {ARTIST_ART_CACHE_DIR}")

    # Update cache file paths - Album art files stay in ART_CACHE_DIR
    mbid_cache_file = os.path.join(ART_CACHE_DIR, "mbid_cache.json")
    dominant_color_cache_file = os.path.join(ART_CACHE_DIR, "dominant_color_cache.json")
    spotify_info_cache_file = os.path.join(ART_CACHE_DIR, "spotify_info_cache.json")
    negative_cache_file = os.path.join(ART_CACHE_DIR, "negative_cache.json")
    mb_album_info_cache_file = os.path.join(ART_CACHE_DIR, "mb_album_info_cache.json")
    
    # Artist-specific cache files go in ARTIST_ART_CACHE_DIR
    spotify_artist_cache_file = os.path.join(ARTIST_ART_CACHE_DIR, "spotify_artist_cache.json")

    # Load caches (after paths are set)
    mbid_cache = load_json_cache(mbid_cache_file)
    dominant_color_cache = load_json_cache(dominant_color_cache_file)
    spotify_info_cache = load_json_cache(spotify_info_cache_file)
    spotify_artist_cache = load_json_cache(spotify_artist_cache_file)  # Load new artist cache
    negative_cache = load_json_cache(negative_cache_file)
    mb_album_info_cache = load_json_cache(mb_album_info_cache_file) # Load new cache
    
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

def get_spotify_track_album_info(artist_name, track_name, album_name_hint, spotify_track_uri=None):
    """
    Searches Spotify for a track and returns its album art URL, canonical album name,
    Spotify album ID, and Spotify artist IDs.
    Uses album_name_hint to disambiguate if multiple album versions exist.
    Tries simplified searches if the initial detailed search fails.
    If spotify_track_uri is provided, it attempts a direct lookup first.
    """
    original_track_name = track_name 
    original_album_hint = album_name_hint
    
    _debug_print(f"\n--- [SPOTIFY_TRACE] Entering get_spotify_track_album_info --- ")
    _debug_print(f"[SPOTIFY_TRACE] Called with (Original): Artist='{artist_name}', Track='{original_track_name}', Album Hint='{original_album_hint}', URI='{spotify_track_uri}'")

    access_token = _get_spotify_access_token()
    if not access_token:
        _debug_print(f"[SPOTIFY_TRACE] Failed to get Spotify access token. Cannot proceed.")
        # No specific cache key to save under here, as failure is general
        _debug_print(f"--- [SPOTIFY_TRACE] Exiting (no access token) ---\\\n")
        return None

    final_result_to_return = None # Define this at a higher scope

    # --- Priority 1: Direct URI Lookup (if spotify_track_uri is provided) ---
    if spotify_track_uri:
        try:
            track_id = spotify_track_uri.split(':')[-1]
            uri_cache_key = f"spotify_tracklookup_{track_id}"
            _debug_print(f"[SPOTIFY_TRACE] URI provided. Attempting direct lookup with track_id: '{track_id}', cache_key: '{uri_cache_key}'")

            if DEBUG_CACHE: print(f"[CACHE DEBUG] Spotify URI Lookup check for key: '{uri_cache_key}'")
            if uri_cache_key in spotify_info_cache:
                cached_value = spotify_info_cache[uri_cache_key]
                if DEBUG_CACHE: print(f"[CACHE DEBUG] Spotify URI Lookup Cache HIT. Value: {cached_value}")
                _debug_print(f"[SPOTIFY_TRACE] URI Lookup Cache HIT. Returning cached: {json.dumps(cached_value, indent=2, ensure_ascii=False) if cached_value is not None else 'None'}")
                _debug_print(f"--- [SPOTIFY_TRACE] Exiting get_spotify_track_album_info (from URI cache) ---\\\n")
                return cached_value
            
            if is_negative_cache_valid(uri_cache_key):
                _debug_print(f"[SPOTIFY_TRACE] Negative cache HIT for URI lookup '{uri_cache_key}'. This search failed recently. Skipping API call.")
                _debug_print(f"--- [SPOTIFY_TRACE] Exiting get_spotify_track_album_info (from URI negative cache) ---\\\n")
                spotify_info_cache[uri_cache_key] = None 
                save_json_cache(spotify_info_cache, spotify_info_cache_file)
                return None
            
            if DEBUG_CACHE: print(f"[CACHE DEBUG] Spotify URI Lookup Cache MISS for '{uri_cache_key}'. Querying API.")

            url = f"{SPOTIFY_API_BASE_URL}tracks/{track_id}"
            headers = {'Authorization': f"Bearer {access_token}", 'User-Agent': USER_AGENT}
            _debug_print(f"Spotify API call (Direct Track Lookup) for URI: {spotify_track_uri}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            track_data = response.json()
            _debug_print(f"[SPOTIFY_TRACE] Spotify API Direct Track Lookup successful (HTTP Status: {response.status_code}).")

            if track_data and track_data.get('album'):
                album_info_from_uri = track_data['album']
                art_url_from_uri = album_info_from_uri.get('images', [{}])[0].get('url') if album_info_from_uri.get('images') else None
                
                uri_lookup_result = None
                if art_url_from_uri:
                    uri_lookup_result = {
                        "art_url": art_url_from_uri,
                        "canonical_album_name": album_info_from_uri.get('name'),
                        "spotify_album_id": album_info_from_uri.get('id'),
                        "spotify_artist_ids": [a['id'] for a in track_data.get('artists', []) if a.get('id')],
                        "album_type": album_info_from_uri.get('album_type'), # Store album_type
                        "source": "spotify (uri_lookup)"
                    }
                    _debug_print(f"[SPOTIFY_TRACE] SUCCESS via URI Lookup! Found art_url: {art_url_from_uri}, Album Type: {uri_lookup_result['album_type']}")
                    final_result_to_return = uri_lookup_result # Tentatively set this as the result
                else:
                    _debug_print(f"[SPOTIFY_TRACE] URI Lookup successful for track '{track_data.get('name')}\' on album '{album_info_from_uri.get('name')}\', but this album entry has NO ART IMAGES LISTED on Spotify.")
                    # Cache that this specific URI lookup yielded an album but no art.
                    spotify_info_cache[uri_cache_key] = None 
                    add_to_negative_cache(uri_cache_key, "spotify_uri_album_has_no_images")
                    save_json_cache(spotify_info_cache, spotify_info_cache_file)
                    # Fall through to search-based logic, as uri_lookup_result is still None

                # --- Secondary Search Logic if URI result seems non-primary ---
                if uri_lookup_result: # Only proceed if URI lookup was successful
                    album_name_from_uri_lower = uri_lookup_result['canonical_album_name'].lower()
                    album_type_from_uri = uri_lookup_result['album_type']
                    
                    non_primary_keywords = ["chapter", " ep", ": ep", "(ep)", "live session", "acoustic", "remixes", "commentary", "single"] 
                    # Check if original_album_hint itself suggests it's an EP/single to avoid redundant search
                    original_hint_is_likely_ep_single = any(kw in original_album_hint.lower() for kw in non_primary_keywords if kw not in ["chapter"]) # chapter is too specific to URI result

                    looks_non_primary = False
                    if album_type_from_uri == 'single':
                        looks_non_primary = True
                        _debug_print(f"[SPOTIFY_TRACE] URI result album type is 'single'. Flagging for secondary search.")
                    elif any(keyword in album_name_from_uri_lower for keyword in non_primary_keywords):
                        looks_non_primary = True
                        _debug_print(f"[SPOTIFY_TRACE] URI result album name '{uri_lookup_result['canonical_album_name']}' contains non-primary keyword. Flagging for secondary search.")
                    
                    if looks_non_primary and not original_hint_is_likely_ep_single:
                        _debug_print(f"[SPOTIFY_TRACE] URI result for '{original_track_name}' appears non-primary. Attempting secondary search for main album using hint: '{original_album_hint}'.")
                        
                        # Use original_album_hint for the secondary search, assuming it might be cleaner
                        # If original_album_hint also contains "chapter", try to strip it for a cleaner search
                        cleaned_secondary_search_album_hint = original_album_hint
                        if "chapter" in cleaned_secondary_search_album_hint.lower():
                            # Basic stripping, might need refinement
                            cleaned_secondary_search_album_hint = re.sub(r':\s*the\s*.*?chapter', '', cleaned_secondary_search_album_hint, flags=re.IGNORECASE).strip()
                            _debug_print(f"[SPOTIFY_TRACE] Cleaned album hint for secondary search: '{cleaned_secondary_search_album_hint}'")

                        # Construct search query for the main album
                        # We will search for track, artist, and the cleaned album hint, then filter by album_type=='album'
                        secondary_query_params = f'track:"{quote(original_track_name)}" artist:"{quote(artist_name)}"'
                        if cleaned_secondary_search_album_hint:
                             secondary_query_params += f' album:"{quote(cleaned_secondary_search_album_hint)}"'
                        
                        secondary_url = f"{SPOTIFY_API_BASE_URL}search?q={secondary_query_params}&type=track&limit=10" # Fetch a few candidates
                        _debug_print(f"Spotify API call (Secondary Search for Main Album): {secondary_url}")
                        
                        try:
                            sec_response = requests.get(secondary_url, headers=headers, timeout=10)
                            sec_response.raise_for_status()
                            sec_data = sec_response.json()

                            if sec_data.get('tracks') and sec_data['tracks'].get('items'):
                                potential_main_albums = []
                                for item in sec_data['tracks']['items']:
                                    if item.get('album') and item['album'].get('album_type') == 'album':
                                        # Further check if this album name also doesn't look like an EP/single
                                        item_album_name_lower = item['album']['name'].lower()
                                        if not any(kw in item_album_name_lower for kw in non_primary_keywords):
                                            potential_main_albums.append(item)
                                
                                if potential_main_albums:
                                    # Prioritize exact match with cleaned_secondary_search_album_hint if available
                                    best_secondary_match = None
                                    if cleaned_secondary_search_album_hint:
                                        for pa_item in potential_main_albums:
                                            if pa_item['album']['name'].lower().strip() == cleaned_secondary_search_album_hint.lower().strip():
                                                best_secondary_match = pa_item
                                                _debug_print(f"[SPOTIFY_TRACE] Secondary search: Found EXACT album match: '{pa_item['album']['name']}'")
                                                break
                                    
                                    if not best_secondary_match: # Fallback to first potential main album
                                        best_secondary_match = potential_main_albums[0]
                                        _debug_print(f"[SPOTIFY_TRACE] Secondary search: No exact match, taking first 'album' type: '{best_secondary_match['album']['name']}'")

                                    sec_album_info = best_secondary_match['album']
                                    sec_art_url = sec_album_info.get('images', [{}])[0].get('url') if sec_album_info.get('images') else None
                                    if sec_art_url:
                                        secondary_search_result = {
                                            "art_url": sec_art_url,
                                            "canonical_album_name": sec_album_info.get('name'),
                                            "spotify_album_id": sec_album_info.get('id'),
                                            "spotify_artist_ids": [a['id'] for a in best_secondary_match.get('artists', []) if a.get('id')],
                                            "album_type": sec_album_info.get('album_type'),
                                            "source": "spotify (secondary_search_main_album)"
                                        }
                                        _debug_print(f"[SPOTIFY_TRACE] SUCCESS via Secondary Search! Overriding URI result. Found art: {sec_art_url} for album '{secondary_search_result['canonical_album_name']}'")
                                        final_result_to_return = secondary_search_result # Override with secondary search result
                                    else:
                                        _debug_print(f"[SPOTIFY_TRACE] Secondary search found album '{sec_album_info.get('name')}' but it has no art. Keeping URI result.")
                                else:
                                    _debug_print(f"[SPOTIFY_TRACE] Secondary search yielded no suitable 'album' type tracks. Keeping URI result.")
                            else:
                                _debug_print(f"[SPOTIFY_TRACE] Secondary search got no items. Keeping URI result.")
                        except Exception as e_sec:
                            _debug_print(f"[SPOTIFY_TRACE] Error during secondary search: {e_sec}. Keeping URI result.")
                    # If not non-primary, or secondary search failed, final_result_to_return remains the uri_lookup_result
                    
                    # Cache the final decision from URI path (either original URI or secondary search override)
                    spotify_info_cache[uri_cache_key] = final_result_to_return 
                    save_json_cache(spotify_info_cache, spotify_info_cache_file)
                    _debug_print(f"--- [SPOTIFY_TRACE] Exiting get_spotify_track_album_info (from URI path, final decision made) ---\\\n")
                    return final_result_to_return # Return the determined result (could be original URI or secondary)

            else: # No album data in track_data from URI
                _debug_print(f"[SPOTIFY_TRACE] URI Lookup successful, but no album data in response for track '{track_id}'.")
                spotify_info_cache[uri_cache_key] = None 
                add_to_negative_cache(uri_cache_key, "spotify_uri_no_album_data")
                save_json_cache(spotify_info_cache, spotify_info_cache_file)
                # Fall through to search-based logic as final_result_to_return is still None

        except requests.exceptions.HTTPError as e_http:
            _debug_print(f"[SPOTIFY_TRACE] HTTPError during URI Lookup for {spotify_track_uri}: {e_http}")
            if e_http.response.status_code == 404:
                _debug_print(f"[SPOTIFY_TRACE] Track ID from URI {spotify_track_uri} not found on Spotify (404). Adding to negative cache.")
                add_to_negative_cache(uri_cache_key, f"spotify_uri_track_not_found_{e_http.response.status_code}")
                spotify_info_cache[uri_cache_key] = None 
                save_json_cache(spotify_info_cache, spotify_info_cache_file)
        except requests.exceptions.RequestException as e_req:
            _debug_print(f"[SPOTIFY_TRACE] RequestException during URI Lookup for {spotify_track_uri}: {e_req}.")
        except Exception as e_generic_uri:
            _debug_print(f"[SPOTIFY_TRACE] Generic Exception during URI Lookup for {spotify_track_uri}: {e_generic_uri}.")
        
        # If URI lookup path failed to yield a final_result_to_return, it will be None here,
        # and we will proceed to broad search. If it did set final_result_to_return, that was already returned.
        _debug_print(f"[SPOTIFY_TRACE] URI lookup for '{spotify_track_uri}' did not yield a final art image or failed. Proceeding to broader search-based methods if not already returned.")


    # --- Priority 2: Search-Based Lookup (Broad Fallback if URI path didn't return) ---
    # This section will only be reached if spotify_track_uri was not provided, 
    # or if the URI path (including potential secondary search) did not successfully return a result.
    if final_result_to_return is not None:
        # This implies the URI path (primary or secondary) was successful and already returned.
        # This check is a safeguard, the return should have happened earlier.
        _debug_print(f"[SPOTIFY_TRACE] Should not reach here if final_result_to_return was set and returned in URI path.")
        return final_result_to_return

    internal_artist_name = artist_name.strip('\"')
    artist_variations_for_cache = clean_artist_name_for_search(internal_artist_name)
    primary_clean_artist = artist_variations_for_cache[0] if artist_variations_for_cache else internal_artist_name
    search_cache_key_album_part = original_album_hint.lower().strip() if original_album_hint else "no_album_hint"

    search_cache_key = f"spotify_search_{primary_clean_artist.lower().strip()}_{original_track_name.lower().strip()}_{search_cache_key_album_part}"

    _debug_print(f"[SPOTIFY_TRACE] Attempting Search-Based Lookup. Artist: '{artist_name}', Track: '{original_track_name}', Album Hint: '{original_album_hint}', Cache Key: '{search_cache_key}'")

    force_api_call_for_this_song = False # Reset for search logic
    # # --- FOR DEBUGGING SPECIFIC TRACKS (Search): UNCOMMENT AND MODIFY AS NEEDED --- 
    # # if "some specific artist" in artist_name.lower() and "some specific track" in original_track_name.lower():
    # #     _debug_print(f"[SPOTIFY_TRACE_FORCE_SEARCH] Matched criteria. Forcing API search call.")
    # #     force_api_call_for_this_song = True
    # # ---

    if not force_api_call_for_this_song:
        if DEBUG_CACHE: 
            print(f"[CACHE DEBUG] Spotify Search Info check for key: '{search_cache_key}'")
        if search_cache_key in spotify_info_cache:
            cached_value = spotify_info_cache[search_cache_key]
            if DEBUG_CACHE: print(f"[CACHE DEBUG] Spotify Search Info Cache HIT. Value: {cached_value}")
            _debug_print(f"[SPOTIFY_TRACE] Search Cache HIT. Returning cached: {json.dumps(cached_value, indent=2, ensure_ascii=False) if cached_value is not None else 'None'}")
            _debug_print(f"--- [SPOTIFY_TRACE] Exiting get_spotify_track_album_info (from search cache) ---\\\n")
            return cached_value
        
        if is_negative_cache_valid(search_cache_key):
            _debug_print(f"[SPOTIFY_TRACE] Negative cache HIT for search '{search_cache_key}'. This search failed recently. Skipping API calls.")
            _debug_print(f"--- [SPOTIFY_TRACE] Exiting get_spotify_track_album_info (from search negative cache) ---\\\n")
            spotify_info_cache[search_cache_key] = None 
            save_json_cache(spotify_info_cache, spotify_info_cache_file)
            return None
        else:
            if DEBUG_CACHE: print(f"[CACHE DEBUG] Spotify Search Info Cache MISS for '{search_cache_key}'. Querying API.")
            _debug_print(f"[SPOTIFY_TRACE] Search Cache MISS. Proceeding to query API for search.")
    else:
        _debug_print(f"[SPOTIFY_TRACE_FORCE_SEARCH] Proceeding to query Spotify API for search (cache check bypassed for search_cache_key).")

    # Access token should still be valid from earlier check, or this function would have exited.
    # If URI lookup failed due to token issue, this part won't run. This is fine.

    search_queries_to_try = []
    artist_variations = artist_variations_for_cache # Re-use from earlier in this function
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
        _debug_print(f"[SPOTIFY_TRACE] Original track name '{original_track_name}' was complex. Adding simplified track search for '{simplified_track_name}'.")
        for artist_var in artist_variations:
            search_queries_to_try.append((simplified_track_name, original_album_hint, artist_var, f"Simplified Track Search (Artist: {artist_var})"))

    # --- Strategy 3: Enhanced Soundtrack-specific strategies ---
    is_soundtrack = any(keyword in original_album_hint.lower() for keyword in [
        "soundtrack", "motion picture", "film", "movie", "original score", "theme"
    ])
    
    if is_soundtrack:
        _debug_print(f"[SPOTIFY_TRACE] Detected soundtrack album '{original_album_hint}'. Adding comprehensive soundtrack-specific searches.")
        
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
        _debug_print(f"[SPOTIFY_TRACE] Using Track for search: '{current_track_to_search}'")
        _debug_print(f"[SPOTIFY_TRACE] Using Album Hint for matching: '{current_album_hint_to_use}'")
        _debug_print(f"[SPOTIFY_TRACE] Using Artist for search: '{current_artist_to_use}'")

        # Build query - use artist if provided, otherwise search more broadly
        if current_artist_to_use:
            query_params = f'track:"{quote(current_track_to_search)}" artist:"{quote(current_artist_to_use)}"'
        else:
            query_params = f'track:"{quote(current_track_to_search)}"'
            if current_album_hint_to_use:
                query_params += f' album:"{quote(current_album_hint_to_use)}"'
        
        url = f"{SPOTIFY_API_BASE_URL}search?q={query_params}&type=track&limit=10"
        
        _debug_print(f"[SPOTIFY_TRACE] Constructed Spotify API URL ({search_type_label}): {url}")
        headers = {'Authorization': f"Bearer {access_token}", 'User-Agent': USER_AGENT}
        _debug_print(f"Spotify API call ({search_type_label}) for: Artist='{current_artist_to_use}', Track='{current_track_to_search}', Album Hint='{current_album_hint_to_use}'")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            _debug_print(f"[SPOTIFY_TRACE] Spotify API call successful ({search_type_label}, HTTP Status: {response.status_code}).")
            # if data.get('tracks') and data['tracks'].get('items'):
            #      _debug_print(f"[SPOTIFY_TRACE] Raw Response (Tracks Items, {search_type_label}): {json.dumps(data['tracks']['items'], indent=2, ensure_ascii=False)}")

            if data.get('tracks') and data['tracks'].get('items'):
                items = data['tracks']['items']
                best_match = None
                normalized_album_hint_for_search = current_album_hint_to_use.lower().strip() if current_album_hint_to_use else ""

                # Stage 1: Try for an EXACT album name match first
                if normalized_album_hint_for_search: # Only if we have a hint
                    for i, item in enumerate(items):
                        spotify_album_name_original = item.get('album', {}).get('name', '')
                        spotify_album_name_lower_stripped = spotify_album_name_original.lower().strip()
                        if spotify_album_name_lower_stripped == normalized_album_hint_for_search:
                            best_match = item
                            _debug_print(f"[SPOTIFY_TRACE] ({search_type_label}) EXACT MATCH Item {i} based on album hint ('{normalized_album_hint_for_search}'). Selected.")
                            break # Found exact match

                # Stage 2: If no exact match, try for containment (more lenient)
                # Ensure normalized_album_hint_for_search is not empty before attempting 'in' operations that might be broad.
                if not best_match and normalized_album_hint_for_search:
                    for i, item in enumerate(items):
                        spotify_album_name_original = item.get('album', {}).get('name', '')
                        spotify_album_name_lower_stripped = spotify_album_name_original.lower().strip()
                        
                        # Check containment: hint in spotify_name OR spotify_name in hint
                        # Be a bit more careful with very short hints to avoid overly broad matches.
                        hint_is_significant = len(normalized_album_hint_for_search) > 3 

                        if hint_is_significant and \
                           (normalized_album_hint_for_search in spotify_album_name_lower_stripped or \
                            spotify_album_name_lower_stripped in normalized_album_hint_for_search):
                            best_match = item
                            _debug_print(f"[SPOTIFY_TRACE] ({search_type_label}) CONTAINMENT MATCH Item {i} based on album hint ('{normalized_album_hint_for_search}' vs '{spotify_album_name_lower_stripped}'). Selected.")
                            break # Found a containment match
                        # Soundtrack-specific matching (more flexible, could be part of this stage or a separate one)
                        elif is_soundtrack: # is_soundtrack was defined earlier in the function
                            # Remove common soundtrack terms for a looser core title match
                            album_core_hint_simplified = normalized_album_hint_for_search.replace("soundtrack", "").replace("original motion picture", "").replace("motion picture", "").replace("score", "").replace("film", "").replace("movie", "").strip()
                            spotify_core_name_simplified = spotify_album_name_lower_stripped.replace("soundtrack", "").replace("original motion picture", "").replace("motion picture", "").replace("score", "").replace("film", "").replace("movie", "").strip()
                            
                            # Avoid empty strings after simplification
                            if album_core_hint_simplified and spotify_core_name_simplified and \
                               (album_core_hint_simplified in spotify_core_name_simplified or spotify_core_name_simplified in album_core_hint_simplified):
                                best_match = item
                                _debug_print(f"[SPOTIFY_TRACE] ({search_type_label}) SOUNDTRACK CORE MATCH Item {i} ('{album_core_hint_simplified}' vs '{spotify_core_name_simplified}'). Selected.")
                                break
                
                # Stage 3: If still no match and items exist, fallback to the first item
                if not best_match and items:
                    best_match = items[0] 
                    _debug_print(f"[SPOTIFY_TRACE] ({search_type_label}) No album hint match (exact or containment). Taking first result (Item 0).")

                if best_match:
                    album_info = best_match.get('album', {})
                    art_url = album_info.get('images', [{}])[0].get('url') if album_info.get('images') else None
                    
                    if art_url: # Found art with this search query!
                        _debug_print(f"[SPOTIFY_TRACE] ({search_type_label}) SUCCESS! Found art_url: {art_url}")
                        final_result_from_api = {
                            "art_url": art_url,
                            "canonical_album_name": album_info.get('name'),
                            "spotify_album_id": album_info.get('id'),
                            "spotify_artist_ids": [a['id'] for a in best_match.get('artists', []) if a.get('id')],
                            "source": f"spotify ({search_type_label})"
                        }
                        break # Exit the loop of search_queries_to_try, we found a good result
                    else:
                        _debug_print(f"[SPOTIFY_TRACE] ({search_type_label}) Found a best_match, but it has no art_url.")
            else: # No items in response
                _debug_print(f"[SPOTIFY_TRACE] ({search_type_label}) No 'items' in Spotify response.")
        
        except requests.exceptions.RequestException as e:
            _debug_print(f"[SPOTIFY_TRACE] ({search_type_label}) RequestException: {e}")
            # Potentially break or continue to next search type depending on error
        except json.JSONDecodeError as e_json:
            _debug_print(f"[SPOTIFY_TRACE] ({search_type_label}) JSONDecodeError: {e_json}")
        
        time.sleep(0.2) # Respect API limits between different search attempts for the same track

    # After trying all search queries:
    if final_result_from_api:
        print(f"Found Spotify info via {final_result_from_api['source']}: Album='{final_result_from_api['canonical_album_name']}', Art URL: {'Yes' if final_result_from_api['art_url'] else 'No'}")
        _debug_print(f"[SPOTIFY_TRACE] Caching and returning search result (from {final_result_from_api['source']}): {json.dumps(final_result_from_api, indent=2, ensure_ascii=False)}")
    else:
        print(f"No suitable track found on Spotify after all search attempts for: Original Track='{original_track_name}', Artist='{artist_name}'")
        _debug_print(f"[SPOTIFY_TRACE] Caching None to '{search_cache_key}' after all search attempts failed.")
        add_to_negative_cache(search_cache_key, f"no_spotify_results_after_{len(search_queries_to_try)}_search_attempts")
    
    spotify_info_cache[search_cache_key] = final_result_from_api 
    save_json_cache(spotify_info_cache, spotify_info_cache_file)
    _debug_print(f"--- [SPOTIFY_TRACE] Exiting get_spotify_track_album_info (after API search attempt(s)) ---\\\n")
    return final_result_from_api


def get_spotify_artist_info(artist_name):
    """
    Searches Spotify for an artist and returns their profile information including photo URL.
    Uses Spotify's Artists API endpoint.
    
    Args:
        artist_name (str): The artist name to search for
        
    Returns:
        dict or None: Dictionary containing artist info:
        {
            "photo_url": "https://...",
            "canonical_artist_name": "Artist Name",
            "spotify_artist_id": "spotify_id",
            "genres": ["genre1", "genre2"],
            "popularity": 75,
            "followers": 1000000,
            "source": "spotify (artist_search)"
        }
        Returns None if no artist found or on error.
    """
    original_artist_name = artist_name
    
    _debug_print(f"\n--- [SPOTIFY_ARTIST_TRACE] Entering get_spotify_artist_info ---")
    _debug_print(f"[SPOTIFY_ARTIST_TRACE] Called with: Artist='{original_artist_name}'")

    access_token = _get_spotify_access_token()
    if not access_token:
        _debug_print(f"[SPOTIFY_ARTIST_TRACE] Failed to get Spotify access token. Cannot proceed.")
        _debug_print(f"--- [SPOTIFY_ARTIST_TRACE] Exiting (no access token) ---\\\n")
        return None

    # Clean artist name for search
    artist_variations = clean_artist_name_for_search(artist_name)
    primary_clean_artist = artist_variations[0] if artist_variations else artist_name
    
    search_cache_key = f"spotify_artist_search_{primary_clean_artist.lower().strip()}"
    
    _debug_print(f"[SPOTIFY_ARTIST_TRACE] Search cache key: '{search_cache_key}'")

    # Check cache first
    if DEBUG_CACHE: print(f"[CACHE DEBUG] Spotify Artist Info check for key: '{search_cache_key}'")
    if search_cache_key in spotify_artist_cache:
        cached_value = spotify_artist_cache[search_cache_key]
        if DEBUG_CACHE: print(f"[CACHE DEBUG] Spotify Artist Info Cache HIT. Value: {cached_value}")
        _debug_print(f"[SPOTIFY_ARTIST_TRACE] Artist Cache HIT. Returning cached: {json.dumps(cached_value, indent=2, ensure_ascii=False) if cached_value is not None else 'None'}")
        _debug_print(f"--- [SPOTIFY_ARTIST_TRACE] Exiting (from artist cache) ---\\\n")
        return cached_value
    
    # Check negative cache
    if is_negative_cache_valid(search_cache_key):
        _debug_print(f"[SPOTIFY_ARTIST_TRACE] Negative cache HIT for artist search '{search_cache_key}'. This search failed recently. Skipping API call.")
        _debug_print(f"--- [SPOTIFY_ARTIST_TRACE] Exiting (from artist negative cache) ---\\\n")
        spotify_artist_cache[search_cache_key] = None 
        save_json_cache(spotify_artist_cache, spotify_artist_cache_file)
        return None

    if DEBUG_CACHE: print(f"[CACHE DEBUG] Spotify Artist Info Cache MISS for '{search_cache_key}'. Querying API.")

    # Try different search strategies
    search_queries_to_try = []
    
    # Strategy 1: Direct artist name search with each variation
    for artist_var in artist_variations:
        search_queries_to_try.append((artist_var, f"Direct Artist Search (Name: {artist_var})"))

    # Strategy 2: Simplified artist name (remove special characters)
    simplified_artist = primary_clean_artist
    # Remove common suffixes and prefixes that might interfere
    for to_remove in [" feat.", " ft.", " featuring", " & ", " and ", " vs ", " vs. "]:
        if to_remove in simplified_artist.lower():
            simplified_artist = simplified_artist.lower().split(to_remove)[0].strip()
            break
    
    if simplified_artist.lower() != primary_clean_artist.lower():
        search_queries_to_try.append((simplified_artist, f"Simplified Artist Search (Name: {simplified_artist})"))

    final_result_from_api = None

    for current_artist_to_search, search_type_label in search_queries_to_try:
        _debug_print(f"\n[SPOTIFY_ARTIST_TRACE] --- Attempting {search_type_label} ---")
        _debug_print(f"[SPOTIFY_ARTIST_TRACE] Using Artist for search: '{current_artist_to_search}'")

        # Build search query
        query_params = f'artist:"{quote(current_artist_to_search)}"'
        url = f"{SPOTIFY_API_BASE_URL}search?q={query_params}&type=artist&limit=10"
        
        _debug_print(f"[SPOTIFY_ARTIST_TRACE] Constructed Spotify API URL ({search_type_label}): {url}")
        headers = {'Authorization': f"Bearer {access_token}", 'User-Agent': USER_AGENT}
        _debug_print(f"Spotify Artist API call ({search_type_label}) for: Artist='{current_artist_to_search}'")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            _debug_print(f"[SPOTIFY_ARTIST_TRACE] Spotify Artist API call successful ({search_type_label}, HTTP Status: {response.status_code}).")

            if data.get('artists') and data['artists'].get('items'):
                items = data['artists']['items']
                best_match = None
                normalized_search_name = current_artist_to_search.lower().strip()

                # Find best match by name similarity
                for i, item in enumerate(items):
                    spotify_artist_name = item.get('name', '').lower().strip()
                    
                    # Exact match first
                    if spotify_artist_name == normalized_search_name:
                        best_match = item
                        _debug_print(f"[SPOTIFY_ARTIST_TRACE] ({search_type_label}) EXACT MATCH Item {i}. Selected.")
                        break
                    # Containment match as fallback
                    elif (normalized_search_name in spotify_artist_name or 
                          spotify_artist_name in normalized_search_name):
                        if not best_match:  # Only take first containment match
                            best_match = item
                            _debug_print(f"[SPOTIFY_ARTIST_TRACE] ({search_type_label}) CONTAINMENT MATCH Item {i}. Selected.")

                # If no name match, take first result (highest popularity)
                if not best_match and items:
                    best_match = items[0] 
                    _debug_print(f"[SPOTIFY_ARTIST_TRACE] ({search_type_label}) No name match. Taking first result (Item 0).")

                if best_match:
                    artist_images = best_match.get('images', [])
                    photo_url = artist_images[0].get('url') if artist_images else None
                    
                    if photo_url:  # Found artist with photo!
                        _debug_print(f"[SPOTIFY_ARTIST_TRACE] ({search_type_label}) SUCCESS! Found photo_url: {photo_url}")
                        final_result_from_api = {
                            "photo_url": photo_url,
                            "canonical_artist_name": best_match.get('name'),
                            "spotify_artist_id": best_match.get('id'),
                            "genres": best_match.get('genres', []),
                            "popularity": best_match.get('popularity', 0),
                            "followers": best_match.get('followers', {}).get('total', 0),
                            "source": f"spotify ({search_type_label})"
                        }
                        break  # Exit the loop, we found a good result
                    else:
                        _debug_print(f"[SPOTIFY_ARTIST_TRACE] ({search_type_label}) Found artist '{best_match.get('name')}', but no profile photo.")
            else:
                _debug_print(f"[SPOTIFY_ARTIST_TRACE] ({search_type_label}) No 'items' in Spotify artists response.")
        
        except requests.exceptions.RequestException as e:
            _debug_print(f"[SPOTIFY_ARTIST_TRACE] ({search_type_label}) RequestException: {e}")
        except json.JSONDecodeError as e_json:
            _debug_print(f"[SPOTIFY_ARTIST_TRACE] ({search_type_label}) JSONDecodeError: {e_json}")
        
        time.sleep(0.2)  # Respect API limits between different search attempts

    # Cache and return result
    if final_result_from_api:
        print(f"Found Spotify artist info via {final_result_from_api['source']}: Artist='{final_result_from_api['canonical_artist_name']}', Photo URL: {'Yes' if final_result_from_api['photo_url'] else 'No'}")
        _debug_print(f"[SPOTIFY_ARTIST_TRACE] Caching and returning artist result (from {final_result_from_api['source']}): {json.dumps(final_result_from_api, indent=2, ensure_ascii=False)}")
    else:
        print(f"No suitable artist found on Spotify after all search attempts for: Original Artist='{original_artist_name}'")
        _debug_print(f"[SPOTIFY_ARTIST_TRACE] Caching None to '{search_cache_key}' after all artist search attempts failed.")
        add_to_negative_cache(search_cache_key, f"no_spotify_artist_results_after_{len(search_queries_to_try)}_search_attempts")
    
    spotify_artist_cache[search_cache_key] = final_result_from_api 
    save_json_cache(spotify_artist_cache, spotify_artist_cache_file)
    _debug_print(f"--- [SPOTIFY_ARTIST_TRACE] Exiting get_spotify_artist_info (after API search attempt(s)) ---\\\n")
    return final_result_from_api

# --- MusicBrainz Functions (Now Legacy/Fallback - Commented out primary usage) ---
def get_canonical_album_name_from_mbid(album_mbid):
    """
    Queries MusicBrainz for a given album_mbid (release MBID) to get its
    canonical album name, preferably from the release group.
    Caches results in mb_album_info_cache.
    THIS IS MAINLY FOR LAST.FM DATA FLOW.
    """
    if not album_mbid:
        return None

    cache_key = f"mb_album_{album_mbid}"
    if DEBUG_CACHE: print(f"[CACHE DEBUG] MB Album Info check for key: '{cache_key}'")

    if cache_key in mb_album_info_cache:
        cached_data = mb_album_info_cache[cache_key]
        if DEBUG_CACHE: print(f"[CACHE DEBUG] MB Album Info Cache HIT. Value: {cached_data}")
        return cached_data.get("canonical_album_name") if isinstance(cached_data, dict) else cached_data # Handle old cache format if any

    # Check negative cache for this specific MBID lookup type
    negative_cache_key_mb_album = f"neg_mb_album_{album_mbid}"
    if is_negative_cache_valid(negative_cache_key_mb_album):
        if DEBUG_CACHE: print(f"[NEGATIVE CACHE DEBUG] Negative cache HIT for '{negative_cache_key_mb_album}'. Skipping MB API call.")
        return None # Already know this MBID lookup failed recently

    if DEBUG_CACHE: print(f"[CACHE DEBUG] MB Album Info Cache MISS for key: '{cache_key}'. Querying MusicBrainz API.")
    _debug_print(f"MusicBrainz API call for canonical album name (MBID: {album_mbid})")

    url = f"https://musicbrainz.org/ws/2/release/{album_mbid}?inc=release-groups&fmt=json"
    headers = {'User-Agent': USER_AGENT}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        canonical_name = None
        # Prefer release group title if available and seems valid
        if data.get('release-group') and data['release-group'].get('title'):
            canonical_name = data['release-group']['title']
            if DEBUG_CACHE: print(f"[MB ALBUM DEBUG] Using release-group title: '{canonical_name}' for MBID {album_mbid}")
        # Fallback to release title if release group title is missing
        elif data.get('title'):
            canonical_name = data['title']
            if DEBUG_CACHE: print(f"[MB ALBUM DEBUG] Using release title: '{canonical_name}' for MBID {album_mbid} (no release-group title)")
        
        if canonical_name:
            mb_album_info_cache[cache_key] = {"canonical_album_name": canonical_name, "source": "musicbrainz_api"}
            save_json_cache(mb_album_info_cache, mb_album_info_cache_file)
            _debug_print(f"Found canonical album name: '{canonical_name}' for MBID: {album_mbid}")
            time.sleep(1) # Respect MusicBrainz API rate limits
            return canonical_name
        else:
            _debug_print(f"No canonical album name found in MusicBrainz response for MBID: {album_mbid}")
            add_to_negative_cache(negative_cache_key_mb_album, "mb_no_album_title_found")
            mb_album_info_cache[cache_key] = {"canonical_album_name": None, "source": "musicbrainz_api_failed_no_title"} # Cache failure
            save_json_cache(mb_album_info_cache, mb_album_info_cache_file)
            time.sleep(1)
            return None

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"MusicBrainz API: Release MBID {album_mbid} not found (404).")
            add_to_negative_cache(negative_cache_key_mb_album, f"mb_mbid_not_found_{e.response.status_code}")
        else:
            print(f"MusicBrainz API HTTPError for MBID {album_mbid}: {e}")
            add_to_negative_cache(negative_cache_key_mb_album, f"mb_http_error_{e.response.status_code}")
        mb_album_info_cache[cache_key] = {"canonical_album_name": None, "source": f"musicbrainz_api_http_error_{e.response.status_code}"}
        save_json_cache(mb_album_info_cache, mb_album_info_cache_file)
        time.sleep(1)
        return None
    except requests.exceptions.RequestException as e:
        _debug_print(f"Error fetching canonical album name for MBID {album_mbid} from MusicBrainz: {e}")
        # Don't add to negative cache for general request exceptions like timeouts, allow retries sooner
        # mb_album_info_cache[cache_key] = {"canonical_album_name": None, "source": "musicbrainz_api_request_exception"} # Optionally cache this type of failure
        # save_json_cache(mb_album_info_cache, mb_album_info_cache_file)
        time.sleep(1)
        return None
    except json.JSONDecodeError:
        _debug_print(f"Error decoding JSON response for canonical album name (MBID: {album_mbid}) from MusicBrainz.")
        add_to_negative_cache(negative_cache_key_mb_album, "mb_json_decode_error")
        mb_album_info_cache[cache_key] = {"canonical_album_name": None, "source": "musicbrainz_api_json_decode_error"}
        save_json_cache(mb_album_info_cache, mb_album_info_cache_file)
        time.sleep(1)
        return None

def get_release_mbid(artist_name, album_name):
    # This function is now effectively deprecated for primary use.
    # Kept for reference or potential future fallback.
    # If called, it will still use its own mbid_cache.
    if DEBUG_CACHE: print(f"[MBID DEPRECATED WARNING] get_release_mbid called for '{artist_name} - {album_name}'. This path is not actively used for Spotify art. Spotify API is primary.")
    
    # --- Original MBID logic ---
    cache_key = f"{artist_name.lower().strip()}_{album_name.lower().strip()}"
    if DEBUG_CACHE: print(f"[CACHE DEBUG] MBID check for key: '{cache_key}' (Artist: '{artist_name}', Album: '{album_name}')")
    
    if cache_key in mbid_cache:
        if DEBUG_CACHE: print(f"[CACHE DEBUG] MBID Cache HIT for key: '{cache_key}'. Value: {mbid_cache[cache_key]}")
        return mbid_cache[cache_key]
    
    if DEBUG_CACHE: print(f"[CACHE DEBUG] MBID Cache MISS for key: '{cache_key}'. Querying API.")
    _debug_print(f"MBID API call for: {artist_name} - {album_name}")
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
    if DEBUG_CACHE: print(f"[CAA DEPRECATED WARNING] get_album_art_url called for MBID '{release_mbid}'. This path is not actively used for Spotify art. Spotify API is primary.")
    
    # --- Original CAA logic ---
    if not release_mbid: return None
    _debug_print(f"CAA API call for MBID: {release_mbid}")
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
    _debug_print(f"Downloading image: {image_url} to {cached_image_path}")
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


def download_artist_image_to_cache(image_url, artist_name_for_file):
    """
    Downloads an artist profile photo from image_url and saves it to the ARTIST_ART_CACHE_DIR.
    Uses artist_name_for_file to create a unique filename with "_artist_" identifier.
    Returns the local path to the downloaded image, or None on failure.
    """
    if not image_url:
        return None

    # Sanitize artist name for filename (using canonical name from Spotify)
    safe_artist_name = "".join(c if c.isalnum() or c in " .-_" else "_" for c in str(artist_name_for_file).strip())[:50]
    
    # Use distinctive naming pattern for artist photos: artist_{name}_artist.jpg
    filename_base = f"artist_{safe_artist_name}_artist"
    try:
        # Attempt to get extension from URL, fallback to .jpg
        extension = os.path.splitext(image_url.split('?')[0])[-1].lower()
        if not extension or len(extension) > 5 or len(extension) < 2 or not extension.startswith('.'):
            extension = ".jpg"
    except:
        extension = ".jpg"

    cached_image_path = os.path.join(ARTIST_ART_CACHE_DIR, filename_base + extension)
    if DEBUG_CACHE: print(f"[ARTIST CACHE DEBUG] Artist image check for path: '{cached_image_path}' (URL: {image_url})")

    if os.path.exists(cached_image_path):
        if DEBUG_CACHE: print(f"[ARTIST CACHE DEBUG] Artist Image Cache HIT: '{cached_image_path}'")
        return cached_image_path
    
    if DEBUG_CACHE: print(f"[ARTIST CACHE DEBUG] Artist Image Cache MISS: '{cached_image_path}'. Downloading artist image.")
    _debug_print(f"Downloading artist image: {image_url} to {cached_image_path}")
    headers = {'User-Agent': USER_AGENT} # Some image hosts might check User-Agent
    try:
        response = requests.get(image_url, headers=headers, stream=True, timeout=15)
        response.raise_for_status()
        with open(cached_image_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        if DEBUG_CACHE: print(f"[ARTIST CACHE DEBUG] Successfully downloaded artist image: '{cached_image_path}'")
        return cached_image_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading artist image {image_url}: {e}")
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


def get_album_art_path(artist_name, track_name, identifier_info):
    """
    DEPRECATED in favor of get_album_art_path_and_spotify_info.
    Main function to get local album art path.
    Uses Spotify API first, potentially leveraging MBID for Last.fm data to refine album name,
    or Spotify Track URI for direct Spotify data.

    Args:
        artist_name (str): Artist name.
        track_name (str): Track name.
        identifier_info (dict): Dictionary containing information to help identify the album:
            {
                "album_name_hint": "Original album name string",
                "album_mbid": "mbid_if_lastfm_and_available" or None,
                "track_uri": "uri_if_spotify_data" or None,
                "source_data_type": "spotify" or "lastfm"
            }

    Returns:
        str: Local path to downloaded album art, or None on failure.
    """
    print(f"WARNING: get_album_art_path is deprecated. Use get_album_art_path_and_spotify_info instead.")
    print(f"Attempting to get art path for: Artist='{artist_name}', Track='{track_name}', Identifiers: {identifier_info}")

    current_album_hint = identifier_info.get("album_name_hint", "")
    track_uri_from_spotify_data = identifier_info.get("track_uri")
    source_type = identifier_info.get("source_data_type")

    if source_type == "lastfm" and identifier_info.get("album_mbid"):
        album_mbid = identifier_info["album_mbid"]
        if DEBUG_CACHE: print(f"[ART_PATH_LOGIC] Last.fm data with MBID: {album_mbid}. Attempting to get canonical album name.")
        canonical_name_from_mb = get_canonical_album_name_from_mbid(album_mbid)
        if canonical_name_from_mb:
            if DEBUG_CACHE: print(f"[ART_PATH_LOGIC] Canonical album name from MB: '{canonical_name_from_mb}'. Using this as hint for Spotify.")
            current_album_hint = canonical_name_from_mb
        elif DEBUG_CACHE:
            print(f"[ART_PATH_LOGIC] No canonical name from MB for {album_mbid}. Using original hint: '{current_album_hint}'")
    
    spotify_data = get_spotify_track_album_info(
        artist_name, 
        track_name, 
        current_album_hint, 
        spotify_track_uri=track_uri_from_spotify_data
    )

    if spotify_data and spotify_data.get("art_url"):
        art_url = spotify_data["art_url"]
        album_name_for_file = spotify_data.get("canonical_album_name", current_album_hint) 
        artist_name_for_file = artist_name
        
        print(f"[ART_PATH_LOGIC] Spotify returned art URL: {art_url}. Album for filename: '{album_name_for_file}'")
        return download_image_to_cache(art_url, album_name_for_file, artist_name_for_file)
    else:
        if spotify_data:
            print(f"[ART_PATH_LOGIC] Spotify found info for '{artist_name} - {track_name}' (Source: {spotify_data.get('source')}) but no art URL.")
        else:
            print(f"[ART_PATH_LOGIC] No Spotify info or art URL found for '{artist_name} - {track_name}' after all attempts.")
        return None

def get_album_art_path_and_spotify_info(artist_name, track_name, identifier_info):
    """
    Main function to get local album art path and the spotify_info data used.
    Uses Spotify API first, potentially leveraging MBID for Last.fm data to refine album name,
    or Spotify Track URI for direct Spotify data.

    Args:
        artist_name (str): Artist name.
        track_name (str): Track name.
        identifier_info (dict): Dictionary containing information to help identify the album:
            {
                "album_name_hint": "Original album name string",
                "album_mbid": "mbid_if_lastfm_and_available" or None,
                "track_uri": "uri_if_spotify_data" or None,
                "source_data_type": "spotify" or "lastfm"
            }

    Returns:
        tuple: (local_art_path, spotify_info_dict) or (None, spotify_info_dict_if_found_else_None)
               spotify_info_dict is the dict returned by get_spotify_track_album_info
    """
    print(f"Attempting to get art path and info for: Artist='{artist_name}', Track='{track_name}', Identifiers: {identifier_info}")

    current_album_hint = identifier_info.get("album_name_hint", "")
    track_uri_from_spotify_data = identifier_info.get("track_uri")
    source_type = identifier_info.get("source_data_type")

    if source_type == "lastfm" and identifier_info.get("album_mbid"):
        album_mbid = identifier_info["album_mbid"]
        if DEBUG_CACHE: print(f"[ART_PATH_LOGIC] Last.fm data with MBID: {album_mbid}. Attempting to get canonical album name.")
        canonical_name_from_mb = get_canonical_album_name_from_mbid(album_mbid)
        if canonical_name_from_mb:
            if DEBUG_CACHE: print(f"[ART_PATH_LOGIC] Canonical album name from MB: '{canonical_name_from_mb}'. Using this as hint for Spotify.")
            current_album_hint = canonical_name_from_mb
        elif DEBUG_CACHE:
            print(f"[ART_PATH_LOGIC] No canonical name from MB for {album_mbid}. Using original hint: '{current_album_hint}'")
    
    spotify_data = get_spotify_track_album_info(
        artist_name, 
        track_name, 
        current_album_hint, 
        spotify_track_uri=track_uri_from_spotify_data
    )

    if spotify_data and spotify_data.get("art_url"):
        art_url = spotify_data["art_url"]
        album_name_for_file = spotify_data.get("canonical_album_name", current_album_hint) 
        artist_name_for_file = artist_name
        
        print(f"[ART_PATH_LOGIC] Spotify returned art URL: {art_url}. Album for filename: '{album_name_for_file}'")
        downloaded_path = download_image_to_cache(art_url, album_name_for_file, artist_name_for_file)
        return downloaded_path, spotify_data # Return path and the spotify_data dict
    else:
        if spotify_data:
            print(f"[ART_PATH_LOGIC] Spotify found info for '{artist_name} - {track_name}' (Source: {spotify_data.get('source')}) but no art URL.")
        else:
            print(f"[ART_PATH_LOGIC] No Spotify info or art URL found for '{artist_name} - {track_name}' after all attempts.")
        return None, spotify_data # Return None for path, but still return spotify_data if it was found


def get_spotify_artist_info_from_track_uri(track_uri):
    """
    Get artist information by using a Spotify track URI to get exact artist ID.
    This is more reliable than name-based search.
    
    Args:
        track_uri (str): Spotify track URI like "spotify:track:..."
    
    Returns:
        dict or None: Artist info similar to get_spotify_artist_info()
    """
    if not track_uri or not track_uri.startswith('spotify:track:'):
        return None
    
    track_id = track_uri.split(':')[-1]
    cache_key = f"spotify_artist_from_track_{track_id}"
    
    _debug_print(f"\n--- [SPOTIFY_ARTIST_URI_TRACE] Entering get_spotify_artist_info_from_track_uri ---")
    _debug_print(f"[SPOTIFY_ARTIST_URI_TRACE] Track URI: {track_uri}, Track ID: {track_id}")

    # Check cache first
    if DEBUG_CACHE: print(f"[CACHE DEBUG] Spotify Artist from Track URI check for key: '{cache_key}'")
    if cache_key in spotify_artist_cache:
        cached_value = spotify_artist_cache[cache_key]
        if DEBUG_CACHE: print(f"[CACHE DEBUG] Spotify Artist from Track URI Cache HIT. Value: {cached_value}")
        _debug_print(f"[SPOTIFY_ARTIST_URI_TRACE] Cache HIT. Returning cached: {json.dumps(cached_value, indent=2, ensure_ascii=False) if cached_value is not None else 'None'}")
        return cached_value

    # Check negative cache
    if is_negative_cache_valid(cache_key):
        _debug_print(f"[SPOTIFY_ARTIST_URI_TRACE] Negative cache HIT for '{cache_key}'. Skipping API call.")
        spotify_artist_cache[cache_key] = None
        save_json_cache(spotify_artist_cache, spotify_artist_cache_file)
        return None

    access_token = _get_spotify_access_token()
    if not access_token:
        _debug_print(f"[SPOTIFY_ARTIST_URI_TRACE] No access token available.")
        return None

    try:
        # Get track details to extract artist ID
        track_url = f"{SPOTIFY_API_BASE_URL}tracks/{track_id}"
        headers = {'Authorization': f"Bearer {access_token}", 'User-Agent': USER_AGENT}
        
        _debug_print(f"[SPOTIFY_ARTIST_URI_TRACE] Getting track details: {track_url}")
        track_response = requests.get(track_url, headers=headers, timeout=10)
        track_response.raise_for_status()
        track_data = track_response.json()

        # Extract primary artist ID
        if track_data.get('artists') and len(track_data['artists']) > 0:
            primary_artist = track_data['artists'][0]  # Use first/primary artist
            artist_id = primary_artist.get('id')
            
            if not artist_id:
                _debug_print(f"[SPOTIFY_ARTIST_URI_TRACE] No artist ID found in track data.")
                add_to_negative_cache(cache_key, "no_artist_id_in_track")
                spotify_artist_cache[cache_key] = None
                save_json_cache(spotify_artist_cache, spotify_artist_cache_file)
                return None

            _debug_print(f"[SPOTIFY_ARTIST_URI_TRACE] Found artist ID: {artist_id}")

            # Get detailed artist information
            artist_url = f"{SPOTIFY_API_BASE_URL}artists/{artist_id}"
            _debug_print(f"[SPOTIFY_ARTIST_URI_TRACE] Getting artist details: {artist_url}")
            
            artist_response = requests.get(artist_url, headers=headers, timeout=10)
            artist_response.raise_for_status()
            artist_data = artist_response.json()

            # Extract artist photo and info
            artist_images = artist_data.get('images', [])
            photo_url = artist_images[0].get('url') if artist_images else None

            if photo_url:
                result = {
                    "photo_url": photo_url,
                    "canonical_artist_name": artist_data.get('name'),
                    "spotify_artist_id": artist_data.get('id'),
                    "genres": artist_data.get('genres', []),
                    "popularity": artist_data.get('popularity', 0),
                    "followers": artist_data.get('followers', {}).get('total', 0),
                    "source": f"spotify (track_uri_lookup)"
                }
                
                _debug_print(f"[SPOTIFY_ARTIST_URI_TRACE] SUCCESS! Artist: {result['canonical_artist_name']}, Photo: {photo_url}")
                spotify_artist_cache[cache_key] = result
                save_json_cache(spotify_artist_cache, spotify_artist_cache_file)
                return result
            else:
                _debug_print(f"[SPOTIFY_ARTIST_URI_TRACE] Artist found but no photo: {artist_data.get('name')}")
                # Cache the fact that this artist has no photo
                result = {
                    "photo_url": None,
                    "canonical_artist_name": artist_data.get('name'),
                    "spotify_artist_id": artist_data.get('id'),
                    "genres": artist_data.get('genres', []),
                    "popularity": artist_data.get('popularity', 0),
                    "followers": artist_data.get('followers', {}).get('total', 0),
                    "source": f"spotify (track_uri_lookup_no_photo)"
                }
                spotify_artist_cache[cache_key] = result
                save_json_cache(spotify_artist_cache, spotify_artist_cache_file)
                return result
        else:
            _debug_print(f"[SPOTIFY_ARTIST_URI_TRACE] No artists found in track data.")
            add_to_negative_cache(cache_key, "no_artists_in_track")
            spotify_artist_cache[cache_key] = None
            save_json_cache(spotify_artist_cache, spotify_artist_cache_file)
            return None

    except requests.exceptions.RequestException as e:
        _debug_print(f"[SPOTIFY_ARTIST_URI_TRACE] Request error: {e}")
        # Don't add to negative cache for network errors
        return None
    except Exception as e:
        _debug_print(f"[SPOTIFY_ARTIST_URI_TRACE] Unexpected error: {e}")
        add_to_negative_cache(cache_key, f"error_{str(e)[:50]}")
        spotify_artist_cache[cache_key] = None
        save_json_cache(spotify_artist_cache, spotify_artist_cache_file)
        return None


def get_artist_profile_photo_and_spotify_info(artist_name, fallback_track_info=None):
    """
    Main function to get artist profile photo path and the spotify_info data used.
    Implements improved strategy: Track URI → Artist ID → Profile Photo → Name Search → Album Art Fallback
    
    Args:
        artist_name (str): The artist name to search for
        fallback_track_info (dict, optional): Fallback track info for album art:
            {
                "track_name": "Track Name",
                "album_name": "Album Name", 
                "track_uri": "spotify:track:..."  # Optional but preferred for accuracy
            }
    
    Returns:
        tuple: (local_photo_path, spotify_artist_info_dict) or (None, spotify_artist_info_dict_if_found_else_None)
               spotify_artist_info_dict is the dict returned by get_spotify_artist_info
    """
    print(f"Attempting to get artist profile photo for: Artist='{artist_name}'")
    
    artist_info = None
    
    # Strategy 1: Use Spotify Track URI to get exact artist (most reliable)
    if fallback_track_info and fallback_track_info.get("track_uri"):
        print(f"[ARTIST_PHOTO_LOGIC] Using track URI for accurate artist lookup: {fallback_track_info['track_uri']}")
        artist_info = get_spotify_artist_info_from_track_uri(fallback_track_info["track_uri"])
        
        if artist_info:
            print(f"[ARTIST_PHOTO_LOGIC] Found artist via track URI: {artist_info.get('canonical_artist_name')} (popularity: {artist_info.get('popularity', 'N/A')})")
        else:
            print(f"[ARTIST_PHOTO_LOGIC] Track URI lookup failed, will try name search")
    
    # Strategy 2: Fallback to name-based search if no URI or URI failed
    if not artist_info:
        print(f"[ARTIST_PHOTO_LOGIC] Attempting name-based search for: {artist_name}")
        artist_info = get_spotify_artist_info(artist_name)
        
        if artist_info:
            print(f"[ARTIST_PHOTO_LOGIC] Found artist via name search: {artist_info.get('canonical_artist_name')} (popularity: {artist_info.get('popularity', 'N/A')})")
            
            # Warn if there might be name mismatch
            canonical_name = artist_info.get('canonical_artist_name', '').lower()
            search_name = artist_name.lower()
            if canonical_name != search_name and canonical_name not in search_name and search_name not in canonical_name:
                print(f"[ARTIST_PHOTO_LOGIC] ⚠️  WARNING: Name mismatch detected!")
                print(f"[ARTIST_PHOTO_LOGIC]    Searched for: '{artist_name}'")
                print(f"[ARTIST_PHOTO_LOGIC]    Found: '{artist_info.get('canonical_artist_name')}'")
                print(f"[ARTIST_PHOTO_LOGIC]    This might be the wrong artist. Consider providing track_uri for accuracy.")
    
    # Strategy 3: Try to get profile photo if we found artist info
    if artist_info and artist_info.get("photo_url"):
        photo_url = artist_info["photo_url"]
        canonical_artist_name = artist_info.get("canonical_artist_name", artist_name)
        
        print(f"[ARTIST_PHOTO_LOGIC] Spotify returned artist photo URL: {photo_url}. Artist: '{canonical_artist_name}'")
        downloaded_path = download_artist_image_to_cache(photo_url, canonical_artist_name)
        return downloaded_path, artist_info
    
    # Strategy 4: Fallback to album art if we have fallback track info
    if fallback_track_info:
        print(f"[ARTIST_PHOTO_LOGIC] No artist profile photo found. Attempting fallback to album art from track: '{fallback_track_info.get('track_name', 'Unknown')}'")
        
        # Create identifier_info for album art lookup
        identifier_info = {
            "album_name_hint": fallback_track_info.get("album_name", ""),
            "album_mbid": None,  # We don't have MBID for artist mode typically
            "track_uri": fallback_track_info.get("track_uri"),
            "source_data_type": "spotify" if fallback_track_info.get("track_uri") else "unknown"
        }
        
        # Use existing album art logic as fallback
        fallback_art_path, _ = get_album_art_path_and_spotify_info(
            artist_name, 
            fallback_track_info.get("track_name", ""), 
            identifier_info
        )
        
        if fallback_art_path:
            print(f"[ARTIST_PHOTO_LOGIC] Successfully retrieved fallback album art for artist '{artist_name}' from track '{fallback_track_info.get('track_name')}'")
            # Return the album art path, but keep the artist_info (even if it was None or had no photo)
            return fallback_art_path, artist_info
        else:
            print(f"[ARTIST_PHOTO_LOGIC] Fallback album art retrieval also failed for artist '{artist_name}'")
    
    # No photo found through any strategy
    if artist_info:
        print(f"[ARTIST_PHOTO_LOGIC] Found Spotify artist info for '{artist_name}' (Source: {artist_info.get('source')}) but no photo URL and no successful fallback.")
    else:
        print(f"[ARTIST_PHOTO_LOGIC] No Spotify artist info found for '{artist_name}' and no successful fallback.")
    
    return None, artist_info


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
    
    # Simulate Last.fm type call (no track_uri, has album_name_hint)
    identifier_info_1_lastfm = {
        "album_name_hint": test_album_1_hint,
        "album_mbid": None, # Assume no MBID for this simple test
        "track_uri": None,
        "source_data_type": "lastfm"
    }
    # art_path_data_1 = get_album_art_path(test_artist_1, test_track_1, identifier_info_1_lastfm)
    art_path_1, spotify_info_1 = get_album_art_path_and_spotify_info(test_artist_1, test_track_1, identifier_info_1_lastfm)

    # art_path_1 = None
    if isinstance(art_path_1, str) and art_path_1:
        art_path_1 = art_path_1
    elif isinstance(art_path_1, dict) and art_path_1.get("art_path"): # If you update get_album_art_path_and_spotify_info later
        art_path_1 = art_path_1["art_path"]
        print(f"Canonical album name from Spotify: {art_path_1.get('canonical_album_name')}")

    print(f"Art path for {test_track_1}: {art_path_1}")
    if art_path_1 and os.path.exists(art_path_1):
        dom_color_1 = get_dominant_color(art_path_1)
        print(f"Dominant color for {test_track_1} (RGB): {dom_color_1}")
        if spotify_info_1:
            print(f"Spotify Info for test 1: Canonical Album='{spotify_info_1.get('canonical_album_name')}', Source='{spotify_info_1.get('source')}'")
    elif art_path_1:
        print(f"Warning: Art path {art_path_1} was returned but file does not exist.")

    # Test 2: A track that might have multiple album versions
    test_artist_2 = "Paramore"
    test_track_2 = "Misery Business"
    test_album_2_hint = "Riot!"
    print(f"\n[STANDALONE TEST 2] With: {test_artist_2} - {test_track_2} (Album Hint: {test_album_2_hint})")
    # Simulate Last.fm type call
    identifier_info_2_lastfm = {
        "album_name_hint": test_album_2_hint,
        "album_mbid": None, 
        "track_uri": None,
        "source_data_type": "lastfm"
    }
    # art_path_data_2 = get_album_art_path(test_artist_2, test_track_2, identifier_info_2_lastfm)
    art_path_2, _ = get_album_art_path_and_spotify_info(test_artist_2, test_track_2, identifier_info_2_lastfm)

    # art_path_2 = None
    if isinstance(art_path_2, str) and art_path_2:
        art_path_2 = art_path_2
    elif isinstance(art_path_2, dict) and art_path_2.get("art_path"):
        art_path_2 = art_path_2["art_path"]

    print(f"Art path for {test_track_2}: {art_path_2}")
    if art_path_2 and os.path.exists(art_path_2):
        dom_color_2 = get_dominant_color(art_path_2)
        print(f"Dominant color for {test_track_2} (RGB): {dom_color_2}")

    # Test 3: Potentially problematic (non-Latin characters)
    test_artist_3 = "ヨルシカ"
    test_track_3 = "晴る"
    test_album_3_hint = "幻燈"
    print(f"\n[STANDALONE TEST 3] With: {test_artist_3} - {test_track_3} (Album Hint: {test_album_3_hint})")
    # Simulate Last.fm type call
    identifier_info_3_lastfm = {
        "album_name_hint": test_album_3_hint,
        "album_mbid": None, 
        "track_uri": None,
        "source_data_type": "lastfm"
    }
    # art_path_data_3 = get_album_art_path(test_artist_3, test_track_3, identifier_info_3_lastfm)
    art_path_3, _ = get_album_art_path_and_spotify_info(test_artist_3, test_track_3, identifier_info_3_lastfm)

    # art_path_3 = None
    if isinstance(art_path_3, str) and art_path_3:
        art_path_3 = art_path_3
    elif isinstance(art_path_3, dict) and art_path_3.get("art_path"):
        art_path_3 = art_path_3["art_path"]

    print(f"Art path for {test_track_3} by {test_artist_3}: {art_path_3}")
    if art_path_3 and os.path.exists(art_path_3):
        dom_color_3 = get_dominant_color(art_path_3)
        print(f"Dominant color for {test_track_3} (RGB): {dom_color_3}")

    # Test 4: Cache hit test (re-run Test 1)
    print(f"\n[STANDALONE TEST 4] Cache Re-Test for: {test_artist_1} - {test_track_1}")
    # art_path_data_1_again = get_album_art_path(test_artist_1, test_track_1, identifier_info_1_lastfm) # Using same identifier info
    art_path_1_again, _ = get_album_art_path_and_spotify_info(test_artist_1, test_track_1, identifier_info_1_lastfm)
    
    # art_path_1_again_val = None
    # if isinstance(art_path_data_1_again, str) and art_path_data_1_again:
    #      art_path_1_again_val = art_path_data_1_again
    # elif isinstance(art_path_data_1_again, dict) and art_path_data_1_again.get("art_path"):
    #     art_path_1_again_val = art_path_data_1_again["art_path"]
    art_path_1_again_val = art_path_1_again # Direct assignment from new function call

    print(f"Art path (2nd call): {art_path_1_again_val}")
    if art_path_1_again_val and os.path.exists(art_path_1_again_val):
        dom_color_1_again = get_dominant_color(art_path_1_again_val) # Should hit dominant color cache
        print(f"Dominant color (2nd call): {dom_color_1_again}")

    # Test 5: Simulate a Spotify data call with a track URI
    test_artist_5 = "Taylor Swift"
    test_track_5 = "Style"
    test_album_5_hint = "1989 (Taylor's Version)" # This might be the album name in some Spotify entries
    test_track_uri_5 = "spotify:track:0ug5NqcwcFR2x02gGFeV3Z" # Example URI for Style (Taylor's Version)
                                                        # For original 1989 Style: "spotify:track:3LmvfNUQtglbTrydsdIqFU"
    print(f"\n[STANDALONE TEST 5] Spotify direct URI lookup: {test_artist_5} - {test_track_5} (URI: {test_track_uri_5})")
    identifier_info_5_spotify = {
        "album_name_hint": test_album_5_hint, # Hint might still be passed but URI takes precedence
        "album_mbid": None, 
        "track_uri": test_track_uri_5,
        "source_data_type": "spotify"
    }
    # art_path_data_5 = get_album_art_path(test_artist_5, test_track_5, identifier_info_5_spotify)
    art_path_5, spotify_info_5 = get_album_art_path_and_spotify_info(test_artist_5, test_track_5, identifier_info_5_spotify)

    # art_path_5 = None
    # if isinstance(art_path_data_5, str) and art_path_data_5:
    #     art_path_5 = art_path_data_5
    # No longer needed, art_path_5 is directly the path or None

    print(f"Art path for {test_track_5} (from URI): {art_path_5}")
    if art_path_5 and os.path.exists(art_path_5):
        dom_color_5 = get_dominant_color(art_path_5)
        print(f"Dominant color for {test_track_5} (RGB): {dom_color_5}")
        if spotify_info_5:
            print(f"Spotify Info for test 5: Canonical Album='{spotify_info_5.get('canonical_album_name')}', Source='{spotify_info_5.get('source')}'")


    # Test 6: Artist Profile Photo Tests (New Phase 2 functionality)
    print("\n=== PHASE 2: TESTING ARTIST PROFILE PHOTO FUNCTIONALITY ===")
    
    # Test 6A: Well-known artist with profile photo
    test_artist_6a = "Taylor Swift"
    print(f"\n[STANDALONE TEST 6A] Artist Profile Photo: {test_artist_6a}")
    artist_photo_path_6a, artist_info_6a = get_artist_profile_photo_and_spotify_info(test_artist_6a)
    
    print(f"Artist photo path for {test_artist_6a}: {artist_photo_path_6a}")
    if artist_photo_path_6a and os.path.exists(artist_photo_path_6a):
        dom_color_6a = get_dominant_color(artist_photo_path_6a)
        print(f"Dominant color for {test_artist_6a} photo (RGB): {dom_color_6a}")
        if artist_info_6a:
            print(f"Artist Info: Name='{artist_info_6a.get('canonical_artist_name')}', Popularity={artist_info_6a.get('popularity', 0)}, Source='{artist_info_6a.get('source')}'")
    elif artist_photo_path_6a:
        print(f"Warning: Artist photo path {artist_photo_path_6a} was returned but file does not exist.")
    
    # Test 6B: Artist with fallback to album art
    test_artist_6b = "Paramore"
    fallback_track_info_6b = {
        "track_name": "Misery Business",
        "album_name": "Riot!",
        "track_uri": None  # Test without URI
    }
    print(f"\n[STANDALONE TEST 6B] Artist with Fallback: {test_artist_6b}")
    artist_photo_path_6b, artist_info_6b = get_artist_profile_photo_and_spotify_info(
        test_artist_6b, 
        fallback_track_info=fallback_track_info_6b
    )
    
    print(f"Artist photo/art path for {test_artist_6b}: {artist_photo_path_6b}")
    if artist_photo_path_6b and os.path.exists(artist_photo_path_6b):
        dom_color_6b = get_dominant_color(artist_photo_path_6b)
        print(f"Dominant color for {test_artist_6b} photo/art (RGB): {dom_color_6b}")
        if artist_info_6b:
            print(f"Artist Info: Name='{artist_info_6b.get('canonical_artist_name')}', Source='{artist_info_6b.get('source')}'")
    
    # Test 6C: Non-existent or very obscure artist
    test_artist_6c = "NonExistentArtistTestName12345"
    print(f"\n[STANDALONE TEST 6C] Non-existent Artist: {test_artist_6c}")
    artist_photo_path_6c, artist_info_6c = get_artist_profile_photo_and_spotify_info(test_artist_6c)
    
    print(f"Artist photo path for {test_artist_6c}: {artist_photo_path_6c}")
    print(f"Artist info for {test_artist_6c}: {artist_info_6c}")
    
    # Test 6D: Artist with special characters (test name cleaning)
    test_artist_6d = "ヨルシカ"  # Japanese artist name
    print(f"\n[STANDALONE TEST 6D] Special Characters Artist: {test_artist_6d}")
    artist_photo_path_6d, artist_info_6d = get_artist_profile_photo_and_spotify_info(test_artist_6d)
    
    print(f"Artist photo path for {test_artist_6d}: {artist_photo_path_6d}")
    if artist_photo_path_6d and os.path.exists(artist_photo_path_6d):
        dom_color_6d = get_dominant_color(artist_photo_path_6d)
        print(f"Dominant color for {test_artist_6d} photo (RGB): {dom_color_6d}")
        if artist_info_6d:
            print(f"Artist Info: Name='{artist_info_6d.get('canonical_artist_name')}', Genres={artist_info_6d.get('genres', [])[:3]}")
    
    # Test 6E: Cache hit test (re-run Test 6A)
    print(f"\n[STANDALONE TEST 6E] Cache Re-Test for: {test_artist_6a}")
    artist_photo_path_6e, artist_info_6e = get_artist_profile_photo_and_spotify_info(test_artist_6a)
    
    print(f"Artist photo path (2nd call): {artist_photo_path_6e}")
    if artist_photo_path_6e and os.path.exists(artist_photo_path_6e):
        dom_color_6e = get_dominant_color(artist_photo_path_6e)  # Should hit dominant color cache
        print(f"Dominant color (2nd call): {dom_color_6e}")
        print(f"Cache verification: {'SUCCESS' if artist_photo_path_6e == artist_photo_path_6a else 'FAILED'}")

    print("\n=== PHASE 2 TESTING COMPLETE ===")
    print("\n--- Standalone Test Complete ---")
    print(f"Check the '{ART_CACHE_DIR}' folder for new images and JSON cache files.")
    print("New files should include: spotify_artist_cache.json and artist profile photos.")
    print("Review console output for [CACHE DEBUG], [SPOTIFY AUTH DEBUG], [SPOTIFY_ARTIST_TRACE], etc., messages.")
    print("Ensure these messages respect the DEBUG_CACHE_ALBUM_ART_UTILS setting in configurations.txt.")