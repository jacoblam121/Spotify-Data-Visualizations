#!/usr/bin/env python3
"""
Quick Similarity System Validation
==================================
Fast validation of the complete multi-source artist similarity system.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from deezer_similarity_api import DeezerSimilarityAPI
from musicbrainz_similarity_api import MusicBrainzSimilarityAPI
from edge_weighting_test import ComprehensiveEdgeWeighter

def quick_validation():
    """Quick validation of key functionality."""
    print("🚀 Quick Multi-Source Similarity System Validation")
    print("=" * 55)
    
    # Initialize APIs
    deezer_api = DeezerSimilarityAPI()
    musicbrainz_api = MusicBrainzSimilarityAPI()
    edge_weighter = ComprehensiveEdgeWeighter()
    
    # Test critical cases from our investigation
    test_artists = [
        "TWICE",      # Should connect to IU via Deezer 
        "IU",         # Should connect to TWICE
        "Paramore",   # Should connect to Tonight Alive
        "ANYUJIN",    # Edge case - should have some connections
        "The Beatles" # Should have rich MusicBrainz data
    ]
    
    print(f"\n🎯 Testing {len(test_artists)} critical artists:")
    
    total_connections = 0
    successful_edges = 0
    
    for artist in test_artists:
        print(f"\n🔍 Testing '{artist}':")
        
        # Test Deezer
        try:
            deezer_results = deezer_api.get_similar_artists(artist, limit=5)
            deezer_count = len(deezer_results)
            print(f"   🎵 Deezer: {deezer_count} connections")
            total_connections += deezer_count
            
            if deezer_results:
                print(f"      Top connections: {', '.join([r['name'] for r in deezer_results[:3]])}")
        except Exception as e:
            print(f"   🎵 Deezer: ERROR - {e}")
            deezer_results = []
        
        # Test MusicBrainz
        try:
            mb_results = musicbrainz_api.get_relationship_based_similar_artists(artist, limit=5)
            mb_count = len(mb_results)
            print(f"   🎭 MusicBrainz: {mb_count} relationships")
            total_connections += mb_count
            
            if mb_results:
                relationships = [f"{r['name']} ({r.get('musicbrainz_relationship', 'unknown')})" 
                               for r in mb_results[:3]]
                print(f"      Top relationships: {', '.join(relationships)}")
        except Exception as e:
            print(f"   🎭 MusicBrainz: ERROR - {e}")
            mb_results = []
        
        # Test edge weighting if we have data
        if deezer_results or mb_results:
            try:
                # Create source data dict
                source_data = {}
                if deezer_results:
                    source_data['deezer'] = deezer_results[:1]  # Test with top result
                if mb_results:
                    source_data['musicbrainz'] = mb_results[:1]
                
                # Test edge creation with top connection
                top_connection = (deezer_results + mb_results)[0]
                target_artist = top_connection['name']
                
                edge = edge_weighter.create_weighted_edge(artist, target_artist, source_data)
                
                if edge:
                    successful_edges += 1
                    print(f"   ⚖️  Edge created: {target_artist}")
                    print(f"      Similarity: {edge.similarity:.3f}, Distance: {edge.distance:.1f}")
                    print(f"      Confidence: {edge.confidence:.3f}, Factual: {edge.is_factual}")
                    print(f"      Fusion: {edge.fusion_method}")
                else:
                    print(f"   ⚖️  Edge creation failed (below threshold)")
                    
            except Exception as e:
                print(f"   ⚖️  Edge weighting ERROR - {e}")
    
    # Summary
    print(f"\n📊 VALIDATION SUMMARY")
    print("=" * 25)
    print(f"🎯 Artists tested: {len(test_artists)}")
    print(f"🔗 Total connections found: {total_connections}")
    print(f"⚖️  Successful edges created: {successful_edges}")
    print(f"✅ Average connections per artist: {total_connections/len(test_artists):.1f}")
    
    # Test specific critical connections
    print(f"\n🔬 Testing Critical Missing Connections:")
    critical_pairs = [
        ("TWICE", "IU"),
        ("Paramore", "Tonight Alive"),
        ("ANYUJIN", "IVE")
    ]
    
    for source_artist, target_artist in critical_pairs:
        print(f"\n🎯 {source_artist} → {target_artist}:")
        
        # Check if connection exists in Deezer results
        try:
            source_connections = deezer_api.get_similar_artists(source_artist, limit=20)
            found_in_deezer = any(conn['name'].lower() == target_artist.lower() 
                                for conn in source_connections)
            print(f"   🎵 Found in Deezer: {'✅ YES' if found_in_deezer else '❌ NO'}")
            
            if found_in_deezer:
                matching_conn = next(conn for conn in source_connections 
                                   if conn['name'].lower() == target_artist.lower())
                print(f"      Similarity score: {matching_conn['match']:.3f}")
        except Exception as e:
            print(f"   🎵 Deezer check failed: {e}")
    
    print(f"\n🎉 Multi-source similarity system validation complete!")

if __name__ == "__main__":
    quick_validation()