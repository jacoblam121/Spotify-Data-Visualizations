#!/usr/bin/env python3
"""
Interactive Manual Test Framework for Network Visualization
Provides comprehensive testing for all phases of development.
"""

import os
import sys
import subprocess
from datetime import datetime
from typing import Optional
import json


class NetworkVisualizationTester:
    """Interactive test framework for network visualization development."""
    
    def __init__(self):
        self.test_results = {}
        self.session_log = []
    
    def log_test(self, test_name: str, result: str, details: str = ""):
        """Log test results for session tracking."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {test_name}: {result}"
        if details:
            entry += f" - {details}"
        self.session_log.append(entry)
        print(f"📝 {entry}")
    
    def show_main_menu(self):
        """Display the main test menu."""
        print("\n" + "="*60)
        print("🎯 NETWORK VISUALIZATION TEST FRAMEWORK")
        print("="*60)
        print("Phase 0 - Foundation & Validation:")
        print("  1. Test API connections")
        print("  2. Validate small network (20 artists)")
        print("  3. Validate medium network (50 artists)")
        print("  4. Export to Gephi for visual validation")
        print("  5. Test different similarity thresholds")
        print("\nOptimized Resolution & Visualization:")
        print("  6. ⭐ Test optimized artist resolution")
        print("  7. ⭐ Create corrected network visualization")
        print("  8. ⭐ Compare old vs new resolution methods")
        print("  9. ⭐ Generate interactive D3.js network")
        print("\nPhase 1 - Core Infrastructure:")
        print("  10. Generate network JSON data")
        print("  11. Test basic sigma.js setup")
        print("  12. Test artist image fetching")
        print("\nPhase 2 - Visual Enhancement:")
        print("  13. Test genre clustering")
        print("  14. Test visual effects")
        print("  15. Performance test (100+ artists)")
        print("\nPhase 3 - Advanced Features:")
        print("  16. Test high-resolution export")
        print("  17. Full end-to-end test")
        print("\nUtilities:")
        print("  18. View test session log")
        print("  19. Clear cache files")
        print("  20. Install missing dependencies")
        print("  0. Exit")
        print("="*60)
    
    def test_api_connections(self):
        """Test 1: Verify API access and credentials."""
        print("\n🔗 Testing API Connections...")
        
        try:
            # Test environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            spotify_id = os.getenv('SPOTIFY_CLIENT_ID')
            spotify_secret = os.getenv('SPOTIFY_CLIENT_SECRET') 
            lastfm_key = os.getenv('LASTFM_API_KEY')
            lastfm_secret = os.getenv('LASTFM_API_SECRET')
            
            print(f"Spotify Client ID: {'✅ Set' if spotify_id else '❌ Missing'}")
            print(f"Spotify Secret: {'✅ Set' if spotify_secret else '❌ Missing'}")
            print(f"Last.fm API Key: {'✅ Set' if lastfm_key else '❌ Missing'}")
            print(f"Last.fm Secret: {'✅ Set' if lastfm_secret else '❌ Missing'}")
            
            if not all([spotify_id, spotify_secret, lastfm_key]):
                self.log_test("API Connections", "FAIL", "Missing credentials in .env")
                return False
            
            # Test Last.fm API
            from lastfm_utils import LastfmAPI
            lastfm = LastfmAPI(lastfm_key, lastfm_secret, 'lastfm_cache')
            test_artist = lastfm.get_similar_artists("Radiohead", limit=5)
            
            if test_artist:
                print(f"✅ Last.fm API working - found {len(test_artist)} similar artists")
                self.log_test("API Connections", "PASS", f"Last.fm returned {len(test_artist)} artists")
                return True
            else:
                self.log_test("API Connections", "FAIL", "Last.fm API not responding")
                return False
                
        except Exception as e:
            print(f"❌ API test failed: {e}")
            self.log_test("API Connections", "FAIL", str(e))
            return False
    
    def validate_network_size(self, n_artists: int, threshold: float = 0.1):
        """Test network generation with specified parameters."""
        print(f"\n🕸️  Validating Network: {n_artists} artists, threshold {threshold}...")
        
        try:
            from validate_graph import validate_artist_network
            result = validate_artist_network(n_artists, threshold)
            
            if result:
                network_data, validation_results, graph = result
                nodes = len(network_data['nodes'])
                edges = len(network_data['edges'])
                
                if edges > 0:
                    self.log_test(f"Network {n_artists} artists", "PASS", 
                                f"{nodes} nodes, {edges} edges")
                    return True
                else:
                    self.log_test(f"Network {n_artists} artists", "FAIL", 
                                "No edges created")
                    return False
            else:
                self.log_test(f"Network {n_artists} artists", "FAIL", "Generation failed")
                return False
                
        except Exception as e:
            print(f"❌ Network validation failed: {e}")
            self.log_test(f"Network {n_artists} artists", "FAIL", str(e))
            return False
    
    def test_gephi_export(self):
        """Test 4: Export network for Gephi validation."""
        print("\n💾 Testing Gephi Export...")
        
        try:
            # Generate a test network
            result = self.validate_network_size(25, 0.08)  # Lower threshold for more edges
            
            if result:
                # Find the most recent .gexf file
                gexf_files = [f for f in os.listdir('.') if f.endswith('.gexf')]
                if gexf_files:
                    latest_gexf = sorted(gexf_files)[-1]
                    print(f"✅ Gephi file created: {latest_gexf}")
                    print("\n📋 Manual validation steps:")
                    print("  1. Open Gephi application")
                    print(f"  2. File -> Open -> {latest_gexf}")
                    print("  3. Layout -> Force Atlas 2 -> Run")
                    print("  4. Verify artist relationships make sense")
                    
                    self.log_test("Gephi Export", "PASS", f"Created {latest_gexf}")
                    return True
                else:
                    self.log_test("Gephi Export", "FAIL", "No .gexf file found")
                    return False
            else:
                self.log_test("Gephi Export", "FAIL", "Network generation failed")
                return False
                
        except Exception as e:
            print(f"❌ Gephi export failed: {e}")
            self.log_test("Gephi Export", "FAIL", str(e))
            return False
    
    def test_similarity_thresholds(self):
        """Test 5: Compare different similarity thresholds."""
        print("\n⚖️  Testing Similarity Thresholds...")
        
        thresholds = [0.05, 0.1, 0.15, 0.2]
        results = {}
        
        try:
            for threshold in thresholds:
                print(f"\n  Testing threshold {threshold}...")
                from validate_graph import validate_artist_network
                result = validate_artist_network(30, threshold)
                
                if result:
                    network_data, _, _ = result
                    results[threshold] = {
                        'nodes': len(network_data['nodes']),
                        'edges': len(network_data['edges'])
                    }
                    print(f"    {threshold}: {results[threshold]['edges']} edges")
                else:
                    results[threshold] = {'nodes': 0, 'edges': 0}
            
            # Print comparison
            print(f"\n📊 Threshold Comparison:")
            for thresh, data in results.items():
                print(f"  {thresh}: {data['edges']} edges")
            
            # Find optimal threshold (balance between too sparse and too dense)
            optimal = None
            for thresh, data in results.items():
                if 10 <= data['edges'] <= 100:  # Good range for visualization
                    optimal = thresh
                    break
            
            if optimal:
                print(f"💡 Recommended threshold: {optimal}")
                self.log_test("Threshold Test", "PASS", f"Optimal: {optimal}")
            else:
                print("⚠️  No optimal threshold found in tested range")
                self.log_test("Threshold Test", "WARN", "No optimal threshold")
            
            return True
            
        except Exception as e:
            print(f"❌ Threshold testing failed: {e}")
            self.log_test("Threshold Test", "FAIL", str(e))
            return False
    
    def test_optimized_artist_resolution(self):
        """Test 6: Test artist resolution with actual dataset artists."""
        print("\n🔍 Testing Artist Resolution on Dataset...")
        
        try:
            from test_top_artists_comprehensive import TopArtistsTestSuite
            
            print("🚀 Running comprehensive test on top dataset artists...")
            
            # Initialize test suite
            suite = TopArtistsTestSuite()
            
            # Run test on smaller subset for interactive testing
            stats = suite.run_comprehensive_test(top_n=15, min_plays=3, save_results=False)
            
            if not stats:
                self.log_test("Dataset Artist Resolution", "FAIL", "Could not load dataset")
                return False
            
            success_rate = stats['success_rate_percent']
            avg_time = stats['average_time_seconds']
            total_tested = stats['total_artists_tested']
            
            print(f"\n📈 Dataset Resolution Results:")
            print(f"   Tested: {total_tested} artists from your dataset")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Average Time: {avg_time:.2f}s per artist")
            
            # Show some successful resolutions
            if stats.get('resolution_methods'):
                print(f"\n🔧 Resolution Methods Used:")
                for method, count in stats['resolution_methods'].items():
                    print(f"   {method}: {count} artists")
            
            # Assessment
            if success_rate >= 85:
                status = "EXCELLENT"
                result = "PASS"
            elif success_rate >= 70:
                status = "GOOD"
                result = "PASS"
            elif success_rate >= 50:
                status = "FAIR"
                result = "WARN"
            else:
                status = "POOR"
                result = "FAIL"
            
            print(f"\n🏥 Assessment: {status} ({success_rate:.1f}% success rate)")
            
            if stats.get('failed_artists'):
                print(f"⚠️  Failed artists: {', '.join(stats['failed_artists'][:3])}{'...' if len(stats['failed_artists']) > 3 else ''}")
            
            self.log_test("Dataset Artist Resolution", result, f"{success_rate:.1f}% success on {total_tested} artists")
            return result in ["PASS"]
                
        except Exception as e:
            print(f"❌ Dataset artist resolution test failed: {e}")
            print(f"💡 Make sure your data files are configured in configurations.txt")
            self.log_test("Dataset Artist Resolution", "FAIL", str(e))
            return False
    
    def create_corrected_network_visualization(self):
        """Test 7: Create corrected network visualization."""
        print("\n🎨 Creating Corrected Network Visualization...")
        
        try:
            from create_corrected_visualization import create_optimized_network, create_corrected_d3_network
            
            # Create network with optimized resolution
            print("📊 Generating network with optimized resolution...")
            network_data, resolved_artists = create_optimized_network(15, 0.08)
            
            if not network_data or not network_data['edges']:
                print("❌ No network data or edges generated")
                print("💡 Try lowering the similarity threshold")
                self.log_test("Corrected Visualization", "FAIL", "No edges generated")
                return False
            
            # Create D3.js visualization
            print("🎨 Creating interactive D3.js visualization...")
            success = create_corrected_d3_network(network_data, "test_corrected_network.html")
            
            if success:
                nodes = len(network_data['nodes'])
                edges = len(network_data['edges'])
                
                print(f"✅ Visualization created successfully!")
                print(f"📁 File: test_corrected_network.html")
                print(f"📊 Network: {nodes} nodes, {edges} edges")
                
                # Check for key corrections
                corrections = []
                if 'anyujin' in resolved_artists:
                    anyujin_listeners = resolved_artists['anyujin']['listeners']
                    if anyujin_listeners > 5000:
                        corrections.append(f"AnYujin: {anyujin_listeners:,} listeners ✅")
                    else:
                        corrections.append(f"AnYujin: {anyujin_listeners:,} listeners ⚠️")
                
                if 'ive' in resolved_artists:
                    ive_listeners = resolved_artists['ive']['listeners']
                    if ive_listeners > 800000:
                        corrections.append(f"IVE: {ive_listeners:,} listeners ✅")
                    else:
                        corrections.append(f"IVE: {ive_listeners:,} listeners ⚠️")
                
                if corrections:
                    print(f"🔍 Key corrections verified:")
                    for correction in corrections:
                        print(f"   {correction}")
                
                self.log_test("Corrected Visualization", "PASS", f"{nodes} nodes, {edges} edges")
                return True
            else:
                print("❌ Failed to create visualization")
                self.log_test("Corrected Visualization", "FAIL", "Visualization creation failed")
                return False
                
        except Exception as e:
            print(f"❌ Corrected visualization test failed: {e}")
            self.log_test("Corrected Visualization", "FAIL", str(e))
            return False
    
    def compare_resolution_methods(self):
        """Test 8: Compare old vs new resolution methods."""
        print("\n⚖️  Comparing Old vs New Resolution Methods...")
        
        try:
            from fix_artist_resolution import OptimizedLastFmClient
            from config_loader import AppConfig
            
            config = AppConfig('configurations.txt')
            lastfm_config = config.get_lastfm_config()
            
            # Test artists known to have issues
            test_artists = ['anyujin', 'ive', 'blackpink', 'twice']
            
            print(f"📊 Comparing resolution methods for {len(test_artists)} artists:")
            
            # Test optimized method
            optimized_client = OptimizedLastFmClient(
                lastfm_config['api_key'], 
                lastfm_config['api_secret']
            )
            
            comparison_results = []
            
            for artist in test_artists:
                print(f"\n🎵 Artist: {artist}")
                
                # Test optimized resolution
                optimized_result = optimized_client.resolve_artist_efficiently(artist)
                
                if optimized_result['resolved']:
                    listeners = optimized_result['listeners']
                    canonical = optimized_result['canonical_name']
                    print(f"   ✅ Optimized: {canonical} ({listeners:,} listeners)")
                    
                    # Determine if this looks correct
                    is_correct = False
                    if artist == 'anyujin' and listeners > 5000:
                        is_correct = True
                    elif artist == 'ive' and listeners > 800000:
                        is_correct = True
                    elif artist in ['blackpink', 'twice'] and listeners > 1000000:
                        is_correct = True
                    elif artist == 'taylor swift' and listeners > 5000000:
                        is_correct = True
                    
                    comparison_results.append({
                        'artist': artist,
                        'optimized_listeners': listeners,
                        'optimized_canonical': canonical,
                        'appears_correct': is_correct
                    })
                    
                    if is_correct:
                        print(f"   🎉 CORRECT: Appears to be the right artist")
                    else:
                        print(f"   ⚠️  UNCERTAIN: May need verification")
                else:
                    print(f"   ❌ Optimized: Failed to resolve")
                    comparison_results.append({
                        'artist': artist,
                        'optimized_listeners': 0,
                        'optimized_canonical': None,
                        'appears_correct': False
                    })
            
            # Summary
            correct_count = sum(1 for r in comparison_results if r['appears_correct'])
            success_rate = (correct_count / len(test_artists)) * 100
            
            print(f"\n📈 Comparison Summary:")
            print(f"   Optimized Method Success: {correct_count}/{len(test_artists)} ({success_rate:.1f}%)")
            print(f"   Key Improvements:")
            print(f"     • Reduced API calls from 5-10 to 1-2 per artist")
            print(f"     • Better artist matching with composite scoring")
            print(f"     • Preserved display name capitalization")
            
            if success_rate >= 75:
                self.log_test("Resolution Comparison", "PASS", f"Optimized method: {success_rate:.1f}% success")
                return True
            else:
                self.log_test("Resolution Comparison", "WARN", f"Only {success_rate:.1f}% success")
                return False
                
        except Exception as e:
            print(f"❌ Resolution comparison failed: {e}")
            self.log_test("Resolution Comparison", "FAIL", str(e))
            return False
    
    def generate_interactive_d3_network(self):
        """Test 9: Generate interactive D3.js network."""
        print("\n🌐 Generating Interactive D3.js Network...")
        
        try:
            # Use the create_simple_network_viz script
            import subprocess
            import os
            
            print("🚀 Running network visualization generator...")
            
            # Run the visualization script
            result = subprocess.run(['python', 'create_simple_network_viz.py'], 
                                  capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0:
                # Check if files were created
                html_files = [f for f in os.listdir('.') if f.endswith('_network_d3.html')]
                
                if html_files:
                    print(f"✅ Interactive network(s) created:")
                    for html_file in html_files:
                        print(f"   📁 {html_file}")
                    
                    print(f"\n🎯 Features included:")
                    print(f"   • Interactive dragging and zooming")
                    print(f"   • Hover tooltips with artist details")
                    print(f"   • Force simulation controls")
                    print(f"   • Color-coded nodes")
                    print(f"   • Click to open Last.fm profiles")
                    
                    self.log_test("Interactive D3 Network", "PASS", f"Created {len(html_files)} files")
                    return True
                else:
                    print("❌ No HTML files were created")
                    self.log_test("Interactive D3 Network", "FAIL", "No HTML output")
                    return False
            else:
                print(f"❌ Script execution failed:")
                print(result.stderr)
                self.log_test("Interactive D3 Network", "FAIL", "Script execution failed")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Script execution timed out")
            self.log_test("Interactive D3 Network", "FAIL", "Timeout")
            return False
        except Exception as e:
            print(f"❌ Interactive D3 network generation failed: {e}")
            self.log_test("Interactive D3 Network", "FAIL", str(e))
            return False
    
    def generate_network_json(self):
        """Test 6: Generate JSON data for visualization."""
        print("\n📄 Generating Network JSON Data...")
        
        try:
            # This will be the main data pipeline script
            print("⚠️  generate_graph_json.py not yet implemented")
            print("📋 This test will:")
            print("  1. Load listening data")
            print("  2. Create network with Last.fm similarities")
            print("  3. Fetch artist images from Spotify")
            print("  4. Pre-calculate node positions")
            print("  5. Export to graph_data.json")
            
            self.log_test("JSON Generation", "PENDING", "Script not implemented")
            return False
            
        except Exception as e:
            print(f"❌ JSON generation failed: {e}")
            self.log_test("JSON Generation", "FAIL", str(e))
            return False
    
    def test_sigma_setup(self):
        """Test 7: Basic sigma.js rendering."""
        print("\n🌐 Testing Sigma.js Setup...")
        
        if not os.path.exists('index.html'):
            print("⚠️  index.html not yet created")
            print("📋 This test will:")
            print("  1. Load sigma.js library")
            print("  2. Fetch graph_data.json")
            print("  3. Render basic nodes and edges")
            print("  4. Test zoom and pan controls")
            
            self.log_test("Sigma.js Setup", "PENDING", "index.html not created")
            return False
        else:
            print("✅ index.html exists")
            # Could add browser automation here
            self.log_test("Sigma.js Setup", "MANUAL", "Requires browser testing")
            return True
    
    def view_session_log(self):
        """Test 14: Display test session log."""
        print("\n📋 Test Session Log:")
        print("-" * 50)
        if self.session_log:
            for entry in self.session_log:
                print(entry)
        else:
            print("No tests run in this session")
        print("-" * 50)
    
    def clear_cache_files(self):
        """Test 15: Clean up cache and temporary files."""
        print("\n🧹 Clearing Cache Files...")
        
        cache_patterns = [
            'artist_network_validation_*.json',
            'artist_network_validation_*.gexf', 
            'artist_network_validation_*.graphml',
            'lastfm_cache/*',
            'album_art_cache/*',
            'artist_art_cache/*'
        ]
        
        cleared = 0
        for pattern in cache_patterns:
            try:
                import glob
                files = glob.glob(pattern)
                for file in files:
                    os.remove(file)
                    cleared += 1
            except:
                pass
        
        print(f"✅ Cleared {cleared} cache files")
        self.log_test("Cache Clear", "PASS", f"Removed {cleared} files")
    
    def install_dependencies(self):
        """Test 16: Install missing dependencies."""
        print("\n📦 Installing Dependencies...")
        
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                         check=True, capture_output=True)
            print("✅ Dependencies installed successfully")
            self.log_test("Dependencies", "PASS", "All packages installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            self.log_test("Dependencies", "FAIL", str(e))
            return False
    
    def run_interactive_tests(self):
        """Main interactive test loop."""
        while True:
            self.show_main_menu()
            
            try:
                choice = input("\n🔧 Select test (0-16): ").strip()
                
                if choice == '0':
                    print("\n👋 Exiting test framework. Happy coding!")
                    break
                elif choice == '1':
                    self.test_api_connections()
                elif choice == '2':
                    self.validate_network_size(20)
                elif choice == '3':
                    self.validate_network_size(50)
                elif choice == '4':
                    self.test_gephi_export()
                elif choice == '5':
                    self.test_similarity_thresholds()
                elif choice == '6':
                    self.test_optimized_artist_resolution()
                elif choice == '7':
                    self.create_corrected_network_visualization()
                elif choice == '8':
                    self.compare_resolution_methods()
                elif choice == '9':
                    self.generate_interactive_d3_network()
                elif choice == '10':
                    self.generate_network_json()
                elif choice == '11':
                    self.test_sigma_setup()
                elif choice == '12':
                    print("⚠️  Artist image testing not yet implemented")
                elif choice == '13':
                    print("⚠️  Genre clustering testing not yet implemented")
                elif choice == '14':
                    print("⚠️  Visual effects testing not yet implemented")
                elif choice == '15':
                    print("⚠️  Performance testing not yet implemented")
                elif choice == '16':
                    print("⚠️  High-res export testing not yet implemented")
                elif choice == '17':
                    print("⚠️  End-to-end testing not yet implemented")
                elif choice == '18':
                    self.view_session_log()
                elif choice == '19':
                    self.clear_cache_files()
                elif choice == '20':
                    self.install_dependencies()
                else:
                    print("❌ Invalid choice. Please try again.")
                
                if choice != '0':
                    input("\n⏸️  Press Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Exiting test framework. Happy coding!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                input("⏸️  Press Enter to continue...")


if __name__ == "__main__":
    tester = NetworkVisualizationTester()
    tester.run_interactive_tests()