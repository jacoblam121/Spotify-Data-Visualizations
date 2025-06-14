#!/usr/bin/env python3
"""
Interactive Network Test Suite
==============================
Comprehensive testing suite with ENHANCED MATCHING that lets you:
1. Test one artist vs all 100 artists with relationship detection
2. Find specific connections using multi-source similarity 
3. Generate custom networks with cross-cultural name matching
4. Control all network generation parameters

Features:
✅ Enhanced name matcher (K-pop/J-pop relationships)
✅ Multi-source integration (Last.fm + Deezer + MusicBrainz) 
✅ Relationship-based connections (member ↔ group)
✅ Cross-cultural matching (Korean ↔ English variants)

Full control over your network testing!
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from integrated_network_generator import IntegratedNetworkGenerator
from fixed_edge_weighting import FixedEdgeWeighter

class InteractiveNetworkTestSuite:
    """Interactive test suite for comprehensive network testing."""
    
    def __init__(self):
        """Initialize the test suite."""
        print("🎯 Interactive Network Test Suite")
        print("=" * 35)
        
        # Load processed artist data (top 100 from your listening history)
        print("📊 Loading artist data from artist_data.json...")
        try:
            with open('artist_data.json', 'r', encoding='utf-8') as f:
                self.all_artists = json.load(f)
            print(f"✅ Loaded {len(self.all_artists)} artists from your data")
        except FileNotFoundError:
            print("❌ artist_data.json not found. Please run extract_artist_data.py first")
            sys.exit(1)
        
        # Initialize network generator
        self.generator = IntegratedNetworkGenerator()
        
        # Create artist lookup
        self.artist_lookup = {a['name'].lower(): a for a in self.all_artists}
        
        print(f"🚀 Ready for interactive testing!")
    
    def test_artist_vs_all(self, artist_name: str, limit: Optional[int] = None) -> Dict:
        """Test one artist against all others in your data."""
        print(f"\n🎯 Testing '{artist_name}' vs all {len(self.all_artists)} artists")
        
        # Find the artist in your data
        artist_key = artist_name.lower()
        if artist_key not in self.artist_lookup:
            print(f"❌ '{artist_name}' not found in your data")
            available = [a for a in self.all_artists if artist_name.lower() in a['name'].lower()]
            if available:
                print(f"🔍 Did you mean one of these?")
                for a in available[:5]:
                    print(f"   • {a['name']} ({a['play_count']} plays)")
            return {'error': 'Artist not found'}
        
        source_artist = self.artist_lookup[artist_key]
        print(f"✅ Found: {source_artist['name']} ({source_artist['play_count']} plays)")
        
        # Get enhanced similarity data from all sources (includes relationships)
        target_artist_names = {a['name'] for a in self.all_artists}
        similarity_data = self.generator._get_multi_source_similarity(source_artist['name'])
        enhanced_similarity_data = self.generator._enhance_similarity_with_relationships(
            source_artist['name'], similarity_data, target_artist_names
        )
        
        # Find connections in your data
        connections_found = []
        
        all_potential_targets = set()
        for source, results in enhanced_similarity_data.items():
            for result in results:
                target_name = result['name']
                if target_name.lower() in self.artist_lookup:
                    all_potential_targets.add(target_name)
        
        # Apply limit if specified
        if limit:
            print(f"   Limiting to top {limit} artists from your data")
            # Test against top N artists by play count
            top_artists = self.all_artists[:limit]
            target_set = {a['name'].lower() for a in top_artists}
            all_potential_targets = {name for name in all_potential_targets 
                                   if name.lower() in target_set}
        
        print(f"   Found {len(all_potential_targets)} potential connections")
        
        # Show enhancement info
        total_original = sum(len(similarity_data[source]) for source in similarity_data)
        total_enhanced = sum(len(enhanced_similarity_data[source]) for source in enhanced_similarity_data)
        enhanced_count = total_enhanced - total_original
        
        if enhanced_count > 0:
            print(f"   🔧 Enhanced matching added {enhanced_count} relationship-based connections")
            for source in enhanced_similarity_data:
                original = len(similarity_data[source])
                enhanced = len(enhanced_similarity_data[source])
                if enhanced > original:
                    print(f"      {source}: {original} → {enhanced} (+{enhanced - original})")
        else:
            print(f"   📊 Using {total_original} API-based similarity matches")
        
        # Analyze each connection
        for target_name in all_potential_targets:
            target_artist = self.artist_lookup[target_name.lower()]
            
            # Create weighted edge using enhanced similarity data
            edge = self.generator.edge_weighter.create_weighted_edge(
                source_artist['name'], target_name, enhanced_similarity_data
            )
            
            if edge:
                connection_info = {
                    'target_artist': target_name,
                    'target_plays': target_artist['play_count'],
                    'similarity': edge.similarity,
                    'distance': edge.distance,
                    'confidence': edge.confidence,
                    'is_factual': edge.is_factual,
                    'fusion_method': edge.fusion_method,
                    'sources': [c.source for c in edge.contributions],
                    'source_details': {
                        c.source: {
                            'raw_value': c.raw_value,
                            'normalized_similarity': c.normalized_similarity
                        } for c in edge.contributions
                    }
                }
                connections_found.append(connection_info)
        
        # Sort by similarity score
        connections_found.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Display results
        print(f"\n📊 Results for '{source_artist['name']}':")
        print(f"   Total connections found: {len(connections_found)}")
        
        if connections_found:
            print(f"\n🔗 Top connections:")
            for i, conn in enumerate(connections_found[:20], 1):
                sources_str = ', '.join(conn['sources'])
                factual_marker = " (FACTUAL)" if conn['is_factual'] else ""
                print(f"   {i:2}. {conn['target_artist']} - sim: {conn['similarity']:.3f}, conf: {conn['confidence']:.3f}{factual_marker}")
                print(f"       Sources: {sources_str}")
        
        return {
            'source_artist': source_artist['name'],
            'total_connections': len(connections_found),
            'connections': connections_found,
            'similarity_data_summary': {
                source: len(results) for source, results in enhanced_similarity_data.items()
            },
            'enhanced_data_summary': {
                source: f"{len(similarity_data[source])} → {len(enhanced_similarity_data[source])}" 
                for source in enhanced_similarity_data.keys()
            }
        }
    
    def test_specific_connection(self, artist1: str, artist2: str) -> Dict:
        """Test if two specific artists are connected."""
        print(f"\n🔍 Testing specific connection: {artist1} ↔ {artist2}")
        
        # Check if both artists exist
        artist1_key = artist1.lower()
        artist2_key = artist2.lower()
        
        if artist1_key not in self.artist_lookup:
            print(f"❌ '{artist1}' not found in your data")
            return {'error': f'{artist1} not found'}
        
        if artist2_key not in self.artist_lookup:
            print(f"❌ '{artist2}' not found in your data")
            return {'error': f'{artist2} not found'}
        
        source_artist = self.artist_lookup[artist1_key]
        target_artist = self.artist_lookup[artist2_key]
        
        print(f"✅ Testing: {source_artist['name']} → {target_artist['name']}")
        
        # Get enhanced similarity data using the relationship-aware system
        target_artist_names = {a['name'] for a in self.all_artists}
        
        # Get and enhance similarity data for forward direction
        similarity_data = self.generator._get_multi_source_similarity(source_artist['name'])
        enhanced_similarity_data = self.generator._enhance_similarity_with_relationships(
            source_artist['name'], similarity_data, target_artist_names
        )
        
        # Test forward direction
        forward_edge = self.generator.edge_weighter.create_weighted_edge(
            source_artist['name'], target_artist['name'], enhanced_similarity_data
        )
        
        # Get and enhance similarity data for reverse direction  
        reverse_similarity_data = self.generator._get_multi_source_similarity(target_artist['name'])
        enhanced_reverse_similarity_data = self.generator._enhance_similarity_with_relationships(
            target_artist['name'], reverse_similarity_data, target_artist_names
        )
        
        reverse_edge = self.generator.edge_weighter.create_weighted_edge(
            target_artist['name'], source_artist['name'], enhanced_reverse_similarity_data
        )
        
        # Display results
        result = {
            'artist1': source_artist['name'],
            'artist2': target_artist['name'],
            'forward_connection': None,
            'reverse_connection': None,
            'bidirectional': False
        }
        
        if forward_edge:
            print(f"   ✅ Forward connection found:")
            print(f"      Similarity: {forward_edge.similarity:.3f}")
            print(f"      Confidence: {forward_edge.confidence:.3f}")
            print(f"      Sources: {', '.join([c.source for c in forward_edge.contributions])}")
            print(f"      Factual: {forward_edge.is_factual}")
            
            result['forward_connection'] = {
                'similarity': forward_edge.similarity,
                'confidence': forward_edge.confidence,
                'sources': [c.source for c in forward_edge.contributions],
                'is_factual': forward_edge.is_factual
            }
        else:
            print(f"   ❌ No forward connection found")
        
        if reverse_edge:
            print(f"   ✅ Reverse connection found:")
            print(f"      Similarity: {reverse_edge.similarity:.3f}")
            print(f"      Confidence: {reverse_edge.confidence:.3f}")
            print(f"      Sources: {', '.join([c.source for c in reverse_edge.contributions])}")
            print(f"      Factual: {reverse_edge.is_factual}")
            
            result['reverse_connection'] = {
                'similarity': reverse_edge.similarity,
                'confidence': reverse_edge.confidence,
                'sources': [c.source for c in reverse_edge.contributions],
                'is_factual': reverse_edge.is_factual
            }
        else:
            print(f"   ❌ No reverse connection found")
        
        if forward_edge and reverse_edge:
            result['bidirectional'] = True
            print(f"   🔄 Bidirectional connection confirmed!")
        
        return result
    
    def generate_custom_network(self, num_artists: int, min_similarity: float = 0.2, 
                               min_plays: int = 5, save_file: bool = True) -> Dict:
        """Generate a custom network with specified parameters."""
        print(f"\n🌐 Generating custom network:")
        print(f"   Artists: {num_artists}")
        print(f"   Min similarity: {min_similarity}")
        print(f"   Min plays: {min_plays}")
        
        # Filter and select artists
        filtered_artists = [
            artist for artist in self.all_artists 
            if artist['play_count'] >= min_plays
        ]
        
        selected_artists = filtered_artists[:num_artists]
        
        print(f"✅ Selected {len(selected_artists)} artists for network")
        
        # Temporarily override generator settings
        original_threshold = self.generator.min_similarity_threshold
        original_plays = self.generator.min_plays_threshold
        
        self.generator.min_similarity_threshold = min_similarity
        self.generator.min_plays_threshold = min_plays
        
        try:
            # Generate filename if saving
            output_filename = None
            if save_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"custom_network_{num_artists}artists_{timestamp}.json"
            
            # Generate network
            network_data = self.generator.generate_comprehensive_network(
                selected_artists, output_filename
            )
            
            # Get statistics
            stats = self.generator.get_network_statistics(network_data)
            
            print(f"\n📊 Custom Network Statistics:")
            print(f"   Nodes: {stats['total_nodes']}")
            print(f"   Edges: {stats['total_edges']}")
            print(f"   Average similarity: {stats['average_similarity']:.3f}")
            print(f"   Average confidence: {stats['average_confidence']:.3f}")
            print(f"   Factual edges: {stats['factual_edges']} ({stats['factual_percentage']:.1f}%)")
            
            print(f"\n🔌 Source Distribution:")
            for source, count in stats['source_statistics'].items():
                percentage = (count / stats['total_edges']) * 100 if stats['total_edges'] > 0 else 0
                print(f"   {source}: {count} ({percentage:.1f}%)")
            
            return network_data
            
        finally:
            # Restore original settings
            self.generator.min_similarity_threshold = original_threshold
            self.generator.min_plays_threshold = original_plays
    
    def show_top_artists(self, limit: int = 50):
        """Show top artists in your data."""
        print(f"\n🎵 Top {limit} artists in your data:")
        for i, artist in enumerate(self.all_artists[:limit], 1):
            print(f"   {i:3}. {artist['name']} ({artist['play_count']} plays)")
    
    def search_artists(self, search_term: str, limit: int = 10):
        """Search for artists in your data."""
        search_lower = search_term.lower()
        matches = [
            artist for artist in self.all_artists 
            if search_lower in artist['name'].lower()
        ]
        
        print(f"\n🔍 Search results for '{search_term}' ({len(matches)} found):")
        for i, artist in enumerate(matches[:limit], 1):
            print(f"   {i}. {artist['name']} ({artist['play_count']} plays)")
        
        return matches
    
    def test_enhanced_matching_demo(self):
        """Demo the enhanced matching capabilities."""
        print(f"\n🔧 Enhanced Matching Demo")
        print("=" * 30)
        
        # Test some key relationships
        test_cases = [
            ("ANYUJIN", "IVE member relationship"),
            ("IVE", "Group with members"),
            ("TWICE", "K-pop group")
        ]
        
        target_artist_names = {a['name'] for a in self.all_artists}
        
        for artist_name, description in test_cases:
            print(f"\n🧪 Testing {artist_name} ({description}):")
            
            # Check if artist exists in dataset
            if artist_name.lower() in self.artist_lookup:
                print(f"   ✅ Found in dataset: {self.artist_lookup[artist_name.lower()]['play_count']} plays")
                
                # Test relationship detection
                relationships = self.generator.name_matcher.find_related_artists(artist_name, target_artist_names)
                if relationships:
                    print(f"   🔗 Relationships found:")
                    for related_artist, relationship_type, strength in relationships:
                        print(f"      → {related_artist}: {relationship_type} (strength: {strength})")
                else:
                    print(f"   📊 No relationships found in current dataset")
                    
                # Test name canonicalization
                canonical = self.generator.name_matcher.find_canonical_name(artist_name)
                if canonical != artist_name:
                    print(f"   🎯 Canonical name: '{artist_name}' → '{canonical}'")
            else:
                print(f"   ❌ Not found in current dataset")

def interactive_menu():
    """Interactive menu for network testing."""
    suite = InteractiveNetworkTestSuite()
    
    while True:
        print(f"\n🎯 Interactive Network Test Menu")
        print("=" * 35)
        print(f"1. Test one artist vs top N artists")
        print(f"2. Test one artist vs ALL {len(suite.all_artists)} artists")
        print(f"3. Test specific connection between two artists")
        print(f"4. Generate custom network (choose # of artists)")
        print(f"5. Show top artists in your data")
        print(f"6. Search for artists")
        print(f"7. Enhanced matching demo")
        print(f"8. Quick tests (critical connections)")
        print(f"9. Exit")
        
        choice = input(f"\nChoose option (1-9): ").strip()
        
        if choice == "1":
            artist = input("Enter artist name: ").strip()
            limit_str = input("Test vs top N artists (default 100): ").strip()
            limit = int(limit_str) if limit_str.isdigit() else 100
            
            if artist:
                result = suite.test_artist_vs_all(artist, limit)
        
        elif choice == "2":
            artist = input("Enter artist name: ").strip()
            if artist:
                print(f"⚠️  This will test against ALL {len(suite.all_artists)} artists (may take time)")
                confirm = input("Continue? (y/n): ").strip().lower()
                if confirm == 'y':
                    result = suite.test_artist_vs_all(artist)
        
        elif choice == "3":
            artist1 = input("Enter first artist: ").strip()
            artist2 = input("Enter second artist: ").strip()
            if artist1 and artist2:
                result = suite.test_specific_connection(artist1, artist2)
        
        elif choice == "4":
            num_str = input("Number of artists for network (default 50): ").strip()
            num_artists = int(num_str) if num_str.isdigit() else 50
            
            min_sim_str = input("Minimum similarity threshold (default 0.2): ").strip()
            min_similarity = float(min_sim_str) if min_sim_str else 0.2
            
            min_plays_str = input("Minimum play count (default 5): ").strip()
            min_plays = int(min_plays_str) if min_plays_str.isdigit() else 5
            
            save_str = input("Save to file? (y/n, default y): ").strip().lower()
            save_file = save_str != 'n'
            
            print(f"\n🚀 Generating network with {num_artists} artists...")
            result = suite.generate_custom_network(num_artists, min_similarity, min_plays, save_file)
        
        elif choice == "5":
            limit_str = input("How many top artists to show (default 50): ").strip()
            limit = int(limit_str) if limit_str.isdigit() else 50
            suite.show_top_artists(limit)
        
        elif choice == "6":
            search_term = input("Search for artist: ").strip()
            if search_term:
                suite.search_artists(search_term)
        
        elif choice == "7":
            suite.test_enhanced_matching_demo()
        
        elif choice == "8":
            print(f"🚀 Running quick tests for critical connections...")
            
            critical_tests = [
                ("ANYUJIN", "IVE"),
                ("TWICE", "IU"), 
                ("Paramore", "Tonight Alive"),
                ("Taylor Swift", "Ed Sheeran")
            ]
            
            for artist1, artist2 in critical_tests:
                suite.test_specific_connection(artist1, artist2)
        
        elif choice == "9":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    interactive_menu()