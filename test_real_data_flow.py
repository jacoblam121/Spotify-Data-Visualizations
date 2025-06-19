#!/usr/bin/env python3
"""
Test Real Data Flow
===================
Test the genre classification with the actual data loading and network generation
that the interactive test uses, but without the interactive menu.
"""

import sys
import os
import pandas as pd
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from network_utils import initialize_network_analyzer
from simplified_genre_colors import classify_artist_genre, get_multi_genres

def load_user_data():
    """Load user's actual music data like the interactive test does."""
    print("🔍 Looking for user music data...")
    
    # Check for Spotify data files
    spotify_files = list(Path('.').glob('*StreamingHistory*.json'))
    if spotify_files:
        print(f"Found Spotify data: {spotify_files[0]}")
        try:
            import json
            with open(spotify_files[0], 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            df = pd.DataFrame(data)
            if 'master_metadata_album_artist_name' in df.columns:
                df['artist'] = df['master_metadata_album_artist_name']
            elif 'artistName' in df.columns:
                df['artist'] = df['artistName']
            
            print(f"Loaded {len(df)} records from Spotify data")
            return df
        except Exception as e:
            print(f"Error loading Spotify data: {e}")
    
    # Check for Last.fm data
    lastfm_file = Path('lastfm_data.csv')
    if lastfm_file.exists():
        print(f"Found Last.fm data: {lastfm_file}")
        try:
            df = pd.read_csv(lastfm_file, encoding='utf-8')
            print(f"Loaded {len(df)} records from Last.fm data")
            return df
        except Exception as e:
            print(f"Error loading Last.fm data: {e}")
    
    print("❌ No user music data found")
    return None

def test_real_genre_classification():
    """Test genre classification with real user data."""
    print("🧪 TESTING REAL DATA GENRE CLASSIFICATION")
    print("=" * 60)
    
    # Load real user data
    df = load_user_data()
    if df is None:
        print("Cannot test without user data")
        return
    
    # Get top artists from real data
    if 'artist' in df.columns:
        top_artists = df['artist'].value_counts().head(10)
        print(f"\n📊 Top 10 artists in user data:")
        for artist, count in top_artists.items():
            print(f"  {artist}: {count} plays")
    else:
        print("❌ No artist column found")
        return
    
    # Initialize network analyzer with real config
    print(f"\n🌐 Initializing network analyzer...")
    try:
        analyzer = initialize_network_analyzer()
        print("✅ Network analyzer initialized")
    except Exception as e:
        print(f"❌ Error initializing analyzer: {e}")
        return
    
    # Generate network data with real user data
    print(f"\n🔗 Generating network with real data...")
    try:
        network_data = analyzer.create_network_data(
            df, 
            top_n_artists=20,  # Smaller number for testing
            min_plays_threshold=5,
            min_similarity_threshold=0.2
        )
        
        if network_data and 'nodes' in network_data:
            print(f"✅ Generated network with {len(network_data['nodes'])} nodes")
            
            # Test genre classification on real artists
            print(f"\n🎤 TESTING GENRE CLASSIFICATION ON REAL ARTISTS:")
            print("-" * 50)
            
            problem_artists = ["Taylor Swift", "IVE", "Paramore", "Yorushika", "IU"]
            
            for node in network_data['nodes'][:15]:  # Test first 15 artists
                artist_name = node.get('name', 'Unknown')
                
                # Check if this artist has genre data
                if 'primary_genre' in node:
                    primary = node['primary_genre']
                    secondary = node.get('secondary_genres', [])
                    
                    result_str = f"{primary} + {secondary}"
                    print(f"  {artist_name}: {result_str}")
                    
                    # Highlight problem artists
                    if artist_name in problem_artists:
                        print(f"    🎯 PROBLEM ARTIST DETECTED!")
                        
                        # Show the raw data that was used
                        if 'artist_data' in node:
                            raw_data = node['artist_data']
                            print(f"    Raw data keys: {list(raw_data.keys())}")
                            
                            if 'spotify_data' in raw_data:
                                spotify_genres = raw_data['spotify_data'].get('genres', [])
                                print(f"    Spotify genres: {spotify_genres}")
                            
                            if 'lastfm_data' in raw_data:
                                lastfm_tags = [tag['name'] for tag in raw_data['lastfm_data'].get('tags', [])]
                                print(f"    Last.fm tags: {lastfm_tags}")
                            
                            # Test our classification function directly
                            our_primary = classify_artist_genre(raw_data)
                            our_multi = get_multi_genres(raw_data, max_genres=2)
                            our_result = f"{our_primary} + {our_multi[1:] if len(our_multi) > 1 else []}"
                            print(f"    Our function result: {our_result}")
                            print(f"    Match: {'✅' if our_result == result_str else '❌'}")
                
        else:
            print("❌ Failed to generate network data")
            
    except Exception as e:
        print(f"❌ Error generating network: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_genre_classification()