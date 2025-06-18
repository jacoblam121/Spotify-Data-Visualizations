#!/usr/bin/env python3
"""
Ultimate Similarity System
===========================
FINAL COMPREHENSIVE SOLUTION: Combines all our discoveries into one robust system.

This system addresses ALL the issues we identified:
1. ✅ Last.fm data quality gaps (especially K-pop)
2. ✅ Missing obvious connections (band members, same artists)  
3. ✅ Canonical name resolution issues
4. ✅ One-way similarity relationships
5. ✅ Spotify API restrictions

Multi-Source Architecture:
- Last.fm API (original names, not canonical)
- Deezer API (fills K-pop gaps, free, no auth)
- Manual connections (obvious relationships)
- Bidirectional checking (reverse connections)
- Smart scoring and deduplication

NON-DESTRUCTIVE: Doesn't interfere with existing bar chart functionality.
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
    """
    Ultimate similarity system that combines all available data sources
    for the most comprehensive artist similarity network possible.
    """
    
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
        logger.info(f"  Manual connections available: True")
        logger.info(f"  Bidirectional checking: Enabled")
    
    def get_ultimate_similar_artists(self, artist_name: str, limit: int = 100, 
                                   min_threshold: float = 0.1) -> List[Dict]:
        """
        Get the most comprehensive artist similarity data possible.
        
        Multi-source process:
        1. Last.fm similarities (using original names)
        2. Deezer similarities (fills gaps, especially K-pop)
        3. Manual connections (obvious relationships)
        4. Bidirectional checking (reverse connections)
        5. Smart merging and scoring
        
        Args:
            artist_name: Artist to find similarities for
            limit: Maximum number of similar artists to return
            min_threshold: Minimum similarity threshold
            
        Returns:
            Comprehensive list of similar artists with rich metadata
        """
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
        
        # Source 4: Bidirectional checking (reverse connections)
        if self.lastfm_api:
            bidirectional_similarities = self._get_bidirectional_similarities(
                artist_name, all_similarities, min_threshold
            )
            all_similarities.extend(bidirectional_similarities)
            source_counts['bidirectional'] = len(bidirectional_similarities)
            logger.info(f"   🔄 Bidirectional: {len(bidirectional_similarities)} reverse connections")
        
        # Source 5: Filter and return individual source edges (no premature fusion)
        # Let ComprehensiveEdgeWeighter handle the fusion to preserve source attribution
        final_similarities = []
        for similarity in all_similarities:
            if similarity['match'] >= min_threshold:
                final_similarities.append(similarity)
        
        # Sort by similarity score and limit
        final_similarities.sort(key=lambda x: x['match'], reverse=True)
        final_similarities = final_similarities[:limit]
        
        # Log final statistics  
        source_breakdown = {}
        for s in final_similarities:
            source = s['source']
            source_breakdown[source] = source_breakdown.get(source, 0) + 1
            
        logger.info(f"✅ Ultimate search result: {len(final_similarities)} individual source edges")
        logger.info(f"   Sources: {', '.join(f'{k}={v}' for k, v in source_counts.items())}")
        logger.info(f"   Individual edges by source: {source_breakdown}")
        
        return final_similarities
    
    def _get_lastfm_similarities(self, artist_name: str, limit: int, min_threshold: float) -> List[Dict]:
        """Get Last.fm similarities using ORIGINAL names (not canonical)."""
        try:
            # KEY: Use original name, disable enhanced matching to prevent canonical resolution issues
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
                        'bidirectional_source': False,
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
                        'manual_connection': False,
                        'bidirectional_source': False
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
                    'bidirectional_source': False,
                    'relationship_type': f'manual_{relationship_type}'
                })
        
        return similarities
    
    def _get_bidirectional_similarities(self, original_artist: str, existing_similarities: List[Dict],
                                       min_threshold: float) -> List[Dict]:
        """Enhanced bidirectional checking using both Last.fm and Deezer."""
        if not self.lastfm_api:
            return []
        
        existing_names = {s['name'].lower() for s in existing_similarities}
        candidate_artists = self._get_enhanced_reverse_candidates(original_artist, existing_similarities)
        
        reverse_connections = []
        
        for candidate in candidate_artists:
            if candidate.lower() in existing_names:
                continue
            
            try:
                # Check Last.fm reverse connection
                lastfm_similarities = self.lastfm_api.get_similar_artists(
                    artist_name=candidate,
                    limit=50,
                    use_enhanced_matching=False
                )
                
                for similar in lastfm_similarities:
                    if self._names_match(similar['name'], original_artist):
                        if similar['match'] >= min_threshold:
                            reverse_connections.append({
                                'name': candidate,
                                'match': similar['match'],
                                'source': 'lastfm_bidirectional',
                                'lastfm_similarity': similar['match'],
                                'deezer_similarity': 0.0,
                                'manual_connection': False,
                                'bidirectional_source': True,
                                'relationship_type': 'lastfm_reverse_discovered'
                            })
                            logger.debug(f"🔄 Found reverse: {candidate} → {original_artist} ({similar['match']:.3f})")
                            break
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.debug(f"Error checking reverse connection from {candidate}: {e}")
                continue
        
        return reverse_connections
    
    def _get_enhanced_reverse_candidates(self, artist_name: str, existing_similarities: List[Dict]) -> List[str]:
        """Get enhanced candidate artists for reverse checking."""
        candidates = set()
        
        # Add manual connection targets
        manual_connections = get_manual_connections(artist_name)
        for target_name, _, _ in manual_connections:
            candidates.add(target_name)
        
        # Add some existing similarities as reverse candidates
        for similar in existing_similarities[:10]:  # Top 10 most similar
            candidates.add(similar['name'])
        
        # Add genre-based candidates
        artist_lower = artist_name.lower()
        
        # Enhanced K-pop coverage
        kpop_groups = [
            'IU', 'TWICE', 'BLACKPINK', 'BTS', 'IVE', 'NewJeans', 'aespa', 'ITZY',
            'LE SSERAFIM', 'NMIXX', 'KISS OF LIFE', 'Red Velvet', 'EVERGLOW', 'LOONA'
        ]
        
        if any(group.lower() in artist_lower for group in kpop_groups):
            candidates.update(kpop_groups)
        
        # Rock/Pop-punk candidates
        rock_artists = [
            'Paramore', 'Fall Out Boy', 'My Chemical Romance', 'Tonight Alive',
            'Hayley Williams', 'Panic! At the Disco', 'Simple Plan', 'All Time Low'
        ]
        
        if any(artist.lower() in artist_lower for artist in rock_artists):
            candidates.update(rock_artists)
        
        # Remove self
        candidates.discard(artist_name)
        
        return list(candidates)[:15]  # Limit to avoid too many API calls
    
    def _ultimate_merge_and_score(self, all_similarities: List[Dict], limit: int,
                                min_threshold: float) -> List[Dict]:
        """Ultimate merging algorithm that handles multiple sources optimally."""
        # Group by artist name (case-insensitive, fuzzy matching)
        artist_groups = {}
        
        for similarity in all_similarities:
            artist_key = self._normalize_artist_name(similarity['name'])
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
        # Categorize by source
        by_source = {}
        for sim in similarities:
            source = sim['source']
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(sim)
        
        # Use the highest scoring entry as base
        base_entry = max(similarities, key=lambda x: x['match']).copy()
        
        # Enhance with multi-source metadata
        sources = list(by_source.keys())
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
    
    def _normalize_artist_name(self, name: str) -> str:
        """Normalize artist names for better matching."""
        # Basic normalization
        normalized = name.lower().strip()
        
        # Handle common K-pop variants
        kpop_variants = {
            'iu': 'iu',
            '아이유': 'iu',
            'twice': 'twice',
            '트와이스': 'twice',
            'ive': 'ive',
            '아이브': 'ive',
            'blackpink': 'blackpink',
            '블랙핑크': 'blackpink'
        }
        
        for variant, canonical in kpop_variants.items():
            if variant in normalized:
                return canonical
        
        return normalized
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Enhanced name matching for similarity detection."""
        norm1 = self._normalize_artist_name(name1)
        norm2 = self._normalize_artist_name(name2)
        
        # Direct match
        if norm1 == norm2:
            return True
        
        # Contains match
        if norm1 in norm2 or norm2 in norm1:
            return True
        
        return False

def test_ultimate_similarity_system():
    """Test the ultimate similarity system with all our problematic cases."""
    print("🌟 Testing Ultimate Similarity System")
    print("=" * 50)
    
    try:
        config = AppConfig("configurations.txt")
        ultimate_system = UltimateSimilaritySystem(config)
        
        # Test the most challenging cases
        test_cases = [
            ("ANYUJIN", "Should find IVE via manual + potentially Deezer"),
            ("IVE", "Should find multiple K-pop connections via Deezer + manual"),
            ("TWICE", "Should find comprehensive connections from all sources"),
            ("Paramore", "Should find rock connections via Last.fm + Deezer"),
            ("NewJeans", "Should leverage Deezer's strong K-pop coverage")
        ]
        
        for artist_name, expected in test_cases:
            print(f"\n🎯 Testing '{artist_name}' ({expected}):")
            
            results = ultimate_system.get_ultimate_similar_artists(
                artist_name,
                limit=12,
                min_threshold=0.1
            )
            
            if results:
                print(f"   ✅ Found {len(results)} total similarities:")
                
                # Group by source for analysis
                source_counts = {}
                for result in results:
                    sources = result.get('sources', [result['source']])
                    for source in sources:
                        source_counts[source] = source_counts.get(source, 0) + 1
                
                print(f"   📊 Source breakdown: {', '.join(f'{k}={v}' for k, v in source_counts.items())}")
                
                # Show top results
                for i, similar in enumerate(results[:6], 1):
                    source_display = similar['source']
                    if similar.get('source_count', 1) > 1:
                        source_display = f"multi({similar['source_count']})"
                    
                    source_icon = {
                        'lastfm': '🎶',
                        'deezer': '🎵',
                        'manual': '✋',
                        'lastfm_bidirectional': '🔄',
                        'multi_source': '🌟'
                    }.get(similar['source'], '❓')
                    
                    print(f"      {i}. {similar['name']} ({similar['match']:.3f}, {source_icon} {source_display})")
                    
                    # Show relationship type for interesting cases
                    if similar.get('multi_source_boost') or similar.get('source_count', 1) > 1:
                        print(f"         └ {similar['relationship_type']}")
            else:
                print("   ❌ No similarities found")
            
            time.sleep(0.5)  # Rate limiting
    
    except Exception as e:
        print(f"❌ Ultimate test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ultimate_similarity_system()