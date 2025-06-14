#!/usr/bin/env python3
"""Stop the test server"""

import os
import signal
import subprocess
from pathlib import Path

def stop_all_servers():
    """Stop all test servers"""
    print("🛑 Stopping test servers...")
    
    stopped = False
    
    # Try PID file first
    if Path("server.pid").exists():
        try:
            with open("server.pid", "r") as f:
                pid = int(f.read().strip())
            
            os.kill(pid, signal.SIGTERM)
            print(f"✅ Stopped server (PID: {pid})")
            stopped = True
            
            Path("server.pid").unlink()
            
        except Exception as e:
            print(f"⚠️  Error with PID file: {e}")
    
    # Kill any remaining processes on port 8080
    try:
        result = subprocess.run(['lsof', '-ti', ':8080'], capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"✅ Killed process {pid} on port 8080")
                    stopped = True
                except:
                    pass
    except:
        pass
    
    if not stopped:
        print("⚠️  No servers found running")
    else:
        print("🎯 All test servers stopped")

if __name__ == "__main__":
    stop_all_servers()