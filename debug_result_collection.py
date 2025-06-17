#!/usr/bin/env python3
"""
Debug Result Collection Issues
==============================

Implements Gemini's detailed exception handling strategy to diagnose
the exact cause of the 37% frame loss issue.

This script will pinpoint whether frames are lost due to:
1. Serialization/pickling errors (most likely)
2. Timeout errors 
3. Process crashes
4. Other transport failures
"""

import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError, CancelledError
# Note: BrokenProcessPool is not available in Python 3.12, we'll handle it differently
from typing import Dict, Any, List, Tuple

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stateless_renderer import RenderConfig
from test_mock_components import MockFrameSpecGenerator, MockConfig
from test_worker_helpers import top_level_test_worker_initializer, top_level_test_render_function


def analyze_result_collection_failures():
    """
    Diagnostic test to identify exact failure modes in result collection.
    
    Uses Gemini's detailed exception handling strategy to categorize failures.
    """
    print("🔍 DIAGNOSTIC: Result Collection Failure Analysis")
    print("=" * 60)
    
    # Test configuration
    workers = 8
    frames = 50  # Smaller test for focused analysis
    
    print(f"Testing with {workers} workers, {frames} frames")
    print("Looking for serialization/transport failures...")
    print()
    
    # Create test configuration
    render_config = RenderConfig(
        dpi=96,
        fig_width_pixels=1920,
        fig_height_pixels=1080,
        target_fps=30,
        font_paths={"DejaVuSans": "fonts/DejaVuSans.ttf"} if os.path.exists("fonts/DejaVuSans.ttf") else {},
        preferred_fonts=["DejaVu Sans", "sans-serif"],
        album_art_cache_dir="album_art_cache",
        album_art_visibility_threshold=0.0628,
        n_bars=10
    )
    
    # Create frame specifications
    mock_config = MockConfig(total_frames=frames, render_delay_ms=10.0)
    frame_specs = []
    
    # Generate all frame specs upfront
    generator = MockFrameSpecGenerator(mock_config)
    for _ in range(frames):
        try:
            frame_spec = next(generator)
            frame_specs.append(frame_spec)
        except StopIteration:
            break
    
    print(f"Generated {len(frame_specs)} frame specifications")
    
    # Result tracking categories
    successful_results = []
    logic_failures = []  # Failures reported by worker logic
    transport_errors = []  # Failures in IPC/serialization
    timeout_errors = []
    process_errors = []
    unknown_errors = []
    
    # Submit all tasks and collect futures
    futures_to_frame = {}
    
    try:
        with ProcessPoolExecutor(
            max_workers=workers,
            initializer=top_level_test_worker_initializer,
            initargs=(render_config.to_dict(), {})  # Empty test config for basic test
        ) as executor:
            
            print("📤 Submitting tasks...")
            
            # Submit all tasks
            for i, frame_spec in enumerate(frame_specs):
                future = executor.submit(top_level_test_render_function, frame_spec)
                futures_to_frame[future] = i
                
            print(f"✅ Submitted {len(futures_to_frame)} tasks")
            print("📥 Collecting results with detailed error analysis...")
            print()
            
            # Collect results with Gemini's detailed exception handling
            completed_count = 0
            
            for future in as_completed(futures_to_frame, timeout=120):  # 2 minute total timeout
                frame_index = futures_to_frame[future]
                
                try:
                    # CRITICAL: This is where transport errors manifest
                    result = future.result(timeout=30)  # 30 second per-task timeout
                    
                    print(f"📦 Frame {frame_index}: Got result from worker")
                    
                    # Analyze the worker's result
                    if isinstance(result, dict):
                        status = result.get('status', 'unknown')
                        if status == 'success':
                            successful_results.append({
                                'frame': frame_index,
                                'worker_pid': result.get('worker_pid', 'unknown'),
                                'render_time': result.get('render_time_seconds', 0)
                            })
                            completed_count += 1
                            print(f"  ✅ Success: Worker {result.get('worker_pid')} completed frame {frame_index}")
                        else:
                            # Worker reported an error in its logic
                            logic_failures.append({
                                'frame': frame_index,
                                'worker_pid': result.get('worker_pid', 'unknown'),
                                'error_type': result.get('error_type', 'unknown'),
                                'error_message': result.get('error', 'No message'),
                                'exception_type': result.get('exception_type', 'N/A')
                            })
                            print(f"  ❌ Logic failure: Frame {frame_index} failed in worker logic: {result.get('error', 'Unknown')}")
                    else:
                        # Unexpected result format
                        unknown_errors.append({
                            'frame': frame_index,
                            'reason': f'Unexpected result type: {type(result)}',
                            'result': str(result)[:100]  # First 100 chars
                        })
                        print(f"  ⚠️  Unexpected result format for frame {frame_index}: {type(result)}")
                
                except TimeoutError:
                    timeout_errors.append({
                        'frame': frame_index,
                        'reason': 'Result collection timed out (30s)'
                    })
                    print(f"  ⏰ Timeout: Frame {frame_index} timed out waiting for result")
                    
                except CancelledError:
                    transport_errors.append({
                        'frame': frame_index,
                        'reason': 'Future was cancelled'
                    })
                    print(f"  🚫 Cancelled: Frame {frame_index} future was cancelled")
                    
                except RuntimeError as e:
                    # In Python 3.12, broken process pools manifest as RuntimeError
                    if 'broken' in str(e).lower() or 'pool' in str(e).lower():
                        process_errors.append({
                            'frame': frame_index,
                            'reason': f'Process pool broken: {e}',
                            'error_type': 'BrokenProcessPool'
                        })
                        print(f"  💥 Process crash: Frame {frame_index} caused process pool failure: {e}")
                        # This is catastrophic - may affect other frames too
                        break
                    else:
                        # Regular RuntimeError
                        transport_errors.append({
                            'frame': frame_index,
                            'reason': f'Runtime error: {e}',
                            'error_type': 'RuntimeError',
                            'error_message': str(e)
                        })
                        print(f"  🔥 Runtime error: Frame {frame_index} failed with: {e}")
                    
                except Exception as e:
                    # This should catch PicklingError, ImportError, etc.
                    transport_errors.append({
                        'frame': frame_index,
                        'reason': f'Transport/deserialization error: {type(e).__name__}: {e}',
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    })
                    print(f"  🔥 Transport error: Frame {frame_index} failed during transport: {type(e).__name__}: {e}")
        
    except Exception as executor_error:
        print(f"💥 EXECUTOR ERROR: {type(executor_error).__name__}: {executor_error}")
        return False
    
    # Comprehensive results analysis
    print("\n" + "=" * 60)
    print("📊 DETAILED FAILURE ANALYSIS")
    print("=" * 60)
    
    total_submitted = len(frame_specs)
    total_collected = len(successful_results) + len(logic_failures) + len(transport_errors) + len(timeout_errors) + len(process_errors) + len(unknown_errors)
    
    print(f"📤 Total submitted: {total_submitted}")
    print(f"📥 Total collected: {total_collected}")
    print(f"❓ Missing results: {total_submitted - total_collected}")
    print()
    
    print(f"✅ Successful: {len(successful_results)} ({len(successful_results)/total_submitted:.1%})")
    print(f"❌ Logic failures: {len(logic_failures)} ({len(logic_failures)/total_submitted:.1%})")
    print(f"🔥 Transport errors: {len(transport_errors)} ({len(transport_errors)/total_submitted:.1%})")
    print(f"⏰ Timeout errors: {len(timeout_errors)} ({len(timeout_errors)/total_submitted:.1%})")
    print(f"💥 Process errors: {len(process_errors)} ({len(process_errors)/total_submitted:.1%})")
    print(f"⚠️  Unknown errors: {len(unknown_errors)} ({len(unknown_errors)/total_submitted:.1%})")
    print()
    
    # Show detailed error breakdown
    if transport_errors:
        print("🔥 TRANSPORT ERROR DETAILS:")
        for error in transport_errors[:5]:  # First 5 transport errors
            print(f"  Frame {error['frame']}: {error['reason']}")
        if len(transport_errors) > 5:
            print(f"  ... and {len(transport_errors)-5} more transport errors")
        print()
    
    if timeout_errors:
        print("⏰ TIMEOUT ERROR DETAILS:")
        for error in timeout_errors[:5]:
            print(f"  Frame {error['frame']}: {error['reason']}")
        print()
    
    if logic_failures:
        print("❌ LOGIC FAILURE DETAILS:")
        for error in logic_failures[:5]:
            print(f"  Frame {error['frame']} (Worker {error['worker_pid']}): {error['error_message']}")
        print()
    
    if process_errors:
        print("💥 PROCESS ERROR DETAILS:")
        for error in process_errors:
            print(f"  Frame {error['frame']}: {error['reason']}")
        print()
    
    # Analysis and recommendations
    print("🎯 ROOT CAUSE ANALYSIS:")
    
    if len(transport_errors) > 0:
        print(f"  🚨 TRANSPORT FAILURES DETECTED: {len(transport_errors)} frames lost in IPC")
        print(f"     This confirms Gemini's serialization failure hypothesis!")
        print(f"     Most likely cause: PicklingError from non-serializable objects")
        
    if len(timeout_errors) > 0:
        print(f"  ⏰ TIMEOUT ISSUES: {len(timeout_errors)} frames timed out")
        print(f"     Workers may be hanging or taking too long")
        
    if len(process_errors) > 0:
        print(f"  💥 PROCESS CRASHES: {len(process_errors)} workers crashed")
        print(f"     This indicates serious stability issues")
        
    if total_collected < total_submitted:
        missing = total_submitted - total_collected
        print(f"  ❓ MISSING RESULTS: {missing} frames completely lost")
        print(f"     These may have been submitted but never returned")
    
    print()
    print("💡 RECOMMENDED NEXT STEPS:")
    
    if transport_errors:
        print("  1. Implement Gemini's 'Result-as-Value' pattern")
        print("  2. Ensure all worker return values are fully serializable")
        print("  3. Add explicit matplotlib object cleanup (plt.close(fig))")
        
    if timeout_errors or process_errors:
        print("  4. Investigate worker process stability issues")
        print("  5. Implement per-worker matplotlib cache isolation")
        
    # Return success if we can explain the failures
    explained_failures = len(transport_errors) + len(timeout_errors) + len(process_errors) + len(logic_failures)
    success_rate = len(successful_results) / total_submitted
    
    if success_rate < 0.8 and explained_failures > 0:
        print(f"\n🎉 DIAGNOSIS SUCCESSFUL: Found {explained_failures} explained failure(s)")
        print("    Root cause identified - ready to implement fix!")
        return True
    elif success_rate >= 0.8:
        print(f"\n✅ SYSTEM APPEARS HEALTHY: {success_rate:.1%} success rate")
        return True
    else:
        print(f"\n❌ DIAGNOSIS INCOMPLETE: Still have unexplained failures")
        return False


if __name__ == "__main__":
    print("🚀 Starting Result Collection Diagnostic")
    print("This will identify the exact failure mode causing 37% frame loss")
    print()
    
    success = analyze_result_collection_failures()
    
    if success:
        print("\n🎯 Diagnostic complete - ready to implement targeted fix!")
    else:
        print("\n⚠️  Diagnostic inconclusive - may need deeper investigation")
    
    print("\nNext: Run this script to see detailed failure categorization")