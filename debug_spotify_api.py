#!/usr/bin/env python3
"""
Debug Spotify API
==================
Debug Spotify API calls to understand why we're getting 404 errors.
"""

import requests
import time
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from album_art_utils import _get_spotify_access_token

def debug_spotify_search():
    """Debug Spotify search step by step."""
    print("🔍 Debugging Spotify API Search")
    print("=" * 35)
    
    # Get access token
    print("1. Getting Spotify access token...")
    access_token = _get_spotify_access_token()
    
    if not access_token:
        print("❌ No access token available")
        return
    
    print(f"✅ Got access token: {access_token[:20]}...")
    
    # Test search for well-known artists
    test_artists = ["TWICE", "Taylor Swift", "Paramore", "IU"]
    
    for artist_name in test_artists:
        print(f"\n2. Testing search for '{artist_name}'...")
        
        url = "https://api.spotify.com/v1/search"
        params = {
            'q': f'artist:"{artist_name}"',
            'type': 'artist',
            'limit': 1
        }
        headers = {'Authorization': f'Bearer {access_token}'}
        
        try:
            response = requests.get(url, params=params, headers=headers)
            print(f"   Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response keys: {list(data.keys())}")
                
                artists = data.get('artists', {}).get('items', [])
                print(f"   Found {len(artists)} artists")
                
                if artists:
                    artist = artists[0]
                    artist_id = artist['id']
                    artist_name_found = artist['name']
                    print(f"   ✅ Found: '{artist_name_found}' (ID: {artist_id})")
                    
                    # Test related artists API
                    print(f"   3. Testing related artists for {artist_id}...")
                    related_url = f"https://api.spotify.com/v1/artists/{artist_id}/related-artists"
                    
                    related_response = requests.get(related_url, headers=headers)
                    print(f"   Related artists status: {related_response.status_code}")
                    
                    if related_response.status_code == 200:
                        related_data = related_response.json()
                        related_artists = related_data.get('artists', [])
                        print(f"   ✅ Found {len(related_artists)} related artists")
                        
                        if related_artists:
                            print(f"   Top 3 related:")
                            for i, related in enumerate(related_artists[:3], 1):
                                print(f"      {i}. {related['name']} (popularity: {related.get('popularity', 0)})")
                    else:
                        print(f"   ❌ Related artists error: {related_response.text}")
                else:
                    print(f"   ❌ No artists found for '{artist_name}'")
            else:
                print(f"   ❌ Search error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        time.sleep(0.2)  # Rate limiting

if __name__ == "__main__":
    debug_spotify_search()