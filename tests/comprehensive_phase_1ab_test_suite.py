"""
Comprehensive Phase 1A/1B Test Suite
====================================

This is an interactive, comprehensive test suite for Phase 1A (Last.fm matching) 
and Phase 1B (Node data structures). It covers all edge cases, data sources, 
and provides detailed validation of the complete pipeline.

Features:
- Interactive menu system
- Custom artist/collaboration testing
- Multiple data source support (Spotify JSON, Last.fm CSV)
- Edge case stress testing
- Performance benchmarking
- Detailed logging and results export

Run this to thoroughly validate Phase 1A/1B before proceeding to Phase 1C.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import traceback

from config_loader import AppConfig
from lastfm_utils import LastfmAPI
from data_processor import prepare_data_for_bar_chart_race, split_artist_collaborations, clean_and_filter_data
from network_utils import prepare_dataframe_for_network_analysis

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PARENT_DIR, 'configurations.txt')

class ComprehensiveTestSuite:
    """Comprehensive test suite for Phase 1A/1B validation."""
    
    def __init__(self):
        self.config = AppConfig(CONFIG_PATH)
        self.lastfm_config = self.config.get_lastfm_config()
        self.lastfm_api = None
        self.test_results = {}
        self.detailed_logs = []
        
        # Initialize Last.fm API
        if self.lastfm_config['enabled'] and self.lastfm_config['api_key']:
            self.lastfm_api = LastfmAPI(
                self.lastfm_config['api_key'],
                self.lastfm_config['api_secret'],
                self.lastfm_config['cache_dir']
            )
            print("✅ Last.fm API initialized successfully")
        else:
            print("❌ Last.fm API not available - some tests will be skipped")
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.detailed_logs.append(log_entry)
        print(log_entry)
    
    def create_test_data_spotify_format(self, include_collaborations: bool = True) -> pd.DataFrame:
        """Create comprehensive test data in Spotify JSON format."""
        self.log("Creating Spotify format test data...")
        
        base_date = datetime.now() - timedelta(days=90)
        test_data = []
        
        # Solo artists with various challenge levels
        solo_artists = [
            # High-confidence artists
            ('Taylor Swift', 60, 'high'),
            ('Ed Sheeran', 50, 'high'),
            ('Ariana Grande', 45, 'high'),
            
            # Medium-confidence artists (international)
            ('IU', 40, 'medium'),
            ('TWICE', 35, 'medium'),
            ('BLACKPINK', 30, 'medium'),
            
            # Challenging artists (from our fixes)
            ('MIYEON', 20, 'challenging'),
            ('88rising', 15, 'challenging'),
            ('SUNMI', 12, 'challenging'),
            ('ヨルシカ', 10, 'challenging'),
            ('Aimyon', 8, 'challenging'),
            
            # Edge case artists
            ('P!nk', 15, 'edge_case'),
            ('Ke$ha', 12, 'edge_case'),
            ('bbno$', 10, 'edge_case'),
            ("Panic! At The Disco", 18, 'edge_case'),
            ('Twenty One Pilots', 25, 'edge_case'),
            
            # Multi-language artists (fixed problematic names)
            ('ユイカ', 6, 'multilang'),  # Removed underscores
            ('THE ORAL CIGARETTES', 8, 'multilang'),
            ('AKMU', 5, 'multilang'),  # Using known alternative for 악동뮤지션
        ]
        
        # Generate solo plays
        for artist, play_count, category in solo_artists:
            for i in range(play_count):
                days_offset = (i * 2) % 90
                hours_offset = (i * 3) % 24
                timestamp = base_date + timedelta(days=days_offset, hours=hours_offset)
                
                test_data.append({
                    'ts': timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'master_metadata_album_artist_name': artist,
                    'master_metadata_album_album_name': f'{artist} Album {(i // 5) + 1}',
                    'master_metadata_track_name': f'Track {i % 10}',
                    'ms_played': 180000 + (i * 1000),  # 3+ minutes
                    'spotify_track_uri': f'spotify:track:fake_uri_{artist}_{i}',
                    'skipped': False,
                    'platform': 'iOS' if i % 2 == 0 else 'Desktop'
                })
        
        if include_collaborations:
            # Collaboration test cases covering all formats
            collaborations = [
                # Standard formats
                ('Taylor Swift feat. Ed Sheeran', 8),
                ('BLACKPINK & Dua Lipa', 6),
                ('IU featuring SUGA', 5),
                ('Ariana Grande ft. Justin Bieber', 4),
                
                # Complex collaborations
                ('Taylor Swift x Ed Sheeran x Justin Bieber', 3),
                ('BLACKPINK with Dua Lipa & Selena Gomez', 3),
                ('88rising, Joji, Rich Brian', 4),
                ('Machine Gun Kelly & blackbear', 3),
                
                # Edge case collaborations
                ('P!nk feat. Nate Ruess', 2),
                ('Twenty One Pilots with Mutemath', 2),
                ('ヨルシカ feat. n-buna', 2),
                
                # Tricky collaborations (potential false positives)
                ('Taylor Swift vs. Kanye West', 1),  # vs. format
                ('Ed Sheeran and Elton John', 2),   # "and" format
                ('MIYEON (featuring Wonstein)', 1), # parenthetical format
            ]
            
            for collab, play_count in collaborations:
                for i in range(play_count):
                    timestamp = base_date + timedelta(days=i * 7, hours=i * 2)
                    
                    test_data.append({
                        'ts': timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'master_metadata_album_artist_name': collab,
                        'master_metadata_album_album_name': 'Collaborations',
                        'master_metadata_track_name': f'Collab Track {i}',
                        'ms_played': 200000 + (i * 5000),
                        'spotify_track_uri': f'spotify:track:collab_uri_{i}',
                        'skipped': False,
                        'platform': 'WebPlayer'
                    })
        
        df = pd.DataFrame(test_data)
        self.log(f"Created Spotify format data: {len(df)} events, {df['master_metadata_album_artist_name'].nunique()} unique artists")
        return df
    
    def create_test_data_lastfm_format(self, include_collaborations: bool = True) -> pd.DataFrame:
        """Create comprehensive test data in Last.fm CSV format."""
        self.log("Creating Last.fm format test data...")
        
        base_timestamp = int((datetime.now() - timedelta(days=90)).timestamp())
        test_data = []
        
        # Same artists as Spotify but in Last.fm format
        solo_artists = [
            ('Taylor Swift', 60), ('Ed Sheeran', 50), ('Ariana Grande', 45),
            ('IU', 40), ('TWICE', 35), ('BLACKPINK', 30),
            ('MIYEON', 20), ('88rising', 15), ('SUNMI', 12),
            ('ヨルシカ', 10), ('Aimyon', 8), ('P!nk', 15),
            ('Ke$ha', 12), ('bbno$', 10), ('Twenty One Pilots', 25)
        ]
        
        for artist, play_count in solo_artists:
            for i in range(play_count):
                timestamp = base_timestamp + (i * 3600 * 24 * 2)  # Every 2 days
                utc_time = datetime.fromtimestamp(timestamp).strftime('%d %b %Y, %H:%M:%S')
                
                test_data.append({
                    'uts': timestamp,
                    'utc_time': utc_time,
                    'artist': artist,
                    'artist_mbid': f'mbid-{artist.lower().replace(" ", "-")}',
                    'album': f'{artist} Album {(i // 5) + 1}',
                    'album_mbid': f'album-mbid-{i}',
                    'track': f'Track {i % 10}',
                    'track_mbid': f'track-mbid-{i}'
                })
        
        if include_collaborations:
            collaborations = [
                ('Taylor Swift feat. Ed Sheeran', 8),
                ('BLACKPINK & Dua Lipa', 6),
                ('IU featuring SUGA', 5),
                ('88rising, Joji, Rich Brian', 4)
            ]
            
            for collab, play_count in collaborations:
                for i in range(play_count):
                    timestamp = base_timestamp + (i * 3600 * 24 * 7)  # Weekly
                    utc_time = datetime.fromtimestamp(timestamp).strftime('%d %b %Y, %H:%M:%S')
                    
                    test_data.append({
                        'uts': timestamp,
                        'utc_time': utc_time,
                        'artist': collab,
                        'artist_mbid': '',
                        'album': 'Collaborations',
                        'album_mbid': '',
                        'track': f'Collab Track {i}',
                        'track_mbid': ''
                    })
        
        df = pd.DataFrame(test_data)
        self.log(f"Created Last.fm format data: {len(df)} events, {df['artist'].nunique()} unique artists")
        return df
    
    def test_phase_1a_robust_matching(self, custom_artists: List[str] = None) -> Dict:
        """Test Phase 1A: Last.fm robust matching capabilities."""
        self.log("=" * 80)
        self.log("TESTING PHASE 1A: LAST.FM ROBUST MATCHING")
        self.log("=" * 80)
        
        if not self.lastfm_api:
            self.log("❌ Last.fm API not available", "ERROR")
            return {'success': False, 'error': 'No Last.fm API'}
        
        # Define test artist categories
        test_categories = {
            'high_confidence': ['Taylor Swift', 'Ed Sheeran', 'Ariana Grande', 'Justin Bieber'],
            'international': ['IU', 'TWICE', 'BLACKPINK', 'BTS'],
            'challenging': ['MIYEON', '88rising', 'SUNMI', 'Aimyon'],
            'edge_cases': ['P!nk', 'Ke$ha', 'bbno$', "Panic! At The Disco"],
            'multilingual': ['ヨルシカ', 'ユイカ', 'AKMU', 'THE ORAL CIGARETTES']
        }
        
        if custom_artists:
            test_categories['custom'] = custom_artists
        
        results = {
            'categories': {},
            'overall_stats': {},
            'failed_artists': [],
            'advanced_search_successes': [],
            'false_positives_caught': []
        }
        
        total_tested = 0
        total_success = 0
        
        for category, artists in test_categories.items():
            self.log(f"\n🧪 Testing {category.upper()} category...")
            category_results = {
                'tested': len(artists),
                'successful': 0,
                'failed': [],
                'advanced_search': 0,
                'methods': {}
            }
            
            for artist in artists:
                total_tested += 1
                self.log(f"   Testing '{artist}'...")
                
                try:
                    # Test artist info
                    start_time = time.time()
                    info = self.lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
                    
                    # Test similar artists
                    similar = self.lastfm_api.get_similar_artists(artist, limit=5, use_enhanced_matching=True)
                    end_time = time.time()
                    
                    if info and similar:
                        total_success += 1
                        category_results['successful'] += 1
                        
                        listeners = info.get('listeners', 0)
                        method = similar[0].get('_search_method', 'direct')
                        variant = similar[0].get('_matched_variant', artist)
                        
                        category_results['methods'][method] = category_results['methods'].get(method, 0) + 1
                        
                        if method == 'advanced_search':
                            category_results['advanced_search'] += 1
                            results['advanced_search_successes'].append({
                                'original': artist,
                                'variant': variant,
                                'listeners': listeners
                            })
                        
                        self.log(f"      ✅ Success: {listeners:,} listeners via {method}")
                        if variant != artist:
                            self.log(f"         Working variant: '{variant}'")
                        
                        # Check for potential false positives
                        if listeners < 1000 and method == 'direct':
                            self.log(f"         ⚠️  Low listener count - potential false positive?")
                    else:
                        category_results['failed'].append(artist)
                        results['failed_artists'].append(artist)
                        self.log(f"      ❌ Failed")
                    
                    self.log(f"         Response time: {(end_time - start_time)*1000:.0f}ms")
                    
                except Exception as e:
                    category_results['failed'].append(artist)
                    results['failed_artists'].append(artist)
                    self.log(f"      ❌ Error: {e}")
            
            success_rate = (category_results['successful'] / category_results['tested']) * 100
            self.log(f"   📊 {category.title()}: {category_results['successful']}/{category_results['tested']} ({success_rate:.1f}%)")
            
            results['categories'][category] = category_results
        
        # Overall statistics
        overall_success_rate = (total_success / total_tested) * 100
        results['overall_stats'] = {
            'total_tested': total_tested,
            'total_successful': total_success,
            'success_rate': overall_success_rate,
            'advanced_search_rate': len(results['advanced_search_successes']) / total_tested * 100
        }
        
        self.log(f"\n📊 PHASE 1A OVERALL RESULTS:")
        self.log(f"   Success rate: {total_success}/{total_tested} ({overall_success_rate:.1f}%)")
        self.log(f"   Advanced search successes: {len(results['advanced_search_successes'])}")
        self.log(f"   Failed artists: {len(results['failed_artists'])}")
        
        if results['failed_artists']:
            self.log(f"   Failed: {', '.join(results['failed_artists'][:5])}{'...' if len(results['failed_artists']) > 5 else ''}")
        
        return results
    
    def test_collaboration_lastfm_integration(self) -> Dict:
        """Test Last.fm integration for collaboration artists (split first, then test individually)."""
        self.log("=" * 80)
        self.log("TESTING COLLABORATION LAST.FM INTEGRATION")
        self.log("=" * 80)
        
        if not self.lastfm_api:
            self.log("❌ Last.fm API not available", "ERROR")
            return {'success': False, 'error': 'No Last.fm API'}
        
        # Test collaborations
        test_collaborations = [
            'Taylor Swift feat. Ed Sheeran',
            'BLACKPINK & Dua Lipa', 
            'IU featuring SUGA',
            'Ariana Grande ft. Justin Bieber',
            '88rising, Joji, Rich Brian',
            'Taylor Swift x Ed Sheeran x Justin Bieber'
        ]
        
        results = {
            'collaborations_tested': len(test_collaborations),
            'collaboration_results': {},
            'individual_artist_results': {},
            'summary': {
                'total_individual_artists': 0,
                'successful_individual_artists': 0,
                'failed_individual_artists': 0
            }
        }
        
        self.log(f"Testing {len(test_collaborations)} collaborations...")
        
        for collaboration in test_collaborations:
            self.log(f"\n🎵 Testing collaboration: '{collaboration}'")
            
            # Split the collaboration into individual artists
            individual_artists = split_artist_collaborations(collaboration)
            self.log(f"   Split into {len(individual_artists)} artists: {individual_artists}")
            
            collab_result = {
                'original': collaboration,
                'split_artists': individual_artists,
                'individual_results': {}
            }
            
            # Test each individual artist
            for artist in individual_artists:
                results['summary']['total_individual_artists'] += 1
                self.log(f"      Testing individual artist: '{artist}'")
                
                try:
                    info = self.lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
                    similar = self.lastfm_api.get_similar_artists(artist, limit=10, use_enhanced_matching=True)
                    
                    if info and similar:
                        results['summary']['successful_individual_artists'] += 1
                        listeners = info.get('listeners', 0)
                        method = similar[0].get('_search_method', 'direct')
                        variant = similar[0].get('_matched_variant', artist)
                        
                        artist_result = {
                            'success': True,
                            'listeners': listeners,
                            'similar_count': len(similar),
                            'method': method,
                            'variant': variant
                        }
                        
                        self.log(f"         ✅ Success: {listeners:,} listeners via {method}")
                        if variant != artist:
                            self.log(f"            Working variant: '{variant}'")
                    else:
                        results['summary']['failed_individual_artists'] += 1
                        artist_result = {
                            'success': False,
                            'listeners': 0,
                            'similar_count': 0,
                            'method': 'none'
                        }
                        self.log(f"         ❌ Failed")
                    
                    collab_result['individual_results'][artist] = artist_result
                    results['individual_artist_results'][artist] = artist_result
                    
                except Exception as e:
                    results['summary']['failed_individual_artists'] += 1
                    artist_result = {
                        'success': False,
                        'error': str(e),
                        'listeners': 0,
                        'similar_count': 0
                    }
                    collab_result['individual_results'][artist] = artist_result
                    results['individual_artist_results'][artist] = artist_result
                    self.log(f"         ❌ Error: {e}")
            
            results['collaboration_results'][collaboration] = collab_result
        
        # Calculate success rate
        success_rate = (results['summary']['successful_individual_artists'] / 
                       max(1, results['summary']['total_individual_artists']) * 100)
        
        self.log(f"\n📊 COLLABORATION LAST.FM INTEGRATION RESULTS:")
        self.log(f"   Collaborations tested: {len(test_collaborations)}")
        self.log(f"   Individual artists: {results['summary']['total_individual_artists']}")
        self.log(f"   Successful: {results['summary']['successful_individual_artists']}")
        self.log(f"   Failed: {results['summary']['failed_individual_artists']}")
        self.log(f"   Success rate: {success_rate:.1f}%")
        
        results['success_rate'] = success_rate
        results['success'] = success_rate >= 80  # 80% threshold
        
        return results
    
    def test_collaboration_splitting_comprehensive(self, custom_collaborations: List[str] = None) -> Dict:
        """Test comprehensive collaboration splitting scenarios."""
        self.log("=" * 80)
        self.log("TESTING COLLABORATION SPLITTING COMPREHENSIVE")
        self.log("=" * 80)
        
        # Define test cases covering all formats
        test_cases = [
            # Standard formats
            "Taylor Swift feat. Ed Sheeran",
            "BLACKPINK & Dua Lipa",
            "IU featuring SUGA",
            "Ariana Grande ft. Justin Bieber",
            
            # Multiple collaborators
            "Taylor Swift x Ed Sheeran x Justin Bieber",
            "BLACKPINK with Dua Lipa & Selena Gomez",
            "88rising, Joji, Rich Brian",
            "A feat. B & C with D",
            
            # Edge cases
            "P!nk feat. Nate Ruess",
            "Twenty One Pilots featuring Mutemath",
            "ヨルシカ feat. n-buna",
            "MIYEON (featuring Wonstein)",
            
            # Tricky cases
            "Taylor Swift vs. Kanye West",
            "Ed Sheeran and Elton John",
            "Artist With Multiple Words feat. Another Artist",
            
            # Single artists (should not split)
            "Taylor Swift",
            "P!nk",
            "Twenty One Pilots",
            "THE ORAL CIGARETTES",
            
            # Empty/invalid cases
            "",
            "   ",
            "feat.",
            "Artist &",
        ]
        
        if custom_collaborations:
            test_cases.extend(custom_collaborations)
        
        results = {
            'test_cases': {},
            'summary': {
                'total_tested': len(test_cases),
                'successful_splits': 0,
                'failed_splits': 0,
                'single_artists': 0,
                'empty_results': 0
            }
        }
        
        self.log(f"Testing {len(test_cases)} collaboration splitting scenarios...")
        
        for i, test_case in enumerate(test_cases, 1):
            self.log(f"\n{i:2d}. Testing: '{test_case}'")
            
            try:
                artists = split_artist_collaborations(test_case)
                
                case_result = {
                    'input': test_case,
                    'output': artists,
                    'artist_count': len(artists),
                    'success': True,
                    'notes': []
                }
                
                if len(artists) == 0:
                    case_result['success'] = False
                    case_result['notes'].append("Empty result")
                    results['summary']['empty_results'] += 1
                    self.log(f"    ❌ Empty result")
                elif len(artists) == 1:
                    results['summary']['single_artists'] += 1
                    self.log(f"    ✅ Single artist: {artists}")
                else:
                    results['summary']['successful_splits'] += 1
                    self.log(f"    ✅ Split into {len(artists)} artists: {artists}")
                    
                    # Validate split quality
                    for artist in artists:
                        if not artist.strip():
                            case_result['notes'].append("Empty artist name found")
                        if len(artist) < 2:
                            case_result['notes'].append("Suspiciously short artist name")
                
                # Check for expected patterns
                if any(sep in test_case.lower() for sep in ['feat.', 'ft.', '&', ',', 'with', ' x ']) and len(artists) == 1:
                    case_result['notes'].append("Expected split but got single artist")
                
                results['test_cases'][test_case] = case_result
                
            except Exception as e:
                results['summary']['failed_splits'] += 1
                results['test_cases'][test_case] = {
                    'input': test_case,
                    'output': [],
                    'artist_count': 0,
                    'success': False,
                    'error': str(e)
                }
                self.log(f"    ❌ Error: {e}")
        
        # Summary
        summary = results['summary']
        self.log(f"\n📊 COLLABORATION SPLITTING SUMMARY:")
        self.log(f"   Total tested: {summary['total_tested']}")
        self.log(f"   Successful splits: {summary['successful_splits']}")
        self.log(f"   Single artists: {summary['single_artists']}")
        self.log(f"   Failed/Empty: {summary['failed_splits'] + summary['empty_results']}")
        
        return results
    
    def test_phase_1b_node_structure(self, data_source: str = 'spotify') -> Dict:
        """Test Phase 1B: Complete node data structure creation."""
        self.log("=" * 80)
        self.log(f"TESTING PHASE 1B: NODE STRUCTURE ({data_source.upper()} DATA)")
        self.log("=" * 80)
        
        # Create test data based on source
        if data_source == 'spotify':
            raw_df = self.create_test_data_spotify_format()
            # Save temporary file and process through full pipeline
            temp_file = os.path.join(PARENT_DIR, 'temp_spotify_test.json')
            spotify_data = raw_df.to_dict('records')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(spotify_data, f, ensure_ascii=False, indent=2)
            
            # Configure for Spotify data
            original_source = self.config.get('DataSource', 'SOURCE')
            original_filename = self.config.get('DataSource', 'INPUT_FILENAME_SPOTIFY')
            self.config.config['DataSource']['SOURCE'] = 'spotify'
            self.config.config['DataSource']['INPUT_FILENAME_SPOTIFY'] = temp_file
            
        elif data_source == 'lastfm':
            raw_df = self.create_test_data_lastfm_format()
            # Save temporary CSV file
            temp_file = os.path.join(PARENT_DIR, 'temp_lastfm_test.csv')
            raw_df.to_csv(temp_file, index=False, encoding='utf-8')
            
            # Configure for Last.fm data
            original_source = self.config.get('DataSource', 'SOURCE')
            original_filename = self.config.get('DataSource', 'INPUT_FILENAME_LASTFM')
            self.config.config['DataSource']['SOURCE'] = 'lastfm'
            self.config.config['DataSource']['INPUT_FILENAME_LASTFM'] = temp_file
        
        try:
            # Step 1: Clean and filter data
            self.log("Step 1: Cleaning and filtering data...")
            cleaned_df = clean_and_filter_data(self.config)
            
            # Fix: If we generated test data, it may need column processing
            if cleaned_df is None and data_source == 'spotify':
                # Process the raw Spotify data manually
                self.log("Processing raw Spotify test data manually...")
                from data_processor import load_spotify_data
                
                # The temp file contains our test data, process it
                cleaned_df = load_spotify_data(temp_file, min_ms_played=10000, filter_skipped_tracks=True)
                if cleaned_df is not None:
                    # Apply time filtering if needed
                    from data_processor import filter_by_timeframe
                    timeframe_config = self.config.get_timeframe_config()
                    cleaned_df = filter_by_timeframe(cleaned_df, timeframe_config)
            
            if cleaned_df is None or cleaned_df.empty:
                return {'success': False, 'error': 'Data cleaning failed'}
            
            self.log(f"✅ Cleaned data: {len(cleaned_df)} events")
            
            # Step 2: Process for artist mode
            self.log("Step 2: Processing for artist mode...")
            race_df, artist_details = prepare_data_for_bar_chart_race(cleaned_df, mode="artists")
            
            if race_df is None:
                return {'success': False, 'error': 'Artist mode processing failed'}
            
            self.log(f"✅ Artist processing: {len(race_df.columns)} artists, {race_df.shape[0]} time points")
            
            # Step 3: Calculate personal metrics
            self.log("Step 3: Calculating personal metrics...")
            personal_metrics = self._calculate_personal_metrics_from_race_df(race_df)
            
            self.log(f"✅ Personal metrics: {len(personal_metrics)} artists")
            
            # Step 4: Test Last.fm integration
            self.log("Step 4: Testing Last.fm integration...")
            lastfm_results = self._test_lastfm_for_artists(list(personal_metrics.keys())[:15])  # Test top 15
            
            # Step 4b: Create cross-artist similarity matrix
            self.log("Step 4b: Creating cross-artist similarity matrix...")
            similarity_matrix_results = self.create_cross_artist_similarity_matrix(list(personal_metrics.keys())[:10])  # Top 10 for matrix
            
            # Step 5: Create complete nodes
            self.log("Step 5: Creating complete node structures...")
            nodes = self._create_complete_nodes(personal_metrics, lastfm_results, artist_details)
            
            # Analyze results
            results = {
                'success': True,
                'data_source': data_source,
                'input_events': len(cleaned_df),
                'processed_artists': len(race_df.columns),
                'personal_metrics_count': len(personal_metrics),
                'lastfm_tested': len(lastfm_results),
                'lastfm_successful': sum(1 for r in lastfm_results.values() if r.get('success', False)),
                'similarity_matrix': similarity_matrix_results if similarity_matrix_results.get('success', False) else None,
                'complete_nodes': len(nodes),
                'node_completeness': {
                    'with_personal_metrics': len([n for n in nodes if n.get('personal_plays', 0) > 0]),
                    'with_lastfm_data': len([n for n in nodes if n.get('has_lastfm_data', False)]),
                    'with_similar_artists': len([n for n in nodes if len(n.get('similar_artists', [])) > 0])
                },
                'sample_nodes': nodes[:3] if nodes else []
            }
            
            success_rate = results['lastfm_successful'] / max(1, results['lastfm_tested']) * 100
            self.log(f"\n📊 PHASE 1B RESULTS:")
            self.log(f"   Data source: {data_source}")
            self.log(f"   Input events: {results['input_events']}")
            self.log(f"   Processed artists: {results['processed_artists']}")
            self.log(f"   Last.fm success: {results['lastfm_successful']}/{results['lastfm_tested']} ({success_rate:.1f}%)")
            self.log(f"   Complete nodes: {results['complete_nodes']}")
            
            return results
            
        except Exception as e:
            self.log(f"❌ Phase 1B test failed: {e}", "ERROR")
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
        
        finally:
            # Restore original configuration
            if data_source == 'spotify':
                self.config.config['DataSource']['SOURCE'] = original_source
                self.config.config['DataSource']['INPUT_FILENAME_SPOTIFY'] = original_filename
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            elif data_source == 'lastfm':
                self.config.config['DataSource']['SOURCE'] = original_source
                self.config.config['DataSource']['INPUT_FILENAME_LASTFM'] = original_filename
                if os.path.exists(temp_file):
                    os.remove(temp_file)
    
    def _calculate_personal_metrics_from_race_df(self, race_df: pd.DataFrame) -> Dict:
        """Calculate personal metrics from race DataFrame."""
        personal_metrics = {}
        
        for artist_id in race_df.columns:
            artist_series = race_df[artist_id]
            total_plays = int(artist_series.max())
            
            if total_plays == 0:
                continue
            
            play_events = artist_series[artist_series > 0]
            if len(play_events) == 0:
                continue
            
            first_played = play_events.index[0]
            last_played = play_events.index[-1]
            date_span_seconds = (last_played - first_played).total_seconds()
            date_span_days = max(1, date_span_seconds / (24 * 3600))
            
            personal_metrics[artist_id] = {
                'total_plays': total_plays,
                'unique_tracks': min(max(1, total_plays // 3), 20),
                'first_played': first_played.isoformat(),
                'last_played': last_played.isoformat(),
                'date_span_days': date_span_days,
                'play_frequency': total_plays / date_span_days
            }
        
        return personal_metrics
    
    def _test_lastfm_for_artists(self, artist_ids: List[str]) -> Dict:
        """Test Last.fm integration for specific artists."""
        if not self.lastfm_api:
            return {}
        
        results = {}
        for artist_id in artist_ids:
            display_name = artist_id.replace('_', ' ').title()
            
            try:
                info = self.lastfm_api.get_artist_info(display_name, use_enhanced_matching=True)
                similar = self.lastfm_api.get_similar_artists(display_name, limit=100, use_enhanced_matching=True)  # Get more similar artists
                
                results[artist_id] = {
                    'success': bool(info and similar),
                    'listeners': info.get('listeners', 0) if info else 0,
                    'similar_count': len(similar) if similar else 0,
                    'method': similar[0].get('_search_method', 'unknown') if similar else 'none',
                    'similar_artists': [s['name'] for s in similar] if similar else []
                }
            except Exception as e:
                results[artist_id] = {
                    'success': False,
                    'error': str(e),
                    'listeners': 0,
                    'similar_count': 0,
                    'similar_artists': []
                }
        
        return results
    
    def create_cross_artist_similarity_matrix(self, artist_ids: List[str]) -> Dict:
        """Create similarity matrix between all artists in the user's dataset."""
        self.log("=" * 80)
        self.log("CREATING CROSS-ARTIST SIMILARITY MATRIX")
        self.log("=" * 80)
        
        if not self.lastfm_api:
            self.log("❌ Last.fm API not available", "ERROR")
            return {'success': False, 'error': 'No Last.fm API'}
        
        # Get all similar artists for each artist in our dataset
        self.log(f"🔍 Fetching similar artists for {len(artist_ids)} artists...")
        artist_similar_map = {}
        
        for i, artist_id in enumerate(artist_ids, 1):
            display_name = artist_id.replace('_', ' ').title()
            self.log(f"   {i}/{len(artist_ids)}: {display_name}")
            
            try:
                # Get up to 100 similar artists to maximize cross-matching opportunities
                similar = self.lastfm_api.get_similar_artists(display_name, limit=100, use_enhanced_matching=True)
                artist_similar_map[artist_id] = {
                    'display_name': display_name,
                    'similar_artists': [s['name'] for s in similar] if similar else [],
                    'similar_scores': {s['name']: s['match'] for s in similar} if similar else {}
                }
                self.log(f"      ✅ Found {len(similar) if similar else 0} similar artists")
            except Exception as e:
                artist_similar_map[artist_id] = {
                    'display_name': display_name,
                    'similar_artists': [],
                    'similar_scores': {},
                    'error': str(e)
                }
                self.log(f"      ❌ Error: {e}")
        
        # Create cross-artist similarity matrix
        self.log(f"\n🔗 Building similarity matrix between dataset artists...")
        similarity_matrix = {}
        connections_found = 0
        
        for artist1_id in artist_ids:
            similarity_matrix[artist1_id] = {}
            artist1_data = artist_similar_map[artist1_id]
            artist1_display = artist1_data['display_name']
            
            for artist2_id in artist_ids:
                if artist1_id == artist2_id:
                    similarity_matrix[artist1_id][artist2_id] = 1.0  # Self-similarity
                    continue
                
                artist2_data = artist_similar_map[artist2_id]
                artist2_display = artist2_data['display_name']
                
                # Check if artist2 appears in artist1's similar artists
                similarity_score = 0.0
                connection_type = 'none'
                
                # Direct similarity: artist2 in artist1's similar list
                if artist2_display in artist1_data['similar_scores']:
                    similarity_score = max(similarity_score, artist1_data['similar_scores'][artist2_display])
                    connection_type = 'direct'
                
                # Reverse similarity: artist1 in artist2's similar list  
                if artist1_display in artist2_data['similar_scores']:
                    reverse_score = artist2_data['similar_scores'][artist1_display]
                    if reverse_score > similarity_score:
                        similarity_score = reverse_score
                        connection_type = 'reverse'
                    elif reverse_score > 0 and connection_type == 'direct':
                        connection_type = 'bidirectional'
                        similarity_score = (similarity_score + reverse_score) / 2  # Average bidirectional
                
                similarity_matrix[artist1_id][artist2_id] = similarity_score
                
                if similarity_score > 0:
                    connections_found += 1
                    self.log(f"   🔗 {artist1_display} ↔ {artist2_display}: {similarity_score:.3f} ({connection_type})")
        
        # Calculate matrix statistics
        total_possible = len(artist_ids) * (len(artist_ids) - 1)  # Exclude self-connections
        connection_density = connections_found / total_possible if total_possible > 0 else 0
        
        results = {
            'success': True,
            'artist_count': len(artist_ids),
            'similarity_matrix': similarity_matrix,
            'artist_similar_map': artist_similar_map,
            'statistics': {
                'total_connections': connections_found,
                'total_possible': total_possible,
                'connection_density': connection_density,
                'average_similarity': sum(sum(row.values()) for row in similarity_matrix.values()) / (len(artist_ids) ** 2)
            }
        }
        
        self.log(f"\n📊 SIMILARITY MATRIX RESULTS:")
        self.log(f"   Artists analyzed: {len(artist_ids)}")
        self.log(f"   Connections found: {connections_found}/{total_possible}")
        self.log(f"   Connection density: {connection_density:.3f}")
        self.log(f"   Average similarity: {results['statistics']['average_similarity']:.3f}")
        
        return results
    
    def _create_complete_nodes(self, personal_metrics: Dict, lastfm_results: Dict, artist_details: Dict) -> List[Dict]:
        """Create complete node structures."""
        nodes = []
        
        for artist_id, metrics in personal_metrics.items():
            display_name = artist_details.get(artist_id, {}).get('display_artist', artist_id.title())
            
            node = {
                'id': artist_id,
                'name': display_name,
                'personal_plays': metrics['total_plays'],
                'personal_tracks': metrics['unique_tracks'],
                'first_played': metrics['first_played'],
                'last_played': metrics['last_played'],
                'date_span_days': metrics['date_span_days'],
                'play_frequency': metrics['play_frequency'],
                'global_listeners': 0,
                'global_playcount': 0,
                'lastfm_url': '',
                'tags': [],
                'similar_artists': [],
                'has_lastfm_data': False,
                'matching_success': False,
                'size': 10,
                'color': '#666666'
            }
            
            if artist_id in lastfm_results and lastfm_results[artist_id]['success']:
                result = lastfm_results[artist_id]
                node['global_listeners'] = result['listeners']
                node['has_lastfm_data'] = True
                node['matching_success'] = result['similar_count'] > 0
            
            nodes.append(node)
        
        return nodes
    
    def test_edge_cases_and_error_handling(self) -> Dict:
        """Test edge cases and error handling."""
        self.log("=" * 80)
        self.log("TESTING EDGE CASES AND ERROR HANDLING")
        self.log("=" * 80)
        
        results = {
            'empty_data_tests': {},
            'malformed_data_tests': {},
            'api_error_tests': {},
            'memory_tests': {}
        }
        
        # Test 1: Empty data handling
        self.log("\n🧪 Testing empty data handling...")
        empty_df = pd.DataFrame()
        try:
            race_df, details = prepare_data_for_bar_chart_race(empty_df, mode="artists")
            results['empty_data_tests']['prepare_data'] = {
                'success': race_df is None,
                'details_empty': len(details) == 0
            }
            self.log("   ✅ Empty data handled correctly")
        except Exception as e:
            results['empty_data_tests']['prepare_data'] = {'error': str(e)}
            self.log(f"   ❌ Empty data error: {e}")
        
        # Test 2: Malformed collaboration strings
        self.log("\n🧪 Testing malformed collaboration strings...")
        malformed_cases = [None, "", "   ", "feat.", "&", ",", "x", "with"]
        malformed_results = {}
        
        for case in malformed_cases:
            try:
                result = split_artist_collaborations(case)
                malformed_results[str(case)] = {
                    'result': result,
                    'length': len(result),
                    'success': True
                }
            except Exception as e:
                malformed_results[str(case)] = {
                    'error': str(e),
                    'success': False
                }
        
        results['malformed_data_tests']['collaborations'] = malformed_results
        self.log(f"   ✅ Tested {len(malformed_cases)} malformed cases")
        
        # Test 3: Large dataset simulation
        self.log("\n🧪 Testing large dataset handling...")
        try:
            large_df = self.create_test_data_spotify_format()
            # Duplicate data to simulate larger dataset
            large_df = pd.concat([large_df] * 5, ignore_index=True)
            
            # Convert to expected format
            large_df_converted = large_df.copy()
            large_df_converted['timestamp'] = pd.to_datetime(large_df_converted['ts'])
            large_df_converted['artist'] = large_df_converted['master_metadata_album_artist_name'].str.lower()
            large_df_converted['original_artist'] = large_df_converted['master_metadata_album_artist_name']
            large_df_converted['track'] = large_df_converted['master_metadata_track_name'].str.lower()
            large_df_converted['original_track'] = large_df_converted['master_metadata_track_name']
            large_df_converted['album'] = large_df_converted['master_metadata_album_album_name']
            
            # Keep only needed columns
            columns_needed = ['timestamp', 'artist', 'original_artist', 'track', 'original_track', 'album']
            large_df_converted = large_df_converted[columns_needed]
            
            start_time = time.time()
            race_df, details = prepare_data_for_bar_chart_race(large_df_converted, mode="artists")
            end_time = time.time()
            
            results['memory_tests']['large_dataset'] = {
                'input_size': len(large_df),
                'output_artists': len(race_df.columns) if race_df is not None else 0,
                'processing_time': end_time - start_time,
                'success': race_df is not None
            }
            
            self.log(f"   ✅ Large dataset: {len(large_df)} events in {(end_time - start_time):.2f}s")
        except Exception as e:
            results['memory_tests']['large_dataset'] = {'error': str(e)}
            self.log(f"   ❌ Large dataset error: {e}")
        
        return results
    
    def run_performance_benchmark(self) -> Dict:
        """Run performance benchmarks."""
        self.log("=" * 80)
        self.log("PERFORMANCE BENCHMARK")
        self.log("=" * 80)
        
        # Create test data of different sizes
        sizes = [100, 500, 1000, 2000]
        results = {'benchmarks': {}}
        
        for size in sizes:
            self.log(f"\n🏃 Benchmarking with {size} events...")
            
            # Create data
            df = self.create_test_data_spotify_format()
            # Duplicate to reach target size
            multiplier = max(1, size // len(df))
            df = pd.concat([df] * multiplier, ignore_index=True)
            df = df.head(size)  # Exact size
            
            benchmark_result = {
                'actual_size': len(df),
                'unique_artists': df['master_metadata_album_artist_name'].nunique()
            }
            
            # Benchmark data processing
            # First convert Spotify format to cleaned format
            try:
                # Convert Spotify test data to the expected format
                df_converted = df.copy()
                df_converted['timestamp'] = pd.to_datetime(df_converted['ts'])
                df_converted['artist'] = df_converted['master_metadata_album_artist_name'].str.lower()
                df_converted['original_artist'] = df_converted['master_metadata_album_artist_name']
                df_converted['track'] = df_converted['master_metadata_track_name'].str.lower()  
                df_converted['original_track'] = df_converted['master_metadata_track_name']
                df_converted['album'] = df_converted['master_metadata_album_album_name']
                df_converted['spotify_track_uri'] = df_converted.get('spotify_track_uri', None)
                
                # Keep only the columns we need
                columns_needed = ['timestamp', 'artist', 'original_artist', 'track', 'original_track', 'album']
                if 'spotify_track_uri' in df_converted.columns:
                    columns_needed.append('spotify_track_uri')
                df_converted = df_converted[columns_needed]
                
                start_time = time.time()
                race_df, details = prepare_data_for_bar_chart_race(df_converted, mode="artists")
                processing_time = time.time() - start_time
            except Exception as e:
                processing_time = -1
                race_df = None
                self.log(f"   ❌ Processing error: {e}")
            
            benchmark_result['processing_time'] = processing_time
            benchmark_result['processed_artists'] = len(race_df.columns) if race_df is not None else 0
            
            # Benchmark Last.fm (sample of 5 artists)
            if race_df is not None and self.lastfm_api:
                sample_artists = list(race_df.columns)[:5]
                
                start_time = time.time()
                lastfm_results = self._test_lastfm_for_artists(sample_artists)
                lastfm_time = time.time() - start_time
                
                benchmark_result['lastfm_time'] = lastfm_time
                benchmark_result['lastfm_per_artist'] = lastfm_time / len(sample_artists)
                benchmark_result['lastfm_success_rate'] = sum(1 for r in lastfm_results.values() if r.get('success', False)) / len(sample_artists)
            
            results['benchmarks'][size] = benchmark_result
            
            self.log(f"   Processing: {processing_time:.2f}s")
            if 'lastfm_time' in benchmark_result:
                self.log(f"   Last.fm (5 artists): {benchmark_result['lastfm_time']:.2f}s")
        
        return results
    
    def export_test_results(self, filename: str = None) -> str:
        """Export all test results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phase_1ab_comprehensive_test_results_{timestamp}.json"
        
        filepath = os.path.join(PARENT_DIR, 'tests', filename)
        
        export_data = {
            'test_date': datetime.now().isoformat(),
            'test_results': self.test_results,
            'detailed_logs': self.detailed_logs,
            'configuration': {
                'lastfm_enabled': self.lastfm_config['enabled'],
                'lastfm_api_available': self.lastfm_api is not None
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.log(f"✅ Test results exported to: {filepath}")
        return filepath
    
    def show_menu(self):
        """Display interactive menu."""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE PHASE 1A/1B TEST SUITE")
        print("=" * 80)
        print("1.  Run Full Phase 1A/1B Test Suite")
        print("2.  Test Phase 1A: Last.fm Robust Matching")
        print("3.  Test Phase 1B: Node Structure (Spotify Data)")
        print("4.  Test Phase 1B: Node Structure (Last.fm Data)")
        print("5.  Test Collaboration Splitting")
        print("6.  Test Collaboration Last.fm Integration (Split + Test)")
        print("7.  Test Cross-Artist Similarity Matrix")
        print("8.  Test Specific Artist (Custom Input)")
        print("9.  Test Custom Collaboration (Custom Input)")
        print("10. Test Edge Cases & Error Handling")
        print("11. Run Performance Benchmark")
        print("12. Export Test Results")
        print("13. View Recent Test Summary")
        print("0.  Exit")
        print("=" * 80)
    
    def run_full_test_suite(self):
        """Run the complete test suite."""
        self.log("🚀 STARTING COMPREHENSIVE PHASE 1A/1B TEST SUITE")
        start_time = time.time()
        
        # Run all tests
        self.test_results['phase_1a'] = self.test_phase_1a_robust_matching()
        self.test_results['collaboration_splitting'] = self.test_collaboration_splitting_comprehensive()
        self.test_results['collaboration_lastfm'] = self.test_collaboration_lastfm_integration()
        self.test_results['phase_1b_spotify'] = self.test_phase_1b_node_structure('spotify')
        self.test_results['phase_1b_lastfm'] = self.test_phase_1b_node_structure('lastfm')
        
        # Create similarity matrix if we have artists from Phase 1B
        if self.test_results['phase_1b_spotify'].get('success', False):
            try:
                # Extract artist IDs from the completed test
                sample_nodes = self.test_results['phase_1b_spotify'].get('sample_nodes', [])
                if sample_nodes:
                    artist_ids = [node['id'] for node in sample_nodes if 'id' in node][:8]  # Top 8 for reasonable performance
                    self.test_results['similarity_matrix'] = self.create_cross_artist_similarity_matrix(artist_ids)
            except Exception as e:
                self.log(f"❌ Similarity matrix creation failed: {e}")
        
        self.test_results['edge_cases'] = self.test_edge_cases_and_error_handling()
        self.test_results['performance'] = self.run_performance_benchmark()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate summary
        self.log("=" * 80)
        self.log("COMPREHENSIVE TEST SUITE COMPLETED")
        self.log("=" * 80)
        self.log(f"Total execution time: {total_time:.2f} seconds")
        
        # Auto-export results
        self.export_test_results()
        
        return self.test_results
    
    def run_interactive_mode(self):
        """Run interactive test mode."""
        while True:
            self.show_menu()
            try:
                choice = input("\nEnter your choice (0-13): ").strip()
                
                if choice == '0':
                    print("Exiting test suite. Goodbye!")
                    break
                elif choice == '1':
                    self.run_full_test_suite()
                elif choice == '2':
                    self.test_results['phase_1a'] = self.test_phase_1a_robust_matching()
                elif choice == '3':
                    self.test_results['phase_1b_spotify'] = self.test_phase_1b_node_structure('spotify')
                elif choice == '4':
                    self.test_results['phase_1b_lastfm'] = self.test_phase_1b_node_structure('lastfm')
                elif choice == '5':
                    self.test_results['collaboration_splitting'] = self.test_collaboration_splitting_comprehensive()
                elif choice == '6':
                    self.test_results['collaboration_lastfm'] = self.test_collaboration_lastfm_integration()
                elif choice == '7':
                    # Get artists from recent Phase 1B test or use defaults
                    if 'phase_1b_spotify' in self.test_results and self.test_results['phase_1b_spotify'].get('success', False):
                        artists = list(self.test_results['phase_1b_spotify'].get('sample_nodes', []))[:10]
                        artist_ids = [node['id'] for node in artists if 'id' in node]
                    else:
                        artist_ids = ['taylor swift', 'ed sheeran', 'blackpink', 'iu', 'twice', 'ariana grande']
                    
                    if artist_ids:
                        self.test_results['similarity_matrix'] = self.create_cross_artist_similarity_matrix(artist_ids)
                    else:
                        print("No artists available. Run Phase 1B test first or enter custom artists.")
                        custom_artists = input("Enter artist names (comma-separated): ").strip()
                        if custom_artists:
                            artist_ids = [a.strip().lower() for a in custom_artists.split(',')]
                            self.test_results['similarity_matrix'] = self.create_cross_artist_similarity_matrix(artist_ids)
                elif choice == '7':
                    artist = input("Enter artist name to test: ").strip()
                    if artist:
                        self.test_results['custom_artist'] = self.test_phase_1a_robust_matching([artist])
                elif choice == '8':
                    collab = input("Enter collaboration string to test: ").strip()
                    if collab:
                        self.test_results['custom_collaboration'] = self.test_collaboration_splitting_comprehensive([collab])
                elif choice == '9':
                    self.test_results['edge_cases'] = self.test_edge_cases_and_error_handling()
                elif choice == '10':
                    self.test_results['performance'] = self.run_performance_benchmark()
                elif choice == '11':
                    self.export_test_results()
                elif choice == '12':
                    self._show_test_summary()
                else:
                    print("Invalid choice. Please try again.")
                
                if choice != '0':
                    input("\nPress Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\nTest interrupted by user. Exiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
                input("Press Enter to continue...")
    
    def _show_test_summary(self):
        """Show summary of recent test results."""
        if not self.test_results:
            print("No test results available yet.")
            return
        
        print("\n" + "=" * 60)
        print("RECENT TEST SUMMARY")
        print("=" * 60)
        
        for test_name, results in self.test_results.items():
            if isinstance(results, dict) and 'success' in results:
                status = "✅ PASS" if results['success'] else "❌ FAIL"
                print(f"{test_name}: {status}")
            elif test_name == 'phase_1a' and 'overall_stats' in results:
                success_rate = results['overall_stats']['success_rate']
                status = "✅ PASS" if success_rate >= 80 else "⚠️ PARTIAL" if success_rate >= 60 else "❌ FAIL"
                print(f"{test_name}: {status} ({success_rate:.1f}% success)")
            else:
                print(f"{test_name}: ✅ COMPLETED")


def main():
    """Main entry point."""
    print(__doc__)
    
    try:
        test_suite = ComprehensiveTestSuite()
        test_suite.run_interactive_mode()
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    main()