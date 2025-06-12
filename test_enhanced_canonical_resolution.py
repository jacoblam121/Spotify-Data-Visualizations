#!/usr/bin/env python3
"""
Test Enhanced Canonical Artist Resolution
=========================================

Tests the new multi-stage verification system for resolving canonical artists.
Specifically tests the ユイカ/YUIKA case with song-based verification.

This validates that we find the correct artist page (highest listener count)
when multiple pages exist for the same artist.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from config_loader import AppConfig
from lastfm_utils import LastfmAPI

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def test_canonical_resolution():
    """Test the enhanced canonical resolution system."""
    print(f"{Colors.BOLD}{Colors.GREEN}🧪 TESTING ENHANCED CANONICAL ARTIST RESOLUTION{Colors.END}")
    print("=" * 80)
    print("Testing multi-stage verification system:")
    print("1. MBID Check (if same MBID, definitely same artist)")
    print("2. Song-based verification (if same songs, same artist)")  
    print("3. Listener count tiebreaker (choose most popular page)")
    print()
    
    # Setup API
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        if not lastfm_config['enabled'] or not lastfm_config['api_key']:
            print(f"{Colors.RED}❌ Last.fm API not configured{Colors.END}")
            return
        
        api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        print(f"{Colors.GREEN}✅ API initialized{Colors.END}")
        
    except Exception as e:
        print(f"{Colors.RED}❌ Setup failed: {e}{Colors.END}")
        return
    
    # Test cases that should benefit from canonical resolution
    test_cases = [
        {
            "name": "Japanese Artist with Multiple Pages",
            "query": "ユイカ",
            "expected_behavior": "Should find YUIKA with higher listener count via song verification"
        },
        {
            "name": "Romanized Version", 
            "query": "YUIKA",
            "expected_behavior": "Should find the canonical page directly"
        },
        {
            "name": "Case Variation",
            "query": "blackbear", 
            "expected_behavior": "Should find the main artist page"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{Colors.BOLD}[TEST {i}/{len(test_cases)}] {test_case['name']}{Colors.END}")
        print(f"Query: '{test_case['query']}'")
        print(f"Expected: {test_case['expected_behavior']}")
        print("-" * 60)
        
        try:
            # Test the enhanced system
            start_time = time.time()
            result = api.get_artist_info(test_case['query'], use_enhanced_matching=True)
            duration = time.time() - start_time
            
            if result:
                name = result.get('name', 'Unknown')
                listeners = result.get('listeners', 0)
                matched_variant = result.get('_matched_variant', test_case['query'])
                resolution_method = result.get('_resolution_method', 'unknown')
                url = result.get('url', '')
                
                print(f"{Colors.GREEN}✅ Found: {name}{Colors.END}")
                print(f"👥 Listeners: {Colors.BOLD}{listeners:,}{Colors.END}")
                print(f"🔗 URL: {Colors.BLUE}{url}{Colors.END}")
                print(f"📝 Matched variant: '{matched_variant}'")
                print(f"🔧 Resolution method: {Colors.CYAN}{resolution_method}{Colors.END}")
                print(f"⏱️ Time: {duration:.2f}s")
                
                # Assessment
                if listeners > 10000:
                    print(f"📈 Assessment: {Colors.GREEN}High popularity - likely correct canonical page{Colors.END}")
                elif listeners > 1000:
                    print(f"📈 Assessment: {Colors.YELLOW}Medium popularity{Colors.END}")
                else:
                    print(f"📈 Assessment: {Colors.RED}Low popularity - might need verification{Colors.END}")
                
                # Show resolution details
                if resolution_method == 'mbid_verified':
                    print(f"🎯 {Colors.GREEN}MBID verification succeeded - definitive match{Colors.END}")
                elif resolution_method == 'song_verified':
                    print(f"🎯 {Colors.GREEN}Song verification succeeded - same artist confirmed{Colors.END}")
                elif resolution_method == 'listener_count_fallback':
                    print(f"🎯 {Colors.YELLOW}Used listener count fallback - manual verification recommended{Colors.END}")
                elif resolution_method == 'single_page':
                    print(f"🎯 {Colors.BLUE}Only one page found - no verification needed{Colors.END}")
                
            else:
                print(f"{Colors.RED}❌ No result found{Colors.END}")
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error: {e}{Colors.END}")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}📋 SUMMARY{Colors.END}")
    print("=" * 80)
    print("✅ Enhanced canonical resolution system tested")
    print("🔍 Check the resolution methods to see how each case was handled")
    print("📊 Compare listener counts with manual Last.fm searches")
    print("🎯 MBID and song verification provide the highest confidence")


def test_song_verification_directly():
    """Test the song verification system directly."""
    print(f"\n{Colors.BOLD}{Colors.PURPLE}🎵 TESTING SONG-BASED VERIFICATION{Colors.END}")
    print("=" * 80)
    print("Testing if different artist name spellings have the same songs")
    print()
    
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test song verification between different spellings
        test_pairs = [
            ("ユイカ", "YUIKA"),  # Japanese vs romanized
            ("blackbear", "Blackbear"),  # Case differences
        ]
        
        for artist1, artist2 in test_pairs:
            print(f"{Colors.CYAN}🎵 Comparing songs: '{artist1}' vs '{artist2}'{Colors.END}")
            
            # Get tracks for both
            tracks1 = api.get_artist_top_tracks(artist1, limit=10)
            tracks2 = api.get_artist_top_tracks(artist2, limit=10)
            
            print(f"   '{artist1}' tracks: {tracks1[:5]}...")  # Show first 5
            print(f"   '{artist2}' tracks: {tracks2[:5]}...")
            
            if tracks1 and tracks2:
                # Calculate similarity
                common = set(tracks1) & set(tracks2)
                total = set(tracks1) | set(tracks2)
                jaccard = len(common) / len(total) if total else 0
                
                print(f"   Common tracks: {len(common)}")
                print(f"   Jaccard similarity: {jaccard:.3f}")
                
                if jaccard > 0.4:
                    print(f"   {Colors.GREEN}✅ Same artist verified by songs{Colors.END}")
                elif len(common) > 3:
                    print(f"   {Colors.GREEN}✅ Same artist verified by common tracks{Colors.END}")
                else:
                    print(f"   {Colors.YELLOW}⚠️ Might be different artists{Colors.END}")
            else:
                print(f"   {Colors.RED}❌ Could not get tracks for comparison{Colors.END}")
            
            print()
            time.sleep(0.3)
    
    except Exception as e:
        print(f"{Colors.RED}❌ Error in song verification test: {e}{Colors.END}")


if __name__ == "__main__":
    test_canonical_resolution()
    test_song_verification_directly()
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 TESTING COMPLETE{Colors.END}")
    print("=" * 80)
    print("The enhanced system should now:")
    print("✅ Find YUIKA (14.6K listeners) instead of ユイカ (49 listeners)")
    print("✅ Use song verification to confirm same artist")
    print("✅ Choose canonical page based on popularity")
    print("✅ Provide detailed resolution method information")
    print()
    print("Manual verification:")
    print("🔗 https://www.last.fm/music/YUIKA (should be the result)")
    print("🔗 https://www.last.fm/music/ユイカ (lower popularity page)")