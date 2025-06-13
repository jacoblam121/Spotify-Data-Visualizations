#!/usr/bin/env python3
"""
Enhanced Artist Data Fetcher
Fetches artist data from both Last.fm and Spotify APIs with configurable source preference.
Provides unified interface for network visualization with listener count source selection.
"""

import time
from typing import Dict, List, Optional, Tuple
from lastfm_utils import LastfmAPI
from album_art_utils import initialize_from_config
from spotify_artist_network_utils import get_spotify_artist_data_for_network
from config_loader import AppConfig
import logging

logger = logging.getLogger(__name__)

class EnhancedArtistDataFetcher:
    """Enhanced artist data fetcher supporting both Last.fm and Spotify APIs."""
    
    def __init__(self, config: AppConfig):
        """Initialize the fetcher with configuration."""
        self.config = config
        self.lastfm_config = config.get_lastfm_config()
        self.spotify_config = config.get_spotify_config() 
        self.network_config = config.get_network_visualization_config()
        
        # Initialize Last.fm API if available
        self.lastfm_api = None
        if self.lastfm_config['api_key']:
            self.lastfm_api = LastfmAPI(
                self.lastfm_config['api_key'],
                self.lastfm_config['api_secret'],
                self.lastfm_config['cache_dir']
            )
        
        # Initialize Spotify album art utils
        initialize_from_config(config)
        
        # Check if Spotify is available
        self.spotify_available = bool(self.spotify_config['client_id'])
        
        logger.info(f"Enhanced Artist Data Fetcher initialized:")
        logger.info(f"  Node sizing strategy: {self.network_config['node_sizing_strategy']}")
        logger.info(f"  Last.fm available: {bool(self.lastfm_api)}")
        logger.info(f"  Spotify available: {self.spotify_available}")
        logger.info(f"  Fetch both sources: {self.network_config['fetch_both_sources']}")
    
    def fetch_artist_data(self, artist_name: str, 
                         include_similar: bool = True) -> Dict:
        """
        Fetch comprehensive artist data from available sources.
        
        Args:
            artist_name: Artist name to fetch data for
            include_similar: Whether to fetch similar artists (for network building)
            
        Returns:
            Dictionary with comprehensive artist data:
            {
                'artist_name': str,
                'canonical_name': str,
                'primary_listener_count': int,
                'primary_source': str ('lastfm' or 'spotify'),
                'lastfm_data': dict or None,
                'spotify_data': dict or None,
                'similar_artists': list or None,
                'photo_url': str or None,
                'success': bool,
                'error_message': str or None
            }
        """
        # Determine which sources to fetch based on strategy
        sizing_strategy = self.network_config['node_sizing_strategy']
        
        result = {
            'artist_name': artist_name,
            'canonical_name': artist_name,
            'primary_listener_count': 0,
            'primary_source': sizing_strategy,
            'lastfm_data': None,
            'spotify_data': None,
            'similar_artists': None,
            'photo_url': None,
            'success': False,
            'error_message': None
        }
        fetch_both = self.network_config['fetch_both_sources']
        fallback_behavior = self.network_config['fallback_behavior']
        
        # Determine primary source from strategy
        if sizing_strategy in ['lastfm']:
            primary_source = 'lastfm'
        elif sizing_strategy in ['spotify_popularity']:
            primary_source = 'spotify'
        else:  # hybrid strategies need both
            primary_source = 'both'
        
        # Fetch from primary source
        if primary_source in ['lastfm', 'both'] and self.lastfm_api:
            result['lastfm_data'] = self._fetch_lastfm_data(artist_name, include_similar)
            if result['lastfm_data']:
                result['canonical_name'] = result['lastfm_data']['name']
                result['primary_listener_count'] = result['lastfm_data']['listeners']
                result['success'] = True
        
        if primary_source in ['spotify', 'both'] and self.spotify_available:
            result['spotify_data'] = self._fetch_spotify_data(artist_name)
            if result['spotify_data'] and primary_source == 'spotify':
                result['canonical_name'] = result['spotify_data']['canonical_artist_name']
                result['primary_listener_count'] = result['spotify_data']['followers']
                result['photo_url'] = result['spotify_data']['photo_url']
                result['success'] = True
        
        # Fetch secondary source if configured or fallback needed
        if (fetch_both or (not result['success'] and fallback_behavior == 'fallback')):
            if primary_source == 'lastfm' and self.spotify_available and not result['spotify_data']:
                result['spotify_data'] = self._fetch_spotify_data(artist_name)
                if result['spotify_data']:
                    result['photo_url'] = result['spotify_data']['photo_url']
                    # Use as fallback if primary failed
                    if not result['success'] and fallback_behavior == 'fallback':
                        result['canonical_name'] = result['spotify_data']['canonical_artist_name']
                        result['primary_listener_count'] = result['spotify_data']['followers']
                        result['primary_source'] = 'spotify'
                        result['success'] = True
            
            elif primary_source == 'spotify' and self.lastfm_api and not result['lastfm_data']:
                result['lastfm_data'] = self._fetch_lastfm_data(artist_name, include_similar)
                if result['lastfm_data']:
                    if not result['similar_artists'] and include_similar:
                        result['similar_artists'] = result['lastfm_data'].get('similar_artists')
                    # Use as fallback if primary failed
                    if not result['success'] and fallback_behavior == 'fallback':
                        result['canonical_name'] = result['lastfm_data']['name']
                        result['primary_listener_count'] = result['lastfm_data']['listeners']
                        result['primary_source'] = 'lastfm'
                        result['success'] = True
        
        # Default fallback behavior
        if not result['success']:
            if fallback_behavior == 'default':
                result['success'] = True
                result['primary_listener_count'] = 0  # Will use play count instead
                result['primary_source'] = 'default'
            elif fallback_behavior == 'skip':
                result['error_message'] = f"Could not fetch data from {primary_source} and fallback disabled"
            else:
                result['error_message'] = f"Could not fetch data from any available source"
        
        return result
    
    def _fetch_lastfm_data(self, artist_name: str, include_similar: bool = True) -> Optional[Dict]:
        """Fetch data from Last.fm API."""
        if not self.lastfm_api:
            return None
        
        try:
            # Get artist info
            artist_info = self.lastfm_api.get_artist_info(artist_name)
            if not artist_info:
                return None
            
            result = {
                'name': artist_info.get('name', artist_name),
                'listeners': artist_info.get('listeners', 0),
                'playcount': artist_info.get('playcount', 0),
                'url': artist_info.get('url', ''),
                'tags': artist_info.get('tags', []),
                'bio': artist_info.get('bio', ''),
                'images': artist_info.get('images', {}),
                'mbid': artist_info.get('mbid', ''),
                'similar_artists': None
            }
            
            # Get similar artists if requested
            if include_similar:
                similar_artists = self.lastfm_api.get_similar_artists(artist_name, limit=20)
                result['similar_artists'] = similar_artists
            
            return result
            
        except Exception as e:
            logger.debug(f"Last.fm fetch failed for '{artist_name}': {e}")
            return None
    
    def _fetch_spotify_data(self, artist_name: str) -> Optional[Dict]:
        """Fetch data from Spotify API using network-specific function."""
        if not self.spotify_available:
            return None
        
        try:
            spotify_info = get_spotify_artist_data_for_network(artist_name)
            if spotify_info:
                return {
                    'canonical_artist_name': spotify_info.get('canonical_artist_name', artist_name),
                    'spotify_artist_id': spotify_info.get('spotify_artist_id', ''),
                    'followers': spotify_info.get('followers', 0),
                    'popularity': spotify_info.get('popularity', 0),
                    'genres': spotify_info.get('genres', []),
                    'photo_url': spotify_info.get('photo_url', ''),
                    'source': spotify_info.get('source', 'spotify')
                }
            return None
            
        except Exception as e:
            logger.debug(f"Spotify fetch failed for '{artist_name}': {e}")
            return None
    
    def batch_fetch_artist_data(self, artist_names: List[str], 
                               include_similar: bool = True,
                               progress_callback: Optional[callable] = None) -> List[Dict]:
        """
        Fetch artist data for multiple artists with progress tracking.
        
        Args:
            artist_names: List of artist names
            include_similar: Whether to fetch similar artists
            progress_callback: Optional callback function(current, total, artist_name)
            
        Returns:
            List of artist data dictionaries
        """
        results = []
        total = len(artist_names)
        
        for i, artist_name in enumerate(artist_names, 1):
            if progress_callback:
                progress_callback(i, total, artist_name)
            
            result = self.fetch_artist_data(artist_name, include_similar)
            results.append(result)
            
            # Small delay to respect API limits
            time.sleep(0.1)
        
        return results
    
    def get_artist_listener_summary(self, artist_data: Dict) -> Dict:
        """
        Get a summary of listener counts from all available sources.
        
        Args:
            artist_data: Result from fetch_artist_data()
            
        Returns:
            Dictionary with listener count summary
        """
        summary = {
            'artist_name': artist_data['artist_name'],
            'canonical_name': artist_data['canonical_name'],
            'primary_source': artist_data['primary_source'],
            'primary_count': artist_data['primary_listener_count'],
            'lastfm_listeners': 0,
            'spotify_followers': 0,
            'has_lastfm': bool(artist_data['lastfm_data']),
            'has_spotify': bool(artist_data['spotify_data']),
            'photo_available': bool(artist_data['photo_url'])
        }
        
        if artist_data['lastfm_data']:
            summary['lastfm_listeners'] = artist_data['lastfm_data']['listeners']
        
        if artist_data['spotify_data']:
            summary['spotify_followers'] = artist_data['spotify_data']['followers']
        
        return summary


def create_artist_data_fetcher(config_file: str = 'configurations.txt') -> EnhancedArtistDataFetcher:
    """Convenience function to create an artist data fetcher."""
    config = AppConfig(config_file)
    return EnhancedArtistDataFetcher(config)


# Example usage and testing functions
def test_artist_data_fetcher():
    """Test the enhanced artist data fetcher."""
    print("🧪 Testing Enhanced Artist Data Fetcher")
    print("=" * 50)
    
    try:
        fetcher = create_artist_data_fetcher()
        
        # Test artists
        test_artists = ['Taylor Swift', 'ive', 'anyujin', 'BLACKPINK']
        
        for artist in test_artists:
            print(f"\n🎵 Testing: {artist}")
            
            result = fetcher.fetch_artist_data(artist, include_similar=False)
            
            if result['success']:
                print(f"  ✅ Success: {result['canonical_name']}")
                print(f"  📊 Primary: {result['primary_listener_count']:,} {result['primary_source']}")
                
                if result['lastfm_data'] and result['spotify_data']:
                    lastfm_count = result['lastfm_data']['listeners']
                    spotify_count = result['spotify_data']['followers']
                    print(f"  🎧 Last.fm: {lastfm_count:,} listeners")
                    print(f"  🎵 Spotify: {spotify_count:,} followers")
                    ratio = spotify_count / lastfm_count if lastfm_count > 0 else 0
                    print(f"  📈 Ratio: {ratio:.1f}x (Spotify/Last.fm)")
                
                if result['photo_url']:
                    print(f"  📷 Photo: Available")
            else:
                print(f"  ❌ Failed: {result['error_message']}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_artist_data_fetcher()