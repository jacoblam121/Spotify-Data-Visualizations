#!/usr/bin/env python3
"""
Ultimate Similarity System (Fixed)
===================================
FINAL COMPREHENSIVE SOLUTION: Combines all our discoveries into one robust system.
"""

import logging
import time
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import sys

# Add project modules
sys.path.insert(0, str(Path(__file__).parent))

from lastfm_utils import LastfmAPI
from deezer_similarity_api import DeezerSimilarityAPI
from manual_connections import get_manual_connections
from config_loader import AppConfig

logger = logging.getLogger(__name__)

class UltimateSimilaritySystem:
    """Ultimate similarity system combining all data sources."""
    
    def __init__(self, config: AppConfig):
        """Initialize with all available APIs and data sources."""
        self.config = config
        self.lastfm_config = config.get_lastfm_config()
        
        # Initialize Last.fm API
        self.lastfm_api = None
        if self.lastfm_config['enabled'] and self.lastfm_config['api_key']:
            self.lastfm_api = LastfmAPI(
                self.lastfm_config['api_key'],
                self.lastfm_config['api_secret'],
                self.lastfm_config['cache_dir']
            )
        
        # Initialize Deezer API (always available, no auth required)
        self.deezer_api = DeezerSimilarityAPI(config)
        
        logger.info(f"Ultimate Similarity System initialized:")
        logger.info(f"  Last.fm available: {bool(self.lastfm_api)}")
        logger.info(f"  Deezer available: True (no auth required)")
    
    def get_ultimate_similar_artists(self, artist_name: str, limit: int = 100, 
                                   min_threshold: float = 0.1) -> List[Dict]:
        """Get comprehensive artist similarity data from all sources."""
        logger.info(f"🌟 Ultimate similarity search for '{artist_name}' (threshold: {min_threshold})")
        
        all_similarities = []
        source_counts = {}
        
        # Source 1: Last.fm similarities (using original names)
        if self.lastfm_api:
            lastfm_similarities = self._get_lastfm_similarities(artist_name, limit * 2, min_threshold)
            all_similarities.extend(lastfm_similarities)
            source_counts['lastfm'] = len(lastfm_similarities)
            logger.info(f"   🎶 Last.fm: {len(lastfm_similarities)} similarities")
        
        # Source 2: Deezer similarities (fills gaps, especially K-pop)
        deezer_similarities = self._get_deezer_similarities(artist_name, limit * 2, min_threshold)
        all_similarities.extend(deezer_similarities)
        source_counts['deezer'] = len(deezer_similarities)
        logger.info(f"   🎵 Deezer: {len(deezer_similarities)} similarities")
        
        # Source 3: Manual connections (obvious relationships)
        manual_similarities = self._get_manual_similarities(artist_name, min_threshold)
        all_similarities.extend(manual_similarities)
        source_counts['manual'] = len(manual_similarities)
        logger.info(f"   ✋ Manual: {len(manual_similarities)} connections")
        
        # Source 4: Smart merging and scoring
        final_similarities = self._ultimate_merge_and_score(
            all_similarities, limit, min_threshold
        )
        
        # Log final statistics
        multi_source_count = sum(1 for s in final_similarities if s.get('source_count', 1) > 1)
        logger.info(f"✅ Ultimate search result: {len(final_similarities)} total similarities")
        logger.info(f"   Sources: {', '.join(f'{k}={v}' for k, v in source_counts.items())}")
        logger.info(f"   Multi-source agreements: {multi_source_count}")
        
        return final_similarities
    
    def _get_lastfm_similarities(self, artist_name: str, limit: int, min_threshold: float) -> List[Dict]:
        """Get Last.fm similarities using ORIGINAL names (not canonical)."""
        try:
            similarities = self.lastfm_api.get_similar_artists(
                artist_name=artist_name,
                limit=limit,
                use_enhanced_matching=False  # This fixes the canonical name mismatch issue
            )
            
            # Filter and add metadata
            filtered = []
            for similar in similarities:
                if similar['match'] >= min_threshold:
                    similar.update({
                        'source': 'lastfm',
                        'lastfm_similarity': similar['match'],
                        'deezer_similarity': 0.0,
                        'manual_connection': False,
                        'relationship_type': 'lastfm_similar'
                    })
                    filtered.append(similar)
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error getting Last.fm similarities for '{artist_name}': {e}")
            return []
    
    def _get_deezer_similarities(self, artist_name: str, limit: int, min_threshold: float) -> List[Dict]:
        """Get Deezer similarities (especially good for K-pop coverage)."""
        try:
            similarities = self.deezer_api.get_similar_artists(artist_name, limit)
            
            # Filter by threshold and add metadata
            filtered = []
            for similar in similarities:
                if similar['match'] >= min_threshold:
                    similar.update({
                        'deezer_similarity': similar['match'],
                        'lastfm_similarity': 0.0,
                        'manual_connection': False
                    })
                    filtered.append(similar)
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error getting Deezer similarities for '{artist_name}': {e}")
            return []
    
    def _get_manual_similarities(self, artist_name: str, min_threshold: float) -> List[Dict]:
        """Get manual connections for obvious relationships."""
        manual_connections = get_manual_connections(artist_name)
        
        similarities = []
        for target_name, similarity_score, relationship_type in manual_connections:
            if similarity_score >= min_threshold:
                similarities.append({
                    'name': target_name,
                    'match': similarity_score,
                    'source': 'manual',
                    'lastfm_similarity': 0.0,
                    'deezer_similarity': 0.0,
                    'manual_connection': True,
                    'relationship_type': f'manual_{relationship_type}'
                })
        
        return similarities
    
    def _ultimate_merge_and_score(self, all_similarities: List[Dict], limit: int,
                                min_threshold: float) -> List[Dict]:
        """Ultimate merging algorithm that handles multiple sources optimally."""
        # Group by artist name (case-insensitive)
        artist_groups = {}
        
        for similarity in all_similarities:
            artist_key = similarity['name'].lower().strip()
            if artist_key not in artist_groups:
                artist_groups[artist_key] = []
            artist_groups[artist_key].append(similarity)
        
        # Merge multiple sources for each artist
        merged_similarities = []
        for artist_key, similarities in artist_groups.items():
            if len(similarities) == 1:
                merged_similarities.append(similarities[0])
            else:
                # Multiple sources - smart merge
                merged = self._smart_merge_artist_sources(similarities)
                merged_similarities.append(merged)
        
        # Filter by threshold
        filtered = [s for s in merged_similarities if s['match'] >= min_threshold]
        
        # Advanced scoring: boost multi-source agreements
        for similarity in filtered:
            source_count = similarity.get('source_count', 1)
            if source_count > 1:
                # Multi-source boost: 10% per additional source
                boost_factor = 1.0 + (0.1 * (source_count - 1))
                similarity['match'] = min(1.0, similarity['match'] * boost_factor)
                similarity['multi_source_boost'] = True
        
        # Sort by enhanced similarity score
        filtered.sort(key=lambda x: (
            x['match'],  # Primary: similarity score
            x.get('source_count', 1),  # Secondary: number of sources
            x.get('lastfm_similarity', 0),  # Tertiary: Last.fm weight
            x.get('deezer_similarity', 0)  # Quaternary: Deezer weight
        ), reverse=True)
        
        return filtered[:limit]
    
    def _smart_merge_artist_sources(self, similarities: List[Dict]) -> Dict:
        """Smart merging that preserves the best features from each source."""
        # Use the highest scoring entry as base
        base_entry = max(similarities, key=lambda x: x['match']).copy()
        
        # Enhance with multi-source metadata
        sources = [s['source'] for s in similarities]
        base_entry['sources'] = sources
        base_entry['source_count'] = len(sources)
        
        # Combine similarity scores intelligently
        lastfm_score = max((s.get('lastfm_similarity', 0) for s in similarities), default=0)
        deezer_score = max((s.get('deezer_similarity', 0) for s in similarities), default=0)
        
        base_entry['lastfm_similarity'] = lastfm_score
        base_entry['deezer_similarity'] = deezer_score
        
        # Create combined score (weighted average favoring Last.fm)
        if lastfm_score > 0 and deezer_score > 0:
            combined_score = (lastfm_score * 0.6) + (deezer_score * 0.4)
            base_entry['match'] = max(base_entry['match'], combined_score)
            base_entry['source'] = 'multi_source'
            base_entry['relationship_type'] = 'multi_source_confirmed'
        
        # Mark special combinations
        if 'manual' in sources and ('lastfm' in sources or 'deezer' in sources):
            base_entry['relationship_type'] = 'manual_api_confirmed'
        
        return base_entry

def test_ultimate_similarity_system():
    """Test the ultimate similarity system with challenging cases."""
    print("🌟 Testing Ultimate Similarity System")
    print("=" * 50)
    
    try:
        config = AppConfig("configurations.txt")
        ultimate_system = UltimateSimilaritySystem(config)
        
        # Test the most challenging cases
        test_cases = [
            ("ANYUJIN", "Should find IVE via manual"),
            ("IVE", "Should find K-pop connections via Deezer + manual"),
            ("TWICE", "Should find comprehensive connections"),
            ("Paramore", "Should find rock connections"),
            ("NewJeans", "Should leverage Deezer's K-pop coverage")
        ]
        
        for artist_name, expected in test_cases:
            print(f"\n🎯 Testing '{artist_name}' ({expected}):")
            
            results = ultimate_system.get_ultimate_similar_artists(
                artist_name,
                limit=10,
                min_threshold=0.1
            )
            
            if results:
                print(f"   ✅ Found {len(results)} total similarities:")
                
                # Show top results
                for i, similar in enumerate(results[:6], 1):
                    source_icon = {
                        'lastfm': '🎶',
                        'deezer': '🎵',
                        'manual': '✋',
                        'multi_source': '🌟'
                    }.get(similar['source'], '❓')
                    
                    print(f"      {i}. {similar['name']} ({similar['match']:.3f}, {source_icon} {similar['source']})")
            else:
                print("   ❌ No similarities found")
            
            time.sleep(0.3)  # Rate limiting
    
    except Exception as e:
        print(f"❌ Ultimate test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ultimate_similarity_system()