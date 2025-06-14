#!/usr/bin/env python3
"""
Spotify Related Artists Deep Debug
==================================
Comprehensive investigation of why related artists endpoint fails.
If album art works, related artists should work too - let's find the issue.
"""

import requests
import time
import json
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from album_art_utils import _get_spotify_access_token, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

def test_spotify_endpoints_comprehensive():
    """Comprehensive test to isolate the related artists issue."""
    print("🔍 Spotify Related Artists Deep Debug")
    print("=" * 50)
    
    # Test multiple token acquisition methods
    print("\n1️⃣ Testing Token Acquisition Methods")
    print("-" * 45)
    
    # Method 1: Use existing album art token
    print("Method 1: Using album_art_utils token...")
    token1 = _get_spotify_access_token()
    print(f"   Token 1: {'✅ Success' if token1 else '❌ Failed'}")
    if token1:
        print(f"   Length: {len(token1)}, First 20 chars: {token1[:20]}")
    
    # Method 2: Fresh manual token request
    print("\nMethod 2: Fresh manual token request...")
    token2 = get_fresh_spotify_token()
    print(f"   Token 2: {'✅ Success' if token2 else '❌ Failed'}")
    if token2:
        print(f"   Length: {len(token2)}, First 20 chars: {token2[:20]}")
        print(f"   Same as token 1: {token1 == token2 if token1 and token2 else 'N/A'}")
    
    # Use the best available token
    access_token = token1 or token2
    if not access_token:
        print("❌ No valid token available - cannot proceed")
        return
    
    print(f"\n🔑 Using token: {access_token[:30]}...")
    
    # Test endpoints with different approaches
    test_artist_id = "06HL4z0CvFAxyc27GXpf02"  # Taylor Swift
    test_artist_name = "Taylor Swift"
    
    print(f"\n2️⃣ Testing Working Endpoints (baseline)")
    print("-" * 45)
    
    # Test search (this works)
    test_search(access_token, test_artist_name)
    
    # Test artist info (this works) 
    test_artist_info(access_token, test_artist_id)
    
    # Test albums (similar to related artists complexity)
    test_artist_albums(access_token, test_artist_id)
    
    print(f"\n3️⃣ Testing Related Artists with Different Approaches")
    print("-" * 55)
    
    # Approach 1: Basic request
    test_related_artists_basic(access_token, test_artist_id)
    
    # Approach 2: Different headers
    test_related_artists_different_headers(access_token, test_artist_id)
    
    # Approach 3: Different URL formats
    test_related_artists_url_variants(access_token, test_artist_id)
    
    # Approach 4: Different artists (maybe some work?)
    test_related_artists_multiple_artists(access_token)
    
    # Approach 5: Compare with working album art request
    test_compare_with_album_art(access_token, test_artist_id)

def get_fresh_spotify_token():
    """Get a completely fresh token to rule out caching issues."""
    try:
        auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode('utf-8')).decode('utf-8')
        headers = {
            'Authorization': f"Basic {auth_header}",
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        payload = {'grant_type': 'client_credentials'}
        
        response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=payload)
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data['access_token']
        else:
            print(f"   Token request failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"   Token exception: {e}")
        return None

def test_search(access_token, artist_name):
    """Test search endpoint (known to work)."""
    try:
        url = "https://api.spotify.com/v1/search"
        params = {'q': f'artist:"{artist_name}"', 'type': 'artist', 'limit': 1}
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = requests.get(url, params=params, headers=headers)
        print(f"Search: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
        
        if response.status_code == 200:
            data = response.json()
            artists = data.get('artists', {}).get('items', [])
            if artists:
                print(f"   Found: {artists[0]['name']} (ID: {artists[0]['id']})")
        
    except Exception as e:
        print(f"Search: ❌ Exception: {e}")

def test_artist_info(access_token, artist_id):
    """Test artist info endpoint (known to work)."""
    try:
        url = f"https://api.spotify.com/v1/artists/{artist_id}"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = requests.get(url, headers=headers)
        print(f"Artist Info: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Artist: {data['name']}, Followers: {data['followers']['total']:,}")
        
    except Exception as e:
        print(f"Artist Info: ❌ Exception: {e}")

def test_artist_albums(access_token, artist_id):
    """Test artist albums endpoint (similar complexity to related artists)."""
    try:
        url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
        params = {'limit': 5}
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = requests.get(url, params=params, headers=headers)
        print(f"Artist Albums: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
        
        if response.status_code == 200:
            data = response.json()
            albums = data.get('items', [])
            print(f"   Found {len(albums)} albums")
        elif response.status_code == 404:
            print(f"   404 Error - same as related artists!")
        else:
            print(f"   Error: {response.text}")
        
    except Exception as e:
        print(f"Artist Albums: ❌ Exception: {e}")

def test_related_artists_basic(access_token, artist_id):
    """Test basic related artists request."""
    try:
        url = f"https://api.spotify.com/v1/artists/{artist_id}/related-artists"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        response = requests.get(url, headers=headers)
        print(f"Related Artists (Basic): {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
        
        if response.status_code == 200:
            data = response.json()
            artists = data.get('artists', [])
            print(f"   Found {len(artists)} related artists")
            if artists:
                print(f"   First 3: {', '.join(a['name'] for a in artists[:3])}")
        else:
            print(f"   Error: {response.text}")
            print(f"   Headers received: {dict(response.headers)}")
        
    except Exception as e:
        print(f"Related Artists (Basic): ❌ Exception: {e}")

def test_related_artists_different_headers(access_token, artist_id):
    """Test related artists with different headers."""
    try:
        url = f"https://api.spotify.com/v1/artists/{artist_id}/related-artists"
        
        # Try different header combinations
        header_variations = [
            {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            },
            {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            },
            {
                'Authorization': f'Bearer {access_token}',
                'User-Agent': 'SpotifyDataViz/1.0'
            },
            {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'SpotifyDataViz/1.0'
            }
        ]
        
        for i, headers in enumerate(header_variations, 1):
            try:
                response = requests.get(url, headers=headers)
                print(f"Related Artists (Headers v{i}): {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
                
                if response.status_code == 200:
                    data = response.json()
                    artists = data.get('artists', [])
                    print(f"   SUCCESS! Found {len(artists)} related artists")
                    return True
                    
            except Exception as e:
                print(f"Related Artists (Headers v{i}): ❌ Exception: {e}")
            
            time.sleep(0.1)
        
        return False
        
    except Exception as e:
        print(f"Related Artists (Different Headers): ❌ Exception: {e}")
        return False

def test_related_artists_url_variants(access_token, artist_id):
    """Test different URL variants for related artists."""
    try:
        url_variants = [
            f"https://api.spotify.com/v1/artists/{artist_id}/related-artists",
            f"https://api.spotify.com/v1/artists/{artist_id}/related",
            f"https://api.spotify.com/v1/artist/{artist_id}/related-artists", 
            f"https://open.spotify.com/v1/artists/{artist_id}/related-artists"
        ]
        
        headers = {'Authorization': f'Bearer {access_token}'}
        
        for i, url in enumerate(url_variants, 1):
            try:
                response = requests.get(url, headers=headers)
                print(f"URL Variant {i}: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
                
                if response.status_code == 200:
                    data = response.json()
                    artists = data.get('artists', [])
                    print(f"   SUCCESS with URL: {url}")
                    print(f"   Found {len(artists)} related artists")
                    return True
                    
            except Exception as e:
                print(f"URL Variant {i}: ❌ Exception: {e}")
            
            time.sleep(0.1)
        
        return False
        
    except Exception as e:
        print(f"Related Artists (URL Variants): ❌ Exception: {e}")
        return False

def test_related_artists_multiple_artists(access_token):
    """Test related artists with different artist IDs - maybe some work?"""
    try:
        test_artists = [
            ("06HL4z0CvFAxyc27GXpf02", "Taylor Swift"),
            ("4Z8W4fKeB5YxbusRsdQVPb", "Radiohead"),  
            ("1Xyo4u8uXC1ZmMpatF05PJ", "The Weeknd"),
            ("0k17h0D3J5VfsdmQ1iZtE9", "Pink Floyd"),
            ("3WrFJ7ztbogyGnTHbHJFl2", "The Beatles")
        ]
        
        headers = {'Authorization': f'Bearer {access_token}'}
        
        for artist_id, artist_name in test_artists:
            try:
                url = f"https://api.spotify.com/v1/artists/{artist_id}/related-artists"
                response = requests.get(url, headers=headers)
                
                print(f"{artist_name}: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
                
                if response.status_code == 200:
                    data = response.json()
                    artists = data.get('artists', [])
                    print(f"   SUCCESS! Found {len(artists)} related artists")
                    if artists:
                        print(f"   First 3: {', '.join(a['name'] for a in artists[:3])}")
                    return True
                    
            except Exception as e:
                print(f"{artist_name}: ❌ Exception: {e}")
            
            time.sleep(0.2)
        
        return False
        
    except Exception as e:
        print(f"Multiple Artists Test: ❌ Exception: {e}")
        return False

def test_compare_with_album_art(access_token, artist_id):
    """Compare the related artists request with a working album art request."""
    print("\nComparing with album art request structure...")
    
    try:
        # First, let's see what a working request looks like
        # Get artist's albums first (this should work)
        albums_url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        albums_response = requests.get(albums_url, headers=headers)
        print(f"Albums endpoint: {albums_response.status_code}")
        
        if albums_response.status_code == 200:
            albums_data = albums_response.json()
            albums = albums_data.get('items', [])
            
            if albums:
                album_id = albums[0]['id']
                print(f"Testing with album: {albums[0]['name']} (ID: {album_id})")
                
                # Test album tracks (similar structure to related artists)
                tracks_url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
                tracks_response = requests.get(tracks_url, headers=headers)
                print(f"Album tracks: {tracks_response.status_code} {'✅' if tracks_response.status_code == 200 else '❌'}")
                
                # Now test related artists with EXACT same headers and approach
                related_url = f"https://api.spotify.com/v1/artists/{artist_id}/related-artists"
                related_response = requests.get(related_url, headers=headers)
                print(f"Related artists (same approach): {related_response.status_code} {'✅' if related_response.status_code == 200 else '❌'}")
                
                if related_response.status_code != 200:
                    print(f"   Related artists error: {related_response.text}")
        
    except Exception as e:
        print(f"Album art comparison: ❌ Exception: {e}")

if __name__ == "__main__":
    test_spotify_endpoints_comprehensive()