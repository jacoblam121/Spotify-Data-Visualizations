#!/usr/bin/env python3
"""
Test Fixed System
=================
Quick test of the fixed edge weighting and manual connections.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from interactive_network_test_suite import InteractiveNetworkTestSuite

def quick_test():
    """Quick test of the fixed system."""
    print("🧪 Testing Fixed Similarity System")
    print("=" * 38)
    
    suite = InteractiveNetworkTestSuite()
    
    # Test 1: ANYUJIN (should now have manual IVE connection)
    print("\n1️⃣ Testing ANYUJIN (should have manual IVE connection):")
    result = suite.test_artist_vs_all("ANYUJIN", limit=50)
    
    # Test 2: Taylor Swift (should have varied similarity scores)
    print("\n2️⃣ Testing Taylor Swift (should have varied scores):")
    result = suite.test_artist_vs_all("Taylor Swift", limit=20)
    
    # Test 3: Specific ANYUJIN-IVE connection
    print("\n3️⃣ Testing specific ANYUJIN ↔ IVE connection:")
    result = suite.test_specific_connection("ANYUJIN", "IVE")

if __name__ == "__main__":
    quick_test()