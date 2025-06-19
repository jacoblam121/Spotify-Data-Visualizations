#!/usr/bin/env python3
"""
Debug Genre Classification Issues

This script helps debug why artists are getting incorrect genre classifications.
"""

def debug_genre_matching():
    """Debug the bidirectional substring matching issue."""
    
    # Import the current problematic logic
    from simplified_genre_colors import GENRE_MAPPINGS
    
    print("🐛 DEBUGGING GENRE CLASSIFICATION ISSUES")
    print("=" * 60)
    
    # Test problematic tags that might appear for Taylor Swift
    test_tags = [
        "pop",
        "country", 
        "folk",
        "seen live in asia 2024",  # This could trigger 'asian'
        "electronic remix version",  # This could trigger 'electronic'
        "alternative country",  # This might trigger multiple genres
        "not country music",  # Negative mention still triggers
        "taylor swift",
        "album",
        "popular",
        "music"
    ]
    
    print("\n🔍 Testing current bidirectional matching logic:")
    print("if keyword in genre_lower or genre_lower in keyword:")
    print("-" * 50)
    
    for tag in test_tags:
        print(f"\nTesting tag: '{tag}'")
        tag_lower = tag.lower().strip()
        
        matched_genres = []
        for category, keywords in GENRE_MAPPINGS.items():
            for keyword in keywords:
                # Current problematic logic
                if keyword in tag_lower or tag_lower in keyword:
                    matched_genres.append(f"{category} (matched '{keyword}')")
                    break
        
        if matched_genres:
            print(f"  ❌ Matches: {matched_genres}")
        else:
            print(f"  ✅ No matches")
    
    print("\n" + "=" * 60)
    print("🔧 PROPOSED FIX: Use exact and careful substring matching")
    print("-" * 50)
    
    for tag in test_tags:
        print(f"\nTesting tag: '{tag}' with improved logic")
        tag_lower = tag.lower().strip()
        
        matched_genres = []
        for category, keywords in GENRE_MAPPINGS.items():
            for keyword in keywords:
                # Improved logic: only match if keyword is in tag, not vice versa
                # And require word boundaries for short keywords
                if len(keyword) <= 3:
                    # Short keywords need exact match or word boundaries
                    import re
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    if re.search(pattern, tag_lower):
                        matched_genres.append(f"{category} (exact match '{keyword}')")
                        break
                else:
                    # Longer keywords can use substring matching
                    if keyword in tag_lower:
                        matched_genres.append(f"{category} (substring '{keyword}')")
                        break
        
        if matched_genres:
            print(f"  ✅ Improved matches: {matched_genres}")
        else:
            print(f"  ✅ No matches")

def debug_specific_artists():
    """Debug specific problematic artists."""
    print("\n🎤 DEBUGGING SPECIFIC ARTISTS")
    print("=" * 60)
    
    # Test with mock data that might cause issues
    problematic_cases = {
        "Taylor Swift": {
            "lastfm_tags": ["pop", "country", "folk", "female vocalists", "seen live", "2000s"],
            "spotify_genres": ["pop", "country pop"]
        },
        "Paramore": {
            "lastfm_tags": ["rock", "alternative rock", "pop punk", "emo", "alternative"],
            "spotify_genres": ["pop punk", "alternative rock", "emo"]
        },
        "IU": {
            "lastfm_tags": ["k-pop", "korean", "pop", "female vocalists", "asian"],
            "spotify_genres": ["k-pop", "korean pop"]
        }
    }
    
    from simplified_genre_colors import classify_artist_genre, get_multi_genres
    
    for artist, data in problematic_cases.items():
        print(f"\n🔍 Testing: {artist}")
        
        # Create mock artist data
        mock_data = {
            'lastfm_data': {
                'tags': [{'name': tag} for tag in data['lastfm_tags']]
            },
            'spotify_data': {
                'genres': data['spotify_genres']
            }
        }
        
        primary_genre = classify_artist_genre(mock_data)
        multi_genres = get_multi_genres(mock_data, max_genres=4)
        
        print(f"  📊 Input tags: {data['lastfm_tags'] + data['spotify_genres']}")
        print(f"  🎯 Primary genre: {primary_genre}")
        print(f"  🌈 Multi-genres: {multi_genres}")

def test_specific_problem_cases():
    """Test the specific problematic substring matches."""
    print("\n🚨 TESTING SPECIFIC PROBLEM CASES")
    print("=" * 60)
    
    from simplified_genre_colors import GENRE_MAPPINGS
    
    # Test cases that should NOT match
    problem_cases = [
        ("asia tour 2024", "asian", "Should not match 'asian' just because 'asia' appears"),
        ("not country", "country", "Should not match 'country' in negative context"),
        ("alternative to country", "country", "Should not match 'country' in comparison"),
        ("indie game soundtrack", "indie", "Should not match 'indie' for game soundtracks"),
        ("electronic remix", "electronic", "Should match 'electronic' for remixes"),
    ]
    
    for tag, genre_category, expected in problem_cases:
        tag_lower = tag.lower()
        keywords = GENRE_MAPPINGS.get(genre_category, [])
        
        matched = False
        matched_keyword = None
        for keyword in keywords:
            if keyword in tag_lower or tag_lower in keyword:
                matched = True
                matched_keyword = keyword
                break
        
        status = "❌ WRONG" if matched else "✅ CORRECT"
        print(f"{status} '{tag}' -> {genre_category}: {expected}")
        if matched:
            print(f"    Matched keyword: '{matched_keyword}'")

if __name__ == "__main__":
    debug_genre_matching()
    debug_specific_artists() 
    test_specific_problem_cases()