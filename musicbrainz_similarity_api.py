#!/usr/bin/env python3
"""
MusicBrainz Relationship-Based Similarity
==========================================
Uses MusicBrainz's structured relationship data to find artist connections.
Unlike Last.fm/Deezer "sounds like" algorithms, this provides explicit relationships:
- Member of band
- Collaboration
- Influenced by
- Tribute to
- Same person (different names)

Perfect for discovering connections that algorithms miss!
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

# Add project modules
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import AppConfig

logger = logging.getLogger(__name__)

class MusicBrainzSimilarityAPI:
    """
    MusicBrainz API integration for relationship-based artist connections.
    Free, no auth required, excellent metadata quality.
    """
    
    def __init__(self, config: AppConfig = None):
        """Initialize MusicBrainz API client."""
        self.base_url = "https://musicbrainz.org/ws/2"
        self.rate_limit_delay = 1.0  # 1 second between requests (required by MusicBrainz)
        self.user_agent = "SpotifyDataViz/1.0 (contact@example.com)"  # Required by MusicBrainz
        
        # Relationship types we consider as "similarity"
        self.similarity_relationship_types = {
            'member of band': 0.9,      # Band member connections
            'collaboration': 0.8,       # Collaborations
            'tribute': 0.7,             # Tribute acts
            'influenced by': 0.6,       # Influence relationships  
            'is person': 0.95,          # Same person, different names
            'performance name': 0.95,   # Performance names/aliases
            'parent': 0.5,              # Parent/child bands
            'sibling': 0.5,             # Sibling bands
            'founder': 0.7,             # Band founders
            'supporting musician': 0.4   # Supporting musicians
        }
        
        logger.info("MusicBrainz Similarity API initialized:")
        logger.info("  No authentication required")
        logger.info("  Rate limit: 1 request per second")
        logger.info(f"  Tracking {len(self.similarity_relationship_types)} relationship types")
    
    def get_relationship_based_similar_artists(self, artist_name: str, limit: int = 20) -> List[Dict]:
        """
        Get similar artists based on MusicBrainz relationship data.
        
        Process:
        1. Search for artist in MusicBrainz
        2. Get all artist relationships
        3. Score relationships based on type
        4. Return in Last.fm-compatible format
        
        Args:
            artist_name: Artist to find relationships for
            limit: Maximum number of related artists to return
            
        Returns:
            List of related artists in compatibility format
        """
        logger.info(f"🎭 MusicBrainz relationship search for '{artist_name}'")
        
        # Step 1: Find artist MBID
        mbid = self._search_artist_mbid(artist_name)
        if not mbid:
            logger.warning(f"Artist '{artist_name}' not found in MusicBrainz")
            return []
        
        # Step 2: Get artist relationships
        relationships = self._get_artist_relationships(mbid, artist_name)
        
        # Step 3: Convert to similarity format
        similar_artists = self._format_relationships_as_similarities(relationships, limit)
        
        logger.info(f"✅ MusicBrainz found {len(similar_artists)} relationship-based connections")
        return similar_artists
    
    def _search_artist_mbid(self, artist_name: str) -> Optional[str]:
        """Search for artist MBID in MusicBrainz."""
        try:
            url = f"{self.base_url}/artist"
            params = {
                'query': f'artist:"{artist_name}"',
                'limit': 5,
                'fmt': 'json'
            }
            headers = {'User-Agent': self.user_agent}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            time.sleep(self.rate_limit_delay)
            
            if response.status_code == 200:
                data = response.json()
                artists = data.get('artists', [])
                
                if artists:
                    # Find best match (exact name match preferred)
                    for artist in artists:
                        if artist['name'].lower() == artist_name.lower():
                            mbid = artist['id']
                            logger.debug(f"Found exact match: {artist['name']} (MBID: {mbid})")
                            return mbid
                    
                    # Fall back to first result if no exact match
                    best_match = artists[0]
                    mbid = best_match['id']
                    logger.debug(f"Using best match: {best_match['name']} (MBID: {mbid})")
                    return mbid
                else:
                    logger.debug(f"No MusicBrainz artists found for '{artist_name}'")
            else:
                logger.error(f"MusicBrainz search failed: {response.status_code} - {response.text}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching MusicBrainz for '{artist_name}': {e}")
            return None
    
    def _get_artist_relationships(self, mbid: str, artist_name: str) -> List[Dict]:
        """Get all relationships for an artist from MusicBrainz."""
        try:
            url = f"{self.base_url}/artist/{mbid}"
            params = {
                'inc': 'artist-rels',  # Include artist-to-artist relationships
                'fmt': 'json'
            }
            headers = {'User-Agent': self.user_agent}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            time.sleep(self.rate_limit_delay)
            
            if response.status_code == 200:
                data = response.json()
                relations = data.get('relations', [])
                
                # Filter for artist-to-artist relationships
                artist_relations = []
                for relation in relations:
                    if relation.get('target-type') == 'artist' and 'artist' in relation:
                        target_artist = relation['artist']
                        relationship_type = relation.get('type-id', '')  # We'll use the human-readable type
                        
                        # Get relationship type name (it's directly in the 'type' field)
                        type_name = relation.get('type', '').lower()
                        
                        if type_name:
                            artist_relations.append({
                                'target_name': target_artist['name'],
                                'target_mbid': target_artist['id'],
                                'relationship_type': type_name,
                                'direction': relation.get('direction', 'forward')
                            })
                
                logger.debug(f"Found {len(artist_relations)} relationships for {artist_name}")
                return artist_relations
            else:
                logger.error(f"MusicBrainz relations failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting relationships for MBID {mbid}: {e}")
            return []
    
    def _get_relationship_type_name(self, relation: Dict) -> Optional[str]:
        """Extract relationship type name from MusicBrainz relation."""
        try:
            # MusicBrainz includes the relationship type info in the relation
            if 'type' in relation:
                return relation['type'].lower()
            
            # Fallback: try to infer from type-id or other fields
            type_id = relation.get('type-id', '')
            
            # Common MusicBrainz relationship type IDs (these are stable UUIDs)
            type_id_map = {
                '5be4c609-9aba-4459-b8d6-e6c2e29c4cd7': 'member of band',
                '75c09861-6857-4ec0-9729-84eefde7fc86': 'collaboration',
                '50c84d42-f1c4-4d8e-b6a8-4de6a26cc9f4': 'tribute',
                '1d4c8b30-6a52-4c8b-a3d7-8f6b1c9c8e4a': 'influenced by',
                # Add more as needed
            }
            
            if type_id in type_id_map:
                return type_id_map[type_id]
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting relationship type: {e}")
            return None
    
    def _format_relationships_as_similarities(self, relationships: List[Dict], limit: int) -> List[Dict]:
        """Convert MusicBrainz relationships to similarity format."""
        similar_artists = []
        
        for relation in relationships:
            relationship_type = relation['relationship_type']
            
            # Check if this relationship type indicates similarity
            similarity_score = self._get_similarity_score(relationship_type)
            
            if similarity_score > 0:
                similar_artists.append({
                    'name': relation['target_name'],
                    'match': similarity_score,
                    'source': 'musicbrainz',
                    'lastfm_similarity': 0.0,
                    'deezer_similarity': 0.0, 
                    'manual_connection': False,
                    'bidirectional_source': False,
                    'relationship_type': f'musicbrainz_{relationship_type.replace(" ", "_")}',
                    
                    # MusicBrainz-specific metadata
                    'musicbrainz_mbid': relation['target_mbid'],
                    'musicbrainz_relationship': relationship_type,
                    'relationship_direction': relation['direction']
                })
        
        # Sort by similarity score and limit
        similar_artists.sort(key=lambda x: x['match'], reverse=True)
        return similar_artists[:limit]
    
    def _get_similarity_score(self, relationship_type: str) -> float:
        """Get similarity score for a relationship type."""
        # Normalize relationship type
        normalized_type = relationship_type.lower().strip()
        
        # Check direct matches
        if normalized_type in self.similarity_relationship_types:
            return self.similarity_relationship_types[normalized_type]
        
        # Check partial matches for fuzzy relationship types
        for rel_type, score in self.similarity_relationship_types.items():
            if rel_type in normalized_type or normalized_type in rel_type:
                return score * 0.8  # Slightly lower score for fuzzy matches
        
        # Check for common variations
        if 'member' in normalized_type or 'band' in normalized_type:
            return 0.9
        if 'collab' in normalized_type:
            return 0.8
        if 'tribute' in normalized_type:
            return 0.7
        if 'influence' in normalized_type:
            return 0.6
        
        return 0.0  # Unknown relationship type
    
    def test_artist_search(self, artist_name: str) -> Dict:
        """Test search functionality and return detailed info."""
        print(f"🔍 Testing MusicBrainz search for '{artist_name}'")
        
        # Search for artist
        mbid = self._search_artist_mbid(artist_name)
        if not mbid:
            return {'status': 'not_found'}
        
        # Get relationships
        try:
            relationships = self._get_artist_relationships(mbid, artist_name)
            
            result = {
                'status': 'found',
                'mbid': mbid,
                'relationships_count': len(relationships),
                'relationship_types': list(set(r['relationship_type'] for r in relationships))
            }
            
            print(f"   ✅ Found: MBID {mbid}")
            print(f"   📊 Relationships: {len(relationships)}")
            if relationships:
                print(f"   🔗 Types: {', '.join(result['relationship_types'][:5])}")
            
            return result
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

def test_musicbrainz_similarity():
    """Test MusicBrainz similarity API with various artists."""
    print("🧪 Testing MusicBrainz Relationship-Based Similarity")
    print("=" * 55)
    
    mb_api = MusicBrainzSimilarityAPI()
    
    # Test search functionality first
    print("\n1️⃣ Testing Artist Search & Relationship Discovery")
    print("-" * 50)
    
    search_tests = ["The Beatles", "Radiohead", "Taylor Swift", "BTS", "Nirvana"]
    for artist in search_tests:
        result = mb_api.test_artist_search(artist)
        if result['status'] != 'found':
            print(f"   ❌ {artist}: {result}")
        time.sleep(1.2)  # Rate limiting
    
    # Test similarity functionality
    print("\n2️⃣ Testing Relationship-Based Similarity")
    print("-" * 45)
    
    similarity_tests = ["The Beatles", "Radiohead", "BTS"]
    for artist in similarity_tests:
        print(f"\n🎯 Relationship search for '{artist}':")
        
        similar_artists = mb_api.get_relationship_based_similar_artists(artist, limit=8)
        
        if similar_artists:
            print(f"   ✅ Found {len(similar_artists)} relationship-based connections:")
            for i, similar in enumerate(similar_artists[:5], 1):
                rel_type = similar.get('musicbrainz_relationship', 'unknown')
                print(f"      {i}. {similar['name']} ({similar['match']:.2f}, {rel_type})")
        else:
            print("   ❌ No relationship-based connections found")
        
        time.sleep(1.5)  # Rate limiting

def test_musicbrainz_vs_other_apis():
    """Compare MusicBrainz vs other APIs for coverage."""
    print("\n3️⃣ Testing MusicBrainz vs Other APIs Coverage")
    print("-" * 50)
    
    try:
        from deezer_similarity_api import DeezerSimilarityAPI
        from lastfm_utils import LastfmAPI
        from config_loader import AppConfig
        
        config = AppConfig("configurations.txt")
        lastfm_config = config.get_lastfm_config()
        
        # Initialize APIs
        mb_api = MusicBrainzSimilarityAPI()
        deezer_api = DeezerSimilarityAPI()
        
        lastfm_api = None
        if lastfm_config['enabled'] and lastfm_config['api_key']:
            lastfm_api = LastfmAPI(
                lastfm_config['api_key'],
                lastfm_config['api_secret'],
                lastfm_config['cache_dir']
            )
        
        # Test cases that might benefit from relationship data
        test_cases = ["The Beatles", "John Lennon", "Paul McCartney"]
        
        for artist in test_cases:
            print(f"\n🔄 Comparing coverage for '{artist}':")
            
            # Test MusicBrainz (relationship-based)
            mb_results = mb_api.get_relationship_based_similar_artists(artist, limit=5)
            print(f"   🎭 MusicBrainz: {len(mb_results)} relationship connections")
            
            if mb_results:
                for similar in mb_results[:3]:
                    rel_type = similar.get('musicbrainz_relationship', 'unknown')
                    print(f"      - {similar['name']} ({rel_type})")
            
            # Test Deezer (algorithmic)
            deezer_results = deezer_api.get_similar_artists(artist, limit=5)
            print(f"   🎵 Deezer: {len(deezer_results)} algorithmic connections")
            
            if deezer_results:
                for similar in deezer_results[:3]:
                    print(f"      - {similar['name']} (algorithmic)")
            
            # Test Last.fm if available
            if lastfm_api:
                lastfm_results = lastfm_api.get_similar_artists(artist, limit=5, use_enhanced_matching=False)
                print(f"   🎶 Last.fm: {len(lastfm_results)} algorithmic connections")
                
                if lastfm_results:
                    for similar in lastfm_results[:3]:
                        print(f"      - {similar['name']} (algorithmic)")
            
            time.sleep(1.5)  # Rate limiting for MusicBrainz
    
    except Exception as e:
        print(f"❌ Coverage test error: {e}")

if __name__ == "__main__":
    test_musicbrainz_similarity()
    test_musicbrainz_vs_other_apis()