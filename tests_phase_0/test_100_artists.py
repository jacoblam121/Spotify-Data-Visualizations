#!/usr/bin/env python3
"""
100 Artist Network Test - Phase 0 Target Validation
Tests network generation with 100 artists to validate final production target.
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from create_id_mapping import create_enhanced_network_with_stable_ids

class ArtistNetworkValidator:
    """Validator for 100-artist network generation."""
    
    def __init__(self):
        self.target_artist_count = 100
        self.max_generation_time = 30  # seconds
        self.results_file = "100_artist_test_results.json"
    
    def test_100_artist_generation(self) -> Dict:
        """Test generating a 100-artist network."""
        print(f"🎯 Testing 100-Artist Network Generation")
        print("=" * 50)
        print(f"Target: {self.target_artist_count} artists")
        print(f"Time limit: {self.max_generation_time} seconds")
        print()
        
        start_time = datetime.now()
        start_timestamp = time.time()
        
        try:
            # Generate network
            timestamp = start_time.strftime("%Y%m%d_%H%M%S")
            output_file = f"network_100artists_production_test_{timestamp}.json"
            
            print(f"🚀 Starting generation...")
            network_data = create_enhanced_network_with_stable_ids(
                top_n_artists=self.target_artist_count,
                output_file=output_file
            )
            
            end_time = datetime.now()
            end_timestamp = time.time()
            generation_time = end_timestamp - start_timestamp
            
            if not network_data:
                return self._create_failure_result("Network generation returned empty data", generation_time)
            
            # Validate results
            validation_results = self._validate_network(network_data)
            
            # Performance analysis
            performance_results = self._analyze_performance(generation_time)
            
            # Create comprehensive results
            results = {
                'success': True,
                'timestamp': start_time.isoformat(),
                'generation_time': generation_time,
                'target_artist_count': self.target_artist_count,
                'actual_artist_count': len(network_data['nodes']),
                'output_file': output_file,
                'performance': performance_results,
                'validation': validation_results,
                'network_stats': {
                    'nodes': len(network_data['nodes']),
                    'edges': len(network_data['edges']),
                    'id_types': self._count_id_types(network_data['nodes']),
                    'avg_radius': sum(n['viz']['radius'] for n in network_data['nodes']) / len(network_data['nodes']),
                    'size_range': {
                        'min': min(n['viz']['radius'] for n in network_data['nodes']),
                        'max': max(n['viz']['radius'] for n in network_data['nodes'])
                    }
                }
            }
            
            # Save detailed results
            self._save_results(results)
            
            # Display summary
            self._display_results(results)
            
            return results
            
        except Exception as e:
            error_time = time.time() - start_timestamp
            return self._create_failure_result(f"Exception: {str(e)}", error_time)
    
    def _validate_network(self, network_data: Dict) -> Dict:
        """Comprehensive validation of network data."""
        print(f"🔍 Validating network structure...")
        
        nodes = network_data.get('nodes', [])
        edges = network_data.get('edges', [])
        metadata = network_data.get('metadata', {})
        
        validation_results = {
            'structure_valid': True,
            'id_system_valid': True,
            'visualization_valid': True,
            'metadata_valid': True,
            'issues': []
        }
        
        # Structure validation
        if len(nodes) == 0:
            validation_results['structure_valid'] = False
            validation_results['issues'].append("No nodes generated")
        
        if len(nodes) < self.target_artist_count * 0.9:  # Allow 10% variance
            validation_results['structure_valid'] = False
            validation_results['issues'].append(f"Generated {len(nodes)} nodes, expected ~{self.target_artist_count}")
        
        # ID system validation
        spotify_ids = 0
        mbid_ids = 0
        local_ids = 0
        invalid_ids = 0
        
        for node in nodes:
            node_id = node.get('id', '')
            if node_id.startswith('spotify:'):
                spotify_ids += 1
            elif node_id.startswith('mbid:'):
                mbid_ids += 1
            elif node_id.startswith('local:'):
                local_ids += 1
            else:
                invalid_ids += 1
                validation_results['id_system_valid'] = False
                validation_results['issues'].append(f"Invalid ID format: {node_id}")
        
        # Expect high Spotify ID success rate for 100 artists
        spotify_success_rate = spotify_ids / len(nodes)
        if spotify_success_rate < 0.8:  # Expect 80%+ Spotify IDs
            validation_results['id_system_valid'] = False
            validation_results['issues'].append(f"Low Spotify ID rate: {spotify_success_rate:.1%}")
        
        # Visualization validation
        for i, node in enumerate(nodes):
            if 'viz' not in node:
                validation_results['visualization_valid'] = False
                validation_results['issues'].append(f"Node {i} missing viz properties")
                continue
            
            viz = node['viz']
            required_viz = ['radius', 'size_score', 'color', 'primary_genre']
            for prop in required_viz:
                if prop not in viz:
                    validation_results['visualization_valid'] = False
                    validation_results['issues'].append(f"Node {i} missing viz.{prop}")
            
            # Check radius bounds
            radius = viz.get('radius', 0)
            if radius < 8 or radius > 45:
                validation_results['visualization_valid'] = False
                validation_results['issues'].append(f"Node {i} radius {radius} out of bounds [8, 45]")
        
        # Metadata validation
        if not metadata:
            validation_results['metadata_valid'] = False
            validation_results['issues'].append("Missing metadata")
        
        # Check for ID migration info
        if 'id_migration' not in metadata:
            validation_results['metadata_valid'] = False
            validation_results['issues'].append("Missing ID migration metadata")
        
        # Store ID distribution
        validation_results['id_distribution'] = {
            'spotify': spotify_ids,
            'musicbrainz': mbid_ids,
            'local': local_ids,
            'invalid': invalid_ids,
            'spotify_rate': spotify_success_rate
        }
        
        print(f"  ID Distribution: {spotify_ids} Spotify, {mbid_ids} MBID, {local_ids} Local")
        print(f"  Spotify Success Rate: {spotify_success_rate:.1%}")
        
        return validation_results
    
    def _analyze_performance(self, generation_time: float) -> Dict:
        """Analyze performance metrics."""
        print(f"⚡ Analyzing performance...")
        
        performance_results = {
            'meets_target': generation_time <= self.max_generation_time,
            'generation_time': generation_time,
            'target_time': self.max_generation_time,
            'time_per_artist': generation_time / self.target_artist_count,
            'performance_grade': 'A'
        }
        
        # Performance grading
        if generation_time <= 15:
            performance_results['performance_grade'] = 'A'
        elif generation_time <= 25:
            performance_results['performance_grade'] = 'B'
        elif generation_time <= 35:
            performance_results['performance_grade'] = 'C'
        else:
            performance_results['performance_grade'] = 'F'
        
        # Scalability estimation
        estimated_200_time = generation_time * 2  # Rough estimate
        performance_results['estimated_200_artists'] = estimated_200_time
        performance_results['scalable_to_200'] = estimated_200_time <= 90
        
        print(f"  Generation Time: {generation_time:.1f}s")
        print(f"  Time per Artist: {performance_results['time_per_artist']:.2f}s")
        print(f"  Performance Grade: {performance_results['performance_grade']}")
        print(f"  Est. 200 artists: {estimated_200_time:.1f}s")
        
        return performance_results
    
    def _count_id_types(self, nodes: List[Dict]) -> Dict[str, int]:
        """Count distribution of ID types."""
        counts = {'spotify': 0, 'musicbrainz': 0, 'local': 0, 'invalid': 0}
        
        for node in nodes:
            node_id = node.get('id', '')
            if node_id.startswith('spotify:'):
                counts['spotify'] += 1
            elif node_id.startswith('mbid:'):
                counts['musicbrainz'] += 1
            elif node_id.startswith('local:'):
                counts['local'] += 1
            else:
                counts['invalid'] += 1
        
        return counts
    
    def _save_results(self, results: Dict):
        """Save detailed results to file."""
        results_file = f"tests_phase_0/{self.results_file}"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Detailed results saved: {results_file}")
    
    def _display_results(self, results: Dict):
        """Display comprehensive results summary."""
        print(f"\\n📊 100-Artist Network Test Results")
        print("=" * 50)
        
        # Basic stats
        print(f"Success: {'✅' if results['success'] else '❌'}")
        print(f"Artists Generated: {results['actual_artist_count']}/{results['target_artist_count']}")
        print(f"Generation Time: {results['generation_time']:.1f}s")
        
        # Performance
        perf = results['performance']
        print(f"Performance Grade: {perf['performance_grade']}")
        print(f"Meets Target: {'✅' if perf['meets_target'] else '❌'}")
        
        # Network stats
        stats = results['network_stats']
        print(f"\\nNetwork Statistics:")
        print(f"  Nodes: {stats['nodes']}")
        print(f"  Edges: {stats['edges']}")
        print(f"  Size Range: {stats['size_range']['min']:.1f} - {stats['size_range']['max']:.1f}px")
        print(f"  Average Size: {stats['avg_radius']:.1f}px")
        
        # ID distribution
        id_dist = results['validation']['id_distribution']
        print(f"\\nID Distribution:")
        print(f"  Spotify: {id_dist['spotify']} ({id_dist['spotify_rate']:.1%})")
        print(f"  MusicBrainz: {id_dist['musicbrainz']}")
        print(f"  Local Hash: {id_dist['local']}")
        
        # Validation summary
        validation = results['validation']
        all_valid = all([
            validation['structure_valid'],
            validation['id_system_valid'],
            validation['visualization_valid'],
            validation['metadata_valid']
        ])
        
        print(f"\\nValidation: {'✅ All Passed' if all_valid else '❌ Issues Found'}")
        
        if validation['issues']:
            print(f"Issues ({len(validation['issues'])}):")
            for issue in validation['issues'][:5]:  # Show first 5
                print(f"  - {issue}")
        
        # Final recommendation
        print(f"\\n🎯 Production Readiness:")
        
        if (results['success'] and perf['meets_target'] and 
            all_valid and id_dist['spotify_rate'] >= 0.8):
            print("✅ READY FOR PRODUCTION")
            print("   100-artist networks can be generated reliably")
        elif results['success'] and perf['performance_grade'] in ['A', 'B']:
            print("⚠️  MOSTLY READY")
            print(f"   Minor issues found but performance is good")
        else:
            print("❌ NOT READY")
            print("   Significant issues need resolution")
    
    def _create_failure_result(self, error_message: str, generation_time: float) -> Dict:
        """Create failure result structure."""
        results = {
            'success': False,
            'error': error_message,
            'generation_time': generation_time,
            'target_artist_count': self.target_artist_count,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"❌ Test Failed: {error_message}")
        print(f"Time before failure: {generation_time:.1f}s")
        
        return results

def run_100_artist_stress_test():
    """Run comprehensive 100-artist stress test."""
    print("🚀 100-Artist Network Stress Test")
    print("Testing production readiness for target network size")
    print("=" * 60)
    
    validator = ArtistNetworkValidator()
    results = validator.test_100_artist_generation()
    
    # Additional tests if main test succeeded
    if results.get('success'):
        print(f"\\n🔄 Running Additional Validation...")
        
        # Test multiple generations for consistency
        print(f"Testing generation consistency...")
        
        consistency_results = []
        for i in range(3):
            print(f"  Generation {i+1}/3...")
            start_time = time.time()
            
            try:
                network_data = create_enhanced_network_with_stable_ids(
                    top_n_artists=20,  # Smaller for quick consistency check
                    output_file=None
                )
                
                generation_time = time.time() - start_time
                node_count = len(network_data['nodes']) if network_data else 0
                
                consistency_results.append({
                    'success': True,
                    'time': generation_time,
                    'nodes': node_count
                })
                
            except Exception as e:
                consistency_results.append({
                    'success': False,
                    'error': str(e)
                })
        
        # Analyze consistency
        successful_runs = [r for r in consistency_results if r['success']]
        
        if len(successful_runs) == 3:
            times = [r['time'] for r in successful_runs]
            avg_time = sum(times) / len(times)
            time_variance = max(times) - min(times)
            
            print(f"  ✅ Consistency check passed")
            print(f"  Average time: {avg_time:.1f}s")
            print(f"  Time variance: {time_variance:.1f}s")
            
            results['consistency_test'] = {
                'passed': True,
                'runs': len(successful_runs),
                'avg_time': avg_time,
                'time_variance': time_variance
            }
        else:
            print(f"  ❌ Consistency issues: {len(successful_runs)}/3 runs succeeded")
            results['consistency_test'] = {
                'passed': False,
                'successful_runs': len(successful_runs),
                'total_runs': 3
            }
    
    return results

if __name__ == "__main__":
    # Ensure we're in the right directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Run the stress test
    results = run_100_artist_stress_test()
    
    # Exit with appropriate code
    sys.exit(0 if results.get('success', False) else 1)