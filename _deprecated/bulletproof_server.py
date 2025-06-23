#!/usr/bin/env python3
"""
Bulletproof HTTP server - no customization, just works
Uses Python's built-in server without any modifications
"""

import http.server
import socketserver
import os
import sys
import threading
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

def start_server():
    # Change to parent directory to serve all files
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(parent_dir)
    
    # Find a free port
    port = find_free_port(8000)
    if port is None:
        print("❌ No free ports found between 8000-8009")
        return
    
    print(f"📁 Serving from: {parent_dir}")
    print(f"🌐 Starting server on port {port}")
    print(f"📱 Open: http://localhost:{port}/static/network_enhanced.html")
    print(f"🧪 UTF-8 Test: http://localhost:{port}/static/utf8_test.html")
    print(f"🛑 Press Ctrl+C to stop")
    
    # Use completely standard handler - no customization at all
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"✅ Server started successfully on http://localhost:{port}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
        print(f"💡 This suggests a system-level issue")

if __name__ == "__main__":
    start_server()