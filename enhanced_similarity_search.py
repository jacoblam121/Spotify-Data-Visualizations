#!/usr/bin/env python3
"""
Enhanced Similarity Search
==========================
Fixes canonical name resolution issues and adds Spotify related artists fallback.

The main issue: get_similar_artists() uses canonical name resolution, but Last.fm
similarity data might reference original artist names, causing mismatches.

This module provides:
1. Fixed similarity search using original names 
2. Spotify related artists as fallback
3. Hybrid similarity scoring
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import sys

# Add project modules
sys.path.insert(0, str(Path(__file__).parent))

from lastfm_utils import LastfmAPI
from config_loader import AppConfig
from album_art_utils import _get_spotify_access_token

logger = logging.getLogger(__name__)

class EnhancedSimilaritySearcher:
    """Enhanced similarity search with fixed name resolution and Spotify fallback."""
    
    def __init__(self, config: AppConfig):
        """Initialize with configuration."""
        self.config = config
        self.lastfm_config = config.get_lastfm_config()
        self.spotify_config = config.get_spotify_config()
        
        # Initialize Last.fm API
        self.lastfm_api = None
        if self.lastfm_config['enabled'] and self.lastfm_config['api_key']:
            self.lastfm_api = LastfmAPI(
                self.lastfm_config['api_key'],
                self.lastfm_config['api_secret'],
                self.lastfm_config['cache_dir']
            )
        
        # Check Spotify availability
        self.spotify_available = bool(self.spotify_config['client_id'])
        
        logger.info(f"Enhanced Similarity Searcher initialized:")
        logger.info(f"  Last.fm available: {bool(self.lastfm_api)}")
        logger.info(f"  Spotify available: {self.spotify_available}")
    
    def get_enhanced_similar_artists(self, artist_name: str, limit: int = 100) -> List[Dict]:
        """
        Get similar artists using enhanced search with original name preservation.
        
        This fixes the canonical name resolution issue by:
        1. Using the original artist name for Last.fm searches (not canonical)
        2. Adding Spotify related artists as fallback
        3. Combining results with proper scoring
        
        Args:
            artist_name: Original artist name to search for
            limit: Maximum number of similar artists to return
            
        Returns:
            List of similar artists with enhanced metadata:
            {
                'name': str,
                'match': float,
                'source': 'lastfm' | 'spotify' | 'manual',
                'lastfm_similarity': float,
                'spotify_popularity': float,
                'relationship_type': str
            }
        """
        logger.info(f"🔍 Enhanced similarity search for '{artist_name}'")
        
        all_similar = []
        lastfm_results = []
        spotify_results = []
        
        # Step 1: Get Last.fm similarities using ORIGINAL name (not canonical)
        if self.lastfm_api:
            logger.debug("🎵 Searching Last.fm with original name...")
            lastfm_results = self._get_lastfm_similar_original_name(artist_name, limit)
            logger.info(f"   Found {len(lastfm_results)} Last.fm similarities")
            all_similar.extend(lastfm_results)
        
        # Step 2: Get Spotify related artists as fallback
        if self.spotify_available:
            logger.debug("🎧 Searching Spotify related artists...")
            spotify_results = self._get_spotify_related_artists(artist_name, limit)
            logger.info(f"   Found {len(spotify_results)} Spotify related artists")
            all_similar.extend(spotify_results)
        
        # Step 3: Combine and deduplicate results
        combined_results = self._combine_similarity_results(all_similar, limit)
        
        logger.info(f"✅ Enhanced search found {len(combined_results)} total similarities")
        logger.info(f"   Last.fm: {len(lastfm_results)}, Spotify: {len(spotify_results)}")
        
        return combined_results
    
    def _get_lastfm_similar_original_name(self, artist_name: str, limit: int) -> List[Dict]:
        """
        Get Last.fm similarities using the ORIGINAL artist name.
        This bypasses canonical resolution to prevent name mismatches.
        """
        try:
            # Use get_similar_artists with enhanced matching disabled
            # This forces it to use the exact name provided without canonical resolution
            similar_artists = self.lastfm_api.get_similar_artists(
                artist_name=artist_name,
                limit=limit,
                use_enhanced_matching=False  # KEY: Disable canonical resolution
            )
            
            # Add source metadata
            for artist in similar_artists:
                artist['source'] = 'lastfm'
                artist['lastfm_similarity'] = artist['match']
                artist['spotify_popularity'] = 0.0
                artist['relationship_type'] = 'lastfm_similar'
            
            return similar_artists
            
        except Exception as e:
            logger.error(f"Error getting Last.fm similarities for '{artist_name}': {e}")
            return []
    
    def _get_spotify_related_artists(self, artist_name: str, limit: int) -> List[Dict]:
        """
        Get Spotify related artists as fallback for missing Last.fm connections.
        """
        try:
            access_token = _get_spotify_access_token()
            if not access_token:
                logger.warning("No Spotify access token available")
                return []
            
            # Step 1: Search for the artist
            artist_id = self._search_spotify_artist_id(artist_name, access_token)
            if not artist_id:
                logger.warning(f"Artist '{artist_name}' not found on Spotify")
                return []
            
            # Step 2: Get related artists
            url = f"https://api.spotify.com/v1/artists/{artist_id}/related-artists"
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = requests.get(url, headers=headers)
            time.sleep(0.1)  # Rate limiting
            
            if response.status_code != 200:
                logger.error(f"Spotify API error: {response.status_code}")
                return []
            
            data = response.json()
            related_artists = data.get('artists', [])
            
            # Convert to our format
            results = []
            for i, artist in enumerate(related_artists[:limit]):
                # Calculate similarity score based on Spotify popularity and position
                # Higher position = lower similarity, popularity adds weight
                position_score = max(0, (limit - i) / limit)  # 1.0 to ~0.0
                popularity_score = artist.get('popularity', 0) / 100.0  # 0.0 to 1.0
                
                # Combined score: position matters more, popularity as secondary factor
                similarity_score = (position_score * 0.7) + (popularity_score * 0.3)
                
                result = {
                    'name': artist['name'],
                    'match': similarity_score,
                    'source': 'spotify',
                    'lastfm_similarity': 0.0,
                    'spotify_popularity': artist.get('popularity', 0),
                    'relationship_type': 'spotify_related',
                    'spotify_id': artist['id'],
                    'genres': artist.get('genres', [])
                }
                results.append(result)
            
            logger.debug(f"Found {len(results)} Spotify related artists for '{artist_name}'")
            return results
            
        except Exception as e:
            logger.error(f"Error getting Spotify related artists for '{artist_name}': {e}")
            return []
    
    def _search_spotify_artist_id(self, artist_name: str, access_token: str) -> Optional[str]:
        """Search for artist ID on Spotify."""
        try:
            url = "https://api.spotify.com/v1/search"
            params = {
                'q': f'artist:"{artist_name}"',
                'type': 'artist',
                'limit': 1
            }
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = requests.get(url, params=params, headers=headers)
            time.sleep(0.1)  # Rate limiting
            
            if response.status_code == 200:
                data = response.json()
                # Fix: Access the correct field for artist search
                artists = data.get('artists', {}).get('items', [])
                
                if artists:
                    artist_id = artists[0]['id']
                    logger.debug(f"Found Spotify artist ID for '{artist_name}': {artist_id}")
                    return artist_id
                else:
                    logger.debug(f"No Spotify artist found for '{artist_name}'")
            else:
                logger.error(f"Spotify search failed: {response.status_code} - {response.text}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Spotify for '{artist_name}': {e}")
            return None
    
    def _combine_similarity_results(self, all_results: List[Dict], limit: int) -> List[Dict]:
        """
        Combine Last.fm and Spotify results, removing duplicates and scoring properly.
        """
        # Group by artist name (case-insensitive)
        artist_groups = {}
        
        for result in all_results:
            artist_name = result['name'].lower().strip()
            if artist_name not in artist_groups:
                artist_groups[artist_name] = []
            artist_groups[artist_name].append(result)
        
        # For each artist, combine data from multiple sources
        combined = []
        for artist_name, results in artist_groups.items():
            if len(results) == 1:
                # Only one source, use as-is
                combined.append(results[0])
            else:
                # Multiple sources, combine them
                combined_result = self._merge_artist_results(results)
                combined.append(combined_result)
        
        # Sort by similarity score and limit
        combined.sort(key=lambda x: x['match'], reverse=True)
        return combined[:limit]
    
    def _merge_artist_results(self, results: List[Dict]) -> Dict:
        """
        Merge multiple results for the same artist from different sources.
        Prioritizes Last.fm but enhances with Spotify data.
        """
        # Separate by source
        lastfm_results = [r for r in results if r['source'] == 'lastfm']
        spotify_results = [r for r in results if r['source'] == 'spotify']
        
        # Use Last.fm as primary if available
        if lastfm_results:
            primary = lastfm_results[0].copy()
            
            # Enhance with Spotify data if available
            if spotify_results:
                spotify_data = spotify_results[0]
                primary['spotify_popularity'] = spotify_data['spotify_popularity']
                primary['genres'] = spotify_data.get('genres', [])
                primary['relationship_type'] = 'lastfm_spotify_combined'
                
                # Boost similarity score if both sources agree
                boost_factor = 1.2  # 20% boost for agreement
                primary['match'] = min(1.0, primary['match'] * boost_factor)
            
            return primary
        
        # Fall back to Spotify if no Last.fm data
        elif spotify_results:
            return spotify_results[0]
        
        # Should not happen, but return first result as fallback
        return results[0]

def test_enhanced_similarity_search():
    """Test the enhanced similarity search with problematic cases."""
    print("🧪 Testing Enhanced Similarity Search")
    print("=" * 40)
    
    try:
        config = AppConfig("configurations.txt")
        searcher = EnhancedSimilaritySearcher(config)
        
        # Test problematic cases
        test_cases = [
            "ANYUJIN",
            "IVE", 
            "TWICE",
            "IU",
            "Paramore"
        ]
        
        for artist in test_cases:
            print(f"\n🎯 Testing enhanced search for '{artist}':")
            
            results = searcher.get_enhanced_similar_artists(artist, limit=10)
            
            if results:
                print(f"   Found {len(results)} similar artists:")
                for i, similar in enumerate(results[:5], 1):
                    source_icon = "🎵" if similar['source'] == 'lastfm' else "🎧"
                    print(f"      {i}. {similar['name']} ({similar['match']:.3f}, {source_icon} {similar['source']})")
            else:
                print("   ❌ No similar artists found")
    
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    test_enhanced_similarity_search()