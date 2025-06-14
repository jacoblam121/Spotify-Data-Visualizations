#!/usr/bin/env python3
"""Quick stop script for the test server"""

from server_control import TestServer

def main():
    """Stop the test server"""
    server = TestServer()
    
    if server.stop():
        print("🎯 Server stopped. Ready for next test!")
    else:
        print("⚠️  No server was running or failed to stop")

if __name__ == "__main__":
    main()