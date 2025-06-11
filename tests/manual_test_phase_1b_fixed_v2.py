"""
Manual Test for Phase 1B: Enhanced Node Data Structure (Fixed V2)
================================================================

This is the definitive fix for Phase 1B that addresses the architectural issue
where collaboration splitting creates a mismatch between expanded artist data
and personal metrics calculation.

The core issue was that:
1. prepare_data_for_bar_chart_race() expands collaborations (e.g., "Taylor Swift feat. Ed Sheeran" → ["Taylor Swift", "Ed Sheeran"])
2. Personal metrics calculation uses the expanded race_df.columns 
3. But network analysis was using the original unexpanded DataFrame
4. This caused a mismatch where individual artists couldn't find their plays

Fix: Use the expanded DataFrame consistently throughout the pipeline.
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

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PARENT_DIR, 'configurations.txt')


def create_comprehensive_test_data():
    """Create comprehensive test data that specifically tests the collaboration issue."""
    print("Creating comprehensive test data...")
    
    base_date = datetime.now() - timedelta(days=60)
    
    # Define test artists including collaborations that caused issues
    test_scenarios = [
        # Solo artists with high play counts
        {'artist': 'Taylor Swift', 'plays': 50},
        {'artist': 'IU', 'plays': 35},
        {'artist': 'TWICE', 'plays': 30},
        {'artist': 'BLACKPINK', 'plays': 25},
        
        # Artists that appear in collaborations
        {'artist': 'Ed Sheeran', 'plays': 20},
        {'artist': 'Dua Lipa', 'plays': 18},
        {'artist': 'SUGA', 'plays': 15},
        {'artist': 'Joji', 'plays': 12},
        
        # Challenging artists
        {'artist': 'MIYEON', 'plays': 10},
        {'artist': '88rising', 'plays': 8},
        {'artist': 'SUNMI', 'plays': 6},
        {'artist': 'ヨルシカ', 'plays': 5},
    ]
    
    # Create solo plays
    test_data = []
    for scenario in test_scenarios:
        artist = scenario['artist']
        play_count = scenario['plays']
        
        for i in range(play_count):
            days_offset = (i * 2) % 60
            hours_offset = (i * 3) % 24
            timestamp = base_date + timedelta(days=days_offset, hours=hours_offset)
            
            test_data.append({
                'timestamp': timestamp,
                'artist': artist.lower(),
                'original_artist': artist,
                'track': f'track_{i % 5}',
                'original_track': f'Track {i % 5}',
                'album': f'{artist} Album'
            })
    
    # Add specific collaboration cases that were problematic
    collaborations = [
        ('Taylor Swift feat. Ed Sheeran', 8),
        ('BLACKPINK & Dua Lipa', 6), 
        ('IU featuring SUGA', 5),
        ('88rising, Joji', 4),
        ('Taylor Swift x Ed Sheeran x Justin Bieber', 3),
        ('BLACKPINK with Dua Lipa & Selena Gomez', 2),
    ]
    
    for collab, play_count in collaborations:
        for i in range(play_count):
            timestamp = base_date + timedelta(days=i * 5, hours=i)
            test_data.append({
                'timestamp': timestamp,
                'artist': collab.lower(),
                'original_artist': collab,
                'track': f'collab_track_{i}',
                'original_track': f'Collaboration Track {i}',
                'album': 'Collaborations'
            })
    
    df = pd.DataFrame(test_data)
    print(f"✅ Created {len(df)} listening events for {df['original_artist'].nunique()} unique artist entries")
    return df


def test_collaboration_pipeline_integration(df):
    """Test the complete collaboration pipeline integration."""
    print("\n" + "=" * 80)
    print("TESTING COLLABORATION PIPELINE INTEGRATION") 
    print("=" * 80)
    
    print(f"\n📊 Input data analysis:")
    print(f"   Total events: {len(df)}")
    print(f"   Unique original artists: {df['original_artist'].nunique()}")
    print(f"   Unique normalized artists: {df['artist'].nunique()}")
    
    # Find collaboration entries
    collabs = df[df['artist'].str.contains('feat\\.|&|,|with', case=False, na=False)]
    print(f"   Collaboration entries: {len(collabs)}")
    
    if len(collabs) > 0:
        print(f"\n🔗 Sample collaborations:")
        for _, row in collabs.head(3).iterrows():
            original = row['original_artist']
            artists = split_artist_collaborations(original)
            print(f"   '{original}' → {len(artists)} artists: {artists}")
    
    # Process through the full pipeline
    print(f"\n🔄 Processing through data pipeline...")
    race_df, artist_details = prepare_data_for_bar_chart_race(df, mode="artists")
    
    if race_df is None:
        print("❌ CRITICAL: Data processing failed!")
        return None, None
    
    print(f"✅ Pipeline processing successful:")
    print(f"   Input events: {len(df)}")
    print(f"   Output artists: {len(race_df.columns)}")
    print(f"   Race DataFrame shape: {race_df.shape}")
    print(f"   Artist details entries: {len(artist_details)}")
    
    # Verify collaboration expansion worked
    expected_expansion = len(collabs) > 0
    actual_expansion = len(race_df.columns) > df['original_artist'].nunique()
    
    if expected_expansion and actual_expansion:
        print(f"✅ Collaboration expansion verified")
    elif not expected_expansion:
        print(f"ℹ️  No collaborations to expand")
    else:
        print(f"⚠️  Expected collaboration expansion but didn't see it")
    
    return race_df, artist_details


def calculate_personal_metrics_from_expanded_data(race_df, artist_details):
    """Calculate personal metrics using the expanded race DataFrame correctly."""
    print("\n" + "=" * 80)
    print("CALCULATING PERSONAL METRICS FROM EXPANDED DATA")
    print("=" * 80)
    
    if race_df is None or race_df.empty:
        print("❌ No race DataFrame provided")
        return {}
    
    print(f"📊 Analyzing {len(race_df.columns)} artists from expanded data...")
    
    personal_metrics = {}
    
    for artist_id in race_df.columns:
        # Get the time series for this artist
        artist_series = race_df[artist_id]
        
        # Calculate total plays (final cumulative value)
        total_plays = int(artist_series.max())
        
        if total_plays == 0:
            continue
        
        # Find first and last play times
        play_events = artist_series[artist_series > 0]
        if len(play_events) == 0:
            continue
            
        first_played = play_events.index[0]
        last_played = play_events.index[-1]
        
        # Calculate date span
        date_span_seconds = (last_played - first_played).total_seconds()
        date_span_days = max(1, date_span_seconds / (24 * 3600))
        
        # Calculate unique tracks (estimate based on typical listening patterns)
        # In a real implementation, this would be tracked during processing
        unique_tracks = min(max(1, total_plays // 3), 20)  # Rough estimate
        
        # Calculate play frequency
        play_frequency = total_plays / date_span_days
        
        # Store metrics
        metrics = {
            'total_plays': total_plays,
            'unique_tracks': unique_tracks,
            'first_played': first_played.isoformat(),
            'last_played': last_played.isoformat(),
            'date_span_days': date_span_days,
            'play_frequency': play_frequency
        }
        
        personal_metrics[artist_id] = metrics
        
        # Get display name from artist details
        display_name = artist_details.get(artist_id, {}).get('display_artist', artist_id.title())
        print(f"   ✅ {display_name}: {total_plays} plays, {unique_tracks} tracks, {play_frequency:.2f} plays/day")
    
    print(f"\n✅ Calculated personal metrics for {len(personal_metrics)} artists")
    return personal_metrics


def test_lastfm_integration_with_expanded_data(personal_metrics):
    """Test Last.fm integration using the correctly calculated personal metrics."""
    print("\n" + "=" * 80)
    print("TESTING LAST.FM INTEGRATION WITH EXPANDED DATA")
    print("=" * 80)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test all artists with personal metrics
        artists_to_test = list(personal_metrics.keys())
        print(f"🧪 Testing Last.fm integration for {len(artists_to_test)} artists...")
        
        successful_fetches = 0
        failed_artists = []
        lastfm_results = {}
        
        for i, artist_id in enumerate(artists_to_test, 1):
            # Convert artist_id back to display format for Last.fm lookup
            # The artist_id is normalized (lowercase), so we need the display name
            display_name = artist_id.replace('_', ' ').title()
            
            print(f"\n{i:2d}. Testing '{display_name}' (id: {artist_id})...")
            
            try:
                # Test artist info
                info = lastfm_api.get_artist_info(display_name, use_enhanced_matching=True)
                similar = lastfm_api.get_similar_artists(display_name, limit=5, use_enhanced_matching=True)
                
                if info and similar:
                    listeners = info.get('listeners', 0)
                    variant = similar[0].get('_matched_variant', display_name)
                    method = similar[0].get('_search_method', 'direct')
                    
                    print(f"   ✅ Success: {listeners:,} listeners, {len(similar)} similar artists")
                    if variant != display_name:
                        print(f"   ℹ️  Working variant: '{variant}' via {method}")
                    
                    successful_fetches += 1
                    lastfm_results[artist_id] = {
                        'success': True,
                        'listeners': listeners,
                        'similar_count': len(similar),
                        'method': method,
                        'variant': variant
                    }
                else:
                    print(f"   ❌ Failed: No data found")
                    failed_artists.append(display_name)
                    lastfm_results[artist_id] = {
                        'success': False,
                        'listeners': 0,
                        'similar_count': 0,
                        'method': 'none',
                        'variant': display_name
                    }
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                failed_artists.append(display_name)
                lastfm_results[artist_id] = {
                    'success': False,
                    'error': str(e),
                    'listeners': 0,
                    'similar_count': 0
                }
        
        # Calculate success rate
        success_rate = (successful_fetches / len(artists_to_test)) * 100 if artists_to_test else 0
        
        print(f"\n📊 Last.fm Integration Results:")
        print(f"   Success rate: {successful_fetches}/{len(artists_to_test)} ({success_rate:.1f}%)")
        
        if failed_artists:
            print(f"   Failed artists: {', '.join(failed_artists[:5])}{'...' if len(failed_artists) > 5 else ''}")
        
        return successful_fetches, failed_artists, lastfm_results
        
    except Exception as e:
        print(f"❌ Last.fm integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 0, [], {}


def create_complete_node_structures(personal_metrics, lastfm_results, artist_details):
    """Create complete node structures using the fixed pipeline."""
    print("\n" + "=" * 80)
    print("CREATING COMPLETE NODE STRUCTURES")
    print("=" * 80)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        nodes = []
        
        for artist_id, metrics in personal_metrics.items():
            print(f"\n🎵 Creating node for '{artist_id}'...")
            
            # Get display name from artist details
            display_name = artist_details.get(artist_id, {}).get('display_artist', artist_id.title())
            
            # Create base node structure
            node = {
                # Core identification
                'id': artist_id,
                'name': display_name,
                
                # Personal metrics (from expanded data)
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
                
                # Status tracking
                'has_lastfm_data': False,
                'matching_success': False,
                'matching_method': 'unknown',
                'working_variant': display_name,
                
                # Visual properties
                'size': 10,
                'color': '#666666'
            }
            
            # Add Last.fm data if available
            if artist_id in lastfm_results and lastfm_results[artist_id]['success']:
                result = lastfm_results[artist_id]
                
                # Get fresh data to ensure we have all fields
                try:
                    info = lastfm_api.get_artist_info(display_name, use_enhanced_matching=True)
                    similar = lastfm_api.get_similar_artists(display_name, limit=5, use_enhanced_matching=True)
                    
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
                        node['matching_success'] = True
                        node['matching_method'] = similar[0].get('_search_method', 'direct')
                        node['working_variant'] = similar[0].get('_matched_variant', display_name)
                    
                except Exception as e:
                    print(f"   ⚠️  Error fetching fresh Last.fm data: {e}")
            
            # Validate node structure
            required_fields = ['id', 'name', 'personal_plays', 'global_listeners', 'similar_artists']
            missing = [f for f in required_fields if f not in node or node[f] is None]
            
            if not missing:
                print(f"   ✅ Complete node: {node['personal_plays']} plays, {node['global_listeners']:,} listeners")
                if node['matching_success']:
                    print(f"      Similar artists: {len(node['similar_artists'])}, Method: {node['matching_method']}")
            else:
                print(f"   ❌ Missing fields: {missing}")
            
            nodes.append(node)
        
        print(f"\n✅ Created {len(nodes)} complete node structures")
        
        # Analyze completeness
        complete_nodes = [n for n in nodes if n['has_lastfm_data']]
        successful_matching = [n for n in nodes if n['matching_success']]
        
        print(f"\n📊 Node Structure Analysis:")
        print(f"   Total nodes: {len(nodes)}")
        print(f"   With Last.fm data: {len(complete_nodes)} ({len(complete_nodes)/len(nodes)*100:.1f}%)")
        print(f"   With similar artists: {len(successful_matching)} ({len(successful_matching)/len(nodes)*100:.1f}%)")
        
        return nodes
        
    except Exception as e:
        print(f"❌ Node structure creation failed: {e}")
        import traceback
        traceback.print_exc()
        return []


def run_comprehensive_phase_1b_test():
    """Run the comprehensive Phase 1B test with architectural fixes."""
    print("=" * 100)
    print("PHASE 1B TEST: ENHANCED NODE DATA STRUCTURE (ARCHITECTURAL FIX)")
    print("=" * 100)
    print("\nThis test fixes the architectural issue where collaboration splitting")
    print("created a mismatch between expanded artist data and personal metrics.")
    
    try:
        # Step 1: Create comprehensive test data
        print("\n🔄 Step 1: Creating comprehensive test data...")
        df = create_comprehensive_test_data()
        
        # Step 2: Test collaboration pipeline integration
        print("\n🔄 Step 2: Testing collaboration pipeline integration...")
        race_df, artist_details = test_collaboration_pipeline_integration(df)
        
        if race_df is None:
            print("❌ CRITICAL: Collaboration pipeline failed!")
            return False
        
        # Step 3: Calculate personal metrics from expanded data
        print("\n🔄 Step 3: Calculating personal metrics from expanded data...")
        personal_metrics = calculate_personal_metrics_from_expanded_data(race_df, artist_details)
        
        if not personal_metrics:
            print("❌ CRITICAL: Personal metrics calculation failed!")
            return False
        
        # Step 4: Test Last.fm integration with expanded data
        print("\n🔄 Step 4: Testing Last.fm integration with expanded data...")
        successful_fetches, failed_artists, lastfm_results = test_lastfm_integration_with_expanded_data(personal_metrics)
        
        # Step 5: Create complete node structures
        print("\n🔄 Step 5: Creating complete node structures...")
        nodes = create_complete_node_structures(personal_metrics, lastfm_results, artist_details)
        
        # Final assessment
        print("\n" + "=" * 100)
        print("PHASE 1B TEST RESULTS (ARCHITECTURAL FIX)")
        print("=" * 100)
        
        total_artists = len(personal_metrics)
        success_rate = (successful_fetches / total_artists * 100) if total_artists > 0 else 0
        
        print(f"\n📊 Final Assessment:")
        print(f"   Input events: {len(df)}")
        print(f"   Processed artists: {total_artists}")
        print(f"   Last.fm success rate: {successful_fetches}/{total_artists} ({success_rate:.1f}%)")
        print(f"   Complete nodes created: {len(nodes)}")
        print(f"   Collaboration pipeline: {'✅ WORKING' if race_df is not None else '❌ FAILED'}")
        print(f"   Personal metrics: {'✅ WORKING' if personal_metrics else '❌ FAILED'}")
        print(f"   Last.fm integration: {'✅ WORKING' if success_rate >= 70 else '⚠️ NEEDS WORK'}")
        
        # Save results
        output_file = os.path.join(PARENT_DIR, 'tests', 'phase_1b_architectural_fix_results.json')
        results = {
            'test_date': datetime.now().isoformat(),
            'test_version': 'architectural_fix_v2',
            'input_events': len(df),
            'processed_artists': total_artists,
            'lastfm_success_rate': success_rate,
            'successful_fetches': successful_fetches,
            'failed_artists': failed_artists[:10],  # Limit for readability
            'node_count': len(nodes),
            'sample_nodes': nodes[:2] if nodes else [],
            'pipeline_working': race_df is not None,
            'personal_metrics_working': bool(personal_metrics),
            'lastfm_integration_working': success_rate >= 70,
            'test_passed': success_rate >= 70 and personal_metrics and race_df is not None
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        # Final verdict
        if results['test_passed']:
            print(f"\n✅ PHASE 1B ARCHITECTURAL FIX SUCCESSFUL!")
            print(f"   The collaboration pipeline and personal metrics are now properly aligned.")
            print(f"   Ready to proceed to Phase 1C: Composite Metrics.")
        else:
            print(f"\n❌ PHASE 1B STILL HAS ISSUES!")
            if success_rate < 70:
                print(f"   Last.fm success rate too low: {success_rate:.1f}% (need ≥70%)")
            if not personal_metrics:
                print(f"   Personal metrics calculation failed")
            if race_df is None:
                print(f"   Collaboration pipeline failed")
        
        return results['test_passed']
        
    except Exception as e:
        print(f"\n❌ TEST EXECUTION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print(__doc__)
    success = run_comprehensive_phase_1b_test()
    
    if success:
        print(f"\n🎉 Phase 1B architectural issues have been resolved!")
        print(f"   The collaboration pipeline now works correctly with personal metrics.")
    else:
        print(f"\n⚠️  Phase 1B architectural fix needs more work.")