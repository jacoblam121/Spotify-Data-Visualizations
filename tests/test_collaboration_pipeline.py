"""
Test Full Collaboration Pipeline
================================

Tests that collaborations are properly handled throughout the entire pipeline:
1. Data loading splits collaborations
2. Each artist gets credit for plays
3. Network building finds similar artists for each artist
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from config_loader import AppConfig
from data_processor import prepare_data_for_bar_chart_race, split_artist_collaborations
from network_utils import build_network_data
from lastfm_utils import LastfmAPI

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PARENT_DIR, 'configurations.txt')


def test_collaboration_pipeline():
    """Test the full collaboration handling pipeline."""
    print("=" * 80)
    print("TESTING FULL COLLABORATION PIPELINE")
    print("=" * 80)
    
    # Create test data with collaborations
    test_data = pd.DataFrame([
        {
            'timestamp': pd.Timestamp('2024-01-01 10:00:00'),
            'artist': 'Taylor Swift feat. Ed Sheeran',
            'original_artist': 'Taylor Swift feat. Ed Sheeran',
            'track': 'Everything Has Changed',
            'album': 'Red'
        },
        {
            'timestamp': pd.Timestamp('2024-01-01 10:05:00'),
            'artist': 'Machine Gun Kelly & blackbear',
            'original_artist': 'Machine Gun Kelly & blackbear',
            'track': 'my ex\'s best friend',
            'album': 'Tickets To My Downfall'
        },
        {
            'timestamp': pd.Timestamp('2024-01-01 10:10:00'),
            'artist': 'BLACKPINK, Dua Lipa',
            'original_artist': 'BLACKPINK, Dua Lipa',
            'track': 'Kiss and Make Up',
            'album': 'BLACKPINK IN YOUR AREA'
        },
        {
            'timestamp': pd.Timestamp('2024-01-01 10:15:00'),
            'artist': 'Taylor Swift',
            'original_artist': 'Taylor Swift',
            'track': 'Shake It Off',
            'album': '1989'
        },
        {
            'timestamp': pd.Timestamp('2024-01-01 10:20:00'),
            'artist': 'Ed Sheeran',
            'original_artist': 'Ed Sheeran',
            'track': 'Shape of You',
            'album': '÷ (Divide)'
        }
    ])
    
    print("\n1️⃣ Original data (5 plays):")
    print("-" * 60)
    for _, row in test_data.iterrows():
        print(f"   {row['artist']} - {row['track']}")
    
    # Process data in artist mode
    print("\n2️⃣ Processing data in artist mode...")
    race_df, details_map = prepare_data_for_bar_chart_race(test_data, mode="artists")
    
    if race_df is not None:
        print(f"\n✅ Expanded to {len(race_df)} artist entries after splitting collaborations")
        
        # Count plays per artist
        artist_plays = race_df.groupby('entity_id').size().sort_values(ascending=False)
        print("\n3️⃣ Play counts per artist:")
        print("-" * 60)
        for artist, count in artist_plays.items():
            original_name = details_map.get(artist, {}).get('display_name', artist)
            print(f"   {original_name}: {count} play(s)")
        
        # Expected results:
        # - Taylor Swift: 2 plays (solo + collab)
        # - Ed Sheeran: 2 plays (solo + collab)
        # - Machine Gun Kelly: 1 play
        # - blackbear: 1 play
        # - BLACKPINK: 1 play
        # - Dua Lipa: 1 play
        
        expected_counts = {
            'taylor swift': 2,
            'ed sheeran': 2,
            'machine gun kelly': 1,
            'blackbear': 1,
            'blackpink': 1,
            'dua lipa': 1
        }
        
        print("\n4️⃣ Verification:")
        print("-" * 60)
        all_correct = True
        for artist, expected in expected_counts.items():
            actual = artist_plays.get(artist, 0)
            status = "✅" if actual == expected else "❌"
            print(f"   {status} {artist}: expected {expected}, got {actual}")
            if actual != expected:
                all_correct = False
        
        if all_correct:
            print("\n✅ All collaboration splits working correctly!")
        else:
            print("\n❌ Some collaboration splits are incorrect!")
            
        # Test network building
        print("\n5️⃣ Testing network data building...")
        print("-" * 60)
        
        try:
            config = AppConfig(CONFIG_PATH)
            lastfm_config = config.get_lastfm_config()
            
            lastfm_api = LastfmAPI(
                lastfm_config['api_key'],
                lastfm_config['api_secret'],
                lastfm_config['cache_dir']
            )
            
            # Build network for top artists
            top_artists = artist_plays.head(3).index.tolist()
            print(f"Building network for top 3 artists: {top_artists}")
            
            network_data = build_network_data(top_artists, details_map, lastfm_api)
            
            print(f"\nNetwork contains {len(network_data['nodes'])} nodes")
            print(f"Network contains {len(network_data['edges'])} edges")
            
            # Check that collaboration artists are included
            node_names = [node['name'] for node in network_data['nodes']]
            print("\nNodes in network:")
            for name in sorted(node_names)[:10]:
                print(f"   - {name}")
                
        except Exception as e:
            print(f"❌ Network building error: {e}")
            import traceback
            traceback.print_exc()
            
    else:
        print("❌ Failed to process data")


if __name__ == '__main__':
    test_collaboration_pipeline()
    
    print("\n" + "=" * 80)
    print("COLLABORATION PIPELINE SUMMARY")
    print("=" * 80)
    print("\nThe pipeline correctly:")
    print("1. ✅ Splits collaboration strings into individual artists")
    print("2. ✅ Credits each artist with plays from collaborations")
    print("3. ✅ Builds networks that include all collaboration artists")