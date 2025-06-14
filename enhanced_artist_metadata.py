#!/usr/bin/env python3
"""
Enhanced Artist Metadata System
===============================
Separates similarity matching from display metadata to get:
- Functional similarity data from working profiles
- Accurate display data (listeners, etc.) from main profiles
"""

from typing import Dict, Optional, Tuple
from lastfm_utils import LastfmAPI
from config_loader import AppConfig
import logging

logger = logging.getLogger(__name__)

class EnhancedArtistMetadata:
    """
    Manages artist metadata by separating similarity matching from display data.
    """
    
    def __init__(self):
        """Initialize with Last.fm API."""
        config = AppConfig()
        lastfm_config = config.get_lastfm_config()
        self.api = LastfmAPI(lastfm_config['api_key'], lastfm_config['api_secret'])
        
        # Cache for display metadata
        self.display_metadata_cache = {}
    
    def get_artist_display_metadata(self, artist_name: str) -> Optional[Dict]:
        """
        Get the BEST display metadata for an artist (highest listeners, etc.)
        This is separate from similarity matching.
        """
        if artist_name in self.display_metadata_cache:
            return self.display_metadata_cache[artist_name]
        
        # Test multiple variants to find the highest-listener profile
        variants = self._get_display_variants(artist_name)
        
        best_profile = None
        best_listeners = 0
        
        for variant in variants:
            try:
                params = {'artist': variant}
                response = self.api._make_request('artist.getinfo', params)
                
                if response and 'artist' in response:
                    artist = response['artist']
                    listeners = int(artist['stats']['listeners'])
                    
                    if listeners > best_listeners:
                        best_listeners = listeners
                        best_profile = {
                            'name': artist['name'],
                            'listeners': listeners,
                            'playcount': int(artist['stats']['playcount']),
                            'mbid': artist.get('mbid', ''),
                            'url': artist.get('url', ''),
                            'variant_used': variant
                        }
                        
            except Exception as e:
                logger.debug(f"Failed to get display metadata for variant '{variant}': {e}")
        
        # Cache the result
        self.display_metadata_cache[artist_name] = best_profile
        
        if best_profile:
            logger.info(f"📊 Display metadata for '{artist_name}': {best_profile['listeners']:,} listeners via '{best_profile['variant_used']}'")
        
        return best_profile
    
    def _get_display_variants(self, artist_name: str) -> list[str]:
        """Get variants to test for display metadata (prioritize high-listener profiles)."""
        name_clean = artist_name.strip()
        name_upper = name_clean.upper()
        
        # Basic variants
        variants = [
            name_clean,
            name_clean.title(),
            name_clean.lower(),
            name_clean.upper()
        ]
        
        # Known high-listener patterns for specific artists
        known_patterns = {
            'IVE': ['Ive', 'IVE', 'IVE (아이브)', '아이브'],
            'TWICE': ['TWICE', 'twice', 'TWICE (트와이스)', '트와이스'],
            'BTS': ['BTS', 'bts', 'BTS (방탄소년단)', '방탄소년단'],
            'BLACKPINK': ['BLACKPINK', 'blackpink', 'BLACKPINK (블랙핑크)', '블랙핑크']
        }
        
        if name_upper in known_patterns:
            variants = known_patterns[name_upper] + variants
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for variant in variants:
            if variant not in seen:
                seen.add(variant)
                unique_variants.append(variant)
        
        return unique_variants
    
    def enhance_network_nodes(self, nodes: list[Dict]) -> list[Dict]:
        """
        Enhance network nodes with accurate display metadata.
        
        Args:
            nodes: List of network nodes with basic info
            
        Returns:
            Enhanced nodes with accurate listener counts, etc.
        """
        enhanced_nodes = []
        
        for node in nodes:
            enhanced_node = node.copy()
            artist_name = node.get('name', '')
            
            # Get display metadata
            display_metadata = self.get_artist_display_metadata(artist_name)
            
            if display_metadata:
                # Update with accurate metadata
                enhanced_node.update({
                    'listeners': display_metadata['listeners'],
                    'playcount': display_metadata['playcount'],
                    'lastfm_url': display_metadata['url'],
                    'canonical_name': display_metadata['name'],
                    'display_metadata_source': display_metadata['variant_used']
                })
                
                # Log significant discrepancies
                original_listeners = node.get('listeners', 0)
                if original_listeners > 0 and abs(display_metadata['listeners'] - original_listeners) > original_listeners * 0.5:
                    logger.warning(f"📊 Listener count updated for '{artist_name}': {original_listeners:,} → {display_metadata['listeners']:,}")
            
            enhanced_nodes.append(enhanced_node)
        
        return enhanced_nodes

def test_enhanced_metadata():
    """Test the enhanced metadata system."""
    print("🧪 Testing Enhanced Artist Metadata")
    print("=" * 40)
    
    metadata = EnhancedArtistMetadata()
    
    test_artists = ['IVE', 'TWICE', 'ANYUJIN', 'Taylor Swift']
    
    for artist in test_artists:
        print(f"\n🎯 Testing {artist}:")
        display_data = metadata.get_artist_display_metadata(artist)
        
        if display_data:
            print(f"   Name: {display_data['name']}")
            print(f"   Listeners: {display_data['listeners']:,}")
            print(f"   Playcount: {display_data['playcount']:,}")
            print(f"   Found via: {display_data['variant_used']}")
        else:
            print(f"   ❌ No display metadata found")

if __name__ == "__main__":
    test_enhanced_metadata()