#!/usr/bin/env python3
"""
Migration Script: From Bandaid Fixes to Robust Artist Resolution
================================================================

This script migrates your existing system from the manual pattern database
approach to the robust cascade-based artist resolver.

What it does:
1. Extracts existing known_patterns from lastfm_utils.py
2. Converts them to the new aliases format
3. Tests the new system against your problematic cases
4. Shows you how to integrate it into your existing codebase

This preserves all your manual curation work while building a scalable foundation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests.artist_resolver import ArtistResolver, migrate_known_patterns_to_aliases
from lastfm_utils import LastfmAPI
from config_loader import AppConfig

def extract_known_patterns_from_lastfm_utils():
    """Extract the known patterns from your existing code."""
    # This is the data from your lastfm_utils.py _get_known_artist_patterns method
    known_patterns = {
        # K-pop groups
        'IVE': ['IVE (아이브)', '아이브'],
        'TWICE': ['TWICE (트와이스)', '트와이스'],
        'BLACKPINK': ['BLACKPINK (블랙핑크)', '블랙핑크'],
        'BTS': ['BTS (방탄소년단)', '방탄소년단'],
        'STRAY KIDS': ['Stray Kids (스트레이 키즈)', '스트레이 키즈'],
        'NEWJEANS': ['NewJeans (뉴진스)', '뉴진스'],
        'LE SSERAFIM': ['LE SSERAFIM (르세라핌)', '르세라핌'],
        'AESPA': ['aespa (에스파)', '에스파'],
        'ITZY': ['ITZY (있지)', '있지'],
        '(G)I-DLE': ['(G)I-DLE ((여자)아이들)', '(여자)아이들'],
        'SEVENTEEN': ['SEVENTEEN (세븐틴)', '세븐틴'],
        'ENHYPEN': ['ENHYPEN (엔하이픈)', '엔하이픈'],
        'TXT': ['TXT (투모로우바이투게더)', 'TOMORROW X TOGETHER', 'TOP'],
        'ARTMS': ['ARTMS (아르테미스)', '아르테미스'],
        'ILLIT': ['ILLIT (아일릿)', '아일릿'],
        
        # K-pop soloists
        'ANYUJIN': ['An Yujin', 'ANYUJIN (IVE)', 'Ahn Yujin', 'Ahn Yu-jin'],
        'JEON SOMI': ['SOMI', 'Somi'],
        'KISS OF LIFE': ['KOL', 'Kiss Of Life'],
        'SUNMI': ['Lee Sun-mi', 'SUNMI (선미)', '선미'],
        'MIYEON': ['Cho Mi-yeon', '미연', 'MIYEON ((G)I-DLE)', 'Mi-yeon'],
        
        # Japanese artists
        'AIMYON': ['Aimyon', 'あいみょん', 'aimyon'],
        'YOASOBI': ['YOASOBI (ヨアソビ)', 'ヨアソビ', 'yoasobi'],
        'ヨルシカ': ['Yorushika', 'YORUSHIKA'],
        'YORUSHIKA': ['ヨルシカ', 'Yorushika'],
        'ユイカ': ['YUIKA', 'Yuika', 'yuika'],
        'YUIKA': ['ユイカ', 'Yuika', 'yuika'],
        
        # Western artists with common issues
        'TWENTY ONE PILOTS': ['twenty one pilots', 'TOP', '21 Pilots', 'Twenty One Pilots'],
        'BRING ME THE HORIZON': ['BMTH', 'Bring Me the Horizon'],
        'LINKIN PARK': ['Linkin Park', 'LP'],
        'MY CHEMICAL ROMANCE': ['MCR', 'My Chemical Romance'],
        'FALL OUT BOY': ['FOB', 'Fall Out Boy'],
        'PANIC! AT THE DISCO': ['P!ATD', 'Panic at the Disco', 'Panic! At The Disco'],
        
        # Artists with special characters
        'P!NK': ['Pink', 'P!nk'],
        'KE$HA': ['Kesha', 'Ke$ha'],
        'BBNO$': ['bbno$', 'BBNO$', 'Baby No Money'],
        
        # Hip-hop/Rap artists
        'MGK': ['Machine Gun Kelly', 'MGK', 'mgk'],
        'MACHINE GUN KELLY': ['Machine Gun Kelly', 'MGK'],
        'XXXTENTACION': ['XXXTentacion', 'xxxtentacion', 'XXXTENTACION'],
        'BLACKBEAR': ['blackbear', 'Blackbear', 'black bear'],
        'BOYWITHUKE': ['BoyWithUke', 'boy with uke', 'Boy with Uke'],
        
        # Common abbreviation patterns
        'LIL WAYNE': ['Lil Wayne', 'lil wayne'],
        'LIL PEEP': ['Lil Peep', 'lil peep'],
        'A$AP ROCKY': ['ASAP Rocky', 'A$AP Rocky'],
        '21 SAVAGE': ['21 Savage', '21savage'],
        'NBA YOUNGBOY': ['YoungBoy Never Broke Again', 'NBA YoungBoy'],
        'JUICE WRLD': ['Juice WRLD', 'JuiceWRLD'],
        
        # Hip-hop collectives & labels
        '88RISING': ['88rising', '88 Rising', 'eighty eight rising'],
    }
    
    return known_patterns

def test_new_system_vs_old():
    """Test the new system against your specific problematic cases."""
    print("=" * 80)
    print("TESTING NEW ROBUST SYSTEM VS OLD BANDAID FIXES")
    print("=" * 80)
    
    # Initialize new resolver
    resolver = ArtistResolver()
    
    # Test cases that were problematic
    test_cases = [
        "ユイカ",                          # Japanese false positive issue
        "blackbear",                      # Popular artist not found
        "BoyWithUke (with blackbear)",    # Collaboration parsing
        "IDGAF (with blackbear)",         # Your specific track example
        "Taylor Swift feat. Ed Sheeran",  # Common collaboration pattern
        "88rising",                       # Another problematic one
        "MIYEON",                         # Another problematic one
    ]
    
    # Mock music library (in real usage, this comes from your Spotify data)
    mock_library = [
        "YUIKA", "ユイカ", "blackbear", "BoyWithUke", "Taylor Swift", 
        "Ed Sheeran", "88rising", "MIYEON", "Cho Mi-yeon", "미연"
    ]
    
    print("🧪 Testing collaboration splitting and resolution:")
    print("-" * 60)
    
    for test_case in test_cases:
        print(f"\n📝 Input: '{test_case}'")
        
        # Step 1: Split collaborations
        artists = resolver.split_collaborations(test_case)
        print(f"   Split into: {artists}")
        
        # Step 2: Resolve each artist
        for artist in artists:
            result = resolver.resolve_artist(artist, mock_library)
            if result:
                print(f"   ✅ '{artist}' -> '{result.artist_name}' "
                      f"(confidence: {result.confidence:.3f}, method: {result.method})")
            else:
                print(f"   ❌ '{artist}' -> No match found")

def show_migration_benefits():
    """Show the benefits of the new system."""
    print("\n" + "=" * 80)
    print("BENEFITS OF THE NEW ROBUST SYSTEM")
    print("=" * 80)
    
    benefits = [
        "✅ SCALABLE: No more manual pattern additions for each new artist",
        "✅ CONFIDENCE SCORING: Know how reliable each match is",
        "✅ COLLABORATION HANDLING: Robust parsing of complex patterns",
        "✅ UNICODE AWARE: Proper handling of international characters",
        "✅ PERFORMANCE: Cascading from fast exact matches to slower fuzzy",
        "✅ SELF-IMPROVING: Human review queue for learning from failures",
        "✅ PRESERVES CURATION: Your existing manual work becomes aliases",
        "✅ DEBUGGABLE: Clear methods and confidence scores for troubleshooting",
    ]
    
    for benefit in benefits:
        print(benefit)
    
    print("\n📊 OLD SYSTEM PROBLEMS:")
    problems = [
        "❌ Manual pattern database (doesn't scale)",
        "❌ Boolean matching (no confidence measure)", 
        "❌ Complex collaboration parsing in multiple places",
        "❌ Unicode issues with .lower() vs .casefold()",
        "❌ Hard to debug when matches fail",
        "❌ Reactive fixes for each new problematic artist",
    ]
    
    for problem in problems:
        print(problem)

def integration_guide():
    """Show how to integrate the new system."""
    print("\n" + "=" * 80)
    print("INTEGRATION GUIDE")
    print("=" * 80)
    
    print("""
🔧 TO INTEGRATE THE NEW SYSTEM:

1. Install dependencies:
   pip install rapidfuzz  # For fast fuzzy matching

2. Migrate existing patterns:
   python migrate_to_robust_system.py --migrate

3. Update your main processing code:
   
   # OLD WAY (in network_utils.py or wherever you call lastfm):
   similar_artists = lastfm_api.get_similar_artists(artist_name=artist)
   
   # NEW WAY:
   from artist_resolver import ArtistResolver
   resolver = ArtistResolver()
   
   # For each artist in your data:
   artists = resolver.split_collaborations(raw_artist_string)
   for artist in artists:
       result = resolver.resolve_artist(artist, your_music_library)
       if result and result.confidence > 0.85:
           # Use the resolved artist
           similar_artists = lastfm_api.get_similar_artists(result.artist_name)

4. Benefits you'll see immediately:
   - Better collaboration handling
   - Fewer false positives
   - Confidence scores for debugging
   - No more manual pattern additions

5. Long-term improvements:
   - Review the artist_review_queue.csv periodically
   - Add confirmed matches as aliases
   - System becomes more accurate over time
""")

def main():
    """Main migration and testing function."""
    print("🚀 MIGRATION FROM BANDAID FIXES TO ROBUST ARTIST RESOLUTION")
    print("=" * 80)
    
    if "--migrate" in sys.argv:
        # Actually perform the migration
        print("📦 Migrating known patterns to aliases format...")
        known_patterns = extract_known_patterns_from_lastfm_utils()
        migrate_known_patterns_to_aliases(known_patterns, "artist_aliases.json")
        print(f"✅ Migrated {len(known_patterns)} pattern groups to aliases")
        return
    
    # Run tests and show benefits
    test_new_system_vs_old()
    show_migration_benefits()
    integration_guide()
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("1. Run: python migrate_to_robust_system.py --migrate")
    print("2. Install: pip install rapidfuzz")
    print("3. Test: python artist_resolver.py")
    print("4. Integrate into your main processing pipeline")
    print("\nThis will give you a truly robust, scalable solution!")

if __name__ == "__main__":
    main()