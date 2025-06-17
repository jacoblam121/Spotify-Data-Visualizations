#!/usr/bin/env python3
"""
Quick launcher for the interactive test menu
"""

import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up environment
os.environ['PYTHONIOENCODING'] = 'utf-8'

if __name__ == "__main__":
    # Force interactive mode
    sys.argv = [sys.argv[0], "--interactive"]
    
    # Import and run the main test suite
    from test_phase1_comprehensive import main
    sys.exit(main())