#!/usr/bin/env python3
"""
Test Suite for Artist Verification System
==========================================
Comprehensive tests for artist identity verification using golden test cases.
"""

import json
import sys
import unittest
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from artist_verification import ArtistVerifier, VerificationResult

class TestArtistVerification(unittest.TestCase):
    """Test cases for artist verification system."""
    
    def setUp(self):
        """Set up test verifier."""
        # Use a mock data path for testing
        self.verifier = ArtistVerifier(spotify_data_path="spotify_data.json")
        self.golden_files_dir = Path(__file__).parent.parent / "golden_files"
    
    def load_golden_test_case(self, filename: str) -> Dict:
        """Load a golden test case from JSON file."""
        file_path = self.golden_files_dir / filename
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_luna_artist_verification(self):
        """Test that *luna is correctly identified and not confused with luna."""
        test_case = self.load_golden_test_case("luna_test_case.json")
        
        result = self.verifier.verify_artist_candidates(
            test_case["query_artist"],
            test_case["mock_candidates"]
        )
        
        chosen_name = result.chosen_profile.get("name")
        expected_name = test_case["expected_choice"]
        
        self.assertEqual(chosen_name, expected_name, 
                        f"Expected {expected_name}, but got {chosen_name}")
        self.assertGreater(result.confidence_score, 0.6, 
                          "Confidence score should be reasonably high")
    
    def test_yoasobi_artist_verification(self):
        """Test that YOASOBI uses the high-listener profile."""
        test_case = self.load_golden_test_case("yoasobi_test_case.json")
        
        result = self.verifier.verify_artist_candidates(
            test_case["query_artist"],
            test_case["mock_candidates"]
        )
        
        chosen_name = result.chosen_profile.get("name")
        chosen_listeners = result.chosen_profile.get("listeners", 0)
        expected_name = test_case["expected_choice"]
        expected_listeners = test_case["expected_listeners"]
        
        self.assertEqual(chosen_name, expected_name,
                        f"Expected {expected_name}, but got {chosen_name}")
        self.assertEqual(chosen_listeners, expected_listeners,
                        f"Expected {expected_listeners} listeners, but got {chosen_listeners}")
    
    def test_ive_dual_profile_scenario(self):
        """Test IVE dual-profile handling (complex case)."""
        test_case = self.load_golden_test_case("ive_test_case.json")
        
        # Test basic verification - should prefer higher listener count
        result = self.verifier.verify_artist_candidates(
            test_case["query_artist"],
            test_case["mock_candidates"]
        )
        
        chosen_listeners = result.chosen_profile.get("listeners", 0)
        
        # Should choose a high-listener profile for basic verification
        self.assertGreater(chosen_listeners, 100000,
                          "Should choose high-listener profile for IVE")
    
    def test_name_similarity_scoring(self):
        """Test name similarity calculations."""
        # Test exact match
        exact_score = self.verifier._calculate_name_similarity("YOASOBI", "YOASOBI")
        self.assertEqual(exact_score, 1.0, "Exact matches should score 1.0")
        
        # Test case insensitive match
        case_score = self.verifier._calculate_name_similarity("yoasobi", "YOASOBI")
        self.assertEqual(case_score, 1.0, "Case insensitive matches should score 1.0")
        
        # Test asterisk penalty
        asterisk_score = self.verifier._calculate_name_similarity("*luna", "luna")
        self.assertLess(asterisk_score, 0.5, "Asterisk mismatch should be heavily penalized")
    
    def test_listener_reasonableness_scoring(self):
        """Test listener count reasonableness calculations."""
        # Test zero listeners
        zero_score = self.verifier._calculate_listener_reasonableness(0)
        self.assertEqual(zero_score, 0.0, "Zero listeners should score 0")
        
        # Test reasonable listener counts
        medium_score = self.verifier._calculate_listener_reasonableness(100000)
        high_score = self.verifier._calculate_listener_reasonableness(1000000)
        
        self.assertGreater(medium_score, 0.5, "100K listeners should score reasonably")
        self.assertGreater(high_score, medium_score, "Higher listeners should score higher")
        
        # Test very high listeners (diminishing returns)
        very_high_score = self.verifier._calculate_listener_reasonableness(10000000)
        self.assertLessEqual(very_high_score, 1.0, "Score should not exceed 1.0")

class TestGoldenFiles(unittest.TestCase):
    """Test that all golden files are valid and loadable."""
    
    def setUp(self):
        self.golden_files_dir = Path(__file__).parent.parent / "golden_files"
    
    def test_all_golden_files_valid(self):
        """Test that all golden test case files are valid JSON."""
        golden_files = list(self.golden_files_dir.glob("*.json"))
        
        self.assertGreater(len(golden_files), 0, "Should have at least one golden file")
        
        for file_path in golden_files:
            with self.subTest(file=file_path.name):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Check required fields
                    required_fields = ["query_artist", "mock_candidates", "expected_choice"]
                    for field in required_fields:
                        self.assertIn(field, data, f"Missing required field: {field}")
                    
                    # Check candidates structure
                    self.assertIsInstance(data["mock_candidates"], list)
                    for candidate in data["mock_candidates"]:
                        self.assertIn("name", candidate)
                        self.assertIn("listeners", candidate)
                        self.assertIsInstance(candidate["listeners"], int)
                
                except json.JSONDecodeError as e:
                    self.fail(f"Invalid JSON in {file_path.name}: {e}")

def run_manual_verification_tests():
    """
    Run manual verification tests that can be executed independently.
    This function provides detailed output for manual verification.
    """
    print("🧪 Manual Artist Verification Tests")
    print("=" * 50)
    
    verifier = ArtistVerifier()
    golden_files_dir = Path(__file__).parent.parent / "golden_files"
    
    test_files = ["luna_test_case.json", "yoasobi_test_case.json", "ive_test_case.json"]
    
    for test_file in test_files:
        print(f"\n🎯 Testing: {test_file}")
        print("-" * 30)
        
        try:
            with open(golden_files_dir / test_file, 'r', encoding='utf-8') as f:
                test_case = json.load(f)
            
            result = verifier.verify_artist_candidates(
                test_case["query_artist"],
                test_case["mock_candidates"]
            )
            
            chosen_name = result.chosen_profile.get("name", "Unknown")
            chosen_listeners = result.chosen_profile.get("listeners", 0)
            expected_name = test_case["expected_choice"]
            
            print(f"   Query Artist: {test_case['query_artist']}")
            print(f"   Candidates: {len(test_case['mock_candidates'])}")
            print(f"   Chosen: {chosen_name} ({chosen_listeners:,} listeners)")
            print(f"   Expected: {expected_name}")
            print(f"   Confidence: {result.confidence_score:.3f}")
            print(f"   Method: {result.verification_method}")
            
            if chosen_name == expected_name:
                print("   ✅ PASS")
            else:
                print("   ❌ FAIL")
                print(f"   Debug info: {result.debug_info}")
        
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print(f"\n✅ Manual verification tests complete!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run artist verification tests")
    parser.add_argument("--manual", action="store_true", 
                       help="Run manual verification tests with detailed output")
    parser.add_argument("--unittest", action="store_true",
                       help="Run automated unit tests")
    
    args = parser.parse_args()
    
    if args.manual:
        run_manual_verification_tests()
    elif args.unittest:
        unittest.main(argv=[''])
    else:
        # Run both by default
        print("Running manual verification tests first...")
        run_manual_verification_tests()
        print("\nRunning automated unit tests...")
        unittest.main(argv=[''], exit=False)