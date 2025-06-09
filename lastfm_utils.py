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
    
    def _generate_name_variants(self, artist_name: str) -> List[str]:
        """
        Generate different name variants to try for failed lookups.
        
        Args:
            artist_name: Original artist name
            
        Returns:
            List of name variants to try
        """
        variants = [artist_name]  # Always try original first
        
        # Common K-pop name patterns
        kpop_patterns = {
            'IVE': ['IVE (아이브)', '아이브', 'IVE (K-pop)', 'IVE (girl group)'],
            'TWICE': ['TWICE (트와이스)', '트와이스'],
            'BLACKPINK': ['BLACKPINK (블랙핑크)', '블랙핑크'],
            'BTS': ['BTS (방탄소년단)', '방탄소년단', 'BTS (Korean group)'],
            'STRAY KIDS': ['Stray Kids (스트레이 키즈)', '스트레이 키즈'],
            'NEWJEANS': ['NewJeans (뉴진스)', '뉴진스'],
            'LE SSERAFIM': ['LE SSERAFIM (르세라핌)', '르세라핌'],
            'aespa': ['aespa (에스파)', '에스파'],
            'ITZY': ['ITZY (있지)', '있지'],
            '(G)I-DLE': ['(G)I-DLE ((여자)아이들)', '(여자)아이들'],
            'SEVENTEEN': ['SEVENTEEN (세븐틴)', '세븐틴'],
            'ENHYPEN': ['ENHYPEN (엔하이픈)', '엔하이픈'],
            'TXT': ['TXT (투모로우바이투게더)', '투모로우바이투게더', 'TOMORROW X TOGETHER'],
            'ANYUJIN': ['An Yujin', 'ANYUJIN (IVE)', 'AnYujin (IVE)', 'AN YUJIN'],
            'KISS OF LIFE': ['KOL', 'Kiss Of Life (키스 오브 라이프)', 'KISS OF LIFE (키스 오브 라이프)'],
            'JEON SOMI': ['SOMI', 'Somi', 'somi', '전소미'],
        }
        
        # Check if this artist has known variants
        artist_upper = artist_name.upper().strip()
        if artist_upper in kpop_patterns:
            variants.extend(kpop_patterns[artist_upper])
        
        # Comprehensive general patterns for any artist
        name_clean = artist_name.strip()
        name_words = name_clean.split()
        
        # Basic case variations
        variants.extend([
            name_clean.title(),  # Title Case
            name_clean.lower(),  # lowercase  
            name_clean.upper()   # UPPERCASE
        ])
        
        # Try with/without common prefixes
        if name_clean.lower().startswith('the '):
            variants.append(name_clean[4:])  # Remove "The "
        else:
            variants.append(f"The {name_clean}")  # Add "The "
        
        # Common suffixes for disambiguation
        suffixes = ['(band)', '(artist)', '(group)', '(singer)', '(K-pop)', '(soloist)']
        for suffix in suffixes:
            variants.extend([
                f"{name_clean} {suffix}",
                f"{name_clean.title()} {suffix}",
                f"{name_clean.lower()} {suffix}"
            ])
        
        # Advanced patterns for multi-word names
        if len(name_words) > 1:
            # Try abbreviations
            abbrev = ''.join(word[0].upper() for word in name_words if word and word[0].isalpha())
            if 2 <= len(abbrev) <= 6:
                variants.append(abbrev)
            
            # Try first name only (for person names)
            if len(name_words) == 2 and all(word.replace('-', '').isalpha() for word in name_words):
                first_name = name_words[0]
                variants.extend([
                    first_name,
                    first_name.upper(),
                    first_name.lower(),
                    first_name.title()
                ])
            
            # Try reversing word order for some Asian names
            if len(name_words) == 2:
                reversed_name = f"{name_words[1]} {name_words[0]}"
                variants.extend([
                    reversed_name,
                    reversed_name.title(),
                    reversed_name.lower(),
                    reversed_name.upper()
                ])
        
        # Special character handling
        if '&' in name_clean:
            # Try replacing & with 'and'
            variants.append(name_clean.replace('&', 'and'))
            variants.append(name_clean.replace('&', 'And'))
        
        if ' and ' in name_clean.lower():
            # Try replacing 'and' with &
            variants.append(name_clean.replace(' and ', ' & '))
            variants.append(name_clean.replace(' And ', ' & '))
        
        # Handle special punctuation
        if any(char in name_clean for char in '!@#$%^*()[]{}'):
            # Try without special characters
            import re
            clean_name = re.sub(r'[!@#$%^*()[\]{}]', '', name_clean)
            if clean_name.strip() != name_clean:
                variants.append(clean_name.strip())
                variants.append(clean_name.strip().title())
        
        # Handle numbers in names
        if any(char.isdigit() for char in name_clean):
            # Try spelling out numbers
            number_words = {
                '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five',
                '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine', '0': 'zero'
            }
            spelled_name = name_clean
            for digit, word in number_words.items():
                spelled_name = spelled_name.replace(digit, word)
            if spelled_name != name_clean:
                variants.append(spelled_name)
                variants.append(spelled_name.title())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for variant in variants:
            if variant not in seen:
                seen.add(variant)
                unique_variants.append(variant)
        
        return unique_variants

    def get_similar_artists(self, artist_name: str = None, mbid: str = None, 
                          limit: int = 100, use_enhanced_matching: bool = True) -> List[Dict]:
        """
        Get similar artists with similarity scores, with enhanced name matching.
        
        Args:
            artist_name: Artist name (required if mbid not provided)
            mbid: MusicBrainz ID (optional, takes precedence over name)
            limit: Maximum number of similar artists to return
            use_enhanced_matching: Whether to try multiple name variants on failure
            
        Returns:
            List of similar artists with scores, or empty list on error
        """
        if not artist_name and not mbid:
            logger.error("Either artist_name or mbid must be provided")
            return []
        
        # If using mbid, skip enhanced matching
        if mbid:
            params = {'limit': str(limit), 'mbid': mbid}
            response = self._make_request('artist.getsimilar', params)
            return self._parse_similar_artists_response(response)
        
        # Try enhanced matching for name-based lookups
        if use_enhanced_matching:
            name_variants = self._generate_name_variants(artist_name)
            logger.debug(f"Trying {len(name_variants)} name variants for '{artist_name}'")
            
            attempted_variants = []
            fallback_candidates = []  # Store candidates that have artist info but no similar artists
            
            for variant in name_variants:
                params = {'limit': str(limit), 'artist': variant}
                response = self._make_request('artist.getsimilar', params)
                attempted_variants.append(variant)
                
                similar_artists = self._parse_similar_artists_response(response)
                
                if similar_artists:
                    logger.info(f"✅ Found {len(similar_artists)} similar artists for '{artist_name}' using variant '{variant}'")
                    # Add metadata about which variant worked
                    for artist in similar_artists:
                        artist['_matched_variant'] = variant
                        artist['_original_query'] = artist_name
                    return similar_artists
                else:
                    logger.debug(f"❌ No similar artists found for variant '{variant}'")
                    
                    # Check if this variant at least has artist info (fallback validation)
                    try:
                        artist_info = self.get_artist_info(variant, use_enhanced_matching=False)
                        if artist_info and artist_info.get('listeners', 0) > 1000:  # Reasonable threshold
                            fallback_candidates.append((variant, artist_info['listeners']))
                    except:
                        pass  # Ignore errors in fallback validation
            
            # Log comprehensive failure with fallback info
            if fallback_candidates:
                fallback_candidates.sort(key=lambda x: x[1], reverse=True)  # Sort by listener count
                best_fallback = fallback_candidates[0]
                logger.warning(f"🔍 No similar artists found for '{artist_name}' after trying {len(attempted_variants)} variants")
                logger.warning(f"   However, artist exists as '{best_fallback[0]}' with {best_fallback[1]:,} listeners")
                logger.warning(f"   This suggests the artist exists but Last.fm's similar artists endpoint may be incomplete")
            else:
                logger.warning(f"🔍 No similar artists found for '{artist_name}' after trying {len(attempted_variants)} variants: {attempted_variants}")
            
            return []
        else:
            # Standard lookup without enhanced matching
            params = {'limit': str(limit), 'artist': artist_name}
            response = self._make_request('artist.getsimilar', params)
            return self._parse_similar_artists_response(response)

    def _parse_similar_artists_response(self, response: Optional[Dict]) -> List[Dict]:
        """
        Parse the similar artists response from Last.fm API.
        
        Args:
            response: Raw API response
            
        Returns:
            Parsed list of similar artists
        """
        if not response or 'similarartists' not in response:
            return []
        
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
    
    def get_artist_info(self, artist_name: str = None, mbid: str = None, 
                       use_enhanced_matching: bool = True) -> Optional[Dict]:
        """
        Get detailed artist information with enhanced name matching.
        
        Args:
            artist_name: Artist name (required if mbid not provided)
            mbid: MusicBrainz ID (optional, takes precedence over name)
            use_enhanced_matching: Whether to try multiple name variants on failure
            
        Returns:
            Artist information dict or None on error
        """
        if not artist_name and not mbid:
            logger.error("Either artist_name or mbid must be provided")
            return None
        
        # If using mbid, skip enhanced matching
        if mbid:
            params = {'mbid': mbid}
            response = self._make_request('artist.getinfo', params)
            return self._parse_artist_info_response(response)
        
        # Try enhanced matching for name-based lookups
        if use_enhanced_matching:
            name_variants = self._generate_name_variants(artist_name)
            logger.debug(f"Trying {len(name_variants)} name variants for artist info '{artist_name}'")
            
            for variant in name_variants:
                params = {'artist': variant}
                response = self._make_request('artist.getinfo', params)
                
                artist_info = self._parse_artist_info_response(response)
                
                if artist_info:
                    logger.info(f"✅ Found artist info for '{artist_name}' using variant '{variant}'")
                    # Add metadata about which variant worked
                    artist_info['_matched_variant'] = variant
                    artist_info['_original_query'] = artist_name
                    return artist_info
                else:
                    logger.debug(f"❌ No artist info found for variant '{variant}'")
            
            logger.warning(f"🔍 No artist info found for '{artist_name}' after trying variants")
            return None
        else:
            # Standard lookup without enhanced matching
            params = {'artist': artist_name}
            response = self._make_request('artist.getinfo', params)
            return self._parse_artist_info_response(response)

    def _parse_artist_info_response(self, response: Optional[Dict]) -> Optional[Dict]:
        """
        Parse the artist info response from Last.fm API.
        
        Args:
            response: Raw API response
            
        Returns:
            Parsed artist info dict or None
        """
        if not response or 'artist' not in response:
            return None
        
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