#!/usr/bin/env python3
"""
Quick Manual Test Runner
Provides easy commands to run specific tests without the interactive menu.
"""

import sys
import subprocess

def show_available_tests():
    """Show all available manual tests."""
    print("🎯 MANUAL TESTS FOR NETWORK VISUALIZATION")
    print("=" * 60)
    
    print("\n📋 API & Configuration Tests:")
    print("  python test_api_configs.py              # Test all API configurations")
    print("  python config_loader.py                 # Test config file loading")
    
    print("\n🕸️  Network Validation Tests:")
    print("  python validate_graph.py 10 0.08        # Small network (10 artists, threshold 0.08)")
    print("  python validate_graph.py 20 0.1         # Medium network (20 artists, threshold 0.1)")
    print("  python validate_graph.py 30 0.05        # Larger network (30 artists, lower threshold)")
    
    print("\n🔧 Interactive Test Framework:")
    print("  python test_network_visualization.py    # Full interactive test menu")
    
    print("\n⭐ RECOMMENDED TESTS - Optimized Resolution:")
    print("  # Option 6: Test optimized artist resolution")
    print("  # Option 7: Create corrected network visualization") 
    print("  # Option 8: Compare old vs new resolution methods")
    print("  # Option 9: Generate interactive D3.js network")
    
    print("\n📊 Individual Component Tests:")
    print("  python fix_artist_resolution.py         # Test optimized resolution directly")
    print("  python test_optimized_network.py        # Test full optimized network")
    print("  python create_corrected_visualization.py # Create corrected D3.js viz")
    print("  python -c 'from test_network_visualization import NetworkVisualizationTester; t=NetworkVisualizationTester(); t.test_optimized_artist_resolution()'")
    print("  python -c 'from test_network_visualization import NetworkVisualizationTester; t=NetworkVisualizationTester(); t.create_corrected_network_visualization()'")
    
    print("\n🎨 Visualization Tests (Phase 1+):")
    print("  # These will be available after Phase 1 implementation:")
    print("  # python generate_graph_json.py         # Generate JSON for visualization")
    print("  # python -m http.server 8000            # Serve HTML visualization")
    
    print("\n💾 File Management:")
    print("  python -c 'from test_network_visualization import NetworkVisualizationTester; t=NetworkVisualizationTester(); t.clear_cache_files()'")
    
    print("\n📁 Generated Files:")
    print("  ls -la artist_network_validation_*.gexf  # Gephi files")
    print("  ls -la artist_network_validation_*.json # Network data files")
    print("  ls -la lastfm_cache/                    # Last.fm API cache")
    
    print("\n🎯 Quick Start Recommendations:")
    print("  1. python test_api_configs.py           # Verify API setup")
    print("  2. python validate_graph.py 15 0.08     # Test small network")
    print("  3. Open .gexf file in Gephi to validate structure")
    
    print("\n📖 Usage Notes:")
    print("  • validate_graph.py ARTISTS THRESHOLD")
    print("  • Lower threshold = more edges (denser network)")
    print("  • Higher threshold = fewer edges (sparser network)")
    print("  • Optimal threshold usually between 0.05-0.15")


def run_test(test_name, *args):
    """Run a specific test by name."""
    tests = {
        'api': ['python', 'test_api_configs.py'],
        'config': ['python', 'config_loader.py'],
        'network': ['python', 'validate_graph.py'] + list(args),
        'interactive': ['python', 'test_network_visualization.py'],
        'small': ['python', 'validate_graph.py', '10', '0.08'],
        'medium': ['python', 'validate_graph.py', '20', '0.1'],
        'large': ['python', 'validate_graph.py', '30', '0.05']
    }
    
    if test_name in tests:
        print(f"🚀 Running test: {test_name}")
        print(f"Command: {' '.join(tests[test_name])}")
        print("-" * 40)
        subprocess.run(tests[test_name])
    else:
        print(f"❌ Unknown test: {test_name}")
        print(f"Available tests: {', '.join(tests.keys())}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        show_available_tests()
    else:
        test_name = sys.argv[1]
        args = sys.argv[2:] if len(sys.argv) > 2 else []
        run_test(test_name, *args)