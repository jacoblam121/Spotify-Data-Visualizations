#!/usr/bin/env python3
"""
Test script to verify MBID matching is working correctly
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from artist_verification import ArtistVerifier

def test_mbid_matching():
    """Test MBID matching with known MBIDs."""
    print("🧪 Testing MBID Matching System")
    print("=" * 40)
    
    # Initialize verifier with Last.fm data
    verifier = ArtistVerifier("lastfm_data.csv")
    
    print(f"📊 Loaded {len(verifier.user_artist_mbids)} artist MBIDs from user data")
    
    # Check if *LUNA is in the data
    if "*LUNA" in verifier.user_artist_mbids:
        user_mbid = verifier.user_artist_mbids["*LUNA"]
        print(f"✅ Found *LUNA in user data with MBID: {user_mbid}")
        
        # Create test candidates - one with matching MBID, one without
        test_candidates = [
            {
                'name': '*LUNA (with MBID)',
                'listeners': 17154,
                'mbid': user_mbid,  # Matching MBID
                'url': 'test1'
            },
            {
                'name': '*LUNA (no MBID)',
                'listeners': 17154,
                'mbid': '',  # No MBID
                'url': 'test2'
            },
            {
                'name': 'Different Artist',
                'listeners': 50000,
                'mbid': 'different-mbid-here',  # Different MBID
                'url': 'test3'
            }
        ]
        
        print("\n🔍 Testing verification with candidates:")
        for i, candidate in enumerate(test_candidates, 1):
            print(f"   [{i}] {candidate['name']} (MBID: {candidate.get('mbid', 'none')})")
        
        # Run verification
        result = verifier.verify_artist_candidates("*LUNA", test_candidates)
        
        print(f"\n🔬 Verification Results:")
        print(f"   Selected: {result.chosen_profile.get('name', 'Unknown')}")
        print(f"   Confidence: {result.confidence_score:.3f}")
        print(f"   Method: {result.verification_method}")
        
        if result.verification_method == "MBID_MATCH" and result.confidence_score >= 0.95:
            print("✅ MBID matching is working correctly!")
            return True
        else:
            print("❌ MBID matching failed")
            return False
    else:
        print("❌ *LUNA not found in user MBID data")
        return False

def test_track_matching():
    """Test the improved track matching system."""
    print("\n🧪 Testing Track Matching System")
    print("=" * 40)
    
    verifier = ArtistVerifier("lastfm_data.csv")
    
    # Test with a mock candidate that has some tracks
    test_tracks = [
        "アトラクトライト",  # Should match user's track
        "different track",
        "another song"
    ]
    
    evidence = verifier._gather_track_evidence("*LUNA", test_tracks)
    
    print(f"📊 Track Evidence for *LUNA:")
    print(f"   Total user tracks: {evidence.total_user_tracks}")
    print(f"   Matches found: {evidence.match_count}")
    print(f"   Perfect matches: {evidence.perfect_match_count}")
    print(f"   Strong matches: {evidence.strong_match_count}")
    print(f"   Average score: {evidence.average_score_of_matches:.3f}")
    print(f"   Match ratio: {evidence.match_ratio:.3f}")
    
    if evidence.match_count > 0:
        print("✅ Track matching found evidence")
        for match in evidence.matched_pairs[:3]:
            print(f"      '{match.user_track}' ↔ '{match.api_track}' ({match.similarity:.2f})")
        return True
    else:
        print("❌ No track matches found")
        return False

if __name__ == "__main__":
    print("🚀 Phase A.2 Verification System Tests")
    print("=" * 50)
    
    test1_passed = test_mbid_matching()
    test2_passed = test_track_matching()
    
    print(f"\n🏁 Test Results:")
    print(f"   MBID Matching: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"   Track Matching: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All verification systems are working correctly!")
    else:
        print("\n⚠️  Some tests failed - review implementation")