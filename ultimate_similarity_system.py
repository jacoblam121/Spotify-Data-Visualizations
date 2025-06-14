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
            bidirectional_similarities = self._get_bidirectional_similarities(\n                artist_name, all_similarities, min_threshold\n            )\n            all_similarities.extend(bidirectional_similarities)\n            source_counts['bidirectional'] = len(bidirectional_similarities)\n            logger.info(f\"   🔄 Bidirectional: {len(bidirectional_similarities)} reverse connections\")\n        \n        # Source 5: Smart merging, deduplication, and scoring\n        final_similarities = self._ultimate_merge_and_score(\n            all_similarities, limit, min_threshold\n        )\n        \n        # Log final statistics\n        multi_source_count = sum(1 for s in final_similarities if s.get('source_count', 1) > 1)\n        logger.info(f\"✅ Ultimate search result: {len(final_similarities)} total similarities\")\n        logger.info(f\"   Sources: {', '.join(f'{k}={v}' for k, v in source_counts.items())}\")\n        logger.info(f\"   Multi-source agreements: {multi_source_count}\")\n        \n        return final_similarities\n    \n    def _get_lastfm_similarities(self, artist_name: str, limit: int, min_threshold: float) -> List[Dict]:\n        \"\"\"Get Last.fm similarities using ORIGINAL names (not canonical).\"\"\"\n        try:\n            # KEY: Use original name, disable enhanced matching to prevent canonical resolution issues\n            similarities = self.lastfm_api.get_similar_artists(\n                artist_name=artist_name,\n                limit=limit,\n                use_enhanced_matching=False  # This fixes the canonical name mismatch issue\n            )\n            \n            # Filter and add metadata\n            filtered = []\n            for similar in similarities:\n                if similar['match'] >= min_threshold:\n                    similar.update({\n                        'source': 'lastfm',\n                        'lastfm_similarity': similar['match'],\n                        'deezer_similarity': 0.0,\n                        'manual_connection': False,\n                        'bidirectional_source': False,\n                        'relationship_type': 'lastfm_similar'\n                    })\n                    filtered.append(similar)\n            \n            return filtered\n            \n        except Exception as e:\n            logger.error(f\"Error getting Last.fm similarities for '{artist_name}': {e}\")\n            return []\n    \n    def _get_deezer_similarities(self, artist_name: str, limit: int, min_threshold: float) -> List[Dict]:\n        \"\"\"Get Deezer similarities (especially good for K-pop coverage).\"\"\"\n        try:\n            similarities = self.deezer_api.get_similar_artists(artist_name, limit)\n            \n            # Filter by threshold and add metadata\n            filtered = []\n            for similar in similarities:\n                if similar['match'] >= min_threshold:\n                    similar.update({\n                        'deezer_similarity': similar['match'],\n                        'lastfm_similarity': 0.0,\n                        'manual_connection': False,\n                        'bidirectional_source': False\n                    })\n                    filtered.append(similar)\n            \n            return filtered\n            \n        except Exception as e:\n            logger.error(f\"Error getting Deezer similarities for '{artist_name}': {e}\")\n            return []\n    \n    def _get_manual_similarities(self, artist_name: str, min_threshold: float) -> List[Dict]:\n        \"\"\"Get manual connections for obvious relationships.\"\"\"\n        manual_connections = get_manual_connections(artist_name)\n        \n        similarities = []\n        for target_name, similarity_score, relationship_type in manual_connections:\n            if similarity_score >= min_threshold:\n                similarities.append({\n                    'name': target_name,\n                    'match': similarity_score,\n                    'source': 'manual',\n                    'lastfm_similarity': 0.0,\n                    'deezer_similarity': 0.0,\n                    'manual_connection': True,\n                    'bidirectional_source': False,\n                    'relationship_type': f'manual_{relationship_type}'\n                })\n        \n        return similarities\n    \n    def _get_bidirectional_similarities(self, original_artist: str, existing_similarities: List[Dict],\n                                       min_threshold: float) -> List[Dict]:\n        \"\"\"Enhanced bidirectional checking using both Last.fm and Deezer.\"\"\"\n        if not self.lastfm_api:\n            return []\n        \n        existing_names = {s['name'].lower() for s in existing_similarities}\n        candidate_artists = self._get_enhanced_reverse_candidates(original_artist, existing_similarities)\n        \n        reverse_connections = []\n        \n        for candidate in candidate_artists:\n            if candidate.lower() in existing_names:\n                continue\n            \n            try:\n                # Check Last.fm reverse connection\n                lastfm_similarities = self.lastfm_api.get_similar_artists(\n                    artist_name=candidate,\n                    limit=50,\n                    use_enhanced_matching=False\n                )\n                \n                for similar in lastfm_similarities:\n                    if self._names_match(similar['name'], original_artist):\n                        if similar['match'] >= min_threshold:\n                            reverse_connections.append({\n                                'name': candidate,\n                                'match': similar['match'],\n                                'source': 'lastfm_bidirectional',\n                                'lastfm_similarity': similar['match'],\n                                'deezer_similarity': 0.0,\n                                'manual_connection': False,\n                                'bidirectional_source': True,\n                                'relationship_type': 'lastfm_reverse_discovered'\n                            })\n                            logger.debug(f\"🔄 Found reverse: {candidate} → {original_artist} ({similar['match']:.3f})\")\n                            break\n                \n                time.sleep(0.1)  # Rate limiting\n                \n            except Exception as e:\n                logger.debug(f\"Error checking reverse connection from {candidate}: {e}\")\n                continue\n        \n        return reverse_connections\n    \n    def _get_enhanced_reverse_candidates(self, artist_name: str, existing_similarities: List[Dict]) -> List[str]:\n        \"\"\"Get enhanced candidate artists for reverse checking.\"\"\"\n        candidates = set()\n        \n        # Add manual connection targets\n        manual_connections = get_manual_connections(artist_name)\n        for target_name, _, _ in manual_connections:\n            candidates.add(target_name)\n        \n        # Add some existing similarities as reverse candidates\n        for similar in existing_similarities[:10]:  # Top 10 most similar\n            candidates.add(similar['name'])\n        \n        # Add genre-based candidates\n        artist_lower = artist_name.lower()\n        \n        # Enhanced K-pop coverage\n        kpop_groups = [\n            'IU', 'TWICE', 'BLACKPINK', 'BTS', 'IVE', 'NewJeans', 'aespa', 'ITZY',\n            'LE SSERAFIM', 'NMIXX', 'KISS OF LIFE', 'Red Velvet', 'EVERGLOW', 'LOONA'\n        ]\n        \n        if any(group.lower() in artist_lower for group in kpop_groups):\n            candidates.update(kpop_groups)\n        \n        # Rock/Pop-punk candidates\n        rock_artists = [\n            'Paramore', 'Fall Out Boy', 'My Chemical Romance', 'Tonight Alive',\n            'Hayley Williams', 'Panic! At the Disco', 'Simple Plan', 'All Time Low'\n        ]\n        \n        if any(artist.lower() in artist_lower for artist in rock_artists):\n            candidates.update(rock_artists)\n        \n        # Remove self\n        candidates.discard(artist_name)\n        \n        return list(candidates)[:15]  # Limit to avoid too many API calls\n    \n    def _ultimate_merge_and_score(self, all_similarities: List[Dict], limit: int,\n                                min_threshold: float) -> List[Dict]:\n        \"\"\"Ultimate merging algorithm that handles multiple sources optimally.\"\"\"\n        # Group by artist name (case-insensitive, fuzzy matching)\n        artist_groups = {}\n        \n        for similarity in all_similarities:\n            artist_key = self._normalize_artist_name(similarity['name'])\n            if artist_key not in artist_groups:\n                artist_groups[artist_key] = []\n            artist_groups[artist_key].append(similarity)\n        \n        # Merge multiple sources for each artist\n        merged_similarities = []\n        for artist_key, similarities in artist_groups.items():\n            if len(similarities) == 1:\n                merged_similarities.append(similarities[0])\n            else:\n                # Multiple sources - smart merge\n                merged = self._smart_merge_artist_sources(similarities)\n                merged_similarities.append(merged)\n        \n        # Filter by threshold\n        filtered = [s for s in merged_similarities if s['match'] >= min_threshold]\n        \n        # Advanced scoring: boost multi-source agreements\n        for similarity in filtered:\n            source_count = similarity.get('source_count', 1)\n            if source_count > 1:\n                # Multi-source boost: 10% per additional source\n                boost_factor = 1.0 + (0.1 * (source_count - 1))\n                similarity['match'] = min(1.0, similarity['match'] * boost_factor)\n                similarity['multi_source_boost'] = True\n        \n        # Sort by enhanced similarity score\n        filtered.sort(key=lambda x: (\n            x['match'],  # Primary: similarity score\n            x.get('source_count', 1),  # Secondary: number of sources\n            x.get('lastfm_similarity', 0),  # Tertiary: Last.fm weight\n            x.get('deezer_similarity', 0)  # Quaternary: Deezer weight\n        ), reverse=True)\n        \n        return filtered[:limit]\n    \n    def _smart_merge_artist_sources(self, similarities: List[Dict]) -> Dict:\n        \"\"\"Smart merging that preserves the best features from each source.\"\"\"\n        # Categorize by source\n        by_source = {}\n        for sim in similarities:\n            source = sim['source']\n            if source not in by_source:\n                by_source[source] = []\n            by_source[source].append(sim)\n        \n        # Use the highest scoring entry as base\n        base_entry = max(similarities, key=lambda x: x['match']).copy()\n        \n        # Enhance with multi-source metadata\n        sources = list(by_source.keys())\n        base_entry['sources'] = sources\n        base_entry['source_count'] = len(sources)\n        \n        # Combine similarity scores intelligently\n        lastfm_score = max((s.get('lastfm_similarity', 0) for s in similarities), default=0)\n        deezer_score = max((s.get('deezer_similarity', 0) for s in similarities), default=0)\n        \n        base_entry['lastfm_similarity'] = lastfm_score\n        base_entry['deezer_similarity'] = deezer_score\n        \n        # Create combined score (weighted average favoring Last.fm)\n        if lastfm_score > 0 and deezer_score > 0:\n            combined_score = (lastfm_score * 0.6) + (deezer_score * 0.4)\n            base_entry['match'] = max(base_entry['match'], combined_score)\n            base_entry['source'] = 'multi_source'\n            base_entry['relationship_type'] = 'multi_source_confirmed'\n        \n        # Mark special combinations\n        if 'manual' in sources and ('lastfm' in sources or 'deezer' in sources):\n            base_entry['relationship_type'] = 'manual_api_confirmed'\n        \n        return base_entry\n    \n    def _normalize_artist_name(self, name: str) -> str:\n        \"\"\"Normalize artist names for better matching.\"\"\"\n        # Basic normalization\n        normalized = name.lower().strip()\n        \n        # Handle common K-pop variants\n        kpop_variants = {\n            'iu': 'iu',\n            '아이유': 'iu',\n            'twice': 'twice',\n            '트와이스': 'twice',\n            'ive': 'ive',\n            '아이브': 'ive',\n            'blackpink': 'blackpink',\n            '블랙핑크': 'blackpink'\n        }\n        \n        for variant, canonical in kpop_variants.items():\n            if variant in normalized:\n                return canonical\n        \n        return normalized\n    \n    def _names_match(self, name1: str, name2: str) -> bool:\n        \"\"\"Enhanced name matching for similarity detection.\"\"\"\n        norm1 = self._normalize_artist_name(name1)\n        norm2 = self._normalize_artist_name(name2)\n        \n        # Direct match\n        if norm1 == norm2:\n            return True\n        \n        # Contains match\n        if norm1 in norm2 or norm2 in norm1:\n            return True\n        \n        return False\n\ndef test_ultimate_similarity_system():\n    \"\"\"Test the ultimate similarity system with all our problematic cases.\"\"\"\n    print(\"🌟 Testing Ultimate Similarity System\")\n    print(\"=\" * 50)\n    \n    try:\n        config = AppConfig(\"configurations.txt\")\n        ultimate_system = UltimateSimilaritySystem(config)\n        \n        # Test the most challenging cases\n        test_cases = [\n            (\"ANYUJIN\", \"Should find IVE via manual + potentially Deezer\"),\n            (\"IVE\", \"Should find multiple K-pop connections via Deezer + manual\"),\n            (\"TWICE\", \"Should find comprehensive connections from all sources\"),\n            (\"Paramore\", \"Should find rock connections via Last.fm + Deezer\"),\n            (\"NewJeans\", \"Should leverage Deezer's strong K-pop coverage\")\n        ]\n        \n        for artist_name, expected in test_cases:\n            print(f\"\\n🎯 Testing '{artist_name}' ({expected}):\")\n            \n            results = ultimate_system.get_ultimate_similar_artists(\n                artist_name,\n                limit=12,\n                min_threshold=0.1\n            )\n            \n            if results:\n                print(f\"   ✅ Found {len(results)} total similarities:\")\n                \n                # Group by source for analysis\n                source_counts = {}\n                for result in results:\n                    sources = result.get('sources', [result['source']])\n                    for source in sources:\n                        source_counts[source] = source_counts.get(source, 0) + 1\n                \n                print(f\"   📊 Source breakdown: {', '.join(f'{k}={v}' for k, v in source_counts.items())}\")\n                \n                # Show top results\n                for i, similar in enumerate(results[:6], 1):\n                    source_display = similar['source']\n                    if similar.get('source_count', 1) > 1:\n                        source_display = f\"multi({similar['source_count']})\"\n                    \n                    source_icon = {\n                        'lastfm': '🎶',\n                        'deezer': '🎵',\n                        'manual': '✋',\n                        'lastfm_bidirectional': '🔄',\n                        'multi_source': '🌟'\n                    }.get(similar['source'], '❓')\n                    \n                    print(f\"      {i}. {similar['name']} ({similar['match']:.3f}, {source_icon} {source_display})\")\n                    \n                    # Show relationship type for interesting cases\n                    if similar.get('multi_source_boost') or similar.get('source_count', 1) > 1:\n                        print(f\"         └ {similar['relationship_type']}\")\n            else:\n                print(\"   ❌ No similarities found\")\n            \n            time.sleep(0.5)  # Rate limiting\n    \n    except Exception as e:\n        print(f\"❌ Ultimate test error: {e}\")\n        import traceback\n        traceback.print_exc()\n\nif __name__ == \"__main__\":\n    test_ultimate_similarity_system()