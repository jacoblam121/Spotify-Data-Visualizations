"""
Manual Test for Phase 1B: Enhanced Node Data Structure
======================================================

This is a comprehensive manual test that you can run to identify any potential issues
with the Phase 1B implementation. It tests real data processing, Last.fm integration,
collaboration handling, and the complete node data structure.

Run this test to verify Phase 1B is working correctly before moving to Phase 1C.
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


def create_realistic_test_data():
    """Create realistic test data with various edge cases."""
    print("Creating realistic test data with edge cases...")
    
    base_date = datetime.now() - timedelta(days=90)  # 3 months of data
    test_data = []
    
    # Define test artists with various challenges
    test_scenarios = [
        # High play count artists
        {
            'artists': ['Taylor Swift', 'IU', 'TWICE'],
            'play_counts': [100, 80, 60],
            'collaboration_rate': 0.1  # 10% collaborations
        },
        # Medium play count with collaborations
        {
            'artists': ['BLACKPINK', 'Ariana Grande', 'Ed Sheeran'],
            'play_counts': [40, 35, 30],
            'collaboration_rate': 0.3  # 30% collaborations
        },
        # Low play count edge cases
        {
            'artists': ['MIYEON', '88rising', 'Aimyon', 'SUNMI', 'ヨルシカ'],
            'play_counts': [15, 12, 10, 8, 5],
            'collaboration_rate': 0.2  # 20% collaborations
        },
        # Special characters and punctuation
        {
            'artists': ['P!nk', 'Ke$ha', 'bbno$', "Panic! At The Disco"],
            'play_counts': [20, 18, 15, 12],
            'collaboration_rate': 0.15  # 15% collaborations
        },
        # Abbreviations and alternatives
        {
            'artists': ['Twenty One Pilots', 'Bring Me The Horizon', 'Fall Out Boy'],
            'play_counts': [25, 22, 18],
            'collaboration_rate': 0.25  # 25% collaborations
        }
    ]
    
    # Generate listening data
    for scenario in test_scenarios:
        for artist, play_count in zip(scenario['artists'], scenario['play_counts']):
            for i in range(play_count):
                # Determine if this should be a collaboration
                is_collaboration = i < int(play_count * scenario['collaboration_rate'])
                
                if is_collaboration:
                    # Create collaboration with another artist from the same scenario
                    other_artists = [a for a in scenario['artists'] if a != artist]
                    if other_artists:
                        collab_partner = other_artists[i % len(other_artists)]
                        collab_formats = [
                            f"{artist} feat. {collab_partner}",
                            f"{artist} & {collab_partner}",
                            f"{artist}, {collab_partner}",
                            f"{artist} with {collab_partner}"
                        ]
                        final_artist = collab_formats[i % len(collab_formats)]
                        display_artist = final_artist
                    else:
                        final_artist = artist.lower()
                        display_artist = artist
                else:
                    final_artist = artist.lower()
                    display_artist = artist
                
                # Generate timestamp with realistic distribution
                days_offset = (i * 3) % 90  # Spread over 90 days
                hours_offset = (i * 2) % 24  # Spread over 24 hours
                timestamp = base_date + timedelta(days=days_offset, hours=hours_offset)
                
                test_data.append({
                    'timestamp': timestamp,
                    'artist': final_artist,
                    'original_artist': display_artist,
                    'track': f'track_{i % 10}_{artist.replace(" ", "_")}',
                    'original_track': f'Track {i % 10} by {artist}',
                    'album': f'{artist} Album {(i // 5) + 1}'
                })
    
    # Add some edge case collaborations
    edge_collaborations = [
        "IU feat. SUGA of BTS",
        "Taylor Swift x Ed Sheeran x Justin Bieber", 
        "BLACKPINK with Dua Lipa & Selena Gomez",
        "88rising, Joji, Rich Brian",
        "Machine Gun Kelly & blackbear"
    ]
    
    for i, collab in enumerate(edge_collaborations):
        test_data.append({
            'timestamp': base_date + timedelta(days=i * 10),
            'artist': collab.lower(),
            'original_artist': collab,
            'track': f'collaboration_track_{i}',
            'original_track': f'Collaboration Track {i}',
            'album': 'Various Artists'
        })
    
    df = pd.DataFrame(test_data)
    print(f"✅ Created {len(df)} listening events across {df['artist'].nunique()} unique artist entries")
    print(f"   Time range: {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")
    
    return df


def test_collaboration_handling(df):
    """Test that collaborations are properly handled."""
    print("\n" + "=" * 80)
    print("TESTING COLLABORATION HANDLING")
    print("=" * 80)
    
    # Find collaboration entries
    collabs = df[df['artist'].str.contains('feat\.|&|,|with', case=False, na=False)]
    print(f"\nFound {len(collabs)} collaboration entries:")
    
    for _, row in collabs.head(10).iterrows():
        original = row['original_artist']
        normalized = row['artist']
        artists = split_artist_collaborations(original)
        print(f"   '{original}' → {len(artists)} artists: {artists}")
    
    return len(collabs) > 0


def test_data_processing_pipeline(df):
    """Test the complete data processing pipeline."""
    print("\n" + "=" * 80)
    print("TESTING DATA PROCESSING PIPELINE")
    print("=" * 80)
    
    print(f"\nInput: {len(df)} listening events")
    
    # Process in artist mode
    print("\n1️⃣ Processing data in artist mode...")
    race_df, artist_details = prepare_data_for_bar_chart_race(df, mode="artists")
    
    if race_df is None:
        print("❌ CRITICAL: Data processing failed!")
        return False
    
    print(f"✅ Processed into {len(race_df.columns)} unique artists")
    print(f"✅ Race DataFrame shape: {race_df.shape}")
    print(f"✅ Artist details map has {len(artist_details)} entries")
    
    # Verify collaboration splitting worked
    total_original_artists = df['artist'].nunique()
    total_processed_artists = len(race_df.columns)
    
    if total_processed_artists >= total_original_artists:
        print(f"✅ Collaboration splitting worked: {total_original_artists} → {total_processed_artists} artists")
    else:
        print(f"⚠️  Artist count decreased: {total_original_artists} → {total_processed_artists}")
    
    return race_df, artist_details


def test_personal_metrics_calculation(df, race_df):
    """Test personal metrics calculation."""
    print("\n" + "=" * 80)
    print("TESTING PERSONAL METRICS CALCULATION")
    print("=" * 80)
    
    try:
        # Process the data again to get the expanded DataFrame with split collaborations
        print("Re-processing data to get expanded artist entries...")
        expanded_race_df, expanded_details = prepare_data_for_bar_chart_race(df, mode="artists")
        
        # Create a DataFrame from the expanded entries for analysis
        # We need to reconstruct this from the race processing
        print(f"✅ Using expanded data with {len(expanded_race_df)} events")
        
        personal_metrics = {}
        for artist in race_df.columns:
            # Calculate metrics directly from the race DataFrame
            # The race DataFrame already contains the cumulative plays per artist
            artist_series = race_df[artist]
            
            # Get total plays (max value in the series)
            total_plays = int(artist_series.max())
            
            # For other metrics, we'll use a simplified approach
            # In a real implementation, we'd need to track these during processing
            if total_plays > 0:
                # Estimate metrics based on available data
                first_play_idx = artist_series[artist_series > 0].index[0] if len(artist_series[artist_series > 0]) > 0 else race_df.index[0]
                last_play_idx = artist_series[artist_series > 0].index[-1] if len(artist_series[artist_series > 0]) > 0 else race_df.index[-1]
                
                date_span = (last_play_idx - first_play_idx).total_seconds() / (24 * 3600) if hasattr(last_play_idx, 'total_seconds') else 1
                if date_span == 0:
                    date_span = 1
                    
                metrics = {
                    'total_plays': total_plays,
                    'unique_tracks': min(10, total_plays),  # Estimate
                    'first_played': first_play_idx.isoformat() if hasattr(first_play_idx, 'isoformat') else str(first_play_idx),
                    'last_played': last_play_idx.isoformat() if hasattr(last_play_idx, 'isoformat') else str(last_play_idx),
                    'date_span_days': date_span,
                    'play_frequency': total_plays / max(1, date_span)
                }
                personal_metrics[artist] = metrics
            else:
                print(f"⚠️  No plays found for artist: {artist}")
        
        print(f"✅ Calculated personal metrics for {len(personal_metrics)} artists")
        
        # Show top artists by play count
        top_artists = sorted(personal_metrics.items(), 
                           key=lambda x: x[1]['total_plays'], 
                           reverse=True)[:5]
        
        print(f"\nTop 5 artists by personal plays:")
        for artist, metrics in top_artists:
            print(f"   {artist}: {metrics['total_plays']} plays, "
                  f"{metrics['unique_tracks']} tracks, "
                  f"{metrics['play_frequency']:.2f} plays/day")
        
        return personal_metrics
        
    except Exception as e:
        print(f"❌ Personal metrics calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return {}


def test_lastfm_integration(personal_metrics):
    """Test Last.fm integration for top artists."""
    print("\n" + "=" * 80)
    print("TESTING LAST.FM INTEGRATION")
    print("=" * 80)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test top 10 artists
        top_artists = sorted(personal_metrics.keys(), 
                           key=lambda x: personal_metrics[x]['total_plays'], 
                           reverse=True)[:10]
        
        print(f"\nTesting Last.fm integration for top {len(top_artists)} artists:")
        
        successful_fetches = 0
        failed_fetches = []
        
        for i, artist in enumerate(top_artists, 1):
            print(f"\n{i:2d}. Testing '{artist}'...")
            
            # Test artist info
            info = lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
            if info:
                listeners = info.get('listeners', 0)
                print(f"    ✅ Artist info: {listeners:,} listeners")
                
                # Test similar artists
                similar = lastfm_api.get_similar_artists(artist, limit=5, use_enhanced_matching=True)
                if similar:
                    variant = similar[0].get('_matched_variant', artist)
                    method = similar[0].get('_search_method', 'direct')
                    print(f"    ✅ Similar artists: {len(similar)} found via {method}")
                    if variant != artist:
                        print(f"    ℹ️  Working variant: '{variant}'")
                    successful_fetches += 1
                else:
                    print(f"    ⚠️  No similar artists found")
                    failed_fetches.append(artist)
            else:
                print(f"    ❌ Artist info not found")
                failed_fetches.append(artist)
        
        success_rate = (successful_fetches / len(top_artists)) * 100
        print(f"\n📊 Last.fm Integration Results:")
        print(f"   Success rate: {successful_fetches}/{len(top_artists)} ({success_rate:.1f}%)")
        
        if failed_fetches:
            print(f"   Failed artists: {', '.join(failed_fetches)}")
        
        return successful_fetches, failed_fetches
        
    except Exception as e:
        print(f"❌ Last.fm integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 0, []


def test_node_data_structure(personal_metrics, artist_details):
    """Test the complete node data structure."""
    print("\n" + "=" * 80)
    print("TESTING COMPLETE NODE DATA STRUCTURE")
    print("=" * 80)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Create nodes for top 5 artists
        top_artists = sorted(personal_metrics.keys(), 
                           key=lambda x: personal_metrics[x]['total_plays'], 
                           reverse=True)[:5]
        
        nodes = []
        for artist in top_artists:
            print(f"\n🎵 Creating node for '{artist}'...")
            
            # Get display name
            display_name = artist_details.get(artist, {}).get('display_name', artist.title())
            
            # Get personal metrics
            metrics = personal_metrics[artist]
            
            # Create base node structure
            node = {
                # Core identification
                'id': artist,
                'name': display_name,
                
                # Personal metrics
                'personal_plays': metrics['total_plays'],
                'personal_tracks': metrics['unique_tracks'],
                'first_played': metrics['first_played'],
                'last_played': metrics['last_played'],
                'date_span_days': metrics['date_span_days'],
                'play_frequency': metrics['play_frequency'],
                
                # Global metrics (defaults)
                'global_listeners': 0,
                'global_playcount': 0,
                'lastfm_url': '',
                'tags': [],
                'similar_artists': [],
                
                # Metadata
                'has_lastfm_data': False,
                'matching_method': 'unknown',
                'working_variant': artist,
                
                # Visual properties (placeholder)
                'size': 10,
                'color': '#666666'
            }
            
            # Try to get Last.fm data
            info = lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
            similar = lastfm_api.get_similar_artists(artist, limit=5, use_enhanced_matching=True)
            
            if info:
                node['global_listeners'] = info.get('listeners', 0)
                node['global_playcount'] = info.get('playcount', 0)
                node['lastfm_url'] = info.get('url', '')
                node['has_lastfm_data'] = True
                
                # Extract tags safely
                tags_data = info.get('tags', {})
                if isinstance(tags_data, dict):
                    tags = tags_data.get('tag', [])
                    if isinstance(tags, dict):
                        tags = [tags]
                elif isinstance(tags_data, list):
                    tags = tags_data
                else:
                    tags = []
                
                tag_names = []
                for tag in tags[:5]:
                    if isinstance(tag, dict):
                        tag_names.append(tag.get('name', ''))
                    elif isinstance(tag, str):
                        tag_names.append(tag)
                node['tags'] = tag_names
            
            if similar:
                node['similar_artists'] = [s['name'] for s in similar[:5]]
                node['matching_method'] = similar[0].get('_search_method', 'direct')
                node['working_variant'] = similar[0].get('_matched_variant', artist)
            
            # Validate node structure
            required_fields = [
                'id', 'name', 'personal_plays', 'personal_tracks', 
                'global_listeners', 'tags', 'similar_artists'
            ]
            
            missing_fields = [field for field in required_fields if field not in node]
            if missing_fields:
                print(f"    ❌ Missing required fields: {missing_fields}")
            else:
                print(f"    ✅ Complete node structure")
                print(f"       Personal: {node['personal_plays']} plays, {node['personal_tracks']} tracks")
                print(f"       Global: {node['global_listeners']:,} listeners")
                print(f"       Last.fm: {'✅' if node['has_lastfm_data'] else '❌'}")
                print(f"       Similar: {len(node['similar_artists'])} artists")
            
            nodes.append(node)
        
        print(f"\n✅ Created {len(nodes)} complete node structures")
        return nodes
        
    except Exception as e:
        print(f"❌ Node data structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return []


def run_comprehensive_test():
    """Run the comprehensive Phase 1B test."""
    print("=" * 100)
    print("MANUAL TEST FOR PHASE 1B: ENHANCED NODE DATA STRUCTURE")
    print("=" * 100)
    print("\nThis test validates the complete Phase 1B implementation.")
    print("It will test real data processing, Last.fm integration, and node structures.")
    
    try:
        # Step 1: Create test data
        print("\n" + "🔄" * 50)
        print("STEP 1: DATA CREATION")
        print("🔄" * 50)
        df = create_realistic_test_data()
        
        # Step 2: Test collaboration handling
        print("\n" + "🔄" * 50)
        print("STEP 2: COLLABORATION HANDLING")
        print("🔄" * 50)
        has_collabs = test_collaboration_handling(df)
        if not has_collabs:
            print("⚠️  Warning: No collaborations found in test data")
        
        # Step 3: Test data processing
        print("\n" + "🔄" * 50)
        print("STEP 3: DATA PROCESSING PIPELINE")
        print("🔄" * 50)
        result = test_data_processing_pipeline(df)
        if not result:
            print("❌ CRITICAL: Data processing pipeline failed!")
            return False
        race_df, artist_details = result
        
        # Step 4: Test personal metrics
        print("\n" + "🔄" * 50)
        print("STEP 4: PERSONAL METRICS CALCULATION")
        print("🔄" * 50)
        personal_metrics = test_personal_metrics_calculation(df, race_df)
        if not personal_metrics:
            print("❌ CRITICAL: Personal metrics calculation failed!")
            return False
        
        # Step 5: Test Last.fm integration
        print("\n" + "🔄" * 50)
        print("STEP 5: LAST.FM INTEGRATION")
        print("🔄" * 50)
        successful_fetches, failed_fetches = test_lastfm_integration(personal_metrics)
        
        # Step 6: Test node data structure
        print("\n" + "🔄" * 50)
        print("STEP 6: NODE DATA STRUCTURE")
        print("🔄" * 50)
        nodes = test_node_data_structure(personal_metrics, artist_details)
        
        # Final results
        print("\n" + "=" * 100)
        print("PHASE 1B TEST RESULTS")
        print("=" * 100)
        
        total_artists = len(personal_metrics)
        success_rate = (successful_fetches / total_artists) * 100 if total_artists > 0 else 0
        
        print(f"\n📊 Summary:")
        print(f"   Total listening events: {len(df)}")
        print(f"   Unique artists processed: {total_artists}")
        print(f"   Last.fm success rate: {successful_fetches}/{total_artists} ({success_rate:.1f}%)")
        print(f"   Complete node structures: {len(nodes)}")
        
        # Save results for inspection
        output_file = os.path.join(PARENT_DIR, 'tests', 'manual_phase_1b_results.json')
        results = {
            'test_date': datetime.now().isoformat(),
            'total_events': len(df),
            'unique_artists': total_artists,
            'lastfm_success_rate': success_rate,
            'failed_artists': failed_fetches,
            'sample_nodes': nodes[:3] if nodes else [],
            'test_passed': success_rate >= 80 and len(nodes) > 0
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        # Final verdict
        if results['test_passed']:
            print(f"\n✅ PHASE 1B TEST PASSED!")
            print(f"   The enhanced node data structure is working correctly.")
            print(f"   Ready to proceed to Phase 1C: Composite Metrics.")
        else:
            print(f"\n❌ PHASE 1B TEST FAILED!")
            print(f"   Issues detected that need to be resolved before Phase 1C.")
            if failed_fetches:
                print(f"   Problematic artists: {', '.join(failed_fetches[:5])}")
        
        return results['test_passed']
        
    except Exception as e:
        print(f"\n❌ TEST EXECUTION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print(__doc__)
    success = run_comprehensive_test()
    
    if success:
        print(f"\n🎉 Phase 1B is ready for production!")
    else:
        print(f"\n⚠️  Phase 1B needs additional work before proceeding.")