#!/usr/bin/env python3
"""
Test Suite for Phase 1A: Flask Development Server
Run this to validate the new server implementation
"""

import requests
import time
import json
import sys
from urllib.parse import urljoin

class TestPhase1A:
    def __init__(self, base_url=None):
        if base_url is None:
            # Auto-detect running server port
            self.base_url = self.find_running_server()
        else:
            self.base_url = base_url
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def find_running_server(self):
        """Try to find a running Flask server on common ports"""
        import socket
        
        ports_to_try = [8000, 8001, 8002, 8003]
        for port in ports_to_try:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('127.0.0.1', port))
                    if result == 0:  # Port is open
                        # Try to verify it's our Flask server
                        try:
                            response = requests.get(f"http://localhost:{port}/health", timeout=2)
                            if response.status_code == 200:
                                data = response.json()
                                if data.get('server') == 'Flask Development Server':
                                    print(f"🎯 Found Flask server running on port {port}")
                                    return f"http://localhost:{port}"
                        except:
                            pass
            except:
                continue
        
        # Default to 8000 if no server found
        print("⚠️  No running Flask server detected, using default port 8000")
        return "http://localhost:8000"
    
    def test(self, name, condition, details=""):
        """Record a test result"""
        status = "✅ PASS" if condition else "❌ FAIL"
        result = {
            "name": name,
            "status": status,
            "passed": condition,
            "details": details
        }
        self.results.append(result)
        
        if condition:
            self.passed += 1
        else:
            self.failed += 1
        
        print(f"{status} {name}")
        if details:
            print(f"    {details}")
    
    def test_server_health(self):
        """Test if server is running and responding"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            self.test(
                "Server Health Check",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test(
                    "Health Endpoint JSON",
                    'status' in data and data['status'] == 'healthy',
                    f"Response: {data.get('status', 'missing')}"
                )
            
        except requests.exceptions.RequestException as e:
            self.test(
                "Server Health Check",
                False,
                f"Connection failed: {e}"
            )
    
    def test_cache_headers(self):
        """Test that proper cache-busting headers are present"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            headers = response.headers
            
            self.test(
                "Cache-Control Header",
                'Cache-Control' in headers and 'no-cache' in headers['Cache-Control'],
                f"Cache-Control: {headers.get('Cache-Control', 'missing')}"
            )
            
            self.test(
                "Pragma Header",
                headers.get('Pragma') == 'no-cache',
                f"Pragma: {headers.get('Pragma', 'missing')}"
            )
            
            self.test(
                "Expires Header",
                headers.get('Expires') == '0',
                f"Expires: {headers.get('Expires', 'missing')}"
            )
            
        except requests.exceptions.RequestException as e:
            self.test(
                "Cache Headers Test",
                False,
                f"Request failed: {e}"
            )
    
    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        try:
            # Test preflight request
            response = requests.options(f"{self.base_url}/health", timeout=5)
            headers = response.headers
            
            self.test(
                "CORS Access-Control-Allow-Origin",
                'Access-Control-Allow-Origin' in headers,
                f"Access-Control-Allow-Origin: {headers.get('Access-Control-Allow-Origin', 'missing')}"
            )
            
        except requests.exceptions.RequestException as e:
            self.test(
                "CORS Headers Test",
                False,
                f"Request failed: {e}"
            )
    
    def test_static_files(self):
        """Test that static files are served correctly"""
        static_files = [
            "/static/js/genre_colors.js",
            "/static/js/renderers/canvas_renderer.js",
            "/static/js/renderers/base_renderer.js"
        ]
        
        for file_path in static_files:
            try:
                response = requests.get(f"{self.base_url}{file_path}", timeout=5)
                self.test(
                    f"Static file: {file_path}",
                    response.status_code == 200,
                    f"Status: {response.status_code}, Content-Type: {response.headers.get('Content-Type', 'unknown')}"
                )
                
                # Check cache headers on static files too
                if response.status_code == 200:
                    self.test(
                        f"Cache headers on {file_path}",
                        'no-cache' in response.headers.get('Cache-Control', ''),
                        f"Cache-Control: {response.headers.get('Cache-Control', 'missing')}"
                    )
                
            except requests.exceptions.RequestException as e:
                self.test(
                    f"Static file: {file_path}",
                    False,
                    f"Request failed: {e}"
                )
    
    def test_main_routes(self):
        """Test main application routes"""
        routes = [
            ("/", "Main page"),
            ("/test", "Test page")
        ]
        
        for route, description in routes:
            try:
                response = requests.get(f"{self.base_url}{route}", timeout=5)
                self.test(
                    f"Route {route} ({description})",
                    response.status_code == 200,
                    f"Status: {response.status_code}, Content-Type: {response.headers.get('Content-Type', 'unknown')}"
                )
                
            except requests.exceptions.RequestException as e:
                self.test(
                    f"Route {route} ({description})",
                    False,
                    f"Request failed: {e}"
                )
    
    def test_port_independence(self):
        """Test that server behavior is consistent"""
        # This test assumes the server is running and checks response consistency
        try:
            response1 = requests.get(f"{self.base_url}/health", timeout=5)
            time.sleep(0.1)  # Small delay
            response2 = requests.get(f"{self.base_url}/health", timeout=5)
            
            self.test(
                "Response Consistency",
                response1.status_code == response2.status_code,
                f"First: {response1.status_code}, Second: {response2.status_code}"
            )
            
            if response1.status_code == 200 and response2.status_code == 200:
                data1 = response1.json()
                data2 = response2.json()
                self.test(
                    "JSON Response Consistency",
                    data1.get('status') == data2.get('status'),
                    f"Both responses have status: {data1.get('status')}"
                )
                
        except requests.exceptions.RequestException as e:
            self.test(
                "Port Independence Test",
                False,
                f"Request failed: {e}"
            )
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("🧪 Running Phase 1A Test Suite")
        print("=" * 50)
        
        self.test_server_health()
        print()
        
        self.test_cache_headers()
        print()
        
        self.test_cors_headers()
        print()
        
        self.test_static_files()
        print()
        
        self.test_main_routes()
        print()
        
        self.test_port_independence()
        print()
        
        # Generate summary
        total = self.passed + self.failed
        print("=" * 50)
        print("📊 Test Summary")
        print(f"✅ Passed: {self.passed}/{total}")
        print(f"❌ Failed: {self.failed}/{total}")
        
        if self.failed == 0:
            print("🎉 All tests passed! Phase 1A is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Check the details above.")
            return False
    
    def save_report(self, filename="test_phase1a_report.json"):
        """Save detailed test report to JSON file"""
        report = {
            "timestamp": time.time(),
            "base_url": self.base_url,
            "summary": {
                "total": self.passed + self.failed,
                "passed": self.passed,
                "failed": self.failed,
                "success_rate": self.passed / (self.passed + self.failed) if (self.passed + self.failed) > 0 else 0
            },
            "results": self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Detailed report saved to {filename}")

def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        tester = TestPhase1A(base_url)
        print(f"🎯 Testing server at: {base_url}")
    else:
        print("🔍 Auto-detecting Flask server...")
        tester = TestPhase1A()  # Auto-detect
        print(f"🎯 Testing server at: {tester.base_url}")
    
    print("Make sure the dev_server.py is running!")
    print()
    success = tester.run_all_tests()
    tester.save_report()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())