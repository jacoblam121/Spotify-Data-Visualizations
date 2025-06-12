"""
Robust Artist Resolution System
==============================

A cascade-based entity resolution system that handles artist matching 
from messy user data to canonical identities. Replaces the bandaid 
approach of hardcoded patterns with a systematic, confidence-scored pipeline.

Architecture:
1. Exact Match (confidence: 1.0)
2. Curated Aliases (confidence: 0.99) 
3. Fuzzy Algorithmic (confidence: 0.85-0.95)
4. Human Review Queue (< 0.85)
"""

import re
import json
import os
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import logging

try:
    from rapidfuzz import fuzz
except ImportError:
    # Fallback to difflib if rapidfuzz not available
    import difflib
    fuzz = None

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Structured result from artist resolution."""
    artist_name: str
    confidence: float
    method: str
    original_query: str
    metadata: Dict = None


class ArtistResolver:
    """
    Robust artist resolution using a cascade of matching strategies.
    
    This replaces the manual pattern database approach with a systematic
    pipeline that gracefully degrades from high-confidence to low-confidence
    matching methods.
    """
    
    def __init__(self, aliases_file: str = "artist_aliases.json", 
                 review_queue_file: str = "artist_review_queue.csv"):
        """
        Initialize the resolver.
        
        Args:
            aliases_file: JSON file containing curated artist aliases
            review_queue_file: CSV file for low-confidence matches to review
        """
        self.aliases_file = aliases_file
        self.review_queue_file = review_queue_file
        self.aliases = self._load_aliases()
        
        # Collaboration patterns for preprocessing
        self.collab_patterns = re.compile(
            r'\s*(?:\((?:with|feat\.?|featuring)\s+([^)]+)\)|'  # (with artist)
            r'(?:feat\.?|ft\.?|featuring|with|&|vs\.?|and)\s+)',  # feat. artist
            re.IGNORECASE
        )
    
    def _load_aliases(self) -> Dict[str, str]:
        """Load curated artist aliases from file."""
        if os.path.exists(self.aliases_file):
            try:
                with open(self.aliases_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load aliases: {e}")
        return {}
    
    def _save_aliases(self):
        """Save aliases back to file."""
        try:
            with open(self.aliases_file, 'w', encoding='utf-8') as f:
                json.dump(self.aliases, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save aliases: {e}")
    
    def _normalize_name(self, name: str) -> str:
        """Normalize artist name for comparison."""
        if not name:
            return ""
        
        # Unicode-aware normalization
        normalized = name.casefold().strip()
        
        # Remove common punctuation but keep meaningful characters
        normalized = re.sub(r'[^\w\s\-&]', '', normalized)
        
        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def split_collaborations(self, artist_string: str) -> List[str]:
        """
        Split collaboration strings into individual artists.
        
        Handles patterns like:
        - "BoyWithUke (with blackbear)"
        - "Taylor Swift feat. Ed Sheeran"
        - "Artist A & Artist B"
        
        Returns:
            List of individual artist names
        """
        if not artist_string:
            return []
        
        artists = []
        
        # Extract parenthetical collaborations first
        paren_matches = re.findall(r'\((?:with|feat\.?|featuring)\s+([^)]+)\)', 
                                   artist_string, re.IGNORECASE)
        
        # Remove parenthetical parts from main string
        main_string = re.sub(r'\s*\((?:with|feat\.?|featuring)[^)]*\)', 
                           '', artist_string, flags=re.IGNORECASE)
        
        # Split main string by collaboration keywords
        parts = re.split(r'\s+(?:feat\.?|ft\.?|featuring|with|&|vs\.?|and)\s+', 
                        main_string, flags=re.IGNORECASE)
        
        # Add main artists
        for part in parts:
            clean_part = part.strip()
            if clean_part:
                artists.append(clean_part)
        
        # Add parenthetical collaborators
        for match in paren_matches:
            # Split in case there are multiple artists in parentheses
            sub_artists = [a.strip() for a in match.split(',') if a.strip()]
            artists.extend(sub_artists)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_artists = []
        for artist in artists:
            normalized = self._normalize_name(artist)
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_artists.append(artist)
        
        return unique_artists
    
    def resolve_artist(self, lastfm_artist: str, 
                      candidate_pool: List[str] = None) -> Optional[MatchResult]:
        """
        Resolve a Last.fm artist name to a canonical artist.
        
        Uses a cascade of matching strategies:
        1. Exact match
        2. Curated aliases  
        3. Fuzzy algorithmic matching
        
        Args:
            lastfm_artist: Raw artist name from Last.fm
            candidate_pool: List of known artists to match against
            
        Returns:
            MatchResult if match found above confidence threshold, None otherwise
        """
        if not lastfm_artist or not lastfm_artist.strip():
            return None
        
        original_query = lastfm_artist.strip()
        normalized_query = self._normalize_name(original_query)
        
        # Stage 1: Exact Match (highest confidence)
        if candidate_pool:
            for candidate in candidate_pool:
                if self._normalize_name(candidate) == normalized_query:
                    return MatchResult(
                        artist_name=candidate,
                        confidence=1.0,
                        method="exact_match",
                        original_query=original_query
                    )
        
        # Stage 2: Curated Aliases (high confidence)
        if normalized_query in self.aliases:
            canonical_name = self.aliases[normalized_query]
            return MatchResult(
                artist_name=canonical_name,
                confidence=0.99,
                method="curated_alias",
                original_query=original_query
            )
        
        # Stage 3: Fuzzy Algorithmic Matching
        if candidate_pool:
            best_match = self._fuzzy_match(original_query, candidate_pool)
            if best_match:
                return best_match
        
        # No match found
        self._add_to_review_queue(original_query, candidate_pool)
        return None
    
    def _fuzzy_match(self, query: str, candidates: List[str], 
                    min_confidence: float = 0.85) -> Optional[MatchResult]:
        """
        Perform fuzzy matching against candidate pool.
        
        Uses rapidfuzz for performance, falls back to difflib if not available.
        """
        if not candidates:
            return None
        
        best_candidate = None
        best_score = 0.0
        
        normalized_query = self._normalize_name(query)
        
        for candidate in candidates:
            normalized_candidate = self._normalize_name(candidate)
            
            if fuzz:
                # Use rapidfuzz token_set_ratio for robust matching
                score = fuzz.token_set_ratio(normalized_query, normalized_candidate) / 100.0
            else:
                # Fallback to difflib
                score = difflib.SequenceMatcher(None, normalized_query, normalized_candidate).ratio()
            
            if score > best_score:
                best_score = score
                best_candidate = candidate
        
        if best_score >= min_confidence:
            return MatchResult(
                artist_name=best_candidate,
                confidence=best_score,
                method="fuzzy_algorithmic",
                original_query=query,
                metadata={"algorithm": "rapidfuzz" if fuzz else "difflib"}
            )
        
        return None
    
    def _add_to_review_queue(self, query: str, candidates: List[str] = None):
        """Add failed matches to human review queue."""
        # Implementation would write to CSV for human review
        logger.debug(f"Added to review queue: '{query}'")
    
    def add_curated_alias(self, lastfm_name: str, canonical_name: str):
        """
        Add a manually verified alias mapping.
        
        This is how the system becomes self-improving based on human feedback.
        """
        normalized_key = self._normalize_name(lastfm_name)
        self.aliases[normalized_key] = canonical_name
        self._save_aliases()
        logger.info(f"Added alias: '{lastfm_name}' -> '{canonical_name}'")
    
    def get_statistics(self) -> Dict:
        """Get resolver statistics for monitoring."""
        return {
            "curated_aliases_count": len(self.aliases),
            "review_queue_exists": os.path.exists(self.review_queue_file)
        }


def migrate_known_patterns_to_aliases(known_patterns: Dict, output_file: str = "artist_aliases.json"):
    """
    Migrate the old known_patterns database to the new aliases format.
    
    This preserves the existing manual curation work while moving to 
    the new architecture.
    """
    aliases = {}
    
    for main_name, variants in known_patterns.items():
        # Normalize all patterns
        resolver = ArtistResolver()
        main_normalized = resolver._normalize_name(main_name)
        
        # The main name maps to itself
        aliases[main_normalized] = main_name
        
        # Each variant maps to the main name
        for variant in variants:
            variant_normalized = resolver._normalize_name(variant)
            if variant_normalized and variant_normalized != main_normalized:
                aliases[variant_normalized] = main_name
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(aliases, f, ensure_ascii=False, indent=2)
    
    print(f"Migrated {len(aliases)} aliases to {output_file}")
    return aliases


# Example usage and testing
if __name__ == "__main__":
    # Test the new system
    resolver = ArtistResolver()
    
    test_cases = [
        "BoyWithUke (with blackbear)",
        "Taylor Swift feat. Ed Sheeran",
        "ユイカ",
        "blackbear",
    ]
    
    # Mock candidate pool (in real usage, this would come from your music library)
    candidates = ["BoyWithUke", "blackbear", "Taylor Swift", "Ed Sheeran", "YUIKA"]
    
    print("Testing Artist Resolver:")
    print("=" * 50)
    
    for test in test_cases:
        # Test collaboration splitting
        split_result = resolver.split_collaborations(test)
        print(f"\nSplitting: '{test}' -> {split_result}")
        
        # Test resolution for each split artist
        for artist in split_result:
            result = resolver.resolve_artist(artist, candidates)
            if result:
                print(f"  Resolved: '{artist}' -> '{result.artist_name}' "
                      f"(confidence: {result.confidence:.3f}, method: {result.method})")
            else:
                print(f"  No match: '{artist}'")