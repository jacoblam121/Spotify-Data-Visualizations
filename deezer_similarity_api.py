#!/usr/bin/env python3
"""
Deezer API Similarity Integration
=================================
SOLUTION: Free alternative to Spotify's restricted endpoints.
Deezer provides exactly what we need: /artist/{id}/related endpoint with no auth required.

This is completely non-destructive and provides additional similarity data
to complement Last.fm and manual connections.

Deezer API Benefits:
- FREE with no API key required
- Direct /artist/{id}/related endpoint  
- Excellent K-pop/J-pop coverage
- Clean, structured data
- ~50 requests per 5 seconds rate limit
"""

import requests
import time
import logging
from typing import Dict, List, Optional
from pathlib import Path
import sys

# Add project modules
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import AppConfig

logger = logging.getLogger(__name__)

class DeezerSimilarityAPI:
    """
    Deezer API integration for artist similarity data.
    Provides free, no-auth alternative to Spotify's restricted endpoints.
    """
    
    def __init__(self, config: AppConfig = None):
        """Initialize Deezer API client."""
        self.base_url = "https://api.deezer.com"
        self.rate_limit_delay = 0.1  # 100ms between requests to stay under 50/5s limit
        
        logger.info("Deezer Similarity API initialized:")
        logger.info("  No authentication required")
        logger.info("  Rate limit: ~50 requests per 5 seconds")
    
    def get_similar_artists(self, artist_name: str, limit: int = 20) -> List[Dict]:
        """
        Get similar artists from Deezer API.
        
        Process:
        1. Search for artist on Deezer
        2. Get related artists using /artist/{id}/related
        3. Format results to match Last.fm format for compatibility
        
        Args:
            artist_name: Artist to find similarities for
            limit: Maximum number of similar artists to return
            
        Returns:
            List of similar artists in Last.fm-compatible format:
            [{'name': str, 'match': float, 'source': 'deezer', ...}]
        """
        logger.info(f"🎵 Deezer similarity search for '{artist_name}'")
        
        # Step 1: Find artist ID on Deezer
        artist_id = self._search_artist_id(artist_name)
        if not artist_id:
            logger.warning(f"Artist '{artist_name}' not found on Deezer")
            return []
        
        # Step 2: Get related artists
        related_artists = self._get_related_artists(artist_id, limit)
        
        # Step 3: Format for compatibility with existing similarity system
        formatted_artists = self._format_for_similarity_system(related_artists)
        
        logger.info(f"✅ Deezer found {len(formatted_artists)} similar artists")
        return formatted_artists
    
    def _search_artist_id(self, artist_name: str) -> Optional[int]:
        """Search for artist ID on Deezer."""
        try:
            url = f"{self.base_url}/search/artist"
            params = {
                'q': artist_name,
                'limit': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            time.sleep(self.rate_limit_delay)
            
            if response.status_code == 200:
                data = response.json()
                artists = data.get('data', [])
                
                if artists:
                    artist = artists[0]
                    artist_id = artist['id']
                    found_name = artist['name']
                    
                    logger.debug(f"Found Deezer artist: '{found_name}' (ID: {artist_id})")
                    return artist_id
                else:
                    logger.debug(f"No Deezer artists found for '{artist_name}'")
            else:
                logger.error(f"Deezer search failed: {response.status_code} - {response.text}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Deezer for '{artist_name}': {e}")
            return None
    
    def _get_related_artists(self, artist_id: int, limit: int) -> List[Dict]:
        """Get related artists from Deezer API."""
        try:
            url = f"{self.base_url}/artist/{artist_id}/related"
            params = {'limit': limit}
            
            response = requests.get(url, params=params, timeout=10)
            time.sleep(self.rate_limit_delay)
            
            if response.status_code == 200:
                data = response.json()
                related_artists = data.get('data', [])
                
                logger.debug(f"Deezer returned {len(related_artists)} related artists")
                return related_artists
            else:
                logger.error(f"Deezer related artists failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting Deezer related artists for ID {artist_id}: {e}")
            return []
    
    def _format_for_similarity_system(self, deezer_artists: List[Dict]) -> List[Dict]:
        """
        Format Deezer results to match Last.fm similarity format.
        
        Deezer doesn't provide similarity scores, so we generate them based on:
        - Position in the list (earlier = more similar)
        - Artist popularity/fan count
        """
        formatted = []
        total_artists = len(deezer_artists)
        
        for i, artist in enumerate(deezer_artists):
            # Generate similarity score based on position and popularity
            position_score = (total_artists - i) / total_artists  # 1.0 to ~0.0
            
            # Factor in artist popularity if available
            fan_count = artist.get('nb_fan', 0)
            popularity_boost = min(0.2, fan_count / 1000000)  # Up to 0.2 boost for 1M+ fans
            
            similarity_score = min(1.0, position_score + popularity_boost)
            
            formatted_artist = {
                'name': artist['name'],
                'match': round(similarity_score, 3),
                'source': 'deezer',
                'lastfm_similarity': 0.0,  # Not from Last.fm
                'spotify_popularity': 0.0,  # Not from Spotify
                'manual_connection': False,
                'bidirectional_source': False,
                'relationship_type': 'deezer_related',
                
                # Deezer-specific metadata
                'deezer_id': artist['id'],
                'deezer_fans': fan_count,
                'deezer_position': i + 1,
                'picture_url': artist.get('picture_medium', ''),
                'deezer_url': artist.get('link', '')
            }
            
            formatted.append(formatted_artist)
        
        return formatted
    
    def test_artist_search(self, artist_name: str) -> Dict:
        """Test search functionality and return detailed info."""
        print(f"🔍 Testing Deezer search for '{artist_name}'")
        
        # Search for artist
        artist_id = self._search_artist_id(artist_name)
        if not artist_id:
            return {'status': 'not_found'}
        
        # Get artist details
        try:
            url = f"{self.base_url}/artist/{artist_id}"
            response = requests.get(url, timeout=10)
            time.sleep(self.rate_limit_delay)
            
            if response.status_code == 200:
                artist_data = response.json()
                
                result = {
                    'status': 'found',
                    'artist_id': artist_id,
                    'name': artist_data['name'],
                    'fans': artist_data.get('nb_fan', 0),
                    'albums': artist_data.get('nb_album', 0),
                    'picture': artist_data.get('picture_medium', ''),
                    'deezer_url': artist_data.get('link', '')
                }
                
                print(f"   ✅ Found: {result['name']} ({result['fans']:,} fans, {result['albums']} albums)")
                return result
            else:
                return {'status': 'api_error', 'code': response.status_code}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

def test_deezer_similarity():
    """Test Deezer similarity API with various artists."""
    print("🧪 Testing Deezer Similarity API")
    print("=" * 40)
    
    deezer_api = DeezerSimilarityAPI()
    
    # Test search functionality first
    print("\n1️⃣ Testing Artist Search")
    print("-" * 30)
    
    search_tests = ["Taylor Swift", "TWICE", "BTS", "Paramore", "Ed Sheeran"]
    for artist in search_tests:
        result = deezer_api.test_artist_search(artist)
        if result['status'] != 'found':
            print(f"   ❌ {artist}: {result}")
        time.sleep(0.2)
    
    # Test similarity functionality
    print("\n2️⃣ Testing Similarity Search")
    print("-" * 30)
    
    similarity_tests = ["Taylor Swift", "TWICE", "Paramore"]
    for artist in similarity_tests:
        print(f"\n🎯 Similarity search for '{artist}':")
        
        similar_artists = deezer_api.get_similar_artists(artist, limit=8)
        
        if similar_artists:
            print(f"   ✅ Found {len(similar_artists)} similar artists:")
            for i, similar in enumerate(similar_artists[:5], 1):
                fans = similar.get('deezer_fans', 0)
                print(f"      {i}. {similar['name']} ({similar['match']:.3f}, {fans:,} fans)")
        else:
            print("   ❌ No similar artists found")
        
        time.sleep(0.5)  # Rate limiting

def test_deezer_vs_lastfm_coverage():
    """Compare Deezer vs Last.fm coverage for problematic artists."""
    print("\n3️⃣ Testing Deezer vs Last.fm Coverage")
    print("-" * 45)
    
    try:
        from lastfm_utils import LastfmAPI
        from config_loader import AppConfig
        
        config = AppConfig("configurations.txt")
        lastfm_config = config.get_lastfm_config()
        
        # Initialize APIs
        deezer_api = DeezerSimilarityAPI()
        lastfm_api = None
        
        if lastfm_config['enabled'] and lastfm_config['api_key']:
            lastfm_api = LastfmAPI(
                lastfm_config['api_key'],
                lastfm_config['api_secret'],
                lastfm_config['cache_dir']
            )
        
        # Test problematic cases
        test_cases = ["ANYUJIN", "IVE", "NewJeans", "aespa"]
        
        for artist in test_cases:
            print(f"\n🔄 Comparing coverage for '{artist}':")
            
            # Test Deezer
            deezer_results = deezer_api.get_similar_artists(artist, limit=5)
            print(f"   🎵 Deezer: {len(deezer_results)} results")
            
            if deezer_results:
                for similar in deezer_results[:3]:
                    print(f"      - {similar['name']} ({similar['match']:.3f})")
            
            # Test Last.fm if available
            if lastfm_api:
                lastfm_results = lastfm_api.get_similar_artists(artist, limit=5, use_enhanced_matching=False)
                print(f"   🎶 Last.fm: {len(lastfm_results)} results")
                
                if lastfm_results:
                    for similar in lastfm_results[:3]:
                        print(f"      - {similar['name']} ({similar['match']:.3f})")
            
            time.sleep(0.3)
    
    except Exception as e:
        print(f"❌ Coverage test error: {e}")

if __name__ == "__main__":
    test_deezer_similarity()
    test_deezer_vs_lastfm_coverage()