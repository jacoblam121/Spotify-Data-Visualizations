"""
Test Full Network Building with Robust Matching
===============================================

Tests that the full network building process now works without errors
with all previously problematic artists included.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from config_loader import AppConfig
from data_processor import clean_and_filter_data
from lastfm_utils import LastfmAPI


def test_full_network_building():
    """Test full network building with robust matching."""
    print("🕸️ Testing Full Network Building with Robust Matching")
    print("=" * 60)
    
    try:
        config = AppConfig('configurations.txt')
        
        # Load data
        print("📊 Loading your listening data...")
        original_source = config.get('DataSource', 'SOURCE', fallback='spotify')
        config.config['DataSource']['SOURCE'] = 'spotify'
        
        df = clean_and_filter_data(config)
        if df is None or df.empty:
            print("❌ No data available")
            return False
        
        # Get top artists
        artist_counts = df.groupby('artist').size().sort_values(ascending=False)
        original_names = df.drop_duplicates('artist').set_index('artist')['original_artist'].to_dict()
        
        # Test with enough artists to include all problematic ones
        num_artists = 25
        top_artists = artist_counts.head(num_artists)
        
        print(f"🔄 Building network with top {num_artists} artists...")
        print(f"📈 Total plays in dataset: {len(df):,}")
        print(f"🎵 Unique artists in dataset: {len(artist_counts):,}")
        
        # Check which problematic artists are included
        problematic_artists = ['ive', 'anyujin', 'kiss of life', 'jeon somi']
        included_problematic = []
        
        for artist in problematic_artists:
            if artist in top_artists.index:
                rank = list(top_artists.index).index(artist) + 1
                plays = top_artists[artist]
                original_name = original_names.get(artist, artist)
                included_problematic.append(artist)
                print(f"   ✅ {original_name}: Rank #{rank} ({plays} plays)")
        
        if not included_problematic:
            print("⚠️  No problematic artists in top 25, network should work fine anyway")
        
        # Initialize Last.fm API with robust matching
        lastfm_config = config.get_lastfm_config()
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Build network data structure
        network_data = {
            'nodes': [],
            'edges': [],
            'metadata': {
                'created': datetime.now().isoformat(),
                'artist_count': len(top_artists),
                'test_type': 'robust_matching_validation',
                'problematic_artists_included': included_problematic
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
                'is_problematic': artist_norm in problematic_artists
            })
        
        # Fetch similarity data - this is where errors would occur
        print(f"\n🔄 Fetching similarity data with robust matching...")
        
        failed_artists = []
        successful_artists = []
        similarity_cache = {}
        
        for i, (artist_norm, plays) in enumerate(top_artists.items(), 1):
            original_name = original_names.get(artist_norm, artist_norm)
            
            print(f"  {i:2d}/{len(top_artists)}: {original_name}", end=" ")
            
            try:
                similar_artists = lastfm_api.get_similar_artists(original_name, limit=30)
                
                if similar_artists:
                    matched_variant = similar_artists[0].get('_matched_variant', original_name)
                    print(f"✅ ({len(similar_artists)} similar, variant: '{matched_variant}')")
                    
                    similarity_cache[artist_norm] = similar_artists
                    successful_artists.append(artist_norm)
                else:
                    print(f"❌ (no similar artists found)")
                    failed_artists.append(artist_norm)
                    
            except Exception as e:
                print(f"❌ (error: {str(e)[:30]})")
                failed_artists.append(artist_norm)
        
        # Create edges based on similarities
        print(f"\n🔗 Building network connections...")
        
        edges_created = 0
        
        for artist_norm in successful_artists:
            similar_artists = similarity_cache.get(artist_norm, [])
            
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
                            edges_created += 1
        
        # Results
        print(f"\n✅ Network building completed!")
        print(f"   📊 Nodes (artists): {len(network_data['nodes'])}")
        print(f"   🔗 Edges (connections): {len(network_data['edges'])}")
        print(f"   📈 Network density: {len(network_data['edges']) / (len(network_data['nodes']) * (len(network_data['nodes']) - 1) / 2):.3f}")
        print(f"   ✅ Successful artists: {len(successful_artists)}/{len(top_artists)} ({len(successful_artists)/len(top_artists)*100:.1f}%)")
        
        if failed_artists:
            print(f"   ❌ Failed artists: {len(failed_artists)}")
            for artist_norm in failed_artists:
                original_name = original_names.get(artist_norm, artist_norm)
                print(f"      - {original_name}")
        
        # Check problematic artists specifically
        problematic_success = 0
        for artist in included_problematic:
            if artist in successful_artists:
                problematic_success += 1
        
        print(f"\n🎯 Problematic Artists Status:")
        print(f"   Included in test: {len(included_problematic)}")
        print(f"   Successfully processed: {problematic_success}")
        
        if problematic_success == len(included_problematic):
            print(f"   🎉 ALL PROBLEMATIC ARTISTS WORKING!")
        
        # Save test network
        filename = f"robust_test_network_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Test network saved: {filename}")
        
        # Restore original source
        config.config['DataSource']['SOURCE'] = original_source
        
        # Final assessment
        overall_success = len(failed_artists) == 0
        return overall_success
        
    except Exception as e:
        print(f"❌ Error in network building test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 70)
    print("ROBUST NETWORK BUILDING - FULL INTEGRATION TEST")
    print("=" * 70)
    
    success = test_full_network_building()
    
    print("\n" + "=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)
    
    if success:
        print("🎉 ROBUST MATCHING SYSTEM: FULLY OPERATIONAL")
        print("   ✅ Network building completes without errors")
        print("   ✅ All problematic artists are now handled correctly")
        print("   ✅ System is ready for production use")
        print("\n💡 You can now run the full network building with confidence!")
        print("   The enhanced matching will automatically handle edge cases.")
    else:
        print("⚠️  ROBUST MATCHING SYSTEM: NEEDS ATTENTION")
        print("   Some artists still failing - check logs above for details")


if __name__ == "__main__":
    # Change to main directory for proper file access
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        main()
    finally:
        os.chdir(original_dir)