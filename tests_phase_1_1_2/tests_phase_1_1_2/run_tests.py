#!/usr/bin/env python3
"""
Phase 1.1.2 Test Runner
Comprehensive testing for the unified network visualization
"""

import json
import time
import requests
from pathlib import Path
from server_control import TestServer

class NetworkVisualizationTester:
    def __init__(self):
        self.server = TestServer()
        self.base_url = None
        self.test_results = []
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 Phase 1.1.2 - Network Visualization Test Suite")
        print("=" * 60)
        
        # Start server
        if not self.start_test_server():
            return False
        
        # Run tests
        self.test_file_structure()
        self.test_data_loading()
        self.test_server_endpoints()
        self.display_manual_test_guide()
        
        # Summary
        self.print_test_summary()
        
        return True
    
    def start_test_server(self):
        """Start the test server"""
        print("🚀 Starting test server...")
        
        host, port = self.server.start()
        if not host or not port:
            print("❌ Failed to start server")
            return False
        
        self.base_url = f"http://{host}:{port}"
        print(f"✅ Server running at {self.base_url}")
        return True
    
    def test_file_structure(self):
        """Test that all required files exist"""
        print("\n📁 Testing file structure...")
        
        required_files = [
            "network_visualization.html",
            "js/network-visualization.js"
        ]
        
        for file_path in required_files:
            if Path(file_path).exists():
                print(f"✅ {file_path}")
                self.test_results.append(("File Structure", file_path, True, "Found"))
            else:
                print(f"❌ {file_path} - MISSING")
                self.test_results.append(("File Structure", file_path, False, "Missing"))
    
    def test_data_loading(self):
        """Test data file loading"""
        print("\n📊 Testing data files...")
        
        # Check for network data files
        json_files = list(Path(".").glob("*.json"))
        
        if json_files:
            print(f"✅ Found {len(json_files)} JSON data files")
            
            # Test data structure
            for json_file in json_files[:3]:  # Test first 3
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                    
                    nodes = data.get('nodes', [])
                    edges = data.get('edges', [])
                    
                    print(f"   📊 {json_file.name}: {len(nodes)} nodes, {len(edges)} edges")
                    
                    # Check node structure
                    if nodes:
                        sample_node = nodes[0]
                        has_required = 'id' in sample_node and 'name' in sample_node
                        has_listeners = 'listeners' in sample_node or 'listener_count' in sample_node
                        has_play_count = 'play_count' in sample_node
                        
                        status = "✅" if has_required else "⚠️"
                        print(f"   {status} Structure: required={has_required}, listeners={has_listeners}, plays={has_play_count}")
                        
                        self.test_results.append(("Data Loading", json_file.name, has_required, 
                                                f"Nodes: {len(nodes)}, Edges: {len(edges)}"))
                    
                except Exception as e:
                    print(f"   ❌ Error loading {json_file.name}: {e}")
                    self.test_results.append(("Data Loading", json_file.name, False, str(e)))
        else:
            print("⚠️  No JSON data files found - will use embedded sample data")
            self.test_results.append(("Data Loading", "JSON files", False, "None found, using fallback"))
    
    def test_server_endpoints(self):
        """Test that server endpoints are accessible"""
        print("\n🌐 Testing server endpoints...")
        
        endpoints = [
            ("Main visualization", "/network_visualization.html"),
            ("JavaScript module", "/js/network-visualization.js")
        ]
        
        for name, endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    print(f"✅ {name}: {response.status_code}")
                    self.test_results.append(("Server Endpoints", name, True, f"HTTP {response.status_code}"))
                else:
                    print(f"⚠️  {name}: HTTP {response.status_code}")
                    self.test_results.append(("Server Endpoints", name, False, f"HTTP {response.status_code}"))
            
            except Exception as e:
                print(f"❌ {name}: {e}")
                self.test_results.append(("Server Endpoints", name, False, str(e)))
    
    def display_manual_test_guide(self):
        """Display manual testing instructions"""
        print(f"\n🎯 MANUAL TESTING GUIDE")
        print("=" * 30)
        print(f"🌐 Open in Windows browser: {self.base_url}/network_visualization.html")
        print()
        
        print("📋 Test Checklist:")
        tests = [
            "✓ Page loads without errors",
            "✓ Three mode buttons appear (Global/Personal/Hybrid)",
            "✓ Network visualization renders with nodes and edges", 
            "✓ Mode switching works smoothly",
            "✓ Node sizes change between modes",
            "✓ Glow effects appear and change per mode",
            "✓ Tooltips show mode-specific content",
            "✓ Force controls work (strength, distance sliders)",
            "✓ Zoom and pan work",
            "✓ Connection highlighting on hover",
            "✓ Edge labels toggle works",
            "✓ Statistics panel updates per mode",
            "✓ Clicking nodes opens Last.fm links"
        ]
        
        for test in tests:
            print(f"   {test}")
        
        print(f"\n🎨 Expected Mode Behaviors:")
        print(f"   Global Mode:   Large nodes = popular artists, glow = your favorites")
        print(f"   Personal Mode: Large nodes = your top plays, glow = popular artists")
        print(f"   Hybrid Mode:   Large nodes = combined, glow = both popular & personal")
        
        print(f"\n💡 Performance Tests:")
        print(f"   - Smooth transitions (< 1 second)")
        print(f"   - No lag during mode switching")
        print(f"   - Responsive force simulation")
        print(f"   - Glow effects don't cause stuttering")
    
    def print_test_summary(self):
        """Print summary of automated tests"""
        print(f"\n📊 AUTOMATED TEST SUMMARY")
        print("=" * 30)
        
        categories = {}
        for category, test, passed, details in self.test_results:
            if category not in categories:
                categories[category] = []
            categories[category].append((test, passed, details))
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, _, passed, _ in self.test_results if passed)
        
        for category, tests in categories.items():
            category_passed = sum(1 for _, passed, _ in tests if passed)
            print(f"\n{category}: {category_passed}/{len(tests)} passed")
            
            for test, passed, details in tests:
                status = "✅" if passed else "❌"
                print(f"   {status} {test}: {details}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} automated tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All automated tests passed! Ready for manual testing.")
        else:
            print("⚠️  Some automated tests failed. Check issues before manual testing.")


def main():
    """Run the test suite"""
    tester = NetworkVisualizationTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print(f"\n💡 Server is running. Use these commands:")
            print(f"   python stop_server.py     # Stop server")
            print(f"   python server_status.py  # Check status") 
            print(f"   python start_server.py   # Restart server")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Tests interrupted")
        tester.server.stop()
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        tester.server.stop()


if __name__ == "__main__":
    main()