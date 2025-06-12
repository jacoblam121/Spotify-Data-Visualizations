#!/usr/bin/env python3
"""
Manual API Configuration Test Script
Tests all API configurations and shows which source is being used (.env vs configurations.txt)
"""

import os
from config_loader import AppConfig
from dotenv import load_dotenv

def test_api_configurations():
    """Test all API configurations and show sources."""
    print("🔧 API Configuration Test")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    config = AppConfig('configurations.txt')
    
    # Test Spotify API
    print("\n🎵 SPOTIFY API:")
    spotify_config = config.get_spotify_config()
    
    env_id = os.getenv('SPOTIFY_CLIENT_ID')
    config_id = config.get('AlbumArtSpotify', 'SPOTIFY_CLIENT_ID', '')
    
    print(f"  Client ID: {spotify_config['client_id'][:10]}..." if spotify_config['client_id'] else "  Client ID: NOT SET")
    print(f"  Source: {'🔒 .env file' if env_id else '📄 configurations.txt' if config_id else '❌ Not found'}")
    
    env_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    config_secret = config.get('AlbumArtSpotify', 'SPOTIFY_CLIENT_SECRET', '')
    
    print(f"  Client Secret: {spotify_config['client_secret'][:10]}..." if spotify_config['client_secret'] else "  Client Secret: NOT SET")
    print(f"  Source: {'🔒 .env file' if env_secret else '📄 configurations.txt' if config_secret else '❌ Not found'}")
    
    # Test Last.fm API
    print("\n🎶 LAST.FM API:")
    lastfm_config = config.get_lastfm_config()
    
    env_key = os.getenv('LASTFM_API_KEY')
    config_key = config.get('LastfmAPI', 'API_KEY', '')
    
    print(f"  API Key: {lastfm_config['api_key'][:10]}..." if lastfm_config['api_key'] else "  API Key: NOT SET")
    print(f"  Source: {'🔒 .env file' if env_key else '📄 configurations.txt' if config_key else '❌ Not found'}")
    
    env_secret = os.getenv('LASTFM_API_SECRET')
    config_secret = config.get('LastfmAPI', 'API_SECRET', '')
    
    print(f"  API Secret: {lastfm_config['api_secret'][:10]}..." if lastfm_config['api_secret'] else "  API Secret: NOT SET")
    print(f"  Source: {'🔒 .env file' if env_secret else '📄 configurations.txt' if config_secret else '❌ Not found'}")
    print(f"  Enabled: {lastfm_config['enabled']}")
    
    # Test MusicBrainz API
    print("\n🎼 MUSICBRAINZ API:")
    mb_config = config.get_musicbrainz_config()
    
    print(f"  Enabled: {mb_config['enabled']}")
    print(f"  User Agent: {mb_config['user_agent']}")
    print("  Note: MusicBrainz doesn't require API keys, only rate limiting")
    
    # Test actual API connections
    print("\n🌐 TESTING API CONNECTIONS:")
    
    # Test Last.fm
    try:
        from lastfm_utils import LastfmAPI
        if lastfm_config['api_key']:
            lastfm = LastfmAPI(lastfm_config['api_key'], lastfm_config['api_secret'], lastfm_config['cache_dir'])
            test_result = lastfm.get_similar_artists("Radiohead", limit=3)
            if test_result:
                print(f"  ✅ Last.fm: Working - found {len(test_result)} similar artists")
            else:
                print("  ❌ Last.fm: API call failed")
        else:
            print("  ⚠️  Last.fm: API key not configured")
    except Exception as e:
        print(f"  ❌ Last.fm: Error - {e}")
    
    # Test Spotify (basic import test)
    try:
        from album_art_utils import get_spotify_artist_info
        if spotify_config['client_id']:
            print("  ✅ Spotify: Configuration loaded (run full test to verify API)")
        else:
            print("  ⚠️  Spotify: Client ID not configured")
    except Exception as e:
        print(f"  ❌ Spotify: Error importing - {e}")
    
    print("\n📋 CONFIGURATION SUMMARY:")
    print(f"  • Spotify: {'✅ Configured' if spotify_config['client_id'] else '❌ Missing'}")
    print(f"  • Last.fm: {'✅ Configured' if lastfm_config['api_key'] else '❌ Missing'}")
    print(f"  • MusicBrainz: {'✅ Enabled' if mb_config['enabled'] else '❌ Disabled'}")
    
    # Test network validation capability
    print("\n🕸️  NETWORK VALIDATION TEST:")
    try:
        from validate_graph import validate_artist_network
        print("  ✅ Network validation script available")
        print("  💡 Run: python validate_graph.py 10 0.08")
    except Exception as e:
        print(f"  ❌ Network validation error: {e}")
    
    print("\n🎯 MANUAL TEST FRAMEWORK:")
    try:
        from test_network_visualization import NetworkVisualizationTester
        print("  ✅ Manual test framework available")
        print("  💡 Run: python test_network_visualization.py")
    except Exception as e:
        print(f"  ❌ Test framework error: {e}")


if __name__ == "__main__":
    test_api_configurations()