#!/usr/bin/env python3
"""Simple server control for Phase 1.1.2 testing"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def start_server(port=8080):
    """Start HTTP server"""
    try:
        # Check if port is in use
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) == 0:
                port += 1
                print(f"⚠️  Port {port-1} in use, trying port {port}")
        
        print(f"🚀 Starting server on port {port}...")
        process = subprocess.Popen([sys.executable, "-m", "http.server", str(port)])
        
        time.sleep(1)
        print(f"✅ Server running at http://localhost:{port}")
        print(f"🌐 Open in Windows browser: http://localhost:{port}/network_visualization.html")
        print(f"📊 PID: {process.pid}")
        
        # Save PID for stopping
        with open("server.pid", "w") as f:
            f.write(str(process.pid))
        
        return process.pid
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

def stop_server():
    """Stop HTTP server"""
    try:
        if Path("server.pid").exists():
            with open("server.pid", "r") as f:
                pid = int(f.read().strip())
            
            print(f"🛑 Stopping server (PID: {pid})")
            os.kill(pid, signal.SIGTERM)
            
            Path("server.pid").unlink()
            print("✅ Server stopped")
            return True
    except:
        pass
    
    print("⚠️  No server running")
    return False

def server_status():
    """Check server status"""
    if Path("server.pid").exists():
        try:
            with open("server.pid", "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # Check if process exists
            print(f"✅ Server running (PID: {pid})")
            return True
        except:
            Path("server.pid").unlink()
    
    print("❌ No server running")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "start":
            start_server()
        elif action == "stop":
            stop_server()
        elif action == "status":
            server_status()
        else:
            print("Usage: python simple_server.py {start|stop|status}")
    else:
        start_server()