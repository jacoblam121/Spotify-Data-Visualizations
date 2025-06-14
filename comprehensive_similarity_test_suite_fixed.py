#!/usr/bin/env python3
"""
Comprehensive Similarity Test Suite
====================================
Manual test suite for the complete multi-source artist similarity system.

Tests all components:
- Last.fm API integration
- Deezer API integration  
- MusicBrainz relationship parsing
- Edge weighting and fusion
- End-to-end network generation

Covers edge cases, error handling, and performance validation.
"""

import logging
import time
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

# Add project modules
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI
from deezer_similarity_api import DeezerSimilarityAPI
from musicbrainz_similarity_api import MusicBrainzSimilarityAPI
from edge_weighting_test import ComprehensiveEdgeWeighter, EdgeWeightingConfig

logger = logging.getLogger(__name__)

class ComprehensiveSimilarityTestSuite:
    """Comprehensive test suite for artist similarity system."""
    
    def __init__(self):
        """Initialize test suite with all APIs."""
        print("🧪 Initializing Comprehensive Similarity Test Suite")
        print("=" * 60)
        
        try:
            # Load configuration
            self.config = AppConfig("configurations.txt")
            lastfm_config = self.config.get_lastfm_config()
            
            # Initialize APIs
            self.lastfm_api = None
            if lastfm_config['enabled'] and lastfm_config['api_key']:
                self.lastfm_api = LastfmAPI(
                    lastfm_config['api_key'],
                    lastfm_config['api_secret'],
                    lastfm_config['cache_dir']
                )
                print("✅ Last.fm API initialized")
            else:
                print("❌ Last.fm API not available")
            
            self.deezer_api = DeezerSimilarityAPI()
            print("✅ Deezer API initialized")
            
            self.musicbrainz_api = MusicBrainzSimilarityAPI()
            print("✅ MusicBrainz API initialized")
            
            # Initialize edge weighter
            self.edge_weighter = ComprehensiveEdgeWeighter()
            print("✅ Edge weighting system initialized")
            
            # Test cases covering various scenarios
            self.test_cases = self._define_test_cases()
            print(f"✅ {len(self.test_cases)} test cases defined")
            
        except Exception as e:
            print(f"❌ Initialization error: {e}")
            raise
    
    def _define_test_cases(self) -> List[Dict]:
        """Define comprehensive test cases."""
        return [
            # Popular Western artists (should work well across all APIs)
            {
                'name': 'Popular Western Artists',
                'artists': ['Taylor Swift', 'Ed Sheeran', 'Adele'],
                'expected_sources': ['lastfm', 'deezer'],
                'min_connections': 5,
                'description': 'High-profile artists with strong API coverage'
            },
            
            # Classic rock (good MusicBrainz coverage)
            {
                'name': 'Classic Rock Bands',
                'artists': ['The Beatles', 'Led Zeppelin', 'Pink Floyd'],
                'expected_sources': ['lastfm', 'deezer', 'musicbrainz'],
                'min_connections': 8,
                'description': 'Classic bands with rich relationship data'
            },
            
            # K-pop groups (Deezer strength, potential MusicBrainz coverage)
            {
                'name': 'K-pop Groups',
                'artists': ['BTS', 'TWICE', 'NewJeans', 'IVE'],
                'expected_sources': ['deezer'],  # May have musicbrainz
                'min_connections': 3,
                'description': 'Modern K-pop with varying API coverage'
            },
            
            # Individual K-pop artists (challenging case)
            {
                'name': 'K-pop Soloists',
                'artists': ['IU', 'Jungkook', 'Taeyeon'],
                'expected_sources': ['lastfm', 'deezer'],
                'min_connections': 2,
                'description': 'Solo artists from K-pop scene'
            },
            
            # Rock/Alternative (good cross-API coverage)
            {
                'name': 'Rock/Alternative',
                'artists': ['Radiohead', 'Arctic Monkeys', 'Foo Fighters'],
                'expected_sources': ['lastfm', 'deezer', 'musicbrainz'],
                'min_connections': 6,
                'description': 'Modern rock with strong similarity data'
            },
            
            # Pop-punk/Emo (testing Tonight Alive connections)
            {
                'name': 'Pop-punk/Emo',
                'artists': ['Paramore', 'Fall Out Boy', 'Tonight Alive'],
                'expected_sources': ['lastfm', 'deezer'],
                'min_connections': 4,
                'description': 'Pop-punk scene connections'
            },
            
            # Hip-hop/Rap (diverse coverage)
            {
                'name': 'Hip-hop/Rap',
                'artists': ['Kendrick Lamar', 'Drake', 'Travis Scott'],
                'expected_sources': ['lastfm', 'deezer'],
                'min_connections': 4,
                'description': 'Contemporary hip-hop artists'
            },
            
            # Edge cases (challenging/rare artists)
            {
                'name': 'Edge Cases',
                'artists': ['ANYUJIN', 'Joji', 'Phoebe Bridgers'],
                'expected_sources': [],  # Variable
                'min_connections': 0,  # May be low
                'description': 'Challenging cases with variable coverage'
            },
            
            # Electronic/EDM
            {
                'name': 'Electronic/EDM',
                'artists': ['Calvin Harris', 'Skrillex', 'Deadmau5'],
                'expected_sources': ['lastfm', 'deezer'],
                'min_connections': 3,
                'description': 'Electronic music producers'
            },
            
            # Indie/Alternative
            {
                'name': 'Indie/Alternative',
                'artists': ['Tame Impala', 'Arctic Monkeys', 'The Strokes'],
                'expected_sources': ['lastfm', 'deezer'],
                'min_connections': 4,
                'description': 'Indie rock scene'
            }
        ]
    
    def run_comprehensive_tests(self):
        """Run the complete test suite."""
        print(f"\n🚀 Running Comprehensive Similarity Test Suite")
        print("=" * 60)
        
        overall_results = {
            'total_test_cases': len(self.test_cases),
            'passed': 0,
            'failed': 0,
            'api_performance': {},
            'edge_weighting_stats': {},
            'issues_found': []
        }
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n📋 Test Case {i}/{len(self.test_cases)}: {test_case['name']}")
            print("-" * 50)
            
            try:
                result = self._run_single_test_case(test_case)
                
                if result['passed']:
                    overall_results['passed'] += 1
                    print(f"✅ Test case PASSED")
                else:
                    overall_results['failed'] += 1
                    print(f"❌ Test case FAILED: {result['failure_reason']}")
                    overall_results['issues_found'].extend(result.get('issues', []))
                
                # Aggregate performance stats
                self._update_performance_stats(overall_results, result)
                
            except Exception as e:
                overall_results['failed'] += 1
                print(f"💥 Test case CRASHED: {e}")
                overall_results['issues_found'].append(f"Crash in {test_case['name']}: {e}")
            
            # Rate limiting between test cases
            time.sleep(1.0)
        
        # Print final results
        self._print_final_results(overall_results)
        
        return overall_results
    
    def _run_single_test_case(self, test_case: Dict) -> Dict:
        """Run a single test case and return detailed results."""
        artists = test_case['artists']
        expected_sources = test_case['expected_sources']
        min_connections = test_case['min_connections']
        
        print(f"   Testing artists: {', '.join(artists)}")
        print(f"   Expected sources: {', '.join(expected_sources) if expected_sources else 'Variable'}")
        print(f"   Minimum connections: {min_connections}")
        
        results = {
            'passed': True,
            'failure_reason': '',
            'artists_tested': len(artists),
            'total_connections': 0,
            'api_coverage': {'lastfm': 0, 'deezer': 0, 'musicbrainz': 0},
            'edge_weights': [],
            'issues': []
        }
        
        for artist in artists:
            print(f"\n   🎯 Testing '{artist}':")
            
            # Test each API individually
            api_results = self._test_all_apis_for_artist(artist)
            
            # Update coverage stats
            for api, count in api_results['connection_counts'].items():
                results['api_coverage'][api] += count
                results['total_connections'] += count
            
            # Test edge weighting
            if api_results['has_connections']:
                edge_test = self._test_edge_weighting_for_artist(artist, api_results['all_data'])
                results['edge_weights'].extend(edge_test['weights'])
                
                if edge_test['issues']:
                    results['issues'].extend(edge_test['issues'])
            
            # Check for issues
            if api_results['issues']:
                results['issues'].extend(api_results['issues'])
            
            time.sleep(0.5)  # Rate limiting between artists
        
        # Validate test case requirements
        if results['total_connections'] < min_connections:
            results['passed'] = False
            results['failure_reason'] = f"Only {results['total_connections']} connections found, expected {min_connections}+"
        
        if expected_sources:
            missing_sources = []
            for source in expected_sources:
                if results['api_coverage'][source] == 0:
                    missing_sources.append(source)
            
            if missing_sources:
                results['passed'] = False
                results['failure_reason'] = f"Missing expected sources: {', '.join(missing_sources)}"
        
        return results
    
    def _test_all_apis_for_artist(self, artist: str) -> Dict:
        """Test all APIs for a single artist."""
        results = {
            'connection_counts': {'lastfm': 0, 'deezer': 0, 'musicbrainz': 0},
            'all_data': {},
            'has_connections': False,
            'issues': []
        }
        
        # Test Last.fm
        if self.lastfm_api:
            try:
                lastfm_results = self.lastfm_api.get_similar_artists(
                    artist, limit=10, use_enhanced_matching=False
                )
                results['connection_counts']['lastfm'] = len(lastfm_results)
                results['all_data']['lastfm'] = lastfm_results
                print(f"      🎶 Last.fm: {len(lastfm_results)} connections")
                
                if len(lastfm_results) > 0:
                    results['has_connections'] = True
                    
            except Exception as e:
                results['issues'].append(f"Last.fm error for {artist}: {e}")
                print(f"      🎶 Last.fm: ERROR - {e}")
        
        # Test Deezer
        try:
            deezer_results = self.deezer_api.get_similar_artists(artist, limit=10)
            results['connection_counts']['deezer'] = len(deezer_results)
            results['all_data']['deezer'] = deezer_results
            print(f"      🎵 Deezer: {len(deezer_results)} connections")
            
            if len(deezer_results) > 0:
                results['has_connections'] = True
                
        except Exception as e:
            results['issues'].append(f"Deezer error for {artist}: {e}")
            print(f"      🎵 Deezer: ERROR - {e}")
        
        # Test MusicBrainz
        try:
            mb_results = self.musicbrainz_api.get_relationship_based_similar_artists(artist, limit=10)
            results['connection_counts']['musicbrainz'] = len(mb_results)
            results['all_data']['musicbrainz'] = mb_results
            print(f"      🎭 MusicBrainz: {len(mb_results)} relationships")
            
            if len(mb_results) > 0:
                results['has_connections'] = True
                
        except Exception as e:
            results['issues'].append(f"MusicBrainz error for {artist}: {e}")
            print(f"      🎭 MusicBrainz: ERROR - {e}")
        
        return results
    
    def _test_edge_weighting_for_artist(self, artist: str, api_data: Dict) -> Dict:
        """Test edge weighting for an artist's connections."""
        results = {
            'weights': [],
            'issues': []
        }
        
        try:
            # Simulate edge creation for top connections from each API
            for api_name, connections in api_data.items():
                if connections:
                    # Test edge weighting with top connection
                    top_connection = connections[0]
                    target_artist = top_connection['name']
                    
                    # Create source data in expected format
                    source_data = {api_name: [top_connection]}
                    
                    # Test edge creation
                    edge = self.edge_weighter.create_weighted_edge(
                        artist, target_artist, source_data
                    )
                    
                    if edge:
                        weight_info = {
                            'source_artist': artist,
                            'target_artist': target_artist,
                            'similarity': edge.similarity,
                            'distance': edge.distance,
                            'confidence': edge.confidence,
                            'is_factual': edge.is_factual,
                            'sources': [c.source for c in edge.contributions],
                            'fusion_method': edge.fusion_method
                        }
                        results['weights'].append(weight_info)
                        
                        print(f"         Edge: {target_artist} (sim={edge.similarity:.2f}, dist={edge.distance:.1f})")
                    else:
                        results['issues'].append(f"Failed to create edge: {artist} -> {target_artist}")
                        
        except Exception as e:
            results['issues'].append(f"Edge weighting error for {artist}: {e}")
        
        return results
    
    def _update_performance_stats(self, overall_results: Dict, test_result: Dict):
        """Update overall performance statistics."""
        # API performance
        for api, count in test_result['api_coverage'].items():
            if api not in overall_results['api_performance']:
                overall_results['api_performance'][api] = {'total_connections': 0, 'artists_with_data': 0}
            
            overall_results['api_performance'][api]['total_connections'] += count
            if count > 0:
                overall_results['api_performance'][api]['artists_with_data'] += 1
        
        # Edge weighting stats
        if test_result['edge_weights']:
            if 'total_edges' not in overall_results['edge_weighting_stats']:
                overall_results['edge_weighting_stats'] = {
                    'total_edges': 0,
                    'factual_edges': 0,
                    'avg_similarity': 0.0,
                    'avg_confidence': 0.0,
                    'fusion_methods': {}
                }
            
            stats = overall_results['edge_weighting_stats']
            
            for weight in test_result['edge_weights']:
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
        print(f"\n📊 FINAL TEST SUITE RESULTS")
        print("=" * 60)
        
        # Overall success rate
        total = results['total_test_cases']
        passed = results['passed']
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"\n🎯 Overall Results:")
        print(f"   Test cases: {passed}/{total} passed ({success_rate:.1f}% success rate)")
        
        if results['failed'] > 0:
            print(f"   ❌ {results['failed']} test case(s) failed")
        
        # API Performance
        print(f"\n🔌 API Performance:")
        for api, stats in results['api_performance'].items():
            total_conn = stats['total_connections']
            artists_with_data = stats['artists_with_data']
            print(f"   {api.capitalize()}: {total_conn} total connections, {artists_with_data} artists with data")
        
        # Edge Weighting Statistics
        if results['edge_weighting_stats']:
            stats = results['edge_weighting_stats']
            print(f"\n⚖️  Edge Weighting Statistics:")
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
            print(f"\n⚠️  Issues Found ({len(results['issues_found'])}):")
            for issue in results['issues_found'][:10]:  # Show first 10
                print(f"   - {issue}")
            
            if len(results['issues_found']) > 10:
                print(f"   ... and {len(results['issues_found']) - 10} more issues")
        else:
            print(f"\n✅ No issues found!")

def run_manual_test_suite():
    """Entry point for running the manual test suite."""
    try:
        test_suite = ComprehensiveSimilarityTestSuite()
        results = test_suite.run_comprehensive_tests()
        
        # Save results to file
        output_file = "similarity_test_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        return results
        
    except Exception as e:
        print(f"💥 Test suite failed to run: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    run_manual_test_suite()