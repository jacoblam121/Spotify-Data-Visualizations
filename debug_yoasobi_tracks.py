#!/usr/bin/env python3
"""
Debug YOASOBI track matching with Last.fm data
"""

import sys
import logging
from artist_verification import ArtistVerifier
from lastfm_utils import LastfmAPI
import os

logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

def debug_yoasobi_tracks():
    """Debug why YOASOBI track matching fails with Last.fm data."""
    print("🔍 Debugging YOASOBI Track Matching")
    print("=" * 50)
    
    # Initialize with Last.fm data
    print("\n📊 Loading Last.fm data...")
    lastfm_verifier = ArtistVerifier(data_path="lastfm_data.csv")
    
    # Check what tracks YOASOBI has in the data
    yoasobi_tracks = lastfm_verifier._get_user_tracks_for_artist("YOASOBI")
    print(f"\n📀 YOASOBI tracks in Last.fm data: {len(yoasobi_tracks)}")
    if yoasobi_tracks:
        print("Sample tracks:")
        for i, track in enumerate(list(yoasobi_tracks)[:5]):
            print(f"  {i+1}. '{track}'")
    
    # Now check with Spotify data for comparison
    print("\n📊 Loading Spotify data...")
    spotify_verifier = ArtistVerifier(data_path="spotify_data.json")
    
    spotify_tracks = spotify_verifier._get_user_tracks_for_artist("YOASOBI")
    print(f"\n📀 YOASOBI tracks in Spotify data: {len(spotify_tracks)}")
    if spotify_tracks:
        print("Sample tracks:")
        for i, track in enumerate(list(spotify_tracks)[:5]):
            print(f"  {i+1}. '{track}'")
    
    # Now test the Last.fm API fetching
    if yoasobi_tracks:
        print("\n🌐 Testing Last.fm API track fetching...")
        api_key = os.getenv('LASTFM_API_KEY')
        if api_key:
            api_secret = os.getenv('LASTFM_API_SECRET', '')
            lastfm_api = LastfmAPI(api_key=api_key, api_secret=api_secret)
            
            # Get candidates for YOASOBI
            try:
                candidates = lastfm_api.search_artists("YOASOBI")
                print(f"\nFound {len(candidates)} candidates for YOASOBI")
                
                for i, candidate in enumerate(candidates[:3]):
                    print(f"\n📌 Candidate {i+1}: {candidate.get('name')} ({candidate.get('listeners', 0):,} listeners)")
                    
                    # Get tracks for this candidate
                    candidate_tracks = lastfm_verifier._get_candidate_tracks(candidate, lastfm_api)
                    print(f"   API returned {len(candidate_tracks)} tracks")
                    if candidate_tracks:
                        print("   Sample API tracks:")
                        for j, track in enumerate(candidate_tracks[:5]):
                            print(f"     {j+1}. '{track}'")
                    
                    # Test track matching
                    evidence = lastfm_verifier._gather_track_evidence("YOASOBI", candidate_tracks)
                    print(f"\n   Track matching results:")
                    print(f"     Total user tracks: {evidence.total_user_tracks}")
                    print(f"     Matches found: {evidence.match_count}")
                    print(f"     Perfect matches: {evidence.perfect_match_count}")
                    print(f"     Strong matches: {evidence.strong_match_count}")
                    print(f"     Average match score: {evidence.average_score_of_matches:.3f}")
                    
                    if evidence.matched_pairs:
                        print(f"\n   Matched pairs:")
                        for match in evidence.matched_pairs[:3]:
                            print(f"     '{match.user_track}' ↔ '{match.candidate_track}' (score: {match.similarity:.3f})")
                    
            except Exception as e:
                print(f"❌ API error: {e}")
        else:
            print("⚠️  No Last.fm API key found")

if __name__ == "__main__":
    debug_yoasobi_tracks()