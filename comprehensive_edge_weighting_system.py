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
        try:
            if source_name == 'musicbrainz':
                return self._create_musicbrainz_contribution(data)
            elif source_name in ['lastfm', 'deezer', 'lastfm_bidirectional']:
                # Handle bidirectional lastfm as regular lastfm
                normalized_source = 'lastfm' if 'lastfm' in source_name else source_name
                return self._create_algorithmic_contribution(normalized_source, data)
            elif source_name == 'manual':
                return self._create_manual_contribution(data)
            elif source_name == 'multi_source':
                # Multi-source is already a fusion result, treat as high-confidence algorithmic
                return self._create_multi_source_contribution(data)
            else:
                logger.warning(f"Unknown source: {source_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating contribution from {source_name}: {e}")
            return None
    
    def _create_musicbrainz_contribution(self, data: Dict) -> Optional[EdgeContribution]:
        """Create contribution from MusicBrainz relationship data."""
        relationship_type = data.get('musicbrainz_relationship', '').lower()
        
        if relationship_type not in self.config.musicbrainz_relationships:
            # Handle unknown relationship types with fallback scoring
            if 'member' in relationship_type or 'band' in relationship_type:
                similarity = 0.9
                distance = 2.0
            elif 'collab' in relationship_type:
                similarity = 0.8
                distance = 3.0
            else:
                similarity = 0.5
                distance = 10.0
            
            is_factual = True
        else:
            rel_config = self.config.musicbrainz_relationships[relationship_type]
            similarity = rel_config['similarity']
            distance = rel_config['distance']
            is_factual = rel_config['is_factual']
        
        return EdgeContribution(
            source='musicbrainz',
            relationship_type=f'musicbrainz_{relationship_type.replace(" ", "_")}',
            raw_value=similarity,
            normalized_similarity=similarity,
            normalized_distance=distance,
            is_factual=is_factual,
            confidence=self.config.source_reliability['musicbrainz']
        )
    
    def _create_algorithmic_contribution(self, source_name: str, data: Dict) -> Optional[EdgeContribution]:
        """Create contribution from algorithmic similarity data (Last.fm/Deezer)."""
        raw_similarity = data.get('match', 0.0)
        
        # Apply power scaling to emphasize high similarities
        power_factor = self.config.similarity_scaling['power_factor']
        scaled_similarity = math.pow(raw_similarity, power_factor)
        
        # Convert similarity to distance (non-linear)
        distance_constant = self.config.similarity_scaling['distance_constant']
        distance = distance_constant / (scaled_similarity + 0.01)
        
        # Confidence based on source reliability and similarity strength
        base_confidence = self.config.source_reliability[source_name]
        similarity_confidence = scaled_similarity  # Higher similarity = higher confidence
        confidence = (base_confidence + similarity_confidence) / 2.0
        
        return EdgeContribution(
            source=source_name,
            relationship_type=f'{source_name}_similarity',
            raw_value=raw_similarity,
            normalized_similarity=scaled_similarity,
            normalized_distance=distance,
            is_factual=False,
            confidence=confidence
        )
    
    def _create_manual_contribution(self, data: Dict) -> Optional[EdgeContribution]:
        """Create contribution from manual connection data."""
        similarity = data.get('match', 1.0)
        
        return EdgeContribution(
            source='manual',
            relationship_type=data.get('relationship_type', 'manual_connection'),
            raw_value=similarity,
            normalized_similarity=similarity,
            normalized_distance=1.0,  # Manual connections are "close"
            is_factual=True,
            confidence=self.config.source_reliability['manual']
        )
    
    def _create_multi_source_contribution(self, data: Dict) -> Optional[EdgeContribution]:
        """Create contribution from pre-fused multi-source data."""
        similarity = data.get('match', 0.0)
        
        # Multi-source entries have already been through fusion, so treat with high confidence
        return EdgeContribution(
            source='multi_source',
            relationship_type=data.get('relationship_type', 'multi_source_fusion'),
            raw_value=similarity,
            normalized_similarity=similarity,
            normalized_distance=2.0,  # Multi-source connections are reliable
            is_factual=False,  # Still algorithmic, just high-confidence
            confidence=0.95  # Very high confidence for multi-source agreements
        )
    
    def _fuse_contributions(self, contributions: List[EdgeContribution]) -> Dict:
        """Fuse multiple contributions into final edge attributes."""
        # Separate factual vs algorithmic contributions
        factual_contributions = [c for c in contributions if c.is_factual]
        algorithmic_contributions = [c for c in contributions if not c.is_factual]
        
        # Primary similarity calculation
        if factual_contributions:
            # If any factual relationships exist, use the strongest one as base
            primary_similarity = max(c.normalized_similarity for c in factual_contributions)
            fusion_method = 'factual_primary'
        else:
            # Pure algorithmic - use weighted average
            weighted_sum = sum(c.normalized_similarity * c.confidence for c in algorithmic_contributions)
            weight_sum = sum(c.confidence for c in algorithmic_contributions)
            primary_similarity = weighted_sum / weight_sum if weight_sum > 0 else 0.0
            fusion_method = 'algorithmic_weighted'
        
        # Apply factual boost if both types present
        if factual_contributions and algorithmic_contributions:
            factual_boost = self.config.fusion_config['factual_boost']
            primary_similarity = min(1.0, primary_similarity * factual_boost)
            fusion_method = 'hybrid_boosted'
        
        # Multi-source agreement bonus
        unique_sources = set(c.source for c in contributions)
        if len(unique_sources) > 1:
            agreement_bonus = self.config.fusion_config['agreement_bonus']
            primary_similarity = min(1.0, primary_similarity + agreement_bonus)
            fusion_method += '_multi_source'
        
        # Distance calculation (use minimum distance from any source)
        primary_distance = min(c.normalized_distance for c in contributions)
        
        # Confidence calculation
        avg_confidence = sum(c.confidence for c in contributions) / len(contributions)
        
        # Penalize high variance between sources (indicates conflict)
        similarities = [c.normalized_similarity for c in contributions]
        if len(similarities) > 1:
            variance = sum((s - primary_similarity) ** 2 for s in similarities) / len(similarities)
            conflict_penalty = self.config.fusion_config['conflict_penalty'] * variance
            avg_confidence = max(0.0, avg_confidence - conflict_penalty)
        
        return {
            'similarity': min(1.0, max(0.0, primary_similarity)),
            'distance': max(0.5, primary_distance),
            'confidence': min(1.0, max(0.0, avg_confidence)),
            'is_factual': len(factual_contributions) > 0,
            'fusion_method': fusion_method
        }
    
    def create_network_edges(self, all_similarities: Dict[str, Dict[str, List[Dict]]]) -> List[WeightedEdge]:
        """Create all weighted edges for the network.
        
        Args:
            all_similarities: Nested dict of artist -> target_artist -> [source_data]
                            
        Returns:
            List of WeightedEdge objects
        """
        edges = []
        
        for source_artist, targets in all_similarities.items():
            for target_artist, source_data_list in targets.items():
                if source_artist == target_artist:
                    continue  # Skip self-connections
                
                # Group source data by source name
                grouped_data = {}
                for source_data in source_data_list:
                    source_name = source_data.get('source', 'unknown')
                    if source_name not in grouped_data:
                        grouped_data[source_name] = []
                    grouped_data[source_name].append(source_data)
                
                # Create weighted edge
                edge = self.create_weighted_edge(source_artist, target_artist, grouped_data)
                if edge:
                    edges.append(edge)
        
        logger.info(f"Created {len(edges)} weighted edges")
        
        # Log fusion method statistics
        fusion_stats = {}
        for edge in edges:
            method = edge.fusion_method
            if method not in fusion_stats:
                fusion_stats[method] = 0
            fusion_stats[method] += 1
        
        logger.info(f"Fusion method breakdown: {fusion_stats}")
        
        return edges

def test_edge_weighting_system():
    """Test the comprehensive edge weighting system."""
    print("🧪 Testing Comprehensive Edge Weighting System")
    print("=" * 55)
    
    # Create test configuration
    config = EdgeWeightingConfig()
    weighter = ComprehensiveEdgeWeighter(config)
    
    # Test case 1: Multi-source agreement (should get high weight)
    print("\n1️⃣ Testing Multi-Source Agreement")
    print("-" * 35)
    
    source_data = {
        'lastfm': [{'match': 0.8, 'source': 'lastfm'}],
        'deezer': [{'match': 0.75, 'source': 'deezer'}],
        'musicbrainz': [{
            'musicbrainz_relationship': 'collaboration',
            'source': 'musicbrainz'
        }]
    }
    
    edge = weighter.create_weighted_edge("Artist A", "Artist B", source_data)
    if edge:
        print(f"Multi-source edge:")
        print(f"   Similarity: {edge.similarity:.3f}")
        print(f"   Distance: {edge.distance:.1f}")
        print(f"   Confidence: {edge.confidence:.3f}")
        print(f"   Is factual: {edge.is_factual}")
        print(f"   Fusion method: {edge.fusion_method}")
        print(f"   Sources: {[c.source for c in edge.contributions]}")
    
    # Test case 2: Factual relationship (should get very high weight)
    print("\n2️⃣ Testing Factual Relationship")
    print("-" * 32)
    
    source_data = {
        'musicbrainz': [{
            'musicbrainz_relationship': 'member of band',
            'source': 'musicbrainz'
        }]
    }
    
    edge = weighter.create_weighted_edge("John Lennon", "The Beatles", source_data)
    if edge:
        print(f"Factual edge:")
        print(f"   Similarity: {edge.similarity:.3f}")
        print(f"   Distance: {edge.distance:.1f}")
        print(f"   Confidence: {edge.confidence:.3f}")
        print(f"   Is factual: {edge.is_factual}")
    
    # Test case 3: Low algorithmic similarity (should be filtered or low weight)
    print("\n3️⃣ Testing Low Algorithmic Similarity")
    print("-" * 37)
    
    source_data = {
        'lastfm': [{'match': 0.15, 'source': 'lastfm'}]
    }
    
    edge = weighter.create_weighted_edge("Artist X", "Artist Y", source_data)
    if edge:
        print(f"Low similarity edge:")
        print(f"   Similarity: {edge.similarity:.3f}")
        print(f"   Confidence: {edge.confidence:.3f}")
    else:
        print("   ✅ Edge filtered out (below confidence threshold)")
    
    # Test case 4: D3.js format conversion
    print("\n4️⃣ Testing D3.js Format Conversion")
    print("-" * 34)
    
    if edge:
        d3_format = edge.to_d3_format()
        print(f"D3.js format:")
        for key, value in d3_format.items():
            print(f"   {key}: {value}")

if __name__ == "__main__":
    test_edge_weighting_system()