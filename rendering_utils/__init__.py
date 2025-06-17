#!/usr/bin/env python3
"""
Rendering Utilities Package

This package contains all the core rendering components for the Spotify Data Visualizations:

Core Components:
- parallel_renderer: Optimized parallel frame rendering system
- stateless_renderer: Stateless frame generation with no global dependencies  
- executor_factory: Configurable process pool executor factory
- progress_tracker: Clean progress bars for frame generation
- worker_utilities: Multiprocessing-safe utilities for worker processes
- frame_spec_generator: Memory-efficient frame specification generator

Main Entry Points:
- render_frames_in_parallel(): Main parallel rendering function
- create_progress_tracker(): Factory for progress tracking
- create_rendering_executor(): Factory for optimized executors
"""

# Main exports
from .parallel_renderer import render_frames_in_parallel
from .progress_tracker import create_progress_tracker
from .executor_factory import create_rendering_executor
from .stateless_renderer import RenderConfig
from .worker_utilities import generic_worker_patcher

__all__ = [
    'render_frames_in_parallel',
    'create_progress_tracker', 
    'create_rendering_executor',
    'RenderConfig',
    'generic_worker_patcher'
]

__version__ = '1.0.0'
__author__ = 'Spotify Data Visualizations Team'