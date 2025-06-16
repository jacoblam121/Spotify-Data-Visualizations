"""
Frame drawing logic extracted from main_animator.
This module contains the pure drawing logic without any multiprocessing concerns.
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects
import matplotlib.font_manager as fm
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import numpy as np
from PIL import Image
from typing import Dict, Any, Optional

from render_config import RenderConfig
from text_utils import truncate_to_fit
from nightingale_chart import draw_nightingale_chart


def draw_frame_content(fig, ax, render_task: Dict, config: RenderConfig,
                      entity_id_to_canonical_name_map: Dict,
                      entity_details_map: Dict,
                      album_art_image_objects: Dict,
                      album_art_image_objects_highres: Dict,
                      album_bar_colors: Dict):
    """Draw all content for a single frame.
    
    This function is pure - it takes all inputs explicitly and draws to the provided figure/axis.
    No global variables or multiprocessing concerns here.
    """
    # Extract frame data
    overall_frame_idx = render_task['overall_frame_index']
    display_timestamp = render_task['display_timestamp']
    bar_render_data_list = render_task['bar_render_data_list']
    rolling_window_info = render_task.get('rolling_window_info', {'top_7_day': None, 'top_30_day': None})
    nightingale_info = render_task.get('nightingale_info', {})
    
    # Define margins for layout
    left_margin_ax = 0.28
    right_margin_ax = 0.985
    bottom_margin_ax = 0.08
    top_margin_ax = 0.98
    
    # --- Main Chart Area Setup ---
    date_str = display_timestamp.strftime('%d %B %Y %H:%M:%S')
    
    ax.set_xlabel("Total Plays", fontsize=18 * (config.video_dpi/100.0), labelpad=15 * (config.video_dpi/100.0))
    
    # Dynamic X-axis limit calculation
    current_frame_max_play_count = 0
    if bar_render_data_list:
        visible_play_counts = [item['interpolated_play_count'] 
                             for item in bar_render_data_list 
                             if item['interpolated_play_count'] > 0.1]
        if visible_play_counts:
            current_frame_max_play_count = max(visible_play_counts)
    
    dynamic_x_axis_limit = max(10, current_frame_max_play_count) * 1.10
    ax.set_xlim(0, dynamic_x_axis_limit)
    
    ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    ax.xaxis.set_ticks_position('top')
    ax.xaxis.set_label_position('top')
    tick_label_fontsize = 11 * (config.video_dpi/100.0)
    ax.tick_params(axis='x', labelsize=tick_label_fontsize)
    
    # Y-axis setup
    ax.set_ylim(config.n_bars - 0.5, -0.5)
    ax.set_yticks(np.arange(config.n_bars))
    ax.set_yticklabels([])
    ax.tick_params(axis='y', length=0)
    
    # Text sizing parameters
    max_char_len_song_name = int(50 * (150.0/config.video_dpi))
    value_label_fontsize = 12 * (config.video_dpi/100.0)
    song_name_fontsize = tick_label_fontsize
    
    image_padding_data_units = dynamic_x_axis_limit * 0.005
    value_label_padding_data_units = dynamic_x_axis_limit * 0.008
    song_name_padding_from_left_spine_data_units = dynamic_x_axis_limit * 0.005
    
    # --- Draw Bars ---
    for bar_item_data in bar_render_data_list:
        entity_id = bar_item_data['entity_id']
        interpolated_plays = bar_item_data['interpolated_play_count']
        interpolated_y_pos = bar_item_data['interpolated_y_position']
        
        if interpolated_plays < 0.01:
            continue
        
        # Get entity details
        canonical_name = entity_id_to_canonical_name_map.get(entity_id, entity_id)
        entity_details = entity_details_map.get(canonical_name, {})
        display_name = entity_details.get('display_name', entity_id)
        
        # Get bar color
        bar_color = album_bar_colors.get(canonical_name, 'skyblue')
        
        # Draw the bar
        barh = ax.barh(interpolated_y_pos, interpolated_plays, height=0.9, color=bar_color)
        
        # Add value label
        ax.text(interpolated_plays + value_label_padding_data_units, interpolated_y_pos,
                f'{int(interpolated_plays):,}', ha='left', va='center',
                fontsize=value_label_fontsize, weight='bold')
        
        # Add entity name
        name_x_pos = song_name_padding_from_left_spine_data_units
        
        # Calculate available width for text
        available_width_pixels = ax.transData.transform((dynamic_x_axis_limit * config.song_text_right_gap_fraction, 0))[0] - \
                               ax.transData.transform((name_x_pos, 0))[0]
        
        # Create font properties for truncation
        font_props = fm.FontProperties(family=config.preferred_fonts, size=song_name_fontsize)
        renderer = fig.canvas.get_renderer()
        truncated_name = truncate_to_fit(
            display_name, font_props, renderer, available_width_pixels
        )
        
        # Define text properties for the semi-transparent gray background
        text_bbox_props = dict(boxstyle="round,pad=0.2,rounding_size=0.1", facecolor="#333333", alpha=0.5, edgecolor="none")
        
        ax.text(name_x_pos, interpolated_y_pos, truncated_name,
                ha='left', va='center', fontsize=song_name_fontsize, weight='bold',
                bbox=text_bbox_props)
        
        # Add album art if visible
        if config.visualization_mode == 'tracks' and interpolated_plays > dynamic_x_axis_limit * config.album_art_visibility_threshold_factor:
            if canonical_name in album_art_image_objects:
                try:
                    art_size = 0.9
                    imagebox = OffsetImage(album_art_image_objects[canonical_name], zoom=art_size)
                    ab = AnnotationBbox(imagebox, (interpolated_plays + image_padding_data_units, interpolated_y_pos),
                                      xycoords='data', frameon=False, pad=0)
                    ax.add_artist(ab)
                except Exception as e:
                    if config.debug_album_art_logic:
                        print(f"Error adding album art for {canonical_name}: {e}")
    
    # Set the subplot position
    ax.set_position([left_margin_ax, bottom_margin_ax, 
                    right_margin_ax - left_margin_ax, 
                    top_margin_ax - bottom_margin_ax])
    
    # --- Draw Timestamp ---
    timestamp_x_pos = config.main_timestamp_x_fig if config.main_timestamp_x_fig >= 0 else (left_margin_ax + right_margin_ax) / 2
    fig.text(timestamp_x_pos, config.main_timestamp_y_fig, date_str,
             ha='center', va='center', fontsize=20 * (config.video_dpi/100.0),
             color='dimgray', weight='bold', transform=fig.transFigure)
    
    # --- Draw Rolling Stats Panels ---
    if rolling_window_info['top_7_day'] is not None or rolling_window_info['top_30_day'] is not None:
        _draw_rolling_stats_panels(fig, rolling_window_info, entity_details_map,
                                 album_art_image_objects_highres, config)
    
    # --- Draw Nightingale Chart ---
    if config.enable_nightingale and nightingale_info:
        try:
            nightingale_ax = fig.add_axes([
                config.nightingale_center_x_fig - config.nightingale_radius_fig * 1.5,
                config.nightingale_center_y_fig - config.nightingale_radius_fig * 1.5,
                config.nightingale_radius_fig * 3,
                config.nightingale_radius_fig * 3
            ])
            
            # Create chart config from render config
            chart_config = {
                'ENABLE': config.enable_nightingale,
                'CHART_X': config.nightingale_center_x_fig,
                'CHART_Y': config.nightingale_center_y_fig,
                'CHART_RADIUS': config.nightingale_radius_fig,
                'SHOW_MONTH_LABELS': config.nightingale_show_period_labels,
                'MONTH_LABEL_DISTANCE': config.nightingale_label_radius_ratio,
                'MONTH_LABEL_FONT_SIZE': config.nightingale_label_font_size,
                'MONTH_LABEL_COLOR': config.nightingale_label_font_color,
                'MONTH_LABEL_FONT_WEIGHT': config.nightingale_label_font_weight,
                'SHOW_HIGH_LOW': config.nightingale_show_high_low_info,
                'HIGH_LOW_FONT_SIZE': config.nightingale_high_low_font_size,
                'HIGH_LOW_POSITION_BELOW_CHART': config.nightingale_high_low_y_offset_fig,
                'HIGH_LOW_SPACING': config.nightingale_high_low_spacing_fig,
                'TITLE_FONT_SIZE': config.nightingale_title_font_size,
                'TITLE_FONT_WEIGHT': config.nightingale_title_font_weight,
                'TITLE_COLOR': config.nightingale_title_color,
                'TITLE_POSITION_ABOVE_CHART': config.nightingale_title_position_above_chart,
                'HIGH_PERIOD_COLOR': config.nightingale_high_period_color,
                'LOW_PERIOD_COLOR': config.nightingale_low_period_color,
                'SHOW_BOUNDARY_CIRCLE': config.nightingale_show_boundary_circle,
                'BOUNDARY_CIRCLE_COLOR': config.nightingale_outer_circle_color,
                'BOUNDARY_CIRCLE_STYLE': config.nightingale_outer_circle_linestyle,
                'BOUNDARY_CIRCLE_WIDTH': config.nightingale_outer_circle_linewidth,
                'DEBUG_MODE': config.nightingale_debug
            }
            
            draw_nightingale_chart(
                fig=fig,
                nightingale_data=nightingale_info,
                chart_config=chart_config
            )
        except Exception as e:
            print(f"Error drawing nightingale chart: {e}")


def _draw_rolling_stats_panels(fig, rolling_window_info, entity_details_map,
                             album_art_image_objects_highres, config: RenderConfig):
    """Draw the 7-day and 30-day rolling stats panels."""
    
    panels_data = []
    if rolling_window_info['top_7_day'] is not None:
        panels_data.append(('Top Songs - Last 7 Days', rolling_window_info['top_7_day']))
    if rolling_window_info['top_30_day'] is not None:
        panels_data.append(('Top Songs - Last 30 Days', rolling_window_info['top_30_day']))
    
    if config.visualization_mode == 'artists':
        panels_data = [(title.replace('Songs', 'Artists'), data) for title, data in panels_data]
    
    # Calculate panel dimensions
    panel_width_fig = config.rolling_panel_area_right_fig - config.rolling_panel_area_left_fig
    
    # Starting Y position for first panel
    current_y_top = 1.0 - config.rolling_panel_title_y_from_top_fig
    
    for panel_idx, (panel_title, panel_songs) in enumerate(panels_data):
        # Panel title position
        title_x = config.rolling_panel_title_x_fig if config.rolling_panel_title_x_fig >= 0 else (config.rolling_panel_area_left_fig + config.rolling_panel_area_right_fig) / 2
        title_ha = 'left' if config.rolling_panel_title_x_fig >= 0 else 'center'
        
        fig.text(title_x, current_y_top, panel_title,
                ha=title_ha, va='top', fontsize=config.rolling_title_font_size,
                weight='bold', transform=fig.transFigure)
        
        # Start drawing songs
        current_y = current_y_top - config.rolling_title_to_content_gap_fig - config.rolling_title_font_size / 72
        
        # Rolling stats only returns the single top track/artist, not a list
        if panel_songs:
            # Extract entity info from the single top track/artist
            if config.visualization_mode == 'tracks':
                entity_name = panel_songs.get('song_id', '')
                play_count = panel_songs.get('plays', 0)
            else:
                entity_name = panel_songs.get('artist_id', '')
                play_count = panel_songs.get('plays', 0)
            
            # Get entity details
            entity_details = entity_details_map.get(entity_name, {})
            display_name = entity_details.get('display_name', entity_name)
            
            # Album art position
            art_left_x = config.rolling_panel_area_left_fig
            art_center_y = current_y - config.rolling_art_height_fig / 2
            
            # Add album art if available
            if entity_name in album_art_image_objects_highres:
                try:
                    art_ax = fig.add_axes([art_left_x, art_center_y - config.rolling_art_height_fig/2,
                                         config.rolling_art_max_width_fig, config.rolling_art_height_fig])
                    art_ax.imshow(album_art_image_objects_highres[entity_name])
                    art_ax.axis('off')
                except Exception as e:
                    if config.debug_album_art_logic:
                        print(f"Error adding rolling stats art for {entity_name}: {e}")
            
            # Text position
            text_left_x = art_left_x + config.rolling_art_max_width_fig + config.rolling_text_to_art_horizontal_gap_fig
            text_right_x = config.rolling_panel_area_right_fig - config.rolling_text_padding_left_fig
            
            # Calculate available width for text
            text_width_fig = text_right_x - text_left_x
            text_width_pixels = text_width_fig * config.video_width + config.rolling_text_truncation_adjust_px
            
            # Truncate and draw entity name (no rank needed - just one item)
            font_props = fm.FontProperties(family=config.preferred_fonts, size=config.rolling_song_artist_font_size)
            renderer = fig.canvas.get_renderer()
            truncated_name = truncate_to_fit(
                display_name,
                font_props,
                renderer,
                text_width_pixels
            )
            
            fig.text(text_left_x, current_y, truncated_name,
                    ha='left', va='top', fontsize=config.rolling_song_artist_font_size,
                    weight='bold', transform=fig.transFigure)
            
            # Play count
            fig.text(text_left_x, current_y - config.rolling_song_artist_to_plays_vertical_gap_fig,
                    f"{play_count} plays",
                    ha='left', va='top', fontsize=config.rolling_plays_font_size,
                    transform=fig.transFigure)
            
            # Move to next item
            current_y -= (config.rolling_art_height_fig + config.rolling_text_line_vertical_spacing_fig)
        
        # Add spacing before next panel
        current_y -= config.rolling_inter_panel_vertical_spacing_fig