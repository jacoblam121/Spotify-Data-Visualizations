#!/usr/bin/env python3
"""
Comprehensive Test Script for Artist Verification System
========================================================
Tests the entire verification system with real problematic cases.
This script can be run manually to verify Phase A implementation.
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from artist_verification import ArtistVerifier
from tests.current.test_artist_verification import run_manual_verification_tests

def test_basic_verification():
    """Test basic verification functionality."""
    print("🧪 Basic Verification System Test")
    print("=" * 40)
    
    try:
        verifier = ArtistVerifier()
        print("✅ ArtistVerifier initialized successfully")
        
        # Test with simple mock data
        mock_candidates = [
            {'name': 'Test Artist 1', 'listeners': 100000, 'url': 'test1'},
            {'name': 'Test Artist 2', 'listeners': 50000, 'url': 'test2'}
        ]
        
        result = verifier.verify_artist_candidates("Test Artist 1", mock_candidates)
        
        print(f"✅ Basic verification completed")
        print(f"   Chosen: {result.chosen_profile.get('name')}")
        print(f"   Confidence: {result.confidence_score:.3f}")
        print(f"   Method: {result.verification_method}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic verification failed: {e}")
        return False

def test_name_similarity_edge_cases():
    """Test name similarity calculations with edge cases."""
    print("\n🧪 Name Similarity Edge Cases")
    print("=" * 40)
    
    try:
        verifier = ArtistVerifier()
        
        # Test cases
        test_cases = [
            ("*luna", "luna", "should be low (asterisk penalty)"),
            ("YOASOBI", "yoasobi", "should be 1.0 (case insensitive)"),
            ("IVE", "Ive", "should be high (case difference)"),
            ("artist", "completely different", "should be low (different names)")
        ]
        
        for query, candidate, expected in test_cases:
            score = verifier._calculate_name_similarity(query, candidate)
            print(f"   '{query}' vs '{candidate}': {score:.3f} ({expected})")
        
        print("✅ Name similarity tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Name similarity tests failed: {e}")
        return False

def test_listener_scoring():
    """Test listener count scoring."""
    print("\n🧪 Listener Count Scoring")
    print("=" * 40)
    
    try:
        verifier = ArtistVerifier()
        
        # Test different listener counts
        test_counts = [0, 100, 10000, 100000, 1000000, 10000000]
        
        for count in test_counts:
            score = verifier._calculate_listener_reasonableness(count)
            print(f"   {count:,} listeners: {score:.3f}")
        
        print("✅ Listener scoring tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Listener scoring tests failed: {e}")
        return False

def test_user_data_loading():
    """Test user data loading functionality."""
    print("\n🧪 User Data Loading")
    print("=" * 40)
    
    try:
        verifier = ArtistVerifier()
        
        total_artists = len(verifier.user_tracks_by_artist)
        
        if total_artists > 0:
            print(f"✅ User data loaded: {total_artists} artists")
            
            # Show sample artists
            sample_artists = list(verifier.user_tracks_by_artist.keys())[:5]
            for artist in sample_artists:
                track_count = len(verifier.user_tracks_by_artist[artist])
                print(f"   {artist}: {track_count} tracks")
        else:
            print("⚠️  No user data loaded (spotify_data.json not found or empty)")
            print("   Verification will rely on name/listener similarity only")
        
        return True
        
    except Exception as e:
        print(f"❌ User data loading failed: {e}")
        return False

def test_problematic_artists():
    """Test the specific problematic artists identified."""
    print("\n🧪 Problematic Artists Test")
    print("=" * 40)
    
    try:
        # Run the golden file tests
        run_manual_verification_tests()
        return True
        
    except Exception as e:
        print(f"❌ Problematic artists test failed: {e}")
        return False

def run_comprehensive_tests():
    """Run all verification system tests."""
    print("🚀 Comprehensive Artist Verification System Tests")
    print("=" * 55)
    
    tests = [
        ("Basic Verification", test_basic_verification),
        ("Name Similarity Edge Cases", test_name_similarity_edge_cases),
        ("Listener Count Scoring", test_listener_scoring),
        ("User Data Loading", test_user_data_loading),
        ("Problematic Artists", test_problematic_artists)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("🏁 TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Verification system is ready.")
    else:
        print("⚠️  Some tests failed. Review the output above.")
    
    return passed == total

def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the artist verification system")
    parser.add_argument("--basic", action="store_true", help="Run basic tests only")
    parser.add_argument("--problematic", action="store_true", help="Test problematic artists only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    
    args = parser.parse_args()
    
    if args.basic:
        test_basic_verification()
    elif args.problematic:
        test_problematic_artists()
    else:
        # Run comprehensive tests by default
        success = run_comprehensive_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()