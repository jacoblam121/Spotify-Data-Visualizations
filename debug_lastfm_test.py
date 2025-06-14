#!/usr/bin/env python3
"""
Debug Last.fm Test
==================
Debug exactly what Last.fm is returning and why it's not showing in results.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from integrated_network_generator import IntegratedNetworkGenerator

def debug_lastfm():
    """Debug Last.fm API calls."""
    print("🔍 Debug Last.fm API Calls")
    print("=" * 30)
    
    generator = IntegratedNetworkGenerator()
    
    # Test artists
    test_artists = ["Taylor Swift", "ANYUJIN", "Paramore"]
    
    for artist in test_artists:
        print(f"\n🎯 Testing '{artist}':")
        
        # Get similarity data from all sources
        similarity_data = generator._get_multi_source_similarity(artist)
        
        print(f"📊 Raw similarity data:")
        for source, results in similarity_data.items():
            print(f"   {source}: {len(results)} results")
            if results:
                print(f"      Sample: {[r.get('name', 'unknown') for r in results[:3]]}")
        
        # Check which artists from the user's data are found
        print(f"\n🔍 Cross-checking with user's data:")
        
        # Load user's artists for comparison
        user_artists = set()
        try:
            import json
            with open('spotify_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for entry in data:
                if 'master_metadata_album_artist_name' in entry:
                    artist_name = entry['master_metadata_album_artist_name']
                    if artist_name:
                        user_artists.add(artist_name.strip().lower())
        except Exception as e:
            print(f"   Error loading user data: {e}")
            continue
        
        # Check each source for matches with user data
        for source, results in similarity_data.items():
            matches = []
            for result in results:
                result_name = result.get('name', '').lower()
                if result_name in user_artists:
                    matches.append((result['name'], result.get('match', 0.0)))
            
            if matches:
                print(f"   {source}: {len(matches)} matches with your data")
                for name, score in matches[:5]:
                    print(f"      • {name} ({score:.3f})")
            else:
                print(f"   {source}: No matches with your data")

if __name__ == "__main__":
    debug_lastfm()