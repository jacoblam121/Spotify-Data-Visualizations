#!/usr/bin/env python3
"""
Kill any process using port 8000 (or specified port)
Useful when the test server gets stuck
"""

import subprocess
import sys
import os

def kill_port(port=8000):
    """Kill any process using the specified port"""
    try:
        # Find process using the port
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"🔍 Found {len(pids)} process(es) using port {port}")
            
            for pid in pids:
                if pid:
                    try:
                        # Kill the process
                        subprocess.run(['kill', '-9', pid], check=True)
                        print(f"💀 Killed process {pid}")
                    except subprocess.CalledProcessError:
                        print(f"⚠️  Could not kill process {pid} (may already be dead)")
            
            print(f"✅ Port {port} should now be free")
        else:
            print(f"✅ No processes found using port {port}")
            
    except FileNotFoundError:
        # lsof not available, try alternative method
        print("⚠️  lsof not found, trying alternative method...")
        try:
            # Use netstat and awk to find the process
            result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if f':{port} ' in line and 'LISTEN' in line:
                        # Extract PID from netstat output
                        parts = line.split()
                        if len(parts) > 6 and '/' in parts[6]:
                            pid = parts[6].split('/')[0]
                            try:
                                subprocess.run(['kill', '-9', pid], check=True)
                                print(f"💀 Killed process {pid}")
                            except subprocess.CalledProcessError:
                                print(f"⚠️  Could not kill process {pid}")
            else:
                print(f"❌ Could not check port {port}")
        except FileNotFoundError:
            print("❌ Neither lsof nor netstat available")
            print("💡 Try manually: ps aux | grep python")

def main():
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Usage: python kill_server.py [port]")
            sys.exit(1)
    
    print(f"🔫 Killing processes on port {port}")
    kill_port(port)

if __name__ == "__main__":
    main()