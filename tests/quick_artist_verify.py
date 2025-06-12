#!/usr/bin/env python3
"""
Quick Artist Verification Tool
==============================

A simpler, focused tool for testing specific problematic artists.
Shows listener counts and Last.fm URLs for easy manual verification.

Usage:
    python quick_artist_verify.py
    python quick_artist_verify.py "ユイカ"
    python quick_artist_verify.py "BoyWithUke (with blackbear)"
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI
from artist_resolver import ArtistResolver
from data_processor import split_artist_collaborations

# Color codes for better visibility
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def setup_apis():
    """Set up API connections."""
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        if not lastfm_config['enabled'] or not lastfm_config['api_key']:
            print(f"{Colors.RED}❌ Last.fm API not configured{Colors.END}")
            return None, None
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        resolver = ArtistResolver()
        
        return lastfm_api, resolver
        
    except Exception as e:
        print(f"{Colors.RED}❌ Setup failed: {e}{Colors.END}")
        return None, None


def test_single_artist(artist_query: str, lastfm_api: LastfmAPI, resolver: ArtistResolver):
    """Test a single artist with detailed output."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}🧪 Testing: '{artist_query}'{Colors.END}")
    print("=" * 80)
    
    # Step 1: Show collaboration splitting
    print(f"{Colors.CYAN}📝 Collaboration Splitting:{Colors.END}")
    old_split = split_artist_collaborations(artist_query)
    new_split = resolver.split_collaborations(artist_query)
    
    print(f"   Current system: {old_split}")
    print(f"   New system:     {new_split}")
    
    if old_split != new_split:
        print(f"   {Colors.YELLOW}⚠️  Different results - new system is more robust{Colors.END}")
    
    # Test each artist from the split
    artists_to_test = new_split if new_split else [artist_query]
    
    for i, artist in enumerate(artists_to_test, 1):
        if len(artists_to_test) > 1:
            print(f"\n{Colors.CYAN}🎵 Testing Artist {i}/{len(artists_to_test)}: '{artist}'{Colors.END}")
            print("-" * 60)
        
        # Test current system
        print(f"{Colors.PURPLE}📊 Current Last.fm System:{Colors.END}")
        try:
            # Try artist info first
            info = lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
            if info:
                listeners = info.get('listeners', 0)
                playcount = info.get('playcount', 0)
                matched_variant = info.get('_matched_variant', artist)
                url = info.get('url', f"https://www.last.fm/music/{artist.replace(' ', '+')}")
                
                print(f"   ✅ Found: {Colors.GREEN}{info['name']}{Colors.END}")
                print(f"   👥 Listeners: {Colors.BOLD}{listeners:,}{Colors.END}")
                print(f"   🎵 Total plays: {playcount:,}")
                print(f"   🔗 URL: {Colors.BLUE}{url}{Colors.END}")
                print(f"   📝 Matched via: '{matched_variant}'")
                
                # Color code listener count for quick assessment
                if listeners > 100000:
                    listener_assessment = f"{Colors.GREEN}High popularity{Colors.END}"
                elif listeners > 10000:
                    listener_assessment = f"{Colors.YELLOW}Medium popularity{Colors.END}"
                elif listeners > 1000:
                    listener_assessment = f"{Colors.YELLOW}Low popularity{Colors.END}"
                else:
                    listener_assessment = f"{Colors.RED}Very low - potential false positive{Colors.END}"
                
                print(f"   📈 Assessment: {listener_assessment}")
                
            else:
                print(f"   {Colors.RED}❌ No artist info found{Colors.END}")
                
                # Try similar artists as backup
                similar = lastfm_api.get_similar_artists(artist, limit=1, use_enhanced_matching=True)
                if similar:
                    print(f"   🔄 Trying similar artists approach...")
                    similar_info = lastfm_api.get_artist_info(similar[0]['name'], use_enhanced_matching=False)
                    if similar_info:
                        listeners = similar_info.get('listeners', 0)
                        print(f"   ✅ Found via similar: {Colors.GREEN}{similar[0]['name']}{Colors.END}")
                        print(f"   👥 Listeners: {Colors.BOLD}{listeners:,}{Colors.END}")
                    else:
                        print(f"   {Colors.RED}❌ Similar artists approach also failed{Colors.END}")
                else:
                    print(f"   {Colors.RED}❌ Similar artists approach also failed{Colors.END}")
        
        except Exception as e:
            print(f"   {Colors.RED}❌ Error: {e}{Colors.END}")
        
        # Test new system (we need a candidate pool)
        print(f"\n{Colors.PURPLE}🚀 New Robust System:{Colors.END}")
        
        # Create a realistic candidate pool
        candidate_pool = create_test_candidate_pool(artist)
        
        try:
            result = resolver.resolve_artist(artist, candidate_pool)
            if result:
                print(f"   ✅ Found: {Colors.GREEN}{result.artist_name}{Colors.END}")
                print(f"   🎯 Confidence: {Colors.BOLD}{result.confidence:.3f}{Colors.END}")
                print(f"   🔧 Method: {result.method}")
                
                # Get Last.fm data for the resolved artist
                verification_info = lastfm_api.get_artist_info(result.artist_name, use_enhanced_matching=False)
                if verification_info:
                    verify_listeners = verification_info.get('listeners', 0)
                    verify_url = verification_info.get('url', f"https://www.last.fm/music/{result.artist_name.replace(' ', '+')}")
                    print(f"   👥 Verified listeners: {Colors.BOLD}{verify_listeners:,}{Colors.END}")
                    print(f"   🔗 Verified URL: {Colors.BLUE}{verify_url}{Colors.END}")
                
                # Color code confidence
                if result.confidence >= 0.95:
                    confidence_assessment = f"{Colors.GREEN}Very high confidence{Colors.END}"
                elif result.confidence >= 0.90:
                    confidence_assessment = f"{Colors.GREEN}High confidence{Colors.END}"
                elif result.confidence >= 0.85:
                    confidence_assessment = f"{Colors.YELLOW}Medium confidence{Colors.END}"
                else:
                    confidence_assessment = f"{Colors.RED}Low confidence - needs review{Colors.END}"
                
                print(f"   📈 Assessment: {confidence_assessment}")
                
            else:
                print(f"   {Colors.RED}❌ No match found{Colors.END}")
                print(f"   💡 This artist would be added to the review queue for manual verification")
        
        except Exception as e:
            print(f"   {Colors.RED}❌ Error: {e}{Colors.END}")
        
        # Manual verification guidance
        print(f"\n{Colors.CYAN}🔍 Manual Verification:{Colors.END}")
        print(f"   1. Visit: https://www.last.fm/search/artists?q={artist.replace(' ', '+')}")
        print(f"   2. Check if the found artist matches what you expect")
        print(f"   3. Verify listener count is reasonable for the artist's popularity")
        print(f"   4. Look for alternative spellings if no match found")


def create_test_candidate_pool(artist: str) -> list:
    """Create a test candidate pool for the new system."""
    # This simulates your actual music library
    base_candidates = [
        # Common artists that might be in your library
        "Taylor Swift", "Ed Sheeran", "blackbear", "BoyWithUke", "Machine Gun Kelly",
        "Ariana Grande", "The Weeknd", "Post Malone", "Billie Eilish", "Dua Lipa",
        
        # Japanese/Korean artists
        "YUIKA", "ユイカ", "YOASOBI", "ヨルシカ", "Yorushika", "AIMYON", 
        "TWICE", "BTS", "NewJeans", "LE SSERAFIM", "aespa", "(G)I-DLE", "MIYEON",
        "BLACKPINK", "ITZY", "SEVENTEEN", "Stray Kids", "ENHYPEN",
        
        # Artists with special characters
        "P!nk", "Pink", "Ke$ha", "Kesha", "BBNO$", "twenty one pilots", 
        "XXXTentacion", "Panic! At The Disco",
        
        # Hip-hop variants
        "88rising", "A$AP Rocky", "21 Savage", "Lil Wayne", "Juice WRLD",
        "Machine Gun Kelly", "MGK", "SOMI", "Jeon Somi", "IU", "SUNMI",
    ]
    
    # Add the query artist itself and simple variations
    candidates = set(base_candidates)
    candidates.add(artist)
    candidates.add(artist.upper())
    candidates.add(artist.lower())
    candidates.add(artist.title())
    
    return list(candidates)


def interactive_mode():
    """Interactive mode for testing artists."""
    lastfm_api, resolver = setup_apis()
    if not lastfm_api or not resolver:
        return
    
    print(f"{Colors.BOLD}{Colors.GREEN}🎵 Quick Artist Verification Tool{Colors.END}")
    print("=" * 80)
    print("Enter artist names to test the matching systems.")
    print("This will show Last.fm listener counts for manual verification.")
    print(f"Type 'quit' to exit.\n")
    
    while True:
        try:
            artist_input = input(f"{Colors.CYAN}Enter artist name: {Colors.END}").strip()
            
            if artist_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not artist_input:
                continue
            
            test_single_artist(artist_input, lastfm_api, resolver)
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Goodbye!{Colors.END}")
            break
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.END}")


def main():
    """Main function."""
    if len(sys.argv) > 1:
        # Test specific artist from command line
        artist = " ".join(sys.argv[1:])
        lastfm_api, resolver = setup_apis()
        if lastfm_api and resolver:
            test_single_artist(artist, lastfm_api, resolver)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()