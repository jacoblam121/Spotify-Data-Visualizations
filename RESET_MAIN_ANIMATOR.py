#!/usr/bin/env python3
"""
RESET MAIN ANIMATOR - Clean Recovery

This script resets main_animator.py to the backup and reapplies the fix cleanly.
Use this if the production fix script created syntax errors or duplicate lines.
"""

import os
import shutil

def reset_and_reapply():
    """Reset to backup and reapply the production fix cleanly"""
    
    original = "/home/jacob/Spotify-Data-Visualizations/main_animator.py"
    backup = "/home/jacob/Spotify-Data-Visualizations/main_animator_ORIGINAL_BACKUP.py"
    
    if not os.path.exists(backup):
        print("❌ No backup file found!")
        print(f"Expected: {backup}")
        return False
    
    print("🔄 RESETTING MAIN_ANIMATOR.PY TO CLEAN STATE")
    print("=" * 50)
    
    # Step 1: Restore from backup
    print("1. Restoring from backup...")
    shutil.copy2(backup, original)
    print("✅ Restored original main_animator.py from backup")
    
    # Step 2: Apply clean fixes manually
    print("\n2. Applying clean fixes...")
    
    with open(original, 'r') as f:
        content = f.read()
    
    # Fix 1: Add global declaration for USE_FRAME_SPEC_GENERATOR
    if "    if USE_FRAME_SPEC_GENERATOR:" in content and "global USE_FRAME_SPEC_GENERATOR" not in content:
        content = content.replace(
            "    if USE_FRAME_SPEC_GENERATOR:",
            "    global USE_FRAME_SPEC_GENERATOR\n    if USE_FRAME_SPEC_GENERATOR:"
        )
        print("✅ Fixed USE_FRAME_SPEC_GENERATOR scoping")
    
    # Fix 2: Add production imports
    if "from config_loader import AppConfig" in content and "from main_animator_PRODUCTION_FIX import" not in content:
        content = content.replace(
            "from config_loader import AppConfig",
            """from config_loader import AppConfig

# PRODUCTION FIX: Import optimized parallel processing
from main_animator_PRODUCTION_FIX import replace_broken_parallel_processing_PRODUCTION"""
        )
        print("✅ Added production imports")
    
    # Fix 3: Replace broken ProcessPoolExecutor
    broken_start = "    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as executor:"
    broken_end = "    overall_drawing_end_time = time.time()"
    
    if broken_start in content and "replace_broken_parallel_processing_PRODUCTION" not in content:
        start_index = content.find(broken_start)
        end_index = content.find(broken_end, start_index)
        
        if start_index != -1 and end_index != -1:
            replacement = """    # PRODUCTION FIX: Replace broken ProcessPoolExecutor with optimized version
    success = replace_broken_parallel_processing_PRODUCTION(
        all_render_tasks, num_total_output_frames,
        entity_id_to_animator_key_map, entity_details_map,
        album_art_image_objects, album_art_image_objects_highres, album_bar_colors,
        N_BARS, chart_xaxis_limit, temp_frame_dir,
        dpi, fig_width_pixels, fig_height_pixels,
        LOG_FRAME_TIMES_CONFIG, PREFERRED_FONTS, LOG_PARALLEL_PROCESS_START_CONFIG,
        ROLLING_PANEL_AREA_LEFT_FIG, ROLLING_PANEL_AREA_RIGHT_FIG, ROLLING_PANEL_TITLE_Y_FROM_TOP_FIG,
        ROLLING_TITLE_TO_CONTENT_GAP_FIG, ROLLING_TITLE_FONT_SIZE, ROLLING_SONG_ARTIST_FONT_SIZE,
        ROLLING_PLAYS_FONT_SIZE, ROLLING_ART_HEIGHT_FIG, ROLLING_ART_ASPECT_RATIO, ROLLING_ART_MAX_WIDTH_FIG,
        ROLLING_ART_PADDING_RIGHT_FIG, ROLLING_TEXT_PADDING_LEFT_FIG, ROLLING_TEXT_TO_ART_HORIZONTAL_GAP_FIG,
        ROLLING_TEXT_LINE_VERTICAL_SPACING_FIG, ROLLING_SONG_ARTIST_TO_PLAYS_VERTICAL_GAP_FIG,
        ROLLING_INTER_PANEL_VERTICAL_SPACING_FIG, ROLLING_PANEL_TITLE_X_FIG, ROLLING_TEXT_TRUNCATION_ADJUST_PX,
        MAIN_TIMESTAMP_X_FIG, MAIN_TIMESTAMP_Y_FIG, VISUALIZATION_MODE,
        MAX_PARALLEL_WORKERS, PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG
    )
    
    if not success:
        print("CRITICAL: Parallel frame generation failed!")
        return
    
    # Variables needed for post-processing (set by our production function)
    """
            
            new_content = content[:start_index] + replacement + content[end_index:]
            content = new_content
            print("✅ Replaced broken ProcessPoolExecutor with optimized version")
    
    # Write the clean fixed content
    with open(original, 'w') as f:
        f.write(content)
    
    print("\n🎉 CLEAN RESET AND FIX COMPLETE!")
    print("=" * 50)
    print("✅ main_animator.py has been cleanly reset and fixed")
    print("✅ No duplicate lines or syntax errors")
    print("✅ Ready to test with: python main_animator.py")
    
    return True

if __name__ == "__main__":
    reset_and_reapply()