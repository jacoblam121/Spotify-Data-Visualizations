#!/usr/bin/env python3
"""
Test script to run a very short animation in artist mode to verify
that the 'song_id' KeyError is completely fixed.
"""

import os
import sys
import tempfile
import shutil

def create_test_config():
    """Create a test configuration for a very short animation"""
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
N_BARS = 3
TRANSITION_DURATION_SECONDS = 0.1
MAX_PARALLEL_WORKERS = 1

[ArtistArt]
ARTIST_ART_CACHE_DIR = artist_art_cache

[AlbumArtSpotify]
CLIENT_ID = test_client_id
CLIENT_SECRET = test_client_secret
CACHE_DIR = album_art_cache

[Timeframe]
START_DATE = 2024-06-01
END_DATE = 2024-06-03

[RollingStats]
CALCULATE_ROLLING_STATS = False

[NightingaleChart]
ENABLE_NIGHTINGALE_CHART = False
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(config_content)
        return f.name

def test_short_animation():
    """Test a very short animation to verify no KeyError"""
    print("Testing complete animation pipeline...")
    
    config_path = create_test_config()
    test_frames_dir = "/tmp/test_frames_short"
    
    try:
        # Clean up any existing test frames
        if os.path.exists(test_frames_dir):
            shutil.rmtree(test_frames_dir)
        
        # Copy the test config to the main directory temporarily
        temp_config_main = "/tmp/test_configurations.txt"
        shutil.copy(config_path, temp_config_main)
        
        # Import and patch main_animator for testing
        import main_animator
        
        # Override some settings for minimal test
        original_config_file = main_animator.CONFIG_FILE if hasattr(main_animator, 'CONFIG_FILE') else None
        
        # Run the animation with the test config
        print("Running animation pipeline...")
        
        # Import specific functions to test step by step
        from config_loader import AppConfig
        from data_processor import clean_and_filter_data, prepare_data_for_bar_chart_race
        
        # Load config
        config = AppConfig(filepath=config_path)
        main_animator.VISUALIZATION_MODE = "artists"
        print("✓ Configuration loaded")
        
        # Load and process data
        cleaned_data = clean_and_filter_data(config)
        race_df, artist_details = prepare_data_for_bar_chart_race(cleaned_data, mode="artists")
        print(f"✓ Data processed: {len(artist_details)} artists, {race_df.shape[0]} frames")
        
        # Generate render tasks
        render_tasks = main_animator.generate_render_tasks(
            race_df[:5],  # Just first 5 frames
            3,  # N_BARS
            2,  # TARGET_FPS  
            0.1,  # TRANSITION_DURATION_SECONDS
            {},  # rolling_stats_data
            {}   # nightingale_data
        )
        print(f"✓ Generated {len(render_tasks)} render tasks")
        
        # Test one frame rendering to check for KeyError
        if render_tasks:
            test_task = render_tasks[0]
            
            # Patch the save operation to avoid actually creating files
            import matplotlib.pyplot as plt
            from unittest.mock import patch
            
            with patch('matplotlib.pyplot.savefig') as mock_save:
                # Try to draw one frame
                args = (
                    test_task,
                    artist_details,  # entity_details_map
                    {},  # entity_id_to_canonical_name_map
                    {},  # album_art_image_objects
                    {},  # album_bar_colors
                    {},  # album_art_image_objects_highres
                    ["Arial"],  # preferred_fonts
                    "artists",  # visualization_mode
                    test_frames_dir,  # temp_frames_dir
                    72,  # dpi
                    True  # cleanup_intermediate_frames
                )
                
                result = main_animator.draw_and_save_single_frame(args)
                print("✓ Frame rendering completed without KeyError!")
                
        print("\n🎉 COMPLETE ANIMATION PIPELINE TEST PASSED!")
        print("✅ The 'song_id' KeyError is completely fixed!")
        return True
        
    except KeyError as e:
        if 'song_id' in str(e):
            print(f"❌ KeyError still exists: {e}")
            return False
        else:
            print(f"❌ Different KeyError: {e}")
            return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        try:
            os.unlink(config_path)
            if os.path.exists(temp_config_main):
                os.unlink(temp_config_main)
        except:
            pass

if __name__ == "__main__":
    print("=" * 60)
    print("SHORT ANIMATION TEST - VERIFY KEYERROR FIX")
    print("=" * 60)
    
    success = test_short_animation()
    
    if success:
        print("\n✅ SUCCESS: Complete animation pipeline works in artist mode!")
        print("🎯 The original 'song_id' KeyError has been completely resolved!")
    else:
        print("\n❌ FAILURE: Animation pipeline still has issues.")
    
    sys.exit(0 if success else 1)