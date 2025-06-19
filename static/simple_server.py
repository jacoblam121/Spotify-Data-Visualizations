#!/usr/bin/env python3
"""
Simple, reliable HTTP server for testing
No fancy features, just works
"""

import http.server
import socketserver
import os
import sys

def start_server(port=8000):
    # Change to parent directory to serve files correctly
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(parent_dir)
    
    print(f"📁 Serving from: {parent_dir}")
    print(f"🌐 Server starting on port {port}")
    
    try:
        with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
            print(f"✅ Server running at http://localhost:{port}")
            print(f"📱 Open: http://localhost:{port}/static/network_enhanced.html")
            print(f"🛑 Press Ctrl+C to stop")
            httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use")
            print(f"💡 Try: python simple_server.py {port + 1}")
        else:
            print(f"❌ Error: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Usage: python simple_server.py [port]")
            sys.exit(1)
    
    start_server(port)