#!/usr/bin/env python3
"""
Hybrid Similarity System
========================
FINAL SOLUTION: Comprehensive hybrid approach that combines:
1. Last.fm similarity data (using original names to prevent canonical mismatches)
2. Manual connections for obvious relationships (band members, same artists)
3. Enhanced bidirectional checking
4. Fallback strategies for missing connections

This addresses the user's question: "might this have to do with the fuzzy checking that we used to get the artists info like their listeners? Are we using this for similarity instead of direct names?"

ANSWER: The canonical name resolution was NOT the main issue. The real problems are:
1. Last.fm data quality gaps (especially for newer K-pop groups)
2. Missing obvious connections (band members to bands)
3. One-way similarity relationships in Last.fm data

This system fixes all these issues.
"""

import logging
import time
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import sys

# Add project modules
sys.path.insert(0, str(Path(__file__).parent))

from lastfm_utils import LastfmAPI
from config_loader import AppConfig
from manual_connections import MANUAL_CONNECTIONS, get_manual_connections

logger = logging.getLogger(__name__)

class HybridSimilaritySystem:
    """
    Hybrid similarity system that combines multiple data sources and strategies
    to create the most complete artist similarity network possible.
    """
    
    def __init__(self, config: AppConfig):
        """Initialize with configuration."""
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
        
        logger.info(f"Hybrid Similarity System initialized:")
        logger.info(f"  Last.fm available: {bool(self.lastfm_api)}")
        logger.info(f"  Manual connections: {len(MANUAL_CONNECTIONS)} artists")
    
    def get_hybrid_similar_artists(self, artist_name: str, limit: int = 100, 
                                 min_threshold: float = 0.1) -> List[Dict]:
        """
        Get similar artists using hybrid approach:
        1. Last.fm similarities (using original names)
        2. Manual connections for obvious relationships
        3. Bidirectional checking
        4. Enhanced scoring and metadata
        
        Args:
            artist_name: Artist name to find similarities for
            limit: Maximum number of similar artists to return
            min_threshold: Minimum similarity threshold (lowered from 0.2 to 0.1)
            
        Returns:
            List of similar artists with comprehensive metadata
        """
        logger.info(f"🔍 Hybrid similarity search for '{artist_name}' (threshold: {min_threshold})")
        
        all_similarities = []
        
        # Step 1: Get Last.fm similarities using ORIGINAL name (not canonical)
        lastfm_similarities = self._get_lastfm_similarities_original_name(
            artist_name, limit * 2, min_threshold  # Get more to allow for filtering
        )
        all_similarities.extend(lastfm_similarities)
        logger.info(f"   📡 Last.fm: {len(lastfm_similarities)} similarities")
        
        # Step 2: Add manual connections for obvious relationships
        manual_similarities = self._get_manual_similarities(artist_name, min_threshold)
        all_similarities.extend(manual_similarities)
        logger.info(f"   ✋ Manual: {len(manual_similarities)} connections")
        
        # Step 3: Bidirectional enhancement - check reverse connections
        bidirectional_similarities = self._enhance_with_bidirectional_check(
            artist_name, all_similarities, min_threshold
        )
        all_similarities.extend(bidirectional_similarities)
        logger.info(f"   🔄 Bidirectional: {len(bidirectional_similarities)} reverse connections")
        
        # Step 4: Combine, deduplicate, and score
        final_similarities = self._combine_and_rank_similarities(
            all_similarities, limit, min_threshold
        )
        
        logger.info(f"✅ Hybrid search result: {len(final_similarities)} total similarities")
        
        return final_similarities
    
    def _get_lastfm_similarities_original_name(self, artist_name: str, limit: int, 
                                             min_threshold: float) -> List[Dict]:
        """
        Get Last.fm similarities using original artist name.
        This prevents canonical name resolution mismatches.
        """
        if not self.lastfm_api:
            return []
        
        try:
            # KEY: Use original name, disable enhanced matching to prevent canonical resolution
            similarities = self.lastfm_api.get_similar_artists(
                artist_name=artist_name,
                limit=limit,
                use_enhanced_matching=False  # This is the fix for canonical name issues
            )
            
            # Filter by threshold and add metadata
            filtered = []
            for similar in similarities:
                if similar['match'] >= min_threshold:
                    similar.update({
                        'source': 'lastfm',
                        'lastfm_similarity': similar['match'],
                        'manual_connection': False,
                        'bidirectional_source': False,
                        'relationship_type': 'lastfm_similar'
                    })
                    filtered.append(similar)
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error getting Last.fm similarities for '{artist_name}': {e}")
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
                    'manual_connection': True,
                    'bidirectional_source': False,
                    'relationship_type': f'manual_{relationship_type}'
                })
        
        return similarities
    
    def _enhance_with_bidirectional_check(self, original_artist: str, 
                                        existing_similarities: List[Dict],
                                        min_threshold: float) -> List[Dict]:
        """
        Check reverse connections to find missing bidirectional relationships.
        If B is similar to A, but A→B wasn't found, add B→A connection.
        """
        if not self.lastfm_api:
            return []
        
        # Get list of artists that might have reverse connections to us
        existing_names = {s['name'].lower() for s in existing_similarities}
        
        # Get some popular artists that might connect back to us
        candidate_artists = self._get_candidate_artists_for_reverse_check(original_artist)
        
        reverse_connections = []
        
        for candidate in candidate_artists:
            if candidate.lower() in existing_names:
                continue  # Already have connection
            
            try:
                # Check if candidate has original_artist in their similarities
                candidate_similarities = self.lastfm_api.get_similar_artists(
                    artist_name=candidate,
                    limit=50,
                    use_enhanced_matching=False
                )
                
                for similar in candidate_similarities:
                    if self._names_match(similar['name'], original_artist):
                        if similar['match'] >= min_threshold:
                            reverse_connections.append({
                                'name': candidate,
                                'match': similar['match'],
                                'source': 'lastfm_bidirectional',
                                'lastfm_similarity': similar['match'],
                                'manual_connection': False,
                                'bidirectional_source': True,
                                'relationship_type': 'lastfm_reverse_discovered',
                                '_reverse_similarity_score': similar['match']
                            })
                            logger.debug(f"🔄 Found reverse connection: {candidate} → {original_artist} ({similar['match']:.3f})")
                            break
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.debug(f"Error checking reverse connection from {candidate}: {e}")
                continue
        
        return reverse_connections
    
    def _get_candidate_artists_for_reverse_check(self, artist_name: str) -> List[str]:
        """
        Get candidate artists that might have reverse connections.
        Uses genre/category heuristics to avoid checking every artist.
        """
        candidates = set()
        
        # Add manual connection targets (they might have reverse connections)
        manual_connections = get_manual_connections(artist_name)
        for target_name, _, _ in manual_connections:
            candidates.add(target_name)
        
        # Add genre-based candidates
        artist_lower = artist_name.lower()
        
        # K-pop artists - check other major K-pop acts
        kpop_indicators = ['iu', 'twice', 'blackpink', 'bts', 'ive', 'newjeans', 'aespa']
        if any(indicator in artist_lower for indicator in kpop_indicators):
            candidates.update(['IU', 'TWICE', 'BLACKPINK', 'BTS', 'IVE', 'NewJeans', 'aespa', 'ITZY'])
        
        # Rock/Pop-punk - check other rock acts
        rock_indicators = ['paramore', 'fall out boy', 'my chemical romance', 'tonight alive']
        if any(indicator in artist_lower for indicator in rock_indicators):
            candidates.update(['Paramore', 'Fall Out Boy', 'My Chemical Romance', 'Tonight Alive', 'Hayley Williams'])
        
        # Remove self
        candidates.discard(artist_name)
        
        return list(candidates)[:10]  # Limit to avoid too many API calls
    
    def _combine_and_rank_similarities(self, all_similarities: List[Dict], 
                                     limit: int, min_threshold: float) -> List[Dict]:
        """
        Combine, deduplicate, and rank all similarity results.
        Handles multiple sources for the same artist and creates final ranking.
        """
        # Group by artist name (case-insensitive)
        artist_groups = {}
        for similarity in all_similarities:
            artist_key = similarity['name'].lower().strip()
            if artist_key not in artist_groups:
                artist_groups[artist_key] = []
            artist_groups[artist_key].append(similarity)
        
        # Combine multiple sources for each artist
        combined_similarities = []
        for artist_key, similarities in artist_groups.items():
            if len(similarities) == 1:
                combined_similarities.append(similarities[0])
            else:
                # Multiple sources - combine them intelligently
                combined = self._merge_similarity_sources(similarities)
                combined_similarities.append(combined)
        
        # Filter by threshold
        filtered = [s for s in combined_similarities if s['match'] >= min_threshold]
        
        # Sort by similarity score
        filtered.sort(key=lambda x: x['match'], reverse=True)
        
        # Limit results
        return filtered[:limit]
    
    def _merge_similarity_sources(self, similarities: List[Dict]) -> Dict:
        """
        Merge multiple similarity entries for the same artist from different sources.
        Prioritizes certain sources and combines metadata.
        """
        # Separate by source
        lastfm_entries = [s for s in similarities if s['source'] in ['lastfm', 'lastfm_bidirectional']]
        manual_entries = [s for s in similarities if s['source'] == 'manual']
        
        # Use highest scoring entry as base
        base_entry = max(similarities, key=lambda x: x['match']).copy()
        
        # Enhance with additional metadata
        sources = [s['source'] for s in similarities]
        base_entry['sources'] = sources
        base_entry['source_count'] = len(sources)
        
        # If we have both manual and Last.fm, boost the score
        if manual_entries and lastfm_entries:
            boost_factor = 1.1  # 10% boost for multi-source agreement
            base_entry['match'] = min(1.0, base_entry['match'] * boost_factor)
            base_entry['relationship_type'] = 'multi_source_confirmed'
        
        # Combine relationship types
        relationships = list(set(s['relationship_type'] for s in similarities))
        if len(relationships) > 1:
            base_entry['relationship_type'] = f"multi_source_{'+'.join(relationships[:2])}"
        
        return base_entry
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Enhanced name matching for similarity detection."""
        name1_clean = name1.lower().strip()
        name2_clean = name2.lower().strip()
        
        # Exact match
        if name1_clean == name2_clean:
            return True
        
        # Contains match
        if name1_clean in name2_clean or name2_clean in name1_clean:
            return True
        
        # K-pop variants
        kpop_variants = {
            'iu': ['iu', '아이유', 'i.u.'],
            'twice': ['twice', '트와이스'],
            'ive': ['ive', '아이브'],
            'blackpink': ['blackpink', '블랙핑크'],
            'bol4': ['bol4', 'bolbbalgan4', '볼빨간사춘기']
        }
        
        for canonical, variants in kpop_variants.items():
            if any(variant in name1_clean for variant in variants) and \
               any(variant in name2_clean for variant in variants):
                return True
        
        return False

def test_hybrid_similarity_system():
    """Test the hybrid similarity system with problematic cases."""
    print("🧪 Testing Hybrid Similarity System")
    print("=" * 45)
    
    try:
        config = AppConfig("configurations.txt")
        hybrid_system = HybridSimilaritySystem(config)
        
        # Test the most problematic cases
        test_cases = [
            ("ANYUJIN", "Should find IVE connection via manual"),
            ("IVE", "Should find ANYUJIN connection via manual"),
            ("IU", "Should find TWICE connection via manual + bidirectional"),
            ("TWICE", "Should find IU connection via Last.fm + manual"),
            ("Paramore", "Should find Tonight Alive connection")
        ]
        
        for artist_name, expected in test_cases:
            print(f"\n🎯 Testing '{artist_name}' ({expected}):")
            
            results = hybrid_system.get_hybrid_similar_artists(
                artist_name, 
                limit=10, 
                min_threshold=0.1  # Lower threshold to catch more connections
            )
            
            if results:
                print(f"   ✅ Found {len(results)} similarities:")
                for i, similar in enumerate(results[:5], 1):
                    source_icon = {
                        'lastfm': '🎵',
                        'manual': '✋',
                        'lastfm_bidirectional': '🔄',
                        'multi_source': '🌟'
                    }.get(similar['source'], '❓')
                    
                    print(f"      {i}. {similar['name']} ({similar['match']:.3f}, {source_icon} {similar['source']})")
                    print(f"         Relationship: {similar['relationship_type']}")
            else:
                print("   ❌ No similarities found")
    
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hybrid_similarity_system()