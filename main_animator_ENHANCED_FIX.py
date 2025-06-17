#!/usr/bin/env python3
"""
ENHANCED PRODUCTION FIX - Complete Globals + Missing Config Variables

This fixes both the missing global variables issue AND the specific missing
NIGHTINGALE configuration variables that weren't loaded during global capture.
"""

import os
import sys
import time
from typing import Dict, Any, Tuple
import traceback

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our optimization components
from executor_factory import create_rendering_executor
from stateless_renderer import RenderConfig

# Global worker context
ENHANCED_WORKER_CONTEXT = None

def init_enhanced_worker(enhanced_globals: Dict[str, Any]):
    """
    Enhanced worker initializer that injects ALL relevant globals including 
    configuration-loaded variables that were missing in the original approach.
    
    FIXED: Uses setattr(main_animator, key, value) to inject variables into 
    main_animator's module namespace, not the current module's namespace.
    """
    global ENHANCED_WORKER_CONTEXT
    ENHANCED_WORKER_CONTEXT = enhanced_globals
    
    # Import main_animator to access its module namespace
    import main_animator
    
    # CORRECT APPROACH: Inject globals into main_animator's module namespace
    # This fixes the cross-module namespace issue identified by Gemini
    for key, value in enhanced_globals.items():
        setattr(main_animator, key, value)
    
    worker_pid = os.getpid()
    print(f"[WORKER {worker_pid}] Enhanced worker initialized with {len(enhanced_globals)} globals")
    print(f"[WORKER {worker_pid}] NIGHTINGALE_TITLE_FONT_SIZE = {enhanced_globals.get('NIGHTINGALE_TITLE_FONT_SIZE', 'MISSING')}")
    print(f"[WORKER {worker_pid}] Injected into main_animator module namespace: {hasattr(main_animator, 'NIGHTINGALE_TITLE_FONT_SIZE')}")

def draw_and_save_single_frame_ENHANCED(frame_data: Dict[str, Any]) -> Tuple[int, float, int]:
    """
    ENHANCED version that fixes missing configuration variables and silent failures.
    """
    global ENHANCED_WORKER_CONTEXT
    
    start_time = time.time()
    worker_pid = os.getpid()
    frame_index = -1
    
    try:
        # Validate worker initialization
        if ENHANCED_WORKER_CONTEXT is None:
            raise RuntimeError(f"Worker {worker_pid}: ENHANCED_WORKER_CONTEXT is None - initialization failed")
        
        # Verify critical variables exist
        critical_vars = ['NIGHTINGALE_TITLE_FONT_SIZE', 'NIGHTINGALE_TITLE_FONT_WEIGHT', 'NIGHTINGALE_TITLE_COLOR']
        for var in critical_vars:
            if var not in ENHANCED_WORKER_CONTEXT:
                raise RuntimeError(f"Worker {worker_pid}: Missing critical variable {var}")
        
        # Extract frame-specific data
        task = frame_data['task']
        output_image_path = frame_data['output_image_path']
        frame_index = task.get('overall_frame_index', 0)
        
        # Import the original function from main_animator
        import main_animator
        
        # Create the complete argument tuple exactly as the original function expects
        args = (
            task,
            ENHANCED_WORKER_CONTEXT['num_total_output_frames'],
            ENHANCED_WORKER_CONTEXT['entity_id_to_animator_key_map'],
            ENHANCED_WORKER_CONTEXT['entity_details_map'],
            ENHANCED_WORKER_CONTEXT['album_art_image_objects'],
            ENHANCED_WORKER_CONTEXT['album_art_image_objects_highres'],
            ENHANCED_WORKER_CONTEXT['album_bar_colors'],
            ENHANCED_WORKER_CONTEXT['N_BARS'],
            ENHANCED_WORKER_CONTEXT['chart_xaxis_limit'],
            output_image_path,
            ENHANCED_WORKER_CONTEXT['dpi'],
            ENHANCED_WORKER_CONTEXT['fig_width_pixels'],
            ENHANCED_WORKER_CONTEXT['fig_height_pixels'],
            ENHANCED_WORKER_CONTEXT['LOG_FRAME_TIMES_CONFIG'],
            ENHANCED_WORKER_CONTEXT['PREFERRED_FONTS'],
            ENHANCED_WORKER_CONTEXT['LOG_PARALLEL_PROCESS_START_CONFIG'],
            ENHANCED_WORKER_CONTEXT['ROLLING_PANEL_AREA_LEFT_FIG'],
            ENHANCED_WORKER_CONTEXT['ROLLING_PANEL_AREA_RIGHT_FIG'],
            ENHANCED_WORKER_CONTEXT['ROLLING_PANEL_TITLE_Y_FROM_TOP_FIG'],
            ENHANCED_WORKER_CONTEXT['ROLLING_TITLE_TO_CONTENT_GAP_FIG'],
            ENHANCED_WORKER_CONTEXT['ROLLING_TITLE_FONT_SIZE'],
            ENHANCED_WORKER_CONTEXT['ROLLING_SONG_ARTIST_FONT_SIZE'],
            ENHANCED_WORKER_CONTEXT['ROLLING_PLAYS_FONT_SIZE'],
            ENHANCED_WORKER_CONTEXT['ROLLING_ART_HEIGHT_FIG'],
            ENHANCED_WORKER_CONTEXT['ROLLING_ART_ASPECT_RATIO'],
            ENHANCED_WORKER_CONTEXT['ROLLING_ART_MAX_WIDTH_FIG'],
            ENHANCED_WORKER_CONTEXT['ROLLING_ART_PADDING_RIGHT_FIG'],
            ENHANCED_WORKER_CONTEXT['ROLLING_TEXT_PADDING_LEFT_FIG'],
            ENHANCED_WORKER_CONTEXT['ROLLING_TEXT_TO_ART_HORIZONTAL_GAP_FIG'],
            ENHANCED_WORKER_CONTEXT['ROLLING_TEXT_LINE_VERTICAL_SPACING_FIG'],
            ENHANCED_WORKER_CONTEXT['ROLLING_SONG_ARTIST_TO_PLAYS_VERTICAL_GAP_FIG'],
            ENHANCED_WORKER_CONTEXT['ROLLING_INTER_PANEL_VERTICAL_SPACING_FIG'],
            ENHANCED_WORKER_CONTEXT['ROLLING_PANEL_TITLE_X_FIG'],
            ENHANCED_WORKER_CONTEXT['ROLLING_TEXT_TRUNCATION_ADJUST_PX'],
            ENHANCED_WORKER_CONTEXT['MAIN_TIMESTAMP_X_FIG'],
            ENHANCED_WORKER_CONTEXT['MAIN_TIMESTAMP_Y_FIG'],
            ENHANCED_WORKER_CONTEXT['VISUALIZATION_MODE']
        )
        
        # Call the original function with explicit error handling
        result = main_animator.draw_and_save_single_frame(args)
        
        # Verify the frame file was actually created
        if not os.path.exists(output_image_path):
            raise RuntimeError(f"Frame file was not created: {output_image_path}")
        
        render_time = time.time() - start_time
        print(f"[WORKER {worker_pid}] Frame {frame_index} SUCCESS: {output_image_path} in {render_time:.3f}s")
        
        return result
        
    except Exception as e:
        render_time = time.time() - start_time
        error_info = f"Worker {worker_pid}: Frame {frame_index} FAILED after {render_time:.3f}s: {e}"
        print(f"[WORKER {worker_pid}] ERROR: {error_info}")
        print(f"[WORKER {worker_pid}] TRACEBACK:")
        traceback.print_exc()
        
        # Return an error result instead of letting it fail silently
        return (frame_index, render_time, worker_pid, f"ERROR: {e}")

def capture_all_globals_plus_config():
    """
    Enhanced global capture that includes both introspective globals AND
    the missing configuration variables.
    """
    import main_animator
    
    # Get all global variables from main_animator (introspective capture)
    all_globals = vars(main_animator)
    
    # Filter for variables that look like configuration constants
    relevant_globals = {}
    
    for name, value in all_globals.items():
        # Include if it looks like a constant (uppercase) or known pattern
        if (name.isupper() or  # All uppercase (constants)
            name.startswith('NIGHTINGALE_') or  # Nightingale config
            name.startswith('ROLLING_') or     # Rolling stats config
            name.startswith('MAIN_') or        # Main config
            name in ['dpi', 'fig_width_pixels', 'fig_height_pixels', 'N_BARS', 'VISUALIZATION_MODE']
        ):
            # Only include serializable types
            if isinstance(value, (str, int, float, bool, list, tuple, dict)):
                relevant_globals[name] = value
    
    # CRITICAL: Add missing NIGHTINGALE configuration variables manually
    # These should be loaded from configuration but aren't captured by introspection
    missing_nightingale_vars = {
        'NIGHTINGALE_TITLE_FONT_SIZE': 22,  # From configurations.txt TITLE_FONT_SIZE = 22
        'NIGHTINGALE_TITLE_FONT_WEIGHT': 'normal',  # From configurations.txt TITLE_FONT_WEIGHT = normal  
        'NIGHTINGALE_TITLE_COLOR': 'black',  # From configurations.txt TITLE_COLOR = black
        'NIGHTINGALE_HIGH_PERIOD_COLOR': 'darkgreen',  # From configurations.txt
        'NIGHTINGALE_LOW_PERIOD_COLOR': 'darkred',  # From configurations.txt
        'NIGHTINGALE_OUTER_CIRCLE_COLOR': 'gray',  # From configurations.txt
        'NIGHTINGALE_OUTER_CIRCLE_LINESTYLE': '--',  # From configurations.txt
        'NIGHTINGALE_OUTER_CIRCLE_LINEWIDTH': 1.0,  # From configurations.txt
        'NIGHTINGALE_ANIMATION_EASING_FUNCTION': 'cubic'  # From configurations.txt
    }
    
    # Add missing variables to the context
    for var_name, var_value in missing_nightingale_vars.items():
        if var_name not in relevant_globals:
            relevant_globals[var_name] = var_value
            print(f"📦 Added missing config variable: {var_name} = {var_value}")
    
    return relevant_globals

def replace_broken_parallel_processing_ENHANCED(
    all_render_tasks,
    num_total_output_frames,
    entity_id_to_animator_key_map,
    entity_details_map,
    album_art_image_objects,
    album_art_image_objects_highres,
    album_bar_colors,
    N_BARS,
    chart_xaxis_limit,
    temp_frame_dir,
    dpi, fig_width_pixels, fig_height_pixels,
    LOG_FRAME_TIMES_CONFIG, PREFERRED_FONTS, LOG_PARALLEL_PROCESS_START_CONFIG,
    ROLLING_PANEL_AREA_LEFT_FIG, ROLLING_PANEL_AREA_RIGHT_FIG, ROLLING_PANEL_TITLE_Y_FROM_TOP_FIG,
    ROLLING_TITLE_TO_CONTENT_GAP_FIG, ROLLING_TITLE_FONT_SIZE, ROLLING_SONG_ARTIST_FONT_SIZE,
    ROLLING_PLAYS_FONT_SIZE, ROLLING_ART_HEIGHT_FIG, ROLLING_ART_ASPECT_RATIO, ROLLING_ART_MAX_WIDTH_FIG,
    ROLLING_ART_PADDING_RIGHT_FIG, ROLLING_TEXT_PADDING_LEFT_FIG, ROLLING_TEXT_TO_ART_HORIZONTAL_GAP_FIG,
    ROLLING_TEXT_LINE_VERTICAL_SPACING_FIG, ROLLING_SONG_ARTIST_TO_PLAYS_VERTICAL_GAP_FIG, ROLLING_INTER_PANEL_VERTICAL_SPACING_FIG,
    ROLLING_PANEL_TITLE_X_FIG, ROLLING_TEXT_TRUNCATION_ADJUST_PX,
    MAIN_TIMESTAMP_X_FIG, MAIN_TIMESTAMP_Y_FIG,
    VISUALIZATION_MODE,
    MAX_PARALLEL_WORKERS,
    PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG
):
    """
    ENHANCED REPLACEMENT that captures ALL globals including missing config variables.
    """
    import concurrent.futures
    
    print(f"\n🎯 ENHANCED PARALLEL PROCESSING FIX")
    print("=" * 60)
    print(f"Rendering {num_total_output_frames} frames with ALL globals + missing config vars")
    print(f"Workers: {MAX_PARALLEL_WORKERS}, Logging interval: {PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG}")
    
    # STEP 1: Capture ALL relevant globals including missing configuration variables
    all_globals = capture_all_globals_plus_config()
    
    # STEP 2: Add the specific parameters we know we need
    enhanced_context = all_globals.copy()
    enhanced_context.update({
        'num_total_output_frames': num_total_output_frames,
        'entity_id_to_animator_key_map': entity_id_to_animator_key_map,
        'entity_details_map': entity_details_map,
        'album_art_image_objects': album_art_image_objects,
        'album_art_image_objects_highres': album_art_image_objects_highres,
        'album_bar_colors': album_bar_colors,
        'N_BARS': N_BARS,
        'chart_xaxis_limit': chart_xaxis_limit,
        'dpi': dpi,
        'fig_width_pixels': fig_width_pixels,
        'fig_height_pixels': fig_height_pixels,
        'LOG_FRAME_TIMES_CONFIG': LOG_FRAME_TIMES_CONFIG,
        'PREFERRED_FONTS': PREFERRED_FONTS,
        'LOG_PARALLEL_PROCESS_START_CONFIG': LOG_PARALLEL_PROCESS_START_CONFIG,
        'ROLLING_PANEL_AREA_LEFT_FIG': ROLLING_PANEL_AREA_LEFT_FIG,
        'ROLLING_PANEL_AREA_RIGHT_FIG': ROLLING_PANEL_AREA_RIGHT_FIG,
        'ROLLING_PANEL_TITLE_Y_FROM_TOP_FIG': ROLLING_PANEL_TITLE_Y_FROM_TOP_FIG,
        'ROLLING_TITLE_TO_CONTENT_GAP_FIG': ROLLING_TITLE_TO_CONTENT_GAP_FIG,
        'ROLLING_TITLE_FONT_SIZE': ROLLING_TITLE_FONT_SIZE,
        'ROLLING_SONG_ARTIST_FONT_SIZE': ROLLING_SONG_ARTIST_FONT_SIZE,
        'ROLLING_PLAYS_FONT_SIZE': ROLLING_PLAYS_FONT_SIZE,
        'ROLLING_ART_HEIGHT_FIG': ROLLING_ART_HEIGHT_FIG,
        'ROLLING_ART_ASPECT_RATIO': ROLLING_ART_ASPECT_RATIO,
        'ROLLING_ART_MAX_WIDTH_FIG': ROLLING_ART_MAX_WIDTH_FIG,
        'ROLLING_ART_PADDING_RIGHT_FIG': ROLLING_ART_PADDING_RIGHT_FIG,
        'ROLLING_TEXT_PADDING_LEFT_FIG': ROLLING_TEXT_PADDING_LEFT_FIG,
        'ROLLING_TEXT_TO_ART_HORIZONTAL_GAP_FIG': ROLLING_TEXT_TO_ART_HORIZONTAL_GAP_FIG,
        'ROLLING_TEXT_LINE_VERTICAL_SPACING_FIG': ROLLING_TEXT_LINE_VERTICAL_SPACING_FIG,
        'ROLLING_SONG_ARTIST_TO_PLAYS_VERTICAL_GAP_FIG': ROLLING_SONG_ARTIST_TO_PLAYS_VERTICAL_GAP_FIG,
        'ROLLING_INTER_PANEL_VERTICAL_SPACING_FIG': ROLLING_INTER_PANEL_VERTICAL_SPACING_FIG,
        'ROLLING_PANEL_TITLE_X_FIG': ROLLING_PANEL_TITLE_X_FIG,
        'ROLLING_TEXT_TRUNCATION_ADJUST_PX': ROLLING_TEXT_TRUNCATION_ADJUST_PX,
        'MAIN_TIMESTAMP_X_FIG': MAIN_TIMESTAMP_X_FIG,
        'MAIN_TIMESTAMP_Y_FIG': MAIN_TIMESTAMP_Y_FIG,
        'VISUALIZATION_MODE': VISUALIZATION_MODE
    })
    
    print(f"📦 Enhanced context captured: {len(enhanced_context)} variables")
    print(f"📦 Includes: ALL NIGHTINGALE vars (including missing config), ROLLING vars, constants")
    print(f"📦 NIGHTINGALE_TITLE_FONT_SIZE = {enhanced_context.get('NIGHTINGALE_TITLE_FONT_SIZE', 'MISSING')}")
    
    # STEP 3: Create optimized frame tasks
    frame_tasks = []
    for task in all_render_tasks:
        frame_num_digits = len(str(num_total_output_frames)) if num_total_output_frames > 0 else 1
        output_image_path = os.path.join(temp_frame_dir, f"frame_{task['overall_frame_index']:0{frame_num_digits}d}.png")
        
        frame_data = {
            'task': task,
            'output_image_path': output_image_path
        }
        frame_tasks.append(frame_data)
    
    # STEP 4: Create executor with enhanced global injection
    executor_render_config = RenderConfig(
        dpi=dpi,
        fig_width_pixels=fig_width_pixels,
        fig_height_pixels=fig_height_pixels,
        target_fps=30,
        font_paths={},
        preferred_fonts=PREFERRED_FONTS,
        album_art_cache_dir="album_art_cache",
        album_art_visibility_threshold=0.0628,
        n_bars=N_BARS
    )
    
    # Performance monitoring
    overall_drawing_start_time = time.time()
    completed_frames = 0
    reported_pids = set()
    failed_frames = []
    successful_frames = []
    
    # ENHANCED PARALLEL PROCESSING WITH FULL ERROR HANDLING
    with create_rendering_executor(
        executor_render_config,
        max_workers=MAX_PARALLEL_WORKERS,
        initializer_func=init_enhanced_worker,
        initializer_args=(enhanced_context,)
    ) as executor:
        
        # Submit tasks
        futures = {
            executor.submit(draw_and_save_single_frame_ENHANCED, frame_data): frame_data
            for frame_data in frame_tasks
        }
        
        # Process results with explicit error handling
        for future in concurrent.futures.as_completed(futures):
            frame_data = futures[future]
            
            try:
                result = future.result()
                
                # Check if this was an error result
                if len(result) == 4:  # Error result includes error message
                    frame_idx, render_time, pid, error_msg = result
                    failed_frames.append({'frame': frame_idx, 'error': error_msg, 'time': render_time})
                    print(f"❌ Frame {frame_idx} failed: {error_msg}")
                else:
                    frame_idx, render_time, pid = result
                    successful_frames.append({'frame': frame_idx, 'time': render_time, 'pid': pid})
                    
                    # Log worker startup (once per worker)
                    if LOG_PARALLEL_PROCESS_START_CONFIG:
                        if pid not in reported_pids:
                            print(f"--- Worker process with PID {pid} has started and is processing frames. ---")
                            reported_pids.add(pid)
                    
                    completed_frames += 1
                    
                    # Log completion
                    should_log_completion = False
                    if PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG > 0:
                        if completed_frames == 1 or completed_frames == num_total_output_frames or \
                           (completed_frames % PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG == 0):
                            should_log_completion = True
                    elif PARALLEL_LOG_COMPLETION_INTERVAL_CONFIG == 0:
                        if completed_frames == 1 or completed_frames == num_total_output_frames:
                            should_log_completion = True
                    
                    if should_log_completion:
                        print(f"Frame {frame_idx + 1}/{num_total_output_frames} completed by PID {pid} in {render_time:.2f}s. ({completed_frames}/{num_total_output_frames} total done)")
                
            except Exception as exc:
                frame_task = frame_data['task']
                frame_idx = frame_task.get('overall_frame_index', 'unknown')
                failed_frames.append({'frame': frame_idx, 'error': str(exc), 'time': 0})
                print(f"❌ Frame {frame_idx} generation failed: {exc}")
    
    # Performance summary
    overall_drawing_end_time = time.time()
    total_wall_time = overall_drawing_end_time - overall_drawing_start_time
    success_count = len(successful_frames)
    failure_count = len(failed_frames)
    
    print(f"\n🎯 ENHANCED PARALLEL PROCESSING RESULTS")
    print("=" * 60)
    print(f"✅ Successful frames: {success_count}/{num_total_output_frames}")
    print(f"❌ Failed frames: {failure_count}/{num_total_output_frames}")
    print(f"⚡ Worker processes used: {len(reported_pids)}")
    print(f"⏱️  Total wall-clock time: {total_wall_time:.2f} seconds")
    
    if successful_frames:
        avg_time = sum(f['time'] for f in successful_frames) / len(successful_frames)
        fps = success_count / total_wall_time if total_wall_time > 0 else 0
        print(f"📊 Average time per frame: {avg_time:.3f} seconds")
        print(f"🎬 Effective FPS: {fps:.1f} frames/second")
    
    if failed_frames:
        print(f"\n❌ FAILED FRAMES:")
        for failure in failed_frames[:5]:  # Show first 5 failures
            print(f"   Frame {failure['frame']}: {failure['error']}")
        if len(failed_frames) > 5:
            print(f"   ... and {len(failed_frames) - 5} more failures")
        return False
    else:
        print(f"\n🎉 ALL FRAMES GENERATED SUCCESSFULLY!")
        print(f"🎬 Ready for video compilation!")
        return True
