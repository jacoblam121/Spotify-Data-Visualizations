#!/usr/bin/env python3
"""
Complete API Integration Test Suite
Tests both Last.fm and Spotify API integration for top artists from user's dataset.
Shows comprehensive data: Spotify followers/popularity, Last.fm listeners/similarity.
Configurable for any number of top artists.
"""

import os
import time
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from lastfm_utils import LastfmAPI
from spotify_artist_network_utils import get_spotify_artist_data_for_network
from config_loader import AppConfig
from data_processor import clean_and_filter_data

class CompleteAPITestSuite:
    """Complete test suite for both Last.fm and Spotify APIs."""
    
    def __init__(self, config_file: str = 'configurations.txt'):
        """Initialize the test suite."""
        load_dotenv()
        self.config = AppConfig(config_file)
        self.lastfm_config = self.config.get_lastfm_config()
        
        # Check API credentials
        if not self.lastfm_config['api_key']:
            raise ValueError("No Last.fm API key found. Add to .env or configurations.txt")
        
        # Initialize APIs
        self.lastfm_api = LastfmAPI(
            self.lastfm_config['api_key'],
            self.lastfm_config['api_secret'], 
            self.lastfm_config['cache_dir']
        )
        
        self.test_results = []
        self.summary_stats = {}
    
    def load_user_top_artists(self, top_n: int = 25, min_plays: int = 5) -> List[Tuple[str, int]]:
        """
        Load the user's actual top artists from their dataset.
        
        Args:
            top_n: Number of top artists to return
            min_plays: Minimum plays required to include artist
            
        Returns:
            List of (artist_name, play_count) tuples
        """
        print(f"📊 Loading top {top_n} artists from user dataset...")
        
        try:
            # Load and process user data
            df = clean_and_filter_data(self.config)
            
            if df is None or df.empty:
                raise ValueError("No data loaded from user dataset")
            
            if 'artist' not in df.columns:
                raise ValueError("No 'artist' column found in dataset")
            
            # Get artist play counts
            artist_counts = df.groupby('artist').size().sort_values(ascending=False)
            
            # Filter by minimum plays
            artist_counts_filtered = artist_counts[artist_counts >= min_plays]
            
            # Get top N
            top_artists = artist_counts_filtered.head(top_n)
            
            print(f"✅ Loaded {len(top_artists)} artists (min {min_plays} plays)")
            print(f"📈 Play count range: {top_artists.iloc[-1]} - {top_artists.iloc[0]} plays")
            
            return [(artist, int(count)) for artist, count in top_artists.items()]
            
        except Exception as e:
            print(f"❌ Failed to load user data: {e}")
            print(f"💡 Make sure your data files are configured correctly in configurations.txt")
            raise
    
    def test_complete_artist_data(self, artist_name: str, play_count: int) -> Dict:
        """
        Test complete data fetching for a single artist from both APIs.
        
        Args:
            artist_name: Artist name to test
            play_count: Play count from user's data
            
        Returns:
            Complete test result dictionary
        """
        result = {
            'artist_name': artist_name,
            'user_play_count': play_count,
            'start_time': time.time(),
            
            # Overall status
            'overall_success': False,
            'apis_working': [],
            'apis_failed': [],
            
            # Last.fm data
            'lastfm_success': False,
            'lastfm_canonical_name': None,
            'lastfm_listeners': 0,
            'lastfm_playcount': 0,
            'lastfm_similar_count': 0,
            'lastfm_top_similar': [],
            'lastfm_matched_variant': None,
            'lastfm_resolution_method': None,
            'lastfm_error': None,
            
            # Spotify data
            'spotify_success': False,
            'spotify_canonical_name': None,
            'spotify_id': None,
            'spotify_followers': 0,
            'spotify_popularity': 0,
            'spotify_genres': [],
            'spotify_photo_url': None,
            'spotify_error': None,
            
            # Timing
            'lastfm_time': 0,
            'spotify_time': 0,
            'total_time': 0
        }
        
        # Test Last.fm API
        lastfm_start = time.time()
        try:
            # Get artist info
            artist_info = self.lastfm_api.get_artist_info(artist_name)
            if artist_info:
                result['lastfm_success'] = True
                result['lastfm_canonical_name'] = artist_info.get('name', artist_name)
                result['lastfm_listeners'] = int(artist_info.get('listeners', 0))
                result['lastfm_playcount'] = int(artist_info.get('playcount', 0))
                result['lastfm_matched_variant'] = artist_info.get('_matched_variant')
                result['lastfm_resolution_method'] = artist_info.get('_resolution_method')
                result['apis_working'].append('Last.fm')
            
            # Get similar artists
            similar_artists = self.lastfm_api.get_similar_artists(artist_name, limit=10)
            if similar_artists:
                result['lastfm_similar_count'] = len(similar_artists)
                result['lastfm_top_similar'] = [
                    {'name': s['name'], 'match': float(s.get('match', 0))}
                    for s in similar_artists[:5]
                ]
                if not result['lastfm_success']:  # If artist_info failed but similar worked
                    result['lastfm_success'] = True
                    result['apis_working'].append('Last.fm')
                    # Try to get resolution info from similar results
                    if similar_artists and '_matched_variant' in similar_artists[0]:
                        result['lastfm_matched_variant'] = similar_artists[0]['_matched_variant']
                        result['lastfm_resolution_method'] = similar_artists[0].get('_resolution_method')
        
        except Exception as e:
            result['lastfm_error'] = str(e)
            result['apis_failed'].append('Last.fm')
        
        result['lastfm_time'] = time.time() - lastfm_start
        
        # Test Spotify API
        spotify_start = time.time()
        try:
            spotify_data = get_spotify_artist_data_for_network(artist_name)
            if spotify_data:
                result['spotify_success'] = True
                result['spotify_canonical_name'] = spotify_data.get('canonical_name', artist_name)
                result['spotify_id'] = spotify_data.get('spotify_id')
                result['spotify_followers'] = int(spotify_data.get('followers', 0))
                result['spotify_popularity'] = int(spotify_data.get('popularity', 0))
                result['spotify_genres'] = spotify_data.get('genres', [])
                result['spotify_photo_url'] = spotify_data.get('photo_url')
                result['apis_working'].append('Spotify')
        
        except Exception as e:
            result['spotify_error'] = str(e)
            result['apis_failed'].append('Spotify')
        
        result['spotify_time'] = time.time() - spotify_start
        
        # Calculate overall results
        result['overall_success'] = result['lastfm_success'] or result['spotify_success']
        result['total_time'] = time.time() - result['start_time']
        
        return result
    
    def run_complete_api_test(self, top_n: int = 25, min_plays: int = 5, 
                            save_results: bool = True, show_details: bool = True) -> Dict:
        """
        Run complete API test on top N artists.
        
        Args:
            top_n: Number of top artists to test
            min_plays: Minimum plays to include artist
            save_results: Whether to save detailed results to file
            show_details: Whether to show detailed per-artist results
            
        Returns:
            Summary statistics dictionary
        """
        print(f"🚀 Starting Complete API Integration Test")
        print(f"   Testing top {top_n} artists (min {min_plays} plays)")
        print(f"   APIs: Last.fm + Spotify")
        print("=" * 70)
        
        # Load top artists from user data
        try:
            top_artists = self.load_user_top_artists(top_n, min_plays)
        except Exception as e:
            print(f"❌ Cannot load user data: {e}")
            return {}
        
        if not top_artists:
            print("❌ No artists found in dataset")
            return {}
        
        print(f"\n🎵 Testing {len(top_artists)} artists...")
        print(f"   Sample artists: {', '.join([name for name, _ in top_artists[:5]])}")
        
        # Test each artist
        self.test_results = []
        
        for i, (artist_name, play_count) in enumerate(top_artists, 1):
            print(f"\n{i:2d}/{len(top_artists)}: {artist_name} ({play_count} plays)")
            
            result = self.test_complete_artist_data(artist_name, play_count)
            self.test_results.append(result)
            
            # Print immediate feedback
            if result['overall_success']:
                print(f"   ✅ SUCCESS - APIs working: {', '.join(result['apis_working'])}")
                
                if show_details:
                    # Last.fm details
                    if result['lastfm_success']:
                        listeners = f"{result['lastfm_listeners']:,}" if result['lastfm_listeners'] else "N/A"
                        similar_count = result['lastfm_similar_count']
                        print(f"      🎧 Last.fm: {listeners} listeners, {similar_count} similar artists")
                        
                        if result['lastfm_top_similar']:
                            top_similar = result['lastfm_top_similar'][0]['name']
                            match_score = result['lastfm_top_similar'][0]['match']
                            print(f"               Most similar: {top_similar} ({match_score:.1f}% match)")
                        
                        if result['lastfm_matched_variant'] and result['lastfm_matched_variant'] != artist_name:
                            print(f"               Resolved as: '{result['lastfm_matched_variant']}'")
                    
                    # Spotify details
                    if result['spotify_success']:
                        followers = f"{result['spotify_followers']:,}" if result['spotify_followers'] else "N/A"
                        popularity = f"{result['spotify_popularity']}/100" if result['spotify_popularity'] else "N/A"
                        print(f"      🎵 Spotify: {followers} followers, {popularity} popularity")
                        
                        if result['spotify_genres']:
                            genres = ', '.join(result['spotify_genres'][:3])
                            if len(result['spotify_genres']) > 3:
                                genres += f" (+{len(result['spotify_genres'])-3} more)"
                            print(f"                Genres: {genres}")
                        
                        if result['spotify_canonical_name'] != artist_name:
                            print(f"                Canonical: '{result['spotify_canonical_name']}'")
            else:
                print(f"   ❌ FAILED - No API data available")
                if result['apis_failed']:
                    print(f"      Failed APIs: {', '.join(result['apis_failed'])}")
                if result['lastfm_error']:
                    print(f"      Last.fm error: {result['lastfm_error']}")
                if result['spotify_error']:
                    print(f"      Spotify error: {result['spotify_error']}")
            
            # Timing info
            time_str = f"Total: {result['total_time']:.2f}s"
            if show_details and result['overall_success']:
                time_str += f" (Last.fm: {result['lastfm_time']:.2f}s, Spotify: {result['spotify_time']:.2f}s)"
            print(f"   ⏱️  {time_str}")
        
        # Calculate summary statistics
        self.summary_stats = self.calculate_complete_summary()
        
        # Save results if requested
        if save_results:
            self.save_complete_results()
        
        # Print summary
        self.print_complete_summary()
        
        return self.summary_stats
    
    def calculate_complete_summary(self) -> Dict:
        """Calculate comprehensive summary statistics for both APIs."""
        total_tests = len(self.test_results)
        if total_tests == 0:
            return {}
        
        # Overall success metrics
        overall_successful = [r for r in self.test_results if r['overall_success']]
        overall_failed = [r for r in self.test_results if not r['overall_success']]
        
        # API-specific success metrics
        lastfm_successful = [r for r in self.test_results if r['lastfm_success']]
        spotify_successful = [r for r in self.test_results if r['spotify_success']]
        both_successful = [r for r in self.test_results if r['lastfm_success'] and r['spotify_success']]
        
        # Performance metrics
        avg_total_time = sum(r['total_time'] for r in self.test_results) / total_tests
        avg_lastfm_time = sum(r['lastfm_time'] for r in self.test_results) / total_tests
        avg_spotify_time = sum(r['spotify_time'] for r in self.test_results) / total_tests
        
        # Data quality metrics
        lastfm_with_listeners = [r for r in lastfm_successful if r['lastfm_listeners'] > 0]
        spotify_with_followers = [r for r in spotify_successful if r['spotify_followers'] > 0]
        spotify_with_popularity = [r for r in spotify_successful if r['spotify_popularity'] > 0]
        
        # Similarity data
        similar_data_available = [r for r in lastfm_successful if r['lastfm_similar_count'] > 0]
        
        return {
            'test_overview': {
                'total_artists_tested': total_tests,
                'test_timestamp': datetime.now().isoformat()
            },
            'overall_success': {
                'successful_artists': len(overall_successful),
                'failed_artists': len(overall_failed),
                'success_rate_percent': (len(overall_successful) / total_tests) * 100
            },
            'api_specific_success': {
                'lastfm_success_count': len(lastfm_successful),
                'lastfm_success_rate': (len(lastfm_successful) / total_tests) * 100,
                'spotify_success_count': len(spotify_successful),
                'spotify_success_rate': (len(spotify_successful) / total_tests) * 100,
                'both_apis_success_count': len(both_successful),
                'both_apis_success_rate': (len(both_successful) / total_tests) * 100
            },
            'performance_metrics': {
                'average_total_time_seconds': avg_total_time,
                'average_lastfm_time_seconds': avg_lastfm_time,
                'average_spotify_time_seconds': avg_spotify_time,
                'total_test_time_seconds': sum(r['total_time'] for r in self.test_results)
            },
            'data_quality': {
                'lastfm_listeners_data': {
                    'artists_with_listener_counts': len(lastfm_with_listeners),
                    'avg_listeners': sum(r['lastfm_listeners'] for r in lastfm_with_listeners) / len(lastfm_with_listeners) if lastfm_with_listeners else 0,
                    'max_listeners': max((r['lastfm_listeners'] for r in lastfm_with_listeners), default=0),
                    'min_listeners': min((r['lastfm_listeners'] for r in lastfm_with_listeners), default=0)
                },
                'spotify_followers_data': {
                    'artists_with_follower_counts': len(spotify_with_followers),
                    'avg_followers': sum(r['spotify_followers'] for r in spotify_with_followers) / len(spotify_with_followers) if spotify_with_followers else 0,
                    'max_followers': max((r['spotify_followers'] for r in spotify_with_followers), default=0),
                    'min_followers': min((r['spotify_followers'] for r in spotify_with_followers), default=0)
                },
                'spotify_popularity_data': {
                    'artists_with_popularity': len(spotify_with_popularity),
                    'avg_popularity': sum(r['spotify_popularity'] for r in spotify_with_popularity) / len(spotify_with_popularity) if spotify_with_popularity else 0,
                    'max_popularity': max((r['spotify_popularity'] for r in spotify_with_popularity), default=0),
                    'min_popularity': min((r['spotify_popularity'] for r in spotify_with_popularity), default=0)
                },
                'similarity_data': {
                    'artists_with_similar_data': len(similar_data_available),
                    'avg_similar_artists_count': sum(r['lastfm_similar_count'] for r in similar_data_available) / len(similar_data_available) if similar_data_available else 0
                }
            },
            'failed_artists': [r['artist_name'] for r in overall_failed],
            'top_performers': {
                'highest_lastfm_listeners': sorted([
                    {'artist': r['artist_name'], 'listeners': r['lastfm_listeners']}
                    for r in lastfm_with_listeners
                ], key=lambda x: x['listeners'], reverse=True)[:5],
                'highest_spotify_followers': sorted([
                    {'artist': r['artist_name'], 'followers': r['spotify_followers']}
                    for r in spotify_with_followers
                ], key=lambda x: x['followers'], reverse=True)[:5],
                'highest_spotify_popularity': sorted([
                    {'artist': r['artist_name'], 'popularity': r['spotify_popularity']}
                    for r in spotify_with_popularity
                ], key=lambda x: x['popularity'], reverse=True)[:5]
            }
        }
    
    def print_complete_summary(self):
        """Print comprehensive test summary for both APIs."""
        stats = self.summary_stats
        if not stats:
            return
        
        print("\n" + "=" * 70)
        print("📊 COMPLETE API INTEGRATION TEST SUMMARY")
        print("=" * 70)
        
        # Overall results
        overall = stats['overall_success']
        print(f"Overall Success Rate: {overall['successful_artists']}/{stats['test_overview']['total_artists_tested']} ({overall['success_rate_percent']:.1f}%)")
        
        # API-specific results
        api_stats = stats['api_specific_success']
        print(f"\n🔌 API Success Rates:")
        print(f"   Last.fm:  {api_stats['lastfm_success_count']}/{stats['test_overview']['total_artists_tested']} ({api_stats['lastfm_success_rate']:.1f}%)")
        print(f"   Spotify:  {api_stats['spotify_success_count']}/{stats['test_overview']['total_artists_tested']} ({api_stats['spotify_success_rate']:.1f}%)")
        print(f"   Both APIs: {api_stats['both_apis_success_count']}/{stats['test_overview']['total_artists_tested']} ({api_stats['both_apis_success_rate']:.1f}%)")
        
        # Performance metrics
        perf = stats['performance_metrics']
        print(f"\n⏱️  Performance:")
        print(f"   Average total time: {perf['average_total_time_seconds']:.2f}s per artist")
        print(f"   Last.fm avg time:   {perf['average_lastfm_time_seconds']:.2f}s per artist")
        print(f"   Spotify avg time:   {perf['average_spotify_time_seconds']:.2f}s per artist")
        print(f"   Total test time:    {perf['total_test_time_seconds']:.1f}s")
        
        # Data quality
        quality = stats['data_quality']
        print(f"\n📈 Data Quality:")
        
        # Last.fm data
        lastfm_listeners = quality['lastfm_listeners_data']
        if lastfm_listeners['artists_with_listener_counts'] > 0:
            print(f"   Last.fm Listeners: {lastfm_listeners['artists_with_listener_counts']} artists")
            print(f"      Range: {lastfm_listeners['min_listeners']:,} - {lastfm_listeners['max_listeners']:,}")
            print(f"      Average: {lastfm_listeners['avg_listeners']:,.0f}")
        
        # Spotify data
        spotify_followers = quality['spotify_followers_data']
        if spotify_followers['artists_with_follower_counts'] > 0:
            print(f"   Spotify Followers: {spotify_followers['artists_with_follower_counts']} artists")
            print(f"      Range: {spotify_followers['min_followers']:,} - {spotify_followers['max_followers']:,}")
            print(f"      Average: {spotify_followers['avg_followers']:,.0f}")
        
        spotify_popularity = quality['spotify_popularity_data']
        if spotify_popularity['artists_with_popularity'] > 0:
            print(f"   Spotify Popularity: {spotify_popularity['artists_with_popularity']} artists")
            print(f"      Range: {spotify_popularity['min_popularity']}/100 - {spotify_popularity['max_popularity']}/100")
            print(f"      Average: {spotify_popularity['avg_popularity']:.1f}/100")
        
        # Similarity data
        similarity = quality['similarity_data']
        if similarity['artists_with_similar_data'] > 0:
            print(f"   Similar Artists: {similarity['artists_with_similar_data']} artists have similarity data")
            print(f"      Average: {similarity['avg_similar_artists_count']:.1f} similar artists per artist")
        
        # Top performers
        top_perf = stats['top_performers']
        print(f"\n🏆 Top Performers:")
        
        if top_perf['highest_lastfm_listeners']:
            print(f"   Highest Last.fm Listeners:")
            for item in top_perf['highest_lastfm_listeners'][:3]:
                print(f"      • {item['artist']}: {item['listeners']:,} listeners")
        
        if top_perf['highest_spotify_followers']:
            print(f"   Highest Spotify Followers:")
            for item in top_perf['highest_spotify_followers'][:3]:
                print(f"      • {item['artist']}: {item['followers']:,} followers")
        
        if top_perf['highest_spotify_popularity']:
            print(f"   Highest Spotify Popularity:")
            for item in top_perf['highest_spotify_popularity'][:3]:
                print(f"      • {item['artist']}: {item['popularity']}/100 popularity")
        
        # Failed artists
        if stats['failed_artists']:
            print(f"\n❌ Failed Artists ({len(stats['failed_artists'])}):")
            for artist in stats['failed_artists'][:5]:
                print(f"   • {artist}")
            if len(stats['failed_artists']) > 5:
                print(f"   ... and {len(stats['failed_artists']) - 5} more")
        
        # System health assessment
        print(f"\n🏥 System Health:")
        if overall['success_rate_percent'] >= 90:
            print(f"   🟢 EXCELLENT: {overall['success_rate_percent']:.1f}% overall success rate")
        elif overall['success_rate_percent'] >= 75:
            print(f"   🟡 GOOD: {overall['success_rate_percent']:.1f}% overall success rate")
        else:
            print(f"   🔴 NEEDS ATTENTION: {overall['success_rate_percent']:.1f}% overall success rate")
        
        if api_stats['both_apis_success_rate'] >= 70:
            print(f"   🔗 GREAT API INTEGRATION: {api_stats['both_apis_success_rate']:.1f}% of artists have data from both APIs")
        elif api_stats['both_apis_success_rate'] >= 50:
            print(f"   🔗 GOOD API INTEGRATION: {api_stats['both_apis_success_rate']:.1f}% of artists have data from both APIs")
        else:
            print(f"   🔗 LIMITED API INTEGRATION: {api_stats['both_apis_success_rate']:.1f}% of artists have data from both APIs")
    
    def save_complete_results(self):
        """Save complete test results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"complete_api_test_results_{timestamp}.json"
        
        output_data = {
            'summary_stats': self.summary_stats,
            'detailed_results': self.test_results,
            'test_config': {
                'total_tested': len(self.test_results),
                'test_timestamp': timestamp,
                'apis_tested': ['Last.fm', 'Spotify'],
                'lastfm_configured': bool(self.lastfm_config['api_key'])
            }
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 Complete results saved: {filename}")
            print(f"   Contains detailed Last.fm + Spotify data for all tested artists")
            
        except Exception as e:
            print(f"⚠️  Failed to save results: {e}")

def run_interactive_complete_test():
    """Interactive test runner for complete API integration."""
    print("🎯 COMPLETE API INTEGRATION TEST SUITE")
    print("=" * 60)
    print("Tests both Last.fm AND Spotify APIs on your top artists")
    print("Shows: listeners, followers, popularity, similarity data")
    print()
    
    try:
        top_n = int(input("Number of top artists to test (default 15): ") or "15")
        min_plays = int(input("Minimum plays required (default 5): ") or "5")
        show_details = input("Show detailed per-artist results? (Y/n): ").lower() != 'n'
        save_results = input("Save detailed results to file? (Y/n): ").lower() != 'n'
        
        print(f"\n🔧 Configuration:")
        print(f"   Top artists: {top_n}")
        print(f"   Minimum plays: {min_plays}")
        print(f"   Show details: {show_details}")
        print(f"   Save results: {save_results}")
        
        confirm = input("\nProceed with complete API test? (Y/n): ")
        if confirm.lower().startswith('n'):
            print("Test cancelled.")
            return
        
    except (ValueError, KeyboardInterrupt):
        print("\nTest cancelled.")
        return
    
    # Run test
    try:
        suite = CompleteAPITestSuite()
        stats = suite.run_complete_api_test(top_n, min_plays, save_results, show_details)
        
        if stats:
            print(f"\n🎉 Complete API test finished!")
            print(f"🎵 Ready for network visualization with rich artist data!")
            return stats
        else:
            print(f"\n❌ Test failed - see errors above")
            return None
            
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        print(f"💡 Check your API credentials and data configuration")
        return None

if __name__ == "__main__":
    run_interactive_complete_test()