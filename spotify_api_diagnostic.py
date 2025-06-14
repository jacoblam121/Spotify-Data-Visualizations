#!/usr/bin/env python3
"""
Spotify API Diagnostic Tool
============================
Systematic testing to diagnose the 404 errors on /related-artists endpoint.
Tests multiple scenarios to isolate the root cause.
"""

import requests
import json
import time
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from album_art_utils import _get_spotify_access_token, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

def get_manual_token():
    """Get token manually to ensure fresh credentials."""
    print("🔑 Getting fresh Spotify access token...")
    
    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode('utf-8')).decode('utf-8')
    headers = {
        'Authorization': f"Basic {auth_header}",
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    payload = {'grant_type': 'client_credentials'}
    
    try:
        response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=payload)
        response.raise_for_status()
        token_data = response.json()
        
        token = token_data['access_token']
        expires_in = token_data['expires_in']
        print(f"✅ Got token: {token[:20]}... (expires in {expires_in}s)")
        return token
        
    except Exception as e:
        print(f"❌ Token error: {e}")
        return None

def test_spotify_endpoints():
    """Comprehensive test of Spotify endpoints to isolate the issue."""
    print("🔍 Spotify API Comprehensive Diagnostic")
    print("=" * 50)
    
    # Get fresh token
    access_token = get_manual_token()
    if not access_token:
        return
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Test cases with different artist types and popularity levels
    test_artists = [
        ("Taylor Swift", "06HL4z0CvFAxyc27GXpf02", "mega-popular western"),
        ("TWICE", "7n2Ycct7Beij7Dj7meI4X0", "popular k-pop"),
        ("Ed Sheeran", "6eUKZXaKkcviH0Ku9w2n3V", "mega-popular western"),
        ("Radiohead", "4Z8W4fKeB5YxbusRsdQVPb", "classic rock"),
        ("Daft Punk", "4tZwfgrHOc3mvqYlEYSvVi", "electronic"),
        ("Unknown Artist", "1234567890123456789012", "invalid ID")
    ]
    
    print("\n1️⃣ Testing Artist Search (baseline functionality)")
    print("-" * 55)
    
    for name, expected_id, category in test_artists[:4]:  # Skip invalid ID for search
        try:
            url = "https://api.spotify.com/v1/search"
            params = {'q': f'artist:"{name}"', 'type': 'artist', 'limit': 1}
            
            response = requests.get(url, params=params, headers=headers)
            print(f"Search '{name}' ({category}): {response.status_code}", end="")
            
            if response.status_code == 200:
                data = response.json()
                artists = data.get('artists', {}).get('items', [])
                if artists:
                    found_id = artists[0]['id']
                    print(f" ✅ ID: {found_id}")
                else:
                    print(" ❌ No results")
            else:
                print(f" ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"Search '{name}': ❌ Exception: {e}")
        
        time.sleep(0.1)
    
    print("\n2️⃣ Testing Artist Info (baseline functionality)")
    print("-" * 55)
    
    for name, artist_id, category in test_artists:
        try:
            url = f"https://api.spotify.com/v1/artists/{artist_id}"
            
            response = requests.get(url, headers=headers)
            print(f"Info '{name}' ({category}): {response.status_code}", end="")
            
            if response.status_code == 200:
                data = response.json()
                print(f" ✅ Name: {data['name']}, Followers: {data['followers']['total']:,}")
            else:
                print(f" ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"Info '{name}': ❌ Exception: {e}")
        
        time.sleep(0.1)
    
    print("\n3️⃣ Testing Top Tracks (similar complexity to related artists)")
    print("-" * 55)
    
    for name, artist_id, category in test_artists:
        try:
            url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
            params = {'market': 'US'}
            
            response = requests.get(url, params=params, headers=headers)
            print(f"Tracks '{name}' ({category}): {response.status_code}", end="")
            
            if response.status_code == 200:
                data = response.json()
                tracks = data.get('tracks', [])
                print(f" ✅ Found {len(tracks)} tracks")
            else:
                print(f" ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"Tracks '{name}': ❌ Exception: {e}")
        
        time.sleep(0.1)
    
    print("\n4️⃣ Testing Related Artists (the problematic endpoint)")
    print("-" * 55)
    
    for name, artist_id, category in test_artists:
        try:
            url = f"https://api.spotify.com/v1/artists/{artist_id}/related-artists"
            
            # Add verbose headers for debugging
            debug_headers = headers.copy()
            debug_headers['User-Agent'] = 'SpotifyDataViz/1.0'
            
            print(f"Related '{name}' ({category}): ", end="")
            response = requests.get(url, headers=debug_headers)
            
            print(f"{response.status_code}", end="")
            
            if response.status_code == 200:
                data = response.json()
                artists = data.get('artists', [])
                print(f" ✅ Found {len(artists)} related artists")
                if artists:
                    print(f"     First 3: {', '.join(a['name'] for a in artists[:3])}")
            else:
                print(f" ❌")
                print(f"     Headers: {dict(response.headers)}")
                print(f"     Body: {response.text}")
                
                # Try alternative URL formats
                if response.status_code == 404:
                    print(f"     🔧 Trying alternative formats...")
                    
                    # Test with different URL patterns
                    alt_urls = [
                        f"https://api.spotify.com/v1/artists/{artist_id}/related",
                        f"https://api.spotify.com/v1/artist/{artist_id}/related-artists",
                        f"https://api.spotify.com/v2/artists/{artist_id}/related-artists"
                    ]
                    
                    for alt_url in alt_urls:
                        try:
                            alt_response = requests.get(alt_url, headers=headers)
                            print(f"       {alt_url}: {alt_response.status_code}")
                        except:
                            print(f"       {alt_url}: Exception")
                
        except Exception as e:
            print(f"Related '{name}': ❌ Exception: {e}")
        
        time.sleep(0.2)  # Slightly longer delay for related artists
    
    print("\n5️⃣ Testing Recommendations (potential alternative)")
    print("-" * 55)
    
    # Test recommendations as the suggested alternative
    test_seeds = [
        ("Taylor Swift", "06HL4z0CvFAxyc27GXpf02"),
        ("TWICE", "7n2Ycct7Beij7Dj7meI4X0")
    ]
    
    for name, artist_id in test_seeds:
        try:
            url = "https://api.spotify.com/v1/recommendations"
            params = {
                'seed_artists': artist_id,
                'limit': 10,
                'market': 'US'
            }
            
            response = requests.get(url, params=params, headers=headers)
            print(f"Recommendations '{name}': {response.status_code}", end="")
            
            if response.status_code == 200:
                data = response.json()
                tracks = data.get('tracks', [])
                unique_artists = list(set(track['artists'][0]['name'] for track in tracks))
                print(f" ✅ {len(tracks)} tracks, {len(unique_artists)} unique artists")
                print(f"     Artists: {', '.join(unique_artists[:5])}")
            else:
                print(f" ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"Recommendations '{name}': ❌ Exception: {e}")
        
        time.sleep(0.1)

if __name__ == "__main__":
    test_spotify_endpoints()