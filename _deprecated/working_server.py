#!/usr/bin/env python3
"""
Minimal working server - no fancy features, just serves files
"""

import http.server
import socketserver
import os

# Change to parent directory to serve all files
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(parent_dir)

PORT = 8003
Handler = http.server.SimpleHTTPRequestHandler

print(f"📁 Serving from: {parent_dir}")
print(f"🌐 Starting server on http://localhost:{PORT}")
print(f"📱 Open: http://localhost:{PORT}/static/network_enhanced.html")
print(f"🛑 Press Ctrl+C to stop")

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n🛑 Server stopped")
except OSError as e:
    print(f"❌ Error: {e}")
    print("💡 Try a different port or kill existing servers")