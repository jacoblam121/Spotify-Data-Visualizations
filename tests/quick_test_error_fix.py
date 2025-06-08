#!/usr/bin/env python3
"""
Quick test to verify that the original AttributeError has been fixed.

This test specifically checks that most_played_track is now properly stored as a dictionary.
"""

import os
import tempfile
from config_loader import AppConfig
from data_processor import clean_and_filter_data, prepare_data_for_bar_chart_race

def create_test_config():
    """Create a test configuration file for artists mode"""
    config_content = """
[DataSource]
SOURCE = lastfm
INPUT_FILENAME_LASTFM = lastfm_data.csv

[VisualizationMode]
MODE = artists

[ArtistArt]
ARTIST_ART_CACHE_DIR = artist_art_cache
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(config_content)
        return f.name

def test_original_error_fix():
    """Test that the original AttributeError is now fixed"""
    print("Testing original AttributeError fix...")
    
    config_path = create_test_config()
    try:
        # Load configuration and data
        config = AppConfig(filepath=config_path)
        cleaned_data = clean_and_filter_data(config)
        
        print(f"✓ Loaded {len(cleaned_data)} rows of Last.fm data")
        
        # Process data in artists mode
        race_df, artist_details = prepare_data_for_bar_chart_race(cleaned_data, mode="artists")
        
        print(f"✓ Processed {len(artist_details)} artists successfully")
        
        # Check that most_played_track is now a dictionary
        sample_artist = list(artist_details.keys())[0]
        artist_info = artist_details[sample_artist]
        most_played_track = artist_info['most_played_track']
        
        # This was the original error - most_played_track was a string instead of dict
        assert isinstance(most_played_track, dict), f"most_played_track should be dict, got {type(most_played_track)}"
        assert 'track_name' in most_played_track, "Missing 'track_name' key"
        assert 'album_name' in most_played_track, "Missing 'album_name' key"
        
        print(f"✓ most_played_track is now properly formatted as dictionary: {most_played_track}")
        
        # Test that it has .get() method (which was failing before)
        track_name = most_played_track.get('track_name', 'Unknown Track')
        album_name = most_played_track.get('album_name', 'Unknown Album')
        
        print(f"✓ Dictionary access works: track='{track_name}', album='{album_name}'")
        
        print("\n🎉 Original AttributeError has been FIXED!")
        print("✅ most_played_track is now stored as a dictionary with proper structure")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        try:
            os.unlink(config_path)
        except:
            pass

if __name__ == "__main__":
    print("=" * 60)
    print("QUICK TEST: ORIGINAL ATTRIBUTEERROR FIX VERIFICATION")
    print("=" * 60)
    
    success = test_original_error_fix()
    
    if success:
        print("\n✅ SUCCESS: The original error has been completely fixed!")
    else:
        print("\n❌ FAILURE: The original error still exists.")
    
    exit(0 if success else 1)