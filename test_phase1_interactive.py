#!/usr/bin/env python3
"""
Interactive Phase 1 Network Test
================================
Interactive test menu for Phase 1 comprehensive network generation.
Allows user to choose network size and inspect results in detail.
"""

import time
import json
from pathlib import Path
import sys

# Add project modules
sys.path.insert(0, str(Path(__file__).parent))

from network_utils import ArtistNetworkAnalyzer, prepare_dataframe_for_network_analysis
from data_processor import clean_and_filter_data
from config_loader import AppConfig

def print_header(title: str, char: str = "="):
    """Print a formatted header."""
    print(f"\n{char * len(title)}")
    print(title)
    print(f"{char * len(title)}")

def print_section(title: str, emoji: str = "🧪"):
    """Print a section header."""
    print(f"\n{emoji} {title}")
    print("-" * (len(title) + 3))

def get_user_choice():
    """Get user's choice for number of artists to test."""
    print_header("🎯 Phase 1 Interactive Network Test")
    print("\nChoose network size to test:")
    print("1. Small (10 artists) - Quick test")
    print("2. Medium (25 artists) - Standard test")  
    print("3. Large (50 artists) - Comprehensive test")
    print("4. Extra Large (100 artists) - Full scale test")
    print("5. Custom - Enter your own number")
    print("6. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                return 10
            elif choice == "2":
                return 25
            elif choice == "3":
                return 50
            elif choice == "4":
                return 100
            elif choice == "5":
                try:
                    custom = int(input("Enter number of artists (5-200): "))
                    if 5 <= custom <= 200:
                        return custom
                    else:
                        print("❌ Please enter a number between 5 and 200")
                except ValueError:
                    print("❌ Please enter a valid number")
            elif choice == "6":
                print("👋 Goodbye!")
                sys.exit(0)
            else:
                print("❌ Please enter a number between 1 and 6")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)

def get_threshold_choice():
    """Get user's choice for similarity threshold."""
    print("\nChoose similarity threshold:")
    print("1. Low (0.1) - More edges, lower quality")
    print("2. Medium (0.2) - Balanced")
    print("3. High (0.3) - Fewer edges, higher quality")
    print("4. Custom")
    
    while True:
        try:
            choice = input("Enter threshold choice (1-4): ").strip()
            
            if choice == "1":
                return 0.1
            elif choice == "2":
                return 0.2
            elif choice == "3":
                return 0.3
            elif choice == "4":
                try:
                    custom = float(input("Enter threshold (0.05-0.5): "))
                    if 0.05 <= custom <= 0.5:
                        return custom
                    else:
                        print("❌ Please enter a number between 0.05 and 0.5")
                except ValueError:
                    print("❌ Please enter a valid number")
            else:
                print("❌ Please enter a number between 1 and 4")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            sys.exit(0)

def analyze_network_comprehensive(network_data):
    """Enhanced network analysis with multi-source edge detection."""
    # Import centralized network analyzer for consistent validation
    from network_utils import ArtistNetworkAnalyzer
    from config_loader import AppConfig
    
    # Use centralized validation (single source of truth)
    config = AppConfig('configurations.txt')
    analyzer = ArtistNetworkAnalyzer(config)
    validation = analyzer.validate_network_data(network_data)
    
    nodes = network_data.get('nodes', [])
    edges = network_data.get('edges', [])
    
    # Node analysis using centralized accessors
    total_nodes = validation['total_nodes']
    nodes_with_genre = validation['nodes_with_genre_classification']
    
    # Count data source coverage
    lastfm_coverage = sum(1 for n in nodes if n.get('lastfm_listeners', 0) > 0)
    spotify_coverage = sum(1 for n in nodes if n.get('spotify_followers', 0) > 0)
    
    # Edge analysis with enhanced multi-source detection
    total_edges = len(edges)
    
    # Check for multi-source edges using multiple possible indicators
    multi_source_edges = 0
    confidence_distribution = {'high': 0, 'medium': 0, 'low': 0}
    factual_edges = 0
    algorithmic_edges = 0
    fusion_methods = {}
    source_combinations = {}
    
    for edge in edges:
        # Multi-source detection (check multiple possible indicators)
        is_multi_source = False
        
        # Method 1: Check for 'sources' attribute
        if 'sources' in edge and isinstance(edge['sources'], (list, set)) and len(edge['sources']) > 1:
            is_multi_source = True
        
        # Method 2: Check for source_count attribute
        elif edge.get('source_count', 1) > 1:
            is_multi_source = True
            
        # Method 3: Check fusion method for multi-source indicators
        elif 'multi' in str(edge.get('fusion_method', '')).lower():
            is_multi_source = True
            
        # Method 4: Check if multiple similarity scores are present
        elif (edge.get('lastfm_similarity', 0) > 0 and 
              edge.get('deezer_similarity', 0) > 0):
            is_multi_source = True
            
        if is_multi_source:
            multi_source_edges += 1
        
        # Confidence analysis
        confidence = edge.get('confidence', edge.get('weight', 0))
        if confidence >= 0.8:
            confidence_distribution['high'] += 1
        elif confidence >= 0.5:
            confidence_distribution['medium'] += 1
        else:
            confidence_distribution['low'] += 1
        
        # Factual vs algorithmic
        if edge.get('is_factual', False):
            factual_edges += 1
        else:
            algorithmic_edges += 1
            
        # Fusion method tracking
        method = edge.get('fusion_method', 'unknown')
        fusion_methods[method] = fusion_methods.get(method, 0) + 1
        
        # Source combination tracking
        source = edge.get('source', 'unknown')
        source_combinations[source] = source_combinations.get(source, 0) + 1
    
    # Genre analysis using centralized distribution
    genre_counts = validation['genre_distribution']
    
    # Network metrics
    max_possible_edges = total_nodes * (total_nodes - 1) // 2
    density = (total_edges / max_possible_edges) if max_possible_edges > 0 else 0
    avg_degree = (2 * total_edges / total_nodes) if total_nodes > 0 else 0
    
    return {
        'node_stats': {
            'total_nodes': total_nodes,
            'nodes_with_genre': nodes_with_genre,
            'genre_distribution': genre_counts,
            'data_coverage': {
                'lastfm': lastfm_coverage,
                'spotify': spotify_coverage,
                'both': min(lastfm_coverage, spotify_coverage)
            }
        },
        'edge_stats': {
            'total_edges': total_edges,
            'multi_source_edges': multi_source_edges,
            'confidence_distribution': confidence_distribution,
            'factual_edges': factual_edges,
            'algorithmic_edges': algorithmic_edges,
            'fusion_methods': fusion_methods,
            'source_combinations': source_combinations
        },
        'network_metrics': {
            'density': density,
            'average_degree': avg_degree,
            'max_possible_edges': max_possible_edges,
            'coverage_percentage': (total_edges / max_possible_edges * 100) if max_possible_edges > 0 else 0
        }
    }

def print_analysis_results(analysis, network_size, threshold, generation_time):
    """Print comprehensive analysis results."""
    
    print_section("Test Configuration", "⚙️")
    print(f"Network size: {network_size} artists")
    print(f"Similarity threshold: {threshold}")
    print(f"Generation time: {generation_time:.1f} seconds")
    
    print_section("Node Analysis", "📊")
    node_stats = analysis['node_stats']
    print(f"Total nodes: {node_stats['total_nodes']}")
    print(f"Nodes with genre classification: {node_stats['nodes_with_genre']}")
    print(f"Last.fm coverage: {node_stats['data_coverage']['lastfm']}")
    print(f"Spotify coverage: {node_stats['data_coverage']['spotify']}")
    print(f"Dual API coverage: {node_stats['data_coverage']['both']}")
    
    print(f"\n📈 Genre distribution:")
    for genre, count in node_stats['genre_distribution'].items():
        print(f"   {genre}: {count} artists")
    
    print_section("Edge Analysis", "🕸️")
    edge_stats = analysis['edge_stats']
    print(f"Total edges: {edge_stats['total_edges']}")
    print(f"Multi-source edges: {edge_stats['multi_source_edges']}")
    print(f"High confidence (≥0.8): {edge_stats['confidence_distribution']['high']}")
    print(f"Medium confidence (0.5-0.8): {edge_stats['confidence_distribution']['medium']}")
    print(f"Low confidence (<0.5): {edge_stats['confidence_distribution']['low']}")
    print(f"Factual relationships: {edge_stats['factual_edges']}")
    print(f"Algorithmic relationships: {edge_stats['algorithmic_edges']}")
    
    print(f"\n⚖️ Fusion methods:")
    for method, count in edge_stats['fusion_methods'].items():
        print(f"   {method}: {count} edges")
        
    print(f"\n🔗 Source combinations:")
    for source, count in edge_stats['source_combinations'].items():
        print(f"   {source}: {count} edges")
    
    print_section("Network Metrics", "📈")
    metrics = analysis['network_metrics']
    print(f"Network density: {metrics['density']:.3f}")
    print(f"Average degree: {metrics['average_degree']:.1f}")
    print(f"Coverage: {metrics['coverage_percentage']:.1f}% of possible edges")
    print(f"Max possible edges: {metrics['max_possible_edges']}")
    
    print_section("Validation Results", "✅")
    
    # Enhanced validation with detailed feedback and failure analysis
    classification_success_rate = node_stats['nodes_with_genre'] / node_stats['total_nodes'] if node_stats['total_nodes'] > 0 else 0
    
    # Log detailed classification performance for monitoring
    print(f"   📊 Genre classification: {node_stats['nodes_with_genre']}/{node_stats['total_nodes']} ({classification_success_rate:.1%})")
    
    # Baseline-aware threshold (95% based on current 98% performance with 3% buffer)
    GENRE_CLASSIFICATION_THRESHOLD = 0.95  # Sensitive enough to catch regressions
    
    validations = {
        "Genre classification": classification_success_rate >= GENRE_CLASSIFICATION_THRESHOLD,
        "Multi-source detection": edge_stats['multi_source_edges'] > 0,
        "Edge generation": edge_stats['total_edges'] > 0,
        "API diversity": len(edge_stats['source_combinations']) >= 2,
        "Confidence scoring": sum(edge_stats['confidence_distribution'].values()) == edge_stats['total_edges']
    }
    
    # Enhanced failure reporting for debugging
    if classification_success_rate < GENRE_CLASSIFICATION_THRESHOLD:
        failed_nodes = [n['name'] for n in network_data.get('nodes', []) 
                       if n.get('cluster_genre', 'other') == 'other'][:3]  # Show first 3 failures
        print(f"   ⚠️  Classification below {GENRE_CLASSIFICATION_THRESHOLD:.0%} threshold. Failed nodes: {failed_nodes}")
        if len(failed_nodes) > 3:
            total_failed = len([n for n in network_data.get('nodes', []) if n.get('cluster_genre', 'other') == 'other'])
            print(f"   ⚠️  ... and {total_failed - 3} more")
    
    all_passed = True
    for test_name, passed in validations.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}")
        if not passed:
            all_passed = False
    
    overall_status = "✅ PASSED" if all_passed else "⚠️ SOME ISSUES"
    print(f"\n🎯 Overall Phase 1 Status: {overall_status}")
    
    if not all_passed:
        print("\n💡 Issues detected:")
        if not validations["Multi-source detection"]:
            print("   • Multi-source edges: Check edge attributes for source fusion indicators")
        if not validations["API diversity"]:
            print("   • API diversity: Ensure multiple APIs are contributing to edge creation")

def run_network_test(num_artists, threshold):
    """Run the network generation test."""
    
    print_header(f"🚀 Running Phase 1 Test: {num_artists} Artists")
    
    try:
        # Initialize
        config = AppConfig("configurations.txt")
        analyzer = ArtistNetworkAnalyzer(config)
        
        print_section("Data Loading", "📂")
        print("Loading listening history data...")
        raw_df = clean_and_filter_data(config)
        df = prepare_dataframe_for_network_analysis(raw_df)
        
        print(f"✅ Loaded {len(df)} listening events")
        print(f"📊 Unique artists: {df['artist'].nunique()}")
        
        print_section("Network Generation", "🌟")
        print(f"Creating network with {num_artists} top artists...")
        print(f"Similarity threshold: {threshold}")
        print(f"Expected pairs: {num_artists * (num_artists - 1) // 2}")
        
        start_time = time.time()
        
        network_data = analyzer.create_network_data(
            df,
            top_n_artists=num_artists,
            min_plays_threshold=3,
            min_similarity_threshold=threshold
        )
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        print_section("Analysis", "🔍")
        analysis = analyze_network_comprehensive(network_data)
        
        print_analysis_results(analysis, num_artists, threshold, generation_time)
        
        # Export results
        print_section("Export", "💾")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"phase1_test_{num_artists}artists_{timestamp}.json"
        
        export_data = {
            'test_config': {
                'num_artists': num_artists,
                'threshold': threshold,
                'generation_time': generation_time,
                'timestamp': timestamp
            },
            'analysis': analysis,
            'network_data': network_data
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        file_size = Path(filename).stat().st_size / 1024  # KB
        print(f"📄 Results exported to: {filename}")
        print(f"📊 File size: {file_size:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main interactive test function."""
    while True:
        try:
            num_artists = get_user_choice()
            threshold = get_threshold_choice()
            
            success = run_network_test(num_artists, threshold)
            
            if success:
                print_section("Next Steps", "🎯")
                print("✅ Phase 1 test completed successfully!")
                print("🚀 Ready to proceed to Phase 2: D3.js Visualization")
            
            # Ask if user wants to run another test
            print("\n" + "="*50)
            again = input("Run another test? (y/n): ").strip().lower()
            if again not in ['y', 'yes']:
                break
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
    
    print("\n🎉 Testing session complete!")

if __name__ == "__main__":
    main()