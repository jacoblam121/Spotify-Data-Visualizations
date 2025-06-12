#!/usr/bin/env python3
"""
Comprehensive Top Artists Test Suite
Tests artist fetching across the user's actual top X artists from their dataset.
Configurable and provides detailed analytics on success rates and performance.
"""

import os
import time
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from lastfm_utils import LastfmAPI
from config_loader import AppConfig
from data_processor import clean_and_filter_data

class TopArtistsTestSuite:
    """Comprehensive test suite for top artists in user's dataset."""
    
    def __init__(self, config_file: str = 'configurations.txt'):
        """Initialize the test suite."""
        load_dotenv()
        self.config = AppConfig(config_file)
        self.lastfm_config = self.config.get_lastfm_config()
        
        # Check API credentials
        if not self.lastfm_config['api_key']:
            raise ValueError("No Last.fm API key found. Add to .env or configurations.txt")
        
        # Initialize API
        self.api = LastfmAPI(
            self.lastfm_config['api_key'],
            self.lastfm_config['api_secret'], 
            self.lastfm_config['cache_dir']
        )
        
        self.test_results = []
        self.summary_stats = {}
    
    def load_user_top_artists(self, top_n: int = 50, min_plays: int = 5) -> List[Tuple[str, int]]:
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
    
    def test_artist_resolution(self, artist_name: str, play_count: int) -> Dict:
        """
        Test resolution for a single artist.
        
        Args:
            artist_name: Artist name to test
            play_count: Play count from user's data
            
        Returns:
            Test result dictionary
        """
        result = {
            'artist_name': artist_name,
            'user_play_count': play_count,
            'start_time': time.time(),
            'success': False,
            'similar_artists_count': 0,
            'artist_info_success': False,
            'canonical_name': None,
            'lastfm_listeners': 0,
            'matched_variant': None,
            'resolution_method': None,
            'time_taken': 0,
            'error_message': None,
            'similar_artists': [],
            'top_similar': None
        }
        
        try:
            # Test similar artists
            similar_artists = self.api.get_similar_artists(artist_name, limit=10)
            
            if similar_artists:
                result['success'] = True
                result['similar_artists_count'] = len(similar_artists)
                result['similar_artists'] = similar_artists
                result['top_similar'] = similar_artists[0]['name'] if similar_artists else None
                
                # Check for resolution metadata
                if similar_artists and '_matched_variant' in similar_artists[0]:
                    result['matched_variant'] = similar_artists[0]['_matched_variant']
                    result['resolution_method'] = similar_artists[0].get('_resolution_method', 'unknown')
            
            # Test artist info
            artist_info = self.api.get_artist_info(artist_name)
            
            if artist_info:
                result['artist_info_success'] = True
                result['canonical_name'] = artist_info.get('name', artist_name)
                result['lastfm_listeners'] = artist_info.get('listeners', 0)
                
                # Update metadata from artist info if available
                if '_matched_variant' in artist_info:
                    result['matched_variant'] = artist_info['_matched_variant']
                    result['resolution_method'] = artist_info.get('_resolution_method', 'unknown')
            
            # Overall success if either worked
            result['success'] = bool(similar_artists or artist_info)
            
        except Exception as e:
            result['error_message'] = str(e)
        
        finally:
            result['time_taken'] = time.time() - result['start_time']
        
        return result
    
    def run_comprehensive_test(self, top_n: int = 50, min_plays: int = 5, 
                             save_results: bool = True) -> Dict:
        """
        Run comprehensive test on top N artists.
        
        Args:
            top_n: Number of top artists to test
            min_plays: Minimum plays to include artist
            save_results: Whether to save detailed results to file
            
        Returns:
            Summary statistics dictionary
        """
        print(f"🚀 Starting Comprehensive Top Artists Test")
        print(f"   Testing top {top_n} artists (min {min_plays} plays)")
        print("=" * 60)
        
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
            print(f"\n{i}/{len(top_artists)}: {artist_name} ({play_count} plays)")
            
            result = self.test_artist_resolution(artist_name, play_count)
            self.test_results.append(result)
            
            # Print immediate feedback
            if result['success']:
                status = "✅"
                details = f"{result['canonical_name']} ({result['lastfm_listeners']:,} listeners)"
                if result['similar_artists_count'] > 0:
                    details += f", {result['similar_artists_count']} similar"
            else:
                status = "❌"
                details = result['error_message'] or "No results found"
            
            time_str = f"{result['time_taken']:.2f}s"
            print(f"   {status} {details} ({time_str})")
            
            # Show resolution method if available
            if result['resolution_method']:
                print(f"      Method: {result['resolution_method']}")
            if result['matched_variant'] and result['matched_variant'] != artist_name:
                print(f"      Variant: '{result['matched_variant']}'")
        
        # Calculate summary statistics
        self.summary_stats = self.calculate_summary_stats()
        
        # Save results if requested
        if save_results:
            self.save_detailed_results()
        
        # Print summary
        self.print_summary()
        
        return self.summary_stats
    
    def calculate_summary_stats(self) -> Dict:
        """Calculate comprehensive summary statistics."""
        total_tests = len(self.test_results)
        if total_tests == 0:
            return {}
        
        successful_tests = [r for r in self.test_results if r['success']]
        failed_tests = [r for r in self.test_results if not r['success']]
        
        # Basic stats
        success_rate = (len(successful_tests) / total_tests) * 100
        avg_time = sum(r['time_taken'] for r in self.test_results) / total_tests
        
        # Performance stats
        times = [r['time_taken'] for r in self.test_results]
        min_time = min(times)
        max_time = max(times)
        
        # Resolution method breakdown
        resolution_methods = {}
        for result in successful_tests:
            method = result.get('resolution_method', 'unknown')
            resolution_methods[method] = resolution_methods.get(method, 0) + 1
        
        # Listener count analysis for successful tests
        listener_counts = [r['lastfm_listeners'] for r in successful_tests if r['lastfm_listeners'] > 0]
        
        # Play count vs success correlation
        high_play_artists = [r for r in self.test_results if r['user_play_count'] >= 10]
        low_play_artists = [r for r in self.test_results if r['user_play_count'] < 10]
        
        high_play_success = sum(1 for r in high_play_artists if r['success']) / len(high_play_artists) * 100 if high_play_artists else 0
        low_play_success = sum(1 for r in low_play_artists if r['success']) / len(low_play_artists) * 100 if low_play_artists else 0
        
        return {
            'total_artists_tested': total_tests,
            'successful_resolutions': len(successful_tests),
            'failed_resolutions': len(failed_tests),
            'success_rate_percent': success_rate,
            'average_time_seconds': avg_time,
            'min_time_seconds': min_time,
            'max_time_seconds': max_time,
            'resolution_methods': resolution_methods,
            'listener_count_stats': {
                'total_with_listeners': len(listener_counts),
                'avg_listeners': sum(listener_counts) / len(listener_counts) if listener_counts else 0,
                'min_listeners': min(listener_counts) if listener_counts else 0,
                'max_listeners': max(listener_counts) if listener_counts else 0
            },
            'play_count_correlation': {
                'high_play_count_success_rate': high_play_success,
                'low_play_count_success_rate': low_play_success,
                'high_play_count_artists': len(high_play_artists),
                'low_play_count_artists': len(low_play_artists)
            },
            'failed_artists': [r['artist_name'] for r in failed_tests],
            'test_timestamp': datetime.now().isoformat()
        }
    
    def print_summary(self):
        """Print comprehensive test summary."""
        stats = self.summary_stats
        if not stats:
            return
        
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        # Overall results
        print(f"Overall Success Rate: {stats['successful_resolutions']}/{stats['total_artists_tested']} ({stats['success_rate_percent']:.1f}%)")
        print(f"Average Resolution Time: {stats['average_time_seconds']:.2f}s")
        print(f"Time Range: {stats['min_time_seconds']:.2f}s - {stats['max_time_seconds']:.2f}s")
        
        # Resolution methods
        if stats['resolution_methods']:
            print(f"\n🔧 Resolution Methods:")
            for method, count in stats['resolution_methods'].items():
                percentage = (count / stats['successful_resolutions']) * 100
                print(f"   {method}: {count} ({percentage:.1f}%)")
        
        # Listener statistics
        listener_stats = stats['listener_count_stats']
        if listener_stats['total_with_listeners'] > 0:
            print(f"\n👥 Last.fm Listener Statistics:")
            print(f"   Artists with listener data: {listener_stats['total_with_listeners']}")
            print(f"   Average listeners: {listener_stats['avg_listeners']:,.0f}")
            print(f"   Range: {listener_stats['min_listeners']:,} - {listener_stats['max_listeners']:,}")
        
        # Play count correlation
        corr = stats['play_count_correlation']
        print(f"\n📈 Play Count vs Success Rate:")
        print(f"   High play count (≥10): {corr['high_play_count_success_rate']:.1f}% ({corr['high_play_count_artists']} artists)")
        print(f"   Low play count (<10): {corr['low_play_count_success_rate']:.1f}% ({corr['low_play_count_artists']} artists)")
        
        # Failed artists
        if stats['failed_artists']:
            print(f"\n❌ Failed Artists ({len(stats['failed_artists'])}):")
            for artist in stats['failed_artists'][:10]:  # Show first 10
                print(f"   • {artist}")
            if len(stats['failed_artists']) > 10:
                print(f"   ... and {len(stats['failed_artists']) - 10} more")
        
        # Health assessment
        print(f"\n🏥 System Health Assessment:")
        if stats['success_rate_percent'] >= 90:
            print(f"   🟢 EXCELLENT: {stats['success_rate_percent']:.1f}% success rate")
        elif stats['success_rate_percent'] >= 75:
            print(f"   🟡 GOOD: {stats['success_rate_percent']:.1f}% success rate")
        elif stats['success_rate_percent'] >= 50:
            print(f"   🟠 FAIR: {stats['success_rate_percent']:.1f}% success rate - some issues")
        else:
            print(f"   🔴 POOR: {stats['success_rate_percent']:.1f}% success rate - significant issues")
        
        if stats['average_time_seconds'] <= 2:
            print(f"   ⚡ FAST: Average {stats['average_time_seconds']:.2f}s resolution time")
        elif stats['average_time_seconds'] <= 5:
            print(f"   🐌 SLOW: Average {stats['average_time_seconds']:.2f}s resolution time")
        else:
            print(f"   🚨 VERY SLOW: Average {stats['average_time_seconds']:.2f}s resolution time")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if stats['success_rate_percent'] < 80:
            print(f"   • Review failed artists for pattern analysis")
            print(f"   • Consider expanding artist name variants database")
        
        if stats['average_time_seconds'] > 3:
            print(f"   • Consider implementing request caching optimization")
            print(f"   • Review API rate limiting settings")
        
        if corr['low_play_count_success_rate'] < corr['high_play_count_success_rate']:
            print(f"   • Low-play artists have lower success rates (possible obscure artists)")
        
    def save_detailed_results(self):
        """Save detailed test results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"top_artists_test_results_{timestamp}.json"
        
        output_data = {
            'summary_stats': self.summary_stats,
            'detailed_results': self.test_results,
            'test_config': {
                'total_tested': len(self.test_results),
                'test_timestamp': timestamp,
                'lastfm_api_configured': bool(self.lastfm_config['api_key'])
            }
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 Detailed results saved: {filename}")
            print(f"   Use this file to analyze patterns in failed artists")
            
        except Exception as e:
            print(f"⚠️  Failed to save results: {e}")

def run_interactive_test():
    """Interactive test runner with configurable options."""
    print("🎯 COMPREHENSIVE TOP ARTISTS TEST SUITE")
    print("=" * 50)
    print("This will test Last.fm artist resolution on your actual top artists")
    print()
    
    # Configuration options
    try:
        top_n = int(input("Number of top artists to test (default 25): ") or "25")
        min_plays = int(input("Minimum plays required (default 5): ") or "5")
        save_results = input("Save detailed results to file? (y/N): ").lower().startswith('y')
        
        print(f"\n🔧 Configuration:")
        print(f"   Top artists: {top_n}")
        print(f"   Minimum plays: {min_plays}")
        print(f"   Save results: {save_results}")
        
        confirm = input("\nProceed with test? (Y/n): ")
        if confirm.lower().startswith('n'):
            print("Test cancelled.")
            return
        
    except (ValueError, KeyboardInterrupt):
        print("\nTest cancelled.")
        return
    
    # Run test
    try:
        suite = TopArtistsTestSuite()
        stats = suite.run_comprehensive_test(top_n, min_plays, save_results)
        
        if stats:
            print(f"\n🎉 Test completed successfully!")
            return stats
        else:
            print(f"\n❌ Test failed - see errors above")
            return None
            
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        print(f"💡 Check your data configuration and API credentials")
        return None

if __name__ == "__main__":
    run_interactive_test()