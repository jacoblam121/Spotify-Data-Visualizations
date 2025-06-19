#!/usr/bin/env python3
"""
Fixed HTTP server with proper UTF-8 handling
"""

import http.server
import socketserver
import os
import sys

class UTF8Handler(http.server.SimpleHTTPRequestHandler):
    """Simple handler that ensures UTF-8 for text files"""
    
    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    
    def guess_type(self, path):
        """Override to add charset for text files"""
        mimetype, encoding = super().guess_type(path)
        
        # Add charset=utf-8 for text-based files
        if mimetype and mimetype.startswith(('text/', 'application/javascript', 'application/json')):
            if 'charset' not in mimetype:
                mimetype += '; charset=utf-8'
        
        return mimetype, encoding

def start_server(port=8004):
    # Change to parent directory to serve all files
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(parent_dir)
    
    print(f"📁 Serving from: {parent_dir}")
    print(f"🌐 Starting UTF-8 server on port {port}")
    print(f"📱 Open: http://localhost:{port}/static/network_enhanced.html")
    print(f"🛑 Press Ctrl+C to stop")
    
    try:
        with socketserver.TCPServer(("", port), UTF8Handler) as httpd:
            httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use")
            print(f"💡 Try: python fixed_server.py {port + 1}")
        else:
            print(f"❌ Error: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

if __name__ == "__main__":
    port = 8004
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Usage: python fixed_server.py [port]")
            sys.exit(1)
    
    start_server(port)