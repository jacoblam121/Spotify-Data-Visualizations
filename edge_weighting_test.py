#!/usr/bin/env python3
"""
Edge Weighting Test (Clean Version)
===================================
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
    source: str              
    relationship_type: str   
    raw_value: float        
    normalized_similarity: float  
    normalized_distance: float    
    is_factual: bool        
    confidence: float       

@dataclass  
class WeightedEdge:
    """Comprehensive edge with multiple attributes for network analysis."""
    source_artist: str
    target_artist: str
    similarity: float       
    distance: float        
    confidence: float      
    is_factual: bool       
    contributions: List[EdgeContribution]
    fusion_method: str     
    
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
            'musicbrainz': 0.95,  
            'lastfm': 0.85,       
            'deezer': 0.80,       
            'manual': 0.90        
        }
        
        # MusicBrainz relationship type mappings
        self.musicbrainz_relationships = {
            'member of band': {
                'similarity': 0.95,
                'distance': 1.0,
                'is_factual': True,
                'description': 'Band member'
            },
            'collaboration': {
                'similarity': 0.85,
                'distance': 2.0,
                'is_factual': True,
                'description': 'Direct collaboration'
            }
        }
        
        # Fusion parameters
        self.fusion_config = {
            'factual_boost': 1.1,       
            'agreement_bonus': 0.1,     
            'min_confidence': 0.3       
        }

class ComprehensiveEdgeWeighter:
    """Advanced edge weighting system for multi-source artist networks."""
    
    def __init__(self, config: EdgeWeightingConfig = None):
        self.config = config or EdgeWeightingConfig()
        
        logger.info("Comprehensive Edge Weighting System initialized")
    
    def create_weighted_edge(self, source_artist: str, target_artist: str,
                           source_data: Dict[str, List[Dict]]) -> Optional[WeightedEdge]:
        """Create a weighted edge from multiple source data."""
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
            elif source_name in ['lastfm', 'deezer']:
                return self._create_algorithmic_contribution(source_name, data)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error creating contribution from {source_name}: {e}")
            return None
    
    def _create_musicbrainz_contribution(self, data: Dict) -> Optional[EdgeContribution]:
        """Create contribution from MusicBrainz relationship data."""
        relationship_type = data.get('musicbrainz_relationship', '').lower()
        
        if relationship_type in self.config.musicbrainz_relationships:
            rel_config = self.config.musicbrainz_relationships[relationship_type]
            similarity = rel_config['similarity']
            distance = rel_config['distance']
            is_factual = rel_config['is_factual']
        else:
            # Fallback for unknown types
            similarity = 0.5
            distance = 10.0
            is_factual = True
        
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
        """Create contribution from algorithmic similarity data."""
        raw_similarity = data.get('match', 0.0)
        
        # Apply power scaling
        scaled_similarity = math.pow(raw_similarity, 1.5)
        
        # Convert similarity to distance
        distance = 20.0 / (scaled_similarity + 0.01)
        
        # Calculate confidence
        base_confidence = self.config.source_reliability[source_name]
        confidence = (base_confidence + scaled_similarity) / 2.0
        
        return EdgeContribution(
            source=source_name,
            relationship_type=f'{source_name}_similarity',
            raw_value=raw_similarity,
            normalized_similarity=scaled_similarity,
            normalized_distance=distance,
            is_factual=False,
            confidence=confidence
        )
    
    def _fuse_contributions(self, contributions: List[EdgeContribution]) -> Dict:
        """Fuse multiple contributions into final edge attributes."""
        # Separate factual vs algorithmic contributions
        factual_contributions = [c for c in contributions if c.is_factual]
        algorithmic_contributions = [c for c in contributions if not c.is_factual]
        
        # Primary similarity calculation
        if factual_contributions:
            primary_similarity = max(c.normalized_similarity for c in factual_contributions)
            fusion_method = 'factual_primary'
        else:
            weighted_sum = sum(c.normalized_similarity * c.confidence for c in algorithmic_contributions)
            weight_sum = sum(c.confidence for c in algorithmic_contributions)
            primary_similarity = weighted_sum / weight_sum if weight_sum > 0 else 0.0
            fusion_method = 'algorithmic_weighted'
        
        # Apply factual boost if both types present
        if factual_contributions and algorithmic_contributions:
            primary_similarity = min(1.0, primary_similarity * self.config.fusion_config['factual_boost'])
            fusion_method = 'hybrid_boosted'
        
        # Multi-source agreement bonus
        unique_sources = set(c.source for c in contributions)
        if len(unique_sources) > 1:
            primary_similarity = min(1.0, primary_similarity + self.config.fusion_config['agreement_bonus'])
            fusion_method += '_multi_source'
        
        # Distance calculation
        primary_distance = min(c.normalized_distance for c in contributions)
        
        # Confidence calculation
        avg_confidence = sum(c.confidence for c in contributions) / len(contributions)
        
        return {
            'similarity': min(1.0, max(0.0, primary_similarity)),
            'distance': max(0.5, primary_distance),
            'confidence': min(1.0, max(0.0, avg_confidence)),
            'is_factual': len(factual_contributions) > 0,
            'fusion_method': fusion_method
        }

def test_edge_weighting_system():
    """Test the comprehensive edge weighting system."""
    print("🧪 Testing Comprehensive Edge Weighting System")
    print("=" * 55)
    
    # Create test configuration
    config = EdgeWeightingConfig()
    weighter = ComprehensiveEdgeWeighter(config)
    
    # Test case 1: Multi-source agreement
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
    
    # Test case 2: Factual relationship
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
    
    # Test case 3: D3.js format conversion
    print("\n3️⃣ Testing D3.js Format Conversion")
    print("-" * 34)
    
    if edge:
        d3_format = edge.to_d3_format()
        print(f"D3.js format:")
        for key, value in d3_format.items():
            print(f"   {key}: {value}")

if __name__ == "__main__":
    test_edge_weighting_system()