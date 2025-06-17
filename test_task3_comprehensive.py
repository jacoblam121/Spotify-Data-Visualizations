#!/usr/bin/env python3
"""
Comprehensive Test Suite for Task 3 - Parallel Render Manager

Interactive menu-based test suite with advanced scenarios:
- Basic functionality testing
- Error injection and recovery testing  
- Performance and scalability testing
- Memory usage monitoring
- Signal handling and graceful shutdown
- Integration testing with real components
"""

import os
import sys
import time
import signal
import subprocess
import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import core components
from parallel_render_manager import (
    ParallelRenderManager, 
    RenderingConfig, 
    ProgressInfo,
    parallel_render_frames
)
from stateless_renderer import (
    RenderConfig, 
    create_render_config_from_app_config,
    initialize_render_worker,
    render_frame_from_spec
)
from config_loader import AppConfig
from test_mock_components import (
    MockFrameSpecGenerator,
    MockConfig,
    TestDataFactory,
    mock_render_frame_from_spec,
    mock_initialize_render_worker,
    set_mock_config_for_workers,
    mock_worker_initializer,
    set_global_mock_config,
    clear_mock_state,
    get_mock_worker_pids
)

# Try to import psutil for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available - memory monitoring will be limited")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MemoryMonitor:
    """Monitor memory usage during testing"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and PSUTIL_AVAILABLE
        self.process = psutil.Process() if self.enabled else None
        self.memory_log = []
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval_seconds: float = 0.5):
        """Start memory monitoring in background thread"""
        if not self.enabled:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval_seconds,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("Memory monitoring stopped")
    
    def _monitor_loop(self, interval: float):
        """Background monitoring loop"""
        while self.monitoring:
            if self.process:
                try:
                    # Get memory info for main process
                    main_rss = self.process.memory_info().rss
                    
                    # Get memory info for child processes (workers)
                    child_rss = sum(
                        child.memory_info().rss 
                        for child in self.process.children(recursive=True)
                        if child.is_running()
                    )
                    
                    total_rss = main_rss + child_rss
                    self.memory_log.append({
                        'timestamp': time.time(),
                        'main_rss_mb': main_rss / (1024 * 1024),
                        'worker_rss_mb': child_rss / (1024 * 1024),
                        'total_rss_mb': total_rss / (1024 * 1024)
                    })
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            time.sleep(interval)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        if not self.memory_log:
            return {'available': False, 'reason': 'No data collected'}
        
        total_values = [entry['total_rss_mb'] for entry in self.memory_log]
        worker_values = [entry['worker_rss_mb'] for entry in self.memory_log]
        
        return {
            'available': True,
            'peak_total_mb': max(total_values),
            'peak_worker_mb': max(worker_values),
            'avg_total_mb': sum(total_values) / len(total_values),
            'avg_worker_mb': sum(worker_values) / len(worker_values),
            'samples_count': len(self.memory_log),
            'duration_seconds': self.memory_log[-1]['timestamp'] - self.memory_log[0]['timestamp'] if len(self.memory_log) > 1 else 0
        }


class Task3ComprehensiveTester:
    """Interactive comprehensive test suite for Task 3"""
    
    def __init__(self):
        self.config = None
        self.render_config = None
        self.test_results = []
        self.memory_monitor = MemoryMonitor()
        
        # Test state
        self._shutdown_test_process = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] {level}:"
        print(f"{prefix} {message}")
    
    def setup_environment(self):
        """Set up test environment"""
        print("\n🔧 Setting up test environment...")
        
        # Set encoding
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # Try to load real configuration
        if os.path.exists('configurations.txt'):
            try:
                self.config = AppConfig('configurations.txt')
                self.render_config = create_render_config_from_app_config(self.config)
                print("✓ Real configuration loaded")
            except Exception as e:
                print(f"⚠️ Real config failed, using test config: {e}")
                self.render_config = TestDataFactory.create_test_render_config()
        else:
            print("⚠️ configurations.txt not found, using test config")
            self.render_config = TestDataFactory.create_test_render_config()
        
        # Clear any previous mock state
        clear_mock_state()
        
        return True
    
    def show_menu(self):
        """Display interactive test menu"""
        print("\n" + "=" * 80)
        print("🧪 Task 3 Comprehensive Test Suite - Parallel Render Manager")
        print("=" * 80)
        print("\n📊 BASIC FUNCTIONALITY TESTS:")
        print("  1.  Basic Parallel Rendering (Mock Components)")
        print("  2.  Configuration Validation")
        print("  3.  TaskContext and State Management")
        print("  4.  Progress Reporting")
        
        print("\n💥 ERROR HANDLING & RECOVERY TESTS:")
        print("  5.  Transient Error Handling and Retry Logic")
        print("  6.  Frame Fatal Error Handling")
        print("  7.  Worker Fatal Error and Circuit Breaker")
        print("  8.  Mixed Error Scenarios")
        
        print("\n⚡ PERFORMANCE & SCALABILITY TESTS:")
        print("  9.  Performance Benchmarking")
        print("  10. Memory Usage Monitoring")
        print("  11. Backpressure Control Validation")
        print("  12. Worker Recycling (maxtasksperchild)")
        
        print("\n🔄 ADVANCED SCENARIOS:")
        print("  13. Signal Handling (SIGINT/SIGTERM)")
        print("  14. Graceful Shutdown Under Load")
        print("  15. Integration with Real Components")
        print("  16. Stress Testing (Large Scale)")
        
        print("\n🛠️  UTILITIES:")
        print("  17. Memory Monitor Demo")
        print("  18. Mock Component Demo")
        print("  19. Clear Test State")
        print("  20. Show Test Results Summary")
        print("\n  0.  Exit")
        print("\n" + "=" * 80)
    
    def run_test_1_basic_parallel(self):
        """Test 1: Basic parallel rendering with mock components"""
        self.log("Test 1: Basic Parallel Rendering", "TEST")
        print("=" * 60)
        
        # Get user configuration
        workers = self._get_int_input("Number of workers", default=2, min_val=1, max_val=8)
        frames = self._get_int_input("Number of frames", default=20, min_val=5, max_val=1000)
        render_delay = self._get_float_input("Render delay per frame (ms)", default=50.0, min_val=1.0)
        
        try:
            # Setup mock configuration
            mock_config = MockConfig(
                total_frames=frames,
                render_delay_ms=render_delay
            )
            
            # Create mock generator
            generator = MockFrameSpecGenerator(mock_config)
            
            # Setup rendering configuration with mock worker initializer
            rendering_config = RenderingConfig(max_workers=workers)
            
            # Create manager
            manager = ParallelRenderManager(self.render_config, rendering_config)
            
            # Override render function with mock and use proper worker initialization
            import parallel_render_manager
            import stateless_renderer
            original_initialize = parallel_render_manager.initialize_render_worker
            original_render = parallel_render_manager.render_frame_from_spec
            original_stateless_render = stateless_renderer.render_frame_from_spec
            
            # Use the new mock worker initializer pattern
            set_mock_config_for_workers(mock_config)
            parallel_render_manager.initialize_render_worker = mock_worker_initializer
            parallel_render_manager.render_frame_from_spec = mock_render_frame_from_spec
            stateless_renderer.render_frame_from_spec = mock_render_frame_from_spec
            
            # Setup progress tracking
            def progress_callback(progress: ProgressInfo):
                print(f"  Progress: {progress.frames_completed}/{progress.frames_total} "
                      f"({progress.success_rate:.1%} success) "
                      f"[{progress.current_fps:.1f} FPS]")
            
            # Start memory monitoring
            self.memory_monitor.start_monitoring()
            
            # Run the test
            start_time = time.time()
            self.log("Starting parallel rendering...")
            
            results = manager.render_frames(generator, progress_callback)
            
            end_time = time.time()
            self.memory_monitor.stop_monitoring()
            
            # Restore original functions
            parallel_render_manager.initialize_render_worker = original_initialize
            parallel_render_manager.render_frame_from_spec = original_render
            stateless_renderer.render_frame_from_spec = original_stateless_render
            
            # Analyze results
            duration = end_time - start_time
            completed = results['stats'].completed_frames
            failed = results['stats'].failed_frames
            
            print(f"\n📊 Results:")
            print(f"  Duration: {duration:.2f} seconds")
            print(f"  Completed frames: {completed}")
            print(f"  Failed frames: {failed}")
            print(f"  Success rate: {completed/(completed+failed):.1%}")
            print(f"  Average FPS: {completed/duration:.1f}")
            
            # Memory analysis
            memory_stats = self.memory_monitor.get_memory_stats()
            if memory_stats['available']:
                print(f"  Peak memory: {memory_stats['peak_total_mb']:.1f} MB")
                print(f"  Worker memory: {memory_stats['peak_worker_mb']:.1f} MB")
            
            # Check for worker PIDs
            worker_pids = get_mock_worker_pids()
            print(f"  Workers used: {len(worker_pids)} processes")
            
            success = completed == frames and failed == 0
            print(f"\n{'✓ TEST PASSED' if success else '✗ TEST FAILED'}")
            
            self.test_results.append({
                'test': 'Basic Parallel Rendering',
                'success': success,
                'details': f"{completed}/{frames} frames, {duration:.2f}s"
            })
            
            return success
            
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_test_5_transient_errors(self):
        """Test 5: Transient error handling and retry logic"""
        self.log("Test 5: Transient Error Handling", "TEST")
        print("=" * 60)
        
        frames = self._get_int_input("Number of frames", default=50, min_val=10, max_val=500)
        error_frames_str = input("Error frame numbers (comma-separated, e.g., '5,15,25'): ").strip()
        
        try:
            # Parse error frames
            error_frames = []
            if error_frames_str:
                error_frames = [int(x.strip()) for x in error_frames_str.split(',')]
            else:
                # Default error frames
                error_frames = [frames//4, frames//2, 3*frames//4]
            
            # Setup mock configuration with transient errors
            mock_config = MockConfig(
                total_frames=frames,
                render_delay_ms=30.0,
                error_type='transient',
                error_frame_numbers=error_frames
            )
            
            # Create components
            generator = MockFrameSpecGenerator(mock_config)
            rendering_config = RenderingConfig(max_workers=2, max_retries_transient=3)
            manager = ParallelRenderManager(self.render_config, rendering_config)
            
            # Override with mock functions using proper worker initialization
            import parallel_render_manager
            import stateless_renderer
            original_initialize = parallel_render_manager.initialize_render_worker
            original_render = parallel_render_manager.render_frame_from_spec
            original_stateless_render = stateless_renderer.render_frame_from_spec
            
            # Use the new mock worker initializer pattern
            set_mock_config_for_workers(mock_config)
            parallel_render_manager.initialize_render_worker = mock_worker_initializer
            parallel_render_manager.render_frame_from_spec = mock_render_frame_from_spec
            stateless_renderer.render_frame_from_spec = mock_render_frame_from_spec
            
            print(f"Injecting transient errors on frames: {error_frames}")
            
            # Track retries
            retry_counts = {}
            def progress_callback(progress: ProgressInfo):
                print(f"  Progress: {progress.frames_completed}/{progress.frames_total} "
                      f"({progress.success_rate:.1%} success)")
            
            # Run test
            self.log("Starting rendering with error injection...")
            results = manager.render_frames(generator, progress_callback)
            
            # Restore functions
            parallel_render_manager.initialize_render_worker = original_initialize
            parallel_render_manager.render_frame_from_spec = original_render
            stateless_renderer.render_frame_from_spec = original_stateless_render
            
            # Analyze results
            completed = results['stats'].completed_frames
            failed = results['stats'].failed_frames
            retried = results['stats'].retried_frames
            
            print(f"\n📊 Results:")
            print(f"  Completed frames: {completed}")
            print(f"  Failed frames: {failed}")
            print(f"  Retried frames: {retried}")
            print(f"  Expected retries: {len(error_frames) * 3}")  # 3 retries per error
            
            # Check that errors were retried and eventually succeeded
            expected_completed = frames
            success = (completed == expected_completed and 
                      retried >= len(error_frames) and
                      failed == 0)
            
            print(f"\n{'✓ TEST PASSED' if success else '✗ TEST FAILED'}")
            if not success:
                print(f"  Expected {expected_completed} completed, got {completed}")
                print(f"  Expected ≥{len(error_frames)} retries, got {retried}")
            
            self.test_results.append({
                'test': 'Transient Error Handling',
                'success': success,
                'details': f"{completed}/{frames} frames, {retried} retries"
            })
            
            return success
            
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_test_7_worker_fatal(self):
        """Test 7: Worker fatal error and circuit breaker"""
        self.log("Test 7: Worker Fatal Error & Circuit Breaker", "TEST")
        print("=" * 60)
        
        frames = self._get_int_input("Number of frames", default=30, min_val=10, max_val=100)
        error_frame = self._get_int_input("Frame to trigger worker fatal", default=15, min_val=5, max_val=frames-5)
        
        try:
            # Setup mock configuration with worker fatal error
            mock_config = MockConfig(
                total_frames=frames,
                render_delay_ms=50.0,
                error_type='worker_fatal',
                error_frame_numbers=[error_frame],
                error_worker_exit=False  # Safe simulation
            )
            
            # Create components
            generator = MockFrameSpecGenerator(mock_config)
            rendering_config = RenderingConfig(
                max_workers=2, 
                max_worker_failures=1  # Low threshold for testing
            )
            manager = ParallelRenderManager(self.render_config, rendering_config)
            
            # Override with mock functions using proper worker initialization
            import parallel_render_manager
            import stateless_renderer
            original_initialize = parallel_render_manager.initialize_render_worker
            original_render = parallel_render_manager.render_frame_from_spec
            original_stateless_render = stateless_renderer.render_frame_from_spec
            
            # Use the new mock worker initializer pattern
            set_mock_config_for_workers(mock_config)
            parallel_render_manager.initialize_render_worker = mock_worker_initializer
            parallel_render_manager.render_frame_from_spec = mock_render_frame_from_spec
            stateless_renderer.render_frame_from_spec = mock_render_frame_from_spec
            
            print(f"Injecting worker fatal error on frame: {error_frame}")
            print(f"Circuit breaker threshold: {rendering_config.max_worker_failures} failures")
            
            def progress_callback(progress: ProgressInfo):
                print(f"  Progress: {progress.frames_completed}/{progress.frames_total}")
            
            # Run test
            self.log("Starting rendering with worker fatal error...")
            results = manager.render_frames(generator, progress_callback)
            
            # Restore functions
            parallel_render_manager.initialize_render_worker = original_initialize
            parallel_render_manager.render_frame_from_spec = original_render
            stateless_renderer.render_frame_from_spec = original_stateless_render
            
            # Analyze results
            completed = results['stats'].completed_frames
            failed = results['stats'].failed_frames
            worker_failures = results['stats'].worker_failures
            status = results.get('status', 'unknown')
            
            print(f"\n📊 Results:")
            print(f"  Status: {status}")
            print(f"  Completed frames: {completed}")
            print(f"  Failed frames: {failed}")
            print(f"  Worker failures: {worker_failures}")
            print(f"  Total processed: {completed + failed}")
            
            # Check that circuit breaker triggered
            circuit_breaker_triggered = (status == 'error' and 
                                       'worker failures' in results.get('error', '').lower())
            
            print(f"  Circuit breaker triggered: {circuit_breaker_triggered}")
            
            success = (worker_failures >= 1 and 
                      completed < frames and  # Job should not complete all frames
                      circuit_breaker_triggered)
            
            print(f"\n{'✓ TEST PASSED' if success else '✗ TEST FAILED'}")
            if not success:
                print(f"  Expected worker failure and circuit breaker activation")
                print(f"  Got worker_failures={worker_failures}, status={status}")
            
            self.test_results.append({
                'test': 'Worker Fatal Error & Circuit Breaker',
                'success': success,
                'details': f"{worker_failures} failures, {completed}/{frames} frames"
            })
            
            return success
            
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_test_10_memory_monitoring(self):
        """Test 10: Memory usage monitoring"""
        self.log("Test 10: Memory Usage Monitoring", "TEST")
        print("=" * 60)
        
        if not PSUTIL_AVAILABLE:
            print("❌ psutil not available - cannot run memory monitoring test")
            return False
        
        frames = self._get_int_input("Number of frames", default=100, min_val=50, max_val=1000)
        simulate_leak = self._get_bool_input("Simulate memory leak", default=False)
        
        try:
            # Setup mock configuration
            mock_config = MockConfig(
                total_frames=frames,
                render_delay_ms=20.0,
                simulate_memory_leak=simulate_leak,
                memory_leak_per_frame_mb=0.2
            )
            
            # Create components
            generator = MockFrameSpecGenerator(mock_config)
            rendering_config = RenderingConfig(max_workers=3)
            manager = ParallelRenderManager(self.render_config, rendering_config)
            
            # Override with mock functions using proper worker initialization
            import parallel_render_manager
            import stateless_renderer
            original_initialize = parallel_render_manager.initialize_render_worker
            original_render = parallel_render_manager.render_frame_from_spec
            original_stateless_render = stateless_renderer.render_frame_from_spec
            
            # Use the new mock worker initializer pattern
            set_mock_config_for_workers(mock_config)
            parallel_render_manager.initialize_render_worker = mock_worker_initializer
            parallel_render_manager.render_frame_from_spec = mock_render_frame_from_spec
            stateless_renderer.render_frame_from_spec = mock_render_frame_from_spec
            
            # Get baseline memory
            process = psutil.Process()
            baseline_memory = process.memory_info().rss / (1024 * 1024)
            print(f"Baseline memory: {baseline_memory:.1f} MB")
            
            # Start intensive memory monitoring
            self.memory_monitor.start_monitoring(interval_seconds=0.2)
            
            def progress_callback(progress: ProgressInfo):
                if progress.frames_completed % 20 == 0:
                    print(f"  Progress: {progress.frames_completed}/{progress.frames_total}")
            
            # Run test
            self.log("Starting rendering with memory monitoring...")
            results = manager.render_frames(generator, progress_callback)
            
            self.memory_monitor.stop_monitoring()
            
            # Restore functions
            parallel_render_manager.initialize_render_worker = original_initialize
            parallel_render_manager.render_frame_from_spec = original_render
            stateless_renderer.render_frame_from_spec = original_stateless_render
            
            # Analyze memory usage (both main process and worker-reported)
            memory_stats = self.memory_monitor.get_memory_stats()
            final_memory = process.memory_info().rss / (1024 * 1024)
            
            # Collect worker-reported memory deltas
            worker_memory_deltas = []
            for result_list in [results['completed_frames'], results['failed_frames']]:
                for frame_result in result_list:
                    if hasattr(frame_result, 'memory_delta_bytes') and frame_result.memory_delta_bytes:
                        worker_memory_deltas.append(frame_result.memory_delta_bytes / (1024 * 1024))
            
            # If we have frame results as dicts (from the results dict itself)
            if 'frame_results' in results:
                for frame_idx, frame_result in results['frame_results'].items():
                    if hasattr(frame_result, 'memory_delta_bytes') and frame_result.memory_delta_bytes:
                        worker_memory_deltas.append(frame_result.memory_delta_bytes / (1024 * 1024))
            
            total_worker_memory_delta = sum(worker_memory_deltas) if worker_memory_deltas else 0
            
            print(f"\n📊 Memory Analysis:")
            print(f"  Baseline memory (main): {baseline_memory:.1f} MB")
            print(f"  Final memory (main): {final_memory:.1f} MB")
            print(f"  Main process increase: {final_memory - baseline_memory:.1f} MB")
            print(f"  Worker memory deltas: {len(worker_memory_deltas)} reported")
            print(f"  Total worker memory delta: {total_worker_memory_delta:.1f} MB")
            
            if memory_stats['available']:
                print(f"  Peak total memory: {memory_stats['peak_total_mb']:.1f} MB")
                print(f"  Peak worker memory: {memory_stats['peak_worker_mb']:.1f} MB")
                print(f"  Average total memory: {memory_stats['avg_total_mb']:.1f} MB")
                print(f"  Monitoring samples: {memory_stats['samples_count']}")
            
            # Check for memory leaks using worker-reported data
            if simulate_leak:
                expected_leak = frames * mock_config.memory_leak_per_frame_mb
                print(f"  Expected leak: ~{expected_leak:.1f} MB")
                print(f"  Worker-reported delta: {total_worker_memory_delta:.1f} MB")
                
                # Memory leak should be detectable in worker processes
                success = total_worker_memory_delta > expected_leak * 0.3  # Allow for some variance
                print(f"  Memory leak detected: {'Yes' if success else 'No'}")
            else:
                # Memory should be relatively stable
                main_increase = final_memory - baseline_memory
                success = main_increase < 50.0 and abs(total_worker_memory_delta) < 10.0
                print(f"  Memory stable: {'Yes' if success else 'No'}")
            
            print(f"\n{'✓ TEST PASSED' if success else '✗ TEST FAILED'}")
            
            self.test_results.append({
                'test': 'Memory Usage Monitoring',
                'success': success,
                'details': f"{final_memory - baseline_memory:.1f} MB increase"
            })
            
            return success
            
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_test_13_signal_handling(self):
        """Test 13: Signal handling (SIGINT/SIGTERM)"""
        self.log("Test 13: Signal Handling", "TEST")
        print("=" * 60)
        
        print("This test will run rendering in a subprocess and send SIGINT")
        proceed = self._get_bool_input("Proceed with signal test", default=True)
        
        if not proceed:
            print("Test skipped")
            return True
        
        try:
            # Create test script for subprocess
            test_script = """
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parallel_render_manager import ParallelRenderManager, RenderingConfig
from test_mock_components import (
    MockFrameSpecGenerator, MockConfig, TestDataFactory,
    mock_render_frame_from_spec, mock_initialize_render_worker,
    set_global_mock_config
)
import parallel_render_manager

# Setup
mock_config = MockConfig(total_frames=1000, render_delay_ms=100.0)
set_global_mock_config(mock_config)

generator = MockFrameSpecGenerator(mock_config)
render_config = TestDataFactory.create_test_render_config()
rendering_config = RenderingConfig(max_workers=2)
manager = ParallelRenderManager(render_config, rendering_config)

# Override with mocks
import stateless_renderer
parallel_render_manager.initialize_render_worker = mock_initialize_render_worker
parallel_render_manager.render_frame_from_spec = mock_render_frame_from_spec
stateless_renderer.render_frame_from_spec = mock_render_frame_from_spec

def progress_callback(progress):
    print(f"Progress: {progress.frames_completed}/{progress.frames_total}")

print("Starting long-running render job...")
results = manager.render_frames(generator, progress_callback)
print(f"Completed: {results['stats'].completed_frames} frames")
"""
            
            # Write test script
            script_path = "temp_signal_test.py"
            with open(script_path, 'w') as f:
                f.write(test_script)
            
            # Start subprocess
            self.log("Starting subprocess for signal test...")
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a bit for it to start
            time.sleep(3.0)
            
            # Send SIGINT
            self.log("Sending SIGINT signal...")
            process.send_signal(signal.SIGINT)
            
            # Wait for graceful shutdown
            try:
                stdout, stderr = process.communicate(timeout=15.0)
                returncode = process.returncode
                
                print(f"\n📊 Signal Test Results:")
                print(f"  Return code: {returncode}")
                print(f"  Stdout lines: {len(stdout.splitlines())}")
                print(f"  Stderr lines: {len(stderr.splitlines())}")
                
                if stdout:
                    print(f"  Last stdout: {stdout.splitlines()[-1] if stdout.splitlines() else 'None'}")
                
                # Check for graceful shutdown indicators
                graceful_shutdown = (
                    returncode == 0 or returncode == -2 and  # SIGINT can return -2
                    "Completed:" in stdout and
                    not "Traceback" in stderr
                )
                
                success = graceful_shutdown
                print(f"  Graceful shutdown: {'Yes' if success else 'No'}")
                
            except subprocess.TimeoutExpired:
                print("❌ Process did not terminate within timeout")
                process.kill()
                process.wait()
                success = False
            
            # Cleanup
            if os.path.exists(script_path):
                os.remove(script_path)
            
            print(f"\n{'✓ TEST PASSED' if success else '✗ TEST FAILED'}")
            
            self.test_results.append({
                'test': 'Signal Handling',
                'success': success,
                'details': f"Return code: {returncode if 'returncode' in locals() else 'timeout'}"
            })
            
            return success
            
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def show_test_results_summary(self):
        """Show summary of all test results"""
        self.log("Test Results Summary", "SUMMARY")
        print("=" * 60)
        
        if not self.test_results:
            print("No tests have been run yet.")
            return
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Overall Results: {passed}/{total} tests passed ({passed/total:.1%})")
        print()
        
        for i, result in enumerate(self.test_results, 1):
            status = "✓ PASS" if result['success'] else "✗ FAIL"
            print(f"{i:2d}. {status} - {result['test']}")
            print(f"     {result['details']}")
        
        print(f"\n{'🎉 ALL TESTS PASSED!' if passed == total else f'❌ {total-passed} TESTS FAILED'}")
    
    # Utility methods
    def _get_int_input(self, prompt: str, default: int, min_val: int = None, max_val: int = None) -> int:
        """Get integer input with validation"""
        while True:
            try:
                value = input(f"{prompt} (default {default}): ").strip()
                if not value:
                    return default
                
                result = int(value)
                if min_val is not None and result < min_val:
                    print(f"Value must be >= {min_val}")
                    continue
                if max_val is not None and result > max_val:
                    print(f"Value must be <= {max_val}")
                    continue
                
                return result
            except ValueError:
                print("Please enter a valid integer")
    
    def _get_float_input(self, prompt: str, default: float, min_val: float = None) -> float:
        """Get float input with validation"""
        while True:
            try:
                value = input(f"{prompt} (default {default}): ").strip()
                if not value:
                    return default
                
                result = float(value)
                if min_val is not None and result < min_val:
                    print(f"Value must be >= {min_val}")
                    continue
                
                return result
            except ValueError:
                print("Please enter a valid number")
    
    def _get_bool_input(self, prompt: str, default: bool) -> bool:
        """Get boolean input"""
        default_str = "y" if default else "n"
        while True:
            value = input(f"{prompt} (y/n, default {default_str}): ").strip().lower()
            if not value:
                return default
            if value in ['y', 'yes', 'true', '1']:
                return True
            elif value in ['n', 'no', 'false', '0']:
                return False
            else:
                print("Please enter y/n")
    
    def run_interactive_menu(self):
        """Run the interactive test menu"""
        if not self.setup_environment():
            print("Failed to setup environment")
            return
        
        while True:
            self.show_menu()
            
            try:
                choice = input("\nSelect test (0-20): ").strip()
                
                if choice == '0':
                    print("Exiting test suite. Goodbye!")
                    break
                elif choice == '1':
                    self.run_test_1_basic_parallel()
                elif choice == '5':
                    self.run_test_5_transient_errors()
                elif choice == '7':
                    self.run_test_7_worker_fatal()
                elif choice == '10':
                    self.run_test_10_memory_monitoring()
                elif choice == '13':
                    self.run_test_13_signal_handling()
                elif choice == '19':
                    clear_mock_state()
                    self.test_results.clear()
                    print("✓ Test state cleared")
                elif choice == '20':
                    self.show_test_results_summary()
                else:
                    print(f"Test {choice} not implemented yet. Coming soon!")
                
                if choice not in ['0', '19', '20']:
                    input("\nPress Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\nExiting due to keyboard interrupt...")
                break
            except Exception as e:
                print(f"Error: {e}")
                input("Press Enter to continue...")


def main():
    """Main entry point"""
    print("🚀 Starting Task 3 Comprehensive Test Suite...")
    
    tester = Task3ComprehensiveTester()
    tester.run_interactive_menu()


if __name__ == "__main__":
    main()