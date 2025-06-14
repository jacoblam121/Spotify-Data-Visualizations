#!/usr/bin/env python3
"""
Fixed Edge Weighting System
===========================
Fixes the issues where all similarities are 1.0 and sources are duplicated.
"""

import logging
import math
from typing import Dict, List, Optional
from dataclasses import dataclass

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

class FixedEdgeWeighter:
    """Fixed edge weighting system that preserves actual similarity scores."""
    
    def __init__(self):
        # Source reliability weights (systematic sources only)
        self.source_weights = {
            'lastfm': 1.0,        # Primary source gets full weight
            'deezer': 0.8,        # Secondary source
            'musicbrainz': 0.9    # Factual relationships
        }
        
        # MusicBrainz relationship mappings
        self.mb_relationships = {
            'member of band': 0.95,
            'collaboration': 0.85,
            'similar': 0.7,
            'unknown': 0.5
        }
        
        logger.info("Fixed Edge Weighting System initialized")
    
    def create_weighted_edge(self, source_artist: str, target_artist: str,
                           source_data: Dict[str, List[Dict]]) -> Optional[WeightedEdge]:
        """Create a weighted edge with FIXED similarity scoring."""
        
        # Check if target artist exists in any source
        target_found = False
        contributions = []
        
        for source_name, data_list in source_data.items():
            if not data_list:
                continue
                
            # Find the target artist in this source's data
            for data_item in data_list:
                if data_item.get('name', '').lower() == target_artist.lower():
                    target_found = True
                    contribution = self._create_contribution(source_name, data_item)
                    if contribution:
                        contributions.append(contribution)
                    break  # Only take first match per source
        
        if not target_found or not contributions:
            return None
        
        # Calculate final edge attributes
        edge_attrs = self._calculate_edge_attributes(contributions)
        
        return WeightedEdge(
            source_artist=source_artist,
            target_artist=target_artist,
            similarity=edge_attrs['similarity'],
            distance=edge_attrs['distance'],
            confidence=edge_attrs['confidence'],
            is_factual=edge_attrs['is_factual'],
            contributions=contributions,
            fusion_method=edge_attrs['fusion_method']
        )
    
    def _create_contribution(self, source_name: str, data: Dict) -> Optional[EdgeContribution]:
        """Create a single contribution from source data."""
        
        if source_name == 'musicbrainz':
            # MusicBrainz factual relationships
            rel_type = data.get('musicbrainz_relationship', 'unknown').lower()
            similarity = self.mb_relationships.get(rel_type, 0.5)
            
            return EdgeContribution(
                source='musicbrainz',
                relationship_type=rel_type,
                raw_value=similarity,
                normalized_similarity=similarity,
                normalized_distance=1.0 / similarity if similarity > 0 else 10.0,
                is_factual=True,
                confidence=0.9
            )
        
        elif source_name in ['lastfm', 'deezer']:
            # Algorithmic similarity scores
            raw_score = data.get('match', 0.0)
            
            # Keep the original similarity score (don't boost to 1.0!)
            normalized_score = raw_score  # Use actual API score
            
            return EdgeContribution(
                source=source_name,
                relationship_type=f'{source_name}_similarity',
                raw_value=raw_score,
                normalized_similarity=normalized_score,
                normalized_distance=1.0 / max(normalized_score, 0.01),
                is_factual=False,
                confidence=self.source_weights[source_name]
            )
        
        # Note: No manual connections - all systematic/data-driven
        
        return None
    
    def _calculate_edge_attributes(self, contributions: List[EdgeContribution]) -> Dict:
        """Calculate final edge attributes from contributions."""
        
        # Separate by type
        factual_contribs = [c for c in contributions if c.is_factual]
        algorithmic_contribs = [c for c in contributions if not c.is_factual]
        
        # Determine primary similarity score
        if factual_contribs:
            # For factual relationships, use the highest factual score
            primary_similarity = max(c.normalized_similarity for c in factual_contribs)
            fusion_method = 'factual_primary'
            is_factual = True
        else:
            # For algorithmic only, use weighted average
            if algorithmic_contribs:
                weighted_sum = sum(c.normalized_similarity * c.confidence for c in algorithmic_contribs)
                weight_sum = sum(c.confidence for c in algorithmic_contribs)
                primary_similarity = weighted_sum / weight_sum if weight_sum > 0 else 0.0
                fusion_method = 'algorithmic_weighted'
                is_factual = False
            else:
                return {'similarity': 0.0, 'distance': 100.0, 'confidence': 0.0, 
                       'is_factual': False, 'fusion_method': 'no_data'}
        
        # If we have both factual and algorithmic, blend them but DON'T boost to 1.0
        if factual_contribs and algorithmic_contribs:
            # Weight factual slightly higher but don't destroy the actual scores
            factual_weight = 0.6
            algo_weight = 0.4
            
            factual_score = max(c.normalized_similarity for c in factual_contribs)
            algo_score = sum(c.normalized_similarity * c.confidence for c in algorithmic_contribs) / sum(c.confidence for c in algorithmic_contribs)
            
            primary_similarity = (factual_score * factual_weight + algo_score * algo_weight)
            fusion_method = 'hybrid_weighted'
            is_factual = True
        
        # Add small multi-source bonus (not huge boost to 1.0)
        unique_sources = set(c.source for c in contributions)
        if len(unique_sources) > 1:
            primary_similarity = min(1.0, primary_similarity + 0.05)  # Small 5% bonus
            fusion_method += '_multi_source'
        
        # Calculate distance and confidence
        distance = min(c.normalized_distance for c in contributions)
        confidence = sum(c.confidence for c in contributions) / len(contributions)
        
        return {
            'similarity': min(1.0, max(0.0, primary_similarity)),
            'distance': max(0.5, distance),
            'confidence': min(1.0, max(0.0, confidence)),
            'is_factual': is_factual,
            'fusion_method': fusion_method
        }

def test_fixed_weighting():
    """Test the fixed edge weighting system."""
    print("🧪 Testing Fixed Edge Weighting System")
    print("=" * 42)
    
    weighter = FixedEdgeWeighter()
    
    # Test 1: Last.fm only (should preserve actual score)
    print("\n1️⃣ Last.fm only (should preserve score):")
    source_data = {
        'lastfm': [{'name': 'Ed Sheeran', 'match': 0.7}]
    }
    edge = weighter.create_weighted_edge('Taylor Swift', 'Ed Sheeran', source_data)
    if edge:
        print(f"   Similarity: {edge.similarity:.3f} (should be ~0.7)")
        print(f"   Sources: {[c.source for c in edge.contributions]}")
    
    # Test 2: MusicBrainz only (factual relationship)
    print("\n2️⃣ MusicBrainz only (factual):")
    source_data = {
        'musicbrainz': [{'name': 'IVE', 'musicbrainz_relationship': 'member of band'}]
    }
    edge = weighter.create_weighted_edge('ANYUJIN', 'IVE', source_data)
    if edge:
        print(f"   Similarity: {edge.similarity:.3f} (should be 0.95)")
        print(f"   Factual: {edge.is_factual}")
        print(f"   Sources: {[c.source for c in edge.contributions]}")
    
    # Test 3: Multi-source (should blend, not boost to 1.0)
    print("\n3️⃣ Multi-source (should blend properly):")
    source_data = {
        'lastfm': [{'name': 'Harry Styles', 'match': 0.6}],
        'deezer': [{'name': 'Harry Styles', 'match': 0.8}]
    }
    edge = weighter.create_weighted_edge('Taylor Swift', 'Harry Styles', source_data)
    if edge:
        print(f"   Similarity: {edge.similarity:.3f} (should be ~0.6-0.8, not 1.0)")
        print(f"   Fusion method: {edge.fusion_method}")
        print(f"   Sources: {[c.source for c in edge.contributions]}")

if __name__ == "__main__":
    test_fixed_weighting()