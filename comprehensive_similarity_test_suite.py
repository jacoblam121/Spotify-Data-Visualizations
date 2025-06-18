#!/usr/bin/env python3
"""
Comprehensive Similarity Test Suite

A comprehensive test suite for validating the multi-API similarity system
including Last.fm, Deezer, and MusicBrainz integration with edge weighting.
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Import the components to test
try:
    from ultimate_similarity_system import UltimateSimilaritySystem
    from comprehensive_edge_weighting_system import ComprehensiveEdgeWeighter
    from lastfm_utils import LastfmAPI
    from cache_manager import CacheManager
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    print("Make sure all required files are in the current directory")
    exit(1)


@dataclass
class TestResult:
    """Results from a single test case."""
    artist: str
    success: bool
    api_coverage: Dict[str, int]
    connection_counts: Dict[str, int] 
    edge_weights: List[Dict[str, Any]]
    issues: List[str]
    execution_time: float


class ComprehensiveSimilarityTestSuite:
    """Test suite for comprehensive similarity analysis."""
    
    def __init__(self):
        """Initialize the test suite with all required components."""
        print("Initializing Comprehensive Similarity Test Suite...")
        
        # Load configuration first
        try:
            from config_loader import AppConfig
            self.config = AppConfig()
        except ImportError:
            print("Warning: Could not load AppConfig, using defaults")
            self.config = None
        
        # Initialize core components with proper error handling
        try:
            if self.config:
                self.similarity_system = UltimateSimilaritySystem(self.config)
            else:
                self.similarity_system = UltimateSimilaritySystem()
        except Exception as e:
            print(f"Warning: Could not initialize UltimateSimilaritySystem: {e}")
            self.similarity_system = None
            
        try:
            self.edge_weighter = ComprehensiveEdgeWeighter()
        except Exception as e:
            print(f"Warning: Could not initialize ComprehensiveEdgeWeighter: {e}")
            self.edge_weighter = None
            
        try:
            if self.config:
                self.cache_manager = CacheManager(self.config)
            else:
                self.cache_manager = CacheManager()
        except Exception as e:
            print(f"Warning: Could not initialize CacheManager: {e}")
            self.cache_manager = None
        
        # Test configuration
        self.test_artists = [
            "Taylor Swift",
            "BTS", 
            "IU",
            "The Beatles",
            "Billie Eilish",
            "Ed Sheeran",
            "Drake",
            "Ariana Grande"
        ]
        
        print(f"Test suite initialized with {len(self.test_artists)} test artists")
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run the complete test suite."""
        print("\n" + "="*60)
        print("RUNNING COMPREHENSIVE SIMILARITY TEST SUITE")
        print("="*60)
        
        start_time = time.time()
        
        # Initialize results tracking
        overall_results = {
            'total_test_cases': len(self.test_artists),
            'passed': 0,
            'failed': 0,
            'test_results': [],
            'api_performance': {},
            'edge_weighting_stats': {},
            'issues_found': [],
            'execution_time': 0,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Run tests for each artist
        for i, artist in enumerate(self.test_artists, 1):
            print(f"\n[{i}/{len(self.test_artists)}] Testing: {artist}")
            print("-" * 40)
            
            test_result = self._test_single_artist(artist)
            
            # Update overall results
            if test_result.success:
                overall_results['passed'] += 1
                print(f"  RESULT: PASS")
            else:
                overall_results['failed'] += 1
                print(f"  RESULT: FAIL")
            
            overall_results['test_results'].append({
                'artist': test_result.artist,
                'success': test_result.success,
                'api_coverage': test_result.api_coverage,
                'connection_counts': test_result.connection_counts,
                'edge_weights': test_result.edge_weights,
                'issues': test_result.issues,
                'execution_time': test_result.execution_time
            })
            
            # Update performance statistics
            self._update_performance_stats(overall_results, test_result)
            
            # Collect issues
            overall_results['issues_found'].extend(test_result.issues)
        
        # Calculate total execution time
        overall_results['execution_time'] = time.time() - start_time
        
        # Print final results
        self._print_final_results(overall_results)
        
        return overall_results
    
    def _test_single_artist(self, artist: str) -> TestResult:
        """Test similarity fetching and edge weighting for a single artist."""
        start_time = time.time()
        
        # Initialize test result
        result = TestResult(
            artist=artist,
            success=False,
            api_coverage={},
            connection_counts={},
            edge_weights=[],
            issues=[],
            execution_time=0
        )
        
        try:
            print(f"  Fetching similarity data for: {artist}")
            
            # Test multi-API similarity fetching
            api_data = self._test_multi_api_fetching(artist, result)
            
            # Test edge weighting if we have data
            if any(connections for connections in api_data.values()):
                edge_results = self._test_edge_weighting_for_artist(artist, api_data)
                result.edge_weights = edge_results['weights']
                result.issues.extend(edge_results['issues'])
                
                # Consider test successful if we got connections from at least one API
                result.success = True
            else:
                result.issues.append(f"No connections found for {artist} from any API")
                result.success = False
                
        except Exception as e:
            result.issues.append(f"Critical error testing {artist}: {e}")
            result.success = False
            print(f"  ERROR: {e}")
        
        result.execution_time = time.time() - start_time
        print(f"  Completed in {result.execution_time:.2f}s")
        
        return result
    
    def _test_multi_api_fetching(self, artist: str, result: TestResult) -> Dict[str, List]:
        """Test fetching using the UltimateSimilaritySystem aggregated API."""
        api_data = {}
        
        if not self.similarity_system:
            result.issues.append("UltimateSimilaritySystem not available")
            return api_data
        
        try:
            # Use the main aggregated method
            all_results = self.similarity_system.get_ultimate_similar_artists(artist, limit=10)
            
            # Group results by source
            source_groups = {}
            for artist_result in all_results:
                source = artist_result.get('source', 'unknown')
                if source not in source_groups:
                    source_groups[source] = []
                source_groups[source].append(artist_result)
            
            # Update result tracking for each source found
            for source, source_results in source_groups.items():
                result.api_coverage[source] = len(source_results)
                result.connection_counts[source] = len(source_results)
                api_data[source] = source_results
                print(f"    {source.capitalize()}: {len(source_results)} similar artists")
            
            # If no results, record that
            if not all_results:
                result.issues.append(f"No similarity results found for {artist}")
                print(f"    No results found for {artist}")
                
        except Exception as e:
            result.issues.append(f"Ultimate similarity system error for {artist}: {e}")
            print(f"    ERROR: {e}")
            
            # Fallback: try individual APIs if they're accessible
            self._try_individual_apis(artist, result, api_data)
        
        return api_data
    
    def _try_individual_apis(self, artist: str, result: TestResult, api_data: Dict[str, List]):
        """Fallback method to try individual APIs if available."""
        # Try Last.fm API if available
        if hasattr(self.similarity_system, 'lastfm_api'):
            try:
                lastfm_results = self.similarity_system.lastfm_api.get_similar_artists(artist, limit=10)
                result.api_coverage['lastfm'] = len(lastfm_results)
                result.connection_counts['lastfm'] = len(lastfm_results)
                api_data['lastfm'] = lastfm_results
                print(f"    Last.fm (fallback): {len(lastfm_results)} similar artists")
                
            except Exception as e:
                result.issues.append(f"Last.fm fallback error for {artist}: {e}")
                print(f"    Last.fm (fallback): ERROR - {e}")
        
        # Try Deezer API if available
        if hasattr(self.similarity_system, 'deezer_api'):
            try:
                # Try different possible method names
                deezer_method = None
                if hasattr(self.similarity_system.deezer_api, 'get_similar_artists'):
                    deezer_method = self.similarity_system.deezer_api.get_similar_artists
                elif hasattr(self.similarity_system.deezer_api, 'get_related_artists'):
                    deezer_method = self.similarity_system.deezer_api.get_related_artists
                
                if deezer_method:
                    deezer_results = deezer_method(artist, limit=10)
                    result.api_coverage['deezer'] = len(deezer_results)
                    result.connection_counts['deezer'] = len(deezer_results)
                    api_data['deezer'] = deezer_results
                    print(f"    Deezer (fallback): {len(deezer_results)} related artists")
                else:
                    print(f"    Deezer (fallback): No suitable method found")
                    
            except Exception as e:
                result.issues.append(f"Deezer fallback error for {artist}: {e}")
                print(f"    Deezer (fallback): ERROR - {e}")
        
        # Try MusicBrainz if available  
        if hasattr(self.similarity_system, 'musicbrainz_api'):
            try:
                # Try different possible method names
                mb_method = None
                if hasattr(self.similarity_system.musicbrainz_api, 'get_similar_artists'):
                    mb_method = self.similarity_system.musicbrainz_api.get_similar_artists
                elif hasattr(self.similarity_system.musicbrainz_api, 'get_relationship_based_similar_artists'):
                    mb_method = self.similarity_system.musicbrainz_api.get_relationship_based_similar_artists
                
                if mb_method:
                    mb_results = mb_method(artist, limit=10)
                    result.api_coverage['musicbrainz'] = len(mb_results)
                    result.connection_counts['musicbrainz'] = len(mb_results)
                    api_data['musicbrainz'] = mb_results
                    print(f"    MusicBrainz (fallback): {len(mb_results)} relationships")
                else:
                    print(f"    MusicBrainz (fallback): No suitable method found")
                    
            except Exception as e:
                result.issues.append(f"MusicBrainz fallback error for {artist}: {e}")
                print(f"    MusicBrainz (fallback): ERROR - {e}")
    
    def _test_edge_weighting_for_artist(self, artist: str, api_data: Dict) -> Dict:
        """Test edge weighting for an artist's connections."""
        results = {
            'weights': [],
            'issues': []
        }
        
        if not self.edge_weighter:
            results['issues'].append("ComprehensiveEdgeWeighter not available")
            return results
        
        try:
            # Simulate edge creation for top connections from each API
            for api_name, connections in api_data.items():
                if connections:
                    # Test edge weighting with top connection
                    top_connection = connections[0]
                    
                    # Handle different possible data structures
                    target_artist = None
                    if isinstance(top_connection, dict):
                        target_artist = top_connection.get('name') or top_connection.get('artist')
                    elif isinstance(top_connection, str):
                        target_artist = top_connection
                    
                    if not target_artist:
                        results['issues'].append(f"Could not extract target artist from {api_name} data")
                        continue
                    
                    # Create source data in expected format
                    source_data = {api_name: [top_connection]}
                    
                    # Test edge creation
                    try:
                        edge = self.edge_weighter.create_weighted_edge(
                            artist, target_artist, source_data
                        )
                        
                        if edge:
                            weight_info = {
                                'source_artist': artist,
                                'target_artist': target_artist,
                                'similarity': getattr(edge, 'similarity', 0.0),
                                'distance': getattr(edge, 'distance', 0.0),
                                'confidence': getattr(edge, 'confidence', 0.0),
                                'is_factual': getattr(edge, 'is_factual', False),
                                'sources': [getattr(c, 'source', 'unknown') for c in getattr(edge, 'contributions', [])],
                                'fusion_method': getattr(edge, 'fusion_method', 'unknown')
                            }
                            results['weights'].append(weight_info)
                            
                            print(f"         Edge: {target_artist} (sim={weight_info['similarity']:.2f}, dist={weight_info['distance']:.1f})")
                        else:
                            results['issues'].append(f"Failed to create edge: {artist} -> {target_artist}")
                            
                    except Exception as edge_error:
                        results['issues'].append(f"Edge creation error for {artist} -> {target_artist}: {edge_error}")
                        
        except Exception as e:
            results['issues'].append(f"Edge weighting error for {artist}: {e}")
        
        return results
    
    def _update_performance_stats(self, overall_results: Dict, test_result: TestResult):
        """Update overall performance statistics."""
        # API performance
        for api, count in test_result.api_coverage.items():
            if api not in overall_results['api_performance']:
                overall_results['api_performance'][api] = {'total_connections': 0, 'artists_with_data': 0}
            
            overall_results['api_performance'][api]['total_connections'] += count
            if count > 0:
                overall_results['api_performance'][api]['artists_with_data'] += 1
        
        # Edge weighting stats
        if test_result.edge_weights:
            if 'total_edges' not in overall_results['edge_weighting_stats']:
                overall_results['edge_weighting_stats'] = {
                    'total_edges': 0,
                    'factual_edges': 0,
                    'avg_similarity': 0.0,
                    'avg_confidence': 0.0,
                    'fusion_methods': {}
                }
            
            stats = overall_results['edge_weighting_stats']
            
            for weight in test_result.edge_weights:
                stats['total_edges'] += 1
                
                if weight['is_factual']:
                    stats['factual_edges'] += 1
                
                # Running average calculation
                n = stats['total_edges']
                stats['avg_similarity'] = ((stats['avg_similarity'] * (n-1)) + weight['similarity']) / n
                stats['avg_confidence'] = ((stats['avg_confidence'] * (n-1)) + weight['confidence']) / n
                
                # Fusion method tracking
                method = weight['fusion_method']
                if method not in stats['fusion_methods']:
                    stats['fusion_methods'][method] = 0
                stats['fusion_methods'][method] += 1
    
    def _print_final_results(self, results: Dict):
        """Print comprehensive final results."""
        print(f"\n[CHART] FINAL TEST SUITE RESULTS")
        print("=" * 60)
        
        # Overall success rate
        total = results['total_test_cases']
        passed = results['passed']
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"\n[TARGET] Overall Results:")
        print(f"   Test cases: {passed}/{total} passed ({success_rate:.1f}% success rate)")
        
        if results['failed'] > 0:
            print(f"   [X] {results['failed']} test case(s) failed")
        
        # API Performance
        print(f"\n[PLUG] API Performance:")
        for api, stats in results['api_performance'].items():
            total_conn = stats['total_connections']
            artists_with_data = stats['artists_with_data']
            print(f"   {api.capitalize()}: {total_conn} total connections, {artists_with_data} artists with data")
        
        # Edge Weighting Statistics
        if results['edge_weighting_stats']:
            stats = results['edge_weighting_stats']
            print(f"\n[BALANCE] Edge Weighting Statistics:")
            print(f"   Total edges created: {stats['total_edges']}")
            print(f"   Factual edges: {stats['factual_edges']} ({(stats['factual_edges']/stats['total_edges']*100):.1f}%)")
            print(f"   Average similarity: {stats['avg_similarity']:.3f}")
            print(f"   Average confidence: {stats['avg_confidence']:.3f}")
            
            print(f"\n   Fusion methods used:")
            for method, count in stats['fusion_methods'].items():
                percentage = (count / stats['total_edges']) * 100
                print(f"      {method}: {count} ({percentage:.1f}%)")
        
        # Issues Summary
        if results['issues_found']:
            print(f"\n[WARNING] Issues Found ({len(results['issues_found'])}):") 
            for issue in results['issues_found'][:10]:  # Show first 10
                print(f"   - {issue}")
            
            if len(results['issues_found']) > 10:
                print(f"   ... and {len(results['issues_found']) - 10} more issues")
        else:
            print(f"\n[CHECK] No issues found!")


def run_manual_test_suite():
    """Entry point for running the manual test suite."""
    try:
        test_suite = ComprehensiveSimilarityTestSuite()
        results = test_suite.run_comprehensive_tests()
        
        # Save results to file
        output_file = "similarity_test_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n[DISK] Detailed results saved to: {output_file}")
        
        return results
        
    except Exception as e:
        print(f"[BOMB] Test suite failed to run: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    run_manual_test_suite()