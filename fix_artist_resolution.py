#!/usr/bin/env python3
"""
Optimized Artist Resolution for Last.fm API
Fixes the inefficient multiple API calls and capitalization issues.
"""

import json
import time
import requests
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

class OptimizedLastFmClient:
    """
    Optimized Last.fm client that preserves display names and reduces API calls.
    """
    
    def __init__(self, api_key: str, api_secret: str = None, cache_dir: str = 'lastfm_cache'):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = 'https://ws.audioscrobbler.com/2.0/'
        self.min_request_interval = 0.2  # 5 requests per second max
        self.last_request_time = 0
        
        # Simple in-memory cache for this session
        self.resolution_cache = {}
    
    def _rate_limit(self):
        """Enforce rate limiting."""
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _make_request(self, method: str, params: Dict) -> Optional[Dict]:
        """Make a rate-limited request to Last.fm API."""
        # Add required parameters
        params['method'] = method
        params['api_key'] = self.api_key
        params['format'] = 'json'
        
        self._rate_limit()
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for Last.fm error
            if 'error' in data:
                error_code = data.get('error', 'unknown')
                error_message = data.get('message', 'No message provided')
                logger.error(f"Last.fm API error {error_code}: {error_message}")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def resolve_artist_efficiently(self, original_name: str) -> Dict:
        """
        Efficiently resolve artist name with minimal API calls.
        
        Returns:
            Dict with display_name, canonical_name, listeners, mbid, url
        """
        # Check cache first
        cache_key = original_name.lower().strip()
        if cache_key in self.resolution_cache:
            return self.resolution_cache[cache_key]
        
        # Stage 1: Try artist.getCorrection (most efficient)
        correction_result = self._try_correction(original_name)
        if correction_result:
            self.resolution_cache[cache_key] = correction_result
            return correction_result
        
        # Stage 2: Try artist.getInfo directly (second most efficient)
        info_result = self._try_get_info(original_name)
        if info_result:
            self.resolution_cache[cache_key] = info_result
            return info_result
        
        # Stage 3: Search with smart candidate selection (last resort)
        search_result = self._try_smart_search(original_name)
        if search_result:
            self.resolution_cache[cache_key] = search_result
            return search_result
        
        # Failed to resolve
        logger.warning(f"Could not resolve artist: {original_name}")
        return {
            'display_name': original_name,
            'canonical_name': None,
            'listeners': 0,
            'mbid': None,
            'url': None,
            'resolved': False
        }
    
    def _try_correction(self, artist_name: str) -> Optional[Dict]:
        """Try artist.getCorrection first - most efficient."""
        params = {'artist': artist_name}
        response = self._make_request('artist.getCorrection', params)
        
        if response and 'corrections' in response:
            correction = response['corrections'].get('correction')
            if correction and 'artist' in correction:
                corrected_artist = correction['artist']
                # Get detailed info for the corrected artist
                return self._get_artist_details(
                    display_name=artist_name,
                    canonical_name=corrected_artist['name'],
                    mbid=corrected_artist.get('mbid')
                )
        return None
    
    def _try_get_info(self, artist_name: str) -> Optional[Dict]:
        """Try artist.getInfo directly."""
        params = {'artist': artist_name}
        response = self._make_request('artist.getInfo', params)
        
        if response and 'artist' in response:
            artist_data = response['artist']
            listeners = int(artist_data.get('stats', {}).get('listeners', 0))
            
            # Basic sanity check - avoid very low listener counts
            if listeners > 100:
                return {
                    'display_name': artist_name,
                    'canonical_name': artist_data['name'],
                    'listeners': listeners,
                    'mbid': artist_data.get('mbid'),
                    'url': artist_data.get('url'),
                    'resolved': True,
                    'method': 'getInfo'
                }
        return None
    
    def _try_smart_search(self, artist_name: str) -> Optional[Dict]:
        """Smart search with candidate evaluation."""
        params = {'artist': artist_name, 'limit': '10'}
        response = self._make_request('artist.search', params)
        
        if not response or 'results' not in response:
            return None
        
        artistmatches = response['results'].get('artistmatches', {})
        if not artistmatches or 'artist' not in artistmatches:
            return None
        
        artists = artistmatches['artist']
        if not isinstance(artists, list):
            artists = [artists]
        
        # Evaluate candidates with composite scoring
        candidates = []
        for artist in artists[:5]:  # Only check top 5
            listeners = int(artist.get('listeners', 0))
            if listeners < 100:  # Skip very unpopular artists
                continue
            
            # Calculate string similarity
            similarity = SequenceMatcher(None, 
                                       artist_name.lower(), 
                                       artist['name'].lower()).ratio()
            
            # Composite score: similarity + log(listeners)
            import math
            score = similarity * 0.7 + (math.log10(listeners + 1) / 10) * 0.3
            
            candidates.append({
                'score': score,
                'artist': artist,
                'similarity': similarity,
                'listeners': listeners
            })
        
        if not candidates:
            return None
        
        # Select best candidate
        best = max(candidates, key=lambda x: x['score'])
        
        # Quality threshold - prevent bad matches
        if best['similarity'] < 0.6:  # Adjust as needed
            logger.warning(f"Best match for '{artist_name}' has low similarity: {best['similarity']}")
            return None
        
        return {
            'display_name': artist_name,
            'canonical_name': best['artist']['name'],
            'listeners': best['listeners'],
            'mbid': best['artist'].get('mbid'),
            'url': best['artist'].get('url'),
            'resolved': True,
            'method': 'search',
            'score': best['score']
        }
    
    def _get_artist_details(self, display_name: str, canonical_name: str, mbid: str = None) -> Dict:
        """Get detailed artist info using name or MBID."""
        params = {'mbid': mbid} if mbid else {'artist': canonical_name}
        response = self._make_request('artist.getInfo', params)
        
        if response and 'artist' in response:
            artist_data = response['artist']
            return {
                'display_name': display_name,
                'canonical_name': artist_data['name'],
                'listeners': int(artist_data.get('stats', {}).get('listeners', 0)),
                'mbid': artist_data.get('mbid'),
                'url': artist_data.get('url'),
                'resolved': True,
                'method': 'correction+info'
            }
        
        # Fallback if detailed info fails
        return {
            'display_name': display_name,
            'canonical_name': canonical_name,
            'listeners': 0,
            'mbid': mbid,
            'url': None,
            'resolved': True,
            'method': 'correction_only'
        }
    
    def get_similar_artists_efficient(self, artist_resolution: Dict, limit: int = 100) -> List[Dict]:
        """
        Get similar artists using resolved artist data.
        
        Args:
            artist_resolution: Result from resolve_artist_efficiently()
            limit: Number of similar artists to return
        """
        if not artist_resolution['resolved']:
            return []
        
        # Use MBID if available (most reliable), otherwise use canonical name
        if artist_resolution['mbid']:
            params = {'mbid': artist_resolution['mbid'], 'limit': str(limit)}
        else:
            params = {'artist': artist_resolution['canonical_name'], 'limit': str(limit)}
        
        response = self._make_request('artist.getsimilar', params)
        
        if not response or 'similarartists' not in response:
            return []
        
        similar_artists = response['similarartists'].get('artist', [])
        if not isinstance(similar_artists, list):
            similar_artists = [similar_artists]
        
        # Parse and return similar artists
        results = []
        for artist in similar_artists:
            try:
                match_score = float(artist.get('match', 0))
                if match_score > 0:  # Only include positive matches
                    results.append({
                        'name': artist['name'],
                        'match': match_score,
                        'mbid': artist.get('mbid'),
                        'url': artist.get('url')
                    })
            except (ValueError, KeyError):
                continue
        
        return results


def test_efficient_resolution():
    """Test the optimized resolution with problematic artists."""
    # You'll need to provide your API key
    api_key = "1e8f179baf2593c1ec228bf7eba1bfa4"  # Replace with actual key
    client = OptimizedLastFmClient(api_key)
    
    test_artists = [
        "BLACKPINK",
        "TWICE", 
        "anyujin",  # Should find AnYujin with 6.8K listeners
        "Taylor Swift",
        "Paramore"
    ]
    
    print("🧪 Testing Optimized Artist Resolution")
    print("=" * 50)
    
    for artist in test_artists:
        print(f"\n🎵 Testing: {artist}")
        result = client.resolve_artist_efficiently(artist)
        
        if result['resolved']:
            print(f"  ✅ Display: {result['display_name']}")
            print(f"  📊 Canonical: {result['canonical_name']}")
            print(f"  👥 Listeners: {result['listeners']:,}")
            print(f"  🔗 URL: {result['url']}")
            print(f"  ⚙️  Method: {result.get('method', 'unknown')}")
        else:
            print(f"  ❌ Could not resolve")


if __name__ == "__main__":
    test_efficient_resolution()