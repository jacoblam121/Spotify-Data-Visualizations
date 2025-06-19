#!/usr/bin/env python3
"""
Server Management Utility
Handles starting, stopping, and restarting the test server
"""

import subprocess
import sys
import os
import time
import signal

def check_port(port):
    """Check if a port is in use"""
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        return result.returncode == 0 and result.stdout.strip()
    except FileNotFoundError:
        # Fallback for systems without lsof
        try:
            result = subprocess.run(['netstat', '-tln'], capture_output=True, text=True)
            return f':{port} ' in result.stdout
        except FileNotFoundError:
            return False

def kill_port(port):
    """Kill processes on a port"""
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    subprocess.run(['kill', '-9', pid], capture_output=True)
            return True
    except FileNotFoundError:
        pass
    return False

def start_server(port=8000):
    """Start the test server"""
    if check_port(port):
        print(f"⚠️  Port {port} is already in use")
        response = input("Kill existing process and restart? (y/N): ")
        if response.lower() in ['y', 'yes']:
            print(f"🔫 Killing processes on port {port}")
            kill_port(port)
            time.sleep(1)
        else:
            port += 1
            print(f"🔄 Trying port {port}")
    
    print(f"🚀 Starting server on port {port}")
    try:
        subprocess.run([sys.executable, 'test_server.py', str(port)])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

def stop_server(port=8000):
    """Stop the test server"""
    if check_port(port):
        print(f"🛑 Stopping server on port {port}")
        kill_port(port)
        print("✅ Server stopped")
    else:
        print(f"✅ No server running on port {port}")

def restart_server(port=8000):
    """Restart the test server"""
    print(f"🔄 Restarting server on port {port}")
    stop_server(port)
    time.sleep(1)
    start_server(port)

def status(port=8000):
    """Check server status"""
    if check_port(port):
        print(f"✅ Server is running on port {port}")
        print(f"🌐 URL: http://localhost:{port}/static/network_enhanced.html")
    else:
        print(f"❌ No server running on port {port}")

def main():
    if len(sys.argv) < 2:
        print("🖥️  Server Manager")
        print("Usage:")
        print("  python server_manager.py start [port]")
        print("  python server_manager.py stop [port]") 
        print("  python server_manager.py restart [port]")
        print("  python server_manager.py status [port]")
        print("  python server_manager.py kill [port]")
        sys.exit(1)
    
    command = sys.argv[1]
    port = 8000
    
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print("❌ Invalid port number")
            sys.exit(1)
    
    if command == 'start':
        start_server(port)
    elif command == 'stop':
        stop_server(port)
    elif command == 'restart':
        restart_server(port)
    elif command == 'status':
        status(port)
    elif command == 'kill':
        stop_server(port)
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()