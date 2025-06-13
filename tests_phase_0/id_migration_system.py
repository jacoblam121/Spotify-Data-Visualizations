#!/usr/bin/env python3
"""
Phase 0.0.2: ID Migration System Design
Creates stable ID system with Spotify/MusicBrainz fallbacks
"""

import json
import hashlib
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class IDType(Enum):
    SPOTIFY = "spotify"
    MUSICBRAINZ = "mbid"
    LOCAL_HASH = "local"

@dataclass
class ArtistID:
    """Stable artist identifier with source tracking."""
    id: str
    type: IDType
    confidence: float  # 0.0 to 1.0
    original_name: str
    canonical_name: str
    
    def __str__(self) -> str:
        return f"{self.type.value}:{self.id}"

class IDMigrationSystem:
    """System for creating stable artist IDs from current name-based system."""
    
    def __init__(self):
        """Initialize the ID migration system."""
        self.spotify_cache = {}  # artist_name -> spotify_data
        self.musicbrainz_cache = {}  # artist_name -> mbid_data
        self.name_normalizations = {}  # original -> normalized
        
    def normalize_artist_name(self, name: str) -> str:
        """
        Normalize artist name for consistent matching.
        
        Handles diacritics, special characters, and common variations.
        
        Args:
            name: Original artist name
            
        Returns:
            Normalized name for matching (ASCII, lowercase, cleaned)
        """
        if name in self.name_normalizations:
            return self.name_normalizations[name]
        
        # Remove common patterns that cause mismatches
        normalized = name.lower().strip()
        
        # Remove parenthetical information like "(트와이스)" 
        normalized = re.sub(r'\s*\([^)]*\)', '', normalized)
        
        # Remove "The " prefix
        if normalized.startswith('the '):
            normalized = normalized[4:]
        
        # Remove diacritics using Unicode normalization
        import unicodedata
        # Decompose characters (ó -> o + ́)
        decomposed = unicodedata.normalize('NFKD', normalized)
        # Remove combining marks (accents, diacritics)
        ascii_text = ''.join(c for c in decomposed if not unicodedata.combining(c))
        
        # Handle remaining special characters
        normalized = re.sub(r'[^\w\s]', '', ascii_text)
        
        # Collapse whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        self.name_normalizations[name] = normalized
        return normalized
    
    def create_local_hash(self, original_name: str) -> str:
        """
        Create a local hash ID for artists without external matches.
        
        Args:
            original_name: Original artist name
            
        Returns:
            SHA1 hash of normalized name
        """
        normalized = self.normalize_artist_name(original_name)
        hash_input = normalized.encode('utf-8')
        return hashlib.sha1(hash_input).hexdigest()[:16]
    
    def extract_spotify_id(self, artist_data: Dict) -> Optional[ArtistID]:
        """
        Extract Spotify ID from enhanced artist data.
        
        Args:
            artist_data: Artist data dict from network system
            
        Returns:
            ArtistID if Spotify data available, None otherwise
        """
        if not artist_data.get('spotify_data') or not artist_data['spotify_data'].get('spotify_artist_id'):
            return None
        
        spotify_data = artist_data['spotify_data']
        spotify_id = spotify_data['spotify_artist_id']
        
        # Confidence based on data completeness
        confidence = 0.9  # High confidence for Spotify matches
        if spotify_data.get('popularity', 0) == 0:
            confidence = 0.7  # Lower confidence if no popularity data
        
        return ArtistID(
            id=spotify_id,
            type=IDType.SPOTIFY,
            confidence=confidence,
            original_name=artist_data['artist_name'],
            canonical_name=spotify_data.get('name', artist_data['artist_name'])
        )
    
    def extract_musicbrainz_id(self, artist_data: Dict) -> Optional[ArtistID]:
        """
        Extract MusicBrainz ID from enhanced artist data.
        
        Args:
            artist_data: Artist data dict from network system
            
        Returns:
            ArtistID if MusicBrainz data available, None otherwise
        """
        # Check Last.fm data for MusicBrainz ID
        if artist_data.get('lastfm_data') and artist_data['lastfm_data'].get('mbid'):
            mbid = artist_data['lastfm_data']['mbid']
            
            return ArtistID(
                id=mbid,
                type=IDType.MUSICBRAINZ,
                confidence=0.8,  # High confidence for MBID
                original_name=artist_data['artist_name'],
                canonical_name=artist_data['lastfm_data'].get('name', artist_data['artist_name'])
            )
        
        return None
    
    def create_fallback_id(self, artist_data: Dict) -> ArtistID:
        """
        Create fallback local hash ID.
        
        Args:
            artist_data: Artist data dict from network system
            
        Returns:
            Local hash ArtistID
        """
        original_name = artist_data['artist_name']
        hash_id = self.create_local_hash(original_name)
        
        return ArtistID(
            id=hash_id,
            type=IDType.LOCAL_HASH,
            confidence=0.3,  # Low confidence for local hash
            original_name=original_name,
            canonical_name=original_name
        )
    
    def migrate_artist_id(self, artist_data: Dict) -> ArtistID:
        """
        Migrate a single artist from name-based to stable ID.
        
        Args:
            artist_data: Enhanced artist data from network system
            
        Returns:
            Best available ArtistID
        """
        # Try Spotify first (highest quality)
        spotify_id = self.extract_spotify_id(artist_data)
        if spotify_id:
            return spotify_id
        
        # Fallback to MusicBrainz
        mbid = self.extract_musicbrainz_id(artist_data)
        if mbid:
            return mbid
        
        # Last resort: local hash
        return self.create_fallback_id(artist_data)
    
    def migrate_network_data(self, network_data: Dict) -> Dict:
        """
        Migrate entire network data to use stable IDs.
        
        Args:
            network_data: Current network data with name-based IDs
            
        Returns:
            Network data with stable IDs
        """
        print("🔄 Migrating network data to stable ID system...")
        
        # Create ID mapping
        id_mapping = {}  # old_id -> new_id
        migrated_nodes = []
        
        for node in network_data['nodes']:
            # Create mock artist data structure for migration
            artist_data = {
                'artist_name': node['name'],
                'spotify_data': {
                    'spotify_artist_id': node.get('spotify_id'),
                    'name': node['name'],
                    'popularity': node.get('spotify_popularity', 0)
                } if node.get('spotify_id') else None,
                'lastfm_data': {
                    'mbid': None,  # Would need to enhance to include MBID
                    'name': node['name']
                } if node.get('lastfm_listeners') else None
            }
            
            # Migrate ID
            new_id = self.migrate_artist_id(artist_data)
            old_id = node['id']
            
            # Store mapping
            id_mapping[old_id] = str(new_id)
            
            # Update node
            migrated_node = node.copy()
            migrated_node['id'] = str(new_id)
            migrated_node['id_type'] = new_id.type.value
            migrated_node['id_confidence'] = new_id.confidence
            migrated_node['canonical_name'] = new_id.canonical_name
            
            migrated_nodes.append(migrated_node)
        
        # Update edges with new IDs
        migrated_edges = []
        for edge in network_data.get('edges', []):
            if edge['source'] in id_mapping and edge['target'] in id_mapping:
                migrated_edge = edge.copy()
                migrated_edge['source'] = id_mapping[edge['source']]
                migrated_edge['target'] = id_mapping[edge['target']]
                migrated_edges.append(migrated_edge)
            else:
                print(f"⚠️  Skipping edge with unmapped ID: {edge['source']} -> {edge['target']}")
        
        # Update metadata
        migrated_metadata = network_data.get('metadata', {}).copy()
        migrated_metadata['id_migration'] = {
            'migration_date': json.dumps(None),  # Would use datetime.now().isoformat()
            'total_artists': len(migrated_nodes),
            'id_types': {
                'spotify': len([n for n in migrated_nodes if n['id_type'] == 'spotify']),
                'musicbrainz': len([n for n in migrated_nodes if n['id_type'] == 'mbid']),
                'local_hash': len([n for n in migrated_nodes if n['id_type'] == 'local'])
            },
            'mapping_changes': len([k for k, v in id_mapping.items() if k != v])
        }
        
        migrated_data = {
            'nodes': migrated_nodes,
            'edges': migrated_edges,
            'metadata': migrated_metadata
        }
        
        print(f"✅ ID migration complete:")
        print(f"  Spotify IDs: {migrated_metadata['id_migration']['id_types']['spotify']}")
        print(f"  MusicBrainz IDs: {migrated_metadata['id_migration']['id_types']['musicbrainz']}")
        print(f"  Local hashes: {migrated_metadata['id_migration']['id_types']['local_hash']}")
        print(f"  IDs changed: {migrated_metadata['id_migration']['mapping_changes']}")
        
        return migrated_data
    
    def generate_id_mapping_report(self, network_data: Dict) -> Dict:
        """
        Generate a report of current ID system for manual review.
        
        Args:
            network_data: Current network data
            
        Returns:
            ID mapping report
        """
        report = {
            'summary': {
                'total_artists': len(network_data['nodes']),
                'using_name_ids': 0,
                'potential_conflicts': []
            },
            'artist_analysis': []
        }
        
        name_ids = set()
        
        for node in network_data['nodes']:
            current_id = node['id']
            name = node['name']
            
            # Check if using name-based ID
            if current_id == name.lower().replace(' ', ''):
                report['summary']['using_name_ids'] += 1
            
            # Check for potential conflicts
            normalized = self.normalize_artist_name(name)
            if normalized in name_ids:
                report['summary']['potential_conflicts'].append({
                    'normalized_name': normalized,
                    'artists': [name]  # Would collect all artists with same normalized name
                })
            name_ids.add(normalized)
            
            # Analyze individual artist
            analysis = {
                'current_id': current_id,
                'name': name,
                'normalized_name': normalized,
                'has_spotify_id': bool(node.get('spotify_id')),
                'has_lastfm_data': bool(node.get('lastfm_listeners')),
                'recommended_id_type': 'spotify' if node.get('spotify_id') else 'local_hash'
            }
            
            report['artist_analysis'].append(analysis)
        
        return report

def test_id_migration_system():
    """Test the ID migration system with sample data."""
    print("🧪 Testing ID Migration System")
    print("=" * 50)
    
    # Sample network data (current format)
    sample_data = {
        'nodes': [
            {
                'id': 'taylor swift',
                'name': 'Taylor Swift',
                'spotify_id': '06HL4z0CvFAxyc27GXpf02',
                'spotify_popularity': 98,
                'lastfm_listeners': 5160232
            },
            {
                'id': 'unknown artist',
                'name': 'Unknown Artist',
                'lastfm_listeners': 1000
            }
        ],
        'edges': [
            {
                'source': 'taylor swift',
                'target': 'unknown artist',
                'weight': 0.5
            }
        ],
        'metadata': {}
    }
    
    # Test migration
    migration_system = IDMigrationSystem()
    
    # Generate report
    print("📊 Current ID Analysis:")
    report = migration_system.generate_id_mapping_report(sample_data)
    print(f"  Total artists: {report['summary']['total_artists']}")
    print(f"  Using name IDs: {report['summary']['using_name_ids']}")
    
    # Test migration
    print(f"\\n🔄 Testing migration...")
    migrated_data = migration_system.migrate_network_data(sample_data)
    
    print(f"\\n📈 Migration Results:")
    for node in migrated_data['nodes']:
        print(f"  {node['canonical_name']}: {node['id']} ({node['id_type']}, confidence: {node['id_confidence']:.1f})")
    
    print(f"\\n🔗 Edge Updates:")
    for edge in migrated_data['edges']:
        print(f"  {edge['source']} -> {edge['target']}")
    
    return migrated_data

if __name__ == "__main__":
    result = test_id_migration_system()
    print(f"\\n✅ ID Migration System test complete!")