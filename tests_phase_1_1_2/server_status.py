#!/usr/bin/env python3
"""Check server status and show URLs"""

from server_control import TestServer

def main():
    """Show current server status"""
    server = TestServer()
    
    if not server.status():
        print("\n💡 Start server with: python start_server.py")
        print("💡 Or use: python server_control.py start")

if __name__ == "__main__":
    main()