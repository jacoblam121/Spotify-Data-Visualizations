#!/usr/bin/env python3
"""
Quick launcher for Node Metrics Analyzer
"""

import os
import sys

# Ensure we're in the right directory
if __name__ == "__main__":
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Import and run the analyzer
    from node_metrics_analyzer import NodeMetricsAnalyzer
    
    print("🚀 Launching Node Metrics Analyzer...")
    print()
    
    analyzer = NodeMetricsAnalyzer()
    analyzer.run_interactive()