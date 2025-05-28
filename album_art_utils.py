# album_art_utils.py
import requests
import json
import os
from PIL import Image, ImageOps
from io import BytesIO
import time
from urllib.parse import quote

# --- Configuration ---
DEBUG_CACHE = True # <--- SET TO True FOR DETAILED CACHE LOGGING
USER_AGENT = "SpotifyRaceChart/1.0 lightningfalconyt@gmail.com"
ART_CACHE_DIR = "album_art_cache"
if not os.path.exists(ART_CACHE_DIR):
    os.makedirs(ART_CACHE_DIR)

mbid_cache_file = os.path.join(ART_CACHE_DIR, "mbid_cache.json")
dominant_color_cache_file = os.path.join(ART_CACHE_DIR, "dominant_color_cache.json")

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

mbid_cache = load_json_cache(mbid_cache_file)
dominant_color_cache = load_json_cache(dominant_color_cache_file)


def get_release_mbid(artist_name, album_name):
    cache_key = f"{artist_name.lower().strip()}_{album_name.lower().strip()}" # Added .strip()
    if DEBUG_CACHE: print(f"[CACHE DEBUG] MBID check for key: '{cache_key}' (Artist: '{artist_name}', Album: '{album_name}')")
    
    if cache_key in mbid_cache:
        if DEBUG_CACHE: print(f"[CACHE DEBUG] MBID Cache HIT for key: '{cache_key}'. Value: {mbid_cache[cache_key]}")
        return mbid_cache[cache_key]
    
    if DEBUG_CACHE: print(f"[CACHE DEBUG] MBID Cache MISS for key: '{cache_key}'. Querying API.")
    # ... (rest of the MBID fetching logic, unchanged) ...
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
            mbid_cache[cache_key] = release_mbid # Store in cache
            save_json_cache(mbid_cache, mbid_cache_file) # Save cache to file
            print(f"Found MBID: {release_mbid} for {artist_name} - {album_name}")
            time.sleep(1) 
            return release_mbid
        else:
            print(f"No MBID found for {artist_name} - {album_name}")
            mbid_cache[cache_key] = None # Cache failure
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


def download_image_to_cache(image_url, album_name, artist_name):
    if not image_url:
        return None

    safe_album_name = "".join(c if c.isalnum() or c in " .-_" else "_" for c in album_name.strip())[:50]
    safe_artist_name = "".join(c if c.isalnum() or c in " .-_" else "_" for c in artist_name.strip())[:50]
    
    filename_base = f"{safe_artist_name}_{safe_album_name}"
    try:
        extension = os.path.splitext(image_url.split('?')[0])[-1]
        if not extension or len(extension) > 5 or len(extension) < 2: # Basic check
            extension = ".jpg"
    except:
        extension = ".jpg"

    cached_image_path = os.path.join(ART_CACHE_DIR, filename_base + extension)
    if DEBUG_CACHE: print(f"[CACHE DEBUG] Image check for path: '{cached_image_path}'")

    if os.path.exists(cached_image_path):
        if DEBUG_CACHE: print(f"[CACHE DEBUG] Image Cache HIT: '{cached_image_path}'")
        return cached_image_path
    
    if DEBUG_CACHE: print(f"[CACHE DEBUG] Image Cache MISS: '{cached_image_path}'. Downloading image.")
    # ... (rest of the image download logic, unchanged) ...
    print(f"Downloading image: {image_url} to {cached_image_path}")
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(image_url, headers=headers, stream=True, timeout=15)
        response.raise_for_status()
        with open(cached_image_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return cached_image_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image {image_url}: {e}")
        if os.path.exists(cached_image_path):
            os.remove(cached_image_path)
        return None

def get_dominant_color(image_path, palette_size=1):
    cache_key = os.path.basename(image_path)
    if DEBUG_CACHE: print(f"[CACHE DEBUG] Dominant color check for key: '{cache_key}'")

    if cache_key in dominant_color_cache:
        if DEBUG_CACHE: print(f"[CACHE DEBUG] Dominant Color Cache HIT for '{cache_key}'. Value: {dominant_color_cache[cache_key]}")
        return tuple(dominant_color_cache[cache_key])

    if DEBUG_CACHE: print(f"[CACHE DEBUG] Dominant Color Cache MISS for '{cache_key}'. Calculating color.")
    # ... (rest of dominant color logic, unchanged) ...
    if not image_path or not os.path.exists(image_path):
        return (128, 128, 128) 
    try:
        img = Image.open(image_path).convert('RGB')
        img.thumbnail((100, 100)) 
        paletted = img.quantize(colors=palette_size * 5, method=Image.Quantize.MEDIANCUT)
        palette = paletted.getpalette()
        color_counts = sorted(paletted.getcolors(), reverse=True)
        if not color_counts:
            dominant_color_cache[cache_key] = [128, 128, 128]
            save_json_cache(dominant_color_cache, dominant_color_cache_file)
            return (128, 128, 128)
        dominant_color_index = color_counts[0][1]
        r = palette[dominant_color_index * 3]
        g = palette[dominant_color_index * 3 + 1]
        b = palette[dominant_color_index * 3 + 2]
        dominant_rgb = (r, g, b)
        dominant_color_cache[cache_key] = list(dominant_rgb)
        save_json_cache(dominant_color_cache, dominant_color_cache_file)
        return dominant_rgb
    except Exception as e:
        print(f"Error getting dominant color for {image_path}: {e}")
        dominant_color_cache[cache_key] = [128, 128, 128]
        save_json_cache(dominant_color_cache, dominant_color_cache_file)
        return (128, 128, 128)

# --- Unchanged functions: get_album_art_url, get_album_art_path, example usage ---
# (You can keep the rest of the file as it was)

def get_album_art_url(release_mbid):
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
                return image['thumbnails'].get('small', image.get('image'))
        print(f"No 'front' image URL found for MBID: {release_mbid}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching album art URL for MBID {release_mbid}: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON response for cover art of MBID {release_mbid}")
        return None

def get_album_art_path(artist_name, album_name):
    release_mbid = get_release_mbid(artist_name, album_name)
    if not release_mbid: return None
    art_url = get_album_art_url(release_mbid)
    if not art_url: return None
    return download_image_to_cache(art_url, album_name, artist_name)

if __name__ == "__main__":
    print("Testing Album Art Utilities with DEBUG_CACHE enabled...")
    DEBUG_CACHE = True # Ensure it's true for direct testing
    
    test_artist_3 = "Perfume"
    test_album_3 = "Future Pop"
    print(f"\nTesting with: {test_artist_3} - {test_album_3}")
    art_path_3 = get_album_art_path(test_artist_3, test_album_3) # First call
    print(f"Cached art path for {test_album_3}: {art_path_3}")
    if art_path_3:
        dom_color_3 = get_dominant_color(art_path_3)
        print(f"Dominant color for {test_album_3} (RGB): {dom_color_3}")

    print(f"\nTesting AGAIN with: {test_artist_3} - {test_album_3} (should hit cache)")
    art_path_3_again = get_album_art_path(test_artist_3, test_album_3) # Second call
    print(f"Cached art path (2nd call): {art_path_3_again}")
    if art_path_3_again:
        dom_color_3_again = get_dominant_color(art_path_3_again)
        print(f"Dominant color (2nd call): {dom_color_3_again}")


    print("\nCheck the 'album_art_cache' folder and console for [CACHE DEBUG] messages.")