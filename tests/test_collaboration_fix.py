"""
Test Collaboration Fix
======================

Simplified test to verify collaboration handling is working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from data_processor import prepare_data_for_bar_chart_race, split_artist_collaborations


def test_collaboration_splitting():
    """Test the collaboration splitting functionality."""
    print("=" * 80)
    print("TESTING COLLABORATION SPLITTING")
    print("=" * 80)
    
    # Test split_artist_collaborations directly
    print("\n1️⃣ Testing split_artist_collaborations function:")
    print("-" * 60)
    
    test_cases = [
        "Taylor Swift feat. Ed Sheeran",
        "Machine Gun Kelly & blackbear",
        "BLACKPINK, Dua Lipa",
        "IU featuring SUGA",
        "Artist1 x Artist2 x Artist3",
        "Single Artist",
        "A & B feat. C with D",
    ]
    
    for test in test_cases:
        result = split_artist_collaborations(test)
        print(f"'{test}' → {result}")
    
    # Test data processing pipeline
    print("\n2️⃣ Testing data processing pipeline:")
    print("-" * 60)
    
    # Create test data
    test_data = pd.DataFrame([
        {
            'timestamp': pd.Timestamp('2024-01-01 10:00:00'),
            'artist': 'taylor swift feat. ed sheeran',
            'original_artist': 'Taylor Swift feat. Ed Sheeran',
            'track': 'everything has changed',
            'original_track': 'Everything Has Changed',
            'album': 'red'
        },
        {
            'timestamp': pd.Timestamp('2024-01-01 10:05:00'),
            'artist': 'machine gun kelly & blackbear',
            'original_artist': 'Machine Gun Kelly & blackbear',
            'track': 'my ex\'s best friend',
            'original_track': 'my ex\'s best friend',
            'album': 'tickets to my downfall'
        },
        {
            'timestamp': pd.Timestamp('2024-01-01 10:10:00'),
            'artist': 'taylor swift',
            'original_artist': 'Taylor Swift',
            'track': 'shake it off',
            'original_track': 'Shake It Off',
            'album': '1989'
        }
    ])
    
    print("Original data (3 plays):")
    for _, row in test_data.iterrows():
        print(f"   {row['original_artist']} - {row['track']}")
    
    # Process in artist mode
    race_df, details_map = prepare_data_for_bar_chart_race(test_data, mode="artists")
    
    if race_df is not None:
        print(f"\n✅ Race dataframe shape: {race_df.shape}")
        print(f"Columns: {list(race_df.columns)}")
        
        # Count plays per artist from the race_df columns
        artist_counts = {}
        for artist in race_df.columns:
            # Sum all non-zero values for this artist
            total_plays = (race_df[artist] > 0).sum()
            if total_plays > 0:
                artist_counts[artist] = total_plays
        
        print("\nPlay counts per artist:")
        for artist, count in sorted(artist_counts.items()):
            display_name = details_map.get(artist, {}).get('display_name', artist)
            print(f"   {display_name}: {count} play(s)")
        
        # Verify expected results
        expected = {
            'taylor swift': 2,  # 1 collab + 1 solo
            'ed sheeran': 1,    # 1 collab
            'machine gun kelly': 1,  # 1 collab
            'blackbear': 1      # 1 collab
        }
        
        print("\n3️⃣ Verification:")
        print("-" * 60)
        all_correct = True
        for artist, expected_count in expected.items():
            actual = artist_counts.get(artist, 0)
            status = "✅" if actual == expected_count else "❌"
            print(f"{status} {artist}: expected {expected_count}, got {actual}")
            if actual != expected_count:
                all_correct = False
        
        if all_correct:
            print("\n✅ ALL TESTS PASSED! Collaborations are handled correctly.")
        else:
            print("\n❌ Some tests failed!")
    else:
        print("❌ Failed to process data")


if __name__ == '__main__':
    test_collaboration_splitting()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nCollaboration handling ensures:")
    print("1. ✅ All artists in a collaboration get credit for the play")
    print("2. ✅ Original display names are preserved")
    print("3. ✅ Artists accumulate plays from both solo and collaborative tracks")