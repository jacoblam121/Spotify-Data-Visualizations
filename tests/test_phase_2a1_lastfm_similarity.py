"""
Phase 2A.1: Test Last.fm API with Your Artists
==============================================

This script extracts your top artists from listening data and tests
Last.fm similarity API calls to verify we get meaningful connections.

Goal: Verify Last.fm similarity API works with your real artist data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
from config_loader import AppConfig
from data_processor import clean_and_filter_data
from network_utils import prepare_dataframe_for_network_analysis
from lastfm_utils import LastfmAPI


def print_separator(title, char="=", width=70):
    """Print a formatted separator."""
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}")


def get_top_artists_from_data(config, top_n=25):
    """
    Extract top N artists from user's listening data.
    
    Returns both Spotify and Last.fm top artists for comparison.
    """
    print_separator("EXTRACTING TOP ARTISTS FROM YOUR DATA")
    
    results = {}
    original_source = config.get('DataSource', 'SOURCE', fallback='spotify')
    
    # Get Spotify top artists
    try:
        config.config['DataSource']['SOURCE'] = 'spotify'
        print("📊 Loading Spotify data...")
        
        df_spotify = clean_and_filter_data(config)
        if df_spotify is not None and not df_spotify.empty:
            # Count plays per artist
            artist_counts = df_spotify.groupby('artist').size().sort_values(ascending=False)
            spotify_top = artist_counts.head(top_n)
            
            print(f"✅ Spotify: {len(df_spotify)} plays, {len(artist_counts)} unique artists")
            print(f"📈 Top {len(spotify_top)} artists by play count:")
            
            for i, (artist, plays) in enumerate(spotify_top.head(10).items(), 1):
                # Get original case for display
                original_artist = df_spotify[df_spotify['artist'] == artist]['original_artist'].iloc[0]
                print(f"   {i:2d}. {original_artist}: {plays} plays")
            
            if len(spotify_top) > 10:
                print(f"   ... and {len(spotify_top) - 10} more")
            
            results['spotify'] = {
                'artists': spotify_top,
                'total_plays': len(df_spotify),
                'original_names': df_spotify.drop_duplicates('artist').set_index('artist')['original_artist'].to_dict()
            }
        else:
            print("❌ No Spotify data available")
            results['spotify'] = None
            
    except Exception as e:
        print(f"❌ Error loading Spotify data: {e}")
        results['spotify'] = None
    
    # Get Last.fm top artists
    try:
        config.config['DataSource']['SOURCE'] = 'lastfm'
        print("\n📊 Loading Last.fm data...")
        
        df_lastfm = clean_and_filter_data(config)
        if df_lastfm is not None and not df_lastfm.empty:
            # Count plays per artist
            artist_counts = df_lastfm.groupby('artist').size().sort_values(ascending=False)
            lastfm_top = artist_counts.head(top_n)
            
            print(f"✅ Last.fm: {len(df_lastfm)} plays, {len(artist_counts)} unique artists")
            print(f"📈 Top {len(lastfm_top)} artists by play count:")
            
            for i, (artist, plays) in enumerate(lastfm_top.head(10).items(), 1):
                # Get original case for display
                original_artist = df_lastfm[df_lastfm['artist'] == artist]['original_artist'].iloc[0]
                print(f"   {i:2d}. {original_artist}: {plays} plays")
            
            if len(lastfm_top) > 10:
                print(f"   ... and {len(lastfm_top) - 10} more")
            
            results['lastfm'] = {
                'artists': lastfm_top,
                'total_plays': len(df_lastfm),
                'original_names': df_lastfm.drop_duplicates('artist').set_index('artist')['original_artist'].to_dict()
            }
        else:
            print("❌ No Last.fm data available")
            results['lastfm'] = None
            
    except Exception as e:
        print(f"❌ Error loading Last.fm data: {e}")
        results['lastfm'] = None
    
    # Restore original source
    config.config['DataSource']['SOURCE'] = original_source
    
    # Compare and get combined top artists
    if results['spotify'] and results['lastfm']:
        print_separator("COMPARING DATA SOURCES")
        
        spotify_artists = set(results['spotify']['artists'].index)
        lastfm_artists = set(results['lastfm']['artists'].index)
        
        overlap = spotify_artists.intersection(lastfm_artists)
        print(f"🔗 Artist overlap: {len(overlap)} artists appear in both sources")
        print(f"   Spotify only: {len(spotify_artists - lastfm_artists)}")
        print(f"   Last.fm only: {len(lastfm_artists - spotify_artists)}")
        
        # Create combined list (use Spotify as primary source)
        combined_artists = results['spotify']['artists'].copy()
        for artist in lastfm_artists - spotify_artists:
            if len(combined_artists) < top_n:
                combined_artists[artist] = results['lastfm']['artists'][artist]
        
        results['combined'] = combined_artists
        
    elif results['spotify']:
        results['combined'] = results['spotify']['artists']
    elif results['lastfm']:
        results['combined'] = results['lastfm']['artists']
    else:
        results['combined'] = pd.Series(dtype=int)
    
    return results


def test_lastfm_api_setup():
    """Test Last.fm API configuration and basic functionality."""
    print_separator("TESTING LAST.FM API SETUP")
    
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        print("📋 Last.fm Configuration:")
        print(f"   Enabled: {lastfm_config.get('enabled', False)}")
        print(f"   API Key: {'Set' if lastfm_config.get('api_key') else 'Missing'}")
        print(f"   API Secret: {'Set' if lastfm_config.get('api_secret') else 'Missing'}")
        print(f"   Cache Dir: {lastfm_config.get('cache_dir', 'Default')}")
        
        if not lastfm_config.get('enabled'):
            print("❌ Last.fm is disabled in configuration")
            return None
        
        if not lastfm_config.get('api_key'):
            print("❌ Last.fm API key is missing")
            return None
        
        # Initialize API
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'], 
            lastfm_config['cache_dir']
        )
        
        print("✅ Last.fm API initialized successfully")
        
        # Test with a well-known artist
        print("\n🧪 Testing API with sample artist: 'Taylor Swift'...")
        similar_artists = lastfm_api.get_similar_artists('Taylor Swift', limit=10)
        
        if similar_artists:
            print(f"✅ API test successful! Found {len(similar_artists)} similar artists:")
            for i, artist in enumerate(similar_artists[:5], 1):
                print(f"   {i}. {artist['name']}: {artist['match']:.3f}")
        else:
            print("❌ API test failed - no results returned")
            return None
        
        return lastfm_api
        
    except Exception as e:
        print(f"❌ Error setting up Last.fm API: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_similarity_with_your_artists(lastfm_api, top_artists_data, max_test_artists=10):
    """Test Last.fm similarity API with your actual top artists."""
    print_separator("TESTING SIMILARITY WITH YOUR TOP ARTISTS")
    
    if not lastfm_api:
        print("❌ Last.fm API not available")
        return {}
    
    # Get artists to test (use combined list or Spotify)
    if 'combined' in top_artists_data and len(top_artists_data['combined']) > 0:
        test_artists = top_artists_data['combined'].head(max_test_artists)
        original_names = top_artists_data.get('spotify', {}).get('original_names', {})
    elif top_artists_data.get('spotify'):
        test_artists = top_artists_data['spotify']['artists'].head(max_test_artists)
        original_names = top_artists_data['spotify']['original_names']
    else:
        print("❌ No artist data available for testing")
        return {}
    
    print(f"🎵 Testing similarity API with your top {len(test_artists)} artists...")
    
    similarity_results = {}
    successful_calls = 0
    failed_calls = 0
    
    for i, (artist_normalized, play_count) in enumerate(test_artists.items(), 1):
        # Get original case name for API call
        original_name = original_names.get(artist_normalized, artist_normalized)
        
        print(f"\n{i:2d}. Testing: {original_name} ({play_count} plays)")
        
        try:
            similar_artists = lastfm_api.get_similar_artists(original_name, limit=15)
            
            if similar_artists:
                print(f"    ✅ Found {len(similar_artists)} similar artists:")
                
                # Show top 5 similar artists
                for j, similar in enumerate(similar_artists[:5], 1):
                    print(f"       {j}. {similar['name']}: {similar['match']:.3f}")
                
                similarity_results[artist_normalized] = {
                    'original_name': original_name,
                    'play_count': play_count,
                    'similar_artists': similar_artists,
                    'similarity_count': len(similar_artists)
                }
                successful_calls += 1
                
            else:
                print(f"    ❌ No similar artists found")
                failed_calls += 1
                
        except Exception as e:
            print(f"    ❌ API call failed: {e}")
            failed_calls += 1
    
    print_separator("SIMILARITY TEST SUMMARY")
    print(f"📊 API Call Results:")
    print(f"   Successful: {successful_calls}/{len(test_artists)}")
    print(f"   Failed: {failed_calls}/{len(test_artists)}")
    print(f"   Success rate: {successful_calls/len(test_artists)*100:.1f}%")
    
    if similarity_results:
        print(f"\n🔗 Similarity Overview:")
        for artist, data in list(similarity_results.items())[:5]:
            print(f"   {data['original_name']}: {data['similarity_count']} similar artists")
    
    return similarity_results


def analyze_similarity_patterns(similarity_results):
    """Analyze patterns in the similarity results."""
    print_separator("ANALYZING SIMILARITY PATTERNS")
    
    if not similarity_results:
        print("❌ No similarity results to analyze")
        return
    
    print("🔍 Looking for meaningful genre connections...")
    
    # Look for cross-references (mutual similarities)
    artist_names = set(similarity_results.keys())
    cross_references = []
    
    for artist1, data1 in similarity_results.items():
        similar_names = [s['name'].lower().strip() for s in data1['similar_artists']]
        
        for artist2 in artist_names:
            if artist1 != artist2:
                data2 = similarity_results[artist2]
                original2 = data2['original_name'].lower().strip()
                
                if original2 in similar_names:
                    # Find the similarity score
                    score = next((s['match'] for s in data1['similar_artists'] 
                                if s['name'].lower().strip() == original2), 0)
                    cross_references.append((artist1, artist2, score))
    
    if cross_references:
        print(f"✅ Found {len(cross_references)} cross-references in your artists!")
        print("🔗 Strong connections within your library:")
        
        # Sort by similarity score
        cross_references.sort(key=lambda x: x[2], reverse=True)
        
        for artist1, artist2, score in cross_references[:10]:
            data1 = similarity_results[artist1]
            data2 = similarity_results[artist2]
            print(f"   {data1['original_name']} ↔ {data2['original_name']}: {score:.3f}")
    else:
        print("⚠️  No cross-references found among your top artists")
        print("   This could mean:")
        print("   - Your taste spans many different genres")
        print("   - Need to test more artists")
        print("   - API returned different name formats")
    
    # Analyze similarity score distributions
    all_scores = []
    for data in similarity_results.values():
        all_scores.extend([s['match'] for s in data['similar_artists']])
    
    if all_scores:
        print(f"\n📊 Similarity Score Analysis ({len(all_scores)} total relationships):")
        print(f"   Average: {sum(all_scores)/len(all_scores):.3f}")
        print(f"   Max: {max(all_scores):.3f}")
        print(f"   Min: {min(all_scores):.3f}")
        
        # Score distribution
        high_scores = len([s for s in all_scores if s >= 0.7])
        med_scores = len([s for s in all_scores if 0.3 <= s < 0.7])
        low_scores = len([s for s in all_scores if s < 0.3])
        
        print(f"   High similarity (≥0.7): {high_scores}")
        print(f"   Medium similarity (0.3-0.7): {med_scores}")
        print(f"   Low similarity (<0.3): {low_scores}")


def main():
    """Main test function for Phase 2A.1."""
    print_separator("PHASE 2A.1: LAST.FM SIMILARITY API TEST", "=", 70)
    print("Testing Last.fm API with your top artists")
    print("Goal: Verify we get meaningful artist similarity connections")
    
    try:
        # Load configuration
        config = AppConfig('configurations.txt')
        
        # Step 1: Extract top artists from your data
        top_artists_data = get_top_artists_from_data(config, top_n=25)
        
        combined_data = top_artists_data.get('combined')
        if combined_data is None or len(combined_data) == 0:
            print("❌ No artist data available - cannot proceed")
            return
        
        # Step 2: Test Last.fm API setup
        lastfm_api = test_lastfm_api_setup()
        
        if not lastfm_api:
            print("❌ Last.fm API setup failed - cannot proceed")
            return
        
        # Step 3: Test similarity with your artists
        similarity_results = test_similarity_with_your_artists(
            lastfm_api, 
            top_artists_data, 
            max_test_artists=10  # Start with 10 for testing
        )
        
        # Step 4: Analyze patterns
        analyze_similarity_patterns(similarity_results)
        
        print_separator("PHASE 2A.1 COMPLETE", "=", 70)
        
        if similarity_results:
            print("✅ Phase 2A.1 successful!")
            print("✅ Last.fm API working with your artist data")
            print("✅ Similarity scores look reasonable")
            print("")
            print("🎯 Ready for Phase 2A.2: Build Similarity Matrix")
            print("   Goal: Create full similarity matrix for network creation")
        else:
            print("❌ Phase 2A.1 had issues - need to investigate")
            print("💡 Check API credentials and network connection")
        
    except Exception as e:
        print(f"❌ Unexpected error in Phase 2A.1: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Change to main directory for proper file access
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original directory
        os.chdir(original_dir)