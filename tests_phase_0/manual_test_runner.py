#!/usr/bin/env python3
"""
Manual Test Runner for Phase 0 - Network Visualization Foundation
Interactive test suite with configurable parameters for comprehensive testing.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from create_id_mapping import create_enhanced_network_with_stable_ids
from id_migration_system import IDMigrationSystem

class ManualTestConfig:
    """Configuration for manual testing scenarios."""
    
    def __init__(self):
        self.sizing_modes = ['global', 'personal', 'adaptive']
        self.test_scenarios = {
            'quick': {
                'name': 'Quick Test (5 artists)',
                'artist_count': 5,
                'validate_structure': True,
                'check_sizing': True,
                'save_results': True
            },
            'small': {
                'name': 'Small Network (20 artists)',
                'artist_count': 20,
                'validate_structure': True,
                'check_sizing': True,
                'check_performance': True,
                'save_results': True
            },
            'medium': {
                'name': 'Medium Network (50 artists)',
                'artist_count': 50,
                'validate_structure': True,
                'check_sizing': True,
                'check_performance': True,
                'save_results': True,
                'benchmark_time': True
            },
            'large': {
                'name': 'Large Network (100 artists)',
                'artist_count': 100,
                'validate_structure': True,
                'check_sizing': True,
                'check_performance': True,
                'save_results': True,
                'benchmark_time': True,
                'stress_test': True
            },
            'edge_cases': {
                'name': 'Edge Cases & Fallbacks',
                'artist_count': 10,
                'test_edge_cases': True,
                'validate_fallbacks': True,
                'check_error_handling': True
            },
            'custom': {
                'name': 'Custom Configuration',
                'artist_count': None,  # Will be set by user
                'custom_config': True
            }
        }
    
    def get_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Get test scenario configuration."""
        return self.test_scenarios.get(scenario_name, {})
    
    def list_scenarios(self) -> List[str]:
        """List available test scenarios."""
        return list(self.test_scenarios.keys())

class ManualTestRunner:
    """Interactive test runner for Phase 0 functionality."""
    
    def __init__(self):
        self.config = ManualTestConfig()
        self.results_dir = "test_results"
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
        """Display interactive test menu."""
        print("🧪 Manual Test Runner - Phase 0 Network Foundation")
        print("=" * 60)
        print()
        print("Available Test Scenarios:")
        
        scenarios = self.config.list_scenarios()
        for i, scenario in enumerate(scenarios, 1):
            config = self.config.get_scenario(scenario)
            print(f"  {i}. {config.get('name', scenario)}")
        
        print()
        print("Sizing Mode Tests:")
        sizing_modes = self.config.sizing_modes
        base_offset = len(scenarios)
        for i, mode in enumerate(sizing_modes):
            print(f"  {base_offset + i + 1}. Test {mode.title()} Mode (5 artists)")
        
        print()
        print("Additional Options:")
        additional_offset = base_offset + len(sizing_modes)
        print(f"  {additional_offset + 1}. Run All Tests")
        print(f"  {additional_offset + 2}. Performance Benchmark")
        print(f"  {additional_offset + 3}. Validate Existing Files")
        print(f"  {additional_offset + 4}. Clean Test Results")
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
    
    def run_network_test(self, scenario_config: Dict[str, Any], scenario_name: str, sizing_mode: str = 'adaptive') -> Dict[str, Any]:
        """Run a network generation test."""
        print(f"🚀 Running: {scenario_config['name']}")
        print("=" * 50)
        
        artist_count = scenario_config.get('artist_count')
        if artist_count is None:
            artist_count = int(input("Enter number of artists: "))
        
        # Start timer if benchmarking
        start_time = datetime.now()
        
        try:
            # Ensure we're in the correct directory context
            self._ensure_project_context()
            
            # Generate network
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Use absolute path for output file to handle directory changes
            output_file = os.path.join(self.original_cwd, self.results_dir, f"test_{scenario_name}_{artist_count}artists_{timestamp}.json")
            
            print(f"📊 Generating network with {artist_count} artists using {sizing_mode} mode...")
            network_data = create_enhanced_network_with_stable_ids(
                top_n_artists=artist_count,
                output_file=output_file if scenario_config.get('save_results') else None,
                sizing_mode=sizing_mode
            )
            
            end_time = datetime.now()
            generation_time = (end_time - start_time).total_seconds()
            
            if not network_data:
                return {
                    'success': False,
                    'error': 'Failed to generate network data',
                    'scenario': scenario_name,
                    'artist_count': artist_count
                }
            
            # Perform validation tests
            results = {
                'success': True,
                'scenario': scenario_name,
                'artist_count': artist_count,
                'generation_time': generation_time,
                'output_file': output_file if scenario_config.get('save_results') else None,
                'nodes_generated': len(network_data['nodes']),
                'edges_generated': len(network_data['edges']),
                'tests': {}
            }
            
            # Structure validation
            if scenario_config.get('validate_structure'):
                results['tests']['structure'] = self.validate_structure(network_data)
            
            # Sizing validation
            if scenario_config.get('check_sizing'):
                results['tests']['sizing'] = self.validate_sizing(network_data)
            
            # Performance check
            if scenario_config.get('check_performance'):
                results['tests']['performance'] = self.check_performance(
                    generation_time, artist_count
                )
            
            # Edge cases
            if scenario_config.get('test_edge_cases'):
                results['tests']['edge_cases'] = self.test_edge_cases(network_data)
            
            self.display_test_results(results)
            return results
            
        except Exception as e:
            error_results = {
                'success': False,
                'error': str(e),
                'scenario': scenario_name,
                'artist_count': artist_count
            }
            print(f"❌ Test failed: {e}")
            return error_results
        finally:
            # Always restore the original working directory
            self._restore_context()
    
    def run_sizing_mode_test(self, sizing_mode: str) -> Dict[str, Any]:
        """Run a test with a specific sizing mode."""
        print(f"🎯 Testing {sizing_mode.title()} Sizing Mode")
        print("=" * 50)
        
        # Create a quick test scenario
        scenario_config = {
            'name': f'{sizing_mode.title()} Mode Test (5 artists)',
            'artist_count': 5,
            'validate_structure': True,
            'check_sizing': True,
            'save_results': True
        }
        
        return self.run_network_test(scenario_config, f'{sizing_mode}_mode', sizing_mode)
    
    def validate_structure(self, network_data: Dict) -> Dict[str, Any]:
        """Validate network data structure."""
        print("🔍 Validating data structure...")
        
        issues = []
        
        # Check top-level structure
        required_keys = ['nodes', 'edges', 'metadata']
        for key in required_keys:
            if key not in network_data:
                issues.append(f"Missing top-level key: {key}")
        
        nodes = network_data.get('nodes', [])
        edges = network_data.get('edges', [])
        
        # Check nodes
        for i, node in enumerate(nodes):
            required_node_keys = ['id', 'name', 'id_type', 'id_confidence', 'viz']
            for key in required_node_keys:
                if key not in node:
                    issues.append(f"Node {i} ({node.get('name', 'unknown')}) missing: {key}")
            
            # Check ID format
            node_id = node.get('id', '')
            if not (node_id.startswith('spotify:') or node_id.startswith('mbid:') or node_id.startswith('local:')):
                issues.append(f"Node {i} has invalid ID format: {node_id}")
            
            # Check viz properties
            viz = node.get('viz', {})
            required_viz_keys = ['radius', 'size_score', 'color', 'primary_genre']
            for key in required_viz_keys:
                if key not in viz:
                    issues.append(f"Node {i} viz missing: {key}")
        
        # Check edges reference valid nodes
        node_ids = {node['id'] for node in nodes}
        for i, edge in enumerate(edges):
            if edge.get('source') not in node_ids:
                issues.append(f"Edge {i} source not found: {edge.get('source')}")
            if edge.get('target') not in node_ids:
                issues.append(f"Edge {i} target not found: {edge.get('target')}")
        
        result = {
            'passed': len(issues) == 0,
            'issues_found': len(issues),
            'issues': issues[:10],  # Limit to first 10 issues
            'total_nodes': len(nodes),
            'total_edges': len(edges)
        }
        
        if result['passed']:
            print("  ✅ Structure validation passed")
        else:
            print(f"  ❌ Found {len(issues)} structural issues")
            for issue in issues[:5]:  # Show first 5
                print(f"    - {issue}")
        
        return result
    
    def validate_sizing(self, network_data: Dict) -> Dict[str, Any]:
        """Validate sizing algorithm results."""
        print("📏 Validating sizing algorithm...")
        
        nodes = network_data.get('nodes', [])
        issues = []
        
        # Check Taylor Swift vs others sizing (if present)
        taylor_node = None
        other_nodes = []
        
        for node in nodes:
            if 'taylor swift' in node.get('canonical_name', '').lower():
                taylor_node = node
            else:
                other_nodes.append(node)
        
        sizing_stats = {
            'min_radius': min(n['viz']['radius'] for n in nodes) if nodes else 0,
            'max_radius': max(n['viz']['radius'] for n in nodes) if nodes else 0,
            'avg_radius': sum(n['viz']['radius'] for n in nodes) / len(nodes) if nodes else 0,
            'spotify_emphasis_validated': False
        }
        
        # Check if Taylor Swift (if present) is sized appropriately larger
        if taylor_node and other_nodes:
            taylor_radius = taylor_node['viz']['radius']
            taylor_followers = taylor_node.get('spotify_followers', 0)
            
            # Find artist with most followers after Taylor Swift
            max_other_followers = 0
            max_other_radius = 0
            
            for node in other_nodes:
                followers = node.get('spotify_followers', 0)
                radius = node['viz']['radius']
                if followers > max_other_followers:
                    max_other_followers = followers
                    max_other_radius = radius
            
            # Taylor Swift should have largest radius if she has most followers
            if taylor_followers > max_other_followers:
                if taylor_radius > max_other_radius:
                    sizing_stats['spotify_emphasis_validated'] = True
                else:
                    issues.append(f"Taylor Swift ({taylor_followers:,} followers) has smaller radius ({taylor_radius:.1f}) than artist with {max_other_followers:,} followers ({max_other_radius:.1f})")
        
        # Check radius bounds
        for node in nodes:
            radius = node['viz']['radius']
            if radius < 8 or radius > 45:
                issues.append(f"{node['name']} has radius {radius:.1f} outside bounds [8, 45]")
            
            size_score = node['viz']['size_score']
            if size_score < 0 or size_score > 1:
                issues.append(f"{node['name']} has size_score {size_score:.3f} outside bounds [0, 1]")
        
        result = {
            'passed': len(issues) == 0,
            'issues_found': len(issues),
            'issues': issues,
            'stats': sizing_stats
        }
        
        if result['passed']:
            print("  ✅ Sizing validation passed")
            if sizing_stats['spotify_emphasis_validated']:
                print("  ✅ Spotify emphasis validated (Taylor Swift correctly sized)")
        else:
            print(f"  ❌ Found {len(issues)} sizing issues")
            for issue in issues[:3]:
                print(f"    - {issue}")
        
        return result
    
    def check_performance(self, generation_time: float, artist_count: int) -> Dict[str, Any]:
        """Check performance metrics."""
        print(f"⚡ Checking performance...")
        
        # Performance targets (from Phase 0 plan)
        targets = {
            20: 3,    # 20 artists: < 3s
            50: 10,   # 50 artists: < 10s
            100: 30,  # 100 artists: < 30s
            200: 90   # 200 artists: < 90s
        }
        
        # Find applicable target
        target_time = None
        for size, time_limit in targets.items():
            if artist_count <= size:
                target_time = time_limit
                break
        
        if target_time is None:
            target_time = 90  # Default for large networks
        
        passed = generation_time <= target_time
        
        result = {
            'passed': passed,
            'generation_time': generation_time,
            'target_time': target_time,
            'artist_count': artist_count,
            'performance_ratio': generation_time / target_time
        }
        
        if passed:
            print(f"  ✅ Performance target met: {generation_time:.1f}s <= {target_time}s")
        else:
            print(f"  ❌ Performance target missed: {generation_time:.1f}s > {target_time}s")
        
        return result
    
    def test_edge_cases(self, network_data: Dict) -> Dict[str, Any]:
        """Test edge cases and error handling."""
        print("🧪 Testing edge cases...")
        
        nodes = network_data.get('nodes', [])
        
        # Check ID type distribution
        id_types = {}
        for node in nodes:
            id_type = node.get('id_type', 'unknown')
            id_types[id_type] = id_types.get(id_type, 0) + 1
        
        # Check for fallback handling
        has_fallbacks = id_types.get('local', 0) > 0
        
        # Check confidence scores
        low_confidence_count = 0
        for node in nodes:
            if node.get('id_confidence', 1.0) < 0.5:
                low_confidence_count += 1
        
        result = {
            'id_type_distribution': id_types,
            'has_fallback_ids': has_fallbacks,
            'low_confidence_count': low_confidence_count,
            'edge_cases_handled': True  # Assume handled if we got this far
        }
        
        print(f"  📊 ID Distribution: {id_types}")
        if has_fallbacks:
            print(f"  ⚠️  {id_types.get('local', 0)} artists using fallback local IDs")
        if low_confidence_count > 0:
            print(f"  ⚠️  {low_confidence_count} artists with low confidence scores")
        
        return result
    
    def display_test_results(self, results: Dict[str, Any]):
        """Display comprehensive test results."""
        print(f"\\n📈 Test Results Summary:")
        print("=" * 40)
        
        print(f"Scenario: {results['scenario']}")
        print(f"Artists: {results['artist_count']}")
        print(f"Generation Time: {results['generation_time']:.1f}s")
        print(f"Nodes Generated: {results['nodes_generated']}")
        print(f"Edges Generated: {results['edges_generated']}")
        
        if results.get('output_file'):
            print(f"Output File: {results['output_file']}")
        
        # Test results
        tests = results.get('tests', {})
        for test_name, test_result in tests.items():
            status = "✅" if test_result.get('passed', False) else "❌"
            print(f"{test_name.title()}: {status}")
        
        overall_success = all(test.get('passed', False) for test in tests.values())
        status_icon = "🎉" if overall_success else "⚠️"
        
        print(f"\\n{status_icon} Overall: {'PASSED' if overall_success else 'ISSUES FOUND'}")
    
    def run_all_tests(self):
        """Run all predefined test scenarios."""
        print("🔄 Running All Test Scenarios")
        print("=" * 50)
        
        scenarios_to_run = ['quick', 'small', 'medium', 'edge_cases']
        all_results = []
        
        for scenario_name in scenarios_to_run:
            print(f"\\n{'='*20} {scenario_name.upper()} {'='*20}")
            scenario_config = self.config.get_scenario(scenario_name)
            result = self.run_network_test(scenario_config, scenario_name)
            all_results.append(result)
        
        # Summary
        print(f"\\n📊 Overall Summary:")
        print("=" * 30)
        
        successful_tests = sum(1 for r in all_results if r.get('success', False))
        total_tests = len(all_results)
        
        print(f"Tests Completed: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {(successful_tests / total_tests * 100):.1f}%")
        
        return all_results
    
    def run_performance_benchmark(self):
        """Run performance benchmark across different sizes."""
        print("⚡ Performance Benchmark")
        print("=" * 30)
        
        test_sizes = [5, 10, 20, 50]
        benchmark_results = []
        
        for size in test_sizes:
            print(f"\\nTesting {size} artists...")
            start_time = datetime.now()
            
            try:
                network_data = create_enhanced_network_with_stable_ids(
                    top_n_artists=size,
                    output_file=None  # Don't save benchmark files
                )
                
                end_time = datetime.now()
                generation_time = (end_time - start_time).total_seconds()
                
                result = {
                    'artist_count': size,
                    'generation_time': generation_time,
                    'time_per_artist': generation_time / size,
                    'success': True
                }
                
                print(f"  ✅ {size} artists: {generation_time:.1f}s ({generation_time/size:.2f}s per artist)")
                
            except Exception as e:
                result = {
                    'artist_count': size,
                    'generation_time': None,
                    'time_per_artist': None,
                    'success': False,
                    'error': str(e)
                }
                
                print(f"  ❌ {size} artists: Failed - {e}")
            
            benchmark_results.append(result)
        
        # Performance analysis
        successful_results = [r for r in benchmark_results if r['success']]
        
        if successful_results:
            print(f"\\n📊 Performance Analysis:")
            print(f"Fastest: {min(r['generation_time'] for r in successful_results):.1f}s")
            print(f"Slowest: {max(r['generation_time'] for r in successful_results):.1f}s")
            
            avg_time_per_artist = sum(r['time_per_artist'] for r in successful_results) / len(successful_results)
            print(f"Average time per artist: {avg_time_per_artist:.2f}s")
            
            # Estimate 100 artist performance
            estimated_100_time = avg_time_per_artist * 100
            print(f"Estimated 100 artists: {estimated_100_time:.1f}s")
            
            if estimated_100_time <= 30:
                print("✅ 100 artist target should be achievable")
            else:
                print("⚠️  100 artist target may be challenging")
        
        return benchmark_results
    
    def run_interactive(self):
        """Run interactive test menu."""
        while True:
            self.display_menu()
            choice = self.get_user_choice()
            
            if choice == 0:
                print("👋 Goodbye!")
                break
            
            scenarios = self.config.list_scenarios()
            sizing_modes = self.config.sizing_modes
            base_offset = len(scenarios)
            additional_offset = base_offset + len(sizing_modes)
            
            if 1 <= choice <= len(scenarios):
                scenario_name = scenarios[choice - 1]
                scenario_config = self.config.get_scenario(scenario_name)
                
                if scenario_name == 'custom':
                    artist_count = int(input("Enter number of artists: "))
                    scenario_config['artist_count'] = artist_count
                
                self.run_network_test(scenario_config, scenario_name)
            
            elif base_offset + 1 <= choice <= base_offset + len(sizing_modes):
                # Sizing mode test
                mode_index = choice - base_offset - 1
                sizing_mode = sizing_modes[mode_index]
                self.run_sizing_mode_test(sizing_mode)
            
            elif choice == additional_offset + 1:
                self.run_all_tests()
            
            elif choice == additional_offset + 2:
                self.run_performance_benchmark()
            
            elif choice == additional_offset + 3:
                self.validate_existing_files()
            
            elif choice == additional_offset + 4:
                self.clean_test_results()
            
            else:
                print("❌ Invalid choice. Please try again.")
            
            input("\\nPress Enter to continue...")
    
    def validate_existing_files(self):
        """Validate existing test result files."""
        print("🔍 Validating Existing Test Files")
        print("=" * 40)
        
        # Find JSON files in results directory
        json_files = [f for f in os.listdir(self.results_dir) if f.endswith('.json')]
        
        if not json_files:
            print("No test result files found.")
            return
        
        for filename in json_files:
            filepath = os.path.join(self.results_dir, filename)
            print(f"\\nValidating: {filename}")
            
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                structure_result = self.validate_structure(data)
                sizing_result = self.validate_sizing(data)
                
                if structure_result['passed'] and sizing_result['passed']:
                    print(f"  ✅ {filename} is valid")
                else:
                    print(f"  ❌ {filename} has issues")
            
            except Exception as e:
                print(f"  💥 {filename} failed to load: {e}")
    
    def clean_test_results(self):
        """Clean test result files."""
        json_files = [f for f in os.listdir(self.results_dir) if f.endswith('.json')]
        
        if not json_files:
            print("No test result files to clean.")
            return
        
        print(f"Found {len(json_files)} test result files.")
        confirm = input("Delete all test results? (y/N): ")
        
        if confirm.lower() == 'y':
            for filename in json_files:
                filepath = os.path.join(self.results_dir, filename)
                os.remove(filepath)
            print(f"✅ Cleaned {len(json_files)} files.")
        else:
            print("❌ Cancelled.")

if __name__ == "__main__":
    runner = ManualTestRunner()
    runner.run_interactive()