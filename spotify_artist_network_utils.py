#!/usr/bin/env python3
"""
Spotify Artist Network Utils
Separate Spotify API functions specifically for network visualization.
This doesn't interfere with the existing album_art_utils.py used for bar chart races.
"""

import requests
import json
import time
import os
from typing import Dict, List, Optional
from album_art_utils import _get_spotify_access_token, initialize_from_config

def get_spotify_artist_data_for_network(artist_name: str) -> Optional[Dict]:
    """
    Get Spotify artist data specifically for network visualization.
    Returns data even if no profile photo is available.
    
    This is separate from get_spotify_artist_info() which requires photos
    for the bar chart race visualization.
    
    Args:
        artist_name: Artist name to search for
        
    Returns:
        Dict with artist data or None if not found:
        {
            "canonical_artist_name": str,
            "spotify_artist_id": str,
            "followers": int,
            "popularity": int (0-100),
            "genres": list,
            "photo_url": str or None,
            "source": str
        }
    """
    access_token = _get_spotify_access_token()
    if not access_token:
        return None
    
    # Clean artist name for search
    search_query = artist_name.strip()
    
    # Search for artist
    url = f"https://api.spotify.com/v1/search"
    params = {
        'q': f'artist:"{search_query}"',
        'type': 'artist',
        'limit': 10
    }
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        artists = data.get('artists', {}).get('items', [])
        if not artists:
            return None
        
        # Find best match
        best_match = None
        normalized_search = search_query.lower().strip()
        
        # Try exact match first
        for artist in artists:
            artist_name_spotify = artist.get('name', '').lower().strip()
            if artist_name_spotify == normalized_search:
                best_match = artist
                break
        
        # If no exact match, try containment
        if not best_match:
            for artist in artists:
                artist_name_spotify = artist.get('name', '').lower().strip()
                if (normalized_search in artist_name_spotify or 
                    artist_name_spotify in normalized_search):
                    best_match = artist
                    break
        
        # If still no match, take first result (highest popularity)
        if not best_match and artists:
            best_match = artists[0]
        
        if best_match:
            # Extract data - photo is optional for network visualization
            images = best_match.get('images', [])
            photo_url = images[0].get('url') if images else None
            
            result = {
                "canonical_artist_name": best_match.get('name', artist_name),
                "spotify_artist_id": best_match.get('id', ''),
                "followers": best_match.get('followers', {}).get('total', 0),
                "popularity": best_match.get('popularity', 0),
                "genres": best_match.get('genres', []),
                "photo_url": photo_url,
                "source": "spotify_network_search"
            }
            
            return result
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Spotify API error for '{artist_name}': {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error for '{artist_name}': {e}")
        return None

def batch_get_spotify_artist_data(artist_names: List[str], 
                                 progress_callback: Optional[callable] = None) -> List[Dict]:
    """
    Get Spotify artist data for multiple artists.
    
    Args:
        artist_names: List of artist names
        progress_callback: Optional callback function(current, total, artist_name)
        
    Returns:
        List of artist data dicts (may contain None for failed lookups)
    """
    results = []
    total = len(artist_names)
    
    for i, artist_name in enumerate(artist_names, 1):
        if progress_callback:
            progress_callback(i, total, artist_name)
        
        result = get_spotify_artist_data_for_network(artist_name)
        results.append(result)
        
        # Small delay to respect API limits
        time.sleep(0.1)
    
    return results

def calculate_hybrid_node_size(lastfm_listeners: int, 
                              spotify_data: Optional[Dict],
                              strategy: str = 'hybrid_multiply',
                              popularity_boost: float = 1.5) -> Dict:
    """
    Calculate node size using hybrid approach combining Last.fm and Spotify data.
    
    Args:
        lastfm_listeners: Last.fm listener count
        spotify_data: Spotify artist data from get_spotify_artist_data_for_network()
        strategy: Sizing strategy ('lastfm', 'spotify_popularity', 'hybrid_multiply', 'hybrid_weighted')
        popularity_boost: Boost factor for Spotify popularity in hybrid methods
        
    Returns:
        Dict with size calculation details:
        {
            'size': int,
            'strategy_used': str,
            'components': dict,
            'display_text': str
        }
    """
    spotify_popularity = spotify_data.get('popularity', 0) if spotify_data else 0
    spotify_followers = spotify_data.get('followers', 0) if spotify_data else 0
    
    result = {
        'size': 0,
        'strategy_used': strategy,
        'components': {
            'lastfm_listeners': lastfm_listeners,
            'spotify_popularity': spotify_popularity,
            'spotify_followers': spotify_followers
        },
        'display_text': ''
    }
    
    if strategy == 'lastfm':
        result['size'] = lastfm_listeners
        result['display_text'] = f"{lastfm_listeners:,} Last.fm listeners"
        
    elif strategy == 'spotify_popularity':
        # Scale popularity (0-100) to reasonable size range
        result['size'] = spotify_popularity * 10000
        result['display_text'] = f"{spotify_popularity}/100 Spotify popularity"
        
    elif strategy == 'hybrid_multiply':
        if lastfm_listeners > 0:
            # Use Last.fm as base, multiply by normalized Spotify popularity boost
            popularity_multiplier = 1 + ((spotify_popularity / 100) * (popularity_boost - 1))
            result['size'] = int(lastfm_listeners * popularity_multiplier)
            result['display_text'] = f"{lastfm_listeners:,} × {popularity_multiplier:.2f} (pop boost)"
        else:
            # Fallback to pure Spotify popularity
            result['size'] = spotify_popularity * 10000
            result['display_text'] = f"{spotify_popularity}/100 Spotify popularity (fallback)"
            result['strategy_used'] = 'spotify_popularity_fallback'
            
    elif strategy == 'hybrid_weighted':
        # Weighted combination: 70% Last.fm, 30% scaled Spotify popularity
        lastfm_component = lastfm_listeners * 0.7
        spotify_component = spotify_popularity * 50000 * 0.3
        result['size'] = int(lastfm_component + spotify_component)
        result['display_text'] = f"{lastfm_listeners:,} + pop({spotify_popularity}) weighted"
    
    # Apply fallbacks if primary strategy failed
    if result['size'] == 0:
        if spotify_followers > 0:
            result['size'] = spotify_followers
            result['strategy_used'] = 'spotify_followers_fallback'
            result['display_text'] = f"{spotify_followers:,} Spotify followers (fallback)"
        elif spotify_popularity > 0:
            result['size'] = spotify_popularity * 10000
            result['strategy_used'] = 'spotify_popularity_fallback' 
            result['display_text'] = f"{spotify_popularity}/100 Spotify popularity (fallback)"
        elif lastfm_listeners > 0:
            result['size'] = lastfm_listeners
            result['strategy_used'] = 'lastfm_fallback'
            result['display_text'] = f"{lastfm_listeners:,} Last.fm listeners (fallback)"
    
    # Ensure minimum size for visualization
    result['size'] = max(result['size'], 1000)
    
    return result

def test_spotify_network_functions():
    """Test the Spotify network functions."""
    print("🧪 Testing Spotify Network Functions")
    print("=" * 50)
    
    # Initialize Spotify API
    from config_loader import AppConfig
    config = AppConfig('configurations.txt')
    initialize_from_config(config)
    
    # Test artists
    test_artists = ['Taylor Swift', 'Ed Sheeran', 'BLACKPINK', 'ive']
    
    print(f"Testing {len(test_artists)} artists...")
    
    for i, artist in enumerate(test_artists, 1):
        print(f"\n{i}/{len(test_artists)}: {artist}")
        
        result = get_spotify_artist_data_for_network(artist)
        
        if result:
            print(f"  ✅ Found: {result['canonical_artist_name']}")
            print(f"  📊 Followers: {result['followers']:,}")
            print(f"  🎯 Popularity: {result['popularity']}/100")
            print(f"  🎵 Genres: {', '.join(result['genres'][:3])}")
            print(f"  📷 Photo: {'Yes' if result['photo_url'] else 'No'}")
            
            # Test hybrid sizing
            hybrid_result = calculate_hybrid_node_size(
                lastfm_listeners=1000000,  # Simulated Last.fm data
                spotify_data=result,
                strategy='hybrid_multiply'
            )
            print(f"  📏 Hybrid size: {hybrid_result['size']:,} ({hybrid_result['display_text']})")
            
        else:
            print(f"  ❌ Not found")

if __name__ == "__main__":
    test_spotify_network_functions()