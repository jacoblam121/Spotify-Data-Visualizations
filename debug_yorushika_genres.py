#!/usr/bin/env python3
"""
Debug Yorushika 3-Genre Issue
=============================
Investigate why Yorushika has 3 genres instead of the 2-genre max.
"""

from simplified_genre_colors import classify_artist_genre, get_multi_genres

def debug_yorushika_case():
    """Debug the specific Yorushika case that's showing 3 genres."""
    print("🐛 DEBUGGING YORUSHIKA 3-GENRE ISSUE")
    print("=" * 60)
    
    # Create mock data similar to what Yorushika might have
    yorushika_mock_data = {
        'lastfm_data': {'tags': [
            {'name': 'j-rock'}, {'name': 'japanese'}, {'name': 'pop'}, 
            {'name': 'rock'}, {'name': 'alternative'}
        ]},
        'spotify_data': {'genres': ['j-rock', 'japanese rock', 'pop']}
    }
    
    print("📊 Mock Yorushika Data:")
    print(f"  Last.fm tags: {[tag['name'] for tag in yorushika_mock_data['lastfm_data']['tags']]}")
    print(f"  Spotify genres: {yorushika_mock_data['spotify_data']['genres']}")
    
    # Test with our functions
    primary = classify_artist_genre(yorushika_mock_data)
    multi = get_multi_genres(yorushika_mock_data, max_genres=2)
    
    print(f"\n🎯 Results:")
    print(f"  Primary genre: {primary}")
    print(f"  Multi genres: {multi}")
    print(f"  Genre count: {len(multi)}")
    print(f"  Result string: {primary} + {multi[1:] if len(multi) > 1 else []}")
    
    if len(multi) > 2:
        print(f"\n❌ PROBLEM: {len(multi)} genres found, should be max 2!")
        print(f"   Expected: max_genres=2 should limit to 2 genres")
        print(f"   Actual: {multi}")
    else:
        print(f"\n✅ GOOD: Within 2-genre limit")
    
    # Debug the multi-genre function step by step
    print(f"\n🔍 DEBUGGING get_multi_genres() STEP BY STEP:")
    print("-" * 50)
    
    # Check if the function is being called with correct max_genres
    print(f"Testing with different max_genres values:")
    
    for max_val in [1, 2, 3]:
        result = get_multi_genres(yorushika_mock_data, max_genres=max_val)
        print(f"  max_genres={max_val}: {result} (count: {len(result)})")
        if max_val == 2 and len(result) > 2:
            print(f"    ❌ ISSUE: max_genres=2 returned {len(result)} genres!")

def trace_multi_genre_logic():
    """Trace through the multi-genre logic to find the bug."""
    print(f"\n🕵️ TRACING MULTI-GENRE LOGIC")
    print("=" * 50)
    
    # Simplified test case
    test_data = {
        'lastfm_data': {'tags': [
            {'name': 'asian'}, {'name': 'pop'}, {'name': 'rock'}
        ]},
        'spotify_data': {'genres': []}
    }
    
    print("Test data:", [tag['name'] for tag in test_data['lastfm_data']['tags']])
    
    # Manually trace the logic
    print("\n1. Get primary genre:")
    primary = classify_artist_genre(test_data)
    print(f"   Primary: {primary}")
    
    print("\n2. Check special handling:")
    source_data = []
    if test_data.get('lastfm_data') and test_data['lastfm_data'].get('tags'):
        lastfm_genres = [tag['name'].lower() for tag in test_data['lastfm_data']['tags']]
        for genre in lastfm_genres:
            source_data.append({'tag': genre, 'source': 'lastfm', 'weight': 1.0})
    
    all_tags = [item['tag'] for item in source_data]
    print(f"   All tags: {all_tags}")
    
    if primary == 'asian' and 'pop' in all_tags:
        print(f"   Special case triggered: asian + pop")
        special_result = ['asian', 'pop']
        print(f"   Special result: {special_result}")
    
    print("\n3. Test actual function:")
    actual_result = get_multi_genres(test_data, max_genres=2)
    print(f"   Actual result: {actual_result} (count: {len(actual_result)})")
    
    if len(actual_result) != len(special_result):
        print(f"   ❌ MISMATCH: Expected {len(special_result)}, got {len(actual_result)}")

def check_function_flow():
    """Check if there's an issue with the function flow."""
    print(f"\n🔧 CHECKING FUNCTION FLOW")
    print("=" * 50)
    
    # Read the actual function code to see what might be wrong
    import inspect
    
    print("get_multi_genres function signature:")
    sig = inspect.signature(get_multi_genres)
    print(f"  {sig}")
    
    # Test edge cases
    edge_cases = [
        {
            'name': 'Asian + Pop case',
            'data': {
                'lastfm_data': {'tags': [{'name': 'asian'}, {'name': 'pop'}]},
                'spotify_data': {'genres': []}
            }
        },
        {
            'name': 'Asian + Pop + Rock case',
            'data': {
                'lastfm_data': {'tags': [{'name': 'asian'}, {'name': 'pop'}, {'name': 'rock'}]},
                'spotify_data': {'genres': []}
            }
        }
    ]
    
    for case in edge_cases:
        print(f"\n{case['name']}:")
        result = get_multi_genres(case['data'], max_genres=2)
        print(f"  Result: {result} (count: {len(result)})")
        if len(result) > 2:
            print(f"  ❌ EXCEEDS LIMIT!")

if __name__ == "__main__":
    debug_yorushika_case()
    trace_multi_genre_logic()
    check_function_flow()