#!/usr/bin/env python3
"""
Node Metrics Analyzer - Phase 0 Testing Suite
Interactive tool to generate and display detailed node metrics across all sizing modes.
"""

import os
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from tabulate import tabulate

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from create_id_mapping import create_enhanced_network_with_stable_ids


class NodeMetricsAnalyzer:
    """Interactive analyzer for node metrics across sizing modes."""
    
    def __init__(self):
        self.results_dir = "node_metrics_results"
        self.ensure_results_dir()
        
        # Store original working directory and find project root
        self.original_cwd = os.getcwd()
        self.project_root = self._find_project_root()
        
    def _find_project_root(self):
        """Find the project root directory (where configurations.txt is located)."""
        current = os.getcwd()
        
        # Check if we're already in the right directory
        if os.path.exists('configurations.txt'):
            return current
            
        # Check parent directory
        parent = os.path.dirname(current)
        if os.path.exists(os.path.join(parent, 'configurations.txt')):
            return parent
            
        # If not found, stay in current directory
        return current
    
    def _ensure_project_context(self):
        """Ensure we're running from the project root directory."""
        if os.getcwd() != self.project_root:
            print(f"📁 Changing to project root: {self.project_root}")
            os.chdir(self.project_root)
    
    def _restore_context(self):
        """Restore original working directory."""
        if os.getcwd() != self.original_cwd:
            os.chdir(self.original_cwd)
    
    def ensure_results_dir(self):
        """Ensure results directory exists."""
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
    
    def display_menu(self):
        """Display main menu options."""
        print("🔬 Node Metrics Analyzer - Phase 0 Testing Suite")
        print("=" * 60)
        print()
        print("Analysis Options:")
        print("  1. Compare All Sizing Modes (5 artists)")
        print("  2. Compare All Sizing Modes (10 artists)")
        print("  3. Compare All Sizing Modes (20 artists)")
        print("  4. Single Mode Analysis (Custom)")
        print("  5. Detailed Node Properties Report")
        print("  6. Glow Effect Analysis")
        print("  7. Personal vs Global Weight Analysis")
        print()
        print("Utility Options:")
        print("  8. View Previous Results")
        print("  9. Clean Results Directory")
        print("  0. Exit")
        print()
    
    def get_user_choice(self) -> int:
        """Get user menu choice."""
        try:
            choice = int(input("Select option: "))
            return choice
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
            return -1
    
    def compare_all_sizing_modes(self, artist_count: int):
        """Generate and compare metrics across all three sizing modes."""
        print(f"🔄 Comparing All Sizing Modes ({artist_count} artists)")
        print("=" * 50)
        
        modes = ['global', 'personal', 'adaptive']
        results = {}
        
        try:
            self._ensure_project_context()
            
            # Generate data for each mode
            for mode in modes:
                print(f"\\n📊 Generating {mode} mode data...")
                network_data = create_enhanced_network_with_stable_ids(
                    top_n_artists=artist_count,
                    sizing_mode=mode
                )
                
                if network_data and 'nodes' in network_data:
                    results[mode] = network_data['nodes']
                    print(f"✅ {mode} mode: {len(network_data['nodes'])} nodes generated")
                else:
                    print(f"❌ {mode} mode: Failed to generate data")
                    return
            
            # Save combined results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            comparison_file = os.path.join(
                self.original_cwd, 
                self.results_dir, 
                f"mode_comparison_{artist_count}artists_{timestamp}.json"
            )
            
            combined_data = {
                'timestamp': timestamp,
                'artist_count': artist_count,
                'modes': results,
                'metadata': {
                    'total_nodes_per_mode': {mode: len(nodes) for mode, nodes in results.items()},
                    'generation_timestamp': timestamp
                }
            }
            
            with open(comparison_file, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, indent=2, ensure_ascii=False)
            
            print(f"\\n💾 Results saved: {comparison_file}")
            
            # Display comparison tables
            self.display_size_comparison(results)
            self.display_glow_comparison(results)
            self.display_metric_comparison(results)
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._restore_context()
    
    def display_size_comparison(self, results: Dict[str, List[Dict]]):
        """Display size comparison table across modes."""
        print("\\n📏 Size Comparison Across Modes")
        print("=" * 40)
        
        # Get artist names from first mode
        if not results:
            return
            
        first_mode = list(results.keys())[0]
        artists = [node['canonical_name'] for node in results[first_mode]]
        
        # Create comparison table
        table_data = []
        for i, artist in enumerate(artists):
            row = [artist]
            for mode in ['global', 'personal', 'adaptive']:
                if mode in results and i < len(results[mode]):
                    node = results[mode][i]
                    radius = node.get('viz', {}).get('radius', 'N/A')
                    size_score = node.get('viz', {}).get('size_score', 'N/A')
                    row.append(f"{radius}px ({size_score:.3f})")
                else:
                    row.append('N/A')
            table_data.append(row)
        
        headers = ['Artist', 'Global Mode', 'Personal Mode', 'Adaptive Mode']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def display_glow_comparison(self, results: Dict[str, List[Dict]]):
        """Display glow intensity comparison across modes."""
        print("\\n✨ Glow Intensity Comparison")
        print("=" * 40)
        
        if not results:
            return
            
        first_mode = list(results.keys())[0]
        artists = [node['canonical_name'] for node in results[first_mode]]
        
        table_data = []
        for i, artist in enumerate(artists):
            row = [artist]
            for mode in ['global', 'personal', 'adaptive']:
                if mode in results and i < len(results[mode]):
                    node = results[mode][i]
                    glow = node.get('viz', {}).get('glow_intensity', 0)
                    if glow > 0:
                        row.append(f"{glow:.3f} ✨")
                    else:
                        row.append("0.000")
                else:
                    row.append('N/A')
            table_data.append(row)
        
        headers = ['Artist', 'Global Glow', 'Personal Glow', 'Adaptive Glow']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def display_metric_comparison(self, results: Dict[str, List[Dict]]):
        """Display sizing metrics comparison."""
        print("\\n📊 Sizing Metrics Comparison")
        print("=" * 40)
        
        if not results:
            return
            
        first_mode = list(results.keys())[0]
        artists = [node['canonical_name'] for node in results[first_mode]]
        
        table_data = []
        for i, artist in enumerate(artists):
            row = [artist]
            for mode in ['global', 'personal', 'adaptive']:
                if mode in results and i < len(results[mode]):
                    node = results[mode][i]
                    viz = node.get('viz', {})
                    metric = viz.get('sizing_metric', 'N/A')
                    value = viz.get('sizing_value', 'N/A')
                    
                    if mode == 'adaptive' and isinstance(value, str):
                        # Show abbreviated hybrid info
                        row.append(f"{metric[:10]}...")
                    else:
                        row.append(f"{metric}: {value}")
                else:
                    row.append('N/A')
            table_data.append(row)
        
        headers = ['Artist', 'Global Metric', 'Personal Metric', 'Adaptive Metric']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def detailed_node_properties_report(self):
        """Generate detailed report of node properties for a single mode."""
        print("🔍 Detailed Node Properties Report")
        print("=" * 40)
        
        # Get mode selection
        print("Select sizing mode:")
        print("  1. Global")
        print("  2. Personal") 
        print("  3. Adaptive")
        
        mode_choice = input("Enter choice (1-3): ")
        mode_map = {'1': 'global', '2': 'personal', '3': 'adaptive'}
        
        if mode_choice not in mode_map:
            print("❌ Invalid choice")
            return
            
        mode = mode_map[mode_choice]
        artist_count = int(input("Enter number of artists (5-20): "))
        
        try:
            self._ensure_project_context()
            
            print(f"\\n📊 Generating detailed report for {mode} mode...")
            network_data = create_enhanced_network_with_stable_ids(
                top_n_artists=artist_count,
                sizing_mode=mode
            )
            
            if not network_data or 'nodes' not in network_data:
                print("❌ Failed to generate network data")
                return
            
            nodes = network_data['nodes']
            
            # Save detailed report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(
                self.original_cwd,
                self.results_dir,
                f"detailed_report_{mode}_{artist_count}artists_{timestamp}.json"
            )
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(network_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Detailed report saved: {report_file}")
            
            # Display summary
            self.display_detailed_properties(nodes, mode)
            
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
        finally:
            self._restore_context()
    
    def display_detailed_properties(self, nodes: List[Dict], mode: str):
        """Display detailed properties for each node."""
        print(f"\\n📋 Detailed Properties - {mode.title()} Mode")
        print("=" * 50)
        
        for i, node in enumerate(nodes):
            print(f"\\n{i+1}. {node['canonical_name']}")
            print(f"   ID: {node['id']}")
            print(f"   Play Count: {node.get('play_count', 'N/A')}")
            print(f"   Spotify Popularity: {node.get('spotify_popularity', 'N/A')}")
            print(f"   Spotify Followers: {node.get('spotify_followers', 'N/A'):,}")
            print(f"   Last.fm Listeners: {node.get('lastfm_listeners', 'N/A'):,}")
            
            if 'viz' in node:
                viz = node['viz']
                print(f"   📊 Visualization Properties:")
                print(f"      Radius: {viz.get('radius', 'N/A')} px")
                print(f"      Size Score: {viz.get('size_score', 'N/A'):.3f}")
                print(f"      Glow Intensity: {viz.get('glow_intensity', 'N/A'):.3f}")
                print(f"      Color: {viz.get('color', 'N/A')}")
                print(f"      Primary Genre: {viz.get('primary_genre', 'N/A')}")
                print(f"      Sizing Metric: {viz.get('sizing_metric', 'N/A')}")
                print(f"      Sizing Value: {viz.get('sizing_value', 'N/A')}")
                
                if 'personal_weight' in viz:
                    print(f"      Personal Weight: {viz['personal_weight']:.3f}")
                    print(f"      Global Weight: {viz['global_weight']:.3f}")
    
    def personal_vs_global_weight_analysis(self):
        """Analyze how personal vs global weighting affects adaptive mode."""
        print("⚖️  Personal vs Global Weight Analysis")
        print("=" * 40)
        
        artist_count = int(input("Enter number of artists for analysis (5-20): "))
        
        try:
            self._ensure_project_context()
            
            print(f"\\n📊 Generating adaptive mode data for weight analysis...")
            network_data = create_enhanced_network_with_stable_ids(
                top_n_artists=artist_count,
                sizing_mode='adaptive'
            )
            
            if not network_data or 'nodes' not in network_data:
                print("❌ Failed to generate network data")
                return
            
            nodes = network_data['nodes']
            
            # Analyze weighting
            print(f"\\n⚖️  Weighting Analysis Results")
            print("=" * 30)
            
            table_data = []
            for node in nodes:
                viz = node.get('viz', {})
                if 'personal_weight' in viz:
                    personal_weight = viz['personal_weight']
                    global_weight = viz['global_weight']
                    size_score = viz.get('size_score', 0)
                    
                    # Calculate what the score would be with different weightings
                    play_count = node.get('play_count', 0)
                    spotify_pop = node.get('spotify_popularity', 0)
                    
                    table_data.append([
                        node['canonical_name'][:15],
                        f"{personal_weight:.2f}",
                        f"{global_weight:.2f}",
                        f"{size_score:.3f}",
                        f"{play_count}",
                        f"{spotify_pop}"
                    ])
            
            headers = ['Artist', 'Personal W.', 'Global W.', 'Final Score', 'Plays', 'Popularity']
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
            
            # Show weighting explanation
            if nodes and 'viz' in nodes[0] and 'personal_weight' in nodes[0]['viz']:
                weight_info = nodes[0]['viz']['personal_weight']
                print(f"\\n📝 Weighting Explanation:")
                print(f"   Personal Weight: {weight_info:.3f} (Based on user's total listening data)")
                print(f"   Global Weight: {1-weight_info:.3f}")
                print(f"   This user is classified as: {'Power User' if weight_info > 0.6 else 'Casual User'}")
            
        except Exception as e:
            print(f"❌ Weight analysis failed: {e}")
        finally:
            self._restore_context()
    
    def view_previous_results(self):
        """View previously generated results."""
        print("📂 Previous Results")
        print("=" * 20)
        
        # List available result files
        result_files = [f for f in os.listdir(self.results_dir) if f.endswith('.json')]
        
        if not result_files:
            print("No previous results found.")
            return
        
        result_files.sort(reverse=True)  # Most recent first
        
        print("Available result files:")
        for i, filename in enumerate(result_files[:10]):  # Show last 10
            print(f"  {i+1}. {filename}")
        
        if len(result_files) > 10:
            print(f"  ... and {len(result_files) - 10} more files")
        
        try:
            choice = int(input("\\nSelect file to view (1-10): "))
            if 1 <= choice <= min(10, len(result_files)):
                selected_file = result_files[choice - 1]
                filepath = os.path.join(self.results_dir, selected_file)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"\\n📄 Contents of {selected_file}:")
                print("=" * 40)
                
                if 'modes' in data:
                    # Mode comparison file
                    print(f"Comparison of {len(data['modes'])} modes with {data['artist_count']} artists")
                    print(f"Generated: {data['timestamp']}")
                    for mode, nodes in data['modes'].items():
                        print(f"  {mode}: {len(nodes)} nodes")
                else:
                    # Single mode file
                    nodes = data.get('nodes', [])
                    print(f"Single mode analysis: {len(nodes)} nodes")
                    if nodes and 'viz' in nodes[0]:
                        mode = nodes[0]['viz'].get('sizing_mode', 'unknown')
                        print(f"Mode: {mode}")
                        
        except (ValueError, IndexError, FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Error viewing file: {e}")
    
    def clean_results_directory(self):
        """Clean the results directory."""
        result_files = [f for f in os.listdir(self.results_dir) if f.endswith('.json')]
        
        if not result_files:
            print("No result files to clean.")
            return
        
        print(f"Found {len(result_files)} result files.")
        confirm = input("Delete all result files? (y/N): ")
        
        if confirm.lower() == 'y':
            for filename in result_files:
                filepath = os.path.join(self.results_dir, filename)
                os.remove(filepath)
            print(f"✅ Cleaned {len(result_files)} files.")
        else:
            print("❌ Cancelled.")
    
    def run_interactive(self):
        """Run the interactive analyzer."""
        while True:
            self.display_menu()
            choice = self.get_user_choice()
            
            if choice == 0:
                print("👋 Goodbye!")
                break
            elif choice == 1:
                self.compare_all_sizing_modes(5)
            elif choice == 2:
                self.compare_all_sizing_modes(10)
            elif choice == 3:
                self.compare_all_sizing_modes(20)
            elif choice == 4:
                # Single mode analysis
                print("\\n🎯 Single Mode Analysis")
                print("Select mode: 1=Global, 2=Personal, 3=Adaptive")
                mode_choice = input("Mode: ")
                mode_map = {'1': 'global', '2': 'personal', '3': 'adaptive'}
                if mode_choice in mode_map:
                    artist_count = int(input("Artist count: "))
                    self.compare_all_sizing_modes(artist_count)  # Will only show one mode
                else:
                    print("❌ Invalid mode choice")
            elif choice == 5:
                self.detailed_node_properties_report()
            elif choice == 6:
                # Glow effect analysis - compare all modes to see glow differences
                print("\\n✨ Glow Effect Analysis")
                artist_count = int(input("Enter number of artists (5-20): "))
                self.compare_all_sizing_modes(artist_count)
            elif choice == 7:
                self.personal_vs_global_weight_analysis()
            elif choice == 8:
                self.view_previous_results()
            elif choice == 9:
                self.clean_results_directory()
            else:
                print("❌ Invalid choice. Please try again.")
            
            input("\\nPress Enter to continue...")


if __name__ == "__main__":
    analyzer = NodeMetricsAnalyzer()
    analyzer.run_interactive()