#!/usr/bin/env python3
"""
Debug MusicBrainz Relationships
================================
Investigate why we're getting 0 relationships for major artists.
"""

import requests
import time
import json

def debug_musicbrainz_relationships():
    """Debug MusicBrainz relationship queries."""
    print("🔍 Debugging MusicBrainz Relationship Queries")
    print("=" * 50)
    
    # Test with The Beatles (should have MANY relationships)
    artist_mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"  # The Beatles
    base_url = "https://musicbrainz.org/ws/2"
    user_agent = "SpotifyDataViz/1.0 (debug@example.com)"
    
    print(f"\n🎯 Testing various relationship include parameters for The Beatles")
    print(f"MBID: {artist_mbid}")
    
    # Test different include parameters
    include_variants = [
        'artist-rels',
        'artist-rels+work-rels', 
        'rels',
        'relationships',
        'artist-relationships',
        'url-rels',
        'work-rels+artist-rels'
    ]
    
    for include_param in include_variants:
        print(f"\n📋 Testing include='{include_param}':")
        
        try:
            url = f"{base_url}/artist/{artist_mbid}"
            params = {
                'inc': include_param,
                'fmt': 'json'
            }
            headers = {'User-Agent': user_agent}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check what we got back
                relations = data.get('relations', [])
                relationships = data.get('relationships', [])
                
                print(f"   Status: 200 ✅")
                print(f"   'relations' field: {len(relations)} items")
                print(f"   'relationships' field: {len(relationships)} items")
                
                # Show structure of first relation if any
                if relations:
                    print(f"   First relation structure:")
                    first_rel = relations[0]
                    print(f"     Type: {first_rel.get('type', 'N/A')}")
                    print(f"     Direction: {first_rel.get('direction', 'N/A')}")
                    print(f"     Target type: {first_rel.get('target-type', 'N/A')}")
                    if 'artist' in first_rel:
                        print(f"     Target artist: {first_rel['artist'].get('name', 'N/A')}")
                
                # Show all relation types
                relation_types = [r.get('type', 'unknown') for r in relations]
                if relation_types:
                    unique_types = list(set(relation_types))
                    print(f"   Relation types found: {', '.join(unique_types[:10])}")
                
            else:
                print(f"   Status: {response.status_code} ❌")
                print(f"   Error: {response.text}")
            
            time.sleep(1.1)  # Rate limiting
            
        except Exception as e:
            print(f"   Exception: {e}")
    
    # Test with raw JSON output to see full structure
    print(f"\n🔬 Raw JSON structure analysis:")
    try:
        url = f"{base_url}/artist/{artist_mbid}"
        params = {
            'inc': 'artist-rels+url-rels',
            'fmt': 'json'
        }
        headers = {'User-Agent': user_agent}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"Top-level keys: {list(data.keys())}")
            
            if 'relations' in data:
                relations = data['relations']
                print(f"Total relations: {len(relations)}")
                
                # Analyze relation types
                relation_analysis = {}
                for rel in relations:
                    rel_type = rel.get('type', 'unknown')
                    target_type = rel.get('target-type', 'unknown')
                    key = f"{rel_type} -> {target_type}"
                    
                    if key not in relation_analysis:
                        relation_analysis[key] = 0
                    relation_analysis[key] += 1
                
                print(f"Relation type breakdown:")
                for rel_type, count in sorted(relation_analysis.items()):
                    print(f"   {rel_type}: {count}")
                
                # Show sample artist-to-artist relations
                artist_relations = [r for r in relations if r.get('target-type') == 'artist']
                print(f"\nArtist-to-artist relations: {len(artist_relations)}")
                
                for i, rel in enumerate(artist_relations[:5], 1):
                    target_name = rel.get('artist', {}).get('name', 'Unknown')
                    rel_type = rel.get('type', 'Unknown')
                    direction = rel.get('direction', 'N/A')
                    print(f"   {i}. {rel_type} -> {target_name} (direction: {direction})")
        
        time.sleep(1.1)
        
    except Exception as e:
        print(f"Raw analysis exception: {e}")

if __name__ == "__main__":
    debug_musicbrainz_relationships()