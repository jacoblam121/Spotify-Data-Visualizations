#!/usr/bin/env python3
"""Quick start script for the test server"""

from server_control import TestServer
import sys

def main():
    """Start server with sensible defaults"""
    
    # Parse optional arguments
    host = "localhost"
    port = 8080
    
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    if len(sys.argv) > 2:
        host = sys.argv[2]
    
    server = TestServer(host=host, port=port)
    host, port = server.start()
    
    if host and port:
        print(f"\n🎉 Server ready!")
        print(f"🌐 Open this URL in Windows browser:")
        print(f"   http://{host}:{port}/network_visualization.html")
        print(f"\n💡 Tips:")
        print(f"   - Test all three modes: Global, Personal, Hybrid")
        print(f"   - Check glow effects and smooth transitions")
        print(f"   - Try force controls and zoom/pan")
        print(f"   - Run 'python stop_server.py' when done")
    else:
        print("❌ Failed to start server")
        sys.exit(1)

if __name__ == "__main__":
    main()