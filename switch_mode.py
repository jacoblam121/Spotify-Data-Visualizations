#!/usr/bin/env python3
"""
Visualization Mode Switcher
===========================

Quick utility to switch between 'tracks' and 'artists' visualization modes
in the configuration file.
"""

import os
import sys

def read_config():
    """Read current configuration."""
    config_file = "configurations.txt"
    if not os.path.exists(config_file):
        print(f"❌ Configuration file not found: {config_file}")
        return None
    
    with open(config_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    return lines

def get_current_mode(lines):
    """Get current visualization mode from config lines."""
    for line in lines:
        if line.strip().startswith('MODE ='):
            mode = line.split('=')[1].strip()
            return mode
    return None

def switch_mode(lines, new_mode):
    """Switch to new mode in config lines."""
    new_lines = []
    
    for line in lines:
        if line.strip().startswith('MODE ='):
            # Replace the mode line
            new_lines.append(f"MODE = {new_mode}\n")
        else:
            new_lines.append(line)
    
    return new_lines

def write_config(lines):
    """Write configuration back to file."""
    config_file = "configurations.txt"
    
    # Backup original
    backup_file = f"{config_file}.backup"
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            original = f.read()
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(original)
    
    # Write new config
    with open(config_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✅ Configuration updated (backup saved as {backup_file})")

def main():
    """Main function."""
    print("🔄 Visualization Mode Switcher")
    print("=" * 40)
    
    # Read current config
    lines = read_config()
    if lines is None:
        return
    
    current_mode = get_current_mode(lines)
    if current_mode is None:
        print("❌ Could not find MODE setting in configuration")
        return
    
    print(f"Current mode: {current_mode}")
    
    if len(sys.argv) > 1:
        # Command line mode
        new_mode = sys.argv[1].lower()
        
        if new_mode not in ['tracks', 'artists']:
            print("❌ Invalid mode. Use 'tracks' or 'artists'")
            print("Usage: python switch_mode.py [tracks|artists]")
            return
        
        if new_mode == current_mode.lower():
            print(f"✅ Already in {new_mode} mode")
            return
        
        # Switch mode
        new_lines = switch_mode(lines, new_mode)
        write_config(new_lines)
        print(f"🔄 Switched from '{current_mode}' to '{new_mode}' mode")
        
    else:
        # Interactive mode
        print("\nAvailable modes:")
        print("1. tracks  - Show top tracks with album covers")
        print("2. artists - Show top artists with profile photos")
        
        choice = input(f"\nCurrent: {current_mode}\nSwitch to (tracks/artists/cancel): ").strip().lower()
        
        if choice in ['cancel', 'c', '']:
            print("❌ Cancelled")
            return
        
        if choice not in ['tracks', 'artists']:
            print("❌ Invalid choice")
            return
        
        if choice == current_mode.lower():
            print(f"✅ Already in {choice} mode")
            return
        
        # Switch mode
        new_lines = switch_mode(lines, choice)
        write_config(new_lines)
        print(f"🔄 Switched from '{current_mode}' to '{choice}' mode")
        
        # Suggest next steps
        print(f"\n💡 Next steps:")
        print(f"   - Test the new mode: python quick_test.py data")
        if choice == 'artists':
            print(f"   - Test artist photos: python quick_test.py artist \"Taylor Swift\"")
        print(f"   - Run full test suite: python test_phases_1_2.py")

if __name__ == "__main__":
    main()