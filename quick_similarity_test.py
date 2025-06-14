#!/usr/bin/env python3
"""
Quick Similarity Test
====================
Fast test for specific artist similarity issues
"""

import sys
from pathlib import Path

# Add project modules
sys.path.insert(0, str(Path(__file__).parent))

def quick_test_specific_cases():
    """Test the specific cases you mentioned"""
    
    print("🔍 Quick Similarity Test")
    print("=" * 30)
    
    # Import our modules
    try:
        from lastfm_utils import LastfmAPI
        from config_loader import AppConfig
    except ImportError as e:
        print(f"❌ Could not import modules: {e}")
        print("Make sure you're in the project root directory")
        return
    
    # Load config
    try:
        config = AppConfig("configurations.txt")
        lastfm_config = config.get_lastfm_config()
        
        if not lastfm_config['enabled'] or not lastfm_config['api_key']:
            print("❌ Last.fm API not configured")
            return
        
        api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'], 
            lastfm_config['cache_dir']
        )
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Test cases you mentioned
    test_cases = [
        ("TWICE", "IU", "K-pop connection expected"),
        ("Paramore", "Tonight Alive", "Rock/pop-punk connection expected"),
        ("IU", "TWICE", "Reverse K-pop test"),
        ("Tonight Alive", "Paramore", "Reverse rock test")
    ]
    
    print(f"Testing {len(test_cases)} problematic cases...\n")
    
    for artist_a, artist_b, description in test_cases:
        print(f"🎯 {artist_a} → {artist_b} ({description})")
        
        try:
            # Get similar artists for A
            similar_to_a = api.get_similar_artists(artist_a, limit=50)
            
            # Check if B is in A's similar artists
            found = False
            similarity_score = 0.0
            
            for similar in similar_to_a:
                if similar['name'].lower() == artist_b.lower() or artist_b.lower() in similar['name'].lower():
                    found = True
                    similarity_score = similar['match']
                    break
            
            if found:
                print(f"   ✅ Found! Similarity: {similarity_score:.3f}")
            else:
                print(f"   ❌ NOT FOUND")
                print(f"   📝 Top 5 similar to {artist_a}:")
                for i, similar in enumerate(similar_to_a[:5], 1):
                    print(f"      {i}. {similar['name']} ({similar['match']:.3f})")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
    
    print("💡 If connections are missing, try the full debug suite:")
    print("   python similarity_debug_suite.py")

if __name__ == "__main__":
    quick_test_specific_cases()