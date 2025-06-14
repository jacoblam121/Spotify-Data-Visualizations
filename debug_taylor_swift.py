#!/usr/bin/env python3
"""
Debug Taylor Swift track matching with Spotify data
"""

import sys
import logging
from artist_verification import ArtistVerifier
from lastfm_utils import LastfmAPI
import os

logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

def debug_taylor_swift():
    """Debug why Taylor Swift track matching fails with Spotify data."""
    print("🔍 Debugging Taylor Swift Track Matching")
    print("=" * 50)
    
    # Initialize with Spotify data
    print("\n📊 Loading Spotify data...")
    verifier = ArtistVerifier(data_path="spotify_data.json")
    
    # Check Taylor Swift tracks
    ts_tracks = verifier._get_user_tracks_for_artist("Taylor Swift")
    print(f"\n📀 Taylor Swift tracks in Spotify data: {len(ts_tracks)}")
    if ts_tracks:
        print("Sample tracks (first 10):")
        for i, track in enumerate(list(ts_tracks)[:10]):
            print(f"  {i+1}. '{track}'")
    
    # Test the Last.fm API fetching
    print("\n🌐 Testing Last.fm API track fetching...")
    api_key = os.getenv('LASTFM_API_KEY')
    if api_key:
        api_secret = os.getenv('LASTFM_API_SECRET', '')
        lastfm_api = LastfmAPI(api_key=api_key, api_secret=api_secret)
        
        # Get candidates for Taylor Swift
        try:
            candidates = lastfm_api.search_artists("Taylor Swift")
            print(f"\nFound {len(candidates)} candidates")
            
            # Focus on the main Taylor Swift candidate
            ts_candidate = None
            for candidate in candidates:
                if candidate.get('name') == 'Taylor Swift':
                    ts_candidate = candidate
                    break
            
            if ts_candidate:
                print(f"\n📌 Main candidate: {ts_candidate.get('name')} ({ts_candidate.get('listeners', 0):,} listeners)")
                
                # Get tracks for this candidate
                candidate_tracks = verifier._get_candidate_tracks(ts_candidate, lastfm_api)
                print(f"   API returned {len(candidate_tracks)} tracks")
                if candidate_tracks:
                    print("   Sample API tracks (first 10):")
                    for j, track in enumerate(candidate_tracks[:10]):
                        print(f"     {j+1}. '{track}'")
                
                # Check for exact matches
                print(f"\n   🔍 Checking for exact matches...")
                exact_matches = set(ts_tracks) & set(candidate_tracks)
                print(f"   Found {len(exact_matches)} exact matches")
                if exact_matches:
                    print("   Exact matches:")
                    for match in list(exact_matches)[:5]:
                        print(f"     - '{match}'")
                
                # Test track matching with evidence
                evidence = verifier._gather_track_evidence("Taylor Swift", candidate_tracks)
                print(f"\n   📊 Track matching results:")
                print(f"     Total user tracks: {evidence.total_user_tracks}")
                print(f"     Matches found: {evidence.match_count}")
                print(f"     Perfect matches: {evidence.perfect_match_count}")
                print(f"     Strong matches: {evidence.strong_match_count}")
                print(f"     Average match score: {evidence.average_score_of_matches:.3f}")
                print(f"     Match ratio: {evidence.match_count}/{evidence.total_user_tracks} = {evidence.match_ratio:.3f}")
                
                # Calculate confidence
                confidence = verifier._calculate_track_confidence(evidence)
                print(f"\n   🎯 Track confidence: {confidence:.3f}")
                
                # Show thresholds for Taylor Swift's track count
                track_count_factor = min(1.0, evidence.total_user_tracks / 10.0)
                print(f"\n   📏 Adaptive thresholds (track_count_factor: {track_count_factor:.2f}):")
                print(f"     Perfect threshold: {max(1, int(3 * track_count_factor))}")
                print(f"     Strong threshold: {max(2, int(5 * track_count_factor))}")
                print(f"     Min match threshold: {max(1, int(3 * track_count_factor))}")
                
                if evidence.matched_pairs and hasattr(evidence.matched_pairs[0], 'user_track'):
                    print(f"\n   Sample matched pairs:")
                    for match in evidence.matched_pairs[:5]:
                        print(f"     '{match.user_track}' ↔ '{match.candidate_track}' (score: {match.similarity:.3f})")
                    
        except Exception as e:
            print(f"❌ API error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️  No Last.fm API key found")

if __name__ == "__main__":
    debug_taylor_swift()