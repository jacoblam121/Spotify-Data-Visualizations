#!/usr/bin/env python3
"""
Data Cross-Check Suite
======================
Configurable test suite that cross-checks artists from YOUR actual data
against similarity APIs, rather than being limited to top 10/20 results.
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI
from deezer_similarity_api import DeezerSimilarityAPI
from musicbrainz_similarity_api import MusicBrainzSimilarityAPI

def load_artists_from_data(spotify_data_file: str = "spotify_data.json"):
    """Load all unique artists from your Spotify data."""
    try:
        with open(spotify_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        artists = set()
        for entry in data:
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

class DataCrossCheckSuite:
    """Cross-check artists from your data against similarity APIs."""
    
    def __init__(self):
        """Initialize the test suite."""
        print("🔬 Data Cross-Check Suite")
        print("=" * 30)
        
        self.artists_in_data = load_artists_from_data()
        print(f"✅ Loaded {len(self.artists_in_data)} artists from your data")
        
        # Create lowercase lookup for fast matching
        self.artists_lower = {a.lower(): a for a in self.artists_in_data}
        
        # Initialize APIs with Last.fm as PRIMARY source
        try:
            config = AppConfig("configurations.txt")
            lastfm_config = config.get_lastfm_config()
            
            self.lastfm_api = None
            if lastfm_config['enabled'] and lastfm_config['api_key']:
                self.lastfm_api = LastfmAPI(
                    lastfm_config['api_key'],
                    lastfm_config['api_secret'],
                    lastfm_config['cache_dir']
                )
                print("✅ Last.fm API initialized (PRIMARY source)")
            else:
                print("⚠️  Last.fm API not configured - this should be your PRIMARY similarity source!")
            
            self.deezer_api = DeezerSimilarityAPI()
            print("✅ Deezer API initialized (secondary source)")
            
            self.musicbrainz_api = MusicBrainzSimilarityAPI()
            print("✅ MusicBrainz API initialized (relationship source)")
            
        except Exception as e:
            print(f"❌ API initialization error: {e}")
            raise
    
    def cross_check_artist_against_your_data(self, artist: str, max_api_results: int = 100) -> Dict:
        """
        Cross-check one artist against ALL artists in your data.
        
        Instead of limiting to top 10 from APIs, we get many results from APIs
        and then see which ones match artists in YOUR data.
        """
        print(f"\n🎯 Cross-checking '{artist}' against your {len(self.artists_in_data)} artists")
        
        if artist not in self.artists_in_data:
            print(f"❌ '{artist}' not found in your data!")
            return {'error': 'Artist not in your data'}
        
        result = {
            'artist': artist,
            'total_artists_in_data': len(self.artists_in_data),
            'lastfm_matches': [],     # PRIMARY source
            'deezer_matches': [],     # Secondary source
            'musicbrainz_matches': [], # Relationship source
            'total_matches': 0,
            'apis_tested': [],
            'api_errors': []
        }
        
        # Test Last.fm FIRST (PRIMARY source)
        if self.lastfm_api:
            print(f"   🎶 Testing Last.fm (PRIMARY, limit {max_api_results})...")
            try:
                lastfm_results = self.lastfm_api.get_similar_artists(artist, limit=max_api_results)
                result['apis_tested'].append('lastfm')
                
                print(f"      Last.fm returned {len(lastfm_results)} results")
                
                # Cross-check against your data
                for api_result in lastfm_results:
                    api_artist_name = api_result['name']
                    if api_artist_name.lower() in self.artists_lower:
                        original_name = self.artists_lower[api_artist_name.lower()]
                        result['lastfm_matches'].append({
                            'target_artist': original_name,
                            'api_name': api_artist_name,
                            'similarity_score': api_result['match'],
                            'source': 'lastfm'
                        })
                
                print(f"      ✅ Found {len(result['lastfm_matches'])} matches with your data")
                
            except Exception as e:
                error_msg = f"Last.fm error: {e}"
                result['api_errors'].append(error_msg)
                print(f"      ❌ {error_msg}")
        else:
            print(f"   ⚠️  Last.fm API not available (should be PRIMARY source)")
        
        # Test Deezer (secondary)
        print(f"   🎵 Testing Deezer (secondary, limit {max_api_results})...")
        try:
            deezer_results = self.deezer_api.get_similar_artists(artist, limit=max_api_results)
            result['apis_tested'].append('deezer')
            
            print(f"      Deezer returned {len(deezer_results)} results")
            
            # Cross-check against your data
            for api_result in deezer_results:
                api_artist_name = api_result['name']
                if api_artist_name.lower() in self.artists_lower:
                    original_name = self.artists_lower[api_artist_name.lower()]
                    result['deezer_matches'].append({
                        'target_artist': original_name,
                        'api_name': api_artist_name,
                        'similarity_score': api_result['match'],
                        'source': 'deezer'
                    })
            
            print(f"      ✅ Found {len(result['deezer_matches'])} matches with your data")
            
        except Exception as e:
            error_msg = f"Deezer error: {e}"
            result['api_errors'].append(error_msg)
            print(f"      ❌ {error_msg}")
        
        # Test MusicBrainz (relationships)
        print(f"   🎭 Testing MusicBrainz (relationships, limit {max_api_results})...")
        try:
            mb_results = self.musicbrainz_api.get_relationship_based_similar_artists(artist, limit=max_api_results)
            result['apis_tested'].append('musicbrainz')
            
            print(f"      MusicBrainz returned {len(mb_results)} results")
            
            # Cross-check against your data
            for api_result in mb_results:
                api_artist_name = api_result['name']
                if api_artist_name.lower() in self.artists_lower:
                    original_name = self.artists_lower[api_artist_name.lower()]
                    result['musicbrainz_matches'].append({
                        'target_artist': original_name,
                        'api_name': api_artist_name,
                        'relationship_type': api_result.get('musicbrainz_relationship', 'unknown'),
                        'source': 'musicbrainz'
                    })
            
            print(f"      ✅ Found {len(result['musicbrainz_matches'])} matches with your data")
            
        except Exception as e:
            error_msg = f"MusicBrainz error: {e}"
            result['api_errors'].append(error_msg)
            print(f"      ❌ {error_msg}")
        
        # Summary
        result['total_matches'] = len(result['lastfm_matches']) + len(result['deezer_matches']) + len(result['musicbrainz_matches'])
        
        print(f"\n📊 Cross-check summary for '{artist}':")
        print(f"   Last.fm matches: {len(result['lastfm_matches'])} (PRIMARY)")
        print(f"   Deezer matches: {len(result['deezer_matches'])} (secondary)")
        print(f"   MusicBrainz matches: {len(result['musicbrainz_matches'])} (relationships)")
        print(f"   Total matches: {result['total_matches']}")
        
        # Show the matches (Last.fm first as PRIMARY)
        if result['lastfm_matches']:
            print(f"\n   🎶 Last.fm matches with your data (PRIMARY):")
            for match in result['lastfm_matches'][:10]:  # Show first 10
                print(f"      • {match['target_artist']} (score: {match['similarity_score']:.3f})")
        
        if result['deezer_matches']:
            print(f"\n   🎵 Deezer matches with your data (secondary):")
            for match in result['deezer_matches'][:10]:  # Show first 10
                print(f"      • {match['target_artist']} (score: {match['similarity_score']:.3f})")
        
        if result['musicbrainz_matches']:
            print(f"\n   🎭 MusicBrainz matches with your data (relationships):")
            for match in result['musicbrainz_matches'][:10]:  # Show first 10
                print(f"      • {match['target_artist']} ({match['relationship_type']})")
        
        return result
    
    def test_multiple_artists(self, artists: List[str], max_api_results: int = 50) -> Dict:
        """Test multiple artists and generate summary."""
        print(f"\n🔬 Testing {len(artists)} artists against your data")
        print("=" * 50)
        
        all_results = []
        total_matches = 0
        
        for i, artist in enumerate(artists, 1):
            print(f"\n[{i}/{len(artists)}] Testing: {artist}")
            result = self.cross_check_artist_against_your_data(artist, max_api_results)
            
            if 'error' not in result:
                all_results.append(result)
                total_matches += result['total_matches']
            
            # Rate limiting
            time.sleep(0.5)
        
        # Generate summary
        summary = {
            'artists_tested': len(all_results),
            'total_matches_found': total_matches,
            'average_matches_per_artist': total_matches / len(all_results) if all_results else 0,
            'results': all_results
        }
        
        print(f"\n📊 MULTI-ARTIST SUMMARY")
        print("=" * 25)
        print(f"Artists tested: {len(all_results)}")
        print(f"Total matches found: {total_matches}")
        print(f"Average matches per artist: {summary['average_matches_per_artist']:.1f}")
        
        # Show which artists had the most connections
        if all_results:
            sorted_results = sorted(all_results, key=lambda x: x['total_matches'], reverse=True)
            print(f"\n🏆 Top connected artists:")
            for result in sorted_results[:5]:
                print(f"   {result['artist']}: {result['total_matches']} connections")
        
        return summary
    
    def find_specific_connection(self, artist1: str, artist2: str, deep_search: bool = True) -> Dict:
        """
        Find if a specific connection exists between two artists.
        Uses deep search to check up to 100 results from each API.
        """
        print(f"\n🔍 Deep search for connection: {artist1} ↔ {artist2}")
        
        result = {
            'artist1': artist1,
            'artist2': artist2,
            'found_in_lastfm': False,    # PRIMARY
            'found_in_deezer': False,    # Secondary
            'found_in_musicbrainz': False, # Relationships
            'lastfm_score': 0.0,
            'deezer_score': 0.0,
            'musicbrainz_relationship': '',
            'direction': None,  # 'forward', 'reverse', or 'both'
            'total_api_results_checked': 0
        }
        
        search_limit = 100 if deep_search else 20
        
        # Check both directions
        for direction, (source, target) in [('forward', (artist1, artist2)), ('reverse', (artist2, artist1))]:
            print(f"   🔍 Checking {direction}: {source} → {target}")
            
            if source not in self.artists_in_data:
                print(f"      ❌ {source} not in your data")
                continue
            
            # Test Last.fm FIRST (PRIMARY)
            if self.lastfm_api:
                try:
                    lastfm_results = self.lastfm_api.get_similar_artists(source, limit=search_limit)
                    result['total_api_results_checked'] += len(lastfm_results)
                    
                    for api_result in lastfm_results:
                        if api_result['name'].lower() == target.lower():
                            result['found_in_lastfm'] = True
                            result['lastfm_score'] = api_result['match']
                            result['direction'] = direction
                            print(f"      ✅ FOUND in Last.fm (PRIMARY)! Score: {api_result['match']:.3f}")
                            break
                    
                except Exception as e:
                    print(f"      ❌ Last.fm error: {e}")
            
            # Test Deezer (secondary)
            try:
                deezer_results = self.deezer_api.get_similar_artists(source, limit=search_limit)
                result['total_api_results_checked'] += len(deezer_results)
                
                for api_result in deezer_results:
                    if api_result['name'].lower() == target.lower():
                        result['found_in_deezer'] = True
                        result['deezer_score'] = api_result['match']
                        if not result['direction']:  # Only set if not already found
                            result['direction'] = direction
                        print(f"      ✅ FOUND in Deezer (secondary)! Score: {api_result['match']:.3f}")
                        break
                
            except Exception as e:
                print(f"      ❌ Deezer error: {e}")
            
            # Test MusicBrainz
            try:
                mb_results = self.musicbrainz_api.get_relationship_based_similar_artists(source, limit=search_limit)
                result['total_api_results_checked'] += len(mb_results)
                
                for api_result in mb_results:
                    if api_result['name'].lower() == target.lower():
                        result['found_in_musicbrainz'] = True
                        result['musicbrainz_relationship'] = api_result.get('musicbrainz_relationship', 'unknown')
                        if not result['direction']:  # Only set if not already found
                            result['direction'] = direction
                        print(f"      ✅ FOUND in MusicBrainz (relationships)! Relationship: {result['musicbrainz_relationship']}")
                        break
                
            except Exception as e:
                print(f"      ❌ MusicBrainz error: {e}")
        
        # Summary
        found_anywhere = result['found_in_lastfm'] or result['found_in_deezer'] or result['found_in_musicbrainz']
        print(f"\n📊 Connection search result:")
        print(f"   Found: {'✅ YES' if found_anywhere else '❌ NO'}")
        print(f"   APIs checked: {result['total_api_results_checked']} total results")
        
        if found_anywhere:
            print(f"   Direction: {result['direction']}")
            if result['found_in_lastfm']:
                print(f"   Last.fm score: {result['lastfm_score']:.3f} (PRIMARY)")
            if result['found_in_deezer']:
                print(f"   Deezer score: {result['deezer_score']:.3f} (secondary)")
            if result['found_in_musicbrainz']:
                print(f"   MusicBrainz: {result['musicbrainz_relationship']} (relationships)")
        
        return result

def interactive_menu():
    """Interactive menu for the cross-check suite."""
    suite = DataCrossCheckSuite()
    
    while True:
        print(f"\n🔬 Data Cross-Check Menu")
        print("=" * 25)
        print(f"1. Cross-check single artist against your {len(suite.artists_in_data)} artists")
        print(f"2. Cross-check multiple artists")
        print(f"3. Find specific connection between two artists")
        print(f"4. Quick test critical missing connections")
        print(f"5. Show sample of your artists")
        print(f"6. Exit")
        
        choice = input(f"\nChoose option (1-6): ").strip()
        
        if choice == "1":
            artist = input("Enter artist name: ").strip()
            if artist:
                max_results = input("Max API results to check (default 50): ").strip()
                max_results = int(max_results) if max_results.isdigit() else 50
                suite.cross_check_artist_against_your_data(artist, max_results)
        
        elif choice == "2":
            artists_input = input("Enter artists (comma-separated): ").strip()
            if artists_input:
                artists = [a.strip() for a in artists_input.split(',')]
                max_results = input("Max API results per artist (default 50): ").strip()
                max_results = int(max_results) if max_results.isdigit() else 50
                suite.test_multiple_artists(artists, max_results)
        
        elif choice == "3":
            artist1 = input("Enter first artist: ").strip()
            artist2 = input("Enter second artist: ").strip()
            if artist1 and artist2:
                deep = input("Deep search? (y/n, default y): ").strip().lower()
                deep_search = deep != 'n'
                suite.find_specific_connection(artist1, artist2, deep_search)
        
        elif choice == "4":
            print("Testing critical missing connections...")
            critical_pairs = [
                ("ANYUJIN", "BTS"),
                ("ANYUJIN", "IVE"),
                ("TWICE", "IU"),
                ("Paramore", "Tonight Alive")
            ]
            
            for artist1, artist2 in critical_pairs:
                suite.find_specific_connection(artist1, artist2, deep_search=True)
        
        elif choice == "5":
            print(f"\n🎵 Sample of your {len(suite.artists_in_data)} artists:")
            for i, artist in enumerate(suite.artists_in_data[:50], 1):
                print(f"   {i:2}. {artist}")
            if len(suite.artists_in_data) > 50:
                print(f"   ... and {len(suite.artists_in_data) - 50} more")
        
        elif choice == "6":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    interactive_menu()