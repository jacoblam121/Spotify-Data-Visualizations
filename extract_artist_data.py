#!/usr/bin/env python3
"""
Extract Artist Data from Spotify Streaming History
==================================================

This script extracts processed artist data (name and play_count) from the Spotify
streaming history and saves it to a JSON file. This is the data structure used
by the network analysis tools.
"""

import json
import pandas as pd
from typing import List, Dict
from data_processor import clean_and_filter_data
from config_loader import AppConfig
from network_utils import prepare_dataframe_for_network_analysis


def extract_artist_data(top_n: int = 100, min_plays: int = 5, 
                       output_file: str = 'artist_data.json') -> List[Dict]:
    """
    Extract artist data with play counts from Spotify streaming history.
    
    Args:
        top_n: Number of top artists to include
        min_plays: Minimum play count threshold
        output_file: Output JSON file path
        
    Returns:
        List of artist dictionaries with 'name' and 'play_count' fields
    """
    print("🎵 Extracting Artist Data from Spotify History")
    print("=" * 50)
    
    try:
        # Load and process data
        print("📁 Loading Spotify streaming history...")
        config = AppConfig('configurations.txt')
        df = clean_and_filter_data(config)
        
        if df.empty:
            print("❌ No data loaded")
            return []
        
        # Prepare for network analysis (sets timestamp as index)
        df_network = prepare_dataframe_for_network_analysis(df)
        
        print(f"✅ Loaded {len(df_network):,} listening records")
        print(f"📊 Data spans: {df_network.index.min()} to {df_network.index.max()}")
        print(f"🎤 Unique artists: {df_network['artist'].nunique():,}")
        
        # Calculate artist play counts
        print(f"\n📈 Calculating artist play counts...")
        artist_plays = df_network.groupby('artist').size().sort_values(ascending=False)
        
        # Filter by minimum plays
        artist_plays_filtered = artist_plays[artist_plays >= min_plays]
        print(f"🔍 Artists with at least {min_plays} plays: {len(artist_plays_filtered)}")
        
        # Get top N artists
        top_artists = artist_plays_filtered.head(top_n)
        print(f"🎯 Selecting top {len(top_artists)} artists")
        
        # Convert to the format expected by network tools
        artist_data = []
        for i, (artist_name, play_count) in enumerate(top_artists.items(), 1):
            artist_data.append({
                'name': artist_name,
                'play_count': int(play_count),
                'rank': i
            })
        
        # Display sample
        print(f"\n📋 Top 10 artists:")
        for i, artist in enumerate(artist_data[:10]):
            print(f"  {i+1:2d}. {artist['name']:<25} ({artist['play_count']:,} plays)")
        
        if len(artist_data) > 10:
            print(f"  ... and {len(artist_data) - 10} more artists")
        
        # Save to file
        print(f"\n💾 Saving artist data to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(artist_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(artist_data)} artists to {output_file}")
        
        # Print data statistics
        print(f"\n📊 Data Statistics:")
        print(f"   Total artists: {len(artist_data)}")
        print(f"   Play count range: {artist_data[-1]['play_count']} - {artist_data[0]['play_count']}")
        print(f"   Average plays: {sum(a['play_count'] for a in artist_data) / len(artist_data):.1f}")
        
        return artist_data
        
    except Exception as e:
        print(f"❌ Error extracting artist data: {e}")
        import traceback
        traceback.print_exc()
        return []


def load_artist_data(file_path: str = 'artist_data.json') -> List[Dict]:
    """
    Load artist data from JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of artist dictionaries
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        return []


def main():
    """Main function for interactive or command-line usage."""
    import sys
    
    # Parse command line arguments
    top_n = 100
    min_plays = 5
    
    if len(sys.argv) > 1:
        try:
            top_n = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid number for top_n")
            return
    
    if len(sys.argv) > 2:
        try:
            min_plays = int(sys.argv[2])
        except ValueError:
            print("❌ Invalid number for min_plays")
            return
    
    # Extract artist data
    artist_data = extract_artist_data(top_n=top_n, min_plays=min_plays)
    
    if artist_data:
        print(f"\n🎉 Successfully extracted artist data!")
        print(f"📄 Use this file with network analysis tools:")
        print(f"   artist_data = load_artist_data('artist_data.json')")
        print(f"   # Each item has: {{'name': 'Artist Name', 'play_count': 123, 'rank': 1}}")


if __name__ == "__main__":
    main()