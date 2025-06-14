#!/usr/bin/env python3
"""
Critical Similarity Test
========================
Test the specific ANYUJIN-BTS connection and other critical missing connections
using your actual data.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from deezer_similarity_api import DeezerSimilarityAPI
from musicbrainz_similarity_api import MusicBrainzSimilarityAPI

def load_artists_from_data(spotify_data_file: str = "spotify_data.json"):
    """Load all unique artists from your Spotify data."""
    try:
        with open(spotify_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        artists = set()
        for entry in data:
            # Check multiple possible artist name fields
            artist_name = None
            
            if 'artistName' in entry:
                artist_name = entry['artistName']
            elif 'master_metadata_album_artist_name' in entry:
                artist_name = entry['master_metadata_album_artist_name']
            elif 'artist' in entry:
                artist_name = entry['artist']
            
            if artist_name:
                artist_name = artist_name.strip()
                if artist_name:
                    artists.add(artist_name)
        
        return sorted(list(artists))
        
    except Exception as e:
        print(f"❌ Error loading data from {spotify_data_file}: {e}")
        return []

def test_critical_connections():
    """Test the critical missing connections."""
    print("🚨 Critical Similarity Connection Test")
    print("=" * 40)
    
    # Load your actual data
    artists_in_data = load_artists_from_data()
    print(f"✅ Loaded {len(artists_in_data)} artists from your data")
    
    # Initialize APIs
    deezer_api = DeezerSimilarityAPI()
    musicbrainz_api = MusicBrainzSimilarityAPI()
    
    # Critical test cases
    critical_pairs = [
        ("ANYUJIN", "BTS"),
        ("ANYUJIN", "IVE"), 
        ("TWICE", "IU"),
        ("Paramore", "Tonight Alive"),
        ("ANYUJIN", "Ahn Yujin")
    ]
    
    print(f"\n🎵 Artists in your data (showing K-pop & rock artists):")
    kpop_rock_artists = [a for a in artists_in_data if any(keyword.lower() in a.lower() for keyword in 
                        ['bts', 'anyujin', 'ahn yujin', 'twice', 'iu', 'ive', 'paramore', 'tonight alive'])]
    for artist in kpop_rock_artists:
        print(f"   • {artist}")
    
    print(f"\n🔍 Testing Critical Connections:")
    print("=" * 35)
    
    for artist1, artist2 in critical_pairs:
        print(f"\n🎯 Testing: {artist1} ↔ {artist2}")
        
        # Check if both artists are in your data
        artist1_in_data = artist1 in artists_in_data
        artist2_in_data = artist2 in artists_in_data
        
        print(f"   {artist1} in your data: {'✅' if artist1_in_data else '❌'}")
        print(f"   {artist2} in your data: {'✅' if artist2_in_data else '❌'}")
        
        if not artist1_in_data and not artist2_in_data:
            print(f"   ❌ Cannot test - neither artist in your data")
            continue
        
        # Test the artist that exists in your data
        test_artist = artist1 if artist1_in_data else artist2
        target_artist = artist2 if artist1_in_data else artist1
        
        print(f"\n   🔍 Checking {test_artist} → {target_artist}:")
        
        # Test Deezer
        try:
            deezer_results = deezer_api.get_similar_artists(test_artist, limit=50)
            deezer_found = False
            deezer_score = 0.0
            
            for result in deezer_results:
                if result['name'].lower() == target_artist.lower():
                    deezer_found = True
                    deezer_score = result['match']
                    break
            
            print(f"      🎵 Deezer: {'✅ Found' if deezer_found else '❌ Not found'}", end="")
            if deezer_found:
                print(f" (score: {deezer_score:.3f})")
            else:
                print()
                # Show top 5 results for context
                print(f"         Top results: {', '.join([r['name'] for r in deezer_results[:5]])}")
                
        except Exception as e:
            print(f"      🎵 Deezer: ERROR - {e}")
        
        # Test MusicBrainz
        try:
            mb_results = musicbrainz_api.get_relationship_based_similar_artists(test_artist, limit=50)
            mb_found = False
            mb_relationship = ""
            
            for result in mb_results:
                if result['name'].lower() == target_artist.lower():
                    mb_found = True
                    mb_relationship = result.get('musicbrainz_relationship', 'unknown')
                    break
            
            print(f"      🎭 MusicBrainz: {'✅ Found' if mb_found else '❌ Not found'}", end="")
            if mb_found:
                print(f" ({mb_relationship})")
            else:
                print()
                if mb_results:
                    relationships_str = ', '.join([f"{r['name']} ({r.get('musicbrainz_relationship', 'unknown')})" for r in mb_results[:3]])
                    print(f"         Top relationships: {relationships_str}")
                
        except Exception as e:
            print(f"      🎭 MusicBrainz: ERROR - {e}")
        
        # Also test the reverse direction if both artists exist
        if artist1_in_data and artist2_in_data:
            reverse_artist = target_artist
            reverse_target = test_artist
            
            print(f"\n   🔄 Checking reverse: {reverse_artist} → {reverse_target}:")
            
            # Test Deezer reverse
            try:
                deezer_results = deezer_api.get_similar_artists(reverse_artist, limit=20)
                reverse_found = any(r['name'].lower() == reverse_target.lower() for r in deezer_results)
                print(f"      🎵 Deezer reverse: {'✅ Found' if reverse_found else '❌ Not found'}")
            except Exception as e:
                print(f"      🎵 Deezer reverse: ERROR - {e}")

def test_anyujin_detailed():
    """Detailed test of ANYUJIN to understand what happened to BTS connection."""
    print(f"\n🔬 DETAILED ANYUJIN ANALYSIS")
    print("=" * 30)
    
    artists_in_data = load_artists_from_data()
    
    # Check exact variations of ANYUJIN in your data
    anyujin_variations = [a for a in artists_in_data if 'anyujin' in a.lower() or 'ahn yujin' in a.lower()]
    print(f"🎵 ANYUJIN variations in your data:")
    for variation in anyujin_variations:
        print(f"   • '{variation}'")
    
    if not anyujin_variations:
        print(f"❌ No ANYUJIN found in your data!")
        return
    
    # Test each variation
    deezer_api = DeezerSimilarityAPI()
    
    for anyujin_name in anyujin_variations:
        print(f"\n🔍 Testing '{anyujin_name}' against ALL artists in your data:")
        
        try:
            # Get ALL Deezer results (not limited to 10)
            deezer_results = deezer_api.get_similar_artists(anyujin_name, limit=100)
            print(f"   🎵 Deezer returned {len(deezer_results)} total results")
            
            # Check specifically for BTS
            bts_found = False
            bts_score = 0.0
            
            for result in deezer_results:
                if 'bts' in result['name'].lower():
                    bts_found = True
                    bts_score = result['match']
                    print(f"   ✅ BTS FOUND: '{result['name']}' (score: {bts_score:.3f})")
                    break
            
            if not bts_found:
                print(f"   ❌ BTS not found in Deezer results")
            
            # Show all results to see what's available
            print(f"\n   📋 All Deezer results for '{anyujin_name}':")
            for i, result in enumerate(deezer_results, 1):
                score = result['match']
                name = result['name']
                print(f"      {i:2}. {name} ({score:.3f})")
            
            # Check which artists from your data appear in the results
            artists_in_data_lower = [a.lower() for a in artists_in_data]
            matches_with_your_data = []
            
            for result in deezer_results:
                if result['name'].lower() in artists_in_data_lower:
                    original_name = next(a for a in artists_in_data if a.lower() == result['name'].lower())
                    matches_with_your_data.append((original_name, result['match']))
            
            print(f"\n   🎯 Artists from YOUR data found in Deezer results:")
            for name, score in matches_with_your_data:
                print(f"      • {name} ({score:.3f})")
            
            if not matches_with_your_data:
                print(f"      ❌ No artists from your data found in Deezer results!")
                
        except Exception as e:
            print(f"   ❌ Error testing '{anyujin_name}': {e}")

if __name__ == "__main__":
    test_critical_connections()
    test_anyujin_detailed()