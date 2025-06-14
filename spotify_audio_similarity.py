#!/usr/bin/env python3
"""
Spotify Audio Feature Similarity System
========================================
SOLUTION: Since related-artists endpoint is restricted to user auth flows,
this implements Gemini's "Audio Feature Profile" approach using working endpoints.

Creates artist similarity based on sonic profiles using:
1. Artist's top tracks → Audio features analysis → Sonic profile
2. Recommendations endpoint with target audio features (may need fallback)
3. Playlist archaeology method as backup
4. Normalized scoring compatible with Last.fm 0.0-1.0 scale

This is NON-DESTRUCTIVE and doesn't interfere with existing album art functionality.
"""

import requests
import json
import time
import statistics
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

# Add project modules
sys.path.insert(0, str(Path(__file__).parent))

from album_art_utils import _get_spotify_access_token
from config_loader import AppConfig

logger = logging.getLogger(__name__)

class SpotifyAudioSimilarityFinder:
    """
    Finds similar artists using audio feature analysis and sonic profiling.
    Uses only endpoints that work with Client Credentials flow.
    """
    
    def __init__(self, config: AppConfig):
        """Initialize with configuration."""
        self.config = config
        self.spotify_config = config.get_spotify_config()
        
        # Check Spotify availability (reuse existing credentials)
        self.spotify_available = bool(self.spotify_config['client_id'])
        
        logger.info(f"Spotify Audio Similarity Finder initialized:")
        logger.info(f"  Spotify available: {self.spotify_available}")
        logger.info(f"  Using existing album art credentials (non-destructive)")
    
    def get_audio_based_similar_artists(self, artist_name: str, limit: int = 20) -> List[Dict]:
        """
        Get similar artists using audio feature profiling.
        
        Process:
        1. Find artist → Get top tracks → Analyze audio features → Create sonic profile
        2. Try recommendations with target features (may fail due to auth)
        3. Fallback to playlist archaeology method
        4. Return scored list compatible with Last.fm format
        
        Args:
            artist_name: Artist to find similarities for
            limit: Maximum number of similar artists to return
            
        Returns:
            List of similar artists with scores 0.0-1.0
        """
        if not self.spotify_available:
            logger.warning("Spotify not available")
            return []
        
        logger.info(f"🎵 Audio similarity search for '{artist_name}'")
        
        # Step 1: Get artist ID
        artist_id = self._search_artist_id(artist_name)
        if not artist_id:
            logger.warning(f"Artist '{artist_name}' not found on Spotify")
            return []
        
        # Step 2: Get artist's sonic profile
        sonic_profile = self._get_artist_sonic_profile(artist_id, artist_name)
        if not sonic_profile:
            logger.warning(f"Could not create sonic profile for '{artist_name}'")
            return []
        
        logger.info(f"   🎚️ Sonic profile: energy={sonic_profile['energy']:.2f}, "
                   f"danceability={sonic_profile['danceability']:.2f}, "
                   f"valence={sonic_profile['valence']:.2f}")
        
        # Step 3: Try recommendations approach (may fail)
        similar_artists = []
        try:
            recommendations_artists = self._get_recommendations_based_similarity(
                artist_id, sonic_profile, limit * 2
            )
            similar_artists.extend(recommendations_artists)
            logger.info(f"   🎯 Recommendations: {len(recommendations_artists)} artists")
        except Exception as e:
            logger.debug(f"Recommendations failed (expected): {e}")
        
        # Step 4: Fallback to playlist archaeology if recommendations failed
        if len(similar_artists) < 5:
            logger.info("   📜 Falling back to playlist archaeology method...")
            playlist_artists = self._get_playlist_based_similarity(artist_name, limit * 2)
            similar_artists.extend(playlist_artists)
            logger.info(f"   📜 Playlist method: {len(playlist_artists)} artists")
        
        # Step 5: Combine, deduplicate, and score
        final_artists = self._combine_and_score_artists(
            similar_artists, sonic_profile, limit
        )
        
        logger.info(f"✅ Audio similarity found {len(final_artists)} artists")
        return final_artists
    
    def _search_artist_id(self, artist_name: str) -> Optional[str]:
        """Search for artist ID (reuses existing working functionality)."""
        try:
            access_token = _get_spotify_access_token()
            if not access_token:
                return None
            
            url = "https://api.spotify.com/v1/search"
            params = {
                'q': f'artist:"{artist_name}"',
                'type': 'artist',
                'limit': 1
            }
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = requests.get(url, params=params, headers=headers)
            time.sleep(0.1)
            
            if response.status_code == 200:
                data = response.json()
                artists = data.get('artists', {}).get('items', [])
                if artists:
                    return artists[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching for artist '{artist_name}': {e}")
            return None
    
    def _get_artist_sonic_profile(self, artist_id: str, artist_name: str) -> Optional[Dict]:
        """
        Create sonic profile by analyzing artist's top tracks.
        This uses the working top-tracks endpoint.
        """
        try:
            access_token = _get_spotify_access_token()
            if not access_token:
                return None
            
            headers = {'Authorization': f'Bearer {access_token}'}
            
            # Get top tracks
            url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
            params = {'market': 'US'}
            
            response = requests.get(url, params=params, headers=headers)
            time.sleep(0.1)
            
            if response.status_code != 200:
                logger.error(f"Top tracks failed: {response.status_code}")
                return None
            
            tracks_data = response.json()
            tracks = tracks_data.get('tracks', [])
            
            if not tracks:
                logger.warning(f"No top tracks found for {artist_name}")
                return None
            
            # Get audio features for tracks
            track_ids = [track['id'] for track in tracks[:10]]  # Top 10 tracks
            
            features_url = "https://api.spotify.com/v1/audio-features"
            params = {'ids': ','.join(track_ids)}
            
            features_response = requests.get(features_url, params=params, headers=headers)
            time.sleep(0.1)
            
            if features_response.status_code != 200:
                logger.error(f"Audio features failed: {features_response.status_code}")
                return None
            
            features_data = features_response.json()
            audio_features = features_data.get('audio_features', [])
            
            # Filter out None values (tracks without audio features)
            valid_features = [f for f in audio_features if f is not None]
            
            if not valid_features:
                logger.warning(f"No audio features available for {artist_name}")
                return None
            
            # Calculate average sonic profile
            sonic_profile = self._calculate_sonic_profile(valid_features)
            
            logger.debug(f"Created sonic profile from {len(valid_features)} tracks")
            return sonic_profile
            
        except Exception as e:
            logger.error(f"Error creating sonic profile for {artist_name}: {e}")
            return None
    
    def _calculate_sonic_profile(self, audio_features: List[Dict]) -> Dict:
        """Calculate average audio features to create sonic profile."""
        # Key audio features for similarity
        feature_keys = [
            'energy', 'danceability', 'valence', 'acousticness',
            'speechiness', 'instrumentalness', 'tempo'
        ]
        
        profile = {}
        
        for key in feature_keys:
            values = [f[key] for f in audio_features if key in f and f[key] is not None]
            if values:
                if key == 'tempo':
                    # Normalize tempo to 0-1 scale (assuming 60-200 BPM range)
                    normalized_values = [(v - 60) / (200 - 60) for v in values]
                    normalized_values = [max(0, min(1, v)) for v in normalized_values]  # Clamp
                    profile[key] = statistics.mean(normalized_values)
                else:
                    profile[key] = statistics.mean(values)
        
        return profile
    
    def _get_recommendations_based_similarity(self, artist_id: str, sonic_profile: Dict, limit: int) -> List[Dict]:
        """
        Try to get similar artists using recommendations endpoint.
        This may fail due to auth restrictions, so it's wrapped in try-catch.
        """
        try:
            access_token = _get_spotify_access_token()
            if not access_token:
                return []
            
            headers = {'Authorization': f'Bearer {access_token}'}
            
            # Build recommendations query with target audio features
            url = "https://api.spotify.com/v1/recommendations"
            params = {
                'seed_artists': artist_id,
                'limit': min(100, limit * 5),  # Get more tracks to extract artists from
                'market': 'US'
            }
            
            # Add target audio features from sonic profile
            for feature, value in sonic_profile.items():
                if feature in ['energy', 'danceability', 'valence', 'acousticness']:
                    params[f'target_{feature}'] = round(value, 2)
            
            response = requests.get(url, params=params, headers=headers)
            time.sleep(0.1)
            
            if response.status_code != 200:
                logger.debug(f"Recommendations failed: {response.status_code}")
                return []
            
            data = response.json()
            tracks = data.get('tracks', [])
            
            # Extract unique artists from recommended tracks
            artist_counts = {}
            for track in tracks:
                for artist in track.get('artists', []):
                    artist_name = artist['name']
                    if artist_name not in artist_counts:
                        artist_counts[artist_name] = {
                            'count': 0,
                            'popularity': artist.get('popularity', 0),
                            'id': artist['id']
                        }
                    artist_counts[artist_name]['count'] += 1
            
            # Convert to scored list
            similar_artists = []
            max_count = max(info['count'] for info in artist_counts.values()) if artist_counts else 1
            
            for artist_name, info in artist_counts.items():
                # Score based on frequency and popularity
                frequency_score = info['count'] / max_count
                popularity_score = info['popularity'] / 100.0
                combined_score = (frequency_score * 0.7) + (popularity_score * 0.3)
                
                similar_artists.append({
                    'name': artist_name,
                    'match': combined_score,
                    'source': 'spotify_recommendations',
                    'method': 'audio_features',
                    'frequency': info['count'],
                    'popularity': info['popularity']
                })
            
            # Sort by score
            similar_artists.sort(key=lambda x: x['match'], reverse=True)
            return similar_artists[:limit]
            
        except Exception as e:
            logger.debug(f"Recommendations method failed: {e}")
            return []
    
    def _get_playlist_based_similarity(self, artist_name: str, limit: int) -> List[Dict]:
        """
        Fallback method: Find similar artists through playlist co-occurrence.
        Searches for playlists containing the artist and analyzes other artists.
        """
        try:
            access_token = _get_spotify_access_token()
            if not access_token:
                return []
            
            headers = {'Authorization': f'Bearer {access_token}'}
            
            # Search for playlists containing the artist
            search_queries = [
                f'"{artist_name}"',
                f'{artist_name} radio',
                f'This is {artist_name}',
                f'{artist_name} mix'
            ]
            
            all_playlist_artists = {}
            
            for query in search_queries:
                try:
                    url = "https://api.spotify.com/v1/search"
                    params = {
                        'q': query,
                        'type': 'playlist',
                        'limit': 20,
                        'market': 'US'
                    }
                    
                    response = requests.get(url, params=params, headers=headers)
                    time.sleep(0.1)
                    
                    if response.status_code == 200:
                        data = response.json()
                        playlists = data.get('playlists', {}).get('items', [])
                        
                        # Analyze first few relevant playlists
                        for playlist in playlists[:5]:
                            playlist_artists = self._analyze_playlist_artists(
                                playlist['id'], artist_name, headers
                            )
                            
                            # Merge artist counts
                            for artist, count in playlist_artists.items():
                                if artist not in all_playlist_artists:
                                    all_playlist_artists[artist] = 0
                                all_playlist_artists[artist] += count
                
                except Exception as e:
                    logger.debug(f"Playlist search failed for query '{query}': {e}")
                    continue
                
                time.sleep(0.2)  # Rate limiting between queries
            
            # Convert to scored list
            if not all_playlist_artists:
                return []
            
            max_count = max(all_playlist_artists.values())
            similar_artists = []
            
            for artist_name_found, count in all_playlist_artists.items():
                score = count / max_count
                
                similar_artists.append({
                    'name': artist_name_found,
                    'match': score,
                    'source': 'spotify_playlists',
                    'method': 'playlist_archaeology',
                    'co_occurrence_count': count
                })
            
            # Sort by score and limit
            similar_artists.sort(key=lambda x: x['match'], reverse=True)
            return similar_artists[:limit]
            
        except Exception as e:
            logger.error(f"Playlist archaeology failed: {e}")
            return []
    
    def _analyze_playlist_artists(self, playlist_id: str, target_artist: str, headers: Dict) -> Dict[str, int]:
        """Analyze artists in a playlist and count co-occurrences."""
        try:
            url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
            params = {'limit': 100, 'market': 'US'}
            
            response = requests.get(url, params=params, headers=headers)
            time.sleep(0.1)
            
            if response.status_code != 200:
                return {}
            
            data = response.json()
            items = data.get('items', [])
            
            artist_counts = {}
            found_target = False
            
            for item in items:
                track = item.get('track')
                if not track or track.get('type') != 'track':
                    continue
                
                for artist in track.get('artists', []):
                    artist_name = artist['name']
                    
                    # Check if this playlist actually contains our target artist
                    if artist_name.lower() == target_artist.lower():
                        found_target = True
                    
                    if artist_name.lower() != target_artist.lower():  # Exclude self
                        if artist_name not in artist_counts:
                            artist_counts[artist_name] = 0
                        artist_counts[artist_name] += 1
            
            # Only return counts if the playlist actually contained our target artist
            return artist_counts if found_target else {}
            
        except Exception as e:
            logger.debug(f"Error analyzing playlist {playlist_id}: {e}")
            return {}
    
    def _combine_and_score_artists(self, artists_list: List[Dict], sonic_profile: Dict, limit: int) -> List[Dict]:
        """
        Combine artists from different methods, deduplicate, and create final scores.
        """
        # Group by artist name
        artist_groups = {}
        for artist in artists_list:
            name_key = artist['name'].lower().strip()
            if name_key not in artist_groups:
                artist_groups[name_key] = []
            artist_groups[name_key].append(artist)
        
        # Combine multiple sources for each artist
        combined_artists = []
        for name_key, artist_entries in artist_groups.items():
            if len(artist_entries) == 1:
                combined_artists.append(artist_entries[0])
            else:
                # Multiple sources - combine scores
                combined_artist = self._merge_artist_sources(artist_entries)
                combined_artists.append(combined_artist)
        
        # Sort by score and limit
        combined_artists.sort(key=lambda x: x['match'], reverse=True)
        final_artists = combined_artists[:limit]
        
        # Add metadata for consistency with other similarity sources
        for artist in final_artists:
            artist['lastfm_similarity'] = 0.0  # Not from Last.fm
            artist['spotify_popularity'] = artist.get('popularity', 0)
            artist['manual_connection'] = False
            artist['bidirectional_source'] = False
            if 'relationship_type' not in artist:
                artist['relationship_type'] = f"spotify_{artist['method']}"
        
        return final_artists
    
    def _merge_artist_sources(self, artist_entries: List[Dict]) -> Dict:
        """Merge multiple entries for the same artist from different sources."""
        # Use the highest scoring entry as base
        base_entry = max(artist_entries, key=lambda x: x['match']).copy()
        
        # Enhance with combined metadata
        sources = [entry['source'] for entry in artist_entries]
        methods = [entry['method'] for entry in artist_entries]
        
        base_entry['sources'] = sources
        base_entry['methods'] = methods
        base_entry['source_count'] = len(sources)
        
        # If multiple sources agree, boost the score
        if len(sources) > 1:
            boost_factor = 1.1  # 10% boost for multi-source agreement
            base_entry['match'] = min(1.0, base_entry['match'] * boost_factor)
            base_entry['source'] = 'spotify_multi_source'
            base_entry['method'] = 'combined'
        
        return base_entry

def test_spotify_audio_similarity():
    """Test the Spotify audio similarity system."""
    print("🧪 Testing Spotify Audio Similarity System")
    print("=" * 50)
    
    try:
        config = AppConfig("configurations.txt")
        similarity_finder = SpotifyAudioSimilarityFinder(config)
        
        # Test with artists we know work
        test_artists = [
            "Taylor Swift",
            "TWICE", 
            "Paramore",
            "Ed Sheeran"
        ]
        
        for artist in test_artists:
            print(f"\n🎯 Testing audio similarity for '{artist}':")
            
            results = similarity_finder.get_audio_based_similar_artists(artist, limit=8)
            
            if results:
                print(f"   ✅ Found {len(results)} similar artists:")
                for i, similar in enumerate(results[:5], 1):
                    method_icon = "🎯" if similar['method'] == 'audio_features' else "📜"
                    print(f"      {i}. {similar['name']} ({similar['match']:.3f}, {method_icon} {similar['method']})")
            else:
                print("   ❌ No similar artists found")
            
            time.sleep(0.5)  # Rate limiting between artists
    
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_spotify_audio_similarity()