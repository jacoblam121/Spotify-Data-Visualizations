#!/usr/bin/env python3
"""
Simple HTTP server for testing the Enhanced Network Visualization
Serves files from the current directory with proper CORS headers
"""

import http.server
import socketserver
import os
import sys

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()
    
    def guess_type(self, path):
        # Override to ensure proper UTF-8 encoding for JSON files
        mimetype, encoding = super().guess_type(path)
        if path.endswith('.json'):
            return 'application/json; charset=utf-8', encoding
        if path.endswith('.js'):
            return 'application/javascript; charset=utf-8', encoding
        if path.endswith('.html'):
            return 'text/html; charset=utf-8', encoding
        return mimetype, encoding
    
    def log_message(self, format, *args):
        # Simple logging
        print(f"[{self.address_string()}] {format % args}")

def start_server(port=8000):
    # Change to the static directory
    static_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(static_dir)
    
    print(f"Starting test server...")
    print(f"Static dir: {static_dir}")
    print(f"Parent dir: {parent_dir}")
    
    # Serve from parent directory so we can access JSON files
    os.chdir(parent_dir)
    
    Handler = CORSRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"✅ Test server running at http://localhost:{port}")
            print(f"📱 Open: http://localhost:{port}/static/network_enhanced.html")
            print(f"🛑 Press Ctrl+C to stop")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Try a different port:")
            print(f"   python test_server.py {port + 1}")
        else:
            print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Usage: python test_server.py [port]")
            sys.exit(1)
    
    start_server(port)