#!/usr/bin/env python3
"""
Comprehensive Edge Weighting System
====================================
Advanced edge weighting that fuses multiple data sources into meaningful network weights.

Key Features:
- Multi-source data fusion (Last.fm + Deezer + MusicBrainz)
- Configuration-driven relationship mapping
- Source reliability weighting
- Handles conflicts and validation
- Optimized for network analysis (clustering, layout, pathfinding)

Edge Attributes Generated:
- similarity: 0.0-1.0 (for clustering, layout attraction)
- distance: 1.0-100.0 (for pathfinding, layout spring length)  
- confidence: 0.0-1.0 (based on source agreement)
- is_factual: bool (verified relationships vs algorithmic)
- sources: list (traceability)
"""

import logging
import json
import math
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
import sys
from dataclasses import dataclass

# Add project modules
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import AppConfig

logger = logging.getLogger(__name__)

@dataclass
class EdgeContribution:
    """Represents a single source's contribution to an edge."""
    source: str              # 'lastfm', 'deezer', 'musicbrainz'
    relationship_type: str   # 'similarity', 'member_of_band', etc.
    raw_value: float        # Original score/weight from source
    normalized_similarity: float  # Normalized to 0.0-1.0
    normalized_distance: float    # Distance representation
    is_factual: bool        # Verified relationship vs algorithmic
    confidence: float       # Source-specific confidence

@dataclass  
class WeightedEdge:
    """Comprehensive edge with multiple attributes for network analysis."""
    source_artist: str
    target_artist: str
    
    # Primary attributes for network analysis
    similarity: float       # 0.0-1.0, for clustering/layout attraction
    distance: float        # 1.0-100.0, for pathfinding/spring length
    confidence: float      # 0.0-1.0, overall confidence in connection
    is_factual: bool       # Any factual sources involved
    
    # Metadata
    contributions: List[EdgeContribution]
    fusion_method: str     # How sources were combined
    
    def to_d3_format(self) -> Dict:
        """Convert to D3.js network format."""
        return {
            'source': self.source_artist,
            'target': self.target_artist,
            'weight': self.similarity,
            'distance': self.distance,
            'confidence': self.confidence,
            'is_factual': self.is_factual,
            'sources': [c.source for c in self.contributions],
            'source_count': len(set(c.source for c in self.contributions)),
            'relationship_types': list(set(c.relationship_type for c in self.contributions)),
            'fusion_method': self.fusion_method
        }

class EdgeWeightingConfig:
    """Configuration for edge weighting system."""
    
    def __init__(self):
        # Source reliability weights (0.0-1.0)
        self.source_reliability = {
            'musicbrainz': 0.95,  # Highest - factual data
            'lastfm': 0.85,       # High - real user behavior  
            'deezer': 0.80,       # Good - commercial algorithm
            'manual': 0.90        # High - curated connections
        }
        
        # MusicBrainz relationship type mappings
        self.musicbrainz_relationships = {
            # Band/group relationships (highest weight)
            'member of band': {
                'similarity': 0.95,
                'distance': 1.0,
                'is_factual': True,
                'description': 'Band member'
            },
            'is person': {
                'similarity': 0.98,
                'distance': 0.5,
                'is_factual': True,
                'description': 'Same person (different names)'
            },
            'performance name': {
                'similarity': 0.95,
                'distance': 0.8,
                'is_factual': True,
                'description': 'Performance alias'
            },
            
            # Collaboration relationships (high weight)
            'collaboration': {
                'similarity': 0.85,
                'distance': 2.0,
                'is_factual': True,
                'description': 'Direct collaboration'
            },
            'supporting musician': {
                'similarity': 0.70,
                'distance': 3.0,
                'is_factual': True,
                'description': 'Supporting musician'
            },
            
            # Influence relationships (medium-high weight)
            'influenced by': {
                'similarity': 0.65,
                'distance': 5.0,
                'is_factual': True,
                'description': 'Musical influence'
            },
            'tribute': {
                'similarity': 0.60,
                'distance': 6.0,
                'is_factual': True,
                'description': 'Tribute act'
            },
            
            # Structural relationships (medium weight)
            'parent': {
                'similarity': 0.55,
                'distance': 7.0,
                'is_factual': True,
                'description': 'Parent/child band'
            },
            'sibling': {
                'similarity': 0.50,
                'distance': 8.0,
                'is_factual': True,
                'description': 'Sibling band'
            },
            
            # Weaker relationships
            'founder': {
                'similarity': 0.45,
                'distance': 10.0,
                'is_factual': True,
                'description': 'Band founder'
            }
        }
        
        # Algorithmic similarity scaling parameters
        self.similarity_scaling = {
            'power_factor': 1.5,        # Emphasize high similarities
            'minimum_threshold': 0.1,   # Drop very weak connections
            'distance_constant': 20.0   # For similarity->distance conversion
        }
        
        # Multi-source fusion parameters
        self.fusion_config = {
            'factual_boost': 1.1,       # Boost when factual sources present
            'agreement_bonus': 0.1,     # Bonus for multi-source agreement
            'conflict_penalty': 0.05,   # Penalty for high source variance
            'min_confidence': 0.3       # Minimum confidence to include edge
        }

class ComprehensiveEdgeWeighter:
    """Advanced edge weighting system for multi-source artist networks."""
    
    def __init__(self, config: EdgeWeightingConfig = None):
        """Initialize edge weighting system."""
        self.config = config or EdgeWeightingConfig()
        
        logger.info("Comprehensive Edge Weighting System initialized:")
        logger.info(f"  Source reliability: {self.config.source_reliability}")
        logger.info(f"  MusicBrainz relationships: {len(self.config.musicbrainz_relationships)}")
        logger.info(f"  Fusion method: Multi-source with confidence scoring")
    
    def create_weighted_edge(self, source_artist: str, target_artist: str,
                           source_data: Dict[str, List[Dict]]) -> Optional[WeightedEdge]:
        """
        Create a weighted edge from multiple source data.
        
        Args:
            source_artist: Source artist name
            target_artist: Target artist name  
            source_data: Dict of source_name -> list of similarity data
                        e.g., {'lastfm': [similarity_dict], 'musicbrainz': [relation_dict]}
                        
        Returns:
            WeightedEdge object or None if below threshold
        """
        # Step 1: Convert all sources to EdgeContribution objects
        contributions = []
        
        for source_name, data_list in source_data.items():
            for data in data_list:
                contribution = self._create_contribution(source_name, data)
                if contribution:
                    contributions.append(contribution)
        
        if not contributions:
            return None
        
        # Step 2: Fuse contributions into final edge attributes
        edge_attributes = self._fuse_contributions(contributions)
        
        # Step 3: Quality check
        if edge_attributes['confidence'] < self.config.fusion_config['min_confidence']:
            logger.debug(f"Edge {source_artist}->{target_artist} below confidence threshold")
            return None
        
        # Step 4: Create final edge
        return WeightedEdge(
            source_artist=source_artist,
            target_artist=target_artist,
            similarity=edge_attributes['similarity'],
            distance=edge_attributes['distance'],
            confidence=edge_attributes['confidence'],
            is_factual=edge_attributes['is_factual'],
            contributions=contributions,
            fusion_method=edge_attributes['fusion_method']
        )
    
    def _create_contribution(self, source_name: str, data: Dict) -> Optional[EdgeContribution]:
        """Convert source data to EdgeContribution."""
        try:\n            if source_name == 'musicbrainz':\n                return self._create_musicbrainz_contribution(data)\n            elif source_name in ['lastfm', 'deezer']:\n                return self._create_algorithmic_contribution(source_name, data)\n            elif source_name == 'manual':\n                return self._create_manual_contribution(data)\n            else:\n                logger.warning(f\"Unknown source: {source_name}\")\n                return None\n                \n        except Exception as e:\n            logger.error(f\"Error creating contribution from {source_name}: {e}\")\n            return None\n    \n    def _create_musicbrainz_contribution(self, data: Dict) -> Optional[EdgeContribution]:\n        \"\"\"Create contribution from MusicBrainz relationship data.\"\"\"\n        relationship_type = data.get('musicbrainz_relationship', '').lower()\n        \n        if relationship_type not in self.config.musicbrainz_relationships:\n            # Handle unknown relationship types with fallback scoring\n            if 'member' in relationship_type or 'band' in relationship_type:\n                similarity = 0.9\n                distance = 2.0\n            elif 'collab' in relationship_type:\n                similarity = 0.8\n                distance = 3.0\n            else:\n                similarity = 0.5\n                distance = 10.0\n            \n            is_factual = True\n        else:\n            rel_config = self.config.musicbrainz_relationships[relationship_type]\n            similarity = rel_config['similarity']\n            distance = rel_config['distance']\n            is_factual = rel_config['is_factual']\n        \n        return EdgeContribution(\n            source='musicbrainz',\n            relationship_type=f'musicbrainz_{relationship_type.replace(\" \", \"_\")}',\n            raw_value=similarity,\n            normalized_similarity=similarity,\n            normalized_distance=distance,\n            is_factual=is_factual,\n            confidence=self.config.source_reliability['musicbrainz']\n        )\n    \n    def _create_algorithmic_contribution(self, source_name: str, data: Dict) -> Optional[EdgeContribution]:\n        \"\"\"Create contribution from algorithmic similarity data (Last.fm/Deezer).\"\"\"\n        raw_similarity = data.get('match', 0.0)\n        \n        # Apply power scaling to emphasize high similarities\n        power_factor = self.config.similarity_scaling['power_factor']\n        scaled_similarity = math.pow(raw_similarity, power_factor)\n        \n        # Convert similarity to distance (non-linear)\n        distance_constant = self.config.similarity_scaling['distance_constant']\n        distance = distance_constant / (scaled_similarity + 0.01)\n        \n        # Confidence based on source reliability and similarity strength\n        base_confidence = self.config.source_reliability[source_name]\n        similarity_confidence = scaled_similarity  # Higher similarity = higher confidence\n        confidence = (base_confidence + similarity_confidence) / 2.0\n        \n        return EdgeContribution(\n            source=source_name,\n            relationship_type=f'{source_name}_similarity',\n            raw_value=raw_similarity,\n            normalized_similarity=scaled_similarity,\n            normalized_distance=distance,\n            is_factual=False,\n            confidence=confidence\n        )\n    \n    def _create_manual_contribution(self, data: Dict) -> Optional[EdgeContribution]:\n        \"\"\"Create contribution from manual connection data.\"\"\"\n        similarity = data.get('match', 1.0)\n        \n        return EdgeContribution(\n            source='manual',\n            relationship_type=data.get('relationship_type', 'manual_connection'),\n            raw_value=similarity,\n            normalized_similarity=similarity,\n            normalized_distance=1.0,  # Manual connections are \"close\"\n            is_factual=True,\n            confidence=self.config.source_reliability['manual']\n        )\n    \n    def _fuse_contributions(self, contributions: List[EdgeContribution]) -> Dict:\n        \"\"\"Fuse multiple contributions into final edge attributes.\"\"\"\n        # Separate factual vs algorithmic contributions\n        factual_contributions = [c for c in contributions if c.is_factual]\n        algorithmic_contributions = [c for c in contributions if not c.is_factual]\n        \n        # Primary similarity calculation\n        if factual_contributions:\n            # If any factual relationships exist, use the strongest one as base\n            primary_similarity = max(c.normalized_similarity for c in factual_contributions)\n            fusion_method = 'factual_primary'\n        else:\n            # Pure algorithmic - use weighted average\n            weighted_sum = sum(c.normalized_similarity * c.confidence for c in algorithmic_contributions)\n            weight_sum = sum(c.confidence for c in algorithmic_contributions)\n            primary_similarity = weighted_sum / weight_sum if weight_sum > 0 else 0.0\n            fusion_method = 'algorithmic_weighted'\n        \n        # Apply factual boost if both types present\n        if factual_contributions and algorithmic_contributions:\n            factual_boost = self.config.fusion_config['factual_boost']\n            primary_similarity = min(1.0, primary_similarity * factual_boost)\n            fusion_method = 'hybrid_boosted'\n        \n        # Multi-source agreement bonus\n        unique_sources = set(c.source for c in contributions)\n        if len(unique_sources) > 1:\n            agreement_bonus = self.config.fusion_config['agreement_bonus']\n            primary_similarity = min(1.0, primary_similarity + agreement_bonus)\n            fusion_method += '_multi_source'\n        \n        # Distance calculation (use minimum distance from any source)\n        primary_distance = min(c.normalized_distance for c in contributions)\n        \n        # Confidence calculation\n        avg_confidence = sum(c.confidence for c in contributions) / len(contributions)\n        \n        # Penalize high variance between sources (indicates conflict)\n        similarities = [c.normalized_similarity for c in contributions]\n        if len(similarities) > 1:\n            variance = sum((s - primary_similarity) ** 2 for s in similarities) / len(similarities)\n            conflict_penalty = self.config.fusion_config['conflict_penalty'] * variance\n            avg_confidence = max(0.0, avg_confidence - conflict_penalty)\n        \n        return {\n            'similarity': min(1.0, max(0.0, primary_similarity)),\n            'distance': max(0.5, primary_distance),\n            'confidence': min(1.0, max(0.0, avg_confidence)),\n            'is_factual': len(factual_contributions) > 0,\n            'fusion_method': fusion_method\n        }\n    \n    def create_network_edges(self, all_similarities: Dict[str, Dict[str, List[Dict]]]) -> List[WeightedEdge]:\n        \"\"\"Create all weighted edges for the network.\n        \n        Args:\n            all_similarities: Nested dict of artist -> target_artist -> [source_data]\n                            \n        Returns:\n            List of WeightedEdge objects\n        \"\"\"\n        edges = []\n        \n        for source_artist, targets in all_similarities.items():\n            for target_artist, source_data_list in targets.items():\n                if source_artist == target_artist:\n                    continue  # Skip self-connections\n                \n                # Group source data by source name\n                grouped_data = {}\n                for source_data in source_data_list:\n                    source_name = source_data.get('source', 'unknown')\n                    if source_name not in grouped_data:\n                        grouped_data[source_name] = []\n                    grouped_data[source_name].append(source_data)\n                \n                # Create weighted edge\n                edge = self.create_weighted_edge(source_artist, target_artist, grouped_data)\n                if edge:\n                    edges.append(edge)\n        \n        logger.info(f\"Created {len(edges)} weighted edges\")\n        \n        # Log fusion method statistics\n        fusion_stats = {}\n        for edge in edges:\n            method = edge.fusion_method\n            if method not in fusion_stats:\n                fusion_stats[method] = 0\n            fusion_stats[method] += 1\n        \n        logger.info(f\"Fusion method breakdown: {fusion_stats}\")\n        \n        return edges\n\ndef test_edge_weighting_system():\n    \"\"\"Test the comprehensive edge weighting system.\"\"\"\n    print(\"🧪 Testing Comprehensive Edge Weighting System\")\n    print(\"=\" * 55)\n    \n    # Create test configuration\n    config = EdgeWeightingConfig()\n    weighter = ComprehensiveEdgeWeighter(config)\n    \n    # Test case 1: Multi-source agreement (should get high weight)\n    print(\"\\n1️⃣ Testing Multi-Source Agreement\")\n    print(\"-\" * 35)\n    \n    source_data = {\n        'lastfm': [{'match': 0.8, 'source': 'lastfm'}],\n        'deezer': [{'match': 0.75, 'source': 'deezer'}],\n        'musicbrainz': [{\n            'musicbrainz_relationship': 'collaboration',\n            'source': 'musicbrainz'\n        }]\n    }\n    \n    edge = weighter.create_weighted_edge(\"Artist A\", \"Artist B\", source_data)\n    if edge:\n        print(f\"Multi-source edge:\")\n        print(f\"   Similarity: {edge.similarity:.3f}\")\n        print(f\"   Distance: {edge.distance:.1f}\")\n        print(f\"   Confidence: {edge.confidence:.3f}\")\n        print(f\"   Is factual: {edge.is_factual}\")\n        print(f\"   Fusion method: {edge.fusion_method}\")\n        print(f\"   Sources: {[c.source for c in edge.contributions]}\")\n    \n    # Test case 2: Factual relationship (should get very high weight)\n    print(\"\\n2️⃣ Testing Factual Relationship\")\n    print(\"-\" * 32)\n    \n    source_data = {\n        'musicbrainz': [{\n            'musicbrainz_relationship': 'member of band',\n            'source': 'musicbrainz'\n        }]\n    }\n    \n    edge = weighter.create_weighted_edge(\"John Lennon\", \"The Beatles\", source_data)\n    if edge:\n        print(f\"Factual edge:\")\n        print(f\"   Similarity: {edge.similarity:.3f}\")\n        print(f\"   Distance: {edge.distance:.1f}\")\n        print(f\"   Confidence: {edge.confidence:.3f}\")\n        print(f\"   Is factual: {edge.is_factual}\")\n    \n    # Test case 3: Low algorithmic similarity (should be filtered or low weight)\n    print(\"\\n3️⃣ Testing Low Algorithmic Similarity\")\n    print(\"-\" * 37)\n    \n    source_data = {\n        'lastfm': [{'match': 0.15, 'source': 'lastfm'}]\n    }\n    \n    edge = weighter.create_weighted_edge(\"Artist X\", \"Artist Y\", source_data)\n    if edge:\n        print(f\"Low similarity edge:\")\n        print(f\"   Similarity: {edge.similarity:.3f}\")\n        print(f\"   Confidence: {edge.confidence:.3f}\")\n    else:\n        print(\"   ✅ Edge filtered out (below confidence threshold)\")\n    \n    # Test case 4: D3.js format conversion\n    print(\"\\n4️⃣ Testing D3.js Format Conversion\")\n    print(\"-\" * 34)\n    \n    if edge:\n        d3_format = edge.to_d3_format()\n        print(f\"D3.js format:\")\n        for key, value in d3_format.items():\n            print(f\"   {key}: {value}\")\n\nif __name__ == \"__main__\":\n    test_edge_weighting_system()