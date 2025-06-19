#!/usr/bin/env python3
"""
Hierarchical Genre Classification Fix
====================================
Implements semantic hierarchy where cultural/regional genres 
(asian, latin) trump generic genres (pop, rock) when specific 
keywords are present.
"""

import re
from collections import defaultdict

# Genre hierarchy - higher numbers = higher priority
GENRE_HIERARCHY = {
    'asian': 10,      # Highest priority - cultural specificity
    'latin': 10,      # Highest priority - cultural specificity
    'world': 9,       # High priority - cultural/regional
    'country': 8,     # High priority - distinct American cultural genre
    'folk': 7,        # Medium-high priority - traditional/cultural
    'classical': 7,   # Medium-high priority - distinct musical tradition
    'metal': 6,       # Medium priority - very specific style
    'rock': 5,        # Medium priority - broad but established
    'electronic': 5,  # Medium priority - broad but established  
    'hip-hop': 5,     # Medium priority - broad but established
    'r&b': 4,         # Lower priority - often overlaps with pop
    'indie': 3,       # Lower priority - more of a descriptor
    'pop': 2,         # Low priority - very generic
    'other': 1,       # Lowest priority
    'unknown': 0      # Fallback
}

# Specific keywords that should immediately determine genre
EXCLUSIVE_KEYWORDS = {
    'asian': {
        'k-pop', 'kpop', 'korean pop', 'k pop',
        'j-pop', 'jpop', 'japanese pop', 'j pop',
        'c-pop', 'cpop', 'chinese pop', 'c pop',
        'korean', 'japanese', 'chinese', 'thai', 'vietnamese'
    },
    'latin': {
        'reggaeton', 'bachata', 'salsa', 'merengue', 'cumbia',
        'latin pop', 'latin rock', 'latin alternative',
        'spanish pop', 'mexican', 'argentinian', 'brazilian'
    },
    'country': {
        'country pop', 'country rock', 'country alternative',
        'americana', 'bluegrass', 'country music'
    },
    'metal': {
        'death metal', 'black metal', 'heavy metal', 'thrash metal',
        'metalcore', 'doom metal', 'power metal'
    },
    'electronic': {
        'edm', 'house music', 'techno', 'dubstep', 'trance',
        'drum and bass', 'synthpop', 'synthwave'
    },
    'hip-hop': {
        'hip hop', 'hip-hop', 'rap music', 'trap music',
        'gangsta rap', 'conscious rap', 'old school rap'
    },
    'classical': {
        'classical music', 'orchestral', 'symphony', 'opera',
        'baroque', 'romantic classical', 'film score'
    }
}

def classify_artist_genre_hierarchical(artist_data) -> str:
    """
    Classify artist using hierarchical semantic rules.
    
    Priority:
    1. Exclusive keywords (k-pop -> asian always)
    2. Exact genre matches with hierarchy weighting
    3. Substring matches with hierarchy weighting
    4. Source authority (Spotify > Last.fm)
    """
    
    # Collect all genre tags from both sources
    all_genres = []
    
    # Spotify genres (higher authority but not always available)
    if artist_data.get('spotify_data') and artist_data['spotify_data'].get('genres'):
        spotify_genres = [genre.lower().strip() for genre in artist_data['spotify_data']['genres'][:5]]
        for genre in spotify_genres:
            all_genres.append({'tag': genre, 'source': 'spotify', 'authority': 2.0})
    
    # Last.fm tags (lower authority but more comprehensive)
    if artist_data.get('lastfm_data') and artist_data['lastfm_data'].get('tags'):
        lastfm_genres = [tag['name'].lower().strip() for tag in artist_data['lastfm_data']['tags'][:5]]
        for genre in lastfm_genres:
            all_genres.append({'tag': genre, 'source': 'lastfm', 'authority': 1.0})
    
    if not all_genres:
        return 'other'
    
    # Step 1: Check for exclusive keywords (immediate classification)
    for category, keywords in EXCLUSIVE_KEYWORDS.items():
        for item in all_genres:
            tag = item['tag']
            for keyword in keywords:
                if keyword in tag:
                    print(f"🎯 Exclusive match: '{tag}' contains '{keyword}' -> {category}")
                    return category
    
    # Step 2: Hierarchical scoring with semantic weights
    genre_scores = defaultdict(float)
    
    # Import the genre mappings
    from simplified_genre_colors import GENRE_MAPPINGS
    
    for item in all_genres:
        tag = item['tag']
        authority = item['authority']
        
        print(f"🔍 Processing: '{tag}' (authority: {authority})")
        
        for category, keywords in GENRE_MAPPINGS.items():
            category_hierarchy = GENRE_HIERARCHY.get(category, 1)
            
            for keyword in keywords:
                if keyword in tag:
                    # Base score: hierarchy weight * authority
                    base_score = category_hierarchy * authority
                    
                    # Exact match bonus
                    if keyword == tag:
                        base_score *= 2.0
                        print(f"   ✅ {category}: '{tag}' == '{keyword}' (EXACT) -> {base_score}")
                    else:
                        print(f"   ✅ {category}: '{tag}' contains '{keyword}' -> {base_score}")
                    
                    genre_scores[category] += base_score
                    break  # Only count once per category
    
    print(f"📊 Hierarchical scores: {dict(genre_scores)}")
    
    if genre_scores:
        # Return highest scoring genre
        primary_genre = max(genre_scores, key=genre_scores.get)
        print(f"🏆 Winner: {primary_genre} (score: {genre_scores[primary_genre]})")
        return primary_genre
    
    return 'other'

def get_multi_genres_hierarchical(artist_data, max_genres: int = 2) -> list:
    """
    Get multi-genres with hierarchical prioritization.
    """
    # Use the same logic as primary classification but return top N
    all_genres = []
    
    # Collect genres
    if artist_data.get('spotify_data') and artist_data['spotify_data'].get('genres'):
        spotify_genres = [genre.lower().strip() for genre in artist_data['spotify_data']['genres'][:5]]
        for genre in spotify_genres:
            all_genres.append({'tag': genre, 'source': 'spotify', 'authority': 2.0})
    
    if artist_data.get('lastfm_data') and artist_data['lastfm_data'].get('tags'):
        lastfm_genres = [tag['name'].lower().strip() for tag in artist_data['lastfm_data']['tags'][:5]]
        for genre in lastfm_genres:
            all_genres.append({'tag': genre, 'source': 'lastfm', 'authority': 1.0})
    
    if not all_genres:
        return ['other']
    
    # Check for exclusive keywords first
    for category, keywords in EXCLUSIVE_KEYWORDS.items():
        for item in all_genres:
            tag = item['tag']
            for keyword in keywords:
                if keyword in tag:
                    # Found exclusive match - this becomes primary, find one secondary
                    secondary_scores = defaultdict(float)
                    
                    from simplified_genre_colors import GENRE_MAPPINGS
                    
                    for item2 in all_genres:
                        tag2 = item2['tag']
                        authority2 = item2['authority']
                        
                        for cat2, keywords2 in GENRE_MAPPINGS.items():
                            if cat2 == category:  # Skip the primary genre
                                continue
                                
                            cat2_hierarchy = GENRE_HIERARCHY.get(cat2, 1)
                            
                            for kw2 in keywords2:
                                if kw2 in tag2:
                                    score = cat2_hierarchy * authority2
                                    if kw2 == tag2:
                                        score *= 2.0
                                    secondary_scores[cat2] += score
                                    break
                    
                    # Return primary + best secondary
                    if secondary_scores and max_genres > 1:
                        best_secondary = max(secondary_scores, key=secondary_scores.get)
                        return [category, best_secondary][:max_genres]
                    else:
                        return [category]
    
    # No exclusive matches - use hierarchical scoring
    genre_scores = defaultdict(float)
    
    from simplified_genre_colors import GENRE_MAPPINGS
    
    for item in all_genres:
        tag = item['tag']
        authority = item['authority']
        
        for category, keywords in GENRE_MAPPINGS.items():
            category_hierarchy = GENRE_HIERARCHY.get(category, 1)
            
            for keyword in keywords:
                if keyword in tag:
                    base_score = category_hierarchy * authority
                    if keyword == tag:
                        base_score *= 2.0
                    genre_scores[category] += base_score
                    break
    
    if genre_scores:
        # Sort by score and return top N
        sorted_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)
        return [genre for genre, score in sorted_genres[:max_genres]]
    
    return ['other']

def test_hierarchical_fix():
    """Test the hierarchical fix with the problem cases."""
    print("🧪 TESTING HIERARCHICAL GENRE CLASSIFICATION")
    print("=" * 60)
    
    test_cases = {
        "Taylor Swift": {
            # Real data from network output
            'lastfm_data': {'tags': [
                {'name': 'country'}, {'name': 'pop'}, {'name': 'female vocalists'}
            ]},
            'spotify_data': {'genres': []}  # Empty like in real data
        },
        "IVE": {
            # Simulated real data
            'lastfm_data': {'tags': [
                {'name': 'k-pop'}, {'name': 'korean'}, {'name': 'pop'}, {'name': 'girl group'}
            ]},
            'spotify_data': {'genres': ['k-pop', 'pop']}
        },
        "Paramore": {
            # Simulated real data
            'lastfm_data': {'tags': [
                {'name': 'rock'}, {'name': 'pop punk'}, {'name': 'alternative'}
            ]},
            'spotify_data': {'genres': ['pop punk', 'emo']}
        }
    }
    
    for artist, data in test_cases.items():
        print(f"\n🎤 {artist}")
        print("-" * 40)
        
        primary = classify_artist_genre_hierarchical(data)
        multi = get_multi_genres_hierarchical(data, max_genres=2)
        
        result_str = f"{primary} + {multi[1:] if len(multi) > 1 else []}"
        print(f"Result: {result_str}")
        
        # Expected results
        expected = {
            "Taylor Swift": "pop + ['country']",  # pop should win due to hierarchy
            "IVE": "asian + ['pop']",             # asian should win due to k-pop exclusivity
            "Paramore": "rock + ['pop']"          # rock should win due to hierarchy
        }
        
        exp = expected.get(artist, "unknown")
        print(f"Expected: {exp}")
        print(f"Match: {'✅' if result_str == exp else '❌'}")

if __name__ == "__main__":
    test_hierarchical_fix()