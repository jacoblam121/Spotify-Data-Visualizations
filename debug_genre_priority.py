#!/usr/bin/env python3
"""
Debug Genre Priority Issues

Analyze why Taylor Swift gets 'folk' as primary instead of 'pop'
and why IVE gets 'pop' instead of 'asian'.
"""

from simplified_genre_colors import classify_artist_genre, get_multi_genres, GENRE_MAPPINGS

def debug_priority_issues():
    """Debug the specific priority issues mentioned."""
    print("🐛 DEBUGGING GENRE PRIORITY ISSUES")
    print("=" * 60)
    
    # Test cases with expected outcomes
    test_cases = {
        "Taylor Swift": {
            "mock_data": {
                'lastfm_data': {'tags': [
                    {'name': 'pop'}, {'name': 'country'}, {'name': 'folk'}, 
                    {'name': 'female vocalists'}, {'name': 'singer-songwriter'}
                ]},
                'spotify_data': {'genres': ['pop', 'country pop']}
            },
            "expected_primary": "pop",
            "current_primary": "folk"
        },
        "IVE": {
            "mock_data": {
                'lastfm_data': {'tags': [
                    {'name': 'k-pop'}, {'name': 'korean'}, {'name': 'pop'}, 
                    {'name': 'girl group'}, {'name': 'asian'}
                ]},
                'spotify_data': {'genres': ['k-pop', 'korean pop']}
            },
            "expected_primary": "asian", 
            "current_primary": "pop"
        }
    }
    
    for artist, data in test_cases.items():
        print(f"\n🎤 Analyzing {artist}")
        print("-" * 30)
        
        mock_data = data["mock_data"]
        
        # Collect all tags
        all_tags = []
        if mock_data.get('lastfm_data') and mock_data['lastfm_data'].get('tags'):
            lastfm_tags = [tag['name'].lower() for tag in mock_data['lastfm_data']['tags']]
            all_tags.extend(lastfm_tags)
        
        if mock_data.get('spotify_data') and mock_data['spotify_data'].get('genres'):
            spotify_tags = [genre.lower() for genre in mock_data['spotify_data']['genres']]
            all_tags.extend(spotify_tags)
        
        print(f"📊 All tags: {all_tags}")
        
        # Debug scoring process
        genre_scores = {}
        tag_matches = {}  # Track which tags matched which genres
        
        for tag in all_tags:
            tag_lower = tag.lower().strip()
            print(f"\n🔍 Processing tag: '{tag}'")
            
            for category, keywords in GENRE_MAPPINGS.items():
                for keyword in keywords:
                    if keyword in tag_lower:
                        genre_scores[category] = genre_scores.get(category, 0) + 1
                        if category not in tag_matches:
                            tag_matches[category] = []
                        tag_matches[category].append(f"'{tag}' matches '{keyword}'")
                        print(f"   ✅ {category}: {tag} -> {keyword}")
                        break
        
        print(f"\n📈 Final scores: {genre_scores}")
        print(f"🏆 Highest scoring genre: {max(genre_scores, key=genre_scores.get) if genre_scores else 'none'}")
        
        # Show what current system returns
        actual_primary = classify_artist_genre(mock_data)
        actual_multi = get_multi_genres(mock_data, max_genres=3)
        
        print(f"\n🎯 Expected primary: {data['expected_primary']}")
        print(f"🎯 Actual primary: {actual_primary} {'✅' if actual_primary == data['expected_primary'] else '❌'}")
        print(f"🌈 Multi-genres: {actual_multi}")
        
        # Analyze the specific issue
        if actual_primary != data["expected_primary"]:
            expected_score = genre_scores.get(data["expected_primary"], 0)
            actual_score = genre_scores.get(actual_primary, 0)
            print(f"\n❗ Issue analysis:")
            print(f"   Expected '{data['expected_primary']}' score: {expected_score}")
            print(f"   Actual '{actual_primary}' score: {actual_score}")
            
            if expected_score == actual_score:
                print(f"   🔍 Tie situation! Need better tie-breaking logic")
            elif expected_score < actual_score:
                print(f"   🔍 '{actual_primary}' legitimately scored higher - need better keyword weights")
                
def analyze_genre_keyword_conflicts():
    """Analyze overlapping keywords that cause conflicts."""
    print(f"\n🔍 ANALYZING KEYWORD CONFLICTS")
    print("=" * 60)
    
    # Check for overlapping keywords between genres
    overlaps = {}
    for genre1, keywords1 in GENRE_MAPPINGS.items():
        for genre2, keywords2 in GENRE_MAPPINGS.items():
            if genre1 < genre2:  # Avoid duplicates
                common = set(keywords1) & set(keywords2)
                if common:
                    overlaps[f"{genre1} vs {genre2}"] = list(common)
    
    print("Overlapping keywords between genres:")
    for pair, keywords in overlaps.items():
        print(f"  {pair}: {keywords}")
    
    # Check for problematic keywords
    print(f"\n🚨 Potentially problematic keywords:")
    broad_keywords = ['pop', 'folk', 'alternative', 'indie']
    
    for keyword in broad_keywords:
        genres_with_keyword = []
        for genre, keywords in GENRE_MAPPINGS.items():
            if keyword in keywords:
                genres_with_keyword.append(genre)
        
        if len(genres_with_keyword) > 1:
            print(f"  '{keyword}' appears in: {genres_with_keyword}")

def propose_fixes():
    """Propose specific fixes for the priority issues."""
    print(f"\n🔧 PROPOSED FIXES")
    print("=" * 60)
    
    print("1. 📊 Implement weighted scoring by source:")
    print("   - Spotify genres: weight = 2.0 (more authoritative)")
    print("   - Last.fm tags: weight = 1.0 (user-generated)")
    
    print("\n2. 🎯 Implement keyword priority:")
    print("   - Exact genre matches get higher priority")
    print("   - 'k-pop' should strongly indicate 'asian' genre")
    print("   - 'pop' alone should indicate 'pop' genre")
    
    print("\n3. 🏆 Implement tie-breaking rules:")
    print("   - When scores are tied, prefer more specific genres")
    print("   - Asian-specific keywords (k-pop, korean) > generic 'pop'")
    print("   - Direct genre names > descriptor words")
    
    print("\n4. 📝 Limit to 2 genres maximum:")
    print("   - Primary + 1 secondary genre only")
    print("   - Reduces complexity and improves clarity")

if __name__ == "__main__":
    debug_priority_issues()
    analyze_genre_keyword_conflicts()
    propose_fixes()