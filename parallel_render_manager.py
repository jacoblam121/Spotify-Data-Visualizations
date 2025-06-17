#!/usr/bin/env python3
"""
Parallel Render Manager for Phase 2 - Task 3

This module implements the parallel frame rendering orchestrator that combines:
- Task 1: Stateless renderer (stateless_renderer.py)
- Task 2: Memory-efficient generator (frame_spec_generator.py)
- Task 3: Parallel manager (this module)

Key Features:
- Memory-efficient O(1) processing using generators
- Structured error handling with retry logic
- Progress reporting with callback interface
- Circuit breaker for worker failures
- Graceful shutdown and resumability
"""

import os
import sys
import time
import signal
import logging
from typing import Dict, Any, Optional, Callable, Iterator, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
import concurrent.futures
from datetime import datetime

# Import existing modules
from rendering_utils.stateless_renderer import (
    RenderConfig, 
    initialize_render_worker, 
    render_frame_from_spec
)
from rendering_utils.frame_spec_generator import FrameSpecGenerator

# Configure logging
logger = logging.getLogger(__name__)


class FrameStatus(Enum):
    """Status of individual frame processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED_TRANSIENT = "failed_transient"
    FAILED_FATAL = "failed_fatal"
    FAILED_MAX_RETRIES = "failed_max_retries"


@dataclass
class TaskContext:
    """Context information for a submitted task"""
    frame_spec: Dict[str, Any]
    retry_count: int = 0
    future: Optional[concurrent.futures.Future] = None
    submission_time: Optional[float] = None
    
    @property
    def frame_index(self) -> int:
        return self.frame_spec.get('frame_index', -1)


@dataclass
class FrameResult:
    """Result of processing a single frame"""
    frame_index: int
    status: FrameStatus
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    retry_count: int = 0
    render_time_seconds: Optional[float] = None
    worker_pid: Optional[int] = None


@dataclass
class ProgressInfo:
    """Progress information for callback reporting"""
    frames_total: int
    frames_completed: int
    frames_failed: int
    frames_in_progress: int
    frames_pending: int
    success_rate: float
    estimated_time_remaining: Optional[float] = None
    current_fps: Optional[float] = None


@dataclass
class RenderingConfig:
    """Configuration for parallel rendering"""
    max_workers: Optional[int] = None
    max_retries_transient: int = 3
    max_worker_failures: int = 3
    backpressure_multiplier: int = 2  # max_workers * multiplier = max in-flight tasks
    progress_update_interval: int = 10  # Update progress every N completed frames
    save_completion_manifest: bool = True
    manifest_filename: str = "render_completion_manifest.json"
    maxtasksperchild: Optional[int] = 1000  # Recycle workers to prevent memory leaks
    graceful_shutdown_timeout: float = 30.0  # Seconds to wait for graceful shutdown
    
    def __post_init__(self):
        if self.max_workers is None:
            self.max_workers = os.cpu_count() or 1


@dataclass
class RenderingStats:
    """Statistics from rendering session"""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_frames: int = 0
    completed_frames: int = 0
    failed_frames: int = 0
    retried_frames: int = 0
    worker_failures: int = 0
    total_render_time: float = 0.0
    average_frame_time: Optional[float] = None
    peak_memory_usage: Optional[int] = None
    
    def finalize(self):
        """Calculate final statistics"""
        self.end_time = datetime.now()
        if self.completed_frames > 0:
            self.average_frame_time = self.total_render_time / self.completed_frames


class ParallelRenderManager:
    """
    Orchestrates parallel frame rendering with robust error handling.
    
    This class manages the complete pipeline from frame spec generation
    through parallel rendering to result collection and reporting.
    """
    
    def __init__(self, 
                 render_config: RenderConfig, 
                 rendering_config: RenderingConfig,
                 worker_initializer: Optional[Callable[..., None]] = None,
                 worker_initargs: Tuple[Any, ...] = ()):
        """
        Initialize the parallel render manager.
        
        Args:
            render_config: Configuration for stateless renderer workers
            rendering_config: Configuration for parallel processing behavior
            worker_initializer: Optional function to initialize workers (for testing)
                              Must be a picklable, top-level function
            worker_initargs: Arguments to pass to worker_initializer (must be picklable)
                           All arguments must be picklable (no complex objects/mocks)
        """
        self.render_config = render_config
        self.rendering_config = rendering_config
        self.worker_initializer = worker_initializer
        self.worker_initargs = worker_initargs
        self.stats = RenderingStats()
        
        # State tracking
        self._shutdown_requested = False
        self._frame_results: Dict[int, FrameResult] = {}
        self._pending_tasks: Dict[concurrent.futures.Future, TaskContext] = {}
        
        # Error tracking
        self._worker_failure_count = 0
        self._transient_retry_counts: Dict[int, int] = {}
        
        # Progress tracking
        self._last_progress_update = 0
        self._start_time = time.time()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"ParallelRenderManager initialized: "
                   f"max_workers={self.rendering_config.max_workers}, "
                   f"max_retries={self.rendering_config.max_retries_transient}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self._shutdown_requested = True
        # Do not call executor.shutdown() here - let main loop handle it
    
    def render_frames(self, 
                     frame_spec_generator: FrameSpecGenerator,
                     progress_callback: Optional[Callable[[ProgressInfo], None]] = None) -> Dict[str, Any]:
        """
        Render frames in parallel using the frame spec generator.
        
        Args:
            frame_spec_generator: Generator yielding frame specifications
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary containing rendering results and statistics
        """
        logger.info("Starting parallel frame rendering...")
        self.stats.start_time = datetime.now()
        self.stats.total_frames = frame_spec_generator.total_frames
        self._start_time = time.time()
        
        try:
            # Determine worker initializer and arguments
            if self.worker_initializer is not None:
                # Use test-provided initializer
                init_func = self.worker_initializer
                init_args = self.worker_initargs
            else:
                # Use default production initializer
                from stateless_renderer import initialize_render_worker as current_init_func
                init_func = current_init_func
                init_args = (self.render_config.to_dict(),)
            
            # Create ProcessPoolExecutor with worker initialization
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=self.rendering_config.max_workers,
                initializer=init_func,
                initargs=init_args,
                mp_context=None,  # Use default multiprocessing context
                max_tasks_per_child=self.rendering_config.maxtasksperchild
            ) as executor:
                
                return self._render_with_executor(
                    executor, 
                    frame_spec_generator, 
                    progress_callback
                )
                
        except KeyboardInterrupt:
            logger.info("Rendering interrupted by user")
            return self._create_final_results(interrupted=True)
        except Exception as e:
            logger.error(f"Unexpected error during rendering: {e}")
            return self._create_final_results(error=str(e))
        finally:
            self.stats.finalize()
            logger.info("Parallel rendering session ended")
    
    def _render_with_executor(self, 
                            executor: concurrent.futures.ProcessPoolExecutor,
                            frame_spec_generator: FrameSpecGenerator,
                            progress_callback: Optional[Callable[[ProgressInfo], None]]) -> Dict[str, Any]:
        """
        Main rendering loop with executor.
        
        This implements the backpressure-controlled producer-consumer pattern.
        """
        logger.info("Starting frame processing pipeline...")
        
        # Initialize pending tasks tracking
        self._pending_tasks.clear()
        max_in_flight = self.rendering_config.max_workers * self.rendering_config.backpressure_multiplier
        
        # Submit initial batch of tasks (up to backpressure limit)
        initial_submitted = self._submit_initial_tasks(executor, frame_spec_generator, max_in_flight)
        logger.info(f"Submitted initial batch of {initial_submitted} tasks")
        
        # Main processing loop
        completed_count = 0
        while self._pending_tasks and not self._shutdown_requested:
            try:
                # Process completed futures
                for future in concurrent.futures.as_completed(self._pending_tasks, timeout=1.0):
                    task_context = self._pending_tasks.pop(future)
                    frame_index = task_context.frame_index
                    
                    # Process the completed future
                    result = self._process_completed_future(future, task_context)
                    self._frame_results[frame_index] = result
                    
                    # Handle the result based on status
                    if result.status == FrameStatus.COMPLETED:
                        completed_count += 1
                        self.stats.completed_frames += 1
                        if result.render_time_seconds:
                            self.stats.total_render_time += result.render_time_seconds
                    
                    elif result.status == FrameStatus.FAILED_TRANSIENT:
                        # Retry if under limit
                        if self._should_retry_frame(frame_index, task_context.retry_count):
                            self._retry_frame(executor, task_context)
                        else:
                            # Max retries exceeded
                            result.status = FrameStatus.FAILED_MAX_RETRIES
                            self.stats.failed_frames += 1
                            logger.warning(f"Frame {frame_index}: Max retries exceeded")
                    
                    elif result.status in [FrameStatus.FAILED_FATAL, FrameStatus.FAILED_MAX_RETRIES]:
                        self.stats.failed_frames += 1
                        
                        # Check for worker fatal error (circuit breaker)
                        if result.error_type == 'worker_fatal':
                            self._worker_failure_count += 1
                            self.stats.worker_failures += 1
                            
                            if self._worker_failure_count >= self.rendering_config.max_worker_failures:
                                logger.error(f"Circuit breaker triggered: {self._worker_failure_count} worker failures")
                                return self._create_final_results(
                                    error=f"Too many worker failures ({self._worker_failure_count})"
                                )
                    
                    # Try to submit next task to maintain pipeline
                    self._try_submit_next_task(executor, frame_spec_generator)
                    
                    # Update progress if needed
                    if progress_callback and self._should_update_progress(completed_count):
                        progress_info = self._create_progress_info()
                        progress_callback(progress_info)
                        self._last_progress_update = completed_count
                    
            except concurrent.futures.TimeoutError:
                # No futures completed in timeout window, continue loop
                # This allows checking for shutdown signals
                continue
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                break
        
        # Handle graceful shutdown if requested
        if self._shutdown_requested and self._pending_tasks:
            logger.info(f"Graceful shutdown: cancelling {len(self._pending_tasks)} pending tasks...")
            cancelled_count = 0
            for future in list(self._pending_tasks.keys()):
                if future.cancel():
                    cancelled_count += 1
                    task_context = self._pending_tasks.pop(future)
                    # Mark as failed due to shutdown
                    result = FrameResult(
                        frame_index=task_context.frame_index,
                        status=FrameStatus.FAILED_FATAL,
                        error_message="Cancelled due to shutdown",
                        error_type="shutdown",
                        retry_count=task_context.retry_count
                    )
                    self._frame_results[task_context.frame_index] = result
                    self.stats.failed_frames += 1
            
            logger.info(f"Cancelled {cancelled_count} tasks during shutdown")
        
        # Final progress update
        if progress_callback:
            final_progress = self._create_progress_info()
            progress_callback(final_progress)
        
        logger.info(f"Processing complete: {self.stats.completed_frames} completed, {self.stats.failed_frames} failed")
        return self._create_final_results()
    
    def _submit_initial_tasks(self, 
                            executor: concurrent.futures.ProcessPoolExecutor,
                            frame_spec_generator: FrameSpecGenerator,
                            max_count: int) -> int:
        """Submit initial batch of frame rendering tasks"""
        submitted = 0
        for _ in range(max_count):
            try:
                frame_spec = next(frame_spec_generator)
                task_context = TaskContext(
                    frame_spec=frame_spec,
                    retry_count=0,
                    submission_time=time.time()
                )
                # Use unified render function - test logic handled in worker initialization
                from worker_utilities import top_level_test_render_function
                future = executor.submit(top_level_test_render_function, frame_spec)
                task_context.future = future
                self._pending_tasks[future] = task_context
                submitted += 1
            except StopIteration:
                break
        return submitted
    
    def _try_submit_next_task(self, 
                            executor: concurrent.futures.ProcessPoolExecutor,
                            frame_spec_generator: FrameSpecGenerator) -> bool:
        """Try to submit the next task from generator to maintain pipeline"""
        try:
            frame_spec = next(frame_spec_generator)
            task_context = TaskContext(
                frame_spec=frame_spec,
                retry_count=0,
                submission_time=time.time()
            )
            # Use unified render function - test logic handled in worker initialization
            from worker_utilities import top_level_test_render_function
            future = executor.submit(top_level_test_render_function, frame_spec)
            task_context.future = future
            self._pending_tasks[future] = task_context
            return True
        except StopIteration:
            return False
    
    def _process_completed_future(self, 
                                future: concurrent.futures.Future,
                                task_context: TaskContext) -> FrameResult:
        """Process a completed future and return FrameResult"""
        frame_index = task_context.frame_index
        
        try:
            # Get result from worker
            worker_result = future.result()
            
            if worker_result['status'] == 'success':
                return FrameResult(
                    frame_index=frame_index,
                    status=FrameStatus.COMPLETED,
                    output_path=worker_result.get('output_path'),
                    retry_count=task_context.retry_count,
                    render_time_seconds=worker_result.get('render_time_seconds'),
                    worker_pid=worker_result.get('worker_pid')
                )
            else:
                # Worker returned error status
                error_type = worker_result.get('error_type', 'unknown')
                error_message = worker_result.get('error', 'Unknown error')
                
                if error_type == 'transient':
                    status = FrameStatus.FAILED_TRANSIENT
                elif error_type == 'worker_fatal':
                    status = FrameStatus.FAILED_FATAL
                else:
                    status = FrameStatus.FAILED_FATAL
                
                return FrameResult(
                    frame_index=frame_index,
                    status=status,
                    error_message=error_message,
                    error_type=error_type,
                    retry_count=task_context.retry_count,
                    render_time_seconds=worker_result.get('render_time_seconds'),
                    worker_pid=worker_result.get('worker_pid')
                )
                
        except Exception as e:
            # Exception occurred in worker process
            logger.error(f"Frame {frame_index}: Worker exception: {e}")
            return FrameResult(
                frame_index=frame_index,
                status=FrameStatus.FAILED_FATAL,
                error_message=str(e),
                error_type='worker_exception',
                retry_count=task_context.retry_count
            )
    
    def _should_retry_frame(self, frame_index: int, retry_count: int) -> bool:
        """Determine if a frame should be retried"""
        return retry_count < self.rendering_config.max_retries_transient
    
    def _retry_frame(self, 
                    executor: concurrent.futures.ProcessPoolExecutor,
                    task_context: TaskContext):
        """Retry a failed frame"""
        frame_index = task_context.frame_index
        new_retry_count = task_context.retry_count + 1
        logger.info(f"Frame {frame_index}: Retrying (attempt {new_retry_count})")
        
        # Create new task context for retry
        retry_context = TaskContext(
            frame_spec=task_context.frame_spec,
            retry_count=new_retry_count,
            submission_time=time.time()
        )
        
        # Use unified render function - test logic handled in worker initialization
        frame_spec = task_context.frame_spec
        from worker_utilities import top_level_test_render_function
        future = executor.submit(top_level_test_render_function, frame_spec)
        retry_context.future = future
        self._pending_tasks[future] = retry_context
        self.stats.retried_frames += 1
    
    def _should_update_progress(self, completed_count: int) -> bool:
        """Determine if progress should be updated"""
        return (completed_count - self._last_progress_update) >= self.rendering_config.progress_update_interval
    
    def _create_progress_info(self) -> ProgressInfo:
        """Create current progress information"""
        frames_in_progress = len(self._pending_tasks)
        frames_pending = self.stats.total_frames - self.stats.completed_frames - self.stats.failed_frames - frames_in_progress
        
        # Calculate success rate
        total_processed = self.stats.completed_frames + self.stats.failed_frames
        success_rate = (self.stats.completed_frames / total_processed) if total_processed > 0 else 0.0
        
        # Estimate time remaining
        elapsed_time = time.time() - self._start_time
        estimated_time_remaining = None
        current_fps = None
        
        if self.stats.completed_frames > 0:
            current_fps = self.stats.completed_frames / elapsed_time
            remaining_frames = self.stats.total_frames - self.stats.completed_frames - self.stats.failed_frames
            estimated_time_remaining = remaining_frames / current_fps if current_fps > 0 else None
        
        return ProgressInfo(
            frames_total=self.stats.total_frames,
            frames_completed=self.stats.completed_frames,
            frames_failed=self.stats.failed_frames,
            frames_in_progress=frames_in_progress,
            frames_pending=max(0, frames_pending),
            success_rate=success_rate,
            estimated_time_remaining=estimated_time_remaining,
            current_fps=current_fps
        )
    
    def _create_final_results(self, interrupted: bool = False, error: Optional[str] = None) -> Dict[str, Any]:
        """Create final results dictionary"""
        return {
            'status': 'interrupted' if interrupted else ('error' if error else 'completed'),
            'error': error,
            'stats': self.stats,
            'frame_results': self._frame_results,
            'completed_frames': [
                result for result in self._frame_results.values() 
                if result.status == FrameStatus.COMPLETED
            ],
            'failed_frames': [
                result for result in self._frame_results.values() 
                if result.status in [FrameStatus.FAILED_FATAL, FrameStatus.FAILED_MAX_RETRIES]
            ]
        }


def parallel_render_frames(frame_spec_generator: FrameSpecGenerator,
                         render_config: RenderConfig,
                         rendering_config: Optional[RenderingConfig] = None,
                         progress_callback: Optional[Callable[[ProgressInfo], None]] = None) -> Dict[str, Any]:
    """
    High-level function to render frames in parallel.
    
    Args:
        frame_spec_generator: Generator yielding frame specifications
        render_config: Configuration for stateless renderer workers
        rendering_config: Configuration for parallel processing (optional)
        progress_callback: Optional callback for progress updates
        
    Returns:
        Dictionary containing rendering results and statistics
    """
    if rendering_config is None:
        rendering_config = RenderingConfig()
    
    manager = ParallelRenderManager(render_config, rendering_config)
    return manager.render_frames(frame_spec_generator, progress_callback)


if __name__ == "__main__":
    # Test module can be run independently
    print("Parallel render manager module loaded successfully")
    
    # Test basic configuration
    test_rendering_config = RenderingConfig(max_workers=2, max_retries_transient=1)
    print(f"Test config: {test_rendering_config.max_workers} workers, {test_rendering_config.max_retries_transient} retries")