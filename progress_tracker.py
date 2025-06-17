#!/usr/bin/env python3
"""
Progress Tracker - Clean progress bar for parallel frame generation

Provides a clean progress bar with frame count and FPS display
to replace verbose worker success messages.
"""

import time
import threading
from typing import Optional

try:
    from tqdm import tqdm
except ImportError:
    print("Warning: tqdm not installed. Install with: pip install tqdm")
    # Fallback implementation
    class tqdm:
        def __init__(self, total=None, desc="", unit="", **kwargs):
            self.total = total
            self.desc = desc
            self.unit = unit
            self.n = 0
            self.start_time = time.time()
            
        def update(self, n=1):
            self.n += n
            elapsed = time.time() - self.start_time
            rate = self.n / elapsed if elapsed > 0 else 0
            if self.total:
                percent = (self.n / self.total) * 100
                print(f"\r{self.desc}: {self.n}/{self.total} ({percent:.1f}%) [{rate:.1f}{self.unit}/s]", end="", flush=True)
            else:
                print(f"\r{self.desc}: {self.n} [{rate:.1f}{self.unit}/s]", end="", flush=True)
                
        def close(self):
            print()  # New line
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            self.close()

class ProgressTracker:
    """
    Thread-safe progress tracker for parallel frame generation.
    
    Provides clean progress bar with:
    - Current frame / Total frames
    - Frames per second (it/s)
    - Estimated time remaining
    """
    
    def __init__(self, total_frames: int, show_progress: bool = True):
        self.total_frames = total_frames
        self.show_progress = show_progress
        self.completed_frames = 0
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.pbar: Optional[tqdm] = None
        
        if self.show_progress:
            self.pbar = tqdm(
                total=total_frames,
                desc="🎬 Rendering frames",
                unit="frames",
                ncols=140,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}] Elapsed: {elapsed} ETA: {remaining}",
                smoothing=0.1  # Better rate smoothing for parallel updates
            )
    
    def update(self, frames_completed: int = 1) -> None:
        """Update progress by the specified number of completed frames."""
        if not self.show_progress:
            return
            
        with self.lock:
            self.completed_frames += frames_completed
            if self.pbar:
                self.pbar.update(frames_completed)
    
    def close(self) -> None:
        """Close the progress bar and print summary."""
        if not self.show_progress:
            return
            
        with self.lock:
            if self.pbar:
                self.pbar.close()
                
            # Print summary
            elapsed = time.time() - self.start_time
            fps = self.completed_frames / elapsed if elapsed > 0 else 0
            print(f"✅ Frame generation complete: {self.completed_frames}/{self.total_frames} frames in {elapsed:.1f}s ({fps:.1f} fps)")
    
    def get_stats(self) -> dict:
        """Get current progress statistics."""
        with self.lock:
            elapsed = time.time() - self.start_time
            fps = self.completed_frames / elapsed if elapsed > 0 else 0
            progress_percent = (self.completed_frames / self.total_frames * 100) if self.total_frames > 0 else 0
            
            return {
                'completed_frames': self.completed_frames,
                'total_frames': self.total_frames,
                'elapsed_time': elapsed,
                'fps': fps,
                'progress_percent': progress_percent
            }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def create_progress_tracker(total_frames: int, show_progress: bool = True) -> ProgressTracker:
    """Factory function to create a progress tracker."""
    return ProgressTracker(total_frames, show_progress)