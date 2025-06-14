#!/usr/bin/env python3
"""
Test Artist Data Usage
======================

Example of how to load and use the extracted artist data file
for network analysis and other purposes.
"""

import json
from extract_artist_data import load_artist_data


def main():
    """Demonstrate how to use the extracted artist data."""
    print("🧪 Testing Artist Data Usage")
    print("=" * 40)
    
    # Load the artist data
    print("📄 Loading artist data...")
    artist_data = load_artist_data('artist_data.json')
    
    if not artist_data:
        print("❌ No artist data found. Run extract_artist_data.py first.")
        return
    
    print(f"✅ Loaded {len(artist_data)} artists")
    
    # Show data structure
    print(f"\n📋 Data Structure:")
    print(f"   Each artist has: {list(artist_data[0].keys())}")
    
    # Show top 10
    print(f"\n🎯 Top 10 Artists:")
    for artist in artist_data[:10]:
        print(f"   {artist['rank']:2d}. {artist['name']:<25} ({artist['play_count']:,} plays)")
    
    # Filter examples
    print(f"\n🔍 Filter Examples:")
    
    # Artists with over 1000 plays
    high_play_artists = [a for a in artist_data if a['play_count'] > 1000]
    print(f"   Artists with >1000 plays: {len(high_play_artists)}")
    
    # Top 20 artists
    top_20 = artist_data[:20]
    print(f"   Top 20 artists: {len(top_20)}")
    
    # Find specific artist
    target_artist = "ive"
    ive_data = next((a for a in artist_data if a['name'].lower() == target_artist), None)
    if ive_data:
        print(f"   Found '{target_artist}': Rank #{ive_data['rank']}, {ive_data['play_count']:,} plays")
    
    # Show how this would be used in network analysis
    print(f"\n🕸️  Network Analysis Usage:")
    print(f"   # This is the format expected by network tools:")
    print(f"   test_artists = [")
    for artist in artist_data[:5]:
        print(f"       {{'name': '{artist['name']}', 'play_count': {artist['play_count']}}},")
    print(f"       # ... and {len(artist_data)-5} more")
    print(f"   ]")
    
    # Statistics
    total_plays = sum(a['play_count'] for a in artist_data)
    avg_plays = total_plays / len(artist_data)
    median_plays = sorted([a['play_count'] for a in artist_data])[len(artist_data)//2]
    
    print(f"\n📊 Statistics:")
    print(f"   Total plays (top {len(artist_data)}): {total_plays:,}")
    print(f"   Average plays per artist: {avg_plays:.1f}")
    print(f"   Median plays: {median_plays:,}")
    print(f"   Range: {artist_data[-1]['play_count']:,} - {artist_data[0]['play_count']:,}")
    
    print(f"\n✅ Artist data is ready for network analysis!")


if __name__ == "__main__":
    main()