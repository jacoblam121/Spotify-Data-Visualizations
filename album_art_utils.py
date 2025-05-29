# album_art_utils.py
import requests
import json
import os
from PIL import Image, ImageOps # ImageOps might not be used directly here, but good to keep if PIL is used
from io import BytesIO
import time
from urllib.parse import quote
import base64 # For Spotify Auth

# --- Configuration ---
DEBUG_CACHE = True # <--- SET TO True FOR DETAILED CACHE LOGGING
USER_AGENT = "SpotifyRaceChart/1.0 lightningfalconyt@gmail.com" # KEEP THIS OR UPDATE AS NEEDED
ART_CACHE_DIR = "album_art_cache"
if not os.path.exists(ART_CACHE_DIR):
    os.makedirs(ART_CACHE_DIR)

# --- Spotify API Configuration ---
SPOTIFY_CLIENT_ID = "eaf67929214947d19e34182fb20e96bc" # YOUR CLIENT ID
SPOTIFY_CLIENT_SECRET = "822e6e3f9d1149d4ad5520237d8385a3" # YOUR CLIENT SECRET
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1/"

# --- Cache Files ---
mbid_cache_file = os.path.join(ART_CACHE_DIR, "mbid_cache.json") # Will become legacy
dominant_color_cache_file = os.path.join(ART_CACHE_DIR, "dominant_color_cache.json")
spotify_info_cache_file = os.path.join(ART_CACHE_DIR, "spotify_info_cache.json") # New cache

# --- Global Caches (In-Memory) ---
_spotify_access_token_cache = {
    "token": None,
    "expires_at": 0
}

def load_json_cache(filepath):
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

# Load caches
mbid_cache = load_json_cache(mbid_cache_file) # Keep for now, but new MBID calls will be disabled
dominant_color_cache = load_json_cache(dominant_color_cache_file)
spotify_info_cache = load_json_cache(spotify_info_cache_file)


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

def get_spotify_track_album_info(artist_name, track_name, album_name_hint):
    """
    Searches Spotify for a track and returns its album art URL, canonical album name,
    Spotify album ID, and Spotify artist IDs.
    Uses album_name_hint to disambiguate if multiple album versions exist.
    """
    cache_key = f"spotify_{artist_name.lower().strip()}_{track_name.lower().strip()}_{album_name_hint.lower().strip()}"
    if DEBUG_CACHE: print(f"[CACHE DEBUG] Spotify info check for key: '{cache_key}' (Artist: '{artist_name}', Track: '{track_name}', Album Hint: '{album_name_hint}')")

    if cache_key in spotify_info_cache:
        if DEBUG_CACHE: print(f"[CACHE DEBUG] Spotify Info Cache HIT for key: '{cache_key}'. Value: {spotify_info_cache[cache_key]}")
        return spotify_info_cache[cache_key]

    if DEBUG_CACHE: print(f"[CACHE DEBUG] Spotify Info Cache MISS for key: '{cache_key}'. Querying API.")
    
    access_token = _get_spotify_access_token()
    if not access_token:
        return None

    # Spotify search query: be specific with track and artist. Album name is harder to match directly in search query.
    # We will use album_name_hint to filter results.
    search_query = f'track:"{quote(track_name)}" artist:"{quote(artist_name)}"'
    # search_query = f'track:"{quote(track_name)}" artist:"{quote(artist_name)}" album:"{quote(album_name_hint)}"' # Alternative
    url = f"{SPOTIFY_API_BASE_URL}search?q={search_query}&type=track&limit=10" # Get a few results to check album match
    
    headers = {
        'Authorization': f"Bearer {access_token}",
        'User-Agent': USER_AGENT
    }

    print(f"Spotify API call for: Artist='{artist_name}', Track='{track_name}', Album Hint='{album_name_hint}'")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('tracks') and data['tracks'].get('items'):
            items = data['tracks']['items']
            
            best_match = None
            
            # Try to find a match where the album name is similar to album_name_hint
            # This is a simple similarity check, can be improved (e.g., Levenshtein distance)
            normalized_album_hint = album_name_hint.lower().strip()
            
            for item in items:
                spotify_album_name = item.get('album', {}).get('name', '').lower().strip()
                if normalized_album_hint in spotify_album_name or spotify_album_name in normalized_album_hint:
                    best_match = item
                    if DEBUG_CACHE: print(f"[SPOTIFY DEBUG] Found album name hint match: '{item.get('album', {}).get('name')}'")
                    break 
            
            if not best_match and items: # If no direct album hint match, take the first result
                best_match = items[0]
                if DEBUG_CACHE: print(f"[SPOTIFY DEBUG] No direct album hint match. Taking first result: '{best_match.get('album', {}).get('name')}'")


            if best_match:
                album_info = best_match.get('album', {})
                canonical_album_name = album_info.get('name')
                spotify_album_id = album_info.get('id')
                
                art_url = None
                if album_info.get('images'):
                    # Prefer largest image, but Spotify usually returns 3 sizes: 640, 300, 64
                    art_url = album_info['images'][0]['url'] # Largest is usually first

                artist_objects = best_match.get('artists', [])
                spotify_artist_ids = [artist['id'] for artist in artist_objects if artist.get('id')]
                # Could also store primary artist name from Spotify if desired:
                # primary_spotify_artist_name = artist_objects[0]['name'] if artist_objects else artist_name

                result = {
                    "art_url": art_url,
                    "canonical_album_name": canonical_album_name,
                    "spotify_album_id": spotify_album_id,
                    "spotify_artist_ids": spotify_artist_ids,
                    "source": "spotify"
                }
                spotify_info_cache[cache_key] = result
                save_json_cache(spotify_info_cache, spotify_info_cache_file)
                print(f"Found Spotify info: Album='{canonical_album_name}', Art URL: {'Yes' if art_url else 'No'}")
                time.sleep(0.2) # Be respectful to API rate limits
                return result
        
        print(f"No suitable track found on Spotify for: {artist_name} - {track_name} (Album hint: {album_name_hint})")
        spotify_info_cache[cache_key] = None # Cache failure
        save_json_cache(spotify_info_cache, spotify_info_cache_file)
        time.sleep(0.2)
        return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Spotify info for {artist_name} - {track_name}: {e}")
        time.sleep(0.2)
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON response from Spotify for {artist_name} - {track_name}")
        time.sleep(0.2)
        return None

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
    print("Testing Album Art Utilities (Spotify Integration) with DEBUG_CACHE enabled...")
    DEBUG_CACHE = True 
    
    # --- Test Cases ---
    # Test 1: A well-known track
    test_artist_1 = "Taylor Swift"
    test_track_1 = "Cruel Summer"
    test_album_1_hint = "Lover" # Last.fm might report this
    print(f"\nTesting with: {test_artist_1} - {test_track_1} (Album Hint: {test_album_1_hint})")
    art_path_1 = get_album_art_path(test_artist_1, test_track_1, test_album_1_hint)
    print(f"Art path for {test_track_1}: {art_path_1}")
    if art_path_1:
        dom_color_1 = get_dominant_color(art_path_1)
        print(f"Dominant color for {test_track_1} (RGB): {dom_color_1}")

    # Test 2: A track that might have multiple album versions (e.g. live, deluxe)
    test_artist_2 = "Paramore"
    test_track_2 = "Misery Business"
    test_album_2_hint = "Riot!" 
    print(f"\nTesting with: {test_artist_2} - {test_track_2} (Album Hint: {test_album_2_hint})")
    art_path_2 = get_album_art_path(test_artist_2, test_track_2, test_album_2_hint)
    print(f"Art path for {test_track_2}: {art_path_2}")
    if art_path_2:
        dom_color_2 = get_dominant_color(art_path_2)
        print(f"Dominant color for {test_track_2} (RGB): {dom_color_2}")

    # Test 3: Your previous Perfume example, but using track name now
    test_artist_3 = "Perfume"
    test_track_3 = "Future Pop" # Assuming track title is same as album, adjust if not
    test_album_3_hint = "Future Pop"
    print(f"\nTesting with: {test_artist_3} - {test_track_3} (Album Hint: {test_album_3_hint})")
    art_path_3 = get_album_art_path(test_artist_3, test_track_3, test_album_3_hint) 
    print(f"Art path for {test_track_3}: {art_path_3}")
    if art_path_3:
        dom_color_3 = get_dominant_color(art_path_3)
        print(f"Dominant color for {test_track_3} (RGB): {dom_color_3}")

    print(f"\nTesting AGAIN with: {test_artist_3} - {test_track_3} (should hit Spotify info cache & image cache)")
    art_path_3_again = get_album_art_path(test_artist_3, test_track_3, test_album_3_hint)
    print(f"Art path (2nd call): {art_path_3_again}")
    if art_path_3_again:
        dom_color_3_again = get_dominant_color(art_path_3_again)
        print(f"Dominant color (2nd call): {dom_color_3_again}")

    # Test 4: A potentially problematic one (e.g., from your demo: 晴る - Yorushika)
    # Note: Spotify search can be sensitive to non-Latin characters if not perfectly matched.
    # This will test how well the quoting and API handle it.
    test_artist_4 = "ヨルシカ" # Yorushika in Japanese
    test_track_4 = "晴る" # Haru in Japanese
    test_album_4_hint = "幻燈" # Album name for "晴る" is "Magic Lantern" (幻燈) - this hint is important
    # Or if Last.fm reports album as "晴る" (single)
    # test_album_4_hint = "晴る"

    print(f"\nTesting with: {test_artist_4} - {test_track_4} (Album Hint: {test_album_4_hint})")
    art_path_4 = get_album_art_path(test_artist_4, test_track_4, test_album_4_hint)
    print(f"Art path for {test_track_4} by {test_artist_4}: {art_path_4}")
    if art_path_4:
        dom_color_4 = get_dominant_color(art_path_4)
        print(f"Dominant color for {test_track_4} (RGB): {dom_color_4}")


    print("\nCheck the 'album_art_cache' folder for new images and 'spotify_info_cache.json'.")
    print("Also check console for [CACHE DEBUG] and [SPOTIFY ...] messages.")