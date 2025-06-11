"""
Debug Artist Names
==================

Debug the artist name matching issue in Phase 1B.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime, timedelta
from data_processor import prepare_data_for_bar_chart_race, split_artist_collaborations
from network_utils import prepare_dataframe_for_network_analysis


def debug_artist_names():
    """Debug the artist name issue."""
    print("=" * 80)
    print("DEBUGGING ARTIST NAME MATCHING")
    print("=" * 80)
    
    # Create simple test data
    base_date = datetime.now() - timedelta(days=30)
    test_data = [
        {
            'timestamp': base_date,
            'artist': 'taylor swift feat. ed sheeran',
            'original_artist': 'Taylor Swift feat. Ed Sheeran',
            'track': 'song1',
            'original_track': 'Song 1',
            'album': 'album1'
        },
        {
            'timestamp': base_date + timedelta(days=1),
            'artist': 'taylor swift',
            'original_artist': 'Taylor Swift',
            'track': 'song2', 
            'original_track': 'Song 2',
            'album': 'album1'
        }
    ]
    
    df = pd.DataFrame(test_data)
    print(f"Original data:")
    for _, row in df.iterrows():
        print(f"   '{row['artist']}' (original: '{row['original_artist']}')")
    
    # Process data
    print(f"\nProcessing data in artist mode...")
    race_df, artist_details = prepare_data_for_bar_chart_race(df, mode="artists")
    
    print(f"\nRace DataFrame columns (artists):")
    for col in sorted(race_df.columns):
        print(f"   '{col}'")
    
    print(f"\nArtist details map:")
    for artist_id, details in artist_details.items():
        display_name = details.get('display_name', 'N/A')
        print(f"   '{artist_id}' → display: '{display_name}'")
    
    # Check network dataframe
    print(f"\nPreparing network DataFrame...")
    df_network = prepare_dataframe_for_network_analysis(df)
    
    print(f"\nNetwork DataFrame unique artists:")
    unique_artists = df_network['artist'].unique()
    for artist in sorted(unique_artists):
        print(f"   '{artist}'")
    
    # Test matching
    print(f"\nTesting artist matching:")
    for race_artist in race_df.columns:
        # Try exact match
        exact_matches = df_network[df_network['artist'] == race_artist]
        print(f"\n   Race artist: '{race_artist}'")
        print(f"   Exact matches: {len(exact_matches)}")
        
        # Try case-insensitive match
        case_matches = df_network[df_network['artist'].str.lower() == race_artist.lower()]
        print(f"   Case-insensitive matches: {len(case_matches)}")
        
        if len(case_matches) > 0:
            print(f"   Network artist values: {case_matches['artist'].unique()}")


if __name__ == '__main__':
    debug_artist_names()