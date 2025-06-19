#!/usr/bin/env python3
"""
Test Taylor Swift Specific Case
===============================
Analyze whether Taylor Swift should be pop or country based on different approaches.
"""

def analyze_taylor_swift_classification():
    """Analyze the Taylor Swift classification debate."""
    print("🎤 TAYLOR SWIFT CLASSIFICATION ANALYSIS")
    print("=" * 60)
    
    print("🤔 The Question: Should Taylor Swift be classified as 'pop' or 'country'?")
    print("\n📊 Arguments for COUNTRY:")
    print("  • Started as country artist (early albums)")
    print("  • Last.fm users tag her as 'country'") 
    print("  • Has country influences throughout career")
    print("  • Country music roots and history")
    
    print("\n📊 Arguments for POP:")
    print("  • Current mainstream appeal is pop")
    print("  • Most popular songs are pop (Shake It Off, Anti-Hero, etc.)")
    print("  • Spotify likely classifies as pop")
    print("  • Modern Taylor Swift is pop-dominant")
    
    print("\n🎯 The Real Issue:")
    print("  • Taylor Swift transcends simple genre classification")
    print("  • She's a multi-genre artist: pop/country/folk")
    print("  • Primary genre depends on time period and context")
    
    print("\n💡 Possible Solutions:")
    print("  1. Always classify as 'pop' (mainstream appeal)")
    print("  2. Use weighted average of career (country -> pop transition)")
    print("  3. Accept 'country' as valid (user data reflects this)")
    print("  4. Create special handling for crossover artists")
    
    print("\n🔍 User's Expected Result: 'pop + [country]'")
    print("🔍 Our Current Result: 'country + [pop]'")
    print("🔍 System Result: Based on available data tags")
    
    print("\n❓ Question for User:")
    print("   Should the system prioritize:")
    print("   A) Current mainstream genre (pop)")
    print("   B) User-generated tags (country from Last.fm)")
    print("   C) Career-spanning classification")
    
    # Test different priority approaches
    print(f"\n🧪 TESTING DIFFERENT APPROACHES:")
    print("=" * 50)
    
    taylor_data = {
        'lastfm_data': {'tags': [
            {'name': 'country'}, {'name': 'pop'}, {'name': 'female vocalists'}
        ]},
        'spotify_data': {'genres': []}  # Empty like in real data
    }
    
    # Approach 1: Pop-first hierarchy
    print("\n1️⃣ Approach: Pop-First Hierarchy")
    pop_first_hierarchy = {
        'pop': 10,      # Prioritize pop for mainstream artists
        'asian': 9,     # Cultural specificity still high
        'latin': 9,
        'rock': 8,      
        'country': 7,   # Lower country priority
        'electronic': 6,
        'hip-hop': 6,
        'folk': 5,
        'r&b': 4,
        'indie': 3,
        'metal': 2,
        'other': 1
    }
    
    scores_pop_first = {}
    for tag_data in taylor_data['lastfm_data']['tags']:
        tag = tag_data['name']
        if tag == 'country':
            scores_pop_first['country'] = pop_first_hierarchy['country'] * 2  # Exact match
        elif tag == 'pop':
            scores_pop_first['pop'] = pop_first_hierarchy['pop'] * 2  # Exact match
    
    print(f"   Scores: {scores_pop_first}")
    winner1 = max(scores_pop_first, key=scores_pop_first.get)
    print(f"   Winner: {winner1} ✅ Matches user expectation")
    
    # Approach 2: Context-aware (if both country and pop, prefer pop)
    print("\n2️⃣ Approach: Context-Aware Rules")
    print("   Rule: If artist has BOTH 'country' and 'pop', prefer 'pop'")
    
    has_country = any(tag['name'] == 'country' for tag in taylor_data['lastfm_data']['tags'])
    has_pop = any(tag['name'] == 'pop' for tag in taylor_data['lastfm_data']['tags'])
    
    if has_country and has_pop:
        winner2 = 'pop'
        print(f"   Both genres found -> Winner: {winner2} ✅ Matches user expectation")
    else:
        print("   Only one genre found, use normal hierarchy")
    
    # Approach 3: Spotify authority (but handle empty case)
    print("\n3️⃣ Approach: Enhanced Source Authority")
    print("   Rule: When Spotify empty but Last.fm has pop+country -> prefer pop")
    
    spotify_empty = not taylor_data['spotify_data']['genres']
    if spotify_empty and has_pop and has_country:
        winner3 = 'pop'
        print(f"   Spotify empty + pop+country detected -> Winner: {winner3} ✅")
    else:
        print("   Use normal classification")
    
    print(f"\n🎯 RECOMMENDATION:")
    print(f"   Use Approach #2 (Context-Aware Rules)")
    print(f"   When artist has BOTH 'country' and 'pop', prefer 'pop'")
    print(f"   This handles crossover artists like Taylor Swift appropriately")

if __name__ == "__main__":
    analyze_taylor_swift_classification()