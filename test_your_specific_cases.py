#!/usr/bin/env python3
"""
Test Your Specific Problematic Cases
====================================

This script specifically tests the cases you mentioned:
1. ユイカ (should find YUIKA with 14.6K listeners)
2. blackbear (should find the 1.5M listener artist)
3. BoyWithUke (with blackbear) collaboration parsing

Shows clear before/after comparison and listener counts for verification.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from config_loader import AppConfig
from lastfm_utils import LastfmAPI
from artist_resolver import ArtistResolver
from data_processor import split_artist_collaborations

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


def test_specific_case(case_name: str, artist_query: str, expected_artist: str, 
                      expected_listeners: str, lastfm_api: LastfmAPI, resolver: ArtistResolver):
    """Test a specific problematic case with detailed analysis."""
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}🎯 TEST CASE: {case_name}{Colors.END}")
    print(f"Query: '{artist_query}'")
    print(f"Expected: {expected_artist} ({expected_listeners} listeners)")
    print("=" * 80)
    
    # Test collaboration splitting first
    print(f"{Colors.CYAN}📝 Collaboration Splitting:{Colors.END}")
    old_split = split_artist_collaborations(artist_query)
    new_split = resolver.split_collaborations(artist_query)
    
    print(f"   Current system: {old_split}")
    print(f"   New system:     {new_split}")
    
    if old_split != new_split:
        if len(new_split) > len(old_split):
            print(f"   {Colors.GREEN}✅ New system found more artists{Colors.END}")
        else:
            print(f"   {Colors.YELLOW}⚠️  Different splitting approach{Colors.END}")
    else:
        print(f"   {Colors.GREEN}✅ Same result{Colors.END}")
    
    # Test each artist that results from splitting
    artists_to_test = new_split if new_split else [artist_query]
    
    for artist in artists_to_test:
        print(f"\n{Colors.PURPLE}🧪 Testing Individual Artist: '{artist}'{Colors.END}")
        print("-" * 60)
        
        # Test current system
        print(f"📊 {Colors.BOLD}CURRENT SYSTEM RESULTS:{Colors.END}")
        try:
            # Test artist info
            info = lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
            if info:
                listeners = info.get('listeners', 0)
                matched_variant = info.get('_matched_variant', artist)
                url = info.get('url', '')
                
                print(f"   ✅ Found: {Colors.GREEN}{info['name']}{Colors.END}")
                print(f"   👥 Listeners: {Colors.BOLD}{listeners:,}{Colors.END}")
                print(f"   🔗 URL: {url}")
                print(f"   📝 Matched via variant: '{matched_variant}'")
                
                # Assess if this matches expectations
                if expected_artist.lower() in info['name'].lower() or info['name'].lower() in expected_artist.lower():
                    if "14.6k" in expected_listeners.lower() and 10000 <= listeners <= 20000:
                        print(f"   {Colors.GREEN}🎉 MATCHES EXPECTATION!{Colors.END}")
                    elif "1.5m" in expected_listeners.lower() and listeners >= 1000000:
                        print(f"   {Colors.GREEN}🎉 MATCHES EXPECTATION!{Colors.END}")
                    else:
                        print(f"   {Colors.YELLOW}⚠️  Artist name matches but listener count differs{Colors.END}")
                        print(f"      Expected: {expected_listeners}, Got: {listeners:,}")
                else:
                    print(f"   {Colors.RED}❌ DOESN'T MATCH EXPECTATION{Colors.END}")
                    print(f"      Expected: {expected_artist}, Got: {info['name']}")
                    
                    # Check if this might be a false positive
                    if listeners < 5000:
                        print(f"   {Colors.RED}🚨 POTENTIAL FALSE POSITIVE - very low listener count{Colors.END}")
            else:
                print(f"   {Colors.RED}❌ Not found{Colors.END}")
                
                # Try similar artists fallback
                similar = lastfm_api.get_similar_artists(artist, limit=3, use_enhanced_matching=True)
                if similar:
                    print(f"   🔄 Trying similar artists fallback...")
                    for sim in similar[:2]:  # Check top 2
                        sim_info = lastfm_api.get_artist_info(sim['name'], use_enhanced_matching=False)
                        if sim_info:
                            sim_listeners = sim_info.get('listeners', 0)
                            print(f"      Found: {sim['name']} ({sim_listeners:,} listeners)")
        
        except Exception as e:
            print(f"   {Colors.RED}❌ Error: {e}{Colors.END}")
        
        # Test new system
        print(f"\n🚀 {Colors.BOLD}NEW ROBUST SYSTEM RESULTS:{Colors.END}")
        
        # Create candidate pool (simulate your music library)
        candidate_pool = [
            expected_artist,  # Include the expected result
            artist,           # Include the query
            "YUIKA", "ユイカ", "blackbear", "BoyWithUke", "Machine Gun Kelly",
            "Taylor Swift", "Ed Sheeran", "Ariana Grande", "Post Malone"
        ]
        
        try:
            result = resolver.resolve_artist(artist, candidate_pool)
            if result:
                print(f"   ✅ Found: {Colors.GREEN}{result.artist_name}{Colors.END}")
                print(f"   🎯 Confidence: {Colors.BOLD}{result.confidence:.3f}{Colors.END}")
                print(f"   🔧 Method: {result.method}")
                
                # Get Last.fm verification for the resolved artist
                verify_info = lastfm_api.get_artist_info(result.artist_name, use_enhanced_matching=False)
                if verify_info:
                    verify_listeners = verify_info.get('listeners', 0)
                    verify_url = verify_info.get('url', '')
                    print(f"   👥 Verified listeners: {Colors.BOLD}{verify_listeners:,}{Colors.END}")
                    print(f"   🔗 Verified URL: {verify_url}")
                    
                    # Check against expectations
                    if expected_artist.lower() in result.artist_name.lower():
                        print(f"   {Colors.GREEN}🎉 MATCHES EXPECTED ARTIST!{Colors.END}")
                        
                        if "14.6k" in expected_listeners.lower() and 10000 <= verify_listeners <= 20000:
                            print(f"   {Colors.GREEN}🎉 LISTENER COUNT MATCHES!{Colors.END}")
                        elif "1.5m" in expected_listeners.lower() and verify_listeners >= 1000000:
                            print(f"   {Colors.GREEN}🎉 LISTENER COUNT MATCHES!{Colors.END}")
                    else:
                        print(f"   {Colors.YELLOW}⚠️  Different artist than expected{Colors.END}")
                
                # Confidence assessment
                if result.confidence >= 0.95:
                    print(f"   📈 {Colors.GREEN}Very high confidence - excellent match{Colors.END}")
                elif result.confidence >= 0.90:
                    print(f"   📈 {Colors.GREEN}High confidence - good match{Colors.END}")
                elif result.confidence >= 0.85:
                    print(f"   📈 {Colors.YELLOW}Medium confidence - review recommended{Colors.END}")
                else:
                    print(f"   📈 {Colors.RED}Low confidence - manual verification needed{Colors.END}")
            else:
                print(f"   {Colors.RED}❌ Not found{Colors.END}")
                print(f"   💡 Would be added to review queue for manual verification")
        
        except Exception as e:
            print(f"   {Colors.RED}❌ Error: {e}{Colors.END}")
        
        # Manual verification suggestion
        print(f"\n{Colors.CYAN}🔍 Manual Verification Steps:{Colors.END}")
        print(f"   1. Search Last.fm: https://www.last.fm/search/artists?q={artist.replace(' ', '+')}")
        print(f"   2. Expected result: https://www.last.fm/music/{expected_artist.replace(' ', '+')}")
        print(f"   3. Check if listener count is around {expected_listeners}")
        
        # Add delay for readability
        if len(artists_to_test) > 1:
            time.sleep(1)


def main():
    """Test the specific cases mentioned by the user."""
    print(f"{Colors.BOLD}{Colors.GREEN}🎯 TESTING YOUR SPECIFIC PROBLEMATIC CASES{Colors.END}")
    print("=" * 80)
    print("This tests the exact issues you mentioned:")
    print("1. ユイカ false positive issue")
    print("2. blackbear not being found")  
    print("3. BoyWithUke collaboration parsing")
    print()
    
    # Setup APIs
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        if not lastfm_config['enabled'] or not lastfm_config['api_key']:
            print(f"{Colors.RED}❌ Last.fm API not configured{Colors.END}")
            return
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        resolver = ArtistResolver()
        
        print(f"{Colors.GREEN}✅ APIs initialized{Colors.END}")
        
    except Exception as e:
        print(f"{Colors.RED}❌ Setup failed: {e}{Colors.END}")
        return
    
    # Test cases based on your specific issues
    test_cases = [
        {
            "name": "Japanese Artist False Positive",
            "query": "ユイカ", 
            "expected_artist": "YUIKA",
            "expected_listeners": "14.6K",
        },
        {
            "name": "Popular Artist Not Found", 
            "query": "blackbear",
            "expected_artist": "blackbear",
            "expected_listeners": "1.5M",
        },
        {
            "name": "Collaboration Parsing",
            "query": "BoyWithUke (with blackbear)",
            "expected_artist": "BoyWithUke + blackbear (both found)",
            "expected_listeners": "Varies",
        },
        {
            "name": "Track Title Collaboration",
            "query": "IDGAF (with blackbear)",
            "expected_artist": "blackbear", 
            "expected_listeners": "1.5M",
        }
    ]
    
    # Run each test case
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{Colors.BOLD}[TEST {i}/{len(test_cases)}]{Colors.END}")
        
        test_specific_case(
            test_case["name"],
            test_case["query"], 
            test_case["expected_artist"],
            test_case["expected_listeners"],
            lastfm_api,
            resolver
        )
        
        # Rate limiting
        time.sleep(0.5)
    
    # Summary
    print(f"\n{Colors.BOLD}{Colors.CYAN}📋 SUMMARY & NEXT STEPS{Colors.END}")
    print("=" * 80)
    print(f"✅ Test completed for your specific problematic cases")
    print(f"📊 Compare the results against the expected Last.fm URLs")
    print(f"🔧 The new robust system should handle these cases better")
    print(f"💡 Any remaining issues can be solved by adding to the aliases database")
    print()
    print(f"{Colors.YELLOW}To verify results manually:{Colors.END}")
    print("1. Check the Last.fm URLs provided above")
    print("2. Verify listener counts match expectations") 
    print("3. Confirm artist names are correct")
    print("4. Report any remaining issues for further refinement")


if __name__ == "__main__":
    main()