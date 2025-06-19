#!/usr/bin/env python3
"""
Debug Real Artist Data
======================
Examine the actual artist data being used in the interactive test
to understand why our priority fixes aren't working.
"""

from simplified_genre_colors import classify_artist_genre, get_multi_genres, GENRE_MAPPINGS
import json

def debug_scoring_process(artist_name, artist_data):
    """Debug the scoring process step by step for real artist data."""
    print(f"\n🔍 DEBUGGING: {artist_name}")
    print("=" * 60)
    
    # Show raw data
    print("📊 RAW DATA:")
    if artist_data.get('lastfm_data'):
        lastfm_tags = [tag['name'] for tag in artist_data['lastfm_data'].get('tags', [])]
        print(f"  Last.fm tags: {lastfm_tags}")
    if artist_data.get('spotify_data'):
        spotify_genres = artist_data['spotify_data'].get('genres', [])
        print(f"  Spotify genres: {spotify_genres}")
    
    # Collect source data with weights
    source_data = []
    
    # Spotify genres (higher authority)
    if artist_data.get('spotify_data') and artist_data['spotify_data'].get('genres'):
        spotify_genres = [genre.lower() for genre in artist_data['spotify_data']['genres'][:5]]
        for genre in spotify_genres:
            source_data.append({'tag': genre, 'source': 'spotify', 'weight': 2.0})
    
    # Last.fm tags (lower authority)
    if artist_data.get('lastfm_data') and artist_data['lastfm_data'].get('tags'):
        lastfm_genres = [tag['name'].lower() for tag in artist_data['lastfm_data']['tags'][:5]]
        for genre in lastfm_genres:
            source_data.append({'tag': genre, 'source': 'lastfm', 'weight': 1.0})
    
    print(f"\n🏷️  WEIGHTED SOURCE DATA:")
    for item in source_data:
        print(f"  {item['tag']} (source: {item['source']}, weight: {item['weight']})")
    
    # Priority keywords
    PRIORITY_KEYWORDS = {
        'asian': ['k-pop', 'kpop', 'j-pop', 'jpop', 'korean', 'japanese', 'chinese', 'c-pop'],
        'pop': ['pop', 'dance pop', 'electropop', 'teen pop'],
        'country': ['country', 'americana', 'bluegrass', 'country pop'], 
        'electronic': ['electronic', 'edm', 'house', 'techno', 'dubstep'],
        'rock': ['rock', 'alternative rock', 'indie rock', 'hard rock']
    }
    
    # Score each genre category with detailed logging
    genre_scores = {}
    detailed_scoring = {}
    
    for item in source_data:
        tag = item['tag'].strip()
        source_weight = item['weight']
        
        print(f"\n🔍 Processing tag: '{tag}' (weight: {source_weight})")
        
        for category, keywords in GENRE_MAPPINGS.items():
            category_score = 0
            matches = []
            
            for keyword in keywords:
                if keyword in tag:
                    # Base score with source weighting
                    score = source_weight
                    
                    # Priority boost for highly specific keywords
                    if category in PRIORITY_KEYWORDS and keyword in PRIORITY_KEYWORDS[category]:
                        score *= 2.0  # Double score for priority keywords
                        matches.append(f"'{keyword}' (PRIORITY x{score})")
                    else:
                        matches.append(f"'{keyword}' (x{score})")
                    
                    # Exact match bonus
                    if keyword == tag:
                        score *= 1.5
                        matches[-1] += " [EXACT]"
                    
                    category_score += score
                    print(f"   ✅ {category}: '{tag}' matches '{keyword}' -> +{score}")
                    break  # Only count once per category
            
            if category_score > 0:
                genre_scores[category] = genre_scores.get(category, 0) + category_score
                if category not in detailed_scoring:
                    detailed_scoring[category] = []
                detailed_scoring[category].extend(matches)
    
    print(f"\n📊 FINAL SCORES:")
    sorted_scores = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)
    for genre, score in sorted_scores:
        print(f"  {genre}: {score} (matches: {detailed_scoring.get(genre, [])})")
    
    # Show what current system returns
    actual_primary = classify_artist_genre(artist_data)
    actual_multi = get_multi_genres(artist_data, max_genres=2)
    
    print(f"\n🎯 RESULTS:")
    print(f"  Primary: {actual_primary}")
    print(f"  Multi: {actual_multi}")
    
    return genre_scores, actual_primary, actual_multi

def test_problematic_artists():
    """Test the specific artists that are failing."""
    print("🐛 DEBUGGING PROBLEMATIC ARTISTS")
    print("=" * 60)
    
    # Mock the problematic artist data based on user results
    problematic_cases = {
        "Taylor Swift": {
            "result": "country + ['pop']",
            "expected": "pop + ['country']",
            # We need to guess what the real data looks like based on the result
            "mock_data": {
                'lastfm_data': {'tags': [
                    {'name': 'country'}, {'name': 'pop'}, {'name': 'folk'}, 
                    {'name': 'singer-songwriter'}, {'name': 'female vocalists'}
                ]},
                'spotify_data': {'genres': ['country pop', 'pop']}
            }
        },
        "IVE": {
            "result": "pop + ['asian']", 
            "expected": "asian + ['pop']",
            "mock_data": {
                'lastfm_data': {'tags': [
                    {'name': 'pop'}, {'name': 'k-pop'}, {'name': 'korean'}, 
                    {'name': 'girl group'}, {'name': 'dance'}
                ]},
                'spotify_data': {'genres': ['pop', 'k-pop']}
            }
        }
    }
    
    for artist, case in problematic_cases.items():
        print(f"\n{'='*60}")
        print(f"🎤 {artist}")
        print(f"Current result: {case['result']}")
        print(f"Expected: {case['expected']}")
        
        scores, primary, multi = debug_scoring_process(artist, case["mock_data"])
        
        # Analyze the problem
        print(f"\n❗ ANALYSIS:")
        if primary != case['expected'].split(' + ')[0]:
            primary_expected = case['expected'].split(' + ')[0]
            primary_score = scores.get(primary, 0)
            expected_score = scores.get(primary_expected, 0)
            
            print(f"  Expected '{primary_expected}' scored: {expected_score}")
            print(f"  Got '{primary}' scored: {primary_score}")
            
            if expected_score > 0:
                ratio = primary_score / expected_score if expected_score > 0 else float('inf')
                print(f"  Score ratio (actual/expected): {ratio:.2f}")
                
                if ratio > 1:
                    print(f"  🔍 Issue: '{primary}' legitimately scored higher")
                    print(f"  💡 Need stronger priority weighting for '{primary_expected}'")
                else:
                    print(f"  🔍 Issue: Tie-breaking or scoring logic problem")

if __name__ == "__main__":
    test_problematic_artists()