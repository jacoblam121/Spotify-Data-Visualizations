#!/usr/bin/env python3
"""
Mock Components for Task 3 Testing

Provides controllable mock implementations for testing parallel render manager:
- MockFrameSpecGenerator: Configurable frame generation for testing
- MockRenderer: Controllable renderer with error injection capabilities
- TestDataFactory: Creates test frame specs and configurations
"""

import os
import sys
import time
import random
from typing import Dict, Any, List, Optional, Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
import logging

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from frame_spec_generator import FrameSpecGenerator
from stateless_renderer import RenderConfig

logger = logging.getLogger(__name__)


@dataclass
class MockConfig:
    """Configuration for mock components"""
    # Generator settings
    total_frames: int = 100
    frame_generation_delay_ms: float = 0.0  # Delay between frame generation
    
    # Renderer settings  
    render_delay_ms: float = 50.0  # Simulated render time per frame
    render_delay_variance: float = 0.2  # Random variance (±20%)
    
    # Error injection settings
    error_type: Optional[str] = None  # 'transient', 'frame_fatal', 'worker_fatal'
    error_frame_numbers: List[int] = None  # Specific frames to inject errors
    error_probability: float = 0.0  # Random error injection (0.0 = never, 1.0 = always)
    error_worker_exit: bool = False  # Use os._exit() for worker_fatal (dangerous!)
    
    # Memory testing
    simulate_memory_leak: bool = False
    memory_leak_per_frame_mb: float = 0.1
    
    def __post_init__(self):
        if self.error_frame_numbers is None:
            self.error_frame_numbers = []


# Global variable for worker-local mock configuration
WORKER_MOCK_CONFIG: Optional[MockConfig] = None


class MockFrameSpecGenerator:
    """
    Mock frame spec generator for testing.
    
    Mimics FrameSpecGenerator but with configurable behavior for testing scenarios.
    """
    
    def __init__(self, config: MockConfig):
        self.config = config
        self.frame_index = 0
        self.total_frames = config.total_frames
        self._generation_start_time = time.time()
        
        logger.info(f"MockFrameSpecGenerator: {self.total_frames} frames, "
                   f"{config.frame_generation_delay_ms}ms delay")
    
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        return self
    
    def __next__(self) -> Dict[str, Any]:
        if self.frame_index >= self.total_frames:
            raise StopIteration
        
        # Simulate generation delay
        if self.config.frame_generation_delay_ms > 0:
            time.sleep(self.config.frame_generation_delay_ms / 1000.0)
        
        frame_spec = self._create_frame_spec(self.frame_index)
        self.frame_index += 1
        
        return frame_spec
    
    def _create_frame_spec(self, frame_index: int) -> Dict[str, Any]:
        """Create a test frame specification"""
        # Create realistic timestamp
        timestamp = datetime.now(timezone.utc)
        
        # Create test bars data
        bars = []
        num_bars = min(10, max(1, frame_index % 15))  # Varying number of bars
        
        for i in range(num_bars):
            # Calculate and clamp color components to valid [0.0, 1.0] range
            red = min(1.0, max(0.0, 0.3 + i * 0.1))
            blue = min(1.0, max(0.0, 0.8 - i * 0.1))
            
            bars.append({
                'entity_id': f'test_track_{i}',
                'canonical_key': f'test_track_{i}',
                'display_name': f'Test Track {i} - Test Artist {i}',
                'interpolated_y_pos': float(i),
                'interpolated_play_count': 100.0 + (frame_index * 5) + (i * 10),
                'bar_color_rgba': (red, 0.5, blue, 1.0),
                'album_art_path': f'test_art_{i}.jpg',
                'entity_details': {
                    'original_artist': f'Test Artist {i}',
                    'original_track': f'Test Track {i}'
                }
            })
        
        return {
            'frame_index': frame_index,
            'display_timestamp': timestamp.isoformat(),
            'bars': bars,
            'dynamic_x_axis_limit': 200.0 + (frame_index * 2),
            'rolling_stats': {
                'top_7_day': [],
                'top_30_day': []
            },
            'nightingale_data': {},
            'visualization_mode': 'tracks'
        }
    
    def get_progress(self) -> tuple[int, int]:
        """Get current progress"""
        return (self.frame_index, self.total_frames)
    
    def reset(self):
        """Reset generator to beginning"""
        self.frame_index = 0
        self._generation_start_time = time.time()


def mock_render_frame_from_spec(frame_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock renderer function that can be used as a drop-in replacement.
    
    This function simulates the behavior of the real render_frame_from_spec
    but with controllable timing and error injection.
    Uses worker-local configuration for multiprocessing compatibility.
    """
    global WORKER_MOCK_CONFIG
    
    frame_index = frame_spec.get('frame_index', 0)
    worker_pid = os.getpid()
    start_time = time.time()
    
    # Use worker-local config if available, otherwise fallback to global config
    config = WORKER_MOCK_CONFIG or getattr(mock_render_frame_from_spec, '_config', MockConfig())
    
    # DEBUG: Print configuration info
    logger.debug(f"Frame {frame_index} - PID {worker_pid}: config={config}, error_frames={config.error_frame_numbers}, error_type={config.error_type}")
    
    # Memory monitoring (worker-side)
    memory_before = 0
    memory_after = 0
    memory_delta = 0
    
    try:
        # Get memory usage before processing (if psutil available)
        try:
            import psutil
            process = psutil.Process(worker_pid)
            memory_before = process.memory_info().rss
        except (ImportError, psutil.NoSuchProcess):
            pass
        
        # Simulate memory leak if configured
        if config.simulate_memory_leak:
            # Allocate memory that won't be released
            size_bytes = int(config.memory_leak_per_frame_mb * 1024 * 1024)
            leaked_memory = bytearray(size_bytes)
            # Store in global to prevent garbage collection
            if not hasattr(mock_render_frame_from_spec, '_leaked_memory'):
                mock_render_frame_from_spec._leaked_memory = []
            mock_render_frame_from_spec._leaked_memory.append(leaked_memory)
        
        # Check for error injection
        should_inject_error = False
        error_type_to_inject = None
        
        # Check specific frame numbers
        if frame_index in config.error_frame_numbers:
            should_inject_error = True
            error_type_to_inject = config.error_type
        
        # Check probability-based injection
        elif config.error_probability > 0 and random.random() < config.error_probability:
            should_inject_error = True
            error_type_to_inject = config.error_type
        
        # Inject error if configured
        if should_inject_error and error_type_to_inject:
            if error_type_to_inject == 'worker_fatal' and config.error_worker_exit:
                # Forcibly exit worker process (dangerous but effective test)
                logger.warning(f"Frame {frame_index}: Injecting worker_fatal with os._exit()")
                os._exit(1)
            elif error_type_to_inject == 'worker_fatal':
                # Simulate worker fatal error without actually killing process
                render_time = time.time() - start_time
                return {
                    'status': 'error',
                    'error_type': 'worker_fatal',
                    'frame_index': frame_index,
                    'error': f'Simulated worker fatal error on frame {frame_index}',
                    'render_time_seconds': render_time,
                    'worker_pid': worker_pid
                }
            elif error_type_to_inject == 'transient':
                render_time = time.time() - start_time
                return {
                    'status': 'error',
                    'error_type': 'transient',
                    'frame_index': frame_index,
                    'error': f'Simulated transient error on frame {frame_index}',
                    'render_time_seconds': render_time,
                    'worker_pid': worker_pid
                }
            elif error_type_to_inject == 'frame_fatal':
                render_time = time.time() - start_time
                return {
                    'status': 'error',
                    'error_type': 'frame_fatal',
                    'frame_index': frame_index,
                    'error': f'Simulated frame fatal error on frame {frame_index}',
                    'render_time_seconds': render_time,
                    'worker_pid': worker_pid
                }
        
        # Simulate render delay with variance
        base_delay = config.render_delay_ms / 1000.0
        variance = base_delay * config.render_delay_variance
        actual_delay = base_delay + random.uniform(-variance, variance)
        actual_delay = max(0.001, actual_delay)  # Minimum 1ms
        
        time.sleep(actual_delay)
        
        # Get memory usage after processing
        try:
            import psutil
            process = psutil.Process(worker_pid)
            memory_after = process.memory_info().rss
            memory_delta = memory_after - memory_before
        except (ImportError, psutil.NoSuchProcess):
            pass
        
        # Simulate successful render
        render_time = time.time() - start_time
        output_path = f"mock_frames/frame_{frame_index:06d}.png"
        
        return {
            'status': 'success',
            'frame_index': frame_index,
            'output_path': output_path,
            'render_time_seconds': render_time,
            'worker_pid': worker_pid,
            'memory_delta_bytes': memory_delta,
            'memory_before_bytes': memory_before,
            'memory_after_bytes': memory_after
        }
        
    except Exception as e:
        # Handle unexpected errors
        render_time = time.time() - start_time
        # Get memory after error if possible
        try:
            import psutil
            process = psutil.Process(worker_pid)
            memory_after = process.memory_info().rss
            memory_delta = memory_after - memory_before
        except (ImportError, psutil.NoSuchProcess):
            pass
        
        return {
            'status': 'error',
            'error_type': 'frame_fatal',
            'frame_index': frame_index,
            'error': f'Unexpected error in mock renderer: {str(e)}',
            'render_time_seconds': render_time,
            'worker_pid': worker_pid,
            'memory_delta_bytes': memory_delta,
            'memory_before_bytes': memory_before,
            'memory_after_bytes': memory_after
        }


def mock_initialize_render_worker(render_config_dict: Dict[str, Any], mock_config_dict: Optional[Dict[str, Any]] = None):
    """
    Mock worker initialization function with proper multiprocessing support.
    
    This replaces the real initialize_render_worker for testing.
    Sets up worker-local mock configuration to work across process boundaries.
    """
    global WORKER_MOCK_CONFIG
    worker_pid = os.getpid()
    
    # Set up worker-local mock configuration
    if mock_config_dict:
        WORKER_MOCK_CONFIG = MockConfig(**mock_config_dict)
        logger.info(f"Mock worker {worker_pid} initialized with config: {WORKER_MOCK_CONFIG.total_frames} frames")
    else:
        WORKER_MOCK_CONFIG = MockConfig()
        logger.info(f"Mock worker {worker_pid} initialized with default config")
    
    # Simulate worker initialization delay if configured
    if hasattr(WORKER_MOCK_CONFIG, 'worker_startup_delay_ms'):
        startup_delay = getattr(WORKER_MOCK_CONFIG, 'worker_startup_delay_ms', 0) / 1000.0
        if startup_delay > 0:
            time.sleep(startup_delay)
    
    # Store worker PID for testing (using file-based storage for multiprocessing)
    try:
        import tempfile
        import fcntl
        pid_file = os.path.join(tempfile.gettempdir(), 'mock_worker_pids.txt')
        with open(pid_file, 'a') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write(f"{worker_pid}\n")
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except (ImportError, OSError):
        # Fallback for systems without fcntl
        pass


class TestDataFactory:
    """Factory for creating test data and configurations"""
    
    @staticmethod
    def create_test_render_config() -> RenderConfig:
        """Create a minimal RenderConfig for testing"""
        return RenderConfig(
            dpi=96,
            fig_width_pixels=1920,
            fig_height_pixels=1080,
            target_fps=30,
            font_paths={},
            preferred_fonts=['DejaVu Sans'],
            album_art_cache_dir='test_album_art_cache',
            album_art_visibility_threshold=0.0628,
            n_bars=10
        )
    
    @staticmethod
    def create_mock_config_preset(preset_name: str) -> MockConfig:
        """Create predefined mock configurations for common test scenarios"""
        
        if preset_name == "basic":
            return MockConfig(
                total_frames=10,
                render_delay_ms=10.0
            )
        
        elif preset_name == "fast_stress":
            return MockConfig(
                total_frames=1000,
                render_delay_ms=1.0,
                frame_generation_delay_ms=0.0
            )
        
        elif preset_name == "slow_render":
            return MockConfig(
                total_frames=50,
                render_delay_ms=200.0,
                render_delay_variance=0.3
            )
        
        elif preset_name == "transient_errors":
            return MockConfig(
                total_frames=100,
                render_delay_ms=20.0,
                error_type='transient',
                error_frame_numbers=[10, 25, 40, 60, 85]
            )
        
        elif preset_name == "fatal_errors":
            return MockConfig(
                total_frames=50,
                render_delay_ms=30.0,
                error_type='frame_fatal',
                error_frame_numbers=[15, 35]
            )
        
        elif preset_name == "worker_crash":
            return MockConfig(
                total_frames=30,
                render_delay_ms=50.0,
                error_type='worker_fatal',
                error_frame_numbers=[20],
                error_worker_exit=False  # Safe simulation
            )
        
        elif preset_name == "memory_leak":
            return MockConfig(
                total_frames=200,
                render_delay_ms=25.0,
                simulate_memory_leak=True,
                memory_leak_per_frame_mb=0.5
            )
        
        elif preset_name == "backpressure":
            return MockConfig(
                total_frames=500,
                render_delay_ms=100.0,  # Slow rendering
                frame_generation_delay_ms=1.0  # Fast generation
            )
        
        else:
            raise ValueError(f"Unknown preset: {preset_name}")


# Global variable to store mock config for worker initialization
_GLOBAL_MOCK_CONFIG_FOR_WORKERS: Optional[Dict[str, Any]] = None


def set_mock_config_for_workers(mock_config: MockConfig):
    """Set global mock config that will be used by workers"""
    global _GLOBAL_MOCK_CONFIG_FOR_WORKERS
    _GLOBAL_MOCK_CONFIG_FOR_WORKERS = mock_config.__dict__ if mock_config else {}


def mock_worker_initializer(render_config_dict: Dict[str, Any]):
    """
    Module-level worker initializer function that can be pickled.
    Uses global config set by set_mock_config_for_workers().
    """
    global _GLOBAL_MOCK_CONFIG_FOR_WORKERS
    mock_initialize_render_worker(render_config_dict, _GLOBAL_MOCK_CONFIG_FOR_WORKERS)


def set_global_mock_config(config: MockConfig):
    """Set global mock configuration for all mock functions (legacy - use worker initializer instead)"""
    mock_render_frame_from_spec._config = config
    logger.info(f"Set global mock config: {config.total_frames} frames, "
               f"{config.render_delay_ms}ms render delay")


def get_mock_worker_pids() -> set:
    """Get set of worker PIDs that have been initialized"""
    return getattr(mock_initialize_render_worker, '_worker_pids', set())


def clear_mock_state():
    """Clear all mock state for clean testing"""
    # Clear worker PIDs
    if hasattr(mock_initialize_render_worker, '_worker_pids'):
        mock_initialize_render_worker._worker_pids.clear()
    
    # Clear leaked memory
    if hasattr(mock_render_frame_from_spec, '_leaked_memory'):
        mock_render_frame_from_spec._leaked_memory.clear()
    
    logger.info("Mock state cleared")


if __name__ == "__main__":
    # Test mock components
    print("Testing mock components...")
    
    # Test mock config presets
    for preset in ["basic", "fast_stress", "transient_errors", "worker_crash"]:
        config = TestDataFactory.create_mock_config_preset(preset)
        print(f"Preset '{preset}': {config.total_frames} frames, {config.error_type} errors")
    
    # Test mock generator
    config = TestDataFactory.create_mock_config_preset("basic")
    generator = MockFrameSpecGenerator(config)
    
    frame_count = 0
    for frame_spec in generator:
        frame_count += 1
        if frame_count <= 3:
            print(f"Frame {frame_spec['frame_index']}: {len(frame_spec['bars'])} bars")
    
    print(f"Generated {frame_count} frames successfully")
    print("Mock components test complete!")