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
        Generate intelligent name variants with priority ordering.
        
        Args:
            artist_name: Original artist name
            
        Returns:
            List of name variants ordered by likelihood of success
        """
        variants = []
        name_clean = artist_name.strip()
        name_upper = name_clean.upper()
        
        # Priority 1: Exact match (always try first)
        variants.append(name_clean)
        
        # Priority 2: Known successful patterns (curated database)
        known_patterns = self._get_known_artist_patterns()
        if name_upper in known_patterns:
            variants.extend(known_patterns[name_upper])
        
        # Priority 3: High-probability variants based on artist type detection
        artist_type = self._detect_artist_type(name_clean)
        if artist_type == 'kpop':
            variants.extend(self._generate_kpop_variants(name_clean))
        elif artist_type == 'jpop':
            variants.extend(self._generate_jpop_variants(name_clean))
        elif artist_type == 'western':
            variants.extend(self._generate_western_variants(name_clean))
        
        # Priority 4: Common abbreviations and stylizations
        variants.extend(self._generate_common_abbreviations(name_clean))
        
        # Priority 5: Basic transformations (last resort)
        variants.extend(self._generate_basic_transformations(name_clean))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for variant in variants:
            if variant not in seen:
                seen.add(variant)
                unique_variants.append(variant)
        
        return unique_variants
    
    def _get_known_artist_patterns(self) -> Dict[str, List[str]]:
        """Get database of known working patterns for specific artists."""
        return {
            # K-pop groups
            'IVE': ['IVE (아이브)', '아이브'],
            'TWICE': ['TWICE (트와이스)', '트와이스'],
            'BLACKPINK': ['BLACKPINK (블랙핑크)', '블랙핑크'],
            'BTS': ['BTS (방탄소년단)', '방탄소년단'],
            'STRAY KIDS': ['Stray Kids (스트레이 키즈)', '스트레이 키즈'],
            'NEWJEANS': ['NewJeans (뉴진스)', '뉴진스'],
            'LE SSERAFIM': ['LE SSERAFIM (르세라핌)', '르세라핌'],
            'AESPA': ['aespa (에스파)', '에스파'],
            'ITZY': ['ITZY (있지)', '있지'],
            '(G)I-DLE': ['(G)I-DLE ((여자)아이들)', '(여자)아이들'],
            'SEVENTEEN': ['SEVENTEEN (세븐틴)', '세븐틴'],
            'ENHYPEN': ['ENHYPEN (엔하이픈)', '엔하이픈'],
            'TXT': ['TXT (투모로우바이투게더)', 'TOMORROW X TOGETHER', 'TOP'],
            'ARTMS': ['ARTMS (아르테미스)', '아르테미스'],
            'ILLIT': ['ILLIT (아일릿)', '아일릿'],
            
            # K-pop soloists
            'ANYUJIN': ['An Yujin', 'ANYUJIN (IVE)', 'Ahn Yujin', 'Ahn Yu-jin'],
            'JEON SOMI': ['SOMI', 'Somi'],
            'KISS OF LIFE': ['KOL', 'Kiss Of Life'],
            'SUNMI': ['Lee Sun-mi', 'SUNMI (선미)', '선미'],
            'MIYEON': ['Cho Mi-yeon', '미연', 'MIYEON ((G)I-DLE)', 'Mi-yeon'],
            
            # Japanese artists
            'AIMYON': ['Aimyon', 'あいみょん', 'aimyon'],
            
            # J-pop / Japanese artists
            'YOASOBI': ['YOASOBI (ヨアソビ)', 'ヨアソビ', 'yoasobi'],
            'ヨルシカ': ['Yorushika', 'YORUSHIKA'],
            'YORUSHIKA': ['ヨルシカ', 'Yorushika'],
            
            # Western artists with common issues
            'TWENTY ONE PILOTS': ['twenty one pilots', 'TOP', '21 Pilots', 'Twenty One Pilots'],
            'BRING ME THE HORIZON': ['BMTH', 'Bring Me the Horizon'],
            'LINKIN PARK': ['Linkin Park', 'LP'],
            'MY CHEMICAL ROMANCE': ['MCR', 'My Chemical Romance'],
            'FALL OUT BOY': ['FOB', 'Fall Out Boy'],
            'PANIC! AT THE DISCO': ['P!ATD', 'Panic at the Disco', 'Panic! At The Disco'],
            
            # Artists with special characters
            'P!NK': ['Pink', 'P!nk'],
            'KE$HA': ['Kesha', 'Ke$ha'],
            'BBNO$': ['bbno$', 'BBNO$', 'Baby No Money'],
            
            # Hip-hop/Rap artists (case sensitive & full names)
            'MGK': ['Machine Gun Kelly', 'MGK', 'mgk'],
            'MACHINE GUN KELLY': ['Machine Gun Kelly', 'MGK'],
            'XXXTENTACION': ['XXXTentacion', 'xxxtentacion', 'XXXTENTACION'],
            'BLACKBEAR': ['blackbear', 'Blackbear'],
            
            # Common abbreviation patterns
            'LIL WAYNE': ['Lil Wayne', 'lil wayne'],
            'LIL PEEP': ['Lil Peep', 'lil peep'],
            'A$AP ROCKY': ['ASAP Rocky', 'A$AP Rocky'],
            '21 SAVAGE': ['21 Savage', '21savage'],
            'NBA YOUNGBOY': ['YoungBoy Never Broke Again', 'NBA YoungBoy'],
            'JUICE WRLD': ['Juice WRLD', 'JuiceWRLD'],
            
            # Hip-hop collectives & labels
            '88RISING': ['88rising', '88 Rising', 'eighty eight rising'],
        }
    
    def _detect_artist_type(self, name: str) -> str:
        """Detect the likely origin/type of artist for targeted variant generation."""
        name_upper = name.upper()
        
        # Korean indicators
        korean_indicators = [
            'IVE', 'BTS', 'TWICE', 'BLACKPINK', 'STRAY', 'NEWJEANS', 'AESPA',
            'SEVENTEEN', 'ENHYPEN', 'ITZY', 'SSERAFIM', 'ARTMS', 'ILLIT',
            'SOMI', 'YUJIN', 'KISS OF LIFE'
        ]
        if any(indicator in name_upper for indicator in korean_indicators):
            return 'kpop'
        
        # Japanese indicators
        japanese_indicators = ['YOASOBI', 'YORUSHIKA', 'BABYMETAL', 'PERFUME']
        if any(indicator in name_upper for indicator in japanese_indicators):
            return 'jpop'
        
        # Check for Japanese characters
        if any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FAF' for char in name):
            return 'jpop'
        
        # Korean characters
        if any('\uAC00' <= char <= '\uD7AF' for char in name):
            return 'kpop'
        
        return 'western'
    
    def _generate_kpop_variants(self, name: str) -> List[str]:
        """Generate K-pop specific variants."""
        variants = []
        name_clean = name.strip()
        
        # Common K-pop formatting patterns
        variants.extend([
            f"{name_clean} (K-pop)",
            f"{name_clean} (girl group)",
            f"{name_clean} (boy group)",
            f"{name_clean} (Korean)",
            name_clean.title(),
            name_clean.lower()
        ])
        
        return variants
    
    def _generate_jpop_variants(self, name: str) -> List[str]:
        """Generate J-pop specific variants."""
        variants = []
        name_clean = name.strip()
        
        # Common J-pop formatting patterns
        variants.extend([
            f"{name_clean} (Japanese)",
            f"{name_clean} (J-pop)",
            name_clean.lower(),
            name_clean.title()
        ])
        
        return variants
    
    def _generate_western_variants(self, name: str) -> List[str]:
        """Generate Western artist variants."""
        variants = []
        name_clean = name.strip()
        
        # Case variations
        variants.extend([
            name_clean.title(),
            name_clean.lower(),
            name_clean.upper()
        ])
        
        return variants
    
    def _generate_common_abbreviations(self, name: str) -> List[str]:
        """Generate common abbreviation patterns."""
        variants = []
        words = name.strip().split()
        
        if len(words) > 1:
            # Initials
            initials = ''.join(word[0].upper() for word in words if word)
            variants.append(initials)
            
            # First word only
            variants.append(words[0])
            
            # Last word only
            variants.append(words[-1])
        
        return variants
    
    def _generate_basic_transformations(self, name: str) -> List[str]:
        """Generate basic transformations as last resort."""
        variants = []
        name_clean = name.strip()
        
        # The/without The
        if name_clean.lower().startswith('the '):
            variants.append(name_clean[4:])
        else:
            variants.append(f"The {name_clean}")
        
        # With/without punctuation
        import re
        no_punct = re.sub(r'[^\w\s]', '', name_clean)
        if no_punct != name_clean:
            variants.append(no_punct)
        
        # Replace & with and
        if '&' in name_clean:
            variants.append(name_clean.replace('&', 'and'))
        
        return variants

    def _is_relevant_artist_match(self, original: str, candidate: str) -> bool:
        """
        Check if a candidate artist name is relevant to the original query.
        Avoids matching completely different artists (e.g., 'blackbear' vs 'Blackbeard').
        Much stricter matching to prevent false positives like SUNMI -> SunMin.
        """
        original_clean = original.lower().strip()
        candidate_clean = candidate.lower().strip()
        
        # Extract the main artist name from collaborations
        def extract_main_artist(name):
            # Remove common collaboration indicators
            for separator in [' & ', ', ', ' feat. ', ' ft. ', ' featuring ', ' x ']:
                if separator in name:
                    parts = name.split(separator)
                    # Return the part that best matches original
                    for part in parts:
                        if any(word in part.lower() for word in original_clean.split()):
                            return part.strip()
                    # If no match, return first part
                    return parts[0].strip()
            return name
        
        main_candidate = extract_main_artist(candidate_clean)
        
        # FIRST: Check blacklist of obvious false positives
        false_positives = {
            'blackbear': ['blackbeard', "blackbeard's tea party", 'blackbeards'],
            'sunmi': ['sunmin', 'sun min', 'sunmee', 'sun-min'],
            'aimyon': ['aiman', 'aimon', 'aimee'],
            # Note: XXXTENTACION removed from blacklist to allow valid variants
        }
        
        if original_clean in false_positives:
            for false_positive in false_positives[original_clean]:
                if false_positive in candidate_clean.lower():
                    return False
        
        # Exact or very close match
        if original_clean == main_candidate:
            return True
        
        # Special case: collaboration with original artist (check for exact word match)
        # Avoid "blackbear" matching "blackbeard" by requiring word boundaries
        if original_clean in candidate_clean:
            # Verify it's a real match by checking if it's surrounded by separators
            import re
            pattern = r'\b' + re.escape(original_clean) + r'\b'
            if re.search(pattern, candidate_clean):
                return True
        
        # Check if original is a substantial substring of candidate (much stricter)
        # Only allow if it's EXACTLY the same or differs by 1 character max
        if len(original_clean) >= 4 and original_clean in main_candidate and len(main_candidate) - len(original_clean) <= 1:
            # Additional check: ensure it's not a completely different name
            # e.g., 'sunmi' in 'sunmin' passes length check but is different artist
            if self._levenshtein_distance(original_clean, main_candidate) <= 1:
                return True
        
        # Check if candidate contains original as a word
        original_words = set(original_clean.split())
        candidate_words = set(main_candidate.split())
        
        # Very high word overlap (100% of original words must be present for single-word artists)
        if len(original_words) == 1:
            # For single-word artists, require exact match or known variant
            if original_clean not in candidate_words:
                return False
        elif original_words and len(original_words & candidate_words) / len(original_words) >= 0.8:
            return True
        
        # Special case: very similar names (edit distance)
        # But be more careful - require very close match
        if len(original_clean) >= 5 and len(main_candidate) >= 5:
            # Only use edit distance for reasonably long names
            if self._similar_strings(original_clean, main_candidate):
                return True
        elif original_clean == main_candidate:
            # For short names, require exact match
            return True
        
        return False
    
    def _similar_strings(self, s1: str, s2: str) -> bool:
        """Check if two strings are very similar (strict matching)."""
        # Must be very close in length (max 2 character difference)
        if abs(len(s1) - len(s2)) > 2:
            return False
        
        # Both must be reasonably long to avoid false positives
        if len(s1) < 3 or len(s2) < 3:
            return False
        
        # Check character overlap - much stricter
        s1_chars = set(s1.replace(' ', '').replace('-', ''))
        s2_chars = set(s2.replace(' ', '').replace('-', ''))
        
        if not s1_chars or not s2_chars:
            return False
        
        overlap = len(s1_chars & s2_chars)
        total = len(s1_chars | s2_chars)
        
        # Very strict: 95% character overlap required AND similar length
        return (overlap / total >= 0.95) and (abs(len(s1_chars) - len(s2_chars)) <= 1)
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

    def _search_artist_variations(self, artist_name: str, limit: int = 5) -> List[Dict]:
        """
        Advanced search strategy: Find all artist variations and test for similar artists.
        
        Args:
            artist_name: Original artist name
            limit: Number of similar artists to fetch for testing
            
        Returns:
            List of similar artists from best working variation, or empty list
        """
        logger.debug(f"🔍 Advanced search for '{artist_name}' variations...")
        
        # Use Last.fm's search API to find all possible matches
        params = {'artist': artist_name, 'limit': '10'}
        response = self._make_request('artist.search', params)
        
        if not response or 'results' not in response:
            logger.debug("❌ Artist search API returned no results")
            return []
        
        matches = response['results'].get('artistmatches', {}).get('artist', [])
        if isinstance(matches, dict):
            matches = [matches]
        
        if not matches:
            logger.debug("❌ No artist matches found in search results")
            return []
        
        logger.debug(f"🔎 Found {len(matches)} search matches, testing for similar artists...")
        
        # Test each match for similar artists data
        best_result = None
        best_score = 0
        
        for match in matches[:5]:  # Test top 5 matches
            name = match.get('name', '')
            listeners = int(match.get('listeners', 0))
            mbid = match.get('mbid', '')
            
            # Skip if too few listeners (likely not the right artist)
            if listeners < 1000:
                continue
            
            # Relevance filtering - avoid completely different artists
            if not self._is_relevant_artist_match(artist_name, name):
                logger.debug(f"   Skipping irrelevant match: '{name}'")
                continue
            
            logger.debug(f"   Testing '{name}' ({listeners:,} listeners)")
            
            # Test for similar artists (without enhanced matching to avoid recursion)
            similar = self.get_similar_artists(name, limit=limit, use_enhanced_matching=False)
            
            # If no similar artists with name, try MBID
            if not similar and mbid:
                similar_mbid = self.get_similar_artists(mbid=mbid, limit=limit)
                if similar_mbid:
                    similar = similar_mbid
            
            # Score based on: has_similar_artists (MASSIVE boost) + listener_count
            # We HEAVILY prioritize having similar artists data over raw popularity
            # Use a boost so large that even tiny collaborations beat huge solo artists
            score = (1000000000 if similar else 0) + listeners
            
            if score > best_score:
                best_score = score
                best_result = {
                    'name': name,
                    'listeners': listeners,
                    'similar': similar,
                    'mbid': mbid
                }
                logger.debug(f"   ✅ New best match: '{name}' ({len(similar)} similar artists)")
            else:
                logger.debug(f"   ❌ No similar artists found for '{name}'")
        
        if best_result and best_result['similar']:
            logger.info(f"🎯 Advanced search found working variation: '{best_result['name']}' "
                       f"({best_result['listeners']:,} listeners, {len(best_result['similar'])} similar)")
            # Add metadata about which variation worked
            for artist in best_result['similar']:
                artist['_matched_variant'] = best_result['name']
                artist['_original_query'] = artist_name
                artist['_search_method'] = 'advanced_search'
            return best_result['similar']
        
        logger.debug(f"❌ Advanced search found no variations with similar artists")
        if best_result:
            logger.debug(f"   Best candidate was '{best_result['name']}' with {best_result['listeners']:,} listeners but no similar artists")
        return []

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
            fallback_candidates = []
            errors_count = 0
            max_consecutive_errors = 5  # Stop after too many consecutive API errors
            
            for i, variant in enumerate(name_variants):
                params = {'limit': str(limit), 'artist': variant}
                response = self._make_request('artist.getsimilar', params)
                attempted_variants.append(variant)
                
                # Check for API errors
                if response is None:
                    errors_count += 1
                    if errors_count >= max_consecutive_errors:
                        logger.warning(f"🛑 Stopping search after {max_consecutive_errors} consecutive API errors")
                        break
                    continue
                else:
                    errors_count = 0  # Reset error count on successful API call
                
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
                    
                    # For first few variants, check if artist exists (fallback validation)
                    if i < 3:  # Only validate first 3 variants to save API calls
                        try:
                            artist_info = self.get_artist_info(variant, use_enhanced_matching=False)
                            if artist_info and artist_info.get('listeners', 0) > 1000:
                                fallback_candidates.append((variant, artist_info['listeners']))
                        except:
                            pass
            
            # Step 4: Advanced search as final attempt
            logger.info(f"🚀 Attempting advanced search for '{artist_name}'...")
            advanced_results = self._search_artist_variations(artist_name, limit)
            if advanced_results:
                return advanced_results
            
            # Enhanced failure reporting
            if fallback_candidates:
                fallback_candidates.sort(key=lambda x: x[1], reverse=True)
                best_fallback = fallback_candidates[0]
                logger.warning(f"🔍 No similar artists found for '{artist_name}' after trying {len(attempted_variants)} variants + advanced search")
                logger.warning(f"   However, artist exists as '{best_fallback[0]}' with {best_fallback[1]:,} listeners")
                logger.warning(f"   This suggests the artist exists but Last.fm's similar artists endpoint may be incomplete")
            else:
                logger.warning(f"🔍 No similar artists found for '{artist_name}' after trying {len(attempted_variants)} variants + advanced search: {attempted_variants}")
            
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