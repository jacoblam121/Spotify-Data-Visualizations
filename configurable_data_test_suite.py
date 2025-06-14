#!/usr/bin/env python3
"""
Configurable Data Test Suite
============================
Test suite that works with YOUR actual data to verify connections between specific artists.

Features:
- Test specific artist pairs from your data
- Cross-check ALL artists in your data (not just top 10 from APIs)
- Configurable number of artists to test
- Compare old vs new similarity systems
- Debug missing connections
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent))

from config_loader import AppConfig
from data_processor import DataProcessor
from lastfm_utils import LastfmAPI
from deezer_similarity_api import DeezerSimilarityAPI
from musicbrainz_similarity_api import MusicBrainzSimilarityAPI
from edge_weighting_test import ComprehensiveEdgeWeighter

@dataclass
class ConnectionResult:
    """Result of testing a connection between two artists."""
    source_artist: str
    target_artist: str
    found_in_lastfm: bool = False
    found_in_deezer: bool = False
    found_in_musicbrainz: bool = False
    lastfm_score: float = 0.0
    deezer_score: float = 0.0
    musicbrainz_relationship: str = ""
    weighted_edge_created: bool = False
    final_similarity: float = 0.0
    final_confidence: float = 0.0
    issues: List[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []

class ConfigurableDataTestSuite:
    """Test suite that works with your actual Spotify data."""
    
    def __init__(self, spotify_data_file: str = "spotify_data.json"):
        """Initialize test suite with your actual data."""
        print("🧪 Configurable Data Test Suite")
        print("=" * 40)
        
        # Load your actual data
        self.spotify_data_file = spotify_data_file
        self.artists_in_data = self._load_artists_from_data()
        print(f"✅ Loaded {len(self.artists_in_data)} artists from your data")
        
        # Initialize APIs
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
                print("✅ Last.fm API initialized")
            else:
                print("⚠️  Last.fm API not configured")
            
            self.deezer_api = DeezerSimilarityAPI()
            print("✅ Deezer API initialized")
            
            self.musicbrainz_api = MusicBrainzSimilarityAPI()
            print("✅ MusicBrainz API initialized")
            
            self.edge_weighter = ComprehensiveEdgeWeighter()
            print("✅ Edge weighting system initialized")
            
        except Exception as e:
            print(f"❌ Initialization error: {e}")
            raise
    
    def _load_artists_from_data(self) -> List[str]:
        """Load all unique artists from your Spotify data."""
        try:
            with open(self.spotify_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            artists = set()
            for entry in data:
                if 'artistName' in entry:
                    artist_name = entry['artistName'].strip()
                    if artist_name:
                        artists.add(artist_name)
            
            return sorted(list(artists))
            
        except Exception as e:
            print(f"❌ Error loading data from {self.spotify_data_file}: {e}")
            return []
    
    def test_specific_artist_pair(self, artist1: str, artist2: str) -> ConnectionResult:
        """Test if two specific artists are connected by any API."""
        print(f"\n🔍 Testing connection: {artist1} ↔ {artist2}")
        
        result = ConnectionResult(artist1, artist2)
        
        # Test Last.fm (bidirectional)
        if self.lastfm_api:
            try:
                # Check artist1 → artist2
                similar_artists = self.lastfm_api.get_similar_artists(artist1, limit=50)
                for similar in similar_artists:
                    if similar['name'].lower() == artist2.lower():
                        result.found_in_lastfm = True
                        result.lastfm_score = similar['match']
                        print(f"   🎶 Last.fm: {artist1} → {artist2} (score: {similar['match']:.3f})")
                        break
                
                # Check artist2 → artist1 (bidirectional)
                if not result.found_in_lastfm:
                    similar_artists = self.lastfm_api.get_similar_artists(artist2, limit=50)
                    for similar in similar_artists:
                        if similar['name'].lower() == artist1.lower():
                            result.found_in_lastfm = True
                            result.lastfm_score = similar['match']
                            print(f"   🎶 Last.fm: {artist2} → {artist1} (score: {similar['match']:.3f})")
                            break
                
                if not result.found_in_lastfm:
                    print(f"   🎶 Last.fm: No connection found")
                    
            except Exception as e:
                result.issues.append(f"Last.fm error: {e}")
                print(f"   🎶 Last.fm: ERROR - {e}")
        
        # Test Deezer (bidirectional)
        try:
            # Check artist1 → artist2
            similar_artists = self.deezer_api.get_similar_artists(artist1, limit=50)
            for similar in similar_artists:
                if similar['name'].lower() == artist2.lower():
                    result.found_in_deezer = True
                    result.deezer_score = similar['match']
                    print(f"   🎵 Deezer: {artist1} → {artist2} (score: {similar['match']:.3f})")
                    break
            
            # Check artist2 → artist1 (bidirectional)
            if not result.found_in_deezer:
                similar_artists = self.deezer_api.get_similar_artists(artist2, limit=50)
                for similar in similar_artists:
                    if similar['name'].lower() == artist1.lower():
                        result.found_in_deezer = True
                        result.deezer_score = similar['match']
                        print(f"   🎵 Deezer: {artist2} → {artist1} (score: {similar['match']:.3f})")
                        break
            
            if not result.found_in_deezer:
                print(f"   🎵 Deezer: No connection found")
                
        except Exception as e:
            result.issues.append(f"Deezer error: {e}")
            print(f"   🎵 Deezer: ERROR - {e}")
        
        # Test MusicBrainz (bidirectional)
        try:
            # Check artist1 → artist2
            relationships = self.musicbrainz_api.get_relationship_based_similar_artists(artist1, limit=50)
            for rel in relationships:
                if rel['name'].lower() == artist2.lower():
                    result.found_in_musicbrainz = True
                    result.musicbrainz_relationship = rel.get('musicbrainz_relationship', 'unknown')
                    print(f"   🎭 MusicBrainz: {artist1} → {artist2} ({result.musicbrainz_relationship})")
                    break
            
            # Check artist2 → artist1 (bidirectional)
            if not result.found_in_musicbrainz:
                relationships = self.musicbrainz_api.get_relationship_based_similar_artists(artist2, limit=50)
                for rel in relationships:
                    if rel['name'].lower() == artist1.lower():
                        result.found_in_musicbrainz = True
                        result.musicbrainz_relationship = rel.get('musicbrainz_relationship', 'unknown')
                        print(f"   🎭 MusicBrainz: {artist2} → {artist1} ({result.musicbrainz_relationship})")
                        break
            
            if not result.found_in_musicbrainz:
                print(f"   🎭 MusicBrainz: No relationship found")
                
        except Exception as e:
            result.issues.append(f"MusicBrainz error: {e}")
            print(f"   🎭 MusicBrainz: ERROR - {e}")
        
        # Test edge weighting if any connection found
        if result.found_in_lastfm or result.found_in_deezer or result.found_in_musicbrainz:
            try:
                # Create source data dict
                source_data = {}
                if result.found_in_lastfm:
                    source_data['lastfm'] = [{'name': artist2, 'match': result.lastfm_score}]
                if result.found_in_deezer:
                    source_data['deezer'] = [{'name': artist2, 'match': result.deezer_score}]
                if result.found_in_musicbrainz:
                    source_data['musicbrainz'] = [{'name': artist2, 'match': 1.0, 'musicbrainz_relationship': result.musicbrainz_relationship}]
                
                edge = self.edge_weighter.create_weighted_edge(artist1, artist2, source_data)
                
                if edge:
                    result.weighted_edge_created = True
                    result.final_similarity = edge.similarity
                    result.final_confidence = edge.confidence
                    print(f"   ⚖️  Edge created: similarity={edge.similarity:.3f}, confidence={edge.confidence:.3f}")
                else:
                    print(f"   ⚖️  Edge creation failed (below threshold)")
                    
            except Exception as e:
                result.issues.append(f"Edge weighting error: {e}")
                print(f"   ⚖️  Edge weighting: ERROR - {e}")
        
        return result
    
    def test_artist_against_all_data(self, artist: str, max_checks: int = 100) -> Dict:
        """Test one artist against ALL others in your data."""
        print(f"\n🎯 Testing {artist} against ALL artists in your data")
        print(f"   (checking up to {max_checks} artists)")
        
        # Filter out the artist itself and get candidates
        other_artists = [a for a in self.artists_in_data if a.lower() != artist.lower()]
        if len(other_artists) > max_checks:
            other_artists = other_artists[:max_checks]
            print(f"   Limited to first {max_checks} artists")
        
        connections_found = []
        total_tested = 0
        
        for target_artist in other_artists:
            total_tested += 1
            
            # Quick test - just check if connection exists
            has_connection = False
            connection_sources = []
            
            # Test each API quickly
            if self.lastfm_api:
                try:
                    similar = self.lastfm_api.get_similar_artists(artist, limit=20)
                    if any(s['name'].lower() == target_artist.lower() for s in similar):
                        has_connection = True
                        connection_sources.append('lastfm')
                except:
                    pass
            
            if not has_connection:
                try:
                    similar = self.deezer_api.get_similar_artists(artist, limit=20)
                    if any(s['name'].lower() == target_artist.lower() for s in similar):
                        has_connection = True
                        connection_sources.append('deezer')
                except:
                    pass
            
            if not has_connection:
                try:
                    similar = self.musicbrainz_api.get_relationship_based_similar_artists(artist, limit=20)
                    if any(s['name'].lower() == target_artist.lower() for s in similar):
                        has_connection = True
                        connection_sources.append('musicbrainz')
                except:
                    pass
            
            if has_connection:
                connections_found.append({
                    'target': target_artist,
                    'sources': connection_sources
                })
                print(f"   ✅ {target_artist} (via {', '.join(connection_sources)})")
            
            # Rate limiting
            if total_tested % 10 == 0:
                print(f"   ... checked {total_tested}/{len(other_artists)} artists")
                time.sleep(0.5)
        
        result = {
            'artist': artist,
            'total_artists_tested': total_tested,
            'connections_found': len(connections_found),
            'connections': connections_found
        }
        
        print(f"\n📊 Results for {artist}:")
        print(f"   Total tested: {total_tested}")
        print(f"   Connections found: {len(connections_found)}")
        
        return result
    
    def test_critical_missing_connections(self) -> Dict:
        """Test the specific connections you mentioned were missing."""
        print(f"\n🚨 Testing Critical Missing Connections")
        print("=" * 45)
        
        critical_pairs = [
            ("ANYUJIN", "BTS"),
            ("ANYUJIN", "IVE"),
            ("TWICE", "IU"),
            ("Paramore", "Tonight Alive"),
            ("ANYUJIN", "Ahn Yujin")
        ]
        
        results = []
        
        for artist1, artist2 in critical_pairs:
            # Check if both artists are in your data
            artist1_in_data = artist1 in self.artists_in_data
            artist2_in_data = artist2 in self.artists_in_data
            
            print(f"\n🔍 {artist1} ↔ {artist2}")
            print(f"   {artist1} in your data: {'✅' if artist1_in_data else '❌'}")
            print(f"   {artist2} in your data: {'✅' if artist2_in_data else '❌'}")
            
            if artist1_in_data and artist2_in_data:
                result = self.test_specific_artist_pair(artist1, artist2)
                results.append(result)
            elif artist1_in_data or artist2_in_data:
                print(f"   ⚠️  Cannot test - one artist not in your data")
                # Still try to test the one that exists
                existing_artist = artist1 if artist1_in_data else artist2
                missing_artist = artist2 if artist1_in_data else artist1
                
                # Test if the missing artist appears in similarity results
                print(f"   🔍 Checking if {missing_artist} appears in {existing_artist}'s results...")
                
                if self.lastfm_api:
                    try:
                        similar = self.lastfm_api.get_similar_artists(existing_artist, limit=50)
                        found = any(s['name'].lower() == missing_artist.lower() for s in similar)
                        print(f"      Last.fm: {'✅ Found' if found else '❌ Not found'}")
                    except Exception as e:
                        print(f"      Last.fm: ERROR - {e}")
                
                try:
                    similar = self.deezer_api.get_similar_artists(existing_artist, limit=50)
                    found = any(s['name'].lower() == missing_artist.lower() for s in similar)
                    print(f"      Deezer: {'✅ Found' if found else '❌ Not found'}")
                except Exception as e:
                    print(f"      Deezer: ERROR - {e}")
            else:
                print(f"   ❌ Cannot test - neither artist in your data")
        
        return results

def run_configurable_tests():
    """Interactive menu for running different test types."""
    print("🚀 Configurable Data Test Suite")
    print("=" * 35)
    
    # Initialize test suite
    try:
        suite = ConfigurableDataTestSuite()
    except Exception as e:
        print(f"❌ Failed to initialize test suite: {e}")
        return
    
    while True:
        print(f"\n📋 Test Options:")
        print(f"1. Test specific artist pair")
        print(f"2. Test one artist against ALL your data")
        print(f"3. Test critical missing connections")
        print(f"4. Show artists in your data")
        print(f"5. Exit")
        
        choice = input(f"\nChoose an option (1-5): ").strip()
        
        if choice == "1":
            artist1 = input("Enter first artist: ").strip()
            artist2 = input("Enter second artist: ").strip()
            if artist1 and artist2:
                result = suite.test_specific_artist_pair(artist1, artist2)
                print(f"\n📊 Summary: {result.source_artist} ↔ {result.target_artist}")
                print(f"   Found in APIs: {sum([result.found_in_lastfm, result.found_in_deezer, result.found_in_musicbrainz])}/3")
                print(f"   Edge created: {'✅' if result.weighted_edge_created else '❌'}")
        
        elif choice == "2":
            artist = input("Enter artist to test: ").strip()
            if artist:
                max_checks = input("Max artists to check (default 50): ").strip()
                max_checks = int(max_checks) if max_checks.isdigit() else 50
                result = suite.test_artist_against_all_data(artist, max_checks)
        
        elif choice == "3":
            results = suite.test_critical_missing_connections()
            print(f"\n📊 Critical Connections Summary:")
            for result in results:
                status = "✅" if result.weighted_edge_created else "❌"
                print(f"   {status} {result.source_artist} ↔ {result.target_artist}")
        
        elif choice == "4":
            print(f"\n🎵 Artists in your data ({len(suite.artists_in_data)}):")
            for i, artist in enumerate(suite.artists_in_data[:50], 1):
                print(f"   {i:2}. {artist}")
            if len(suite.artists_in_data) > 50:
                print(f"   ... and {len(suite.artists_in_data) - 50} more")
        
        elif choice == "5":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    run_configurable_tests()