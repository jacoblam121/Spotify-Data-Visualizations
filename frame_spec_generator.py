# frame_spec_generator.py
"""
Memory-efficient frame specification generator for Spotify data visualization.
Converts frame preparation from loading all frames into memory to streaming generation.

This module implements Task 2 of the parallel processing approach:
- Task 1: Stateless renderer (completed)
- Task 2: Generator pipeline (this module)  
- Task 3: Parallel manager (future)
"""

import pandas as pd
from typing import Dict, Any, Iterator, Optional, List
import logging

# Import existing utility function from main_animator
try:
    from main_animator import make_json_serializable
except ImportError:
    # Fallback implementation if import fails
    def make_json_serializable(obj):
        """Fallback JSON serialization for basic types."""
        if obj is None:
            return None
        elif isinstance(obj, dict):
            return {k: make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_json_serializable(item) for item in obj]
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return obj

# Configure logging
logger = logging.getLogger(__name__)

class FrameSpecGenerator:
    """
    Memory-efficient generator for frame specifications.
    
    Yields frame specs one at a time instead of loading all into memory.
    Maintains state for frame-to-frame continuity in animations.
    
    Key benefits:
    - Memory usage: O(1) instead of O(num_frames)
    - Compatible with existing stateless renderer
    - Thread-safe when used with producer-consumer pattern
    """
    
    def __init__(self, 
                 all_render_tasks: List[Dict[str, Any]],
                 entity_id_to_canonical_name_map: Dict[str, str],
                 entity_details_map: Dict[str, Dict[str, Any]], 
                 album_bar_colors: Dict[str, tuple],
                 n_bars: int,
                 max_play_count_overall: float,
                 visualization_mode: str):
        """
        Initialize the frame spec generator.
        
        Args:
            all_render_tasks: List of render task dictionaries from generate_render_tasks()
            entity_id_to_canonical_name_map: Maps entity IDs to canonical names for caching
            entity_details_map: Entity metadata for display names
            album_bar_colors: Pre-computed bar colors
            n_bars: Number of bars to display
            max_play_count_overall: Maximum play count for scaling
            visualization_mode: "tracks" or "artists"
        """
        # Store input parameters
        self.all_render_tasks = all_render_tasks
        self.entity_id_to_canonical_name_map = entity_id_to_canonical_name_map
        self.entity_details_map = entity_details_map
        self.album_bar_colors = album_bar_colors
        self.n_bars = n_bars
        self.max_play_count_overall = max_play_count_overall
        self.visualization_mode = visualization_mode
        
        # Iterator state
        self.frame_index = 0
        self.total_frames = len(all_render_tasks)
        
        # Animation state (for frame-to-frame continuity)
        self._previous_bar_positions = {}  # entity_id -> y_position
        self._previous_play_counts = {}    # entity_id -> play_count
        
        # Statistics state (for rolling windows)
        self._stats_state = {}
        
        logger.info(f"FrameSpecGenerator initialized: {self.total_frames} frames, "
                   f"mode={visualization_mode}, n_bars={n_bars}")
    
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Return self as iterator."""
        return self
    
    def __next__(self) -> Dict[str, Any]:
        """
        Generate the next frame specification.
        
        Follows the critical order of operations:
        1. Check for termination
        2. Calculate spec for current frame using current state
        3. Yield the frame spec
        4. Update state for next frame
        5. Increment frame index
        
        Returns:
            Dict containing frame specification compatible with stateless renderer
            
        Raises:
            StopIteration: When all frames have been generated
        """
        # 1. Check for termination
        if self.frame_index >= self.total_frames:
            raise StopIteration
        
        # 2. Calculate spec for current frame using current state
        current_render_task = self.all_render_tasks[self.frame_index]
        frame_spec = self._calculate_frame_spec(current_render_task)
        
        # 3. Update state for next frame (before incrementing index)
        self._update_state_for_next_frame(current_render_task, frame_spec)
        
        # 4. Increment frame index
        self.frame_index += 1
        
        logger.debug(f"Generated frame spec {self.frame_index}/{self.total_frames}")
        
        return frame_spec
    
    def _calculate_frame_spec(self, render_task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate frame specification for the current render task.
        
        This adapts the logic from prepare_frame_spec() but with state management.
        
        Args:
            render_task: Current render task from generate_render_tasks()
            
        Returns:
            Frame specification dictionary
        """
        # Calculate dynamic x-axis limit for this frame
        current_frame_max_play_count = 0
        if render_task['bar_render_data_list']:
            visible_play_counts = [
                item['interpolated_play_count'] 
                for item in render_task['bar_render_data_list'] 
                if item['interpolated_play_count'] > 0.1
            ]
            if visible_play_counts:
                current_frame_max_play_count = max(visible_play_counts)
        
        dynamic_x_axis_limit = max(10, current_frame_max_play_count) * 1.10
        
        # Get rolling stats and nightingale data
        rolling_window_info = render_task.get('rolling_window_info', {'top_7_day': None, 'top_30_day': None})
        nightingale_info = render_task.get('nightingale_info', {})
        
        # Use existing prepare_frame_spec logic
        frame_spec = self._prepare_frame_spec_core(
            render_task,
            self.entity_id_to_canonical_name_map,
            self.entity_details_map,
            self.n_bars,
            dynamic_x_axis_limit,
            rolling_window_info,
            nightingale_info,
            self.visualization_mode
        )
        
        # Add pre-fetched colors to frame spec
        for bar in frame_spec['bars']:
            canonical_key = bar['canonical_key']
            if canonical_key in self.album_bar_colors:
                bar['bar_color_rgba'] = self.album_bar_colors[canonical_key]
        
        return frame_spec
    
    def _prepare_frame_spec_core(self, render_task, entity_id_to_canonical_name_map, entity_details_map,
                                n_bars, dynamic_x_axis_limit, rolling_window_info, nightingale_info,
                                visualization_mode):
        """
        Core frame spec preparation logic adapted from main_animator.py:prepare_frame_spec().
        
        This is essentially a copy of the existing prepare_frame_spec function to maintain
        exact compatibility while allowing for future state-aware modifications.
        """
        # Convert timestamp to string for JSON serialization
        display_timestamp = render_task['display_timestamp']
        if hasattr(display_timestamp, 'isoformat'):
            display_timestamp_str = display_timestamp.isoformat()
        else:
            display_timestamp_str = str(display_timestamp)
        
        frame_spec = {
            'frame_index': render_task['overall_frame_index'],
            'display_timestamp': display_timestamp_str,
            'bars': [],
            'rolling_stats': make_json_serializable(rolling_window_info),
            'nightingale_data': make_json_serializable(nightingale_info),
            'dynamic_x_axis_limit': dynamic_x_axis_limit,
            'visualization_mode': visualization_mode
        }
        
        # Pre-process bar data
        for bar_data in render_task['bar_render_data_list']:
            entity_id = bar_data['entity_id']
            canonical_key = entity_id_to_canonical_name_map.get(entity_id, entity_id)
            entity_details = entity_details_map.get(entity_id, {})
            
            # Get display name based on mode
            if visualization_mode == "artists":
                display_name = entity_details.get('original_artist', 'Unknown Artist')
            else:
                artist_name = entity_details.get('original_artist', 'Unknown Artist')
                track_name = entity_details.get('original_track', 'Unknown Track')
                display_name = f"{track_name} - {artist_name}"
            
            bar_spec = {
                'entity_id': entity_id,
                'canonical_key': canonical_key,
                'display_name': display_name,
                'interpolated_y_pos': bar_data.get('interpolated_y_position', 0.0),
                'interpolated_play_count': bar_data.get('interpolated_play_count', 0.0),
                'bar_color': bar_data.get('bar_color', (0.5, 0.5, 0.5, 1.0)),
                'is_new': bar_data.get('is_new', False),
                'current_rank': bar_data.get('current_rank', -1),
                'entity_details': entity_details
            }
            frame_spec['bars'].append(bar_spec)
        
        return frame_spec
    
    
    def _update_state_for_next_frame(self, current_render_task: Dict[str, Any], frame_spec: Dict[str, Any]):
        """
        Update internal state after generating current frame spec.
        
        This maintains continuity for animations and statistics.
        Currently stores bar positions and play counts for future use.
        
        Args:
            current_render_task: The render task that was just processed  
            frame_spec: The frame spec that was just generated
        """
        # Update bar position tracking for animation continuity
        self._previous_bar_positions.clear()
        self._previous_play_counts.clear()
        
        for bar in frame_spec['bars']:
            entity_id = bar['entity_id']
            self._previous_bar_positions[entity_id] = bar['interpolated_y_pos']
            self._previous_play_counts[entity_id] = bar['interpolated_play_count']
        
        # Update statistics state (placeholder for future rolling window state)
        # This could track rolling statistics that span multiple frames
        frame_index = frame_spec['frame_index']
        self._stats_state[frame_index] = {
            'entities_shown': list(self._previous_bar_positions.keys()),
            'max_play_count': max(self._previous_play_counts.values()) if self._previous_play_counts else 0
        }
        
        # Keep only recent state to prevent memory growth
        if len(self._stats_state) > 100:  # Keep last 100 frames of state
            oldest_key = min(self._stats_state.keys())
            del self._stats_state[oldest_key]
        
        logger.debug(f"Updated state: {len(self._previous_bar_positions)} bars tracked")
    
    def reset(self):
        """
        Reset the generator to start over from the beginning.
        
        This is useful for testing and debugging. In production,
        create a new generator instance instead.
        """
        self.frame_index = 0
        self._previous_bar_positions.clear()
        self._previous_play_counts.clear()
        self._stats_state.clear()
        logger.info("FrameSpecGenerator reset to beginning")
    
    def get_progress(self) -> tuple[int, int]:
        """
        Get current progress.
        
        Returns:
            Tuple of (current_frame, total_frames)
        """
        return (self.frame_index, self.total_frames)
    
    def get_memory_info(self) -> Dict[str, Any]:
        """
        Get memory usage information for debugging.
        
        Returns:
            Dictionary with memory usage statistics
        """
        import sys
        
        return {
            'frame_index': self.frame_index,
            'total_frames': self.total_frames,
            'previous_positions_count': len(self._previous_bar_positions),
            'previous_counts_count': len(self._previous_play_counts),
            'stats_state_frames': len(self._stats_state),
            'generator_size_bytes': sys.getsizeof(self),
            'render_tasks_size_bytes': sys.getsizeof(self.all_render_tasks)
        }


def create_frame_spec_generator(all_render_tasks: List[Dict[str, Any]],
                               entity_id_to_canonical_name_map: Dict[str, str],
                               entity_details_map: Dict[str, Dict[str, Any]], 
                               album_bar_colors: Dict[str, tuple],
                               n_bars: int,
                               max_play_count_overall: float,
                               visualization_mode: str) -> FrameSpecGenerator:
    """
    Factory function to create a FrameSpecGenerator instance.
    
    This function provides a convenient interface matching the signature
    of the original prepare_all_frame_specs function.
    
    Returns:
        FrameSpecGenerator instance ready for iteration
    """
    return FrameSpecGenerator(
        all_render_tasks=all_render_tasks,
        entity_id_to_canonical_name_map=entity_id_to_canonical_name_map,
        entity_details_map=entity_details_map,
        album_bar_colors=album_bar_colors,
        n_bars=n_bars,
        max_play_count_overall=max_play_count_overall,
        visualization_mode=visualization_mode
    )