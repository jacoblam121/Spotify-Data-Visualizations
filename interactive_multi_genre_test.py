#!/usr/bin/env python3
"""
Interactive Multi-Genre Network Test Suite

An interactive test suite for exploring multi-genre artist networks with real music data.
This provides an engaging, menu-driven interface to test different configurations and 
explore the Phase 1.1 multi-genre enhancements.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
import pandas as pd


class InteractiveMultiGenreTest:
    """Interactive test suite for multi-genre network analysis."""
    
    def __init__(self):
        """Initialize the interactive test suite."""
        self.data_file = None
        self.network_data = None
        self.analyzer = None
        self.config_overrides = {}
        
        print("🎵 Interactive Multi-Genre Network Test Suite")
        print("=" * 60)
        print("This interactive suite lets you explore multi-genre artist networks")
        print("with your actual music data using different configurations.")
        print("=" * 60)
    
    def _normalize_data_format(self, df):
        """Detect and normalize data format to expected schema."""
        columns = df.columns.tolist()
        
        # Detect Spotify format
        spotify_indicators = ['master_metadata_album_artist_name', 'spotify_track_uri', 'ts']
        if all(col in columns for col in spotify_indicators):
            print("   🎵 Detected: Spotify Extended Streaming History")
            return self._normalize_spotify_data(df)
        
        # Detect Last.fm format
        lastfm_indicators = ['artist', 'track', 'timestamp']
        if all(col in columns for col in lastfm_indicators):
            print("   🎵 Detected: Last.fm Export Format")
            return self._normalize_lastfm_data(df)
        
        # Check for basic artist column
        if 'artist' in columns:
            print("   🎵 Detected: Generic format with 'artist' column")
            return df  # Already in expected format
            
        # Try to detect artist column by name patterns
        artist_candidates = [col for col in columns if 'artist' in col.lower()]
        if artist_candidates:
            print(f"   🎵 Detected: Possible artist column '{artist_candidates[0]}'")
            df_copy = df.copy()
            df_copy['artist'] = df_copy[artist_candidates[0]]
            return df_copy
        
        print(f"   ❌ Unknown data format. Columns found: {columns}")
        print(f"   💡 Expected: 'artist' column or Spotify/Last.fm format")
        return None
    
    def _normalize_spotify_data(self, df):
        """Normalize Spotify extended streaming history data."""
        print("   🔄 Normalizing Spotify data...")
        
        df_normalized = df.copy()
        
        # Handle mixed content types (music, podcasts, audiobooks)
        track_rows = df_normalized['master_metadata_track_name'].notna()
        episode_rows = df_normalized['episode_name'].notna()
        audiobook_rows = df_normalized['audiobook_title'].notna()
        
        print(f"      🎵 Music tracks: {track_rows.sum():,}")
        print(f"      🎙️  Podcast episodes: {episode_rows.sum():,}")  
        print(f"      📚 Audiobook chapters: {audiobook_rows.sum():,}")
        
        # Focus on music tracks for network analysis
        music_df = df_normalized[track_rows].copy()
        
        if len(music_df) == 0:
            print("   ❌ No music tracks found in Spotify data!")
            return None
        
        # Normalize column names
        music_df['artist'] = music_df['master_metadata_album_artist_name']
        music_df['track'] = music_df['master_metadata_track_name']
        music_df['album'] = music_df['master_metadata_album_album_name']
        
        # Normalize timestamp
        try:
            music_df['timestamp'] = pd.to_datetime(music_df['ts'], utc=True)
        except Exception as e:
            print(f"   ⚠️  Timestamp parsing warning: {e}")
            music_df['timestamp'] = music_df['ts']  # Keep as-is
        
        # Filter out rows with missing essential data
        essential_cols = ['artist', 'track']
        before_filter = len(music_df)
        music_df = music_df.dropna(subset=essential_cols)
        after_filter = len(music_df)
        
        if before_filter != after_filter:
            print(f"   🧹 Filtered out {before_filter - after_filter:,} rows with missing artist/track data")
        
        print(f"   ✅ Normalized {len(music_df):,} music tracks")
        return music_df
    
    def _normalize_lastfm_data(self, df):
        """Normalize Last.fm export data."""
        print("   🔄 Normalizing Last.fm data...")
        
        df_normalized = df.copy()
        
        # Ensure required columns exist
        if 'artist' not in df_normalized.columns:
            print("   ❌ Last.fm data missing 'artist' column!")
            return None
            
        # Filter out rows with missing essential data
        essential_cols = ['artist']
        before_filter = len(df_normalized)
        df_normalized = df_normalized.dropna(subset=essential_cols)
        after_filter = len(df_normalized)
        
        if before_filter != after_filter:
            print(f"   🧹 Filtered out {before_filter - after_filter:,} rows with missing artist data")
        
        print(f"   ✅ Normalized {len(df_normalized):,} Last.fm scrobbles")
        return df_normalized
        
    def display_main_menu(self):
        """Display the main menu options."""
        print("\n🏠 MAIN MENU")
        print("-" * 40)
        print("1. 📂 Load Music Data")
        print("2. ⚙️  Configure Network Settings")
        print("3. 🌟 Generate Multi-Genre Network")
        print("4. 📊 Analyze Network Results")
        print("5. 💾 Export Network Data")
        print("6. 🎨 Compare Multi-Genre vs Single-Genre")
        print("7. 🔍 Explore Individual Artists")
        print("8. ❓ Help & Information")
        print("9. 🚪 Exit")
        print("-" * 40)
        return input("Select an option (1-9): ").strip()
        
    def load_data_menu(self):
        """Interactive data loading menu."""
        print("\n📂 LOAD MUSIC DATA")
        print("-" * 40)
        
        # Look for common data files
        data_files = []
        common_patterns = [
            "StreamingHistory*.json",
            "lastfm_data.csv", 
            "spotify_data.json",
            "*.csv",
            "*.json"
        ]
        
        for pattern in common_patterns:
            import glob
            files = glob.glob(pattern)
            data_files.extend(files)
        
        # Remove duplicates and sort
        data_files = sorted(list(set(data_files)))
        
        if data_files:
            print("Found data files:")
            for i, file in enumerate(data_files, 1):
                size = os.path.getsize(file) / 1024 / 1024  # MB
                print(f"  {i}. {file} ({size:.1f} MB)")
            
            print(f"  {len(data_files) + 1}. Enter custom file path")
            print(f"  {len(data_files) + 2}. Back to main menu")
            
            choice = input(f"\nSelect data file (1-{len(data_files) + 2}): ").strip()
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(data_files):
                    self.data_file = data_files[choice_num - 1]
                elif choice_num == len(data_files) + 1:
                    custom_path = input("Enter file path: ").strip()
                    if os.path.exists(custom_path):
                        self.data_file = custom_path
                    else:
                        print("❌ File not found!")
                        return
                else:
                    return
            except ValueError:
                print("❌ Invalid selection!")
                return
        else:
            print("No data files found automatically.")
            custom_path = input("Enter file path: ").strip()
            if os.path.exists(custom_path):
                self.data_file = custom_path
            else:
                print("❌ File not found!")
                return
        
        # Load and preview the data
        try:
            print(f"\n🔄 Loading {self.data_file}...")
            
            if self.data_file.endswith('.csv'):
                df = pd.read_csv(self.data_file)
            elif self.data_file.endswith('.json'):
                df = pd.read_json(self.data_file)
            else:
                print("❌ Unsupported file format!")
                return
            
            print(f"✅ Data loaded successfully!")
            print(f"   📊 {len(df)} rows, {df.columns.tolist()}")
            
            # Detect and normalize data format
            df_normalized = self._normalize_data_format(df)
            
            if df_normalized is not None:
                print(f"   🔄 Data format normalized successfully")
                self.df = df_normalized
                
                if 'artist' in self.df.columns:
                    unique_artists = self.df['artist'].nunique()
                    print(f"   🎤 {unique_artists} unique artists")
                    
                    # Show top artists
                    if unique_artists > 0:
                        top_artists = self.df['artist'].value_counts().head(5)
                        print(f"   🔝 Top artists: {', '.join(top_artists.index.tolist())}")
            else:
                print("❌ Could not normalize data format!")
                return
            
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            self.data_file = None
            input("Press Enter to continue...")
    
    def configure_settings_menu(self):
        """Interactive configuration menu."""
        print("\n⚙️ CONFIGURE NETWORK SETTINGS")
        print("-" * 40)
        
        current_settings = {
            'enable_secondary_genres': True,
            'max_secondary_genres': 3,
            'top_n_artists': 50,
            'min_similarity_threshold': 0.2,
            'min_plays_threshold': 5
        }
        current_settings.update(self.config_overrides)
        
        print("Current settings:")
        for key, value in current_settings.items():
            print(f"  {key}: {value}")
        
        print("\nConfiguration options:")
        print("1. Toggle multi-genre support (enable_secondary_genres)")
        print("2. Set maximum secondary genres (1-5)")
        print("3. Set number of top artists to analyze (10-200)")
        print("4. Set minimum similarity threshold (0.1-0.8)")
        print("5. Set minimum plays threshold (1-20)")
        print("6. Reset to defaults")
        print("7. Back to main menu")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == "1":
            current = current_settings['enable_secondary_genres']
            new_value = not current
            self.config_overrides['enable_secondary_genres'] = new_value
            print(f"✅ Multi-genre support: {new_value}")
            
        elif choice == "2":
            try:
                value = int(input("Enter max secondary genres (1-5): "))
                if 1 <= value <= 5:
                    self.config_overrides['max_secondary_genres'] = value
                    print(f"✅ Max secondary genres: {value}")
                else:
                    print("❌ Value must be between 1 and 5")
            except ValueError:
                print("❌ Invalid number")
                
        elif choice == "3":
            try:
                value = int(input("Enter number of top artists (10-200): "))
                if 10 <= value <= 200:
                    self.config_overrides['top_n_artists'] = value
                    print(f"✅ Top artists: {value}")
                else:
                    print("❌ Value must be between 10 and 200")
            except ValueError:
                print("❌ Invalid number")
                
        elif choice == "4":
            try:
                value = float(input("Enter similarity threshold (0.1-0.8): "))
                if 0.1 <= value <= 0.8:
                    self.config_overrides['min_similarity_threshold'] = value
                    print(f"✅ Similarity threshold: {value}")
                else:
                    print("❌ Value must be between 0.1 and 0.8")
            except ValueError:
                print("❌ Invalid number")
                
        elif choice == "5":
            try:
                value = int(input("Enter min plays threshold (1-20): "))
                if 1 <= value <= 20:
                    self.config_overrides['min_plays_threshold'] = value
                    print(f"✅ Min plays threshold: {value}")
                else:
                    print("❌ Value must be between 1 and 20")
            except ValueError:
                print("❌ Invalid number")
                
        elif choice == "6":
            self.config_overrides = {}
            print("✅ Settings reset to defaults")
            
        elif choice == "7":
            return
        else:
            print("❌ Invalid option")
            
        input("Press Enter to continue...")
    
    def generate_network_menu(self):
        """Interactive network generation."""
        if not hasattr(self, 'df'):
            print("❌ Please load data first!")
            input("Press Enter to continue...")
            return
            
        print("\n🌟 GENERATE MULTI-GENRE NETWORK")
        print("-" * 40)
        
        # Show current configuration
        settings = {
            'enable_secondary_genres': True,
            'top_n_artists': 50,
            'min_similarity_threshold': 0.2,
            'min_plays_threshold': 5
        }
        settings.update(self.config_overrides)
        
        print("Generation settings:")
        for key, value in settings.items():
            print(f"  {key}: {value}")
        
        confirm = input(f"\nGenerate network with these settings? (y/N): ").strip().lower()
        if confirm != 'y':
            return
        
        try:
            from network_utils import initialize_network_analyzer
            
            # Initialize analyzer
            print("\n🔄 Initializing network analyzer...")
            self.analyzer = initialize_network_analyzer()
            
            # Apply configuration overrides
            for key, value in self.config_overrides.items():
                if key in self.analyzer.network_config:
                    self.analyzer.network_config[key] = value
                    
            # Generate network
            print("🔄 Generating network data...")
            start_time = time.time()
            
            self.network_data = self.analyzer.create_network_data(
                self.df,
                top_n_artists=settings.get('top_n_artists'),
                min_plays_threshold=settings.get('min_plays_threshold'),
                min_similarity_threshold=settings.get('min_similarity_threshold')
            )
            
            generation_time = time.time() - start_time
            
            # Display results
            nodes = self.network_data.get('nodes', [])
            edges = self.network_data.get('edges', [])
            
            print(f"\n🎉 Network generation complete!")
            print(f"   ⏱️  Generation time: {generation_time:.2f} seconds")
            print(f"   📊 {len(nodes)} nodes, {len(edges)} edges")
            
            if settings.get('enable_secondary_genres', True):
                multi_genre_nodes = [n for n in nodes if n.get('is_multi_genre', False)]
                print(f"   🎨 Multi-genre nodes: {len(multi_genre_nodes)}")
                
                if multi_genre_nodes:
                    print(f"   🌈 Top multi-genre artists:")
                    for node in multi_genre_nodes[:5]:
                        primary = node.get('primary_genre', 'unknown')
                        secondary = node.get('secondary_genres', [])
                        print(f"      {node['name']}: {primary} + {secondary}")
            
            # Show genre distribution
            genre_dist = {}
            for node in nodes:
                genre = node.get('cluster_genre', 'unknown')
                genre_dist[genre] = genre_dist.get(genre, 0) + 1
            
            print(f"   🎭 Genre distribution:")
            for genre, count in sorted(genre_dist.items(), key=lambda x: x[1], reverse=True):
                print(f"      {genre}: {count} artists")
                
        except Exception as e:
            print(f"❌ Network generation failed: {e}")
            import traceback
            traceback.print_exc()
            
        input("\nPress Enter to continue...")
    
    def analyze_results_menu(self):
        """Interactive results analysis."""
        if not self.network_data:
            print("❌ Please generate a network first!")
            input("Press Enter to continue...")
            return
            
        print("\n📊 ANALYZE NETWORK RESULTS")
        print("-" * 40)
        
        nodes = self.network_data.get('nodes', [])
        edges = self.network_data.get('edges', [])
        
        print("Analysis options:")
        print("1. 📈 Basic network statistics")
        print("2. 🎨 Multi-genre analysis")
        print("3. 🔗 Edge analysis")
        print("4. 🎭 Genre clustering analysis")
        print("5. 🔍 Search specific artist")
        print("6. Back to main menu")
        
        choice = input("\nSelect analysis (1-6): ").strip()
        
        if choice == "1":
            self._show_basic_stats(nodes, edges)
        elif choice == "2":
            self._show_multi_genre_analysis(nodes)
        elif choice == "3":
            self._show_edge_analysis(edges)
        elif choice == "4":
            self._show_genre_clustering(nodes)
        elif choice == "5":
            self._search_artist(nodes)
        elif choice == "6":
            return
        else:
            print("❌ Invalid option")
            
        input("\nPress Enter to continue...")
    
    def _show_basic_stats(self, nodes, edges):
        """Show basic network statistics."""
        print("\n📈 BASIC NETWORK STATISTICS")
        print("-" * 30)
        print(f"Total nodes: {len(nodes)}")
        print(f"Total edges: {len(edges)}")
        
        if edges:
            weights = [e.get('weight', 0) for e in edges]
            print(f"Average edge weight: {sum(weights)/len(weights):.3f}")
            print(f"Max edge weight: {max(weights):.3f}")
            print(f"Min edge weight: {min(weights):.3f}")
        
        if nodes:
            play_counts = [n.get('play_count', 0) for n in nodes]
            print(f"Total play count: {sum(play_counts):,}")
            print(f"Average plays per artist: {sum(play_counts)/len(play_counts):.1f}")
    
    def _show_multi_genre_analysis(self, nodes):
        """Show multi-genre specific analysis."""
        print("\n🎨 MULTI-GENRE ANALYSIS")
        print("-" * 30)
        
        multi_genre_nodes = [n for n in nodes if n.get('is_multi_genre', False)]
        single_genre_nodes = [n for n in nodes if not n.get('is_multi_genre', False)]
        
        print(f"Multi-genre artists: {len(multi_genre_nodes)}")
        print(f"Single-genre artists: {len(single_genre_nodes)}")
        
        if multi_genre_nodes:
            print(f"\nTop multi-genre artists:")
            for node in sorted(multi_genre_nodes, key=lambda x: x.get('play_count', 0), reverse=True)[:10]:
                primary = node.get('primary_genre', 'unknown')
                secondary = node.get('secondary_genres', [])
                plays = node.get('play_count', 0)
                print(f"  {node['name']}: {primary} + {secondary} ({plays} plays)")
    
    def _show_edge_analysis(self, edges):
        """Show edge analysis."""
        print("\n🔗 EDGE ANALYSIS")
        print("-" * 30)
        
        if not edges:
            print("No edges found")
            return
            
        # Group by weight ranges
        weight_ranges = {
            'Very Strong (0.8+)': 0,
            'Strong (0.6-0.8)': 0,
            'Medium (0.4-0.6)': 0,
            'Weak (0.2-0.4)': 0,
            'Very Weak (<0.2)': 0
        }
        
        for edge in edges:
            weight = edge.get('weight', 0)
            if weight >= 0.8:
                weight_ranges['Very Strong (0.8+)'] += 1
            elif weight >= 0.6:
                weight_ranges['Strong (0.6-0.8)'] += 1
            elif weight >= 0.4:
                weight_ranges['Medium (0.4-0.6)'] += 1
            elif weight >= 0.2:
                weight_ranges['Weak (0.2-0.4)'] += 1
            else:
                weight_ranges['Very Weak (<0.2)'] += 1
        
        print("Edge strength distribution:")
        for range_name, count in weight_ranges.items():
            percentage = (count / len(edges)) * 100
            print(f"  {range_name}: {count} ({percentage:.1f}%)")
    
    def _show_genre_clustering(self, nodes):
        """Show genre clustering analysis."""
        print("\n🎭 GENRE CLUSTERING ANALYSIS")
        print("-" * 30)
        
        genre_stats = {}
        for node in nodes:
            genre = node.get('cluster_genre', 'unknown')
            if genre not in genre_stats:
                genre_stats[genre] = {
                    'count': 0,
                    'total_plays': 0,
                    'multi_genre_count': 0
                }
            
            genre_stats[genre]['count'] += 1
            genre_stats[genre]['total_plays'] += node.get('play_count', 0)
            if node.get('is_multi_genre', False):
                genre_stats[genre]['multi_genre_count'] += 1
        
        print("Genre statistics:")
        for genre, stats in sorted(genre_stats.items(), key=lambda x: x[1]['count'], reverse=True):
            multi_pct = (stats['multi_genre_count'] / stats['count']) * 100 if stats['count'] > 0 else 0
            avg_plays = stats['total_plays'] / stats['count'] if stats['count'] > 0 else 0
            print(f"  {genre}: {stats['count']} artists, {multi_pct:.1f}% multi-genre, {avg_plays:.0f} avg plays")
    
    def _search_artist(self, nodes):
        """Search for specific artist."""
        search_term = input("Enter artist name to search: ").strip().lower()
        
        matches = []
        for node in nodes:
            if search_term in node.get('name', '').lower():
                matches.append(node)
        
        if not matches:
            print(f"No artists found matching '{search_term}'")
            return
        
        print(f"\nFound {len(matches)} matching artist(s):")
        for node in matches:
            print(f"\n🎤 {node['name']}")
            print(f"   Play count: {node.get('play_count', 0)}")
            print(f"   Rank: #{node.get('rank', 'unknown')}")
            print(f"   Primary genre: {node.get('cluster_genre', 'unknown')}")
            if node.get('is_multi_genre', False):
                print(f"   Secondary genres: {node.get('secondary_genres', [])}")
                print(f"   Multi-genre styling: {node.get('styling', {})}")
            else:
                print(f"   Single-genre artist")
    
    def export_data_menu(self):
        """Export network data menu."""
        if not self.network_data:
            print("❌ Please generate a network first!")
            input("Press Enter to continue...")
            return
            
        print("\n💾 EXPORT NETWORK DATA")
        print("-" * 40)
        
        filename = input("Enter filename (or press Enter for default): ").strip()
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"interactive_network_{timestamp}.json"
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.network_data, f, indent=2, default=str)
            
            file_size = os.path.getsize(filename) / 1024  # KB
            print(f"✅ Network data exported to: {filename}")
            print(f"   📁 File size: {file_size:.1f} KB")
            print(f"   📊 Contains: {len(self.network_data.get('nodes', []))} nodes, {len(self.network_data.get('edges', []))} edges")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            
        input("Press Enter to continue...")
    
    def compare_modes_menu(self):
        """Compare multi-genre vs single-genre modes."""
        if not hasattr(self, 'df'):
            print("❌ Please load data first!")
            input("Press Enter to continue...")
            return
            
        print("\n🎨 COMPARE MULTI-GENRE VS SINGLE-GENRE")
        print("-" * 40)
        print("This will generate networks in both modes for comparison...")
        
        confirm = input("Continue? This may take a while (y/N): ").strip().lower()
        if confirm != 'y':
            return
        
        try:
            from network_utils import initialize_network_analyzer
            
            # Settings for comparison
            settings = {
                'top_n_artists': 30,  # Smaller for faster comparison
                'min_similarity_threshold': 0.2,
                'min_plays_threshold': 5
            }
            settings.update(self.config_overrides)
            
            print("\n🔄 Generating single-genre network...")
            analyzer1 = initialize_network_analyzer()
            analyzer1.network_config['enable_secondary_genres'] = False
            
            network1 = analyzer1.create_network_data(
                self.df,
                top_n_artists=settings['top_n_artists'],
                min_plays_threshold=settings['min_plays_threshold'],
                min_similarity_threshold=settings['min_similarity_threshold']
            )
            
            print("🔄 Generating multi-genre network...")
            analyzer2 = initialize_network_analyzer()
            analyzer2.network_config['enable_secondary_genres'] = True
            
            network2 = analyzer2.create_network_data(
                self.df,
                top_n_artists=settings['top_n_artists'],
                min_plays_threshold=settings['min_plays_threshold'],
                min_similarity_threshold=settings['min_similarity_threshold']
            )
            
            # Compare results
            print("\n📊 COMPARISON RESULTS")
            print("-" * 30)
            print(f"Single-genre mode:")
            print(f"  Nodes: {len(network1.get('nodes', []))}")
            print(f"  Edges: {len(network1.get('edges', []))}")
            
            print(f"\nMulti-genre mode:")
            print(f"  Nodes: {len(network2.get('nodes', []))}")
            print(f"  Edges: {len(network2.get('edges', []))}")
            
            # Check for multi-genre enhancements
            multi_genre_nodes = [n for n in network2.get('nodes', []) if n.get('is_multi_genre', False)]
            print(f"  Multi-genre nodes: {len(multi_genre_nodes)}")
            
            # Save both for comparison
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            with open(f"single_genre_network_{timestamp}.json", 'w') as f:
                json.dump(network1, f, indent=2, default=str)
            
            with open(f"multi_genre_network_{timestamp}.json", 'w') as f:
                json.dump(network2, f, indent=2, default=str)
            
            print(f"\n💾 Both networks saved with timestamp {timestamp}")
            
        except Exception as e:
            print(f"❌ Comparison failed: {e}")
            import traceback
            traceback.print_exc()
            
        input("\nPress Enter to continue...")
    
    def show_help(self):
        """Show help and information."""
        print("\n❓ HELP & INFORMATION")
        print("-" * 40)
        print("🎵 Interactive Multi-Genre Network Test Suite")
        print("\nThis tool helps you explore multi-genre artist networks with your music data.")
        print("\n🔧 Workflow:")
        print("1. Load your music data (CSV or JSON)")
        print("2. Configure network generation settings")
        print("3. Generate the network with multi-genre support")
        print("4. Analyze and explore the results")
        print("5. Export data for visualization")
        print("\n🎨 Multi-Genre Features:")
        print("• Artists can span multiple genres")
        print("• Enhanced styling data for visualization")
        print("• Genre-based clustering and positioning")
        print("• Configurable secondary genre limits")
        print("\n📊 Supported Data Formats:")
        print("• Spotify JSON files (StreamingHistory)")
        print("• Last.fm CSV exports")
        print("• Any CSV/JSON with 'artist' column")
        print("\n🎯 Configuration Options:")
        print("• enable_secondary_genres: Enable/disable multi-genre support")
        print("• max_secondary_genres: How many secondary genres per artist")
        print("• top_n_artists: Number of top artists to analyze")
        print("• min_similarity_threshold: Minimum connection strength")
        print("• min_plays_threshold: Minimum plays to include artist")
        
        input("\nPress Enter to continue...")
    
    def run(self):
        """Run the interactive test suite."""
        while True:
            try:
                choice = self.display_main_menu()
                
                if choice == "1":
                    self.load_data_menu()
                elif choice == "2":
                    self.configure_settings_menu()
                elif choice == "3":
                    self.generate_network_menu()
                elif choice == "4":
                    self.analyze_results_menu()
                elif choice == "5":
                    self.export_data_menu()
                elif choice == "6":
                    self.compare_modes_menu()
                elif choice == "7":
                    self.analyze_results_menu()  # Reuse analysis menu for artist exploration
                elif choice == "8":
                    self.show_help()
                elif choice == "9":
                    print("\n👋 Thanks for using the Interactive Multi-Genre Test Suite!")
                    print("🎵 Happy network exploring!")
                    break
                else:
                    print("❌ Invalid option. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                print("Please try again or report this issue.")
                input("Press Enter to continue...")


def main():
    """Main entry point."""
    test_suite = InteractiveMultiGenreTest()
    test_suite.run()


if __name__ == "__main__":
    main()