#!/usr/bin/env python3
"""Test the genre priority fix"""

from simplified_genre_colors import classify_artist_genre, get_multi_genres

# Test the specific problem cases mentioned by user
test_cases = {
    "Taylor Swift": {
        "input": {
            'lastfm_data': {'tags': [
                {'name': 'pop'}, {'name': 'country'}, {'name': 'folk'}, 
                {'name': 'female vocalists'}, {'name': 'singer-songwriter'}
            ]},
            'spotify_data': {'genres': ['pop', 'country pop']}
        },
        "expected": "pop + ['country']",
        "current_problem": "folk + ['country', 'pop']"
    },
    "IVE": {
        "input": {
            'lastfm_data': {'tags': [
                {'name': 'k-pop'}, {'name': 'korean'}, {'name': 'pop'}, 
                {'name': 'girl group'}, {'name': 'asian'}
            ]},
            'spotify_data': {'genres': ['k-pop', 'korean pop']}
        },
        "expected": "asian + ['pop']",
        "current_problem": "pop + ['asian']"
    },
    "Paramore": {
        "input": {
            'lastfm_data': {'tags': [
                {'name': 'rock'}, {'name': 'alternative rock'}, {'name': 'pop punk'}, 
                {'name': 'emo'}, {'name': 'alternative'}
            ]},
            'spotify_data': {'genres': ['pop punk', 'alternative rock', 'emo']}
        },
        "expected": "rock + ['pop'] or similar",
        "current_problem": "pop + ['rock', 'indie']"
    }
}

print("🧪 TESTING PRIORITY FIX")
print("=" * 60)

all_passed = True

for artist, data in test_cases.items():
    print(f"\n🎤 {artist}")
    print(f"  Problem: {data['current_problem']}")
    print(f"  Expected: {data['expected']}")
    
    # Test the fix
    primary = classify_artist_genre(data["input"])
    multi = get_multi_genres(data["input"], max_genres=2)
    
    result_str = f"{primary} + {multi[1:] if len(multi) > 1 else []}"
    print(f"  Result: {result_str}")
    
    # Check specific expectations
    success = True
    if artist == "Taylor Swift":
        success = primary == "pop" and "country" in multi
        print(f"  ✅ Taylor Swift primary = pop: {primary == 'pop'}")
        print(f"  ✅ Taylor Swift has country: {'country' in multi}")
    elif artist == "IVE":
        success = primary == "asian" and "pop" in multi
        print(f"  ✅ IVE primary = asian: {primary == 'asian'}")
        print(f"  ✅ IVE has pop: {'pop' in multi}")
    elif artist == "Paramore":
        success = primary in ["rock", "pop"] and len(multi) <= 2
        print(f"  ✅ Paramore primary reasonable: {primary in ['rock', 'pop']}")
        print(f"  ✅ Paramore limited to 2 genres: {len(multi) <= 2}")
    
    if success:
        print(f"  🎉 FIXED!")
    else:
        print(f"  ❌ Still needs work")
        all_passed = False

print(f"\n📊 SUMMARY")
print("=" * 30)
if all_passed:
    print("🎉 All priority issues fixed!")
    print("✅ Taylor Swift: pop primary")
    print("✅ IVE: asian primary") 
    print("✅ Limited to 2 genres max")
else:
    print("❌ Some issues remain - need further tuning")

# Test the 2-genre limit
print(f"\n📏 TESTING 2-GENRE LIMIT")
print("-" * 30)
for artist, data in test_cases.items():
    multi = get_multi_genres(data["input"], max_genres=2)
    print(f"{artist}: {len(multi)} genres = {multi}")
    if len(multi) > 2:
        print(f"  ❌ Exceeds 2-genre limit!")
        all_passed = False
    else:
        print(f"  ✅ Within 2-genre limit")

print(f"\n🏁 FINAL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ NEEDS MORE WORK'}")