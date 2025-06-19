#!/usr/bin/env python3
"""
Clean up stuck processes on common development ports
"""

import subprocess
import sys

def cleanup_ports():
    """Kill processes on common development ports"""
    ports = [8000, 8001, 8002, 8003, 8004, 8005]
    killed_any = False
    
    for port in ports:
        try:
            # Find processes using the port
            result = subprocess.run(
                ['ss', '-tulpn'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if f':{port} ' in line and 'LISTEN' in line:
                        # Extract PID if possible
                        if 'pid=' in line:
                            try:
                                pid_part = line.split('pid=')[1].split(',')[0]
                                pid = pid_part.split()[0]
                                
                                # Kill the process
                                subprocess.run(['kill', '-9', pid], check=True)
                                print(f"💀 Killed process {pid} on port {port}")
                                killed_any = True
                            except (IndexError, subprocess.CalledProcessError):
                                print(f"⚠️  Found process on port {port} but couldn't kill it")
                        else:
                            print(f"⚠️  Port {port} in use but no PID found")
                            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Try alternative method
            try:
                result = subprocess.run(
                    ['fuser', '-k', f'{port}/tcp'], 
                    capture_output=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"💀 Killed process on port {port} (via fuser)")
                    killed_any = True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
    
    if not killed_any:
        print("✅ No processes found on common ports (8000-8005)")
    else:
        print("✅ Port cleanup completed")

if __name__ == "__main__":
    print("🧹 Cleaning up development ports...")
    cleanup_ports()