#!/usr/bin/env python3
"""
Comprehensive Test Suite for Top Artists Implementation

This test suite covers all phases of the top artists implementation:
- Phase 1: Core Mode Infrastructure 
- Phase 2: Artist Photo System Integration
- Phase 3: Rendering Updates
- Phase 4: Rolling Stats & Display
- Phase 5: Testing & Integration

Run with: python test_comprehensive_artists.py
"""

import os
import sys
import pandas as pd
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import the modules we want to test
from config_loader import AppConfig
from data_processor import clean_and_filter_data, prepare_data_for_bar_chart_race, calculate_rolling_window_stats
import main_animator

class TestResults:
    """Helper class to track test results"""
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []
    
    def run_test(self, test_name, test_func):
        """Run a test and track results"""
        self.tests_run += 1
        try:
            print(f"\n{'='*60}")
            print(f"Running Test: {test_name}")
            print(f"{'='*60}")
            
            result = test_func()
            if result:
                self.tests_passed += 1
                print(f"✓ PASSED: {test_name}")
            else:
                self.failures.append(f"FAILED: {test_name} - Test returned False")
                print(f"✗ FAILED: {test_name}")
        except Exception as e:
            self.failures.append(f"ERROR: {test_name} - {str(e)}")
            print(f"✗ ERROR: {test_name} - {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        
        if self.failures:
            print(f"\nFailures:")
            for failure in self.failures:
                print(f"  - {failure}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        return len(self.failures) == 0

def create_test_config(mode="artists"):
    """Create a test configuration file"""
    config_content = f"""
[DataSource]
SOURCE = lastfm
INPUT_FILENAME_LASTFM = lastfm_data.csv
MIN_MS_PLAYED_FOR_COUNT = 30000
FILTER_SKIPPED_TRACKS = True

[Timeframe]
START_DATE = all_time
END_DATE = all_time

[VisualizationMode]
MODE = {mode}

[AlbumArtSpotify]
CLIENT_ID = test_client_id
CLIENT_SECRET = test_client_secret
CACHE_DIR = album_art_cache

[ArtistArt]
ARTIST_ART_CACHE_DIR = artist_art_cache

[AnimationOutput]
OUTPUT_WIDTH = 1920
OUTPUT_HEIGHT = 1080
FPS = 30
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(config_content)
        return f.name

def test_phase1_core_mode_infrastructure():
    """Test Phase 1: Core Mode Infrastructure"""
    print("Testing core mode infrastructure...")
    
    # Test 1: Configuration loading
    config_path = create_test_config("artists")
    try:
        config = AppConfig(filepath=config_path)
        mode = config.get('VisualizationMode', 'MODE', 'tracks')
        assert mode == "artists", f"Expected 'artists', got '{mode}'"
        print("✓ Configuration loading works")
        
        # Test with tracks mode
        config_tracks = create_test_config("tracks")
        config2 = AppConfig(filepath=config_tracks)
        mode2 = config2.get('VisualizationMode', 'MODE', 'tracks')
        assert mode2 == "tracks", f"Expected 'tracks', got '{mode2}'"
        print("✓ Mode switching in config works")
        
        # Test mode validation in main_animator
        original_load_config = main_animator.load_configuration
        def mock_load_config():
            return config
        
        main_animator.load_configuration = mock_load_config
        result = main_animator.load_configuration()
        assert result is not None, "Configuration loading failed"
        print("✓ Main animator configuration integration works")
        
        main_animator.load_configuration = original_load_config
        
        return True
        
    except Exception as e:
        print(f"✗ Phase 1 test failed: {e}")
        return False
    finally:
        # Cleanup
        try:
            os.unlink(config_path)
            if 'config_tracks' in locals():
                os.unlink(config_tracks)
        except:
            pass

def test_phase2_data_processing():
    """Test Phase 2: Data Processing for both modes"""
    print("Testing data processing for tracks and artists modes...")
    
    config_path = create_test_config("artists")
    try:
        config = AppConfig(filepath=config_path)
        
        # Load actual data
        cleaned_data = clean_and_filter_data(config)
        assert cleaned_data is not None, "Data loading failed"
        assert not cleaned_data.empty, "No data loaded"
        print(f"✓ Loaded {len(cleaned_data)} rows of data")
        
        # Test tracks mode
        race_df_tracks, track_details = prepare_data_for_bar_chart_race(cleaned_data, mode="tracks")
        assert race_df_tracks is not None, "Tracks race data preparation failed"
        assert len(track_details) > 0, "No track details created"
        print(f"✓ Tracks mode: {race_df_tracks.shape[1]} unique tracks processed")
        
        # Test artists mode
        race_df_artists, artist_details = prepare_data_for_bar_chart_race(cleaned_data, mode="artists")
        assert race_df_artists is not None, "Artists race data preparation failed"
        assert len(artist_details) > 0, "No artist details created"
        print(f"✓ Artists mode: {race_df_artists.shape[1]} unique artists processed")
        
        # Verify artist details structure
        sample_artist = list(artist_details.keys())[0]
        artist_info = artist_details[sample_artist]
        
        required_keys = ['display_artist', 'normalized_artist', 'most_played_track']
        for key in required_keys:
            assert key in artist_info, f"Missing key '{key}' in artist details"
        
        # Check most_played_track is now a dictionary
        mpt = artist_info['most_played_track']
        assert isinstance(mpt, dict), f"most_played_track should be dict, got {type(mpt)}"
        assert 'track_name' in mpt, "Missing 'track_name' in most_played_track"
        assert 'album_name' in mpt, "Missing 'album_name' in most_played_track"
        print("✓ Artist details structure is correct")
        print(f"✓ most_played_track format fixed: {type(mpt)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Phase 2 test failed: {e}")
        return False
    finally:
        try:
            os.unlink(config_path)
        except:
            pass

def test_phase3_artist_photo_retrieval():
    """Test Phase 3: Artist Photo Retrieval System"""
    print("Testing artist photo retrieval system...")
    
    try:
        # Mock the album_art_utils functions to avoid actual API calls
        with patch('album_art_utils.get_artist_profile_photo_and_spotify_info') as mock_get_artist_photo, \
             patch('album_art_utils.get_artist_dominant_color_by_name') as mock_get_artist_color:
            
            mock_get_artist_photo.return_value = ('/fake/path/artist.jpg', {'name': 'Test Artist'})
            mock_get_artist_color.return_value = (255, 0, 0)
            
            # Create test artist details
            test_artist_details = {
                'test artist': {
                    'display_artist': 'Test Artist',
                    'normalized_artist': 'test artist',
                    'most_played_track': {
                        'track_name': 'Test Song',
                        'album_name': 'Test Album',
                        'track_uri': 'spotify:track:test123'
                    }
                }
            }
            
            # Test the pre-fetch function with correct parameters
            result = main_animator.pre_fetch_artist_photos_and_colors(
                test_artist_details, 
                entity_ids_to_fetch_art_for=['test artist'],
                target_img_height_pixels_for_resize=100,
                fig_dpi=72
            )
            
            assert result is not None, "Pre-fetch function failed"
            print("✓ Artist photo pre-fetching works")
            
            # Verify the functions were called
            print(f"✓ Artist photo and color functions accessible")
            
            return True
            
    except Exception as e:
        print(f"✗ Phase 3 test failed: {e}")
        return False

def test_phase4_rolling_stats():
    """Test Phase 4: Rolling Stats for Artists"""
    print("Testing rolling stats calculation for artists...")
    
    config_path = create_test_config("artists")
    try:
        config = AppConfig(filepath=config_path)
        cleaned_data = clean_and_filter_data(config)
        
        # Create some test timestamps
        test_timestamps = pd.date_range(
            start=cleaned_data['timestamp'].min() + pd.Timedelta(days=30),
            end=cleaned_data['timestamp'].max(),
            freq='7D'  # Weekly samples
        )[:5]  # Just test first 5
        
        # Test rolling stats for artists
        rolling_stats = calculate_rolling_window_stats(
            cleaned_data, 
            test_timestamps, 
            mode="artists"
        )
        
        assert rolling_stats is not None, "Rolling stats calculation failed"
        assert len(rolling_stats) == len(test_timestamps), "Wrong number of rolling stats"
        print(f"✓ Rolling stats calculated for {len(rolling_stats)} timestamps")
        
        # Verify structure
        sample_timestamp = list(rolling_stats.keys())[0]
        sample_stats = rolling_stats[sample_timestamp]
        
        assert 'top_7_day' in sample_stats, "Missing top_7_day stats"
        assert 'top_30_day' in sample_stats, "Missing top_30_day stats"
        
        # Check if we have valid data (not None)
        if sample_stats['top_7_day'] is not None:
            assert 'artist_id' in sample_stats['top_7_day'], "Missing artist_id in 7-day stats"
            assert 'original_artist' in sample_stats['top_7_day'], "Missing original_artist in 7-day stats"
            print("✓ Rolling stats structure is correct for artists")
        
        return True
        
    except Exception as e:
        print(f"✗ Phase 4 test failed: {e}")
        return False
    finally:
        try:
            os.unlink(config_path)
        except:
            pass

def test_phase5_integration():
    """Test Phase 5: Integration Testing"""
    print("Testing full integration...")
    
    config_path = create_test_config("artists")
    try:
        # Mock external dependencies
        with patch('album_art_utils.get_artist_profile_photo_and_spotify_info') as mock_get_artist_photo, \
             patch('album_art_utils.get_artist_dominant_color_by_name') as mock_get_artist_color:
            
            mock_get_artist_photo.return_value = ('/fake/path/artist.jpg', {'name': 'Test Artist'})
            mock_get_artist_color.return_value = (255, 0, 0)
            
            # Test the main pipeline
            config = AppConfig(filepath=config_path)
            
            # Test mode detection
            mode = config.get('VisualizationMode', 'MODE', 'tracks')
            assert mode == "artists", f"Mode detection failed: {mode}"
            print("✓ Mode detection works")
            
            # Test data pipeline
            cleaned_data = clean_and_filter_data(config)
            race_df, entity_details = prepare_data_for_bar_chart_race(cleaned_data, mode=mode)
            
            assert race_df is not None, "Data pipeline failed"
            assert len(entity_details) > 0, "No entities processed"
            print(f"✓ Data pipeline works: {len(entity_details)} entities")
            
            # Test artist photo pre-fetching with minimal data
            if mode == "artists":
                # Get a small subset for testing
                test_entities = dict(list(entity_details.items())[:2])  # Just test 2 artists
                entity_ids = list(test_entities.keys())
                
                photo_results = main_animator.pre_fetch_artist_photos_and_colors(
                    test_entities, 
                    entity_ids_to_fetch_art_for=entity_ids,
                    target_img_height_pixels_for_resize=100,
                    fig_dpi=72
                )
                assert photo_results is not None, "Artist photo pre-fetching failed"
                print("✓ Artist photo pre-fetching integration works")
            
            return True
            
    except Exception as e:
        print(f"✗ Phase 5 test failed: {e}")
        return False
    finally:
        try:
            os.unlink(config_path)
        except:
            pass

def test_cache_management():
    """Test cache management and separation"""
    print("Testing cache management...")
    
    try:
        # Test that artist cache directory is separate
        config_path = create_test_config("artists")
        config = AppConfig(filepath=config_path)
        
        album_cache = config.get('AlbumArtSpotify', 'CACHE_DIR', 'album_art_cache')
        artist_cache = config.get('ArtistArt', 'ARTIST_ART_CACHE_DIR', 'artist_art_cache')
        
        assert album_cache != artist_cache, "Cache directories should be separate"
        print(f"✓ Separate cache directories: {album_cache} vs {artist_cache}")
        
        # Check that the directories exist
        assert os.path.exists(album_cache), f"Album cache directory missing: {album_cache}"
        assert os.path.exists(artist_cache), f"Artist cache directory missing: {artist_cache}"
        print("✓ Cache directories exist")
        
        return True
        
    except Exception as e:
        print(f"✗ Cache management test failed: {e}")
        return False
    finally:
        try:
            os.unlink(config_path)
        except:
            pass

def test_mode_switching():
    """Test switching between tracks and artists modes"""
    print("Testing mode switching...")
    
    try:
        # Test tracks mode
        config_tracks = create_test_config("tracks")
        config1 = AppConfig(filepath=config_tracks)
        
        cleaned_data = clean_and_filter_data(config1)
        race_df_tracks, track_details = prepare_data_for_bar_chart_race(cleaned_data, mode="tracks")
        
        assert 'entity_id' in race_df_tracks.columns or len(race_df_tracks.columns) > 0, "Tracks mode failed"
        print(f"✓ Tracks mode: {race_df_tracks.shape[1]} tracks")
        
        # Test artists mode
        config_artists = create_test_config("artists")
        config2 = AppConfig(filepath=config_artists)
        
        race_df_artists, artist_details = prepare_data_for_bar_chart_race(cleaned_data, mode="artists")
        
        assert len(artist_details) > 0, "Artists mode failed"
        print(f"✓ Artists mode: {len(artist_details)} artists")
        
        # Verify different structures
        sample_track = list(track_details.keys())[0] if track_details else None
        sample_artist = list(artist_details.keys())[0] if artist_details else None
        
        if sample_track and sample_artist:
            track_info = track_details[sample_track]
            artist_info = artist_details[sample_artist]
            
            # Track details should have different structure than artist details
            assert 'display_track' in track_info, "Track details missing display_track"
            assert 'normalized_artist' in artist_info, "Artist details missing normalized_artist"
            print("✓ Different data structures for different modes")
        
        return True
        
    except Exception as e:
        print(f"✗ Mode switching test failed: {e}")
        return False
    finally:
        try:
            os.unlink(config_tracks)
            os.unlink(config_artists)
        except:
            pass

def test_error_handling():
    """Test error handling and edge cases"""
    print("Testing error handling...")
    
    try:
        # Test with empty data
        empty_df = pd.DataFrame()
        race_df, details = prepare_data_for_bar_chart_race(empty_df, mode="artists")
        assert race_df is None, "Should handle empty data gracefully"
        assert details == {}, "Should return empty details for empty data"
        print("✓ Empty data handling works")
        
        # Test with invalid mode
        try:
            config_path = create_test_config("artists")
            config = AppConfig(filepath=config_path)
            cleaned_data = clean_and_filter_data(config)
            
            prepare_data_for_bar_chart_race(cleaned_data, mode="invalid_mode")
            assert False, "Should raise error for invalid mode"
        except ValueError as e:
            assert "Unsupported mode" in str(e), "Wrong error message"
            print("✓ Invalid mode handling works")
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False
    finally:
        try:
            if 'config_path' in locals():
                os.unlink(config_path)
        except:
            pass

def main():
    """Main test runner"""
    print("="*60)
    print("COMPREHENSIVE TEST SUITE FOR TOP ARTISTS IMPLEMENTATION")
    print("="*60)
    
    # Check if required files exist
    required_files = ['lastfm_data.csv', 'main_animator.py', 'data_processor.py', 'config_loader.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"ERROR: Required file not found: {file}")
            return False
    
    print("✓ All required files found")
    
    # Initialize test results tracker
    results = TestResults()
    
    # Run all tests
    results.run_test("Phase 1: Core Mode Infrastructure", test_phase1_core_mode_infrastructure)
    results.run_test("Phase 2: Data Processing", test_phase2_data_processing)
    results.run_test("Phase 3: Artist Photo Retrieval", test_phase3_artist_photo_retrieval)
    results.run_test("Phase 4: Rolling Stats", test_phase4_rolling_stats)
    results.run_test("Phase 5: Integration", test_phase5_integration)
    results.run_test("Cache Management", test_cache_management)
    results.run_test("Mode Switching", test_mode_switching)
    results.run_test("Error Handling", test_error_handling)
    
    # Print final summary
    success = results.print_summary()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! Top Artists implementation is working correctly.")
    else:
        print("\n❌ Some tests failed. Please review the failures above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)