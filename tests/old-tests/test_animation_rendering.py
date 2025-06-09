#!/usr/bin/env python3
"""
Test script to verify that animation rendering works in artist mode
without the 'song_id' KeyError.
"""

import os
import sys
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

[AnimationOutput]
OUTPUT_WIDTH = 640
OUTPUT_HEIGHT = 480
FPS = 2
FRAME_AGGREGATION_PERIOD = W
N_BARS = 5

[ArtistArt]
ARTIST_ART_CACHE_DIR = artist_art_cache

[AlbumArtSpotify]
CLIENT_ID = test_client_id
CLIENT_SECRET = test_client_secret
CACHE_DIR = album_art_cache

[Timeframe]
START_DATE = 2024-01-01
END_DATE = 2024-01-31
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(config_content)
        return f.name

def test_animation_rendering():
    """Test that animation rendering works without song_id errors"""
    print("Testing animation rendering in artist mode...")
    
    config_path = create_test_config()
    
    try:
        # Load configuration and data
        config = AppConfig(filepath=config_path)
        
        # Set up a temporary directory for test frames
        test_frames_dir = "/tmp/test_frames_animation"
        if os.path.exists(test_frames_dir):
            import shutil
            shutil.rmtree(test_frames_dir)
        
        print("✓ Configuration loaded")
        
        # Import main_animator after config is ready
        import main_animator
        
        # Override some globals for testing
        main_animator.VISUALIZATION_MODE = "artists"
        main_animator.TEMP_FRAMES_DIR = test_frames_dir
        main_animator.MAX_PARALLEL_WORKERS = 1  # Single process for easier debugging
        
        print("✓ Main animator imported and configured")
        
        # Load and process data
        cleaned_data = clean_and_filter_data(config)
        race_df, artist_details = prepare_data_for_bar_chart_race(cleaned_data, mode="artists")
        
        print(f"✓ Data processed: {len(artist_details)} artists")
        
        # Try to generate just a few render tasks
        timestamps_for_animation = race_df.index[:3]  # Just first 3 timestamps
        
        # Create minimal rolling stats and nightingale data
        rolling_stats_data = {}
        nightingale_data = {}
        
        # Call the generate_render_tasks function
        render_tasks = main_animator.generate_render_tasks(
            race_df.iloc[:3],  # Just first 3 rows
            5,  # N_BARS
            2,   # TARGET_FPS
            0.5,  # TRANSITION_DURATION_SECONDS
            rolling_stats_data,
            nightingale_data
        )
        
        print(f"✓ Generated {len(render_tasks)} render tasks")
        
        # Test the first render task to see if it has the right structure
        if render_tasks:
            test_task = render_tasks[0]
            bar_data = test_task.get('bar_render_data_list', [])
            
            print(f"✓ First render task has {len(bar_data)} bars")
            
            if bar_data:
                # Check if the first bar has 'entity_id' instead of 'song_id'
                first_bar = bar_data[0]
                if 'entity_id' in first_bar:
                    print("✓ Bar data uses 'entity_id' (correct for both modes)")
                elif 'song_id' in first_bar:
                    print("❌ Bar data still uses 'song_id' (needs fixing)")
                    return False
                else:
                    print("❌ Bar data missing both 'entity_id' and 'song_id'")
                    return False
        
        print("\n🎉 Animation rendering structure test PASSED!")
        print("✅ The 'song_id' KeyError should now be fixed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            os.unlink(config_path)
        except:
            pass

if __name__ == "__main__":
    print("=" * 60)
    print("ANIMATION RENDERING TEST - ARTIST MODE")
    print("=" * 60)
    
    success = test_animation_rendering()
    
    if success:
        print("\n✅ SUCCESS: Animation rendering structure is correct for artist mode!")
    else:
        print("\n❌ FAILURE: Animation rendering still has issues.")
    
    sys.exit(0 if success else 1)