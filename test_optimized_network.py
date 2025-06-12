#!/usr/bin/env python3
"""
Test network generation with optimized artist resolution.
This shows the correct artist selection vs the old inefficient method.
"""

import pandas as pd
import networkx as nx
from typing import Dict, List
from fix_artist_resolution import OptimizedLastFmClient
from data_processor import clean_and_filter_data
from config_loader import AppConfig


def create_optimized_network(top_n: int = 20, min_threshold: float = 0.08):
    """Create network using optimized artist resolution."""
    
    print(f"🚀 Creating Optimized Artist Network")
    print(f"📊 Parameters: {top_n} artists, threshold {min_threshold}")
    
    try:
        # Load data
        print("\n📁 Loading listening data...")
        config = AppConfig('configurations.txt')
        df = clean_and_filter_data(config)
        df_network = df.set_index('timestamp')
        print(f"✅ Loaded {len(df_network)} listening records")
        
        # Get top artists
        artist_plays = df_network.groupby('artist').size().sort_values(ascending=False)
        top_artists = artist_plays.head(top_n)
        artist_list = list(top_artists.index)
        
        print(f"\n🎯 Top {top_n} artists:")
        for i, (artist, plays) in enumerate(top_artists.items(), 1):
            print(f"  {i:2d}. {artist} ({plays} plays)")
        
        # Initialize optimized client
        lastfm_config = config.get_lastfm_config()
        client = OptimizedLastFmClient(
            lastfm_config['api_key'], 
            lastfm_config['api_secret']
        )
        
        # Test specific problematic artists first
        print(f"\n🧪 Testing Problematic Artists:")
        test_artists = ['anyujin', 'ive', 'blackpink', 'twice']
        
        for artist in test_artists:
            if artist in artist_list:
                print(f"\n🎵 Testing: {artist}")
                result = client.resolve_artist_efficiently(artist)
                if result['resolved']:
                    print(f"  ✅ Display: {result['display_name']}")
                    print(f"  📊 Canonical: {result['canonical_name']}")
                    print(f"  👥 Listeners: {result['listeners']:,}")
                    print(f"  🔗 URL: {result['url']}")
                    
                    # Check if this is the correct artist
                    if artist == 'anyujin' and result['listeners'] > 5000:
                        print(f"  🎉 CORRECT: Found high-listener AnYujin!")
                    elif artist == 'ive' and result['listeners'] > 800000:
                        print(f"  🎉 CORRECT: Found high-listener IVE!")
                    elif result['listeners'] < 1000:
                        print(f"  ⚠️  LOW LISTENERS: Might be wrong artist")
                else:
                    print(f"  ❌ Could not resolve")
        
        # Create network with optimized resolution
        print(f"\n🕸️  Creating similarity network...")
        
        # Resolve all artists efficiently
        resolved_artists = {}
        failed_artists = []
        
        for i, artist in enumerate(artist_list, 1):
            print(f"  {i}/{len(artist_list)}: {artist}")
            result = client.resolve_artist_efficiently(artist)
            if result['resolved']:
                resolved_artists[artist] = result
            else:
                failed_artists.append(artist)
        
        print(f"\n📈 Resolution Results:")
        print(f"  ✅ Successfully resolved: {len(resolved_artists)}")
        print(f"  ❌ Failed to resolve: {len(failed_artists)}")
        if failed_artists:
            print(f"  Failed artists: {failed_artists}")
        
        # Get similarities between resolved artists
        print(f"\n🔗 Finding similarities...")
        similarities = {}
        similarity_count = 0
        
        resolved_list = list(resolved_artists.keys())
        for i, artist1 in enumerate(resolved_list):
            resolution1 = resolved_artists[artist1]
            similar_artists = client.get_similar_artists_efficient(resolution1)
            
            for similar in similar_artists:
                # Find if this similar artist is in our resolved list
                for artist2 in resolved_list[i+1:]:  # Avoid duplicates
                    resolution2 = resolved_artists[artist2]
                    
                    # Match by canonical name or MBID
                    if (similar['name'].lower() == resolution2['canonical_name'].lower() or
                        (similar.get('mbid') and similar['mbid'] == resolution2.get('mbid'))):
                        
                        if similar['match'] >= min_threshold:
                            pair_key = tuple(sorted([artist1, artist2]))
                            similarities[pair_key] = {
                                'weight': similar['match'],
                                'source_artist': artist1,
                                'target_artist': artist2
                            }
                            similarity_count += 1
                            print(f"    ✅ {artist1} ↔ {artist2} (similarity: {similar['match']:.3f})")
        
        print(f"\n📊 Network Statistics:")
        print(f"  • Nodes: {len(resolved_artists)}")
        print(f"  • Edges: {similarity_count}")
        print(f"  • Density: {2 * similarity_count / (len(resolved_artists) * (len(resolved_artists) - 1)):.4f}")
        
        # Create network data structure
        nodes = []
        for artist, resolution in resolved_artists.items():
            play_count = int(top_artists[artist])
            nodes.append({
                'id': artist,
                'display_name': resolution['display_name'],
                'canonical_name': resolution['canonical_name'],
                'play_count': play_count,
                'listeners': resolution['listeners'],
                'url': resolution.get('url'),
                'size': max(10, min(50, play_count / 50))  # Visual sizing
            })
        
        edges = []
        for pair_key, sim_data in similarities.items():
            edges.append({
                'source': pair_key[0],
                'target': pair_key[1],
                'weight': sim_data['weight'],
                'type': 'lastfm_similarity'
            })
        
        network_data = {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'total_artists': len(artist_list),
                'resolved_artists': len(resolved_artists),
                'failed_artists': len(failed_artists),
                'edges_found': len(edges),
                'min_threshold': min_threshold,
                'method': 'optimized_resolution'
            }
        }
        
        return network_data, resolved_artists
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def compare_resolution_methods():
    """Compare old vs new resolution for specific artists."""
    
    print("\n🔍 COMPARING RESOLUTION METHODS")
    print("=" * 50)
    
    # Test artists we know have issues
    test_artists = ['anyujin', 'ive', 'blackpink', 'twice']
    
    # Get config for API keys
    config = AppConfig('configurations.txt')
    lastfm_config = config.get_lastfm_config()
    
    # Initialize optimized client
    optimized_client = OptimizedLastFmClient(
        lastfm_config['api_key'], 
        lastfm_config['api_secret']
    )
    
    print(f"\n📊 Testing {len(test_artists)} problematic artists:")
    
    for artist in test_artists:
        print(f"\n🎵 Artist: {artist}")
        
        # Test optimized resolution
        result = optimized_client.resolve_artist_efficiently(artist)
        if result['resolved']:
            print(f"  ✅ Optimized: {result['canonical_name']} ({result['listeners']:,} listeners)")
            print(f"      Display: {result['display_name']}")
            print(f"      Method: {result.get('method', 'unknown')}")
        else:
            print(f"  ❌ Optimized: Failed to resolve")
        
        print(f"  📝 Expected for {artist}:")
        if artist == 'anyujin':
            print(f"      Should find: AnYujin with ~6.8K listeners")
        elif artist == 'ive':
            print(f"      Should find: IVE with ~837K listeners")
        elif artist == 'blackpink':
            print(f"      Should preserve: BLACKPINK capitalization")
        elif artist == 'twice':
            print(f"      Should preserve: TWICE capitalization")


if __name__ == "__main__":
    print("🧪 OPTIMIZED NETWORK TESTING")
    print("=" * 60)
    
    # First, compare resolution methods
    compare_resolution_methods()
    
    # Then create full network
    print(f"\n" + "=" * 60)
    network_data, resolved_artists = create_optimized_network(15, 0.08)
    
    if network_data:
        print(f"\n🎉 SUCCESS! Optimized network created.")
        print(f"📁 Network data available for visualization")
        
        # Show key differences
        print(f"\n🔍 Key Improvements:")
        if 'anyujin' in resolved_artists:
            anyujin_data = resolved_artists['anyujin']
            if anyujin_data['listeners'] > 5000:
                print(f"  ✅ AnYujin: {anyujin_data['listeners']:,} listeners (CORRECT!)")
            else:
                print(f"  ⚠️  AnYujin: {anyujin_data['listeners']:,} listeners (still wrong)")
                
        if 'ive' in resolved_artists:
            ive_data = resolved_artists['ive']
            if ive_data['listeners'] > 800000:
                print(f"  ✅ IVE: {ive_data['listeners']:,} listeners (CORRECT!)")
            else:
                print(f"  ⚠️  IVE: {ive_data['listeners']:,} listeners (still wrong)")
    else:
        print(f"\n❌ Failed to create optimized network")