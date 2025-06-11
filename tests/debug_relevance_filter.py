"""
Debug Relevance Filter
======================

Debug why blackbear is matching Blackbeard.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PARENT_DIR, 'configurations.txt')


def test_relevance_filter():
    """Test the relevance filter logic."""
    print("=" * 60)
    print("TESTING RELEVANCE FILTER")
    print("=" * 60)
    
    try:
        config = AppConfig(CONFIG_PATH)
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test specific relevance cases
        test_cases = [
            ('blackbear', 'Blackbear', 'Should match - exact'),
            ('blackbear', 'Blackbeard', 'Should NOT match - different artist'),
            ('blackbear', "Blackbeard's Tea Party", 'Should NOT match - different'),
            ('blackbear', 'Machine Gun Kelly & Blackbear', 'Should match - collaboration'),
            ('blackbear', 'BoyWithUke, blackbear', 'Should match - collaboration'),
            ('XXXTENTACION', 'xxxtentacion', 'Should match - case'),
            ('XXXTENTACION', 'Xxxtentacion, Trippie Redd', 'Should match - collaboration'),
            ('XXXTENTACION', 'lil peep & XXXTentacion', 'Should match - collaboration'),
        ]
        
        print(f"\nTesting relevance filter logic:")
        print("-" * 60)
        
        for original, candidate, expected in test_cases:
            is_relevant = lastfm_api._is_relevant_artist_match(original, candidate)
            status = "✅ PASS" if ("Should match" in expected) == is_relevant else "❌ FAIL"
            
            print(f"{status} '{original}' vs '{candidate}'")
            print(f"     Expected: {expected}")
            print(f"     Result: {'Relevant' if is_relevant else 'Not relevant'}")
            print()
        
        # Test actual search results for blackbear
        print("\n" + "=" * 60)
        print("TESTING BLACKBEAR SEARCH RESULTS")
        print("=" * 60)
        
        params = {'artist': 'blackbear', 'limit': '10'}
        response = lastfm_api._make_request('artist.search', params)
        
        if response and 'results' in response:
            matches = response['results'].get('artistmatches', {}).get('artist', [])
            if isinstance(matches, dict):
                matches = [matches]
            
            print(f"\nFound {len(matches)} search results:")
            
            relevant_matches = []
            for i, match in enumerate(matches[:8], 1):
                name = match.get('name', '')
                listeners = int(match.get('listeners', 0))
                
                is_relevant = lastfm_api._is_relevant_artist_match('blackbear', name)
                relevance = "✅ RELEVANT" if is_relevant else "❌ IRRELEVANT"
                
                print(f"\n{i}. '{name}' ({listeners:,} listeners)")
                print(f"   {relevance}")
                
                if is_relevant:
                    relevant_matches.append((name, listeners))
            
            print(f"\nRelevant matches found: {len(relevant_matches)}")
            for name, listeners in relevant_matches:
                print(f"   - '{name}' ({listeners:,} listeners)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_relevance_filter()