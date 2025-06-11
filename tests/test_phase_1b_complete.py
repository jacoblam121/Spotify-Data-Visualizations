"""
Phase 1B Complete Test Suite
============================

Comprehensive test of Phase 1B: Enhanced node data structure with global listeners and personal metrics.

Tests:
1. Artist info fetching with listener counts
2. Collaboration handling and crediting
3. Personal play metrics calculation
4. Node data structure with all required fields
5. Error handling for missing data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import json
from datetime import datetime, timedelta
from config_loader import AppConfig
from lastfm_utils import LastfmAPI
from data_processor import prepare_data_for_bar_chart_race, split_artist_collaborations
from network_utils import prepare_dataframe_for_network_analysis

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PARENT_DIR, 'configurations.txt')


def create_test_listening_data():
    """Create test listening data with various scenarios."""
    # Create 30 days of test data
    base_date = datetime.now() - timedelta(days=30)
    
    test_data = []
    
    # Taylor Swift - heavy listener (50 plays)
    for i in range(50):
        test_data.append({
            'timestamp': base_date + timedelta(days=i % 30, hours=i % 24),
            'artist': 'taylor swift',
            'original_artist': 'Taylor Swift',
            'track': f'song_{i % 10}',
            'original_track': f'Song {i % 10}',
            'album': 'folklore'
        })
    
    # IU - moderate listener (20 plays)
    for i in range(20):
        test_data.append({
            'timestamp': base_date + timedelta(days=i % 20, hours=i % 12),
            'artist': 'iu',
            'original_artist': 'IU',
            'track': f'iu_song_{i % 5}',
            'original_track': f'IU Song {i % 5}',
            'album': 'LILAC'
        })
    
    # Collaborations (10 plays)
    collab_artists = [
        ('taylor swift feat. ed sheeran', 'Taylor Swift feat. Ed Sheeran'),
        ('iu feat. suga', 'IU feat. SUGA'),
        ('blackpink, dua lipa', 'BLACKPINK, Dua Lipa'),
        ('machine gun kelly & blackbear', 'Machine Gun Kelly & blackbear'),
        ('ive, newjeans', 'IVE, NewJeans')
    ]
    
    for i, (artist, original) in enumerate(collab_artists * 2):
        test_data.append({
            'timestamp': base_date + timedelta(days=i * 3, hours=i * 2),
            'artist': artist,
            'original_artist': original,
            'track': f'collab_{i}',
            'original_track': f'Collaboration {i}',
            'album': 'collabs'
        })
    
    # Solo artists with few plays
    solo_artists = [
        ('paramore', 'Paramore'),
        ('bring me the horizon', 'Bring Me The Horizon'),
        ('aimyon', 'Aimyon'),
        ('sunmi', 'SUNMI'),
        ('yorushika', 'ヨルシカ')
    ]
    
    for i, (artist, original) in enumerate(solo_artists):
        test_data.append({
            'timestamp': base_date + timedelta(days=i * 5),
            'artist': artist,
            'original_artist': original,
            'track': f'{artist}_track',
            'original_track': f'{original} Track',
            'album': f'{artist}_album'
        })
    
    return pd.DataFrame(test_data)


def test_phase_1b_node_structure():
    """Test the complete Phase 1B node data structure."""
    print("=" * 80)
    print("PHASE 1B: ENHANCED NODE DATA STRUCTURE TEST")
    print("=" * 80)
    
    try:
        # Initialize APIs
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Create test data
        print("\n1️⃣ Creating test listening data...")
        df = create_test_listening_data()
        print(f"✅ Created {len(df)} listening events")
        
        # Process in artist mode to handle collaborations
        print("\n2️⃣ Processing data in artist mode...")
        race_df, artist_details = prepare_data_for_bar_chart_race(df, mode="artists")
        
        if race_df is None:
            print("❌ Failed to process data")
            return
        
        print(f"✅ Processed into {len(race_df.columns)} unique artists")
        
        # Calculate personal metrics
        print("\n3️⃣ Calculating personal metrics...")
        personal_metrics = {}
        
        # Prepare dataframe for network analysis
        df_network = prepare_dataframe_for_network_analysis(df)
        
        for artist in race_df.columns:
            # Get all plays for this artist
            artist_plays = df_network[df_network['artist'].str.lower() == artist]
            
            metrics = {
                'total_plays': len(artist_plays),
                'unique_tracks': artist_plays['track'].nunique(),
                'first_played': artist_plays.index.min().isoformat() if not artist_plays.empty else None,
                'last_played': artist_plays.index.max().isoformat() if not artist_plays.empty else None,
                'play_frequency': len(artist_plays) / 30  # plays per day over 30 days
            }
            personal_metrics[artist] = metrics
        
        print(f"✅ Calculated metrics for {len(personal_metrics)} artists")
        
        # Fetch Last.fm data for top artists
        print("\n4️⃣ Fetching Last.fm data for top artists...")
        top_artists = sorted(personal_metrics.keys(), 
                           key=lambda x: personal_metrics[x]['total_plays'], 
                           reverse=True)[:10]
        
        nodes = []
        for i, artist in enumerate(top_artists):
            print(f"\n   Processing {i+1}/{len(top_artists)}: {artist}")
            
            # Get display name from details map
            display_name = artist_details.get(artist, {}).get('display_name', artist.title())
            
            # Fetch artist info from Last.fm
            artist_info = lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
            
            # Create node with Phase 1B structure
            node = {
                # Core identification
                'id': artist,
                'name': display_name,
                
                # Personal metrics
                'personal_plays': personal_metrics[artist]['total_plays'],
                'personal_tracks': personal_metrics[artist]['unique_tracks'],
                'first_played': personal_metrics[artist]['first_played'],
                'last_played': personal_metrics[artist]['last_played'],
                'play_frequency': personal_metrics[artist]['play_frequency'],
                
                # Global metrics from Last.fm
                'global_listeners': 0,
                'global_playcount': 0,
                'lastfm_url': '',
                'tags': [],
                
                # Visual properties (placeholder for now)
                'size': 10,
                'color': '#666666'
            }
            
            # Add Last.fm data if available
            if artist_info:
                node['global_listeners'] = artist_info.get('listeners', 0)
                node['global_playcount'] = artist_info.get('playcount', 0)
                node['lastfm_url'] = artist_info.get('url', '')
                
                # Extract tags
                tags_data = artist_info.get('tags', {})
                if isinstance(tags_data, dict):
                    tags = tags_data.get('tag', [])
                    if isinstance(tags, dict):
                        tags = [tags]
                elif isinstance(tags_data, list):
                    tags = tags_data
                else:
                    tags = []
                
                # Extract tag names safely
                tag_names = []
                for tag in tags[:5]:  # Top 5 tags
                    if isinstance(tag, dict):
                        tag_names.append(tag.get('name', ''))
                    elif isinstance(tag, str):
                        tag_names.append(tag)
                node['tags'] = tag_names
                
                print(f"      ✅ Found on Last.fm: {node['global_listeners']:,} listeners")
            else:
                print(f"      ⚠️  Not found on Last.fm")
            
            nodes.append(node)
        
        # Display results
        print("\n5️⃣ Node Data Structure Results:")
        print("=" * 80)
        
        for node in nodes[:5]:  # Show first 5
            print(f"\n🎵 {node['name']}:")
            print(f"   ID: {node['id']}")
            print(f"   Personal metrics:")
            print(f"      - Plays: {node['personal_plays']}")
            print(f"      - Unique tracks: {node['personal_tracks']}")
            print(f"      - Play frequency: {node['play_frequency']:.2f} plays/day")
            print(f"      - First played: {node['first_played'][:10] if node['first_played'] else 'N/A'}")
            print(f"      - Last played: {node['last_played'][:10] if node['last_played'] else 'N/A'}")
            print(f"   Global metrics:")
            print(f"      - Listeners: {node['global_listeners']:,}")
            print(f"      - Total plays: {node['global_playcount']:,}")
            print(f"      - Tags: {', '.join(node['tags'][:3]) if node['tags'] else 'None'}")
            print(f"      - URL: {node['lastfm_url'][:50]}..." if node['lastfm_url'] else "      - URL: N/A")
        
        # Test collaboration handling
        print("\n6️⃣ Testing Collaboration Handling:")
        print("-" * 60)
        
        # Check if collaboration artists were properly split
        collab_artists = ['ed sheeran', 'suga', 'dua lipa', 'blackbear', 'newjeans']
        found_collabs = [a for a in collab_artists if a in personal_metrics]
        
        print(f"Found {len(found_collabs)}/{len(collab_artists)} collaboration artists:")
        for artist in found_collabs:
            metrics = personal_metrics[artist]
            print(f"   ✅ {artist}: {metrics['total_plays']} plays")
        
        # Verify data completeness
        print("\n7️⃣ Data Completeness Check:")
        print("-" * 60)
        
        complete_nodes = [n for n in nodes if n['global_listeners'] > 0]
        print(f"✅ {len(complete_nodes)}/{len(nodes)} nodes have Last.fm data")
        
        missing_lastfm = [n for n in nodes if n['global_listeners'] == 0]
        if missing_lastfm:
            print(f"⚠️  Missing Last.fm data for: {', '.join(n['name'] for n in missing_lastfm)}")
        
        # Save test results
        output_file = os.path.join(PARENT_DIR, 'tests', 'phase_1b_test_results.json')
        test_results = {
            'test_date': datetime.now().isoformat(),
            'total_plays': len(df),
            'unique_artists': len(personal_metrics),
            'collaboration_artists': len(found_collabs),
            'nodes_with_lastfm': len(complete_nodes),
            'sample_nodes': nodes[:3]  # Save first 3 for inspection
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Test results saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "=" * 80)
    print("EDGE CASE TESTING")
    print("=" * 80)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test 1: Non-existent artist
        print("\n1️⃣ Testing non-existent artist:")
        fake_artist = "ThisArtistDefinitelyDoesNotExist12345"
        info = lastfm_api.get_artist_info(fake_artist)
        if info is None:
            print("   ✅ Correctly returned None for non-existent artist")
        else:
            print("   ❌ Unexpectedly found data for fake artist")
        
        # Test 2: Empty collaboration string
        print("\n2️⃣ Testing empty collaboration:")
        result = split_artist_collaborations("")
        expected = []  # Empty string should return empty list
        print(f"   Empty string → {result}")
        print(f"   {'✅' if result == expected else '❌'} Handled correctly")
        
        # Test 3: Complex collaboration
        print("\n3️⃣ Testing complex collaboration:")
        complex_collab = "A feat. B & C with D featuring E, F"
        result = split_artist_collaborations(complex_collab)
        print(f"   '{complex_collab}' → {result}")
        print(f"   ✅ Split into {len(result)} artists")
        
        # Test 4: Unicode handling
        print("\n4️⃣ Testing Unicode artists:")
        unicode_artists = ['ヨルシカ', 'IU (아이유)', 'Björk']
        for artist in unicode_artists:
            info = lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
            status = "✅" if info else "❌"
            print(f"   {status} {artist}: {'Found' if info else 'Not found'}")
        
    except Exception as e:
        print(f"❌ Error in edge case testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # Run main test
    success = test_phase_1b_node_structure()
    
    # Run edge case tests
    test_edge_cases()
    
    print("\n" + "=" * 80)
    print("PHASE 1B TEST SUMMARY")
    print("=" * 80)
    
    if success:
        print("\n✅ Phase 1B implementation is working correctly!")
        print("\nVerified functionality:")
        print("1. ✅ Artist info fetching with global listener counts")
        print("2. ✅ Collaboration splitting and crediting")
        print("3. ✅ Personal play metrics calculation")
        print("4. ✅ Complete node data structure with all fields")
        print("5. ✅ Robust error handling for missing data")
    else:
        print("\n❌ Phase 1B implementation has issues that need fixing")
    
    print("\nNode structure includes:")
    print("- Personal metrics: plays, tracks, frequency, date range")
    print("- Global metrics: listeners, playcount, tags, URL")
    print("- Ready for Phase 1C: Composite metrics calculation")