"""
Parallel frame renderer with clean architecture.
Uses spawn mode with explicit state passing to avoid fork/matplotlib issues.
"""

import os
import time
import multiprocessing
import concurrent.futures
from typing import List, Dict, Tuple, Any, Optional
from tqdm import tqdm
import signal
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from render_config import RenderConfig


def init_worker(config: RenderConfig, custom_font_dir: str):
    """Initialize worker process with matplotlib and fonts.
    
    This function runs ONCE per worker process when it's created.
    Sets up matplotlib backend and registers custom fonts.
    """
    # CRITICAL: Set backend before any other matplotlib imports
    matplotlib.use('Agg')
    
    # Register custom fonts if directory exists
    if os.path.exists(custom_font_dir):
        try:
            for font_file in os.listdir(custom_font_dir):
                if font_file.endswith(('.ttf', '.otf')):
                    font_path = os.path.join(custom_font_dir, font_file)
                    try:
                        fm.fontManager.addfont(font_path)
                    except Exception as e:
                        print(f"[Worker {os.getpid()}] Warning: Could not register font {font_file}: {e}")
        except Exception as e:
            print(f"[Worker {os.getpid()}] Warning: Error accessing font directory: {e}")
    
    print(f"[Worker {os.getpid()}] Initialized with matplotlib backend: {matplotlib.get_backend()}")


def render_single_frame_clean(task_data: Tuple[Dict, RenderConfig, Dict, Dict, Dict, Dict, Dict]) -> Tuple[int, float, int]:
    """Clean frame rendering function that accepts all data explicitly.
    
    Args:
        task_data: Tuple containing:
            - render_task: Dict with frame rendering information
            - config: RenderConfig object with all configuration
            - entity_id_to_canonical_name_map: Maps entity_id -> canonical_name
            - entity_details_map: Main entity details with display info
            - album_art_image_objects: Pre-loaded album art images
            - album_art_image_objects_highres: High-res album art for panels
            - album_bar_colors: Pre-computed bar colors
    
    Returns:
        Tuple of (frame_index, render_time, worker_pid)
    """
    start_time = time.monotonic()
    
    # Unpack task data
    (render_task, config, entity_id_to_canonical_name_map, entity_details_map,
     album_art_image_objects, album_art_image_objects_highres, album_bar_colors) = task_data
    
    # Extract frame information
    overall_frame_idx = render_task['overall_frame_index']
    display_timestamp = render_task['display_timestamp']
    bar_render_data_list = render_task['bar_render_data_list']
    rolling_window_info = render_task.get('rolling_window_info', {'top_7_day': None, 'top_30_day': None})
    nightingale_info = render_task.get('nightingale_info', {})
    
    # Set matplotlib font preferences
    plt.rcParams['font.family'] = config.preferred_fonts
    
    # Memory monitoring if enabled
    mem_before_mb = None
    if config.memory_debug:
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_before_mb = process.memory_info().rss / 1024**2
            print(f"[Worker {os.getpid()}] Frame {overall_frame_idx} starting. Memory: {mem_before_mb:.1f} MB")
        except:
            pass
    
    # Create figure
    figsize_w = config.video_width / config.video_dpi
    figsize_h = config.video_height / config.video_dpi
    fig, ax = plt.subplots(figsize=(figsize_w, figsize_h), dpi=config.video_dpi)
    
    try:
        # Import the actual drawing logic
        # This avoids circular imports and keeps the drawing logic separate
        from frame_drawer import draw_frame_content
        
        # Draw the frame content
        draw_frame_content(
            fig=fig,
            ax=ax,
            render_task=render_task,
            config=config,
            entity_id_to_canonical_name_map=entity_id_to_canonical_name_map,
            entity_details_map=entity_details_map,
            album_art_image_objects=album_art_image_objects,
            album_art_image_objects_highres=album_art_image_objects_highres,
            album_bar_colors=album_bar_colors
        )
        
        # Save the frame - using the exact same approach as the old version
        num_frames = render_task.get('total_frames', 10000)  # Default for padding
        # Use same padding calculation as main_animator.py
        frame_number_padding = len(str(num_frames))
        output_path = os.path.join(
            config.temp_frame_dir,
            f"frame_{overall_frame_idx:0{frame_number_padding}d}.png"
        )
        
        # Save exactly like the old version - no bbox_inches parameter at all
        fig.savefig(output_path)
        
        # Only log frame times if explicitly requested AND not using progress bar
        # This prevents interference with tqdm
        if config.log_frame_times and config.parallel_log_completion_interval < 0:
            render_time = time.monotonic() - start_time
            print(f"[Worker {os.getpid()}] Frame {overall_frame_idx} saved in {render_time:.3f}s")
    
    finally:
        # CRITICAL: Always close the figure to free memory
        plt.close(fig)
        
        # Optional: Force garbage collection for large renders
        if config.memory_debug and overall_frame_idx % 10 == 0:
            import gc
            gc.collect()
            
            if mem_before_mb is not None:
                try:
                    import psutil
                    process = psutil.Process(os.getpid())
                    mem_after_mb = process.memory_info().rss / 1024**2
                    print(f"[Worker {os.getpid()}] Frame {overall_frame_idx} done. Memory: {mem_before_mb:.1f} -> {mem_after_mb:.1f} MB")
                except:
                    pass
    
    render_time = time.monotonic() - start_time
    return (overall_frame_idx, render_time, os.getpid())


class ParallelFrameRenderer:
    """Manages parallel frame rendering with clean architecture."""
    
    def __init__(self, config: RenderConfig, custom_font_dir: str = 'fonts'):
        self.config = config
        self.custom_font_dir = os.path.abspath(custom_font_dir)
        self.worker_pids_reported = set()
        
        # Set spawn mode globally at initialization
        multiprocessing.set_start_method('spawn', force=True)
        print(f"Multiprocessing start method set to: {multiprocessing.get_start_method()}")
    
    def render_frames(self, 
                     render_tasks: List[Dict],
                     entity_id_to_canonical_name_map: Dict,
                     entity_details_map: Dict,
                     album_art_image_objects: Dict,
                     album_art_image_objects_highres: Dict,
                     album_bar_colors: Dict) -> List[float]:
        """Render all frames in parallel using ProcessPoolExecutor.
        
        Returns:
            List of render times for each frame
        """
        num_frames = len(render_tasks)
        
        # Add total frames to each task for padding calculation
        for task in render_tasks:
            task['total_frames'] = num_frames
        
        # Prepare task data tuples
        task_data_list = [
            (task, self.config, entity_id_to_canonical_name_map, entity_details_map,
             album_art_image_objects, album_art_image_objects_highres, album_bar_colors)
            for task in render_tasks
        ]
        
        # Determine worker count with intelligent scaling
        actual_workers = self._calculate_optimal_workers(num_frames)
        
        if self.config.serial_mode:
            return self._render_serial(task_data_list)
        else:
            return self._render_parallel(task_data_list, actual_workers)
    
    def _calculate_optimal_workers(self, num_frames: int) -> int:
        """Calculate optimal number of workers based on workload."""
        base_workers = self.config.max_parallel_workers
        
        # Check if user forced a specific worker count
        if self.config.force_parallel_workers > 0:
            print(f"Using forced worker count: {self.config.force_parallel_workers}")
            return self.config.force_parallel_workers
        
        # For large workloads, reduce workers to prevent memory exhaustion
        if num_frames > 100:
            avg_frames_per_worker = num_frames / base_workers
            if avg_frames_per_worker > 10:
                recommended = min(base_workers, max(1, (os.cpu_count() or 4) // 2))
                if base_workers > recommended:
                    print(f"🧠 MEMORY OPTIMIZATION: Reducing workers from {base_workers} to {recommended}")
                    print(f"   Reason: Large workload ({num_frames} frames, ~{avg_frames_per_worker:.1f} frames/worker)")
                    return recommended
        
        return base_workers
    
    def _render_serial(self, task_data_list: List[Tuple]) -> List[float]:
        """Render frames serially for debugging."""
        print("--- SERIAL MODE: Processing frames sequentially ---")
        render_times = []
        
        for i, task_data in enumerate(task_data_list):
            try:
                frame_idx, render_time, pid = render_single_frame_clean(task_data)
                render_times.append(render_time)
                
                # Log progress
                if (i + 1) == 1 or (i + 1) == len(task_data_list) or \
                   (self.config.parallel_log_completion_interval > 0 and 
                    (i + 1) % self.config.parallel_log_completion_interval == 0):
                    print(f"Frame {frame_idx + 1}/{len(task_data_list)} completed in {render_time:.2f}s")
                    
            except Exception as e:
                print(f"SERIAL MODE - Frame {i} failed: {e}")
                raise
        
        return render_times
    
    def _render_parallel(self, task_data_list: List[Tuple], num_workers: int) -> List[float]:
        """Render frames in parallel using ProcessPoolExecutor."""
        print(f"--- PARALLEL MODE: Using {num_workers} worker processes with spawn mode ---")
        
        render_times = []
        completed_frames = 0
        
        # Configure executor with proper initialization
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=num_workers,
            mp_context=multiprocessing.get_context('spawn'),
            initializer=init_worker,
            initargs=(self.config, self.custom_font_dir)
        ) as executor:
            
            # Submit all tasks and create progress bar
            # Use leave=True to keep the bar after completion, and dynamic_ncols for terminal width
            with tqdm(total=len(task_data_list), desc="Rendering frames", 
                     leave=True, dynamic_ncols=True, smoothing=0.1) as pbar:
                
                # Use map for ordered results or as_completed for responsiveness
                # Here we'll use as_completed for better progress feedback
                future_to_idx = {
                    executor.submit(render_single_frame_clean, task_data): i
                    for i, task_data in enumerate(task_data_list)
                }
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_idx):
                    try:
                        frame_idx, render_time, pid = future.result(timeout=30)  # 30 second timeout per frame
                        render_times.append(render_time)
                        completed_frames += 1
                        
                        # Update progress bar
                        pbar.update(1)
                        
                        # Log worker PIDs once
                        if self.config.log_parallel_process_start and pid not in self.worker_pids_reported:
                            print(f"--- Worker process with PID {pid} has started ---")
                            self.worker_pids_reported.add(pid)
                        
                        # Log completion at intervals
                        if self._should_log_completion(completed_frames, len(task_data_list)):
                            avg_time = sum(render_times) / len(render_times)
                            print(f"Progress: {completed_frames}/{len(task_data_list)} frames, avg: {avg_time:.2f}s/frame")
                            
                    except concurrent.futures.TimeoutError:
                        print(f"❌ Frame rendering timeout after 30 seconds")
                        raise
                    except Exception as e:
                        print(f"❌ Frame rendering failed: {e}")
                        raise
        
        print(f"✅ All {len(task_data_list)} frames rendered successfully")
        return render_times
    
    def _should_log_completion(self, completed: int, total: int) -> bool:
        """Determine if completion should be logged based on config."""
        interval = self.config.parallel_log_completion_interval
        
        if interval > 0:
            return (completed == 1 or completed == total or completed % interval == 0)
        elif interval == 0:
            return (completed == 1 or completed == total)
        else:
            return False