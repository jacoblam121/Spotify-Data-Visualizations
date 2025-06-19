#!/usr/bin/env python3
"""
Isolated Test - Match Interactive Test Exactly
==============================================
This test uses the exact same flow as interactive_multi_genre_test.py
to see why we're getting different results.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simplified_genre_colors import classify_artist_genre, get_multi_genres

def test_isolated_artists():
    """Test the exact same way the interactive test does."""
    print("🔬 ISOLATED TEST - Matching Interactive Flow")
    print("=" * 60)
    
    # Create test data that might match what the interactive test is seeing
    test_artists = {
        "Taylor Swift": {
            # Possible real data based on user's result: "country + ['pop']"
            'lastfm_data': {'tags': [
                {'name': 'country'}, {'name': 'pop'}, {'name': 'singer-songwriter'}, 
                {'name': 'female vocalists'}, {'name': 'folk'}
            ]},
            'spotify_data': {'genres': ['country pop', 'pop']}
        },
        "IVE": {
            # Possible real data based on user's result: "pop + ['asian']"  
            'lastfm_data': {'tags': [
                {'name': 'pop'}, {'name': 'k-pop'}, {'name': 'korean'}, 
                {'name': 'girl group'}, {'name': 'dance'}
            ]},
            'spotify_data': {'genres': ['pop', 'k-pop']}
        },
        "Paramore": {
            # User result: "pop + ['rock']" - this seems wrong, should be rock primary
            'lastfm_data': {'tags': [
                {'name': 'pop punk'}, {'name': 'rock'}, {'name': 'alternative'}, 
                {'name': 'emo'}, {'name': 'female vocalists'}
            ]},
            'spotify_data': {'genres': ['pop punk', 'alternative rock']}
        }
    }
    
    for artist_name, artist_data in test_artists.items():
        print(f"\n🎤 {artist_name}")
        print("-" * 40)
        
        # Use the exact same function calls as interactive test
        primary_genre = classify_artist_genre(artist_data)
        multi_genres = get_multi_genres(artist_data, max_genres=2)
        
        result_string = f"{primary_genre} + {multi_genres[1:] if len(multi_genres) > 1 else []}"
        print(f"Result: {result_string}")
        
        # Check if this matches what user reported
        user_results = {
            "Taylor Swift": "country + ['pop']",
            "IVE": "pop + ['asian']", 
            "Paramore": "pop + ['rock']"
        }
        
        expected = user_results.get(artist_name, "unknown")
        matches_user = result_string == expected
        
        print(f"User reported: {expected}")
        print(f"Match: {'✅' if matches_user else '❌'}")
        
        if not matches_user:
            print(f"🔍 Difference detected - our test may have different data")

def test_with_raw_genre_lists():
    """Test with simple genre lists like the interactive test might use."""
    print(f"\n" + "="*60)
    print("🧪 TESTING WITH RAW GENRE LISTS")
    print("=" * 60)
    
    # Test with simplified data structures
    raw_test_cases = {
        "Taylor Swift - Raw": {
            'spotify_data': {'genres': ['country pop', 'pop']},
            'lastfm_data': {'tags': [{'name': 'country'}, {'name': 'pop'}]}
        },
        "IVE - Raw": {
            'spotify_data': {'genres': ['k-pop', 'pop']}, 
            'lastfm_data': {'tags': [{'name': 'k-pop'}, {'name': 'pop'}]}
        }
    }
    
    for name, data in raw_test_cases.items():
        print(f"\n🎯 {name}")
        primary = classify_artist_genre(data)
        multi = get_multi_genres(data, max_genres=2)
        print(f"  Primary: {primary}")
        print(f"  Multi: {multi}")
        print(f"  Result: {primary} + {multi[1:] if len(multi) > 1 else []}")

def debug_function_behavior():
    """Debug the actual function behavior step by step."""
    print(f"\n" + "="*60)
    print("🐛 DEBUGGING FUNCTION BEHAVIOR")
    print("=" * 60)
    
    # Test IVE case specifically
    ive_data = {
        'spotify_data': {'genres': ['k-pop', 'pop']},
        'lastfm_data': {'tags': [{'name': 'k-pop'}, {'name': 'pop'}]}
    }
    
    print("🎤 IVE Debug Case")
    print("Raw data:", ive_data)
    
    # Import the internal functions to debug
    from simplified_genre_colors import GENRE_MAPPINGS
    
    # Replicate the scoring logic manually
    source_data = []
    
    # Spotify genres (higher authority)
    if ive_data.get('spotify_data') and ive_data['spotify_data'].get('genres'):
        spotify_genres = [genre.lower() for genre in ive_data['spotify_data']['genres'][:5]]
        for genre in spotify_genres:
            source_data.append({'tag': genre, 'source': 'spotify', 'weight': 2.0})
    
    # Last.fm tags (lower authority)  
    if ive_data.get('lastfm_data') and ive_data['lastfm_data'].get('tags'):
        lastfm_genres = [tag['name'].lower() for tag in ive_data['lastfm_data']['tags'][:5]]
        for genre in lastfm_genres:
            source_data.append({'tag': genre, 'source': 'lastfm', 'weight': 1.0})
    
    print("Source data:", source_data)
    
    # Priority keywords
    PRIORITY_KEYWORDS = {
        'asian': ['k-pop', 'kpop', 'j-pop', 'jpop', 'korean', 'japanese', 'chinese', 'c-pop'],
        'pop': ['pop', 'dance pop', 'electropop', 'teen pop'],
        'country': ['country', 'americana', 'bluegrass', 'country pop'], 
        'electronic': ['electronic', 'edm', 'house', 'techno', 'dubstep'],
        'rock': ['rock', 'alternative rock', 'indie rock', 'hard rock']
    }
    
    # Score each genre category
    genre_scores = {}
    for item in source_data:
        tag = item['tag'].strip()
        source_weight = item['weight']
        
        print(f"\nProcessing: '{tag}' (weight: {source_weight})")
        
        for category, keywords in GENRE_MAPPINGS.items():
            for keyword in keywords:
                if keyword in tag:
                    # Base score with source weighting
                    score = source_weight
                    
                    # Priority boost for highly specific keywords
                    if category in PRIORITY_KEYWORDS and keyword in PRIORITY_KEYWORDS[category]:
                        score *= 2.0  # Double score for priority keywords
                        print(f"  {category}: '{tag}' -> '{keyword}' (PRIORITY) = {score}")
                    else:
                        print(f"  {category}: '{tag}' -> '{keyword}' = {score}")
                    
                    # Exact match bonus
                    if keyword == tag:
                        score *= 1.5
                        print(f"    EXACT MATCH BONUS: {score}")
                    
                    genre_scores[category] = genre_scores.get(category, 0) + score
                    break
    
    print(f"\nFinal scores: {genre_scores}")
    
    # Test actual function results
    actual_primary = classify_artist_genre(ive_data)
    actual_multi = get_multi_genres(ive_data, max_genres=2)
    
    print(f"Function results:")
    print(f"  Primary: {actual_primary}")
    print(f"  Multi: {actual_multi}")

if __name__ == "__main__":
    test_isolated_artists()
    test_with_raw_genre_lists()
    debug_function_behavior()