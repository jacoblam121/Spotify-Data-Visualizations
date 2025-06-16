"""
RenderConfig dataclass for parallelization.
Consolidates all configuration parameters into a single serializable object
that can be passed to worker processes in spawn mode.
"""

import dataclasses
from typing import List, Tuple, Dict, Optional, Any
from datetime import datetime
import pandas as pd


@dataclasses.dataclass(frozen=True)
class RenderConfig:
    """Configuration object containing all parameters needed for frame rendering.
    
    This replaces the need for global variables in worker processes.
    Frozen=True makes it immutable, preventing accidental modification.
    """
    
    # --- Core Configuration ---
    visualization_mode: str  # 'tracks' or 'artists'
    n_bars: int
    target_fps: int
    output_filename_base: str
    
    # --- Video Resolution ---
    video_width: int
    video_height: int
    video_dpi: int
    
    # --- Album Art Configuration ---
    debug_album_art_logic: bool
    album_art_visibility_threshold_factor: float
    song_text_right_gap_fraction: float
    
    # --- Font Configuration ---
    preferred_fonts: List[str]
    
    # --- Animation Configuration ---
    animation_transition_duration_seconds: float
    enable_overtake_animations: bool
    
    # --- Parallel Processing Configuration ---
    max_parallel_workers: int
    cleanup_intermediate_frames: bool
    serial_mode: bool
    max_tasks_per_child: int
    force_parallel_workers: int
    memory_debug: bool
    
    # --- Logging Configuration ---
    log_frame_times: bool
    log_parallel_process_start: bool
    parallel_log_completion_interval: int
    
    # --- Rolling Stats Display Configuration ---
    rolling_panel_area_left_fig: float
    rolling_panel_area_right_fig: float
    rolling_panel_title_y_from_top_fig: float
    rolling_title_to_content_gap_fig: float
    rolling_title_font_size: float
    rolling_song_artist_font_size: float
    rolling_plays_font_size: float
    rolling_art_height_fig: float
    rolling_art_aspect_ratio: float
    rolling_art_max_width_fig: float
    rolling_art_padding_right_fig: float
    rolling_text_padding_left_fig: float
    rolling_text_to_art_horizontal_gap_fig: float
    rolling_text_line_vertical_spacing_fig: float
    rolling_song_artist_to_plays_vertical_gap_fig: float
    rolling_inter_panel_vertical_spacing_fig: float
    rolling_panel_title_x_fig: float
    rolling_text_truncation_adjust_px: int
    
    # --- Main Timestamp Display ---
    main_timestamp_x_fig: float
    main_timestamp_y_fig: float
    
    # --- Nightingale Chart Configuration ---
    enable_nightingale: bool
    nightingale_center_x_fig: float
    nightingale_center_y_fig: float
    nightingale_radius_fig: float
    nightingale_show_period_labels: bool
    nightingale_label_radius_ratio: float
    nightingale_label_font_color: str
    nightingale_label_font_weight: str
    nightingale_show_high_low_info: bool
    nightingale_high_low_y_offset_fig: float
    nightingale_high_low_spacing_fig: float
    nightingale_label_font_size: int
    nightingale_high_low_font_size: int
    nightingale_enable_smooth_transitions: bool
    nightingale_transition_duration_seconds: float
    nightingale_aggregation_type: str
    nightingale_sampling_rate: str
    nightingale_debug: bool
    nightingale_title_font_size: int
    nightingale_title_font_weight: str
    nightingale_title_color: str
    nightingale_title_position_above_chart: float
    nightingale_high_period_color: str
    nightingale_low_period_color: str
    nightingale_show_boundary_circle: bool
    nightingale_outer_circle_color: str
    nightingale_outer_circle_linestyle: str
    nightingale_outer_circle_linewidth: float
    nightingale_animation_easing_function: str
    
    # --- File Paths ---
    temp_frame_dir: str
    output_filename: str
    
    # --- Other Settings ---
    use_nvenc_if_available: bool
    max_frames_for_test_render: int
    
    @classmethod
    def from_config_object(cls, config, args=None):
        """Create RenderConfig from AppConfig object and optional command line args.
        
        This method extracts all configuration values from the loaded config
        and creates a frozen RenderConfig instance.
        """
        # Video resolution handling
        video_resolution_preset = config.get('AnimationOutput', 'RESOLUTION', '1080p')
        presets = {
            "1080p": {"width": 1920, "height": 1080, "dpi": 96},
            "4k": {"width": 3840, "height": 2160, "dpi": 165}
        }
        resolution = presets.get(video_resolution_preset, presets["1080p"])
        
        # Build output filename
        output_base = config.get('AnimationOutput', 'FILENAME_BASE', 'spotify_top_songs_race')
        output_filename = f"{output_base}_{video_resolution_preset}.mp4"
        
        # Get visualization mode
        viz_mode = config.get('VisualizationMode', 'MODE', 'tracks').lower()
        if viz_mode not in ['tracks', 'artists']:
            viz_mode = 'tracks'
        
        # Worker count logic
        workers_from_config = config.get_int('AnimationOutput', 'MAX_PARALLEL_WORKERS', -1)
        if workers_from_config <= 0:
            max_workers = os.cpu_count() or 1
        else:
            max_workers = workers_from_config
        
        return cls(
            # Core Configuration
            visualization_mode=viz_mode,
            n_bars=config.get_int('AnimationOutput', 'N_BARS', 10),
            target_fps=config.get_int('AnimationOutput', 'TARGET_FPS', 30),
            output_filename_base=output_base,
            
            # Video Resolution
            video_width=resolution['width'],
            video_height=resolution['height'],
            video_dpi=resolution['dpi'],
            
            # Album Art Configuration
            debug_album_art_logic=config.get_bool('Debugging', 'DEBUG_ALBUM_ART_LOGIC_ANIMATOR', True),
            album_art_visibility_threshold_factor=config.get_float('AlbumArtSpotify', 'ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR', 0.0628),
            song_text_right_gap_fraction=config.get_float('AlbumArtSpotify', 'SONG_TEXT_RIGHT_GAP_FRACTION', 0.1),
            
            # Font Configuration
            preferred_fonts=config.get_list('FontPreferences', 'PREFERRED_FONTS', fallback=['DejaVu Sans', 'sans-serif']),
            
            # Animation Configuration
            animation_transition_duration_seconds=config.get_float('AnimationOutput', 'ANIMATION_TRANSITION_DURATION_SECONDS', 0.3),
            enable_overtake_animations=config.get_bool('AnimationOutput', 'ENABLE_OVERTAKE_ANIMATIONS', True),
            
            # Parallel Processing Configuration
            max_parallel_workers=max_workers,
            cleanup_intermediate_frames=config.get_bool('AnimationOutput', 'CLEANUP_INTERMEDIATE_FRAMES', True),
            serial_mode=config.get_bool('AnimationOutput', 'SERIAL_MODE', False),
            max_tasks_per_child=config.get_int('AnimationOutput', 'MAX_TASKS_PER_CHILD', 100),
            force_parallel_workers=config.get_int('AnimationOutput', 'FORCE_PARALLEL_WORKERS', 0),
            memory_debug=config.get_bool('AnimationOutput', 'MEMORY_DEBUG', False),
            
            # Logging Configuration
            log_frame_times=config.get_bool('Debugging', 'LOG_FRAME_TIMES', False),
            log_parallel_process_start=config.get_bool('Debugging', 'LOG_PARALLEL_PROCESS_START', True),
            parallel_log_completion_interval=config.get_int('Debugging', 'PARALLEL_LOG_COMPLETION_INTERVAL', 50),
            
            # Rolling Stats Display Configuration
            rolling_panel_area_left_fig=config.get_float('RollingStatsDisplay', 'PANEL_AREA_LEFT_FIG', 0.03),
            rolling_panel_area_right_fig=config.get_float('RollingStatsDisplay', 'PANEL_AREA_RIGHT_FIG', 0.25),
            rolling_panel_title_y_from_top_fig=config.get_float('RollingStatsDisplay', 'PANEL_TITLE_Y_FROM_TOP_FIG', 0.02),
            rolling_title_to_content_gap_fig=config.get_float('RollingStatsDisplay', 'TITLE_TO_CONTENT_GAP_FIG', 0.01),
            rolling_title_font_size=config.get_float('RollingStatsDisplay', 'TITLE_FONT_SIZE', 11.0),
            rolling_song_artist_font_size=config.get_float('RollingStatsDisplay', 'SONG_ARTIST_FONT_SIZE', 9.0),
            rolling_plays_font_size=config.get_float('RollingStatsDisplay', 'PLAYS_FONT_SIZE', 8.0),
            rolling_art_height_fig=config.get_float('RollingStatsDisplay', 'ART_HEIGHT_FIG', 0.07),
            rolling_art_aspect_ratio=config.get_float('RollingStatsDisplay', 'ART_ASPECT_RATIO', 1.0),
            rolling_art_max_width_fig=config.get_float('RollingStatsDisplay', 'ART_MAX_WIDTH_FIG', 0.07),
            rolling_art_padding_right_fig=config.get_float('RollingStatsDisplay', 'ART_PADDING_RIGHT_FIG', 0.005),
            rolling_text_padding_left_fig=config.get_float('RollingStatsDisplay', 'TEXT_PADDING_LEFT_FIG', 0.005),
            rolling_text_to_art_horizontal_gap_fig=config.get_float('RollingStatsDisplay', 'TEXT_TO_ART_HORIZONTAL_GAP_FIG', 0.005),
            rolling_text_line_vertical_spacing_fig=config.get_float('RollingStatsDisplay', 'TEXT_LINE_VERTICAL_SPACING_FIG', 0.02),
            rolling_song_artist_to_plays_vertical_gap_fig=config.get_float('RollingStatsDisplay', 'SONG_ARTIST_TO_PLAYS_VERTICAL_GAP_FIG', 0.025),
            rolling_inter_panel_vertical_spacing_fig=config.get_float('RollingStatsDisplay', 'INTER_PANEL_VERTICAL_SPACING_FIG', 0.04),
            rolling_panel_title_x_fig=config.get_float('RollingStatsDisplay', 'PANEL_TITLE_X_FIG', -1.0),
            rolling_text_truncation_adjust_px=config.get_int('RollingStatsDisplay', 'ROLLING_TEXT_TRUNCATION_ADJUST_PX', 0),
            
            # Main Timestamp Display
            main_timestamp_x_fig=config.get_float('TimestampDisplay', 'TIMESTAMP_X_FIG', -1.0),
            main_timestamp_y_fig=config.get_float('TimestampDisplay', 'TIMESTAMP_Y_FIG', 0.04),
            
            # Nightingale Chart Configuration
            enable_nightingale=config.get_bool('NightingaleChart', 'ENABLE', True),
            nightingale_center_x_fig=config.get_float('NightingaleChart', 'CHART_X', 0.15),
            nightingale_center_y_fig=config.get_float('NightingaleChart', 'CHART_Y', 0.20),
            nightingale_radius_fig=config.get_float('NightingaleChart', 'CHART_RADIUS', 0.08),
            nightingale_show_period_labels=config.get_bool('NightingaleChart', 'SHOW_MONTH_LABELS', True),
            nightingale_label_radius_ratio=config.get_float('NightingaleChart', 'MONTH_LABEL_DISTANCE', 1.15),
            nightingale_label_font_color=config.get('NightingaleChart', 'MONTH_LABEL_COLOR', 'black'),
            nightingale_label_font_weight=config.get('NightingaleChart', 'MONTH_LABEL_FONT_WEIGHT', 'normal'),
            nightingale_show_high_low_info=config.get_bool('NightingaleChart', 'SHOW_HIGH_LOW', True),
            nightingale_high_low_y_offset_fig=config.get_float('NightingaleChart', 'HIGH_LOW_POSITION_BELOW_CHART', -0.12),
            nightingale_high_low_spacing_fig=config.get_float('NightingaleChart', 'HIGH_LOW_SPACING', 0.025),
            nightingale_label_font_size=config.get_int('NightingaleChart', 'MONTH_LABEL_FONT_SIZE', 10),
            nightingale_high_low_font_size=config.get_int('NightingaleChart', 'HIGH_LOW_FONT_SIZE', 9),
            nightingale_enable_smooth_transitions=config.get_bool('NightingaleChart', 'SMOOTH_TRANSITIONS', True),
            nightingale_transition_duration_seconds=config.get_float('NightingaleChart', 'TRANSITION_DURATION', 0.3),
            nightingale_aggregation_type=config.get('NightingaleChart', 'TIME_AGGREGATION', 'auto').lower(),
            nightingale_sampling_rate=config.get('NightingaleChart', 'SAMPLING_RATE', 'D'),
            nightingale_debug=config.get_bool('NightingaleChart', 'DEBUG_MODE', False),
            nightingale_title_font_size=config.get_int('NightingaleChart', 'TITLE_FONT_SIZE', 12),
            nightingale_title_font_weight=config.get('NightingaleChart', 'TITLE_FONT_WEIGHT', 'bold'),
            nightingale_title_color=config.get('NightingaleChart', 'TITLE_COLOR', 'black'),
            nightingale_title_position_above_chart=config.get_float('NightingaleChart', 'TITLE_POSITION_ABOVE_CHART', 0.02),
            nightingale_high_period_color=config.get('NightingaleChart', 'HIGH_PERIOD_COLOR', 'darkgreen'),
            nightingale_low_period_color=config.get('NightingaleChart', 'LOW_PERIOD_COLOR', 'darkred'),
            nightingale_show_boundary_circle=config.get_bool('NightingaleChart', 'SHOW_BOUNDARY_CIRCLE', True),
            nightingale_outer_circle_color=config.get('NightingaleChart', 'BOUNDARY_CIRCLE_COLOR', 'gray'),
            nightingale_outer_circle_linestyle=config.get('NightingaleChart', 'BOUNDARY_CIRCLE_STYLE', '--'),
            nightingale_outer_circle_linewidth=config.get_float('NightingaleChart', 'BOUNDARY_CIRCLE_WIDTH', 1.0),
            nightingale_animation_easing_function=config.get('NightingaleChart', 'ANIMATION_STYLE', 'cubic'),
            
            # File Paths (will be set later)
            temp_frame_dir='',  # Set after directory creation
            output_filename=output_filename,
            
            # Other Settings
            use_nvenc_if_available=config.get_bool('AnimationOutput', 'USE_NVENC_IF_AVAILABLE', True),
            max_frames_for_test_render=config.get_int('AnimationOutput', 'MAX_FRAMES_FOR_TEST_RENDER', 0),
        )


# Import OS for cpu_count
import os