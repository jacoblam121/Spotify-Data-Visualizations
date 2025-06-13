#!/usr/bin/env python3
"""
Debug script to trace exactly what happens with IU and BOL4 in network generation.
Since the Last.fm relationship exists, we need to find where it gets lost.
"""

import os
import sys
os.chdir('/home/jacob/Spotify-Data-Visualizations')

import pandas as pd
from data_processor import clean_and_filter_data
from network_utils import initialize_network_analyzer, prepare_dataframe_for_network_analysis

def debug_iu_bol4_network():
    """Debug the specific IU ↔ BOL4 relationship in network generation."""
    print("🔍 Debugging IU ↔ BOL4 in network generation pipeline")
    print("=" * 60)
    
    # Load data
    print("📂 Loading data...")
    try:
        from config_loader import AppConfig
        config = AppConfig()
        df = clean_and_filter_data(config)
        df_network = prepare_dataframe_for_network_analysis(df)
        print(f"   ✅ Loaded {len(df_network)} plays")
    except Exception as e:
        print(f"   ❌ Failed to load data: {e}")
        return
    
    # Check if IU and BOL4 are in the data
    artist_counts = df_network['artist'].value_counts()
    
    iu_count = 0
    bol4_count = 0
    iu_name_in_data = None
    bol4_name_in_data = None
    
    for artist, count in artist_counts.items():
        artist_upper = artist.upper()
        if 'IU' in artist_upper or '아이유' in artist or artist.strip().upper() == 'IU':
            if count > iu_count:
                iu_count = count
                iu_name_in_data = artist
        if 'BOL4' in artist_upper or 'BOLBBALGAN' in artist_upper or '볼빨간' in artist:
            if count > bol4_count:
                bol4_count = count
                bol4_name_in_data = artist
    
    print(f"\n🎵 Artists in data:")
    print(f"   IU variant: '{iu_name_in_data}' ({iu_count} plays)")
    print(f"   BOL4 variant: '{bol4_name_in_data}' ({bol4_count} plays)")
    
    # Show some similar artists for debugging
    print(f"\n📋 Searching for similar artist names...")
    for artist, count in artist_counts.head(50).items():
        if any(keyword in artist.lower() for keyword in ['iu', 'bolb', 'bol4', '아이유', '볼빨간']):
            print(f"   Found: '{artist}' ({count} plays)")
    
    if not iu_name_in_data or not bol4_name_in_data:
        print("❌ One or both artists not found in data")
        return
    
    # Initialize network analyzer
    print(f"\n🕸️  Initializing network analyzer...")
    analyzer = initialize_network_analyzer()
    
    # Create a small network with just these two artists for debugging
    print(f"\n🔬 Creating focused test network...")
    
    # Filter to just top artists including our targets
    top_artists = artist_counts.head(20)
    
    # Make sure IU and BOL4 are included
    if iu_name_in_data not in top_artists.index:
        top_artists[iu_name_in_data] = iu_count
    if bol4_name_in_data not in top_artists.index:
        top_artists[bol4_name_in_data] = bol4_count
    
    print(f"   📊 Test network will include {len(top_artists)} artists")
    
    # Get enhanced artist data specifically for these two
    print(f"\n🔍 Fetching enhanced artist data...")
    test_artists = [iu_name_in_data, bol4_name_in_data]
    
    enhanced_data = analyzer.artist_fetcher.batch_fetch_artist_data(
        test_artists,
        include_similar=True
    )
    
    # Analyze the enhanced data
    print(f"\n📋 Enhanced data analysis:")
    for i, artist_name in enumerate(test_artists):
        data = enhanced_data[i]
        print(f"\n   🎵 {artist_name}:")
        print(f"      Success: {data['success']}")
        print(f"      Canonical name: {data['canonical_name']}")
        
        if data['similar_artists']:
            print(f"      Similar artists: {len(data['similar_artists'])}")
            
            # Look for the other artist in similar list
            other_artist = bol4_name_in_data if artist_name == iu_name_in_data else iu_name_in_data
            found_matches = []
            
            for similar in data['similar_artists']:
                similar_name = similar['name']
                similarity = similar['match']
                
                # Check if this matches the other artist
                if artist_name == iu_name_in_data and ('BOL4' in similar_name or 'Bolbbalgan' in similar_name):
                    found_matches.append((similar_name, similarity))
                elif artist_name == bol4_name_in_data and ('IU' in similar_name or '아이유' in similar_name):
                    found_matches.append((similar_name, similarity))
            
            if found_matches:
                print(f"      🎯 MATCHES FOUND:")
                for match_name, similarity in found_matches:
                    print(f"         {match_name} (similarity: {similarity})")
            else:
                print(f"      ❌ No matches for other artist")
                print(f"      📋 Top 5 similar artists:")
                for similar in data['similar_artists'][:5]:
                    print(f"         {similar['name']} ({similar['match']})")
        else:
            print(f"      ❌ No similar artists found")
    
    # Test the bidirectional similarity matrix logic
    print(f"\n🔗 Testing bidirectional similarity matrix logic...")
    
    similarity_matrix = {}
    artist_list = test_artists
    
    for data in enhanced_data:
        source_artist = data['artist_name']
        similarity_matrix[source_artist] = {}
        
        if data['similar_artists']:
            for similar in data['similar_artists']:
                target_artist = similar['name']
                similarity_score = similar['match']
                
                # Check if target is in our test list (with fuzzy matching)
                matched_target = None
                for test_artist in artist_list:
                    if (target_artist.upper() == test_artist.upper() or 
                        'BOL4' in target_artist and 'BOL4' in test_artist.upper() or
                        'IU' in target_artist and 'IU' in test_artist.upper()):
                        matched_target = test_artist
                        break
                
                if matched_target:
                    similarity_matrix[source_artist][matched_target] = similarity_score
                    print(f"      ✅ Added: {source_artist} → {matched_target} = {similarity_score}")
    
    # Check bidirectional connections
    print(f"\n🔄 Checking bidirectional connections:")
    for i, artist_a in enumerate(artist_list):
        for j, artist_b in enumerate(artist_list):
            if i >= j:  # Skip same artist and avoid duplicates
                continue
            
            similarity_ab = similarity_matrix.get(artist_a, {}).get(artist_b, 0)
            similarity_ba = similarity_matrix.get(artist_b, {}).get(artist_a, 0)
            max_similarity = max(similarity_ab, similarity_ba)
            
            print(f"   {artist_a} ↔ {artist_b}:")
            print(f"      A→B: {similarity_ab}")
            print(f"      B→A: {similarity_ba}")
            print(f"      Max: {max_similarity}")
            
            if max_similarity > 0:
                print(f"      🎉 EDGE WOULD BE CREATED! (weight: {max_similarity})")
            else:
                print(f"      ❌ No edge (both directions = 0)")

if __name__ == "__main__":
    debug_iu_bol4_network()