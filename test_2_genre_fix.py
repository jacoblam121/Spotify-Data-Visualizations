#!/usr/bin/env python3
"""
Test 2-Genre Limit Fix
======================
Test that the network generation now properly limits to 2 genres.
"""

from network_utils import initialize_network_analyzer
import pandas as pd

def test_genre_limit_fix():
    """Test that the fix properly limits genres to 2."""
    print("🧪 TESTING 2-GENRE LIMIT FIX")
    print("=" * 50)
    
    # Load user data
    try:
        df = pd.read_csv('lastfm_data.csv', encoding='utf-8')
        print(f"✅ Loaded {len(df)} records")
    except Exception as e:
        print(f"❌ Could not load data: {e}")
        return
    
    # Initialize analyzer
    try:
        analyzer = initialize_network_analyzer()
        print("✅ Network analyzer initialized")
    except Exception as e:
        print(f"❌ Could not initialize analyzer: {e}")
        return
    
    # Generate small network to test
    print("\n🌐 Generating test network...")
    try:
        network_data = analyzer.create_network_data(
            df, 
            top_n_artists=10,  # Small test
            min_plays_threshold=50,
            min_similarity_threshold=0.2
        )
        
        if network_data and 'nodes' in network_data:
            print(f"✅ Generated network with {len(network_data['nodes'])} nodes")
            
            # Check for artists with > 2 genres
            print(f"\n🔍 CHECKING GENRE COUNTS:")
            print("-" * 40)
            
            max_genres_found = 0
            problem_artists = []
            
            for node in network_data['nodes']:
                artist_name = node.get('name', 'Unknown')
                primary = node.get('primary_genre', 'unknown')
                secondary = node.get('secondary_genres', [])
                
                total_genres = 1 + len(secondary)  # primary + secondary count
                max_genres_found = max(max_genres_found, total_genres)
                
                genre_str = f"{primary} + {secondary}" if secondary else primary
                print(f"  {artist_name}: {genre_str} ({total_genres} total)")
                
                if total_genres > 2:
                    problem_artists.append(artist_name)
            
            print(f"\n📊 RESULTS:")
            print(f"  Maximum genres found: {max_genres_found}")
            print(f"  Problem artists (>2 genres): {problem_artists}")
            
            if max_genres_found <= 2:
                print(f"  ✅ SUCCESS: All artists limited to 2 genres!")
            else:
                print(f"  ❌ ISSUE: Some artists have {max_genres_found} genres")
                
        else:
            print("❌ Failed to generate network")
            
    except Exception as e:
        print(f"❌ Error during network generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_genre_limit_fix()