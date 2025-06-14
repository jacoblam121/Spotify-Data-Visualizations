#!/usr/bin/env python3
"""
Clean Test Launcher for Phase 1.1.2
Simple, single-command testing for the three-mode visualization
"""

import os
import sys
import subprocess
import signal
import time
import socket
from pathlib import Path

def kill_existing_servers():
    """Kill any existing HTTP servers"""
    print("🧹 Cleaning up any existing servers...")
    
    try:
        # Kill processes using our target port
        result = subprocess.run(['lsof', '-ti', ':8080'], capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"   Killed process {pid}")
                except:
                    pass
    except:
        pass
    
    # Clean up any PID files
    for pid_file in Path(".").glob("*.pid"):
        pid_file.unlink(missing_ok=True)
    
    time.sleep(1)
    print("✅ Cleanup complete")

def start_server():
    """Start the visualization server on port 8080"""
    print("🚀 Starting visualization server on port 8080...")
    
    try:
        # Start server in background
        process = subprocess.Popen(
            [sys.executable, "-m", "http.server", "8080"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Check if it's running
        if process.poll() is None:
            # Test connection
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(3)
                    result = s.connect_ex(('localhost', 8080))
                    if result == 0:
                        print("✅ Server started successfully!")
                        
                        # Save PID for cleanup
                        with open("server.pid", "w") as f:
                            f.write(str(process.pid))
                        
                        return process.pid
            except:
                pass
        
        print("❌ Server failed to start")
        return None
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

def open_in_browser():
    """Attempt to open in Windows browser from WSL"""
    url = "http://localhost:8080/network_visualization.html"
    
    print(f"🌐 Opening: {url}")
    
    # Try different methods to open browser in Windows from WSL
    try:
        # Try wslview (if available)
        subprocess.run(['wslview', url], check=True, timeout=5)
        print("✅ Opened with wslview")
        return True
    except:
        pass
    
    try:
        # Try explorer.exe
        subprocess.run(['explorer.exe', url], timeout=5)
        print("✅ Opened with explorer.exe")
        return True
    except:
        pass
    
    try:
        # Try cmd.exe start
        subprocess.run(['cmd.exe', '/c', 'start', url], timeout=5)
        print("✅ Opened with cmd.exe")
        return True
    except:
        pass
    
    print("⚠️  Could not auto-open browser")
    return False

def display_instructions():
    """Display testing instructions"""
    print("\n" + "="*60)
    print("🎯 THREE-MODE VISUALIZATION TESTING")
    print("="*60)
    
    print("\n🌐 ACCESS:")
    print("   http://localhost:8080/network_visualization.html")
    
    print("\n📋 TEST CHECKLIST:")
    print("   1. ✓ Page loads with network visualization")
    print("   2. ✓ Three mode buttons visible: Global | Personal | Hybrid")
    print("   3. ✓ Switch between modes - smooth transitions")
    print("   4. ✓ Node sizes change per mode")
    print("   5. ✓ Glow effects change per mode")
    print("   6. ✓ Tooltips show mode-specific content")
    print("   7. ✓ Force controls work (sliders)")
    print("   8. ✓ Zoom/pan works")
    print("   9. ✓ Hover highlights connections")
    print("   10. ✓ Statistics panel updates")
    
    print("\n🎨 EXPECTED MODE BEHAVIORS:")
    print("   🌍 GLOBAL MODE:")
    print("      • Large nodes = globally popular artists")
    print("      • Glowing nodes = your personal favorites")
    print("      • Description updates accordingly")
    
    print("   👤 PERSONAL MODE:")
    print("      • Large nodes = your most-played artists")  
    print("      • Glowing nodes = globally popular artists")
    print("      • Description updates accordingly")
    
    print("   🔀 HYBRID MODE:")
    print("      • Large nodes = combined popularity + personal")
    print("      • Glowing nodes = artists both popular AND personal")
    print("      • Description updates accordingly")
    
    print("\n⚡ PERFORMANCE CHECKS:")
    print("   • Mode transitions < 1 second")
    print("   • No lag during switching")
    print("   • Smooth glow animations")
    print("   • Responsive interactions")
    
    print("\n🛑 TO STOP:")
    print("   python stop_test.py")
    print("   (or Ctrl+C in this terminal)")

def main():
    """Main test launcher"""
    print("🧪 Phase 1.1.2 - Clean Test Launcher")
    print("Starting unified three-mode network visualization...")
    
    # 1. Clean up
    kill_existing_servers()
    
    # 2. Start server
    pid = start_server()
    if not pid:
        print("❌ Failed to start server. Exiting.")
        return
    
    # 3. Try to open browser
    browser_opened = open_in_browser()
    
    # 4. Display instructions
    display_instructions()
    
    if not browser_opened:
        print(f"\n💡 MANUAL BROWSER ACCESS:")
        print(f"   Copy and paste this URL into your Windows browser:")
        print(f"   http://localhost:8080/network_visualization.html")
    
    try:
        print(f"\n🎉 Test environment ready! Server PID: {pid}")
        print(f"Press Ctrl+C to stop the server and exit")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Stopping server...")
        try:
            os.kill(pid, signal.SIGTERM)
            Path("server.pid").unlink(missing_ok=True)
            print("✅ Server stopped cleanly")
        except:
            print("⚠️  Server may have already stopped")

if __name__ == "__main__":
    main()