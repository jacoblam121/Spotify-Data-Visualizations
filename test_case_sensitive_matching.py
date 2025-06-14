#!/usr/bin/env python3
"""
Test Case-Insensitive Artist Matching
=====================================
Tests the case-insensitive fallback implementation for artist verification.
"""

import sys
import logging
from artist_verification import ArtistVerifier

logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

def test_case_variations():
    """Test case-insensitive matching with various artist name variations."""
    print("🧪 Testing Case-Insensitive Artist Matching")
    print("=" * 50)
    
    # Test with Last.fm data
    print("\n📊 Testing with Last.fm data...")
    lastfm_verifier = ArtistVerifier(data_path="lastfm_data.csv")
    
    # Test artist present in data
    artists_to_test = ["*LUNA", "*luna", "*Luna", "*LuNa"]
    for artist in artists_to_test:
        tracks = lastfm_verifier._get_user_tracks_for_artist(artist)
        albums = lastfm_verifier._get_user_albums_for_artist(artist)
        mbid = lastfm_verifier._get_user_mbid_for_artist(artist)
        
        if tracks:
            print(f"✅ {artist}: Found {len(tracks)} tracks")
            if mbid:
                print(f"   🔑 MBID: {mbid}")
        else:
            print(f"❌ {artist}: No tracks found")
    
    # Test with Spotify data
    print("\n\n📊 Testing with Spotify data...")
    spotify_verifier = ArtistVerifier(data_path="spotify_data.json")
    
    # Test different case variations
    test_cases = [
        ("*Luna", "*LUNA"),  # Spotify has *Luna, testing *LUNA lookup
        ("YOASOBI", "yoasobi"),  # Testing Japanese artist
        ("IVE", "ive"),  # Testing K-pop artist
        ("Taylor Swift", "taylor swift"),  # Testing common artist
    ]
    
    for original, variant in test_cases:
        print(f"\n📝 Testing {original} -> {variant}")
        
        # Test original
        original_tracks = spotify_verifier._get_user_tracks_for_artist(original)
        if original_tracks:
            print(f"   ✅ Original '{original}': {len(original_tracks)} tracks")
        else:
            print(f"   ❌ Original '{original}': Not found")
        
        # Test variant
        variant_tracks = spotify_verifier._get_user_tracks_for_artist(variant)
        if variant_tracks:
            print(f"   ✅ Variant '{variant}': {len(variant_tracks)} tracks")
            if original_tracks and original_tracks == variant_tracks:
                print(f"   🎯 Case-insensitive match confirmed!")
        else:
            print(f"   ❌ Variant '{variant}': Not found")

def test_edge_cases():
    """Test edge cases for case-insensitive matching."""
    print("\n\n🔧 Testing Edge Cases")
    print("=" * 50)
    
    verifier = ArtistVerifier(data_path="spotify_data.json")
    
    # Test empty string
    tracks = verifier._get_user_tracks_for_artist("")
    print(f"Empty string: {len(tracks)} tracks (expected: 0)")
    
    # Test non-existent artist
    tracks = verifier._get_user_tracks_for_artist("NonExistentArtist123")
    print(f"Non-existent artist: {len(tracks)} tracks (expected: 0)")
    
    # Test Unicode normalization
    unicode_tests = [
        ("café", "CAFÉ"),
        ("naïve", "NAÏVE"),
        ("Björk", "BJÖRK"),
    ]
    
    print("\n📝 Unicode normalization tests:")
    for lower, upper in unicode_tests:
        # These would need actual data to test properly
        lower_normalized = lower.casefold()
        upper_normalized = upper.casefold()
        match = lower_normalized == upper_normalized
        print(f"   {lower} vs {upper}: {'✅ Match' if match else '❌ No match'}")

if __name__ == "__main__":
    test_case_variations()
    test_edge_cases()
    print("\n\n✨ Case-insensitive matching tests complete!")