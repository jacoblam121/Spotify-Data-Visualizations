#!/usr/bin/env python3
"""
Comprehensive Manual Test Suite for Phase A.2 Artist Verification
================================================================
Interactive test suite for validating all verification scenarios and edge cases.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from artist_verification import ArtistVerifier, TrackMatchEvidence
from lastfm_utils import LastfmAPI
from config_loader import AppConfig

class TestConfig:
    """Configuration class for test suite parameters."""
    
    def __init__(self):
        # Data source configuration
        self.data_path = "lastfm_data.csv"
        self.force_data_source = None  # 'lastfm' or 'spotify' to override detection
        
        # Performance test configuration
        self.performance_iterations = 5
        self.max_verification_time = 0.5  # seconds
        self.max_batch_time_per_artist = 1.0  # seconds
        
        # Confidence threshold configuration
        self.mbid_min_confidence = 0.95
        self.track_strong_min_confidence = 0.85
        self.heuristic_improvement_threshold = 0.75
        
        # Test scope configuration
        self.max_candidates_per_test = 5
        self.performance_test_artists = 10
        self.edge_case_long_name_length = 500
        self.edge_case_timeout = 5.0  # seconds
        
        # API configuration
        self.api_timeout = 10.0  # seconds
        self.max_api_retries = 3
        self.use_api_for_real_tests = True
        
        # Test selection configuration
        self.skip_slow_tests = False
        self.skip_api_tests = False
        self.skip_performance_tests = False
        self.verbose_output = True
        self.detailed_track_analysis = True
        
        # Quality thresholds
        self.min_pass_rate = 75.0  # percentage
        self.max_failed_tests = 5
        self.expected_mbid_coverage = 10.0  # percentage of artists with MBIDs
        
        # Test artist configuration
        self.problematic_artists = ["*LUNA", "YOASOBI", "IVE", "BTS", "Taylor Swift"]
        self.unicode_test_artists = ["*LUNA", "YOASOBI", "방탄소년단"]
        self.performance_test_sample_size = 10
        
        # Output configuration
        self.save_results = True
        self.results_file = "test_results_a2.json"
        self.show_progress = True
        self.colorized_output = True

class ComprehensiveTestSuite:
    """Comprehensive test suite for artist verification system."""
    
    def __init__(self, config: Optional[TestConfig] = None):
        """Initialize test suite with configuration."""
        self.config = config or TestConfig()
        
        print("🧪 Phase A.2 Comprehensive Manual Test Suite")
        print("=" * 55)
        self._print_config()
        
        # Initialize verifier with configured data path
        self.verifier = ArtistVerifier(self.config.data_path)
        
        # Initialize Last.fm API based on configuration
        if self.config.skip_api_tests or not self.config.use_api_for_real_tests:
            self.lastfm_api = None
            print("⚠️  API tests disabled - will use mock data")
        else:
            try:
                app_config = AppConfig()
                lastfm_config = app_config.get_lastfm_config()
                
                if lastfm_config['enabled'] and lastfm_config['api_key']:
                    self.lastfm_api = LastfmAPI(
                        lastfm_config['api_key'],
                        lastfm_config['api_secret'],
                        lastfm_config['cache_dir']
                    )
                    print("✅ Last.fm API initialized")
                else:
                    self.lastfm_api = None
                    print("⚠️  Last.fm API not available - will use mock data")
                    
            except Exception as e:
                self.lastfm_api = None
                print(f"⚠️  Could not initialize Last.fm API: {e}")
        
        # Test results tracking
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
    
    def _print_config(self):
        """Print current test configuration."""
        if not self.config.verbose_output:
            return
            
        print(f"📋 Test Configuration:")
        print(f"   Data Source: {self.config.data_path}")
        print(f"   API Tests: {'Enabled' if self.config.use_api_for_real_tests and not self.config.skip_api_tests else 'Disabled'}")
        print(f"   Performance Tests: {'Enabled' if not self.config.skip_performance_tests else 'Disabled'}")
        print(f"   Slow Tests: {'Enabled' if not self.config.skip_slow_tests else 'Disabled'}")
        print(f"   MBID Confidence Threshold: {self.config.mbid_min_confidence}")
        print(f"   Track Confidence Threshold: {self.config.track_strong_min_confidence}")
        print(f"   Expected Pass Rate: {self.config.min_pass_rate}%")
        print()
    
    def run_all_tests(self):
        """Run all test categories."""
        print(f"\n🚀 Starting Comprehensive Test Suite")
        print("=" * 50)
        
        test_categories = [
            ("MBID Matching Tests", self.test_mbid_matching),
            ("Track Matching Tests", self.test_track_matching),
            ("Unicode & International Tests", self.test_unicode_handling),
            ("Edge Case Tests", self.test_edge_cases),
            ("Performance Tests", self.test_performance),
            ("Data Source Tests", self.test_data_sources),
            ("Confidence Threshold Tests", self.test_confidence_thresholds),
            ("Case-Insensitive Matching Tests", self.test_case_insensitive_matching),
            ("Real Artist Tests", self.test_real_problematic_artists)
        ]
        
        for category_name, test_func in test_categories:
            print(f"\n{'='*60}")
            print(f"📋 {category_name}")
            print('='*60)
            
            try:
                test_func()
            except KeyboardInterrupt:
                print("\n⏹️  Test suite interrupted by user")
                break
            except Exception as e:
                print(f"❌ Test category failed: {e}")
                self.test_results['failed'] += 1
        
        self.show_final_results()
    
    def test_mbid_matching(self):
        """Test MBID matching functionality."""
        print("🔍 Testing MBID Matching System")
        
        # Test Case 1: Perfect MBID Match
        print("\n📝 Test 1: Perfect MBID Match")
        if "*LUNA" in self.verifier.user_artist_mbids:
            user_mbid = self.verifier.user_artist_mbids["*LUNA"]
            print(f"   User MBID for *LUNA: {user_mbid}")
            
            test_candidates = [
                {
                    'name': '*LUNA Perfect Match',
                    'listeners': 17154,
                    'mbid': user_mbid,  # Exact match
                    'url': 'test'
                },
                {
                    'name': '*LUNA No MBID',
                    'listeners': 17154,
                    'mbid': '',  # No MBID
                    'url': 'test'
                }
            ]
            
            result = self.verifier.verify_artist_candidates("*LUNA", test_candidates)
            expected_method = "MBID_MATCH"
            expected_confidence_min = 0.95
            
            self.assert_test(
                "Perfect MBID Match",
                result.verification_method == expected_method and result.confidence_score >= expected_confidence_min,
                f"Expected {expected_method} with >{expected_confidence_min} confidence, got {result.verification_method} with {result.confidence_score:.3f}"
            )
        else:
            print("   ⚠️  *LUNA not found in user data - skipping MBID test")
            self.test_results['skipped'] += 1
        
        # Test Case 2: No MBID Match (fallback behavior)
        print("\n📝 Test 2: No MBID Match - Proper Fallback")
        test_candidates = [
            {
                'name': 'Artist Without MBID',
                'listeners': 100000,
                'mbid': '',  # No MBID
                'url': 'test'
            }
        ]
        
        # Pick any artist from user data
        test_artist = list(self.verifier.user_tracks_by_artist.keys())[0]
        result = self.verifier.verify_artist_candidates(test_artist, test_candidates)
        
        self.assert_test(
            "No MBID Fallback",
            result.verification_method != "MBID_MATCH",
            f"Should fall back from MBID matching, but got {result.verification_method}"
        )
        
        # Test Case 3: Wrong MBID (should not match)
        print("\n📝 Test 3: Wrong MBID - Should Not Match")
        if "*LUNA" in self.verifier.user_artist_mbids:
            test_candidates = [
                {
                    'name': '*LUNA Wrong MBID',
                    'listeners': 17154,
                    'mbid': 'wrong-mbid-12345',  # Wrong MBID
                    'url': 'test'
                }
            ]
            
            result = self.verifier.verify_artist_candidates("*LUNA", test_candidates)
            
            self.assert_test(
                "Wrong MBID Rejection",
                result.verification_method != "MBID_MATCH",
                f"Should not match wrong MBID, but got {result.verification_method}"
            )
    
    def test_track_matching(self):
        """Test track-based verification."""
        print("🎵 Testing Track Matching System")
        
        # Test Case 1: Perfect Track Matches
        print("\n📝 Test 1: Perfect Track Matches")
        test_artist = "*LUNA"
        if test_artist in self.verifier.user_tracks_by_artist:
            user_tracks = list(self.verifier.user_tracks_by_artist[test_artist])[:3]
            print(f"   User tracks for {test_artist}: {user_tracks}")
            
            # Create candidate with exact track matches
            evidence = self.verifier._gather_track_evidence(test_artist, user_tracks)
            
            self.assert_test(
                "Perfect Track Matches",
                evidence.perfect_match_count >= 1,
                f"Expected perfect matches, got {evidence.perfect_match_count} perfect, {evidence.match_count} total"
            )
            
            print(f"   📊 Evidence: {evidence.perfect_match_count} perfect, {evidence.strong_match_count} strong, {evidence.match_count} total")
        
        # Test Case 2: Similar Track Matches (with variations)
        print("\n📝 Test 2: Similar Track Matches")
        similar_tracks = [
            "アトラクトライト (Radio Edit)",  # Should match "アトラクトライト"
            "track that won't match",
            "another non-match"
        ]
        
        evidence = self.verifier._gather_track_evidence("*LUNA", similar_tracks)
        confidence = self.verifier._calculate_track_confidence(evidence)
        
        print(f"   📊 Similar track evidence: {evidence.match_count} matches, confidence: {confidence:.3f}")
        
        # Test Case 3: No Track Matches
        print("\n📝 Test 3: No Track Matches")
        no_match_tracks = [
            "completely different song",
            "another unrelated track",
            "third non-matching track"
        ]
        
        evidence = self.verifier._gather_track_evidence("*LUNA", no_match_tracks)
        
        self.assert_test(
            "No Track Matches",
            evidence.match_count == 0,
            f"Expected no matches, got {evidence.match_count}"
        )
    
    def test_unicode_handling(self):
        """Test Unicode and international character handling."""
        print("🌐 Testing Unicode & International Character Handling")
        
        # Test Case 1: Japanese Characters
        print("\n📝 Test 1: Japanese Character Normalization")
        from artist_verification import canonicalize_title
        
        test_cases = [
            ("アトラクトライト", "アトラクトライト", True),  # Exact match
            ("アトラクトライト (Live)", "アトラクトライト", True),  # Should clean metadata
            ("ＡＴＴＲＡＣＴ", "attract", True),  # Full-width to half-width
            ("different song", "アトラクトライト", False)  # No match
        ]
        
        for input_title, target_title, should_match in test_cases:
            canonical_input = canonicalize_title(input_title)
            canonical_target = canonicalize_title(target_title)
            matches = canonical_input == canonical_target
            
            result_desc = "✅ MATCH" if matches else "❌ NO MATCH"
            expected_desc = "should match" if should_match else "should not match"
            
            print(f"   '{input_title}' → '{canonical_input}'")
            print(f"   '{target_title}' → '{canonical_target}'")
            print(f"   Result: {result_desc} ({expected_desc})")
            
            self.assert_test(
                f"Unicode: {input_title} vs {target_title}",
                matches == should_match,
                f"Unicode normalization failed for {input_title}"
            )
        
        # Test Case 2: K-pop Artist Names
        print("\n📝 Test 2: K-pop Artist Name Variations")
        kpop_variations = [
            ("BTS", "bts", True),
            ("방탄소년단", "BTS", False),  # Different scripts shouldn't auto-match
            ("IVE", "ive", True),
            ("아이브", "IVE", False)
        ]
        
        for name1, name2, should_match in kpop_variations:
            canonical1 = canonicalize_title(name1)
            canonical2 = canonicalize_title(name2)
            matches = canonical1 == canonical2
            
            print(f"   '{name1}' ↔ '{name2}': {'✅' if matches else '❌'} ({'expected' if matches == should_match else 'unexpected'})")
    
    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        print("⚠️  Testing Edge Cases & Error Conditions")
        
        # Test Case 1: Empty Data
        print("\n📝 Test 1: Empty Data Handling")
        try:
            result = self.verifier.verify_artist_candidates("NonexistentArtist", [])
            self.test_results['failed'] += 1
            print("   ❌ Should have raised exception for empty candidates")
        except ValueError:
            self.test_results['passed'] += 1
            print("   ✅ Correctly raised exception for empty candidates")
        except Exception as e:
            self.test_results['failed'] += 1
            print(f"   ❌ Unexpected exception: {e}")
        
        # Test Case 2: Malformed Candidates
        print("\n📝 Test 2: Malformed Candidate Data")
        malformed_candidates = [
            {},  # Empty dict
            {'name': 'Only Name'},  # Missing fields
            {'listeners': 'not_a_number', 'name': 'Bad Listeners'},  # Invalid data types
        ]
        
        try:
            result = self.verifier.verify_artist_candidates("TestArtist", malformed_candidates)
            print(f"   ✅ Handled malformed data gracefully: {result.verification_method}")
            self.test_results['passed'] += 1
        except Exception as e:
            print(f"   ❌ Failed to handle malformed data: {e}")
            self.test_results['failed'] += 1
        
        # Test Case 3: Very Long Artist Names
        print("\n📝 Test 3: Extremely Long Artist Names")
        if self.config.skip_slow_tests:
            print("   ⚠️  Skipped (slow tests disabled)")
            self.test_results['skipped'] += 1
        else:
            long_name = "A" * self.config.edge_case_long_name_length
            long_candidates = [
                {'name': long_name, 'listeners': 1000, 'mbid': '', 'url': 'test'}
            ]
            
            try:
                start_time = time.time()
                result = self.verifier.verify_artist_candidates(long_name, long_candidates)
                elapsed_time = time.time() - start_time
                
                print(f"   ✅ Handled long names: {elapsed_time:.3f}s, method: {result.verification_method}")
                print(f"   📊 Threshold: {self.config.edge_case_timeout:.1f}s")
                
                self.assert_test(
                    "Long Name Performance",
                    elapsed_time < self.config.edge_case_timeout,
                    f"Long name processing took {elapsed_time:.3f}s (exceeds {self.config.edge_case_timeout:.1f}s threshold)"
                )
            except Exception as e:
                print(f"   ❌ Failed with long names: {e}")
                self.test_results['failed'] += 1
        
        # Test Case 4: Special Characters in Names
        print("\n📝 Test 4: Special Characters in Names")
        special_names = [
            "*LUNA",  # Asterisk
            "Sigur Rós",  # Accented characters
            "!!!",  # All special chars
            "deadmau5",  # Numbers
            "A$AP Rocky",  # Dollar sign
            "Godspeed You! Black Emperor"  # Punctuation
        ]
        
        for special_name in special_names:
            try:
                candidates = [{'name': special_name, 'listeners': 1000, 'mbid': '', 'url': 'test'}]
                result = self.verifier.verify_artist_candidates(special_name, candidates)
                print(f"   ✅ '{special_name}': {result.verification_method}")
            except Exception as e:
                print(f"   ❌ '{special_name}': {e}")
                self.test_results['failed'] += 1
    
    def test_performance(self):
        """Test performance characteristics."""
        if self.config.skip_performance_tests:
            print("⚡ Performance Tests - SKIPPED (disabled in config)")
            self.test_results['skipped'] += 2
            return
            
        print("⚡ Testing Performance")
        
        # Test Case 1: Single Artist Performance
        print("\n📝 Test 1: Single Artist Verification Speed")
        test_artist = list(self.verifier.user_tracks_by_artist.keys())[0]
        test_candidates = [
            {'name': test_artist, 'listeners': 100000, 'mbid': '', 'url': 'test'},
            {'name': f"{test_artist}_variant", 'listeners': 50000, 'mbid': '', 'url': 'test'}
        ]
        
        times = []
        for i in range(self.config.performance_iterations):
            start_time = time.time()
            result = self.verifier.verify_artist_candidates(test_artist, test_candidates)
            elapsed_time = time.time() - start_time
            times.append(elapsed_time)
            
            if self.config.show_progress and i % 2 == 0:
                print(f"     Iteration {i+1}/{self.config.performance_iterations}: {elapsed_time:.3f}s")
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"   📊 Average time: {avg_time:.3f}s, Max time: {max_time:.3f}s")
        print(f"   📊 Threshold: {self.config.max_verification_time:.3f}s")
        
        self.assert_test(
            "Verification Speed",
            avg_time < self.config.max_verification_time,
            f"Average verification time {avg_time:.3f}s exceeds threshold {self.config.max_verification_time:.3f}s"
        )
        
        # Test Case 2: Batch Performance
        print("\n📝 Test 2: Batch Verification Performance")
        sample_artists = list(self.verifier.user_tracks_by_artist.keys())[:self.config.performance_test_sample_size]
        
        start_time = time.time()
        for i, artist in enumerate(sample_artists):
            candidates = [{'name': artist, 'listeners': 100000, 'mbid': '', 'url': 'test'}]
            result = self.verifier.verify_artist_candidates(artist, candidates)
            
            if self.config.show_progress and i % 3 == 0:
                print(f"     Testing artist {i+1}/{len(sample_artists)}: {artist}")
                
        elapsed_time = time.time() - start_time
        
        avg_per_artist = elapsed_time / len(sample_artists)
        print(f"   📊 Batch performance: {elapsed_time:.3f}s total, {avg_per_artist:.3f}s per artist")
        print(f"   📊 Threshold: {self.config.max_batch_time_per_artist:.3f}s per artist")
        
        self.assert_test(
            "Batch Performance",
            avg_per_artist < self.config.max_batch_time_per_artist,
            f"Batch performance {avg_per_artist:.3f}s per artist exceeds threshold {self.config.max_batch_time_per_artist:.3f}s"
        )
    
    def test_data_sources(self):
        """Test different data source scenarios."""
        print("📊 Testing Data Source Handling")
        
        # Test Case 1: Last.fm vs Spotify Detection
        print("\n📝 Test 1: Data Source Detection")
        
        # Test Last.fm CSV detection
        lastfm_verifier = ArtistVerifier("lastfm_data.csv")
        spotify_verifier = ArtistVerifier("spotify_data.json")  # May not exist, but tests logic
        
        self.assert_test(
            "Last.fm Source Detection",
            lastfm_verifier.data_source == "lastfm",
            f"Expected 'lastfm', got '{lastfm_verifier.data_source}'"
        )
        
        self.assert_test(
            "Spotify Source Detection",
            spotify_verifier.data_source == "spotify",
            f"Expected 'spotify', got '{spotify_verifier.data_source}'"
        )
        
        # Test Case 2: MBID Availability
        print("\n📝 Test 2: MBID Data Availability")
        mbid_count = len(self.verifier.user_artist_mbids)
        total_artists = len(self.verifier.user_tracks_by_artist)
        mbid_coverage = (mbid_count / total_artists) * 100 if total_artists > 0 else 0
        
        print(f"   📊 MBID Coverage: {mbid_count}/{total_artists} artists ({mbid_coverage:.1f}%)")
        
        # Only check MBID data for Last.fm source
        if self.verifier.data_source == 'lastfm':
            self.assert_test(
                "MBID Data Loaded",
                mbid_count > 0,
                "No MBID data found in Last.fm file"
            )
        else:
            print("   ℹ️  MBID test skipped for Spotify data source")
    
    def test_confidence_thresholds(self):
        """Test confidence threshold logic."""
        print("🎯 Testing Confidence Threshold Logic")
        
        # Test Case 1: MBID Confidence
        print("\n📝 Test 1: MBID Match Confidence")
        # Use case-insensitive lookup for MBID
        user_mbid = self.verifier._get_user_mbid_for_artist("*LUNA")
        if user_mbid:
            candidates = [
                {'name': '*LUNA', 'listeners': 17154, 'mbid': user_mbid, 'url': 'test'}
            ]
            
            result = self.verifier.verify_artist_candidates("*LUNA", candidates)
            
            self.assert_test(
                "MBID Confidence Level",
                result.confidence_score >= self.config.mbid_min_confidence and result.verification_method == "MBID_MATCH",
                f"MBID match should have >{self.config.mbid_min_confidence} confidence, got {result.confidence_score:.3f} with {result.verification_method}"
            )
        
        # Test Case 2: Track Evidence Thresholds
        print("\n📝 Test 2: Track Evidence Confidence Thresholds")
        
        # Mock track evidence scenarios
        high_evidence = self.verifier._calculate_track_confidence(
            TrackMatchEvidence(
                total_user_tracks=10,
                match_count=5,
                strong_match_count=0,
                perfect_match_count=5,  # 5 perfect matches
                average_score_of_matches=0.99,
                best_match_score=1.0,
                matched_pairs=[]
            )
        )
        
        medium_evidence = self.verifier._calculate_track_confidence(
            TrackMatchEvidence(
                total_user_tracks=10,
                match_count=3,
                strong_match_count=3,
                perfect_match_count=0,  # No perfect, but good strong matches
                average_score_of_matches=0.92,
                best_match_score=0.95,
                matched_pairs=[]
            )
        )
        
        low_evidence = self.verifier._calculate_track_confidence(
            TrackMatchEvidence(
                total_user_tracks=10,
                match_count=1,
                strong_match_count=0,
                perfect_match_count=0,
                average_score_of_matches=0.7,
                best_match_score=0.7,
                matched_pairs=[]
            )
        )
        
        print(f"   📊 High evidence confidence: {high_evidence:.3f}")
        print(f"   📊 Medium evidence confidence: {medium_evidence:.3f}")
        print(f"   📊 Low evidence confidence: {low_evidence:.3f}")
        
        self.assert_test(
            "High Track Evidence",
            high_evidence >= self.config.track_strong_min_confidence,
            f"High evidence should be >{self.config.track_strong_min_confidence}, got {high_evidence:.3f}"
        )
        
        self.assert_test(
            "Evidence Ranking",
            high_evidence > medium_evidence > low_evidence,
            "Evidence confidence should rank correctly"
        )
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive artist matching."""
        print("🔤 Testing Case-Insensitive Artist Matching")
        
        # Test Case 1: Basic case variations
        print("\n📝 Test 1: Basic Case Variations")
        
        # Find an artist that exists in the data
        test_artist = None
        for artist in list(self.verifier.user_tracks_by_artist.keys())[:5]:
            if artist and len(artist) > 3:  # Skip short names
                test_artist = artist
                break
        
        if test_artist:
            variations = [
                test_artist.upper(),
                test_artist.lower(),
                test_artist.capitalize(),
                test_artist.swapcase()
            ]
            
            original_tracks = self.verifier._get_user_tracks_for_artist(test_artist)
            print(f"   Original '{test_artist}': {len(original_tracks)} tracks")
            
            for variant in variations:
                variant_tracks = self.verifier._get_user_tracks_for_artist(variant)
                matches = variant_tracks == original_tracks
                
                self.assert_test(
                    f"Case variant: {variant}",
                    matches,
                    f"Failed to match '{variant}' to '{test_artist}'"
                )
                
                if matches:
                    print(f"   ✅ '{variant}' matches original")
        
        # Test Case 2: MBID case-insensitive lookup
        print("\n📝 Test 2: MBID Case-Insensitive Lookup")
        
        # Test with *LUNA if available
        mbid_variations = ["*LUNA", "*luna", "*Luna", "*LuNa"]
        mbid_found = None
        
        for variant in mbid_variations:
            mbid = self.verifier._get_user_mbid_for_artist(variant)
            if mbid:
                if mbid_found and mbid != mbid_found:
                    self.assert_test(
                        f"MBID consistency for {variant}",
                        False,
                        f"Different MBIDs returned for case variations"
                    )
                mbid_found = mbid
                print(f"   ✅ '{variant}' → MBID: {mbid[:8]}...")
        
        # Test Case 3: Album case-insensitive lookup
        print("\n📝 Test 3: Album Case-Insensitive Lookup")
        
        if test_artist:
            original_albums = self.verifier._get_user_albums_for_artist(test_artist)
            variant_albums = self.verifier._get_user_albums_for_artist(test_artist.upper())
            
            self.assert_test(
                "Album case-insensitive lookup",
                original_albums == variant_albums,
                "Album lookup should be case-insensitive"
            )
            
            if original_albums:
                print(f"   ✅ Found {len(original_albums)} albums for both cases")
    
    def test_real_problematic_artists(self):
        """Test the original problematic artists."""
        if self.config.skip_api_tests:
            print("🎯 Real Problematic Artists Tests - SKIPPED (API tests disabled)")
            self.test_results['skipped'] += len(self.config.problematic_artists)
            return
            
        print("🎯 Testing Real Problematic Artists")
        
        problematic_artists = self.config.problematic_artists
        
        for artist in problematic_artists:
            print(f"\n📝 Testing: {artist}")
            
            # Use case-insensitive lookup to check if artist exists
            if self.verifier._get_user_tracks_for_artist(artist):
                if self.lastfm_api:
                    try:
                        # Get real candidates from API
                        candidates = self._get_real_candidates(artist)
                        
                        if candidates:
                            result = self.verifier.verify_artist_candidates(artist, candidates, self.lastfm_api)
                            
                            print(f"   📊 Result: {result.verification_method}")
                            print(f"   📊 Confidence: {result.confidence_score:.3f}")
                            
                            chosen_name = result.chosen_profile.get('name', 'Unknown')
                            chosen_listeners = result.chosen_profile.get('listeners', 0)
                            chosen_url = result.chosen_profile.get('url', '')
                            
                            print(f"   📊 Chosen: {chosen_name}")
                            if chosen_listeners > 0:
                                print(f"   👥 Last.fm Listeners: {chosen_listeners:,}")
                            if chosen_url:
                                print(f"   🔗 Last.fm URL: {chosen_url}")
                            
                            # Show MBID if available for verification
                            chosen_mbid = result.chosen_profile.get('mbid', '')
                            if chosen_mbid:
                                print(f"   🔑 MBID: {chosen_mbid}")
                            
                            # Check if improvement over original system
                            improved = (
                                result.confidence_score > self.config.heuristic_improvement_threshold or  # High confidence
                                result.verification_method in ["MBID_MATCH", "STRONG_TRACK_MATCH"]  # Better method
                            )
                            
                            self.assert_test(
                                f"{artist} Improvement",
                                improved,
                                f"Should show improvement for {artist}, got {result.confidence_score:.3f} with {result.verification_method}"
                            )
                        else:
                            print(f"   ⚠️  No candidates found for {artist}")
                            self.test_results['skipped'] += 1
                    except Exception as e:
                        print(f"   ❌ Error testing {artist}: {e}")
                        self.test_results['failed'] += 1
                else:
                    print(f"   ⚠️  No API available - skipping {artist}")
                    self.test_results['skipped'] += 1
            else:
                print(f"   ⚠️  {artist} not found in user data")
                self.test_results['skipped'] += 1
    
    def _get_real_candidates(self, artist: str, max_candidates: int = 5) -> List[Dict]:
        """Get real candidates from Last.fm API."""
        try:
            candidates = []
            
            # Get self info
            self_info = self.lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
            if self_info:
                candidates.append({
                    'name': self_info.get('name', artist),
                    'listeners': int(self_info.get('listeners', 0)),
                    'mbid': self_info.get('mbid', ''),
                    'url': self_info.get('url', '')
                })
            
            # Get similar artists
            similar = self.lastfm_api.get_similar_artists(artist, use_enhanced_matching=True)
            for sim_artist in similar[:max_candidates-1]:
                candidates.append({
                    'name': sim_artist.get('name', ''),
                    'listeners': int(sim_artist.get('_canonical_listeners', 0)),
                    'mbid': sim_artist.get('mbid', ''),
                    'url': sim_artist.get('url', '')
                })
            
            return candidates[:max_candidates]
            
        except Exception as e:
            print(f"   ❌ Error getting candidates: {e}")
            return []
    
    def assert_test(self, test_name: str, condition: bool, error_message: str):
        """Assert a test condition and record results."""
        if condition:
            print(f"   ✅ {test_name}")
            self.test_results['passed'] += 1
        else:
            print(f"   ❌ {test_name}: {error_message}")
            self.test_results['failed'] += 1
        
        self.test_results['details'].append({
            'test': test_name,
            'passed': condition,
            'error': error_message if not condition else None
        })
    
    def show_final_results(self):
        """Show final test results summary."""
        print(f"\n🏁 Test Suite Complete")
        print("=" * 50)
        
        total_tests = self.test_results['passed'] + self.test_results['failed']
        pass_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Test Results:")
        print(f"   ✅ Passed: {self.test_results['passed']}")
        print(f"   ❌ Failed: {self.test_results['failed']}")
        print(f"   ⚠️  Skipped: {self.test_results['skipped']}")
        print(f"   📈 Pass Rate: {pass_rate:.1f}%")
        
        if self.test_results['failed'] > 0:
            print(f"\n❌ Failed Tests:")
            for detail in self.test_results['details']:
                if not detail['passed']:
                    print(f"   • {detail['test']}: {detail['error']}")
        
        # Overall assessment based on configuration
        min_rate = self.config.min_pass_rate
        max_failures = self.config.max_failed_tests
        
        if pass_rate >= min_rate and self.test_results['failed'] <= max_failures:
            print(f"\n🎉 Excellent! System meets quality thresholds (>{min_rate}% pass rate, <={max_failures} failures)")
        elif pass_rate >= min_rate * 0.9:
            print(f"\n✅ Good! Close to quality threshold ({min_rate}% target)")
        elif pass_rate >= min_rate * 0.7:
            print(f"\n⚠️  Moderate issues - below quality threshold ({pass_rate:.1f}% < {min_rate}%)")
        else:
            print(f"\n❌ Major issues - significant quality concerns ({pass_rate:.1f}% << {min_rate}%)")
        
        # Save detailed results if configured
        if self.config.save_results:
            results_file = Path(__file__).parent / self.config.results_file
            with open(results_file, 'w') as f:
                # Include configuration in results
                full_results = {
                    'config': self.config.__dict__,
                    'results': self.test_results
                }
                json.dump(full_results, f, indent=2, default=str)
            
            print(f"\n📝 Detailed results saved to: {results_file}")

def create_config_from_args(args) -> TestConfig:
    """Create test configuration from command line arguments."""
    config = TestConfig()
    
    # Data source options
    if args.data_path:
        config.data_path = args.data_path
    if args.force_source:
        config.force_data_source = args.force_source
    
    # Performance options
    if args.perf_iterations:
        config.performance_iterations = args.perf_iterations
    if args.max_time:
        config.max_verification_time = args.max_time
    if args.batch_time:
        config.max_batch_time_per_artist = args.batch_time
    
    # Confidence thresholds
    if args.mbid_confidence:
        config.mbid_min_confidence = args.mbid_confidence
    if args.track_confidence:
        config.track_strong_min_confidence = args.track_confidence
    if args.improvement_threshold:
        config.heuristic_improvement_threshold = args.improvement_threshold
    
    # Test scope options
    if args.max_candidates:
        config.max_candidates_per_test = args.max_candidates
    if args.sample_size:
        config.performance_test_sample_size = args.sample_size
    
    # Test selection flags
    config.skip_slow_tests = args.skip_slow
    config.skip_api_tests = args.skip_api
    config.skip_performance_tests = args.skip_performance
    config.verbose_output = not args.quiet
    config.show_progress = not args.no_progress
    
    # Quality thresholds
    if args.min_pass_rate:
        config.min_pass_rate = args.min_pass_rate
    if args.max_failures:
        config.max_failed_tests = args.max_failures
    
    # Output options
    config.save_results = not args.no_save
    if args.results_file:
        config.results_file = args.results_file
    
    # Custom artist lists
    if args.problematic_artists:
        config.problematic_artists = args.problematic_artists.split(',')
    
    return config

def main():
    """Main test runner with comprehensive configuration options."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Phase A.2 Comprehensive Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration Examples:
  # Quick test with custom thresholds
  python manual_test_suite_a2.py --quick --mbid-confidence 0.98 --track-confidence 0.90

  # Performance focus with custom limits
  python manual_test_suite_a2.py --category performance --perf-iterations 10 --max-time 0.3

  # Full test with strict quality requirements
  python manual_test_suite_a2.py --min-pass-rate 95 --max-failures 2

  # API-free testing
  python manual_test_suite_a2.py --skip-api --skip-slow

  # Custom problematic artists
  python manual_test_suite_a2.py --category real --problematic-artists "*LUNA,YOASOBI,NewJeans"
        """
    )
    
    # Basic test selection
    parser.add_argument("--quick", action="store_true", help="Run quick subset of tests")
    parser.add_argument("--category", help="Run specific test category only")
    parser.add_argument("--list-categories", action="store_true", help="List available test categories")
    
    # Data source configuration
    parser.add_argument("--data-path", help="Path to data file (default: lastfm_data.csv)")
    parser.add_argument("--force-source", choices=['lastfm', 'spotify'], help="Force data source type")
    
    # Performance configuration
    parser.add_argument("--perf-iterations", type=int, help="Number of performance test iterations (default: 5)")
    parser.add_argument("--max-time", type=float, help="Max verification time in seconds (default: 0.5)")
    parser.add_argument("--batch-time", type=float, help="Max batch time per artist in seconds (default: 1.0)")
    parser.add_argument("--sample-size", type=int, help="Performance test sample size (default: 10)")
    
    # Confidence thresholds
    parser.add_argument("--mbid-confidence", type=float, help="Minimum MBID confidence (default: 0.95)")
    parser.add_argument("--track-confidence", type=float, help="Minimum track confidence (default: 0.85)")
    parser.add_argument("--improvement-threshold", type=float, help="Improvement threshold (default: 0.75)")
    
    # Test scope
    parser.add_argument("--max-candidates", type=int, help="Max candidates per test (default: 5)")
    parser.add_argument("--problematic-artists", help="Comma-separated list of problematic artists")
    
    # Test selection flags
    parser.add_argument("--skip-slow", action="store_true", help="Skip slow tests")
    parser.add_argument("--skip-api", action="store_true", help="Skip API-dependent tests")
    parser.add_argument("--skip-performance", action="store_true", help="Skip performance tests")
    
    # Output configuration
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress indicators")
    parser.add_argument("--no-save", action="store_true", help="Don't save results to file")
    parser.add_argument("--results-file", help="Custom results file name")
    
    # Quality thresholds
    parser.add_argument("--min-pass-rate", type=float, help="Minimum pass rate percentage (default: 75)")
    parser.add_argument("--max-failures", type=int, help="Maximum allowed failures (default: 5)")
    
    args = parser.parse_args()
    
    if args.list_categories:
        print("Available test categories:")
        print("  • mbid       - MBID matching tests")
        print("  • track      - Track matching tests") 
        print("  • unicode    - Unicode/international tests")
        print("  • edge       - Edge case tests")
        print("  • performance - Performance tests")
        print("  • data       - Data source tests")
        print("  • confidence - Confidence threshold tests")
        print("  • real       - Real problematic artist tests")
        print("\nTest configuration options:")
        print("  • Use --help to see all configuration parameters")
        print("  • Configuration affects test behavior and thresholds")
        print("  • Results include configuration for reproducibility")
        return
    
    # Create configuration from arguments
    config = create_config_from_args(args)
    suite = ComprehensiveTestSuite(config)
    
    if args.category:
        category_map = {
            'mbid': suite.test_mbid_matching,
            'track': suite.test_track_matching,
            'unicode': suite.test_unicode_handling,
            'edge': suite.test_edge_cases,
            'performance': suite.test_performance,
            'data': suite.test_data_sources,
            'confidence': suite.test_confidence_thresholds,
            'case': suite.test_case_insensitive_matching,
            'real': suite.test_real_problematic_artists
        }
        
        if args.category in category_map:
            print(f"Running {args.category} tests only...")
            category_map[args.category]()
            suite.show_final_results()
        else:
            print(f"Unknown category: {args.category}")
            print("Use --list-categories to see available options")
    elif args.quick:
        print("Running quick test subset...")
        suite.test_mbid_matching()
        suite.test_track_matching()
        suite.test_real_problematic_artists()
        suite.show_final_results()
    else:
        suite.run_all_tests()

if __name__ == "__main__":
    main()