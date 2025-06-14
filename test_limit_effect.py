#!/usr/bin/env python3
"""
Test Limit Effect
=================
Test how the artist limit affects the number of connections found.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from interactive_network_test_suite import InteractiveNetworkTestSuite

def test_limits():
    """Test different artist limits to see the effect."""
    print("🔍 Testing Artist Limit Effect")
    print("=" * 32)
    
    suite = InteractiveNetworkTestSuite()
    
    artist = "Taylor Swift"
    limits = [10, 20, 50, 100, None]  # None = all artists
    
    for limit in limits:
        limit_str = "ALL" if limit is None else str(limit)
        print(f"\n🎯 Testing '{artist}' vs top {limit_str} artists:")
        
        result = suite.test_artist_vs_all(artist, limit)
        
        if 'error' not in result:
            total = result['total_connections']
            print(f"   Connections found: {total}")
            
            # Show source breakdown
            lastfm_count = sum(1 for c in result['connections'] if 'lastfm' in c['sources'])
            deezer_count = sum(1 for c in result['connections'] if 'deezer' in c['sources'])
            mb_count = sum(1 for c in result['connections'] if 'musicbrainz' in c['sources'])
            
            print(f"   Source breakdown:")
            print(f"     Last.fm: {lastfm_count}")
            print(f"     Deezer: {deezer_count}")
            print(f"     MusicBrainz: {mb_count}")

if __name__ == "__main__":
    test_limits()