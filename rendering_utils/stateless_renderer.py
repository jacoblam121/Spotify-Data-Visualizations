#!/usr/bin/env python3
"""
Stateless Parallel Frame Renderer for Phase 2

This module implements truly stateless frame rendering that can be executed
in parallel worker processes without shared state dependencies.
"""

import os
import sys
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Tuple
import json
import time
import multiprocessing


@dataclass
class RenderConfig:
    """
    Serializable configuration for worker processes.
    Contains all rendering settings needed by workers.
    """
    # Video output settings
    dpi: int
    fig_width_pixels: int
    fig_height_pixels: int
    target_fps: int
    
    # Font configuration  
    font_paths: Dict[str, str]  # font_name -> file_path
    preferred_fonts: list
    
    # Album art settings
    album_art_cache_dir: str
    album_art_visibility_threshold: float
    
    # Layout parameters
    n_bars: int
    left_margin_ax: float = 0.28
    right_margin_ax: float = 0.985
    bottom_margin_ax: float = 0.08
    top_margin_ax: float = 0.98
    
    # Text settings
    song_text_right_gap_fraction: float = 0.1
    bar_text_truncation_adjust_px: int = 0
    max_char_len_song_name: int = 50
    
    # Font sizes (scaled by DPI)
    value_label_fontsize_base: float = 12.0
    song_name_fontsize_base: float = 11.0
    xlabel_fontsize_base: float = 18.0
    tick_label_fontsize_base: float = 11.0
    
    # Rolling stats display config
    rs_panel_area_left_fig: float = 0.03
    rs_panel_area_right_fig: float = 0.25
    rs_panel_title_y_from_top_fig: float = 0.02
    rs_title_to_content_gap_fig: float = 0.01
    rs_title_font_size: float = 11.0
    rs_song_artist_font_size: float = 9.0
    rs_plays_font_size: float = 8.0
    rs_art_height_fig: float = 0.07
    rs_art_aspect_ratio: float = 1.0
    rs_art_max_width_fig: float = 0.07
    rs_art_padding_right_fig: float = 0.005
    rs_text_padding_left_fig: float = 0.005
    rs_text_to_art_horizontal_gap_fig: float = 0.005
    rs_text_line_vertical_spacing_fig: float = 0.02
    rs_song_artist_to_plays_gap_fig: float = 0.025
    rs_inter_panel_vertical_spacing_fig: float = 0.04
    rs_panel_title_x_fig: float = -1.0
    rs_text_truncation_adjust_px: int = 0
    
    # Main timestamp position
    main_timestamp_x_fig: float = -1.0
    main_timestamp_y_fig: float = 0.04
    
    # Nightingale chart settings
    enable_nightingale: bool = True
    nightingale_center_x_fig: float = 0.15
    nightingale_center_y_fig: float = 0.20
    nightingale_radius_fig: float = 0.08
    nightingale_chart_width_fig: float = 0.16
    nightingale_chart_height_fig: float = 0.16
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RenderConfig':
        """Create from dictionary"""
        return cls(**data)
    
    def get_scaled_fontsize(self, base_size: float) -> float:
        """Get font size scaled by DPI"""
        return base_size * (self.dpi / 100.0)


# Global variable to store worker context
WORKER_RENDER_CONFIG: Optional[RenderConfig] = None
WORKER_PID_REPORTED = False


def _validate_album_art_path(relative_path: str, trusted_base_dir: str) -> Optional[str]:
    """
    Validate album art path to prevent path traversal attacks.
    
    Args:
        relative_path: Path from frame_spec (potentially user-controlled)
        trusted_base_dir: Trusted base directory for album art
        
    Returns:
        Validated absolute path if safe, None if unsafe
    """
    try:
        # Get absolute path to trusted base directory
        trusted_root = os.path.realpath(trusted_base_dir)
        
        # Handle case where relative_path might already be absolute or have traversal attempts
        if os.path.isabs(relative_path):
            # Absolute paths are not allowed - potential security risk
            print(f"Security warning: Absolute path rejected: {relative_path}")
            return None
        
        # Additional check for obvious traversal patterns (cross-platform)
        if '..' in relative_path or '\\' in relative_path:
            print(f"Security warning: Path traversal pattern detected: {relative_path}")
            return None
        
        # Join with trusted root and resolve to canonical path
        candidate_path = os.path.join(trusted_root, relative_path)
        resolved_path = os.path.realpath(candidate_path)
        
        # Security check: ensure resolved path is within trusted directory
        if not resolved_path.startswith(trusted_root + os.sep) and resolved_path != trusted_root:
            print(f"Security warning: Path traversal attempt blocked: {relative_path}")
            return None
            
        return resolved_path
        
    except Exception as e:
        print(f"Path validation error for {relative_path}: {e}")
        return None


def initialize_render_worker(render_config_dict: Dict[str, Any]):
    """
    Initialize a worker process for rendering.
    Called once per worker process when the pool is created.
    
    Args:
        render_config_dict: Serialized RenderConfig dictionary
    """
    global WORKER_RENDER_CONFIG, WORKER_PID_REPORTED
    
    try:
        # CRITICAL: Set matplotlib backend before any other matplotlib imports
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend for headless rendering
        
        # Now safe to import other matplotlib modules
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
        
        # Reconstruct config object
        WORKER_RENDER_CONFIG = RenderConfig.from_dict(render_config_dict)
        
        # Register fonts for this worker process
        registered_fonts = []
        for font_name, font_path in WORKER_RENDER_CONFIG.font_paths.items():
            if os.path.exists(font_path):
                try:
                    fm.fontManager.addfont(font_path)
                    
                    # Get the actual font family name
                    font_props = fm.FontProperties(fname=font_path)
                    family_name = font_props.get_name()
                    registered_fonts.append(family_name)
                    
                except Exception as e:
                    print(f"[Worker PID: {os.getpid()}] Warning: Could not register font {font_name} from {font_path}: {e}")
        
        # Set preferred fonts for this process
        if WORKER_RENDER_CONFIG.preferred_fonts:
            try:
                plt.rcParams['font.family'] = WORKER_RENDER_CONFIG.preferred_fonts
            except Exception as e:
                print(f"[Worker PID: {os.getpid()}] Warning: Could not set preferred fonts: {e}")
        
        # Force matplotlib to rebuild font cache for this process
        try:
            fm._load_fontmanager(try_read_cache=False)
        except Exception as e:
            print(f"[Worker PID: {os.getpid()}] Warning: Font cache reload failed: {e}")
        
        print(f"[Worker PID: {os.getpid()}] Initialized successfully. Registered {len(registered_fonts)} fonts.")
        
    except Exception as e:
        print(f"[Worker PID: {os.getpid()}] CRITICAL: Worker initialization failed: {e}")
        raise


def render_frame_from_spec(frame_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Completely stateless frame renderer.
    
    Args:
        frame_spec: JSON-serializable dictionary containing all data needed to render one frame
        
    Returns:
        Dictionary with render result: {'status': 'success'/'error', 'frame_index': int, ...}
    """
    global WORKER_RENDER_CONFIG, WORKER_PID_REPORTED
    
    if WORKER_RENDER_CONFIG is None:
        return {
            'status': 'error',
            'error_type': 'worker_fatal',
            'frame_index': frame_spec.get('frame_index', -1),
            'error': 'Worker not properly initialized - WORKER_RENDER_CONFIG is None',
            'worker_pid': os.getpid()
        }
    
    # Log worker startup once per process
    if not WORKER_PID_REPORTED:
        print(f"--- Worker process with PID {os.getpid()} is processing frames ---")
        WORKER_PID_REPORTED = True
    
    frame_start_time = time.monotonic()
    fig = None
    
    try:
        # Import matplotlib modules (already safe since backend is set)
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
        import numpy as np
        from matplotlib.offsetbox import OffsetImage, AnnotationBbox
        from PIL import Image
        import matplotlib.patheffects as path_effects
        import matplotlib.font_manager as fm
        
        # Import text truncation utility
        from text_utils import truncate_to_fit
        
        # Extract frame data
        frame_index = frame_spec.get('frame_index', 0)
        display_timestamp_str = frame_spec.get('display_timestamp', '')
        bars = frame_spec.get('bars', [])
        dynamic_x_axis_limit = frame_spec.get('dynamic_x_axis_limit', 100)
        rolling_stats = frame_spec.get('rolling_stats', {})
        nightingale_data = frame_spec.get('nightingale_data', {})
        visualization_mode = frame_spec.get('visualization_mode', 'tracks')
        
        # Calculate figure size
        figsize_w = WORKER_RENDER_CONFIG.fig_width_pixels / WORKER_RENDER_CONFIG.dpi
        figsize_h = WORKER_RENDER_CONFIG.fig_height_pixels / WORKER_RENDER_CONFIG.dpi
        
        # Create figure
        fig, ax = plt.subplots(figsize=(figsize_w, figsize_h), dpi=WORKER_RENDER_CONFIG.dpi)
        
        # Parse timestamp for display
        try:
            from datetime import datetime
            if display_timestamp_str:
                if display_timestamp_str.endswith('Z'):
                    timestamp_dt = datetime.fromisoformat(display_timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp_dt = datetime.fromisoformat(display_timestamp_str)
                date_str = timestamp_dt.strftime('%d %B %Y %H:%M:%S')
            else:
                date_str = 'Unknown Date'
        except Exception:
            date_str = display_timestamp_str or 'Unknown Date'
        
        # Set up axes
        ax.set_xlabel("Total Plays", 
                     fontsize=WORKER_RENDER_CONFIG.get_scaled_fontsize(WORKER_RENDER_CONFIG.xlabel_fontsize_base),
                     labelpad=15 * (WORKER_RENDER_CONFIG.dpi/100.0))
        
        ax.set_xlim(0, dynamic_x_axis_limit)
        ax.set_ylim(WORKER_RENDER_CONFIG.n_bars - 0.5, -0.5)  # Inverted: 0 is top
        
        # Format x-axis
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        ax.xaxis.set_ticks_position('top')
        ax.xaxis.set_label_position('top')
        
        tick_label_fontsize = WORKER_RENDER_CONFIG.get_scaled_fontsize(WORKER_RENDER_CONFIG.tick_label_fontsize_base)
        ax.tick_params(axis='x', labelsize=tick_label_fontsize)
        
        # Set up y-axis
        ax.set_yticks(np.arange(WORKER_RENDER_CONFIG.n_bars))
        ax.set_yticklabels([])
        ax.tick_params(axis='y', length=0)
        
        # Calculate font sizes and spacing
        value_label_fontsize = WORKER_RENDER_CONFIG.get_scaled_fontsize(WORKER_RENDER_CONFIG.value_label_fontsize_base)
        song_name_fontsize = WORKER_RENDER_CONFIG.get_scaled_fontsize(WORKER_RENDER_CONFIG.song_name_fontsize_base)
        
        # Calculate spacing in data units
        image_padding_data_units = dynamic_x_axis_limit * 0.005
        value_label_padding_data_units = dynamic_x_axis_limit * 0.008
        song_name_padding_from_left_spine_data_units = dynamic_x_axis_limit * 0.005
        
        # Render bars
        for bar in bars:
            entity_id = bar.get('entity_id', '')
            interpolated_plays = bar.get('interpolated_play_count', 0)
            interpolated_y_pos = bar.get('interpolated_y_position', 0)
            display_name = bar.get('display_name', entity_id)
            bar_color = bar.get('bar_color_rgba', (0.5, 0.5, 0.5, 1.0))
            album_art_path = bar.get('album_art_path', '')
            
            if interpolated_plays < 0.01:
                continue
            
            # Draw bar
            ax.barh(interpolated_y_pos, interpolated_plays, 
                   color=bar_color, height=0.8, zorder=2, align='center')
            
            # Load album art if available (with security validation)
            pil_image = None
            if album_art_path:
                try:
                    # Security: Validate album art path to prevent path traversal attacks
                    validated_path = _validate_album_art_path(album_art_path, WORKER_RENDER_CONFIG.album_art_cache_dir)
                    if validated_path and os.path.exists(validated_path):
                        pil_image = Image.open(validated_path)
                except Exception as e:
                    print(f"[Worker PID: {os.getpid()}] Warning: Could not load album art {album_art_path}: {e}")
            
            # Calculate text positioning
            text_bbox_props = dict(boxstyle="round,pad=0.2,rounding_size=0.1", 
                                 facecolor="#333333", alpha=0.5, edgecolor="none")
            
            start_x_data = song_name_padding_from_left_spine_data_units
            right_gap_units = dynamic_x_axis_limit * WORKER_RENDER_CONFIG.song_text_right_gap_fraction
            
            if pil_image:
                resized_img_w_pix, _ = pil_image.size
                image_width_units = (resized_img_w_pix / WORKER_RENDER_CONFIG.fig_width_pixels) * dynamic_x_axis_limit
                art_nudge_units = dynamic_x_axis_limit * 0.0175
                art_left_edge = interpolated_plays - image_width_units - art_nudge_units
                end_x_data = art_left_edge - right_gap_units
            else:
                end_x_data = interpolated_plays - value_label_padding_data_units - right_gap_units
            
            # Calculate available text width and truncate properly
            available_px = 0
            text_to_display = display_name
            
            if end_x_data > start_x_data:
                ax_width_in_fig_coords = WORKER_RENDER_CONFIG.right_margin_ax - WORKER_RENDER_CONFIG.left_margin_ax
                ax_width_pixels = ax_width_in_fig_coords * WORKER_RENDER_CONFIG.fig_width_pixels
                available_px = (end_x_data - start_x_data) / dynamic_x_axis_limit * ax_width_pixels
                
                # Account for text bbox padding
                bbox_pad_multiplier = 0.2
                bbox_horizontal_padding_points = 2 * bbox_pad_multiplier * song_name_fontsize
                bbox_horizontal_padding_pixels = bbox_horizontal_padding_points * (WORKER_RENDER_CONFIG.dpi / 72.0)
                available_px -= bbox_horizontal_padding_pixels
                
                # Apply manual adjustment from configuration
                available_px += WORKER_RENDER_CONFIG.bar_text_truncation_adjust_px
                
                # Use proper text truncation with font metrics
                if available_px > 0:
                    font_props = fm.FontProperties(size=song_name_fontsize)
                    renderer = fig.canvas.get_renderer()
                    text_to_display = truncate_to_fit(display_name, font_props, renderer, max(0, available_px))
            
            # Draw song text
            song_text_obj = ax.text(
                song_name_padding_from_left_spine_data_units,
                interpolated_y_pos,
                text_to_display,
                va="center",
                ha="left",
                fontsize=song_name_fontsize,
                color="white",
                zorder=5,
                bbox=text_bbox_props,
            )
            
            # Draw album art
            if pil_image:
                try:
                    resized_img_width_pixels, resized_img_height_pixels = pil_image.size
                    image_width_data_units = (resized_img_width_pixels / WORKER_RENDER_CONFIG.fig_width_pixels) * dynamic_x_axis_limit
                    
                    art_horizontal_nudge_factor = 0.0175
                    img_center_x_pos = interpolated_plays - (image_width_data_units / 2.0) - (dynamic_x_axis_limit * art_horizontal_nudge_factor)
                    
                    min_x_for_image_start = dynamic_x_axis_limit * 0.02
                    if img_center_x_pos - (image_width_data_units / 2.0) > min_x_for_image_start:
                        imagebox = OffsetImage(pil_image, zoom=1.0, resample=False)
                        ab = AnnotationBbox(imagebox, (img_center_x_pos, interpolated_y_pos),
                                          xybox=(0,0), xycoords='data', boxcoords="offset points",
                                          pad=0, frameon=False, zorder=3)
                        ax.add_artist(ab)
                except Exception as e:
                    print(f"[Worker PID: {os.getpid()}] Error adding album art for {entity_id}: {e}")
            
            # Draw play count label
            text_x_pos_for_value = interpolated_plays + value_label_padding_data_units
            ax.text(
                text_x_pos_for_value,
                interpolated_y_pos,
                f"{int(round(interpolated_plays))}",
                va="center",
                ha="left",
                fontsize=value_label_fontsize,
                weight="bold",
                zorder=4,
            )
        
        # Style the plot
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_linewidth(1.5 * (WORKER_RENDER_CONFIG.dpi/100.0))
        ax.grid(True, axis='y', linestyle=':', color='lightgray', alpha=0.7, zorder=0)
        
        # Apply layout
        try:
            fig.tight_layout(rect=[WORKER_RENDER_CONFIG.left_margin_ax, WORKER_RENDER_CONFIG.bottom_margin_ax,
                                  WORKER_RENDER_CONFIG.right_margin_ax, WORKER_RENDER_CONFIG.top_margin_ax])
        except Exception as e_layout:
            print(f"[Worker PID: {os.getpid()}] Layout adjustment warning: {e_layout}")
            plt.subplots_adjust(left=WORKER_RENDER_CONFIG.left_margin_ax, 
                              bottom=WORKER_RENDER_CONFIG.bottom_margin_ax,
                              right=WORKER_RENDER_CONFIG.right_margin_ax, 
                              top=WORKER_RENDER_CONFIG.top_margin_ax, 
                              wspace=0, hspace=0)
        
        # TODO: Add rolling stats panels and nightingale chart rendering
        # For now, just add the timestamp
        timestamp_x = 0.98 if WORKER_RENDER_CONFIG.main_timestamp_x_fig < 0 else WORKER_RENDER_CONFIG.main_timestamp_x_fig
        timestamp_y = WORKER_RENDER_CONFIG.main_timestamp_y_fig
        
        fig.text(timestamp_x, timestamp_y, date_str, 
                transform=fig.transFigure, ha='right', va='bottom',
                fontsize=20 * (WORKER_RENDER_CONFIG.dpi/100.0), 
                color='dimgray', weight='bold')
        
        # Save the frame
        output_path = f"frames/frame_{frame_index:06d}.png"
        os.makedirs("frames", exist_ok=True)
        
        fig.savefig(output_path, dpi=WORKER_RENDER_CONFIG.dpi, 
                   bbox_inches='tight', facecolor='white')
        
        render_time = time.monotonic() - frame_start_time
        
        return {
            'status': 'success',
            'frame_index': frame_index,
            'output_path': output_path,
            'render_time_seconds': render_time,
            'worker_pid': os.getpid()
        }
        
    except Exception as e:
        render_time = time.monotonic() - frame_start_time
        # Determine error type based on the exception
        error_type = 'frame_fatal'  # Default to frame-specific error
        
        if isinstance(e, MemoryError):
            error_type = 'worker_fatal'
        elif isinstance(e, (OSError, IOError)) and 'No space left on device' in str(e):
            error_type = 'worker_fatal'
        elif isinstance(e, FileNotFoundError):
            error_type = 'transient'
        
        return {
            'status': 'error',
            'error_type': error_type,
            'frame_index': frame_spec.get('frame_index', -1),
            'error': str(e),
            'render_time_seconds': render_time,
            'worker_pid': os.getpid()
        }
    finally:
        # CRITICAL: Always close the figure to prevent memory leaks
        if fig is not None:
            plt.close(fig)


def create_render_config_from_app_config(app_config) -> RenderConfig:
    """
    Create a RenderConfig from the main application configuration.
    
    Args:
        app_config: AppConfig object from config_loader
        
    Returns:
        RenderConfig object ready for serialization
    """
    # Get video resolution settings
    video_resolution = app_config.get('AnimationOutput', 'VIDEO_RESOLUTION', '1080p')
    resolution_presets = {
        "1080p": {"width": 1920, "height": 1080, "dpi": 96},
        "4k": {"width": 3840, "height": 2160, "dpi": 165}
    }
    
    if video_resolution in resolution_presets:
        res_config = resolution_presets[video_resolution]
        fig_width = res_config["width"]
        fig_height = res_config["height"] 
        dpi = res_config["dpi"]
    else:
        # Fallback to 1080p
        fig_width = 1920
        fig_height = 1080
        dpi = 96
    
    # Build font paths dictionary
    font_paths = {}
    custom_font_dir = app_config.get('FontPreferences', 'CUSTOM_FONT_DIR', 'fonts')
    
    if os.path.exists(custom_font_dir):
        for font_file in os.listdir(custom_font_dir):
            if font_file.endswith(('.ttf', '.otf')):
                font_name = os.path.splitext(font_file)[0]
                font_paths[font_name] = os.path.join(custom_font_dir, font_file)
    
    # Get preferred fonts list
    preferred_fonts_str = app_config.get('FontPreferences', 'PREFERRED_FONTS', 
                                        'DejaVu Sans,Noto Sans JP,Noto Sans KR,Arial Unicode MS,sans-serif')
    preferred_fonts = [font.strip() for font in preferred_fonts_str.split(',')]
    
    return RenderConfig(
        # Basic settings
        dpi=dpi,
        fig_width_pixels=fig_width,
        fig_height_pixels=fig_height,
        target_fps=app_config.get_int('AnimationOutput', 'TARGET_FPS', 30),
        
        # Font settings
        font_paths=font_paths,
        preferred_fonts=preferred_fonts,
        
        # Album art settings
        album_art_cache_dir=app_config.get('AlbumArtSpotify', 'ALBUM_ART_CACHE_DIR', 'album_art_cache'),
        album_art_visibility_threshold=app_config.get_float('AlbumArtSpotify', 'ALBUM_ART_VISIBILITY_THRESHOLD_FACTOR', 0.0628),
        
        # Layout settings
        n_bars=app_config.get_int('AnimationOutput', 'N_BARS', 10),
        
        # Text settings
        song_text_right_gap_fraction=app_config.get_float('AlbumArtSpotify', 'SONG_TEXT_RIGHT_GAP_FRACTION', 0.032),
        bar_text_truncation_adjust_px=app_config.get_int('AlbumArtSpotify', 'BAR_TEXT_TRUNCATION_ADJUST_PX', 0),
        
        # Rolling stats settings (load from config)
        rs_panel_area_left_fig=app_config.get_float('RollingStatsDisplay', 'ROLLING_PANEL_AREA_LEFT_FIG', 0.03),
        rs_panel_area_right_fig=app_config.get_float('RollingStatsDisplay', 'ROLLING_PANEL_AREA_RIGHT_FIG', 0.25),
        rs_panel_title_y_from_top_fig=app_config.get_float('RollingStatsDisplay', 'ROLLING_PANEL_TITLE_Y_FROM_TOP_FIG', 0.02),
        rs_title_to_content_gap_fig=app_config.get_float('RollingStatsDisplay', 'ROLLING_TITLE_TO_CONTENT_GAP_FIG', 0.01),
        rs_title_font_size=app_config.get_float('RollingStatsDisplay', 'ROLLING_TITLE_FONT_SIZE', 11.0),
        rs_song_artist_font_size=app_config.get_float('RollingStatsDisplay', 'ROLLING_SONG_ARTIST_FONT_SIZE', 9.0),
        rs_plays_font_size=app_config.get_float('RollingStatsDisplay', 'ROLLING_PLAYS_FONT_SIZE', 8.0),
        rs_art_height_fig=app_config.get_float('RollingStatsDisplay', 'ROLLING_ART_HEIGHT_FIG', 0.07),
        rs_art_aspect_ratio=app_config.get_float('RollingStatsDisplay', 'ROLLING_ART_ASPECT_RATIO', 1.0),
        rs_art_max_width_fig=app_config.get_float('RollingStatsDisplay', 'ROLLING_ART_MAX_WIDTH_FIG', 0.07),
        rs_art_padding_right_fig=app_config.get_float('RollingStatsDisplay', 'ROLLING_ART_PADDING_RIGHT_FIG', 0.005),
        rs_text_padding_left_fig=app_config.get_float('RollingStatsDisplay', 'ROLLING_TEXT_PADDING_LEFT_FIG', 0.005),
        rs_text_to_art_horizontal_gap_fig=app_config.get_float('RollingStatsDisplay', 'ROLLING_TEXT_TO_ART_HORIZONTAL_GAP_FIG', 0.005),
        rs_text_line_vertical_spacing_fig=app_config.get_float('RollingStatsDisplay', 'ROLLING_TEXT_LINE_VERTICAL_SPACING_FIG', 0.02),
        rs_song_artist_to_plays_gap_fig=app_config.get_float('RollingStatsDisplay', 'ROLLING_SONG_ARTIST_TO_PLAYS_VERTICAL_GAP_FIG', 0.025),
        rs_inter_panel_vertical_spacing_fig=app_config.get_float('RollingStatsDisplay', 'ROLLING_INTER_PANEL_VERTICAL_SPACING_FIG', 0.04),
        rs_panel_title_x_fig=app_config.get_float('RollingStatsDisplay', 'ROLLING_PANEL_TITLE_X_FIG', -1.0),
        rs_text_truncation_adjust_px=app_config.get_int('RollingStatsDisplay', 'ROLLING_TEXT_TRUNCATION_ADJUST_PX', 0),
        
        # Main timestamp settings
        main_timestamp_x_fig=app_config.get_float('AnimationOutput', 'MAIN_TIMESTAMP_X_FIG', -1.0),
        main_timestamp_y_fig=app_config.get_float('AnimationOutput', 'MAIN_TIMESTAMP_Y_FIG', 0.04),
        
        # Nightingale chart settings
        enable_nightingale=app_config.get_bool('NightingaleChart', 'ENABLE', True),
        nightingale_center_x_fig=app_config.get_float('NightingaleChart', 'NIGHTINGALE_CENTER_X_FIG', 0.15),
        nightingale_center_y_fig=app_config.get_float('NightingaleChart', 'NIGHTINGALE_CENTER_Y_FIG', 0.20),
        nightingale_radius_fig=app_config.get_float('NightingaleChart', 'NIGHTINGALE_RADIUS_FIG', 0.08),
        nightingale_chart_width_fig=app_config.get_float('NightingaleChart', 'NIGHTINGALE_CHART_WIDTH_FIG', 0.16),
        nightingale_chart_height_fig=app_config.get_float('NightingaleChart', 'NIGHTINGALE_CHART_HEIGHT_FIG', 0.16),
    )


if __name__ == "__main__":
    # Test module can be run independently
    print("Stateless renderer module loaded successfully")
    
    # Create a minimal test config
    test_config = RenderConfig(
        dpi=96, fig_width_pixels=1920, fig_height_pixels=1080, target_fps=30,
        font_paths={}, preferred_fonts=['DejaVu Sans'], 
        album_art_cache_dir='album_art_cache', album_art_visibility_threshold=0.0628,
        n_bars=10
    )
    
    print(f"Test config created: {test_config.dpi}x{test_config.fig_width_pixels}x{test_config.fig_height_pixels}")