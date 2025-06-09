"""
Test ANYUJIN in Network Building
===============================

Tests that ANYUJIN now works properly in the full network building process.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from config_loader import AppConfig
from data_processor import clean_and_filter_data
from lastfm_utils import LastfmAPI


def test_anyujin_in_network():
    """Test ANYUJIN in full network building process."""
    print("🕸️ Testing ANYUJIN in Network Building")
    print("=" * 50)
    
    try:
        config = AppConfig('configurations.txt')
        
        # Load your data
        print("📊 Loading your top artists...")
        original_source = config.get('DataSource', 'SOURCE', fallback='spotify')
        config.config['DataSource']['SOURCE'] = 'spotify'
        
        df = clean_and_filter_data(config)
        if df is None or df.empty:
            print("❌ No data available")
            return False
        
        # Get top artists including ANYUJIN
        artist_counts = df.groupby('artist').size().sort_values(ascending=False)
        original_names = df.drop_duplicates('artist').set_index('artist')['original_artist'].to_dict()
        
        # Find ANYUJIN rank
        anyujin_rank = None
        anyujin_plays = 0
        if 'anyujin' in artist_counts.index:
            anyujin_rank = list(artist_counts.index).index('anyujin') + 1
            anyujin_plays = artist_counts['anyujin']
            print(f"✅ ANYUJIN found in your data: Rank #{anyujin_rank} with {anyujin_plays} plays")
        else:
            print("❌ ANYUJIN not found in your listening data")
            return False
        
        # Test network building with ANYUJIN included
        num_artists = max(15, anyujin_rank + 2)  # Include enough to get ANYUJIN
        top_artists = artist_counts.head(num_artists)
        
        print(f"🔄 Building network with top {num_artists} artists (includes ANYUJIN)...")
        
        # Initialize Last.fm API
        lastfm_config = config.get_lastfm_config()
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Build network data
        network_data = {
            'nodes': [],
            'edges': [],
            'metadata': {
                'created': datetime.now().isoformat(),
                'artist_count': len(top_artists),
                'test_type': 'anyujin_validation'
            }
        }
        
        # Create nodes
        for rank, (artist_norm, plays) in enumerate(top_artists.items(), 1):
            original_name = original_names.get(artist_norm, artist_norm)
            network_data['nodes'].append({
                'id': artist_norm,
                'name': original_name,
                'play_count': int(plays),
                'rank': rank,
                'is_anyujin': artist_norm == 'anyujin'
            })
        
        # Test ANYUJIN specifically
        anyujin_original = original_names.get('anyujin', 'ANYUJIN')
        print(f"🧪 Testing ANYUJIN similarity (original name: '{anyujin_original}')...")
        
        anyujin_similar = lastfm_api.get_similar_artists(anyujin_original, limit=20)
        
        if anyujin_similar:
            matched_variant = anyujin_similar[0].get('_matched_variant', anyujin_original)
            print(f"✅ ANYUJIN similar artists found using variant: '{matched_variant}'")
            print(f"🎵 Top similar artists:")
            for i, similar in enumerate(anyujin_similar[:5], 1):
                print(f"   {i}. {similar['name']}: {similar['match']:.3f}")
        else:
            print(f"❌ ANYUJIN similar artists not found")
            return False
        
        # Create edges for full network
        edges_found = 0
        anyujin_connections = 0
        
        for i, (artist_norm, plays) in enumerate(top_artists.items(), 1):
            original_name = original_names.get(artist_norm, artist_norm)
            
            if i <= 5 or artist_norm == 'anyujin':  # Test top 5 + ANYUJIN for speed
                print(f"  {i}/{len(top_artists)}: {original_name}")
                
                similar_artists = lastfm_api.get_similar_artists(original_name, limit=30)
                
                if similar_artists:
                    # Check for connections to other artists in our list
                    for similar in similar_artists:
                        similar_name_lower = similar['name'].lower().strip()
                        
                        for other_artist_norm in top_artists.index:
                            if other_artist_norm != artist_norm:
                                other_original = original_names.get(other_artist_norm, other_artist_norm).lower().strip()
                                
                                if similar_name_lower == other_original:
                                    # Found a connection!
                                    network_data['edges'].append({
                                        'source': artist_norm,
                                        'target': other_artist_norm,
                                        'weight': similar['match'],
                                        'similarity_score': similar['match']
                                    })
                                    edges_found += 1
                                    
                                    # Track ANYUJIN connections specifically
                                    if artist_norm == 'anyujin' or other_artist_norm == 'anyujin':
                                        anyujin_connections += 1
        
        print(f"\n✅ Network building test completed!")
        print(f"   Total nodes: {len(network_data['nodes'])}")
        print(f"   Total edges: {len(network_data['edges'])}")
        print(f"   ANYUJIN connections: {anyujin_connections}")
        
        # Show ANYUJIN connections specifically
        if anyujin_connections > 0:
            print(f"\n🔗 ANYUJIN connections found:")
            anyujin_edges = [e for e in network_data['edges'] 
                           if e['source'] == 'anyujin' or e['target'] == 'anyujin']
            
            for edge in anyujin_edges:
                source_name = original_names.get(edge['source'], edge['source'])
                target_name = original_names.get(edge['target'], edge['target'])
                print(f"   {source_name} ↔ {target_name}: {edge['weight']:.3f}")
        
        # Save test network
        filename = f"anyujin_test_network_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Test network saved: {filename}")
        
        # Restore original source
        config.config['DataSource']['SOURCE'] = original_source
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing ANYUJIN in network: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("ANYUJIN NETWORK BUILDING TEST")
    print("=" * 60)
    
    success = test_anyujin_in_network()
    
    if success:
        print(f"\n🎉 ANYUJIN network building test PASSED!")
        print(f"   ANYUJIN can now be included in similarity networks")
        print(f"   The original network building error should be resolved")
    else:
        print(f"\n❌ ANYUJIN network building test FAILED")
        print(f"   Further investigation needed")


if __name__ == "__main__":
    # Change to main directory for proper file access
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        main()
    finally:
        os.chdir(original_dir)