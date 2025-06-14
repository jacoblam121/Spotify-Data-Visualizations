#!/usr/bin/env python3
"""
Test Original Name Fix
======================
Test if using original names (not canonical) fixes bidirectional connections.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_similarity_search import EnhancedSimilaritySearcher
from lastfm_utils import LastfmAPI
from config_loader import AppConfig

def test_bidirectional_connections():
    """Test if original name approach fixes bidirectional connections."""
    print("🔄 Testing Bidirectional Connections with Original Names")
    print("=" * 60)
    
    config = AppConfig("configurations.txt")
    searcher = EnhancedSimilaritySearcher(config)
    lastfm_api = searcher.lastfm_api
    
    # Critical test cases
    test_cases = [
        ("TWICE", "IU"),
        ("IU", "TWICE"),
        ("Paramore", "Tonight Alive"),
        ("Tonight Alive", "Paramore")
    ]
    
    for artist_a, artist_b in test_cases:
        print(f"\n🎯 Testing: {artist_a} → {artist_b}")
        
        # Test with ORIGINAL names (our new approach)
        print("   📍 Using ORIGINAL name search...")
        original_results = lastfm_api.get_similar_artists(
            artist_name=artist_a,
            limit=50,
            use_enhanced_matching=False  # Disable canonical resolution
        )
        
        found_original = False
        similarity_original = 0.0
        
        for similar in original_results:
            if similar['name'].lower() == artist_b.lower() or artist_b.lower() in similar['name'].lower():
                found_original = True
                similarity_original = similar['match']
                break
        
        # Test with CANONICAL names (old approach)
        print("   🎯 Using CANONICAL name search...")
        canonical_results = lastfm_api.get_similar_artists(
            artist_name=artist_a,
            limit=50,
            use_enhanced_matching=True  # Enable canonical resolution
        )
        
        found_canonical = False
        similarity_canonical = 0.0
        canonical_variant = "unknown"
        
        for similar in canonical_results:
            if similar['name'].lower() == artist_b.lower() or artist_b.lower() in similar['name'].lower():
                found_canonical = True
                similarity_canonical = similar['match']
                canonical_variant = similar.get('_matched_variant', 'unknown')
                break
        
        # Compare results
        print(f"   📊 ORIGINAL name approach: {similarity_original:.3f} {'✅' if found_original else '❌'}")
        print(f"   📊 CANONICAL name approach: {similarity_canonical:.3f} {'✅' if found_canonical else '❌'}")
        
        if canonical_results and hasattr(canonical_results[0], '_matched_variant'):
            print(f"   🏷️  Canonical variant used: '{canonical_variant}'")
        
        # Analysis
        if found_original and not found_canonical:
            print("   🎉 FIXED! Original name approach found connection that canonical missed!")
        elif found_canonical and not found_original:
            print("   ⚠️  Canonical approach worked better in this case")
        elif found_original and found_canonical:
            if similarity_original != similarity_canonical:
                print(f"   📈 Different similarities: original={similarity_original:.3f}, canonical={similarity_canonical:.3f}")
            else:
                print("   ✅ Both approaches found same connection")
        else:
            print("   ❌ Neither approach found connection - genuinely missing from Last.fm")

if __name__ == "__main__":
    test_bidirectional_connections()