"""
Last.fm API integration for fetching artist information and similarity data.
This module provides functions to interact with the Last.fm API, including
fetching similar artists with similarity scores, artist tags, and metadata.
"""

import requests
import json
import os
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LastfmAPI:
    """Handler for Last.fm API interactions with caching support."""
    
    def __init__(self, api_key: str, api_secret: str, cache_dir: str = "lastfm_cache"):
        """
        Initialize Last.fm API handler.
        
        Args:
            api_key: Last.fm API key
            api_secret: Last.fm API secret (for future authenticated endpoints)
            cache_dir: Directory to store cache files
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://ws.audioscrobbler.com/2.0/"
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "lastfm_cache.json")
        self.cache_expiry_days = 30
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        # Load existing cache
        self.cache = self._load_cache()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms between requests
        
    def _load_cache(self) -> Dict:
        """Load cache from disk."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    # Clean expired entries
                    return self._clean_expired_cache(cache_data)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _clean_expired_cache(self, cache_data: Dict) -> Dict:
        """Remove expired cache entries."""
        cleaned_cache = {}
        expiry_date = datetime.now() - timedelta(days=self.cache_expiry_days)
        
        for key, value in cache_data.items():
            if 'timestamp' in value:
                cache_time = datetime.fromisoformat(value['timestamp'])
                if cache_time > expiry_date:
                    cleaned_cache[key] = value
            else:
                # Keep entries without timestamp (legacy)
                cleaned_cache[key] = value
                
        return cleaned_cache
    
    def _get_cache_key(self, method: str, params: Dict) -> str:
        """Generate a unique cache key for the request."""
        # Remove API key from params for cache key
        cache_params = {k: v for k, v in params.items() if k != 'api_key'}
        param_str = json.dumps(cache_params, sort_keys=True)
        return hashlib.md5(f"{method}:{param_str}".encode()).hexdigest()
    
    def _rate_limit(self):
        """Implement rate limiting to avoid hitting API limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
    
    def _make_request(self, method: str, params: Dict) -> Optional[Dict]:
        """Make a request to the Last.fm API."""
        # Check cache first
        cache_key = self._get_cache_key(method, params)
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {method} with params {params}")
            return self.cache[cache_key]['data']
        
        # Add required parameters
        params['method'] = method
        params['api_key'] = self.api_key
        params['format'] = 'json'
        
        # Rate limiting
        self._rate_limit()
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for Last.fm error response
            if 'error' in data:
                logger.error(f"Last.fm API error: {data['message']}")
                return None
            
            # Cache successful response
            self.cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            self._save_cache()
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None
    
    def get_similar_artists(self, artist_name: str = None, mbid: str = None, 
                          limit: int = 100) -> List[Dict]:
        """
        Get similar artists with similarity scores.
        
        Args:
            artist_name: Artist name (required if mbid not provided)
            mbid: MusicBrainz ID (optional, takes precedence over name)
            limit: Maximum number of similar artists to return
            
        Returns:
            List of similar artists with scores, or empty list on error
        """
        if not artist_name and not mbid:
            logger.error("Either artist_name or mbid must be provided")
            return []
        
        params = {'limit': str(limit)}
        if mbid:
            params['mbid'] = mbid
        else:
            params['artist'] = artist_name
            
        response = self._make_request('artist.getsimilar', params)
        
        if response and 'similarartists' in response:
            artists = response['similarartists'].get('artist', [])
            # Ensure we always return a list
            if isinstance(artists, dict):
                artists = [artists]
                
            # Parse and structure the data
            similar_artists = []
            for artist in artists:
                similar_artist = {
                    'name': artist.get('name', ''),
                    'mbid': artist.get('mbid', ''),
                    'match': float(artist.get('match', 0)),  # Similarity score
                    'url': artist.get('url', ''),
                    'images': {}
                }
                
                # Parse images
                if 'image' in artist:
                    for img in artist['image']:
                        size = img.get('size', 'medium')
                        similar_artist['images'][size] = img.get('#text', '')
                        
                similar_artists.append(similar_artist)
                
            return similar_artists
        
        return []
    
    def get_artist_info(self, artist_name: str = None, mbid: str = None) -> Optional[Dict]:
        """
        Get detailed artist information.
        
        Args:
            artist_name: Artist name (required if mbid not provided)
            mbid: MusicBrainz ID (optional, takes precedence over name)
            
        Returns:
            Artist information dict or None on error
        """
        if not artist_name and not mbid:
            logger.error("Either artist_name or mbid must be provided")
            return None
        
        params = {}
        if mbid:
            params['mbid'] = mbid
        else:
            params['artist'] = artist_name
            
        response = self._make_request('artist.getinfo', params)
        
        if response and 'artist' in response:
            artist = response['artist']
            
            # Structure the response
            artist_info = {
                'name': artist.get('name', ''),
                'mbid': artist.get('mbid', ''),
                'url': artist.get('url', ''),
                'playcount': int(artist.get('stats', {}).get('playcount', 0)),
                'listeners': int(artist.get('stats', {}).get('listeners', 0)),
                'ontour': artist.get('ontour', '0') == '1',
                'tags': [],
                'similar': [],
                'bio': artist.get('bio', {}).get('content', ''),
                'images': {}
            }
            
            # Parse tags
            if 'tags' in artist and 'tag' in artist['tags']:
                tags = artist['tags']['tag']
                if isinstance(tags, dict):
                    tags = [tags]
                artist_info['tags'] = [{'name': tag.get('name', ''), 
                                       'url': tag.get('url', '')} for tag in tags]
            
            # Parse similar artists
            if 'similar' in artist and 'artist' in artist['similar']:
                similar = artist['similar']['artist']
                if isinstance(similar, dict):
                    similar = [similar]
                artist_info['similar'] = [{'name': s.get('name', ''), 
                                         'url': s.get('url', '')} for s in similar]
            
            # Parse images
            if 'image' in artist:
                for img in artist['image']:
                    size = img.get('size', 'medium')
                    artist_info['images'][size] = img.get('#text', '')
                    
            return artist_info
        
        return None
    
    def get_artist_tags(self, artist_name: str = None, mbid: str = None) -> List[Dict]:
        """
        Get top tags for an artist.
        
        Args:
            artist_name: Artist name (required if mbid not provided)
            mbid: MusicBrainz ID (optional, takes precedence over name)
            
        Returns:
            List of tags with counts
        """
        if not artist_name and not mbid:
            logger.error("Either artist_name or mbid must be provided")
            return []
        
        params = {}
        if mbid:
            params['mbid'] = mbid
        else:
            params['artist'] = artist_name
            
        response = self._make_request('artist.gettoptags', params)
        
        if response and 'toptags' in response:
            tags = response['toptags'].get('tag', [])
            if isinstance(tags, dict):
                tags = [tags]
                
            return [{'name': tag.get('name', ''), 
                    'count': int(tag.get('count', 0)),
                    'url': tag.get('url', '')} for tag in tags]
        
        return []


# Convenience functions for direct usage
_api_instance = None

def initialize_lastfm_api(api_key: str, api_secret: str, cache_dir: str = "lastfm_cache"):
    """Initialize the Last.fm API with credentials."""
    global _api_instance
    _api_instance = LastfmAPI(api_key, api_secret, cache_dir)
    return _api_instance

def get_lastfm_similar_artists(artist_name: str = None, mbid: str = None, 
                              limit: int = 100) -> List[Dict]:
    """Get similar artists from Last.fm."""
    if not _api_instance:
        raise RuntimeError("Last.fm API not initialized. Call initialize_lastfm_api first.")
    return _api_instance.get_similar_artists(artist_name, mbid, limit)

def get_lastfm_artist_info(artist_name: str = None, mbid: str = None) -> Optional[Dict]:
    """Get artist info from Last.fm."""
    if not _api_instance:
        raise RuntimeError("Last.fm API not initialized. Call initialize_lastfm_api first.")
    return _api_instance.get_artist_info(artist_name, mbid)

def get_lastfm_artist_tags(artist_name: str = None, mbid: str = None) -> List[Dict]:
    """Get artist tags from Last.fm."""
    if not _api_instance:
        raise RuntimeError("Last.fm API not initialized. Call initialize_lastfm_api first.")
    return _api_instance.get_artist_tags(artist_name, mbid)