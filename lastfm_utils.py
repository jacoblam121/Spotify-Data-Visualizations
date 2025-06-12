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
                error_code = data.get('error', 'unknown')
                error_message = data.get('message', 'No message provided')
                logger.error(f"Last.fm API error {error_code}: {error_message}")
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
            'ユイカ': ['YUIKA', 'Yuika', 'yuika'],
            'YUIKA': ['ユイカ', 'Yuika', 'yuika'],
            
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
            'BLACKBEAR': ['blackbear', 'Blackbear', 'black bear'],
            'BOYWITHUKE': ['BoyWithUke', 'boy with uke', 'Boy with Uke'],
            
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
        original_clean = original.casefold().strip()
        candidate_clean = candidate.casefold().strip()
        
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
        
        # SPECIAL CASE: Handle exact matches that are being filtered incorrectly
        # e.g., 'blackbear' should match 'blackbear' exactly
        if original_clean == main_candidate or original_clean == candidate_clean:
            return True
        
        # FIRST: Check blacklist of obvious false positives
        false_positives = {
            'blackbear': ['blackbeard', "blackbeard's tea party", 'blackbeards'],
            'sunmi': ['sunmin', 'sun min', 'sunmee', 'sun-min'],
            'aimyon': ['aiman', 'aimon', 'aimee'],
            # Note: XXXTENTACION removed from blacklist to allow valid variants
        }
        
        # ENHANCED: Only apply blacklist if it's not an exact match
        # This prevents legitimate artists from being blocked
        if original_clean != main_candidate and original_clean in false_positives:
            for false_positive in false_positives[original_clean]:
                if false_positive in candidate_clean.lower():
                    logger.debug(f"Blacklist triggered: '{original}' vs '{candidate}' - rejected due to '{false_positive}'")
                    return False
        
        # Blacklist logic moved above to prevent exact match blocking
        
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
        """Check if two strings are very similar (strict matching with Unicode awareness)."""
        # Use Unicode-aware normalization
        s1_norm = s1.casefold().strip()
        s2_norm = s2.casefold().strip()
        
        # Must be very close in length (max 2 character difference)
        if abs(len(s1_norm) - len(s2_norm)) > 2:
            return False
        
        # Both must be reasonably long to avoid false positives
        if len(s1_norm) < 3 or len(s2_norm) < 3:
            return False
        
        # Check character overlap - much stricter
        s1_chars = set(s1_norm.replace(' ', '').replace('-', ''))
        s2_chars = set(s2_norm.replace(' ', '').replace('-', ''))
        
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
        
        # Try enhanced matching for name-based lookups with canonical resolution
        if use_enhanced_matching:
            return self._get_canonical_similar_artists(artist_name, limit)
        else:
            # Standard lookup without enhanced matching
            params = {'limit': str(limit), 'artist': artist_name}
            response = self._make_request('artist.getsimilar', params)
            return self._parse_similar_artists_response(response)
    
    def _get_canonical_similar_artists(self, artist_name: str, limit: int) -> List[Dict]:
        """
        Get similar artists using canonical artist resolution.
        Tests multiple variants and chooses the one with the highest listener count.
        """
        name_variants = self._generate_name_variants(artist_name)
        logger.debug(f"Trying {len(name_variants)} name variants for '{artist_name}' with canonical resolution")
        
        variant_results = []  # Store all successful results with metadata
        attempted_variants = []
        errors_count = 0
        max_consecutive_errors = 5
        
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
                errors_count = 0
            
            similar_artists = self._parse_similar_artists_response(response)
            
            if similar_artists:
                # Get artist info to determine listener count for this variant
                artist_info = self.get_artist_info(variant, use_enhanced_matching=False)
                listeners = artist_info.get('listeners', 0) if artist_info else 0
                
                variant_results.append({
                    'variant': variant,
                    'similar_artists': similar_artists,
                    'listeners': listeners,
                    'artist_info': artist_info
                })
                
                logger.debug(f"✅ Found {len(similar_artists)} similar artists for variant '{variant}' ({listeners:,} listeners)")
            else:
                logger.debug(f"❌ No similar artists found for variant '{variant}'")
        
        # Choose the canonical result (highest listener count)
        if variant_results:
            # Sort by listener count (descending) and take the best one
            best_result = max(variant_results, key=lambda x: x['listeners'])
            best_variant = best_result['variant']
            best_listeners = best_result['listeners']
            similar_artists = best_result['similar_artists']
            
            # Log the canonical resolution decision
            if len(variant_results) > 1:
                other_counts = [f"'{r['variant']}' ({r['listeners']:,})" for r in variant_results if r['variant'] != best_variant]
                logger.info(f"🎯 Canonical resolution: chose '{best_variant}' ({best_listeners:,} listeners) over {', '.join(other_counts)}")
            else:
                logger.info(f"✅ Found {len(similar_artists)} similar artists for '{artist_name}' using variant '{best_variant}' ({best_listeners:,} listeners)")
            
            # Add metadata about canonical resolution
            for artist in similar_artists:
                artist['_matched_variant'] = best_variant
                artist['_original_query'] = artist_name
                artist['_canonical_listeners'] = best_listeners
                artist['_resolution_method'] = 'canonical_similar_artists'
            
            return similar_artists
            
        # Step 4: Advanced search as final attempt
        logger.info(f"🚀 Attempting advanced search for '{artist_name}'...")
        advanced_results = self._search_artist_variations(artist_name, limit)
        if advanced_results:
            return advanced_results
        
        # No results found
        logger.warning(f"🔍 No similar artists found for '{artist_name}' after trying {len(attempted_variants)} variants + advanced search")
        return []

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
        
        # Try enhanced matching with multi-stage verification
        if use_enhanced_matching:
            return self._get_canonical_artist_info_with_verification(artist_name)
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
    
    def get_artist_top_tracks(self, artist_name: str = None, mbid: str = None, limit: int = 10) -> List[Dict]:
        """
        Get top tracks for an artist for verification purposes.
        
        Args:
            artist_name: Artist name (required if mbid not provided)
            mbid: MusicBrainz ID (optional, takes precedence over name)
            limit: Number of top tracks to fetch
            
        Returns:
            List of top track names (normalized for comparison)
        """
        if not artist_name and not mbid:
            logger.error("Either artist_name or mbid must be provided")
            return []
        
        params = {'limit': str(limit)}
        if mbid:
            params['mbid'] = mbid
        else:
            params['artist'] = artist_name
            
        response = self._make_request('artist.gettoptracks', params)
        
        if response and 'toptracks' in response:
            tracks = response['toptracks'].get('track', [])
            if isinstance(tracks, dict):
                tracks = [tracks]
                
            # Return normalized track names for comparison
            track_names = []
            for track in tracks:
                track_name = track.get('name', '').strip()
                if track_name:
                    normalized_name = self._normalize_track_name(track_name)
                    if normalized_name:  # Only add non-empty normalized names
                        track_names.append(normalized_name)
            
            return track_names
    
    def _normalize_track_name(self, track_name: str) -> str:
        """Normalize track name for comparison (more aggressive than artist names)."""
        if not track_name:
            return ""
        
        import re
        
        # Start with basic normalization
        normalized = track_name.casefold().strip()
        
        # Remove content in parentheses/brackets (live, remix, feat., etc.)
        normalized = re.sub(r'[\(\[].*?[\)\]]', '', normalized)
        
        # Remove common modifiers
        normalized = re.sub(r'\b(feat\.?|ft\.?|featuring|with|remix|live|acoustic|version)\b.*', '', normalized)
        
        # Remove punctuation except for meaningful characters
        normalized = re.sub(r'[^\w\s\-&]', '', normalized)
        
        # Collapse multiple spaces and trim
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _verify_same_artist_by_songs(self, artist1_name: str, artist2_name: str, 
                                    min_common_tracks: int = 3) -> bool:
        """
        Verify if two artist names refer to the same artist by comparing their top tracks.
        
        Args:
            artist1_name: First artist name
            artist2_name: Second artist name  
            min_common_tracks: Minimum number of common tracks to consider same artist
            
        Returns:
            True if they appear to be the same artist based on shared songs
        """
        try:
            tracks1 = self.get_artist_top_tracks(artist1_name, limit=15)
            tracks2 = self.get_artist_top_tracks(artist2_name, limit=15)
            
            if not tracks1 or not tracks2:
                logger.debug(f"Could not get tracks for comparison: '{artist1_name}' vs '{artist2_name}'")
                return False
            
            # Find common tracks
            common_tracks = set(tracks1) & set(tracks2)
            common_count = len(common_tracks)
            
            # Calculate similarity percentage
            total_unique_tracks = len(set(tracks1) | set(tracks2))
            similarity_ratio = common_count / total_unique_tracks if total_unique_tracks > 0 else 0
            
            logger.debug(f"Song verification: '{artist1_name}' vs '{artist2_name}'")
            logger.debug(f"   Common tracks: {common_count}/{min(len(tracks1), len(tracks2))} ({similarity_ratio:.2f} similarity)")
            
            # Consider same artist if:
            # 1. At least min_common_tracks in common, AND
            # 2. High similarity ratio (>60%) OR many common tracks (>5)
            is_same_artist = (common_count >= min_common_tracks and 
                            (similarity_ratio > 0.6 or common_count > 5))
            
            if is_same_artist:
                logger.debug(f"   ✅ Verified as same artist")
            else:
                logger.debug(f"   ❌ Appear to be different artists")
            
            return is_same_artist
            
        except Exception as e:
            logger.debug(f"Error in song verification: {e}")
            return False
    
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
    
    def _get_canonical_artist_info_with_verification(self, artist_name: str) -> Optional[Dict]:
        """
        Get artist info using multi-stage verification:
        1. MBID Check (if same MBID, definitely same artist)
        2. Song-based verification (if same songs, same artist)
        3. Listener count tiebreaker (choose most popular page)
        """
        name_variants = self._generate_name_variants(artist_name)
        logger.debug(f"Multi-stage verification for '{artist_name}' with {len(name_variants)} variants")
        
        # Collect all valid artist pages
        artist_pages = []
        
        for variant in name_variants:
            params = {'artist': variant}
            response = self._make_request('artist.getinfo', params)
            artist_info = self._parse_artist_info_response(response)
            
            if artist_info:
                artist_pages.append({
                    'variant': variant,
                    'info': artist_info,
                    'listeners': artist_info.get('listeners', 0),
                    'mbid': artist_info.get('mbid', '')
                })
                logger.debug(f"✅ Found page for '{variant}': {artist_info.get('listeners', 0):,} listeners")
        
        if not artist_pages:
            logger.warning(f"🔍 No artist pages found for '{artist_name}'")
            return None
        
        if len(artist_pages) == 1:
            # Only one page found, use it
            page = artist_pages[0]
            page['info']['_matched_variant'] = page['variant']
            page['info']['_original_query'] = artist_name
            page['info']['_resolution_method'] = 'single_page'
            return page['info']
        
        # Multiple pages found - apply multi-stage verification
        logger.info(f"🔍 Multiple pages found for '{artist_name}': {[p['variant'] for p in artist_pages]}")
        
        # Stage 1: MBID Check (Gemini's suggestion)
        mbid_groups = self._group_by_mbid(artist_pages)
        if len(mbid_groups) == 1 and list(mbid_groups.keys())[0] != 'no_mbid':  # All have same valid MBID
            mbid = list(mbid_groups.keys())[0]
            pages_with_mbid = mbid_groups[mbid]
            best_page = max(pages_with_mbid, key=lambda x: x['listeners'])
            logger.info(f"🎯 MBID verification: All pages share MBID {mbid}, choosing highest listener count")
            
            best_page['info']['_resolution_method'] = 'mbid_verified'
            best_page['info']['_matched_variant'] = best_page['variant']
            best_page['info']['_original_query'] = artist_name
            return best_page['info']
        
        # Stage 2: Song-based verification
        verified_groups = self._group_by_song_similarity(artist_pages)
        if verified_groups:
            # Find the group with the highest total listener count
            best_group = max(verified_groups, key=lambda group: sum(p['listeners'] for p in group))
            best_page = max(best_group, key=lambda x: x['listeners'])
            
            if len(best_group) > 1:
                other_variants = [p['variant'] for p in best_group if p['variant'] != best_page['variant']]
                logger.info(f"🎯 Song verification: '{best_page['variant']}' ({best_page['listeners']:,} listeners) verified same as {other_variants}")
            
            best_page['info']['_resolution_method'] = 'song_verified'
            best_page['info']['_matched_variant'] = best_page['variant']
            best_page['info']['_original_query'] = artist_name
            return best_page['info']
        
        # Stage 3: Fallback to highest listener count
        best_page = max(artist_pages, key=lambda x: x['listeners'])
        logger.warning(f"⚠️ No verification possible, choosing highest listener count: '{best_page['variant']}' ({best_page['listeners']:,} listeners)")
        
        best_page['info']['_resolution_method'] = 'listener_count_fallback'
        best_page['info']['_matched_variant'] = best_page['variant']
        best_page['info']['_original_query'] = artist_name
        return best_page['info']
    
    def _group_by_mbid(self, artist_pages: List[Dict]) -> Dict[str, List[Dict]]:
        """Group artist pages by their MusicBrainz ID."""
        mbid_groups = {}
        for page in artist_pages:
            mbid = page['mbid'] or 'no_mbid'
            if mbid not in mbid_groups:
                mbid_groups[mbid] = []
            mbid_groups[mbid].append(page)
        return mbid_groups
    
    def _group_by_song_similarity(self, artist_pages: List[Dict]) -> List[List[Dict]]:
        """
        Group artist pages by song similarity using Jaccard similarity.
        Returns groups of pages that appear to be the same artist.
        """
        if len(artist_pages) < 2:
            return [artist_pages]
        
        # Get top tracks for each page
        page_tracks = []
        for page in artist_pages:
            tracks = self.get_artist_top_tracks(page['variant'], limit=12)
            page_tracks.append({
                'page': page,
                'tracks': set(tracks),
                'track_count': len(tracks)
            })
        
        # Group pages by similarity
        groups = []
        used_indices = set()
        
        for i, page_data in enumerate(page_tracks):
            if i in used_indices:
                continue
            
            current_group = [page_data['page']]
            used_indices.add(i)
            
            for j, other_page_data in enumerate(page_tracks[i+1:], i+1):
                if j in used_indices:
                    continue
                
                # Calculate Jaccard similarity (Gemini's suggestion)
                common_tracks = page_data['tracks'] & other_page_data['tracks']
                total_tracks = page_data['tracks'] | other_page_data['tracks']
                
                if total_tracks:
                    jaccard_similarity = len(common_tracks) / len(total_tracks)
                    
                    # Verify as same artist if:
                    # - High Jaccard similarity (>0.4) OR
                    # - Many common tracks (>4) with decent similarity (>0.25)
                    is_same_artist = (jaccard_similarity > 0.4 or 
                                    (len(common_tracks) > 4 and jaccard_similarity > 0.25))
                    
                    logger.debug(f"Song similarity: '{page_data['page']['variant']}' vs '{other_page_data['page']['variant']}': "
                               f"{len(common_tracks)} common, {jaccard_similarity:.3f} Jaccard -> {'Same' if is_same_artist else 'Different'}")
                    
                    if is_same_artist:
                        current_group.append(other_page_data['page'])
                        used_indices.add(j)
            
            if current_group:
                groups.append(current_group)
        
        # Only return groups with multiple pages (verified duplicates)
        verified_groups = [group for group in groups if len(group) > 1]
        
        if verified_groups:
            logger.info(f"🎧 Song verification found {len(verified_groups)} groups of duplicate artist pages")
        
        return verified_groups


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