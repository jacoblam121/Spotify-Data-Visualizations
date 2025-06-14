#!/usr/bin/env python3
"""
Test script to verify the dual-profile system works correctly.
Tests that IVE shows 838K listeners while maintaining ANYUJIN-IVE connections.
"""

import json
from integrated_network_generator import IntegratedNetworkGenerator

def test_dual_profile_system():
    """Test that dual-profile system works for IVE and ANYUJIN."""
    print("🎯 Testing Dual-Profile System")
    print("=" * 50)
    
    # Load artist data
    try:
        with open('artist_data.json', 'r', encoding='utf-8') as f:
            artists_data = json.load(f)
        print(f"✅ Loaded {len(artists_data)} artists from artist_data.json")
    except FileNotFoundError:
        print("❌ artist_data.json not found")
        return
    
    # Find test artists
    test_artists = ['ANYUJIN', 'IVE']
    found_artists = []
    
    for artist_name in test_artists:
        for artist in artists_data:
            if artist_name.lower() in artist['name'].lower():
                found_artists.append(artist)
                print(f"✅ Found test artist: {artist['name']} (plays: {artist.get('play_count', 0)})")
                break
    
    if len(found_artists) < 2:
        print(f"❌ Only found {len(found_artists)} test artists, need both ANYUJIN and IVE")
        return
    
    # Initialize network generator
    print("\n🌐 Initializing network generator...")
    generator = IntegratedNetworkGenerator()
    
    # Test enhanced metadata for IVE
    print(f"\n🔍 Testing enhanced metadata for IVE...")
    ive_metadata = generator.metadata_enhancer.get_artist_display_metadata('IVE')
    if ive_metadata:
        print(f"✅ IVE metadata found:")
        print(f"   Name: {ive_metadata['name']}")
        print(f"   Listeners: {ive_metadata['listeners']:,}")
        print(f"   Variant used: {ive_metadata['variant_used']}")
        
        if ive_metadata['listeners'] > 800000:
            print("✅ IVE has high listener count (>800K) - CORRECT for display")
        else:
            print(f"⚠️  IVE has low listener count ({ive_metadata['listeners']:,}) - may be using functional profile")
    else:
        print("❌ No enhanced metadata found for IVE")
    
    # Test node creation with small subset
    print(f"\n🎯 Testing node creation with test artists...")
    test_nodes = generator._create_nodes(found_artists)
    
    for node in test_nodes:
        print(f"\n📊 Node: {node['name']}")
        print(f"   Listeners: {node.get('listeners', 0):,}")
        print(f"   Play count: {node['play_count']}")
        print(f"   Metadata source: {node.get('display_metadata_source', 'unknown')}")
        
        if 'IVE' in node['name'] and node.get('listeners', 0) < 100000:
            print("⚠️  WARNING: IVE node has low listener count - dual-profile may not be working")
    
    # Test similarity connection (functional profile)
    print(f"\n🔗 Testing ANYUJIN-IVE similarity connection...")
    anyujin_name = found_artists[0]['name']
    ive_name = found_artists[1]['name']
    
    # Get similarity using functional profiles (should work)
    similarity = generator.lastfm_api.get_similar_artists(anyujin_name, use_enhanced_matching=True)
    
    ive_found_in_similarity = False
    for similar_artist in similarity:
        if 'IVE' in similar_artist['name'] or 'ive' in similar_artist['name'].lower():
            ive_found_in_similarity = True
            print(f"✅ Found IVE in ANYUJIN similarity: {similar_artist['name']} (score: {similar_artist['match']})")
            break
    
    if not ive_found_in_similarity:
        print("❌ IVE not found in ANYUJIN similarity - functional profile may be broken")
    
    print(f"\n🏁 Test Summary:")
    print(f"   Enhanced metadata: {'✅' if ive_metadata else '❌'}")
    print(f"   High listener count: {'✅' if ive_metadata and ive_metadata['listeners'] > 800000 else '❌'}")
    print(f"   Functional similarity: {'✅' if ive_found_in_similarity else '❌'}")
    
    if ive_metadata and ive_metadata['listeners'] > 800000 and ive_found_in_similarity:
        print("\n🎉 DUAL-PROFILE SYSTEM WORKING CORRECTLY!")
        print("   Display data: High listener count for visualization")
        print("   Functional data: Working similarity connections")
    else:
        print("\n⚠️  Dual-profile system needs debugging")

if __name__ == "__main__":
    test_dual_profile_system()