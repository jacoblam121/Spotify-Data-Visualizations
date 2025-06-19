#!/usr/bin/env python3
"""Test the genre classification fix"""

from simplified_genre_colors import classify_artist_genre, get_multi_genres

# Test artists with their expected vs actual results
test_cases = {
    "Taylor Swift": {
        "input": {
            'lastfm_data': {'tags': [{'name': 'pop'}, {'name': 'country'}, {'name': 'folk'}, {'name': 'female vocalists'}]},
            'spotify_data': {'genres': ['pop', 'country pop']}
        },
        "expected_primary": "pop",
        "expected_secondary": ["country", "folk"]
    },
    "Paramore": {
        "input": {
            'lastfm_data': {'tags': [{'name': 'rock'}, {'name': 'alternative rock'}, {'name': 'pop punk'}, {'name': 'emo'}]},
            'spotify_data': {'genres': ['pop punk', 'alternative rock', 'emo']}
        },
        "expected_primary": "rock", 
        "expected_secondary": ["pop", "indie"]
    },
    "IU": {
        "input": {
            'lastfm_data': {'tags': [{'name': 'k-pop'}, {'name': 'korean'}, {'name': 'pop'}, {'name': 'asian'}]},
            'spotify_data': {'genres': ['k-pop', 'korean pop']}
        },
        "expected_primary": "asian",
        "expected_secondary": ["pop"]
    }
}

print("🧪 TESTING GENRE CLASSIFICATION FIX")
print("=" * 50)

for artist, data in test_cases.items():
    print(f"\n🎤 {artist}")
    
    primary = classify_artist_genre(data["input"])
    multi = get_multi_genres(data["input"], max_genres=4)
    
    primary_ok = primary == data["expected_primary"]
    
    print(f"  Primary: {primary} {'✅' if primary_ok else '❌'}")
    print(f"  Multi: {multi}")
    
    # Check for problematic genres
    problematic = []
    if "electronic" in multi and artist != "Electronic Artist":
        problematic.append("electronic")
    if "asian" in multi and artist not in ["IU", "Yorushika"]:
        problematic.append("asian") 
    if "country" in multi and artist == "Yorushika":
        problematic.append("country")
    
    if problematic:
        print(f"  ⚠️  Still has problematic genres: {problematic}")
    else:
        print(f"  ✅ No problematic genres detected")

print(f"\n📊 SUMMARY")
print(f"The fix should eliminate:")
print(f"  ❌ Taylor Swift getting 'asian' or 'electronic'")
print(f"  ❌ Paramore getting 'country'") 
print(f"  ❌ Yorushika getting 'country'")
print(f"  ❌ Non-Asian artists getting 'asian'")