#!/usr/bin/env python3
"""
Debug why ANYUJIN's Last.fm matches aren't creating edges
"""

import json
from integrated_network_generator import IntegratedNetworkGenerator

def debug_anyujin_target_matching():
    """Debug why ANYUJIN similarity matches aren't found in target dataset."""
    
    print("🔍 Debug ANYUJIN Target Matching")
    print("=" * 40)
    
    # Load artist data
    with open('artist_data.json', 'r', encoding='utf-8') as f:
        artists_data = json.load(f)
    
    # Create target lookup
    target_artists = {a['name'].lower(): a for a in artists_data}
    
    # Initialize network generator
    generator = IntegratedNetworkGenerator()
    
    # Get ANYUJIN similarity
    print("\n1️⃣ Getting ANYUJIN Last.fm matches:")
    anyujin_similarity = generator._get_multi_source_similarity("ANYUJIN")
    lastfm_matches = anyujin_similarity.get('lastfm', [])
    
    print(f"   Last.fm returned {len(lastfm_matches)} matches")
    
    # Check each match against target dataset
    print("\n2️⃣ Checking each match against target dataset:")
    found_matches = []
    missing_matches = []
    
    for i, match in enumerate(lastfm_matches[:15]):  # Check first 15
        match_name = match['name']
        match_name_lower = match_name.lower()
        
        if match_name_lower in target_artists:
            found_matches.append((match_name, target_artists[match_name_lower]))
            print(f"   ✅ FOUND: '{match_name}' -> {target_artists[match_name_lower]['play_count']} plays")
        else:
            missing_matches.append(match_name)
            print(f"   ❌ MISSING: '{match_name}' not in dataset")
    
    print(f"\n📊 Summary:")
    print(f"   Found in dataset: {len(found_matches)}")
    print(f"   Missing from dataset: {len(missing_matches)}")
    
    # Show some artists that ARE in the dataset for comparison
    print(f"\n3️⃣ Sample artists in dataset (for reference):")
    sample_artists = [a['name'] for a in artists_data[:20]]
    print(f"   {sample_artists}")
    
    # If we have found matches, test edge creation with just those
    if found_matches:
        print(f"\n4️⃣ Testing edge creation with found matches:")
        anyujin_data = {'name': 'ANYUJIN', 'play_count': 427}
        
        # Create a simplified similarity data structure with only found matches
        filtered_similarity = {
            'lastfm': [{'name': match[0], 'similarity': 0.8} for match in found_matches],
            'deezer': [],
            'musicbrainz': []
        }
        
        edges = generator._create_edges_for_artist(
            anyujin_data, 
            filtered_similarity, 
            target_artists
        )
        
        print(f"   Created {len(edges)} edges with filtered matches")
        for edge in edges:
            target_name = [a['name'] for a in artists_data if a['name'].lower().replace(' ', '_') == edge['target']]
            print(f"   -> {target_name[0] if target_name else edge['target']}: weight={edge['weight']:.3f}")
    
    # Check Korean name variants that might be causing issues
    print(f"\n5️⃣ Checking for Korean name variants:")
    korean_names = [match for match in lastfm_matches if any(ord(c) > 127 for c in match['name'])]
    print(f"   Korean/Unicode names: {len(korean_names)}")
    for name_obj in korean_names[:5]:
        name = name_obj['name']
        print(f"   '{name}' -> found in dataset: {name.lower() in target_artists}")

if __name__ == "__main__":
    debug_anyujin_target_matching()