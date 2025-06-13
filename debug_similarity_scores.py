#!/usr/bin/env python3
"""
Debug script to check raw Last.fm similarity scores vs what we're processing.
"""

from config_loader import AppConfig
from lastfm_utils import LastfmAPI
import json

def debug_similarity_scores():
    """Check raw Last.fm API responses vs processed data."""
    print("🔍 Debugging Last.fm Similarity Scores")
    print("=" * 50)
    
    # Initialize API
    config = AppConfig('configurations.txt')
    lastfm_config = config.get_lastfm_config()
    
    lastfm_api = LastfmAPI(
        lastfm_config['api_key'],
        lastfm_config['api_secret'],
        lastfm_config['cache_dir']
    )
    
    # Test with a popular artist
    test_artist = "Taylor Swift"
    print(f"Testing with: {test_artist}")
    print()
    
    # Get similar artists and examine scores
    similar_artists = lastfm_api.get_similar_artists(test_artist, limit=10)
    
    if similar_artists:
        print("📊 Similarity Scores from Last.fm:")
        print("   Artist Name                | Score   | Description")
        print("   " + "-" * 55)
        
        for i, artist in enumerate(similar_artists, 1):
            score = artist['match']
            description = get_score_description(score)
            print(f"   {i:2d}. {artist['name']:<20} | {score:.3f}  | {description}")
        
        print()
        print("🎯 Score Analysis:")
        scores = [artist['match'] for artist in similar_artists]
        print(f"   Range: {min(scores):.3f} - {max(scores):.3f}")
        print(f"   Average: {sum(scores)/len(scores):.3f}")
        
        # Check if any scores are above 0.6 (strong similarity)
        strong_scores = [s for s in scores if s > 0.6]
        print(f"   Strong similarities (>0.6): {len(strong_scores)}")
        
        if len(strong_scores) == 0:
            print("   ⚠️  No strong similarities found - this might be the issue!")
    else:
        print("❌ No similar artists found")

def get_score_description(score):
    """Get human-readable description of similarity score."""
    if score >= 0.8:
        return "Very High"
    elif score >= 0.6:
        return "High"
    elif score >= 0.4:
        return "Medium"
    elif score >= 0.2:
        return "Low"
    else:
        return "Very Low"

if __name__ == "__main__":
    debug_similarity_scores()