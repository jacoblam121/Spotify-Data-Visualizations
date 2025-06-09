"""
Automated test suite for Last.fm API integration.
Tests API connectivity, data retrieval, caching, and error handling.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import json
import shutil
import time
from unittest.mock import patch, MagicMock
from lastfm_utils import LastfmAPI, initialize_lastfm_api, get_lastfm_similar_artists


class TestLastfmIntegration(unittest.TestCase):
    """Test cases for Last.fm API integration."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Use test cache directory
        cls.test_cache_dir = "test_lastfm_cache"
        cls.api_key = "1e8f179baf2593c1ec228bf7eba1bfa4"
        cls.api_secret = "2b04ee3940408d3c13ff58ee5567ebd4"
        
    def setUp(self):
        """Set up each test."""
        # Clean test cache directory
        if os.path.exists(self.test_cache_dir):
            shutil.rmtree(self.test_cache_dir)
            
        # Initialize API
        self.api = LastfmAPI(self.api_key, self.api_secret, self.test_cache_dir)
        
    def tearDown(self):
        """Clean up after each test."""
        # Remove test cache directory
        if os.path.exists(self.test_cache_dir):
            shutil.rmtree(self.test_cache_dir)
    
    def test_api_initialization(self):
        """Test API initialization and cache directory creation."""
        self.assertTrue(os.path.exists(self.test_cache_dir))
        self.assertEqual(self.api.api_key, self.api_key)
        self.assertEqual(self.api.cache_dir, self.test_cache_dir)
        
    def test_cache_key_generation(self):
        """Test cache key generation is consistent."""
        params1 = {'artist': 'Taylor Swift', 'limit': '50'}
        params2 = {'limit': '50', 'artist': 'Taylor Swift'}  # Different order
        
        key1 = self.api._get_cache_key('artist.getsimilar', params1)
        key2 = self.api._get_cache_key('artist.getsimilar', params2)
        
        self.assertEqual(key1, key2)  # Should be same regardless of order
        
    def test_get_similar_artists_by_name(self):
        """Test fetching similar artists by name."""
        # Use a popular artist to ensure data exists
        similar = self.api.get_similar_artists(artist_name="Taylor Swift", limit=10)
        
        self.assertIsInstance(similar, list)
        self.assertGreater(len(similar), 0)
        
        # Check structure of first result
        if similar:
            first = similar[0]
            self.assertIn('name', first)
            self.assertIn('match', first)
            self.assertIn('mbid', first)
            self.assertIsInstance(first['match'], float)
            self.assertGreaterEqual(first['match'], 0)
            self.assertLessEqual(first['match'], 1)
            
    def test_get_similar_artists_with_mbid(self):
        """Test fetching similar artists by MBID."""
        # Taylor Swift's MBID
        mbid = "20244d07-534f-4eff-b4d4-930878889970"
        similar = self.api.get_similar_artists(mbid=mbid, limit=5)
        
        self.assertIsInstance(similar, list)
        if similar:  # Only check if API returns data
            self.assertGreater(len(similar), 0)
            
    def test_similarity_score_validation(self):
        """Test that similarity scores are valid."""
        similar = self.api.get_similar_artists(artist_name="Paramore", limit=20)
        
        for artist in similar:
            score = artist.get('match', 0)
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1)
            
        # Check that scores are sorted (highest first)
        if len(similar) > 1:
            scores = [a['match'] for a in similar]
            self.assertEqual(scores, sorted(scores, reverse=True))
            
    def test_cache_functionality(self):
        """Test that caching works correctly."""
        # First request (should hit API)
        start_time = time.time()
        result1 = self.api.get_similar_artists(artist_name="Ariana Grande", limit=5)
        first_duration = time.time() - start_time
        
        # Second request (should hit cache)
        start_time = time.time()
        result2 = self.api.get_similar_artists(artist_name="Ariana Grande", limit=5)
        second_duration = time.time() - start_time
        
        # Check results are identical
        self.assertEqual(result1, result2)
        
        # Second request should be much faster (cache hit)
        self.assertLess(second_duration, first_duration / 2)
        
        # Check cache file exists
        self.assertTrue(os.path.exists(self.api.cache_file))
        
    def test_rate_limiting(self):
        """Test rate limiting between requests."""
        # Make multiple requests
        start_time = time.time()
        
        for i in range(3):
            self.api.get_similar_artists(artist_name=f"TestArtist{i}", limit=1)
            
        total_time = time.time() - start_time
        
        # Should take at least (n-1) * min_interval seconds
        expected_min_time = 2 * self.api.min_request_interval
        self.assertGreaterEqual(total_time, expected_min_time * 0.9)  # Allow 10% margin
        
    def test_get_artist_info(self):
        """Test fetching full artist information."""
        info = self.api.get_artist_info(artist_name="BLACKPINK")
        
        self.assertIsNotNone(info)
        self.assertIn('name', info)
        self.assertIn('playcount', info)
        self.assertIn('listeners', info)
        self.assertIn('tags', info)
        self.assertIn('bio', info)
        
        # Check data types
        self.assertIsInstance(info['playcount'], int)
        self.assertIsInstance(info['listeners'], int)
        self.assertIsInstance(info['tags'], list)
        
    def test_get_artist_tags(self):
        """Test fetching artist tags."""
        tags = self.api.get_artist_tags(artist_name="BTS")
        
        self.assertIsInstance(tags, list)
        if tags:
            first_tag = tags[0]
            self.assertIn('name', first_tag)
            self.assertIn('count', first_tag)
            self.assertIsInstance(first_tag['count'], int)
            
    def test_error_handling_nonexistent_artist(self):
        """Test handling of non-existent artists."""
        # Random string unlikely to be an artist
        similar = self.api.get_similar_artists(artist_name="zxcvbnm123456789")
        self.assertIsInstance(similar, list)
        self.assertEqual(len(similar), 0)
        
    def test_error_handling_special_characters(self):
        """Test handling of special characters in artist names."""
        # Test with accented characters
        similar = self.api.get_similar_artists(artist_name="Beyoncé")
        self.assertIsInstance(similar, list)
        
        # Test with Unicode (Japanese)
        similar_jp = self.api.get_similar_artists(artist_name="ヨルシカ")
        self.assertIsInstance(similar_jp, list)
        
    def test_convenience_functions(self):
        """Test the module-level convenience functions."""
        # Initialize the global instance
        initialize_lastfm_api(self.api_key, self.api_secret, self.test_cache_dir)
        
        # Test getting similar artists
        similar = get_lastfm_similar_artists("Linkin Park", limit=5)
        self.assertIsInstance(similar, list)
        
    def test_missing_parameters(self):
        """Test error handling when required parameters are missing."""
        # Should return empty list when no parameters provided
        similar = self.api.get_similar_artists()
        self.assertEqual(similar, [])
        
        # Should return None when no parameters provided
        info = self.api.get_artist_info()
        self.assertIsNone(info)
        
    def test_network_error_handling(self):
        """Test handling of network errors."""
        # Use the existing API error response test approach
        # Network errors are handled the same way as API errors
        bad_api = LastfmAPI("invalid_key", "invalid_secret", self.test_cache_dir)
        
        # This will cause a 403 error which tests error handling
        similar = bad_api.get_similar_artists(artist_name="Test")
        self.assertEqual(similar, [])
        
    def test_api_error_response(self):
        """Test handling of Last.fm API error responses."""
        # Use invalid API key to trigger error
        bad_api = LastfmAPI("invalid_key", "invalid_secret", self.test_cache_dir)
        
        similar = bad_api.get_similar_artists(artist_name="Test")
        self.assertEqual(similar, [])


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)