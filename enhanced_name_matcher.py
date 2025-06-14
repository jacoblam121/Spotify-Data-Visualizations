#!/usr/bin/env python3
"""
Enhanced Name Matcher for Cross-Cultural Artist Matching
========================================================
Focused solution for K-pop/J-pop artist name variants and group-member relationships.
This implements a targeted approach to solve the ANYUJIN-IVE connection issue.
"""

import json
import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ArtistMapping:
    """Represents an artist with all known name variants and relationships."""
    canonical_name: str
    aliases: Set[str]
    group_memberships: Set[str]  # Groups this artist is a member of
    members: Set[str]  # If this is a group, list of members
    confidence: float = 1.0

class EnhancedNameMatcher:
    """
    Enhanced name matching system that handles:
    1. Cross-script matching (Korean ↔ English)
    2. Group-member relationships  
    3. Platform-specific variants
    4. Fuzzy matching for typos/variations
    """
    
    def __init__(self):
        """Initialize with curated artist mappings."""
        self.artist_mappings: Dict[str, ArtistMapping] = {}
        self.alias_to_canonical: Dict[str, str] = {}
        
        # Load curated mappings
        self._load_kpop_mappings()
        self._load_jpop_mappings()
        
        logger.info(f"Enhanced name matcher initialized with {len(self.artist_mappings)} mappings")
    
    def _load_kpop_mappings(self):
        """Load curated K-pop artist mappings."""
        
        # IVE and members
        ive_mapping = ArtistMapping(
            canonical_name="IVE",
            aliases={
                "ive", "아이브", "ive (아이브)", "ive 아이브", 
                "i*ve", "아이브 (ive)", "ive (girl group)"
            },
            group_memberships=set(),
            members={
                "anyujin", "안유진", "ahn yujin", "ahn yu-jin",
                "jang wonyoung", "장원영", "wonyoung",
                "rei", "레이", "naoi rei",
                "gaeul", "가을", 
                "liz", "리즈",
                "leeseo", "이서"
            }
        )
        self._add_mapping(ive_mapping)
        
        # ANYUJIN (IVE member)
        anyujin_mapping = ArtistMapping(
            canonical_name="ANYUJIN",
            aliases={
                "anyujin", "안유진", "ahn yujin", "ahn yu-jin", "ahn yu jin",
                "안유진 (ive)", "anyujin (ive)", "yujin", "유진",
                "an yujin", "anyujin ive"
            },
            group_memberships={"IVE"},
            members=set()
        )
        self._add_mapping(anyujin_mapping)
        
        # IZ*ONE connections (for ANYUJIN's Last.fm matches)
        izone_mapping = ArtistMapping(
            canonical_name="IZ*ONE",
            aliases={
                "iz*one", "izone", "아이즈원", "iz*one 아이즈원",
                "izone アイズワン", "iz*one (아이즈원)"
            },
            group_memberships=set(),
            members={
                "안유진", "장원영", "조유리", "최예나", "김채원", 
                "권은비", "이채연", "조유리", "야마구치 나코", "혼다 히토미",
                "강혜원", "김민주"
            }
        )
        self._add_mapping(izone_mapping)
        
        # Additional common K-pop groups that might appear in similarity data
        common_groups = [
            # TWICE
            ArtistMapping(
                canonical_name="TWICE",
                aliases={"twice", "트와이스", "twice 트와이스"},
                group_memberships=set(),
                members={"nayeon", "jeongyeon", "momo", "sana", "jihyo", "mina", "dahyun", "chaeyoung", "tzuyu"}
            ),
            # ITZY  
            ArtistMapping(
                canonical_name="ITZY",
                aliases={"itzy", "있지", "itzy 있지"},
                group_memberships=set(),
                members={"yeji", "lia", "ryujin", "chaeryeong", "yuna"}
            ),
            # (G)I-DLE
            ArtistMapping(
                canonical_name="(G)I-DLE",
                aliases={"(g)i-dle", "gidle", "여자아이들", "(여자)아이들", "girl idle"},
                group_memberships=set(),
                members={"soyeon", "miyeon", "minnie", "shuhua", "yuqi"}
            )
        ]
        
        for mapping in common_groups:
            self._add_mapping(mapping)
    
    def _load_jpop_mappings(self):
        """Load curated J-pop artist mappings (placeholder for future expansion)."""
        # Future: Add mappings for J-pop artists like ヨルシカ, YOASOBI, etc.
        pass
    
    def _add_mapping(self, mapping: ArtistMapping):
        """Add an artist mapping and update lookup indices."""
        canonical_lower = mapping.canonical_name.lower()
        self.artist_mappings[canonical_lower] = mapping
        
        # Index all aliases
        for alias in mapping.aliases:
            alias_lower = alias.lower()
            self.alias_to_canonical[alias_lower] = canonical_lower
        
        # Also index the canonical name itself
        self.alias_to_canonical[canonical_lower] = canonical_lower
    
    def find_canonical_name(self, artist_name: str) -> Optional[str]:
        """
        Find the canonical name for an artist, handling variants and relationships.
        
        Args:
            artist_name: Raw artist name from any source
            
        Returns:
            Canonical name if found, None otherwise
        """
        if not artist_name:
            return None
        
        # Normalize input
        normalized = self._normalize_name(artist_name)
        
        # Special case for (G)I-DLE variants
        if '(g)i-dle' in normalized or 'gidle' in normalized:
            return "(G)I-DLE"
        
        # Direct lookup
        if normalized in self.alias_to_canonical:
            canonical = self.alias_to_canonical[normalized]
            return self.artist_mappings[canonical].canonical_name
        
        # Fuzzy matching for typos/variations
        best_match = self._fuzzy_match(normalized)
        if best_match:
            return best_match
        
        return None
    
    def find_related_artists(self, artist_name: str, target_artists: Set[str]) -> List[Tuple[str, str, float]]:
        """
        Find artists related to the given artist through group memberships.
        
        Args:
            artist_name: Source artist name
            target_artists: Set of available target artists (from user's dataset)
            
        Returns:
            List of (related_artist, relationship_type, strength) tuples
        """
        canonical = self.find_canonical_name(artist_name)
        if not canonical:
            return []
        
        canonical_lower = canonical.lower()
        if canonical_lower not in self.artist_mappings:
            return []
        
        mapping = self.artist_mappings[canonical_lower]
        related = []
        
        # Check group memberships (individual → group)
        for group in mapping.group_memberships:
            group_canonical = self.find_canonical_name(group)
            if group_canonical and group_canonical.lower() in {t.lower() for t in target_artists}:
                related.append((group_canonical, "member_of", 0.9))
        
        # Check members (group → individuals)  
        for member in mapping.members:
            member_canonical = self.find_canonical_name(member)
            if member_canonical and member_canonical.lower() in {t.lower() for t in target_artists}:
                related.append((member_canonical, "has_member", 0.8))
        
        return related
    
    def _normalize_name(self, name: str) -> str:
        """Normalize artist name for matching."""
        if not name:
            return ""
        
        # Basic normalization
        normalized = name.lower().strip()
        
        # Remove common prefixes/suffixes
        normalized = re.sub(r'\s*\(.*?\)\s*', '', normalized)  # Remove parentheses
        normalized = re.sub(r'\s*feat\.?\s+.*', '', normalized)  # Remove features
        normalized = re.sub(r'\s+', ' ', normalized)  # Normalize whitespace
        
        return normalized.strip()
    
    def _fuzzy_match(self, normalized_name: str, threshold: float = 0.85) -> Optional[str]:
        """Perform fuzzy matching against known aliases."""
        try:
            from rapidfuzz import fuzz, process
        except ImportError:
            # Fallback to simple contains matching
            return self._simple_fuzzy_match(normalized_name)
        
        # Use rapidfuzz for high-performance fuzzy matching
        matches = process.extract(
            normalized_name, 
            list(self.alias_to_canonical.keys()),
            scorer=fuzz.ratio,
            limit=3
        )
        
        for match, score, _ in matches:
            if score >= threshold * 100:  # rapidfuzz uses 0-100 scale
                canonical = self.alias_to_canonical[match]
                return self.artist_mappings[canonical].canonical_name
        
        return None
    
    def _simple_fuzzy_match(self, normalized_name: str) -> Optional[str]:
        """Simple fallback fuzzy matching."""
        # Check if the name is contained in any alias
        for alias, canonical in self.alias_to_canonical.items():
            if normalized_name in alias or alias in normalized_name:
                if len(normalized_name) > 2 and len(alias) > 2:  # Avoid matching very short strings
                    return self.artist_mappings[canonical].canonical_name
        
        return None
    
    def enhance_similarity_matching(self, source_artist: str, similarity_results: List[Dict], 
                                  target_artists: Set[str]) -> List[Dict]:
        """
        Enhance similarity results by adding relationship-based connections.
        
        Args:
            source_artist: Source artist name
            similarity_results: Original similarity results from APIs
            target_artists: Available target artists from user's dataset
            
        Returns:
            Enhanced similarity results with relationship-based matches
        """
        enhanced_results = list(similarity_results)  # Copy original results
        
        # Find direct relationships
        related = self.find_related_artists(source_artist, target_artists)
        
        for related_artist, relationship_type, strength in related:
            # Find the exact case-sensitive name from target_artists
            target_name = self._find_exact_target_name(related_artist, target_artists)
            if target_name:
                # Add relationship-based similarity
                enhanced_results.append({
                    'name': target_name,
                    'similarity': strength,
                    'source': 'relationship',
                    'relationship_type': relationship_type,
                    '_enhanced_match': True
                })
        
        # Also check if any similarity results can be canonicalized to target artists
        for result in similarity_results:
            result_canonical = self.find_canonical_name(result['name'])
            if result_canonical:
                target_name = self._find_exact_target_name(result_canonical, target_artists)
                if target_name:
                    # This similarity result maps to a target artist
                    enhanced_results.append({
                        'name': target_name,
                        'similarity': result.get('similarity', 0.5),
                        'source': result.get('source', 'unknown'),
                        '_canonical_match': result['name'],
                        '_enhanced_match': True
                    })
        
        return enhanced_results
    
    def _find_exact_target_name(self, canonical_name: str, target_artists: Set[str]) -> Optional[str]:
        """Find the exact case-sensitive name for a canonical artist in the target set."""
        canonical_lower = canonical_name.lower()
        
        for target in target_artists:
            if target.lower() == canonical_lower:
                return target
        
        return None

def test_enhanced_matching():
    """Test the enhanced name matching system."""
    matcher = EnhancedNameMatcher()
    
    test_cases = [
        ("ANYUJIN", "ANYUJIN"),
        ("안유진", "ANYUJIN"), 
        ("ahn yujin", "ANYUJIN"),
        ("IVE", "IVE"),
        ("아이브", "IVE"),
        ("ive (아이브)", "IVE"),
        ("twice", "TWICE"),
        ("(g)i-dle", "(G)I-DLE")
    ]
    
    print("🧪 Testing Enhanced Name Matching")
    print("=" * 40)
    
    for input_name, expected in test_cases:
        result = matcher.find_canonical_name(input_name)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_name}' -> '{result}' (expected: '{expected}')")
    
    # Test relationships
    print(f"\n🔗 Testing Relationship Matching")
    target_artists = {"IVE", "TWICE", "ANYUJIN"}
    
    anyujin_related = matcher.find_related_artists("ANYUJIN", target_artists)
    print(f"ANYUJIN related: {anyujin_related}")
    
    ive_related = matcher.find_related_artists("IVE", target_artists)  
    print(f"IVE related: {ive_related}")

if __name__ == "__main__":
    test_enhanced_matching()