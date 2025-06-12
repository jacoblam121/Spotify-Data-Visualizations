#!/usr/bin/env python3
"""
Comprehensive Artist Matching Test Suite
========================================

This test suite validates the enhanced artist resolution system against real Last.fm data.
It shows listener counts so you can manually verify matches against lastfm.com.

Features:
- Tests both basic and enhanced systems side-by-side
- Shows Last.fm listener counts for verification
- Tests the new canonical resolution with MBID and song verification
- Color-coded output for easy verification
- Exports results to CSV for analysis
- Includes problematic cases from your original issues

Usage:
    python comprehensive_artist_test_suite.py
    python comprehensive_artist_test_suite.py --export-csv
    python comprehensive_artist_test_suite.py --test-specific "ユイカ,blackbear"
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csv
import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import argparse
from dataclasses import dataclass, asdict

from config_loader import AppConfig
from lastfm_utils import LastfmAPI
from data_processor import split_artist_collaborations

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

@dataclass
class TestResult:
    """Structured test result for analysis."""
    query: str
    collaboration_split: List[str]
    old_system_found: bool
    old_system_artist: str
    old_system_listeners: int
    old_system_variant: str
    new_system_found: bool
    new_system_artist: str
    new_system_confidence: float
    new_system_method: str
    lastfm_listeners: int
    lastfm_url: str
    manual_verification_needed: bool
    notes: str


class ComprehensiveArtistTester:
    """Comprehensive testing framework for artist matching systems."""
    
    def __init__(self):
        """Initialize the tester with both basic and enhanced systems."""
        self.setup_apis()
        self.test_results: List[TestResult] = []
        
        # Test cases covering various problematic scenarios
        self.test_cases = self.get_comprehensive_test_cases()
    
    def setup_apis(self):
        """Set up Last.fm API connection."""
        try:
            config = AppConfig('configurations.txt')
            lastfm_config = config.get_lastfm_config()
            
            if not lastfm_config['enabled'] or not lastfm_config['api_key']:
                print(f"{Colors.RED}❌ Last.fm API not configured. Please check configurations.txt{Colors.END}")
                sys.exit(1)
            
            self.lastfm_api = LastfmAPI(
                lastfm_config['api_key'],
                lastfm_config['api_secret'],
                lastfm_config['cache_dir']
            )
            print(f"{Colors.GREEN}✅ Last.fm API initialized{Colors.END}")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to initialize APIs: {e}{Colors.END}")
            sys.exit(1)
    
    def get_comprehensive_test_cases(self) -> List[str]:
        """Get comprehensive test cases covering various problematic scenarios."""
        return [
            # Your original problematic cases
            "ユイカ",  # Japanese artist with false positive issue
            "blackbear",  # Popular artist that couldn't be found
            "BoyWithUke (with blackbear)",  # Collaboration that was causing issues
            
            # More Japanese/Korean artists (Unicode challenges)
            "YOASOBI",
            "ヨルシカ", 
            "TWICE",
            "BTS",
            "NewJeans",
            "LE SSERAFIM",
            "aespa",
            "(G)I-DLE",
            "MIYEON",  # Another you mentioned as problematic
            "88rising",  # Another you mentioned as problematic
            
            # Collaboration patterns
            "Taylor Swift feat. Ed Sheeran",
            "Machine Gun Kelly & blackbear", 
            "Dua Lipa, BLACKPINK",
            "Post Malone (feat. 21 Savage)",
            "Ariana Grande feat. The Weeknd",
            "Justin Bieber & Chance the Rapper",
            
            # Artists with special characters/styling
            "P!nk",
            "Ke$ha", 
            "BBNO$",
            "XXXTentacion",
            "twenty one pilots",
            "Panic! At The Disco",
            
            # Common abbreviations that might cause issues
            "MGK",  # Machine Gun Kelly
            "TOP",  # TWENTY ONE PILOTS or T.O.P
            "FOB",  # Fall Out Boy
            "MCR",  # My Chemical Romance
            "BMTH",  # Bring Me The Horizon
            
            # Hip-hop artists with stylized names
            "A$AP Rocky",
            "21 Savage", 
            "Lil Wayne",
            "Juice WRLD",
            "NBA YoungBoy",
            
            # Artists that might have name variations
            "SOMI",  # vs Jeon Somi
            "IU",
            "SUNMI",
            "AIMYON",
            
            # Western artists that might have issues
            "The Beatles",
            "Led Zeppelin", 
            "Queen",
            "AC/DC",
            "Guns N' Roses",
            
            # More complex collaborations
            "BoyWithUke, blackbear, nobody likes you pat",
            "Lady Gaga, Ariana Grande",
            "The Chainsmokers & Coldplay",
            "Calvin Harris feat. Pharrell Williams, Katy Perry, Big Sean",
            
            # Edge cases
            "",  # Empty string
            "   ",  # Whitespace only
            "Unknown Artist",  # Generic name
            "Various Artists",  # Compilation indicator
            
            # International artists from different regions
            "Bad Bunny",  # Latin
            "ROSALÍA", 
            "Stromae",  # French
            "Indila",
            "Rammstein",  # German
            "BABYMETAL",  # Japanese Metal
            "PSY",  # Korean
        ]
    
    def test_basic_system(self, artist: str) -> Tuple[bool, str, int, str]:
        """Test the basic Last.fm system (no enhanced matching)."""
        try:
            # Test artist info without enhanced matching
            info = self.lastfm_api.get_artist_info(artist, use_enhanced_matching=False)
            if info:
                listeners = info.get('listeners', 0)
                return True, info['name'], listeners, artist
            
            return False, "", 0, ""
            
        except Exception as e:
            print(f"   {Colors.RED}Error in basic system: {e}{Colors.END}")
            return False, "", 0, ""
    
    def test_enhanced_system(self, artist: str) -> Tuple[bool, str, int, str]:
        """Test the enhanced Last.fm system (with canonical resolution)."""
        try:
            # Test with enhanced matching using canonical resolution
            info = self.lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
            if info:
                listeners = info.get('listeners', 0)
                matched_variant = info.get('_matched_variant', artist)
                resolution_method = info.get('_resolution_method', 'unknown')
                return True, info['name'], listeners, f"{matched_variant} ({resolution_method})"
            
            return False, "", 0, ""
            
        except Exception as e:
            print(f"   {Colors.RED}Error in enhanced system: {e}{Colors.END}")
            return False, "", 0, ""
    
    def get_lastfm_verification_data(self, artist_name: str) -> Tuple[int, str]:
        """Get Last.fm data for manual verification."""
        try:
            info = self.lastfm_api.get_artist_info(artist_name, use_enhanced_matching=False)
            if info:
                listeners = info.get('listeners', 0)
                url = info.get('url', f"https://www.last.fm/music/{artist_name.replace(' ', '+')}")
                return listeners, url
            return 0, f"https://www.last.fm/music/{artist_name.replace(' ', '+')}"
        except:
            return 0, f"https://www.last.fm/music/{artist_name.replace(' ', '+')}"
    
    def run_single_test(self, query: str, show_details: bool = True) -> TestResult:
        """Run a comprehensive test for a single artist query."""
        if show_details:
            print(f"\n{Colors.BOLD}{Colors.BLUE}🧪 Testing: '{query}'{Colors.END}")
            print("=" * 80)
        
        # Step 1: Test collaboration splitting
        basic_split = split_artist_collaborations(query)  # Basic system
        enhanced_split = split_artist_collaborations(query)  # Enhanced system (same for now)
        
        if show_details:
            print(f"{Colors.CYAN}📝 Collaboration Splitting:{Colors.END}")
            print(f"   Basic system: {basic_split}")
            print(f"   Enhanced system: {enhanced_split}")
            
            if basic_split != enhanced_split:
                print(f"   {Colors.YELLOW}⚠️  Different splitting results!{Colors.END}")
        
        # Use basic splitting for both tests
        artists_to_test = basic_split if basic_split else [query]
        
        # For this test, we'll use the first artist from the split
        test_artist = artists_to_test[0] if artists_to_test else query
        
        if show_details:
            print(f"\n{Colors.CYAN}🔍 Testing Artist: '{test_artist}'{Colors.END}")
        
        # Step 2: Test basic system
        basic_found, basic_artist, basic_listeners, basic_variant = self.test_basic_system(test_artist)
        
        if show_details:
            if basic_found:
                print(f"   {Colors.GREEN}✅ Basic System: Found '{basic_artist}'{Colors.END}")
                print(f"      Listeners: {basic_listeners:,}")
                print(f"      Matched via: '{basic_variant}'")
            else:
                print(f"   {Colors.RED}❌ Basic System: No match found{Colors.END}")
        
        # Step 3: Test enhanced system
        enhanced_found, enhanced_artist, enhanced_listeners, enhanced_info = self.test_enhanced_system(test_artist)
        
        if show_details:
            if enhanced_found:
                print(f"   {Colors.GREEN}✅ Enhanced System: Found '{enhanced_artist}'{Colors.END}")
                print(f"      Listeners: {enhanced_listeners:,}")
                print(f"      Details: {enhanced_info}")
            else:
                print(f"   {Colors.RED}❌ Enhanced System: No match found{Colors.END}")
        
        # Step 4: Get Last.fm verification data
        verification_artist = enhanced_artist if enhanced_found else (basic_artist if basic_found else test_artist)
        lastfm_listeners, lastfm_url = self.get_lastfm_verification_data(verification_artist)
        
        if show_details:
            print(f"\n{Colors.PURPLE}🌐 Last.fm Verification:{Colors.END}")
            print(f"   Artist: {verification_artist}")
            print(f"   Listeners: {lastfm_listeners:,}")
            print(f"   URL: {lastfm_url}")
        
        # Step 5: Analysis and recommendations
        manual_verification_needed = False
        notes = []
        
        if basic_found and enhanced_found and basic_artist != enhanced_artist:
            notes.append("Different artists found by basic vs enhanced system")
            manual_verification_needed = True
        
        if enhanced_found and enhanced_listeners < 1000:
            notes.append("Very low listener count - potential false positive")
            manual_verification_needed = True
        
        if lastfm_listeners == 0:
            notes.append("No Last.fm data found for verification")
            manual_verification_needed = True
        
        if show_details and manual_verification_needed:
            print(f"\n   {Colors.YELLOW}⚠️  Manual verification recommended:{Colors.END}")
            for note in notes:
                print(f"      - {note}")
        
        # Create test result
        result = TestResult(
            query=query,
            collaboration_split=basic_split,
            old_system_found=basic_found,
            old_system_artist=basic_artist,
            old_system_listeners=basic_listeners,
            old_system_variant=basic_variant,
            new_system_found=enhanced_found,
            new_system_artist=enhanced_artist,
            new_system_confidence=float(enhanced_listeners / 1000000) if enhanced_found else 0.0,  # Convert listeners to confidence-like score
            new_system_method=enhanced_info if enhanced_found else "",
            lastfm_listeners=lastfm_listeners,
            lastfm_url=lastfm_url,
            manual_verification_needed=manual_verification_needed,
            notes="; ".join(notes)
        )
        
        self.test_results.append(result)
        return result
    
    
    def run_comprehensive_test(self, specific_tests: List[str] = None):
        """Run the comprehensive test suite."""
        print(f"{Colors.BOLD}{Colors.GREEN}🚀 COMPREHENSIVE ARTIST MATCHING TEST SUITE{Colors.END}")
        print("=" * 80)
        print("This suite tests both basic and enhanced artist matching systems")
        print("and provides Last.fm listener counts for manual verification.")
        print(f"Total test cases: {len(specific_tests or self.test_cases)}")
        print()
        
        test_cases = specific_tests or self.test_cases
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{Colors.BOLD}[{i}/{len(test_cases)}]{Colors.END}", end="")
            
            try:
                result = self.run_single_test(test_case)
                
                # Brief summary for batch testing
                if len(test_cases) > 5:  # Only show brief summary for large test runs
                    status_old = f"{Colors.GREEN}✅{Colors.END}" if result.old_system_found else f"{Colors.RED}❌{Colors.END}"
                    status_new = f"{Colors.GREEN}✅{Colors.END}" if result.new_system_found else f"{Colors.RED}❌{Colors.END}"
                    listeners = f"{result.lastfm_listeners:,}" if result.lastfm_listeners > 0 else "Unknown"
                    
                    print(f" '{test_case}' - Basic: {status_old} Enhanced: {status_new} Listeners: {listeners}")
                
                # Rate limiting
                time.sleep(0.3)  # Be nice to Last.fm API
                
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}⚠️  Test interrupted by user{Colors.END}")
                break
            except Exception as e:
                print(f"\n{Colors.RED}❌ Error testing '{test_case}': {e}{Colors.END}")
                continue
        
        self.print_summary()
    
    def print_summary(self):
        """Print a summary of all test results."""
        if not self.test_results:
            return
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}📊 TEST SUMMARY{Colors.END}")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        old_found = sum(1 for r in self.test_results if r.old_system_found)
        new_found = sum(1 for r in self.test_results if r.new_system_found)
        manual_verification = sum(1 for r in self.test_results if r.manual_verification_needed)
        
        print(f"Total tests: {total_tests}")
        print(f"Basic system found: {old_found}/{total_tests} ({old_found/total_tests*100:.1f}%)")
        print(f"Enhanced system found: {new_found}/{total_tests} ({new_found/total_tests*100:.1f}%)")
        print(f"Manual verification needed: {manual_verification}/{total_tests} ({manual_verification/total_tests*100:.1f}%)")
        
        print(f"\n{Colors.YELLOW}⚠️  Cases needing manual verification:{Colors.END}")
        for result in self.test_results:
            if result.manual_verification_needed:
                print(f"   - '{result.query}': {result.notes}")
        
        print(f"\n{Colors.GREEN}✅ High listener count matches:{Colors.END}")
        high_listeners = [r for r in self.test_results if r.new_system_found and (r.lastfm_listeners or 0) > 100000]
        for result in high_listeners[:10]:  # Show first 10
            listeners = result.lastfm_listeners or 0
            print(f"   - '{result.query}' -> '{result.new_system_artist}' ({listeners:,} listeners)")
        
        if len(high_listeners) > 10:
            print(f"   ... and {len(high_listeners) - 10} more")
    
    def export_to_csv(self, filename: str = None):
        """Export test results to CSV for analysis."""
        if not self.test_results:
            print(f"{Colors.RED}No test results to export{Colors.END}")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"artist_matching_test_results_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = list(asdict(self.test_results[0]).keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in self.test_results:
                    writer.writerow(asdict(result))
            
            print(f"{Colors.GREEN}✅ Results exported to: {filename}{Colors.END}")
            print(f"   You can open this in Excel/Google Sheets for analysis")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to export CSV: {e}{Colors.END}")


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Comprehensive Artist Matching Test Suite")
    parser.add_argument("--export-csv", action="store_true", 
                       help="Export results to CSV file")
    parser.add_argument("--test-specific", type=str,
                       help="Test specific artists (comma-separated)")
    parser.add_argument("--output-file", type=str,
                       help="Custom output filename for CSV export")
    
    args = parser.parse_args()
    
    tester = ComprehensiveArtistTester()
    
    # Parse specific tests if provided
    specific_tests = None
    if args.test_specific:
        specific_tests = [artist.strip() for artist in args.test_specific.split(",")]
        print(f"Testing specific artists: {specific_tests}")
    
    # Run the tests
    tester.run_comprehensive_test(specific_tests)
    
    # Export if requested
    if args.export_csv:
        tester.export_to_csv(args.output_file)
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 Testing complete!{Colors.END}")
    print(f"Check the URLs provided to manually verify artist matches on last.fm")


if __name__ == "__main__":
    main()