#!/usr/bin/env python3
"""
Clean Server Startup - Consolidated Solution
Auto-finds free port and starts visualization server
"""

import http.server
import socketserver
import os
import sys
import time

def find_free_port(start_port=8000):
    """Find a free port starting from start_port"""
    import socket
    for port in range(start_port, start_port + 10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None

def main():
    # Change to project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Find a free port
    port = find_free_port(8000)
    if port is None:
        print("❌ No free ports found between 8000-8009")
        return 1
    
    print(f"📁 Serving from: {script_dir}")
    print(f"🌐 Starting server on port {port}")
    print(f"📱 Open: http://localhost:{port}/static/network_enhanced.html")
    print(f"🧪 Phase 1.1 Test: http://localhost:{port}/static/test_phase1_1_manual.html")
    print(f"🛑 Press Ctrl+C to stop")
    
    try:
        with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
            print(f"✅ Server started successfully on http://localhost:{port}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        return 0
    except Exception as e:
        print(f"❌ Server error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())