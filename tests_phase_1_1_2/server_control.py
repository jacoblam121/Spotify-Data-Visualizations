#!/usr/bin/env python3
"""
Server Control Script for Phase 1.1.2 Testing
Manages HTTP server for testing the network visualization
"""

import os
import sys
import signal
import subprocess
import time
import socket
import argparse
from pathlib import Path

class TestServer:
    def __init__(self, host="localhost", port=8080, project_root=".."):
        self.host = host
        self.port = port
        self.project_root = Path(project_root).resolve()
        self.pid_file = Path("server.pid")
        self.process = None
    
    def is_port_in_use(self, port):
        """Check if port is already in use"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return False
            except OSError:
                return True
    
    def find_free_port(self, start_port=8080):
        """Find the next available port"""
        port = start_port
        while port < start_port + 100:  # Try 100 ports
            if not self.is_port_in_use(port):
                return port
            port += 1
        raise RuntimeError("No free ports found")
    
    def get_running_server_info(self):
        """Get info about currently running server"""
        if not self.pid_file.exists():
            return None
        
        try:
            with open(self.pid_file, 'r') as f:
                data = f.read().strip().split('\n')
                if len(data) >= 3:
                    return {
                        'pid': int(data[0]),
                        'host': data[1],
                        'port': int(data[2])
                    }
        except (ValueError, FileNotFoundError):
            pass
        return None
    
    def start(self, auto_port=True):
        """Start the HTTP server"""
        # Check if server is already running
        server_info = self.get_running_server_info()
        if server_info:
            try:
                os.kill(server_info['pid'], 0)  # Check if process exists
                print(f"✅ Server already running at http://{server_info['host']}:{server_info['port']}")
                return server_info['host'], server_info['port']
            except OSError:
                # Process doesn't exist, clean up pid file
                self.pid_file.unlink(missing_ok=True)
        
        # Find available port if needed
        if auto_port and self.is_port_in_use(self.port):
            self.port = self.find_free_port(self.port)
            print(f"⚠️  Port {self.port} in use, using port {self.port}")
        
        # Change to project directory
        original_dir = os.getcwd()
        os.chdir(self.project_root)
        
        try:
            # Start server
            print(f"🚀 Starting server at http://{self.host}:{self.port}")
            print(f"📁 Serving from: {self.project_root}")
            
            self.process = subprocess.Popen(
                [sys.executable, "-m", "http.server", str(self.port), "--bind", self.host],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Wait a moment to see if it starts successfully
            time.sleep(1)
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                print(f"❌ Server failed to start:")
                print(f"   stdout: {stdout.decode()}")
                print(f"   stderr: {stderr.decode()}")
                return None, None
            
            # Save server info
            with open(self.pid_file, 'w') as f:
                f.write(f"{self.process.pid}\n{self.host}\n{self.port}\n")
            
            print(f"✅ Server started successfully!")
            print(f"🌐 Open in browser: http://{self.host}:{self.port}/network_visualization.html")
            print(f"📊 PID: {self.process.pid}")
            
            return self.host, self.port
            
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return None, None
        finally:
            os.chdir(original_dir)
    
    def stop(self):
        """Stop the HTTP server"""
        server_info = self.get_running_server_info()
        
        if not server_info:
            print("⚠️  No server running (no PID file found)")
            return False
        
        try:
            pid = server_info['pid']
            print(f"🛑 Stopping server (PID: {pid})")
            
            # Kill the process group to ensure all child processes are terminated
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            
            # Wait for process to terminate
            timeout = 5
            while timeout > 0:
                try:
                    os.kill(pid, 0)  # Check if process still exists
                    time.sleep(0.5)
                    timeout -= 0.5
                except OSError:
                    break
            
            # Force kill if still running
            try:
                os.kill(pid, 0)
                print("⚠️  Process still running, force killing...")
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except OSError:
                pass
            
            # Clean up PID file
            self.pid_file.unlink(missing_ok=True)
            print("✅ Server stopped successfully")
            return True
            
        except OSError as e:
            print(f"⚠️  Process may have already stopped: {e}")
            self.pid_file.unlink(missing_ok=True)
            return True
        except Exception as e:
            print(f"❌ Error stopping server: {e}")
            return False
    
    def status(self):
        """Show server status"""
        server_info = self.get_running_server_info()
        
        if not server_info:
            print("❌ No server running")
            return False
        
        try:
            pid = server_info['pid']
            os.kill(pid, 0)  # Check if process exists
            print(f"✅ Server running at http://{server_info['host']}:{server_info['port']}")
            print(f"📊 PID: {pid}")
            print(f"🌐 Visualization: http://{server_info['host']}:{server_info['port']}/network_visualization.html")
            return True
        except OSError:
            print("❌ Server not running (stale PID file)")
            self.pid_file.unlink(missing_ok=True)
            return False
    
    def restart(self):
        """Restart the server"""
        print("🔄 Restarting server...")
        self.stop()
        time.sleep(1)
        return self.start()


def main():
    parser = argparse.ArgumentParser(description="Control test server for network visualization")
    parser.add_argument("action", choices=["start", "stop", "restart", "status"], 
                       help="Server action to perform")
    parser.add_argument("--host", default="localhost", help="Host to bind to (default: localhost)")
    parser.add_argument("--port", type=int, default=8080, help="Port to use (default: 8080)")
    parser.add_argument("--project-root", default="..", help="Project root directory (default: ..)")
    
    args = parser.parse_args()
    
    server = TestServer(host=args.host, port=args.port, project_root=args.project_root)
    
    if args.action == "start":
        host, port = server.start()
        if host and port:
            print(f"\n🎯 Quick Test URLs:")
            print(f"   Main viz: http://{host}:{port}/network_visualization.html")
            print(f"   Test data: http://{host}:{port}/bidirectional_network_100artists_20250613_012900.json")
            print(f"\n💡 Use 'python server_control.py stop' to stop the server")
    elif args.action == "stop":
        server.stop()
    elif args.action == "restart":
        server.restart()
    elif args.action == "status":
        server.status()


if __name__ == "__main__":
    main()