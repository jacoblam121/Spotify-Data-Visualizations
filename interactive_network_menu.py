#!/usr/bin/env python3
"""
Interactive Network Test Suite Menu
===================================
User-friendly menu interface for the Comprehensive Network Test Suite.

Similar to interactive_test_menu.py for Phase A.2, this provides an accessible
way to configure and run network generation and testing without command-line arguments.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from comprehensive_network_test_suite import (
    NetworkTestConfig,
    ComprehensiveNetworkTestSuite,
    analyze_artist_connections,
    load_network_from_file
)

class InteractiveNetworkMenu:
    """Interactive menu system for network testing."""
    
    def __init__(self):
        self.config = NetworkTestConfig()  # Default configuration
        self.suite = None
        self.last_network_file = None
        
    def display_header(self):
        """Display the main header."""
        print("\n" + "="*60)
        print("🌐 INTERACTIVE NETWORK TEST SUITE MENU")
        print("="*60)
        print("A comprehensive testing framework for artist similarity networks")
        print("Integrates with Phase A.2 artist verification system")
        print("="*60)
    
    def display_main_menu(self):
        """Display the main menu options."""
        print(f"\n📋 MAIN MENU")
        print("-" * 20)
        print("1. 🔧 Configure Network Parameters")
        print("2. 🧪 Run Network Tests")
        print("3. 🔍 Analyze Existing Network")
        print("4. 📊 Quick Network Generation")
        print("5. 🎨 Visual Properties Demo")
        print("6. ℹ️  Show Current Configuration")
        print("7. 📁 Manage Network Files")
        print("8. ❌ Exit")
        print()
    
    def get_user_choice(self, prompt: str, valid_choices: List[str]) -> str:
        """Get validated user input."""
        while True:
            try:
                choice = input(prompt).strip()
                if choice in valid_choices:
                    return choice
                print(f"❌ Invalid choice. Please select from: {', '.join(valid_choices)}")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
            except EOFError:
                print("\n👋 Goodbye!")
                sys.exit(0)
    
    def get_number_input(self, prompt: str, min_val: float = 0, max_val: float = float('inf')) -> float:
        """Get validated numeric input."""
        while True:
            try:
                value = float(input(prompt).strip())
                if min_val <= value <= max_val:
                    return value
                print(f"❌ Please enter a number between {min_val} and {max_val}")
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
    
    def get_text_input(self, prompt: str, allow_empty: bool = False) -> str:
        """Get text input with validation."""
        while True:
            try:
                text = input(prompt).strip()
                if text or allow_empty:
                    return text
                print("❌ Please enter some text")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
    
    def configure_network_parameters(self):
        """Configure network generation parameters."""
        print(f"\n🔧 CONFIGURE NETWORK PARAMETERS")
        print("=" * 40)
        
        # Core parameters
        print(f"\n📊 Core Parameters")
        print("-" * 20)
        
        # Top N Artists
        print(f"Current: {self.config.top_n_artists} artists")
        if self.get_user_choice("Change number of top artists? (y/n): ", ["y", "n", "Y", "N"]).lower() == "y":
            self.config.top_n_artists = int(self.get_number_input(
                "Enter number of top artists (5-200): ", 5, 200
            ))
        
        # Similarity threshold
        print(f"\nCurrent similarity threshold: {self.config.similarity_threshold}")
        if self.get_user_choice("Change similarity threshold? (y/n): ", ["y", "n", "Y", "N"]).lower() == "y":
            self.config.similarity_threshold = self.get_number_input(
                "Enter similarity threshold (0.1-1.0): ", 0.1, 1.0
            )
        
        # Seed artists
        print(f"\n🎵 Seed Artists")
        print("-" * 15)
        print(f"Current: {', '.join(self.config.seed_artists)}")
        
        if self.get_user_choice("Modify seed artists? (y/n): ", ["y", "n", "Y", "N"]).lower() == "y":
            self._configure_seed_artists()
        
        # Data source
        print(f"\n📂 Data Source")
        print("-" * 13)
        print(f"Current: {self.config.data_path}")
        
        if self.get_user_choice("Change data source? (y/n): ", ["y", "n", "Y", "N"]).lower() == "y":
            self._configure_data_source()
        
        # Visual properties
        print(f"\n🎨 Visual Properties")
        print("-" * 20)
        
        if self.get_user_choice("Configure visual properties? (y/n): ", ["y", "n", "Y", "N"]).lower() == "y":
            self._configure_visual_properties()
        
        # Test selection
        print(f"\n🧪 Test Selection")
        print("-" * 16)
        
        if self.get_user_choice("Configure which tests to run? (y/n): ", ["y", "n", "Y", "N"]).lower() == "y":
            self._configure_test_selection()
        
        print(f"\n✅ Configuration updated!")
        input("Press Enter to continue...")
    
    def _configure_seed_artists(self):
        """Configure seed artists for network generation."""
        print(f"\n🎵 Configure Seed Artists")
        print("-" * 25)
        print("Seed artists are the starting points for network generation.")
        print("Choose artists you have significant listening history with.")
        print()
        
        # Show presets
        presets = {
            "1": ["YOASOBI", "IVE", "BTS"],
            "2": ["Taylor Swift", "Olivia Rodrigo", "Billie Eilish"],
            "3": ["Arctic Monkeys", "The 1975", "Radiohead"],
            "4": ["NewJeans", "LE SSERAFIM", "aespa"],
            "5": ["Custom"]
        }
        
        print("📋 Preset Options:")
        print("1. K-pop Focus: YOASOBI, IVE, BTS")
        print("2. Pop Stars: Taylor Swift, Olivia Rodrigo, Billie Eilish")
        print("3. Indie/Alt: Arctic Monkeys, The 1975, Radiohead")
        print("4. K-pop Girl Groups: NewJeans, LE SSERAFIM, aespa")
        print("5. Custom (enter your own)")
        
        choice = self.get_user_choice("Select preset (1-5): ", ["1", "2", "3", "4", "5"])
        
        if choice == "5":
            # Custom artists
            print(f"\n✏️  Enter Custom Artists")
            print("-" * 22)
            print("Enter artist names one by one. Press Enter with empty name when done.")
            
            artists = []
            while True:
                artist = self.get_text_input(f"Artist {len(artists)+1} (or Enter to finish): ", allow_empty=True)
                if not artist:
                    break
                artists.append(artist)
                
                if len(artists) >= 10:
                    print("⚠️  Maximum 10 seed artists recommended")
                    if self.get_user_choice("Add more artists? (y/n): ", ["y", "n", "Y", "N"]).lower() == "n":
                        break
            
            if artists:
                self.config.seed_artists = artists
            else:
                print("⚠️  No artists entered, keeping current configuration")
        else:
            self.config.seed_artists = presets[choice]
        
        print(f"✅ Seed artists set to: {', '.join(self.config.seed_artists)}")
    
    def _configure_data_source(self):
        """Configure data source."""
        print(f"\n📂 Configure Data Source")
        print("-" * 25)
        
        print("Available data sources:")
        print("1. 📊 Last.fm CSV (lastfm_data.csv)")
        print("2. 🎵 Spotify JSON (spotify_data.json)")
        print("3. 🔧 Custom file path")
        
        choice = self.get_user_choice("Select data source (1-3): ", ["1", "2", "3"])
        
        if choice == "1":
            self.config.data_path = "lastfm_data.csv"
            self.config.force_data_source = "lastfm"
        elif choice == "2":
            self.config.data_path = "spotify_data.json"
            self.config.force_data_source = "spotify"
        else:
            custom_path = self.get_text_input("Enter file path: ")
            self.config.data_path = custom_path
            self.config.force_data_source = None
        
        print(f"✅ Data source set to: {self.config.data_path}")
    
    def _configure_visual_properties(self):
        """Configure visual property ranges."""
        print(f"\n🎨 Configure Visual Properties")
        print("-" * 32)
        
        # Node sizes
        print(f"📏 Node Size Range")
        print(f"Current: {self.config.min_node_size} - {self.config.max_node_size}")
        
        if self.get_user_choice("Change node size range? (y/n): ", ["y", "n", "Y", "N"]).lower() == "y":
            self.config.min_node_size = self.get_number_input("Minimum node size (1-50): ", 1, 50)
            self.config.max_node_size = self.get_number_input(
                f"Maximum node size ({self.config.min_node_size}-100): ", 
                self.config.min_node_size, 100
            )
        
        # Glow values
        print(f"\n✨ Glow Value Range")
        print(f"Current: {self.config.min_glow_value} - {self.config.max_glow_value}")
        
        if self.get_user_choice("Change glow value range? (y/n): ", ["y", "n", "Y", "N"]).lower() == "y":
            self.config.min_glow_value = self.get_number_input("Minimum glow value (0-1): ", 0, 1)
            self.config.max_glow_value = self.get_number_input(
                f"Maximum glow value ({self.config.min_glow_value}-1): ", 
                self.config.min_glow_value, 1
            )
        
        print(f"✅ Visual properties configured!")
    
    def _configure_test_selection(self):
        """Configure which tests to run."""
        print(f"\n🧪 Configure Test Selection")
        print("-" * 28)
        
        tests = [
            ("test_verification", "Artist Verification", self.config.test_verification),
            ("test_similarity_symmetry", "Similarity Symmetry", self.config.test_similarity_symmetry),
            ("test_visual_properties", "Visual Properties", self.config.test_visual_properties),
            ("test_persistence", "Network Persistence", self.config.test_persistence),
            ("test_individual_connections", "Individual Connections", self.config.test_individual_connections)
        ]
        
        for attr, name, current in tests:
            status = "✅ Enabled" if current else "❌ Disabled"
            print(f"{name}: {status}")
            
            if self.get_user_choice(f"Toggle {name}? (y/n): ", ["y", "n", "Y", "N"]).lower() == "y":
                setattr(self.config, attr, not current)
        
        print(f"✅ Test selection updated!")
    
    def run_network_tests(self):
        """Run the network test suite."""
        print(f"\n🧪 RUN NETWORK TESTS")
        print("=" * 25)
        
        # Show configuration summary
        print(f"📊 Configuration Summary:")
        print(f"   Artists: {self.config.top_n_artists}")
        print(f"   Similarity Threshold: {self.config.similarity_threshold}")
        print(f"   Seed Artists: {', '.join(self.config.seed_artists)}")
        print(f"   Data Source: {self.config.data_path}")
        print()
        
        # Confirm before running
        if self.get_user_choice("Start network test suite? (y/n): ", ["y", "n", "Y", "N"]).lower() != "y":
            return
        
        print(f"\n🚀 Starting Network Test Suite...")
        print("This may take several minutes depending on configuration.")
        print("=" * 50)
        
        try:
            # Create and run test suite
            self.suite = ComprehensiveNetworkTestSuite(self.config)
            self.suite.run_full_suite()
            
            # Store reference to generated network file
            if self.suite.results.artifacts.get("Network JSON"):
                self.last_network_file = self.suite.results.artifacts["Network JSON"]
            
            # Show summary
            summary = self.suite.results.summary()
            print(f"\n🏁 Test Suite Complete!")
            print("=" * 30)
            print(f"✅ Passed: {summary['tests_passed']}")
            print(f"❌ Failed: {summary['tests_failed']}")
            print(f"📊 Success Rate: {summary['success_rate']:.1%}")
            print(f"⏱️  Duration: {summary['duration_seconds']:.1f}s")
            
            if summary['warnings']:
                print(f"⚠️  Warnings: {summary['warnings']}")
            
            if summary['errors']:
                print(f"🚨 Errors: {summary['errors']}")
            
            # Show generated files
            if self.suite.results.artifacts:
                print(f"\n💾 Generated Files:")
                for name, path in self.suite.results.artifacts.items():
                    print(f"   {name}: {path}")
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
        
        input("\\nPress Enter to continue...")
    
    def analyze_existing_network(self):
        """Analyze an existing network file."""
        print(f"\n🔍 ANALYZE EXISTING NETWORK")
        print("=" * 35)
        
        # Find available network files
        network_files = list(Path("network_test_results").glob("*.json")) if Path("network_test_results").exists() else []
        
        if not network_files:
            print("❌ No network files found in 'network_test_results' directory")
            print("Run a network test first to generate network files.")
            input("Press Enter to continue...")
            return
        
        # Show available files
        print(f"📁 Available Network Files:")
        for i, file_path in enumerate(network_files, 1):
            file_size = file_path.stat().st_size / 1024  # KB
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            print(f"{i:2d}. {file_path.name}")
            print(f"     Size: {file_size:.1f} KB, Modified: {mod_time.strftime('%Y-%m-%d %H:%M')}")
        
        # Add option for custom file
        print(f"{len(network_files)+1:2d}. Enter custom file path")
        
        # Get user choice
        max_choice = len(network_files) + 1
        choice = int(self.get_number_input(f"Select file (1-{max_choice}): ", 1, max_choice))
        
        if choice <= len(network_files):
            selected_file = str(network_files[choice-1])
        else:
            selected_file = self.get_text_input("Enter file path: ")
        
        # Load and analyze network
        try:
            graph = load_network_from_file(selected_file)
            if not graph:
                print(f"❌ Failed to load network from {selected_file}")
                input("Press Enter to continue...")
                return
            
            self._display_network_overview(graph, selected_file)
            self._network_analysis_submenu(graph, selected_file)
            
        except Exception as e:
            print(f"❌ Error analyzing network: {e}")
            input("Press Enter to continue...")
    
    def _display_network_overview(self, graph, file_path):
        """Display network overview statistics."""
        print(f"\n📊 Network Overview: {Path(file_path).name}")
        print("=" * 50)
        
        # Basic statistics
        nodes = graph.number_of_nodes()
        edges = graph.number_of_edges()
        density = graph.density() if nodes > 1 else 0
        
        print(f"📈 Basic Statistics:")
        print(f"   Nodes: {nodes}")
        print(f"   Edges: {edges}")
        print(f"   Density: {density:.3f}")
        
        if nodes > 2:
            try:
                clustering = graph.average_clustering()
                print(f"   Average Clustering: {clustering:.3f}")
            except:
                pass
        
        # Node analysis
        if nodes > 0:
            sample_node = list(graph.nodes(data=True))[0]
            node_data = sample_node[1]
            
            print(f"\n🎵 Sample Artist: {sample_node[0]}")
            print(f"   Display Name: {node_data.get('display_name', 'N/A')}")
            print(f"   Last.fm Listeners: {node_data.get('lastfm_listeners', 0):,}")
            print(f"   User Plays: {node_data.get('user_plays', 0)}")
            print(f"   Verification: {node_data.get('verification_method', 'N/A')} ({node_data.get('verification_confidence', 0):.3f})")
            print(f"   Visual: Size={node_data.get('node_size', 0):.1f}, Glow={node_data.get('glow_value', 0):.2f}, Color={node_data.get('color', 'N/A')}")
        
        # Edge analysis
        if edges > 0:
            similarities = [data.get('similarity', 0) for _, _, data in graph.edges(data=True)]
            print(f"\n🔗 Similarity Statistics:")
            print(f"   Range: {min(similarities):.3f} - {max(similarities):.3f}")
            print(f"   Average: {sum(similarities)/len(similarities):.3f}")
    
    def _network_analysis_submenu(self, graph, file_path):
        """Network analysis submenu."""
        while True:
            print(f"\n🔍 Network Analysis Options")
            print("-" * 30)
            print("1. 🎵 Analyze Specific Artist")
            print("2. 🏆 Show Top Connections")
            print("3. 🎨 Visual Properties Analysis")
            print("4. 🔗 Similarity Relationships")
            print("5. 📊 Detailed Statistics")
            print("6. ⬅️  Back to Main Menu")
            
            choice = self.get_user_choice("Select option (1-6): ", ["1", "2", "3", "4", "5", "6"])
            
            if choice == "1":
                self._analyze_specific_artist(graph, file_path)
            elif choice == "2":
                self._show_top_connections(graph)
            elif choice == "3":
                self._analyze_visual_properties(graph)
            elif choice == "4":
                self._analyze_similarity_relationships(graph)
            elif choice == "5":
                self._show_detailed_statistics(graph)
            elif choice == "6":
                break
    
    def _analyze_specific_artist(self, graph, file_path):
        """Analyze connections for a specific artist."""
        print(f"\n🎵 Analyze Specific Artist")
        print("-" * 28)
        
        # Show available artists
        artists = list(graph.nodes())
        print(f"📋 Available Artists ({len(artists)} total):")
        
        # Show first 20 artists
        for i, artist in enumerate(artists[:20], 1):
            display_name = graph.nodes[artist].get('display_name', artist)
            print(f"{i:2d}. {display_name}")
        
        if len(artists) > 20:
            print(f"    ... and {len(artists)-20} more")
        
        # Get artist selection
        print(f"\nOptions:")
        print(f"1. Select by number (1-{min(20, len(artists))})")
        print(f"2. Enter artist name")
        
        option = self.get_user_choice("Choose option (1-2): ", ["1", "2"])
        
        if option == "1":
            if len(artists) <= 20:
                choice = int(self.get_number_input(f"Select artist (1-{len(artists)}): ", 1, len(artists)))
                selected_artist = artists[choice-1]
            else:
                print("⚠️  Too many artists to show all. Please use option 2 to enter name.")
                return
        else:
            artist_name = self.get_text_input("Enter artist name: ")
            
            # Find matching artist (case-insensitive)
            matches = [a for a in artists if a.lower() == artist_name.lower()]
            if not matches:
                # Try partial matches
                matches = [a for a in artists if artist_name.lower() in a.lower()]
            
            if not matches:
                print(f"❌ Artist '{artist_name}' not found in network")
                return
            elif len(matches) == 1:
                selected_artist = matches[0]
            else:
                print(f"🔍 Multiple matches found:")
                for i, match in enumerate(matches, 1):
                    print(f"{i}. {match}")
                choice = int(self.get_number_input(f"Select match (1-{len(matches)}): ", 1, len(matches)))
                selected_artist = matches[choice-1]
        
        # Analyze the selected artist
        print(f"\n" + "="*60)
        analyze_artist_connections(file_path, selected_artist)
        print("="*60)
        input("Press Enter to continue...")
    
    def _show_top_connections(self, graph):
        """Show artists with most connections."""
        print(f"\n🏆 Top Connected Artists")
        print("-" * 28)
        
        # Calculate degree (number of connections) for each artist
        degrees = graph.degree()
        sorted_artists = sorted(degrees, key=lambda x: x[1], reverse=True)
        
        print(f"📊 Artists by Connection Count:")
        for i, (artist, degree) in enumerate(sorted_artists[:15], 1):
            display_name = graph.nodes[artist].get('display_name', artist)
            listeners = graph.nodes[artist].get('lastfm_listeners', 0)
            print(f"{i:2d}. {display_name}")
            print(f"     Connections: {degree}, Listeners: {listeners:,}")
        
        input("\\nPress Enter to continue...")
    
    def _analyze_visual_properties(self, graph):
        """Analyze visual properties across the network."""
        print(f"\n🎨 Visual Properties Analysis")
        print("-" * 35)
        
        # Collect visual property data
        node_sizes = []
        glow_values = []
        colors = {}
        
        for node, data in graph.nodes(data=True):
            node_sizes.append(data.get('node_size', 0))
            glow_values.append(data.get('glow_value', 0))
            color = data.get('color', 'unknown')
            colors[color] = colors.get(color, 0) + 1
        
        # Node sizes
        print(f"📏 Node Sizes:")
        print(f"   Range: {min(node_sizes):.1f} - {max(node_sizes):.1f}")
        print(f"   Average: {sum(node_sizes)/len(node_sizes):.1f}")
        
        # Glow values
        print(f"\\n✨ Glow Values:")
        print(f"   Range: {min(glow_values):.2f} - {max(glow_values):.2f}")
        print(f"   Average: {sum(glow_values)/len(glow_values):.2f}")
        
        # Colors
        print(f"\\n🌈 Color Distribution:")
        color_meanings = {
            "#FF6B6B": "Red (High Engagement)",
            "#4ECDC4": "Teal (Medium Engagement)", 
            "#45B7D1": "Blue (Low Engagement)",
            "#96CEB4": "Green (Popular, Low Personal)",
            "#808080": "Gray (No Plays)"
        }
        
        for color, count in colors.items():
            meaning = color_meanings.get(color, "Custom Color")
            print(f"   {color}: {count} artists ({meaning})")
        
        input("\\nPress Enter to continue...")
    
    def _analyze_similarity_relationships(self, graph):
        """Analyze similarity relationships."""
        print(f"\n🔗 Similarity Relationships")
        print("-" * 32)
        
        if graph.number_of_edges() == 0:
            print("❌ No edges found in network")
            input("Press Enter to continue...")
            return
        
        # Collect similarity data
        similarities = []
        sources = {}
        
        for u, v, data in graph.edges(data=True):
            sim = data.get('similarity', 0)
            source = data.get('source', 'unknown')
            similarities.append(sim)
            sources[source] = sources.get(source, 0) + 1
        
        # Statistics
        similarities.sort(reverse=True)
        print(f"📊 Similarity Statistics:")
        print(f"   Total Edges: {len(similarities)}")
        print(f"   Range: {min(similarities):.3f} - {max(similarities):.3f}")
        print(f"   Average: {sum(similarities)/len(similarities):.3f}")
        print(f"   Median: {similarities[len(similarities)//2]:.3f}")
        
        # Data sources
        print(f"\\n🌐 Data Sources:")
        for source, count in sources.items():
            print(f"   {source}: {count} edges")
        
        # Top similarities
        print(f"\\n🏆 Strongest Similarities:")
        edge_list = [(u, v, data.get('similarity', 0)) for u, v, data in graph.edges(data=True)]
        edge_list.sort(key=lambda x: x[2], reverse=True)
        
        for i, (u, v, sim) in enumerate(edge_list[:10], 1):
            u_display = graph.nodes[u].get('display_name', u)
            v_display = graph.nodes[v].get('display_name', v)
            print(f"{i:2d}. {u_display} ↔ {v_display}: {sim:.3f}")
        
        input("\\nPress Enter to continue...")
    
    def _show_detailed_statistics(self, graph):
        """Show detailed network statistics."""
        print(f"\n📊 Detailed Network Statistics")
        print("-" * 35)
        
        nodes = graph.number_of_nodes()
        edges = graph.number_of_edges()
        
        print(f"🔢 Basic Metrics:")
        print(f"   Nodes: {nodes}")
        print(f"   Edges: {edges}")
        print(f"   Density: {graph.density():.3f}")
        
        if nodes > 2:
            try:
                clustering = graph.average_clustering()
                print(f"   Average Clustering: {clustering:.3f}")
            except:
                print(f"   Average Clustering: N/A")
        
        # Degree statistics
        degrees = [d for n, d in graph.degree()]
        if degrees:
            print(f"\\n📈 Degree Statistics:")
            print(f"   Average Degree: {sum(degrees)/len(degrees):.1f}")
            print(f"   Max Degree: {max(degrees)}")
            print(f"   Min Degree: {min(degrees)}")
        
        # Component analysis
        if not graph.is_directed():
            components = list(graph.connected_components())
            print(f"\\n🔗 Connectivity:")
            print(f"   Connected Components: {len(components)}")
            if components:
                largest_component_size = max(len(c) for c in components)
                print(f"   Largest Component: {largest_component_size} nodes")
        
        # Artist statistics
        listeners_data = [data.get('lastfm_listeners', 0) for node, data in graph.nodes(data=True)]
        if listeners_data:
            print(f"\\n👥 Listener Statistics:")
            print(f"   Total Artists: {len(listeners_data)}")
            print(f"   Average Listeners: {sum(listeners_data)/len(listeners_data):,.0f}")
            print(f"   Max Listeners: {max(listeners_data):,}")
            print(f"   Min Listeners: {min(listeners_data):,}")
        
        input("\\nPress Enter to continue...")
    
    def quick_network_generation(self):
        """Quick network generation with minimal configuration."""
        print(f"\n📊 QUICK NETWORK GENERATION")
        print("=" * 35)
        print("Generate a small network quickly for testing purposes.")
        print()
        
        # Quick configuration
        quick_config = NetworkTestConfig(
            top_n_artists=10,
            seed_artists=["YOASOBI", "IVE"],
            similarity_threshold=0.3,
            test_individual_connections=True,
            save_networks=True
        )
        
        print(f"⚡ Quick Configuration:")
        print(f"   Artists: {quick_config.top_n_artists}")
        print(f"   Seeds: {', '.join(quick_config.seed_artists)}")
        print(f"   Threshold: {quick_config.similarity_threshold}")
        print()
        
        if self.get_user_choice("Use this configuration? (y/n): ", ["y", "n", "Y", "N"]).lower() != "y":
            return
        
        print(f"\n🚀 Generating Quick Network...")
        print("=" * 35)
        
        try:
            suite = ComprehensiveNetworkTestSuite(quick_config)
            suite.run_full_suite()
            
            # Store reference to generated network file
            if suite.results.artifacts.get("Network JSON"):
                self.last_network_file = suite.results.artifacts["Network JSON"]
            
            # Show results
            summary = suite.results.summary()
            print(f"\n✅ Quick network generated!")
            print(f"Success Rate: {summary['success_rate']:.1%}")
            print(f"Duration: {summary['duration_seconds']:.1f}s")
            
            if suite.results.artifacts:
                print(f"\\n💾 Files:")
                for name, path in suite.results.artifacts.items():
                    print(f"   {path}")
            
        except Exception as e:
            print(f"❌ Quick generation failed: {e}")
        
        input("\\nPress Enter to continue...")
    
    def visual_properties_demo(self):
        """Demo visual properties calculation."""
        print(f"\n🎨 VISUAL PROPERTIES DEMO")
        print("=" * 32)
        print("See how visual properties are calculated based on artist metrics.")
        print()
        
        # Sample artists with different characteristics
        sample_artists = [
            {"name": "Taylor Swift", "listeners": 5161355, "user_plays": 119, "confidence": 0.95},
            {"name": "YOASOBI", "listeners": 713328, "user_plays": 30, "confidence": 0.91},
            {"name": "Niche Artist", "listeners": 50000, "user_plays": 2, "confidence": 0.75},
            {"name": "Popular No Plays", "listeners": 2000000, "user_plays": 0, "confidence": 0.85},
        ]
        
        suite = ComprehensiveNetworkTestSuite(self.config)
        
        print(f"🎵 Sample Visual Properties:")
        print("-" * 40)
        
        for artist in sample_artists:
            # Calculate visual properties
            node_size = suite._calculate_node_size(artist["listeners"], artist["user_plays"])
            glow_value = suite._calculate_glow_value(artist["confidence"], artist["listeners"])
            color = suite._calculate_node_color(artist["user_plays"], artist["listeners"])
            
            print(f"\\n{artist['name']}:")
            print(f"   Last.fm Listeners: {artist['listeners']:,}")
            print(f"   User Plays: {artist['user_plays']}")
            print(f"   Verification Confidence: {artist['confidence']:.3f}")
            print(f"   → Node Size: {node_size:.1f}")
            print(f"   → Glow Value: {glow_value:.2f}")
            print(f"   → Color: {color}")
            
            # Explain color meaning
            color_meanings = {
                "#FF6B6B": "High personal engagement",
                "#4ECDC4": "Medium engagement",
                "#45B7D1": "Low engagement", 
                "#96CEB4": "Popular but low personal engagement",
                "#808080": "No user plays"
            }
            meaning = color_meanings.get(color, "Custom color")
            print(f"   → Meaning: {meaning}")
        
        input("\\nPress Enter to continue...")
    
    def show_current_configuration(self):
        """Display current configuration."""
        print(f"\nℹ️  CURRENT CONFIGURATION")
        print("=" * 30)
        
        print(f"📊 Core Parameters:")
        print(f"   Top N Artists: {self.config.top_n_artists}")
        print(f"   Similarity Threshold: {self.config.similarity_threshold}")
        print(f"   Min Plays Threshold: {self.config.min_plays_threshold}")
        
        print(f"\\n🎵 Seed Artists:")
        for i, artist in enumerate(self.config.seed_artists, 1):
            print(f"   {i}. {artist}")
        
        print(f"\\n📂 Data Source:")
        print(f"   Path: {self.config.data_path}")
        print(f"   Forced Source: {self.config.force_data_source or 'Auto-detect'}")
        
        print(f"\\n🎨 Visual Properties:")
        print(f"   Node Size: {self.config.min_node_size} - {self.config.max_node_size}")
        print(f"   Glow Value: {self.config.min_glow_value} - {self.config.max_glow_value}")
        
        print(f"\\n🧪 Test Configuration:")
        tests = [
            ("Verification", self.config.test_verification),
            ("Similarity Symmetry", self.config.test_similarity_symmetry),
            ("Visual Properties", self.config.test_visual_properties),
            ("Persistence", self.config.test_persistence),
            ("Individual Connections", self.config.test_individual_connections)
        ]
        
        for test_name, enabled in tests:
            status = "✅ Enabled" if enabled else "❌ Disabled"
            print(f"   {test_name}: {status}")
        
        print(f"\\n📁 Output:")
        print(f"   Directory: {self.config.output_dir}")
        print(f"   Save Networks: {'✅ Yes' if self.config.save_networks else '❌ No'}")
        print(f"   Generate Reports: {'✅ Yes' if self.config.generate_reports else '❌ No'}")
        
        input("\\nPress Enter to continue...")
    
    def manage_network_files(self):
        """Manage saved network files."""
        print(f"\n📁 MANAGE NETWORK FILES")
        print("=" * 28)
        
        # Check if directory exists
        results_dir = Path(self.config.output_dir)
        if not results_dir.exists():
            print(f"❌ Results directory '{self.config.output_dir}' does not exist")
            input("Press Enter to continue...")
            return
        
        # Find network files
        json_files = list(results_dir.glob("*.json"))
        graphml_files = list(results_dir.glob("*.graphml"))
        
        if not json_files and not graphml_files:
            print(f"❌ No network files found in '{self.config.output_dir}'")
            print("Run a network test to generate files first.")
            input("Press Enter to continue...")
            return
        
        while True:
            print(f"\\n📋 File Management Options:")
            print("1. 📊 List All Files")
            print("2. 🔍 View File Details")
            print("3. 🗑️  Delete Files")
            print("4. 📦 Export Files")
            print("5. ⬅️  Back to Main Menu")
            
            choice = self.get_user_choice("Select option (1-5): ", ["1", "2", "3", "4", "5"])
            
            if choice == "1":
                self._list_network_files(json_files, graphml_files)
            elif choice == "2":
                self._view_file_details(json_files + graphml_files)
            elif choice == "3":
                self._delete_files(json_files + graphml_files)
            elif choice == "4":
                self._export_files(json_files + graphml_files)
            elif choice == "5":
                break
    
    def _list_network_files(self, json_files, graphml_files):
        """List all network files."""
        print(f"\\n📊 Network Files")
        print("-" * 20)
        
        all_files = json_files + graphml_files
        all_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        for i, file_path in enumerate(all_files, 1):
            file_size = file_path.stat().st_size / 1024  # KB
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            file_type = "JSON" if file_path.suffix == ".json" else "GraphML"
            
            print(f"{i:2d}. {file_path.name}")
            print(f"     Type: {file_type}, Size: {file_size:.1f} KB")
            print(f"     Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        input("\\nPress Enter to continue...")
    
    def _view_file_details(self, all_files):
        """View details of a specific file."""
        if not all_files:
            print("❌ No files available")
            return
        
        print(f"\\n🔍 Select File to View:")
        for i, file_path in enumerate(all_files, 1):
            print(f"{i}. {file_path.name}")
        
        choice = int(self.get_number_input(f"Select file (1-{len(all_files)}): ", 1, len(all_files)))
        selected_file = all_files[choice-1]
        
        try:
            if selected_file.suffix == ".json":
                with open(selected_file, 'r') as f:
                    data = json.load(f)
                
                nodes = data.get('nodes', [])
                edges = data.get('edges', [])
                metadata = data.get('metadata', {})
                
                print(f"\\n📊 File Details: {selected_file.name}")
                print("-" * 40)
                print(f"Nodes: {len(nodes)}")
                print(f"Edges: {len(edges)}")
                print(f"Generated: {metadata.get('generated_at', 'Unknown')}")
                
                if 'config' in metadata:
                    config = metadata['config']
                    print(f"\\nConfiguration:")
                    print(f"   Top N Artists: {config.get('top_n_artists', 'N/A')}")
                    print(f"   Similarity Threshold: {config.get('similarity_threshold', 'N/A')}")
                    print(f"   Seed Artists: {', '.join(config.get('seed_artists', []))}")
                
                if 'metrics' in metadata:
                    metrics = metadata['metrics']
                    print(f"\\nNetwork Metrics:")
                    for key, value in metrics.items():
                        print(f"   {key}: {value}")
            
            else:  # GraphML
                print(f"\\n📊 GraphML File: {selected_file.name}")
                print("Use Gephi or similar tools to view detailed GraphML content.")
                
        except Exception as e:
            print(f"❌ Error reading file: {e}")
        
        input("\\nPress Enter to continue...")
    
    def _delete_files(self, all_files):
        """Delete selected files."""
        if not all_files:
            print("❌ No files available")
            return
        
        print(f"\\n🗑️  Select Files to Delete:")
        for i, file_path in enumerate(all_files, 1):
            print(f"{i}. {file_path.name}")
        
        print(f"{len(all_files)+1}. Delete ALL files")
        
        choice = int(self.get_number_input(f"Select option (1-{len(all_files)+1}): ", 1, len(all_files)+1))
        
        if choice <= len(all_files):
            selected_file = all_files[choice-1]
            if self.get_user_choice(f"Delete {selected_file.name}? (y/n): ", ["y", "n", "Y", "N"]).lower() == "y":
                try:
                    selected_file.unlink()
                    print(f"✅ Deleted {selected_file.name}")
                except Exception as e:
                    print(f"❌ Error deleting file: {e}")
        else:
            if self.get_user_choice("Delete ALL network files? This cannot be undone! (y/n): ", ["y", "n", "Y", "N"]).lower() == "y":
                deleted_count = 0
                for file_path in all_files:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        print(f"❌ Error deleting {file_path.name}: {e}")
                
                print(f"✅ Deleted {deleted_count} files")
        
        input("\\nPress Enter to continue...")
    
    def _export_files(self, all_files):
        """Export files to a different location."""
        if not all_files:
            print("❌ No files available")
            return
        
        print(f"\\n📦 Export Network Files")
        print("-" * 25)
        
        export_dir = self.get_text_input("Enter export directory path: ")
        export_path = Path(export_dir)
        
        try:
            export_path.mkdir(parents=True, exist_ok=True)
            
            exported_count = 0
            for file_path in all_files:
                dest_path = export_path / file_path.name
                try:
                    dest_path.write_bytes(file_path.read_bytes())
                    exported_count += 1
                except Exception as e:
                    print(f"❌ Error exporting {file_path.name}: {e}")
            
            print(f"✅ Exported {exported_count} files to {export_path}")
            
        except Exception as e:
            print(f"❌ Error creating export directory: {e}")
        
        input("\\nPress Enter to continue...")
    
    def run(self):
        """Run the interactive menu."""
        try:
            while True:
                self.display_header()
                self.display_main_menu()
                
                choice = self.get_user_choice("Select option (1-8): ", 
                                            ["1", "2", "3", "4", "5", "6", "7", "8"])
                
                if choice == "1":
                    self.configure_network_parameters()
                elif choice == "2":
                    self.run_network_tests()
                elif choice == "3":
                    self.analyze_existing_network()
                elif choice == "4":
                    self.quick_network_generation()
                elif choice == "5":
                    self.visual_properties_demo()
                elif choice == "6":
                    self.show_current_configuration()
                elif choice == "7":
                    self.manage_network_files()
                elif choice == "8":
                    print("\\n👋 Thank you for using the Network Test Suite!")
                    break
        
        except KeyboardInterrupt:
            print("\\n\\n👋 Goodbye!")
        except Exception as e:
            print(f"\\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main entry point."""
    # Ensure output directory exists
    Path("network_test_results").mkdir(exist_ok=True)
    
    # Run interactive menu
    menu = InteractiveNetworkMenu()
    menu.run()

if __name__ == "__main__":
    main()