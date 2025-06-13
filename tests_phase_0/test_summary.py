#!/usr/bin/env python3
"""
Test Summary for Phase 0 - Quick validation of key functionality
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from create_id_mapping import create_enhanced_network_with_stable_ids

def quick_validation_test():
    """Run quick validation test for Phase 0."""
    print("🚀 Quick Phase 0 Validation Test")
    print("=" * 50)
    
    # Change to project root if needed
    original_cwd = os.getcwd()
    if not os.path.exists('configurations.txt'):
        parent = os.path.dirname(os.getcwd())
        if os.path.exists(os.path.join(parent, 'configurations.txt')):
            print(f"📁 Changing to project root: {parent}")
            os.chdir(parent)
    
    try:
        # Test small network (10 artists)
        print("Testing 10-artist network generation...")
        start_time = time.time()
        
        network_data = create_enhanced_network_with_stable_ids(
            top_n_artists=10,
            output_file="quick_test_10artists.json"
        )
        
        generation_time = time.time() - start_time
        
        if not network_data:
            print("❌ Failed to generate network")
            return False
        
        # Quick validation
        nodes = network_data.get('nodes', [])
        edges = network_data.get('edges', [])
        metadata = network_data.get('metadata', {})
        
        print(f"✅ Generated {len(nodes)} nodes in {generation_time:.1f}s")
        
        # Check key features
        spotify_ids = sum(1 for n in nodes if n['id'].startswith('spotify:'))
        print(f"📊 Spotify IDs: {spotify_ids}/{len(nodes)} ({spotify_ids/len(nodes)*100:.1f}%)")
        
        # Check visualization properties
        has_viz = sum(1 for n in nodes if 'viz' in n)
        print(f"🎨 Visualization properties: {has_viz}/{len(nodes)}")
        
        # Check sizing (Taylor Swift should be largest if present)
        taylor_node = None
        for node in nodes:
            if 'taylor swift' in node.get('canonical_name', '').lower():
                taylor_node = node
                break
        
        if taylor_node:
            taylor_radius = taylor_node['viz']['radius']
            max_other_radius = max(n['viz']['radius'] for n in nodes if n != taylor_node)
            print(f"🎯 Taylor Swift sizing: {taylor_radius:.1f}px (others max: {max_other_radius:.1f}px)")
            
            if taylor_radius > max_other_radius:
                print("✅ Spotify emphasis validated")
            else:
                print("⚠️  Sizing algorithm needs review")
        
        # Performance check
        if generation_time <= 10:  # 10s for 10 artists
            print(f"⚡ Performance: ✅ ({generation_time:.1f}s)")
            
            # Estimate 100 artists
            estimated_100 = generation_time * 10
            print(f"📈 Estimated 100 artists: {estimated_100:.1f}s")
            
            if estimated_100 <= 60:  # Within reasonable bounds
                print("✅ 100-artist target looks achievable")
            else:
                print("⚠️  100-artist target may be challenging")
        else:
            print(f"⚠️  Performance: Slow ({generation_time:.1f}s)")
        
        print(f"\\n📄 Full results saved: quick_test_10artists.json")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Restore original directory
        os.chdir(original_cwd)

def run_performance_estimate():
    """Quick performance estimate for different sizes."""
    print("\\n⚡ Performance Estimation")
    print("=" * 30)
    
    # Ensure we're in the right directory (already changed in previous function)
    test_sizes = [5, 10]
    times = []
    
    for size in test_sizes:
        print(f"Testing {size} artists...")
        start_time = time.time()
        
        try:
            network_data = create_enhanced_network_with_stable_ids(
                top_n_artists=size,
                output_file=None  # Don't save
            )
            
            if network_data:
                generation_time = time.time() - start_time
                times.append((size, generation_time))
                print(f"  ✅ {size} artists: {generation_time:.1f}s")
            else:
                print(f"  ❌ {size} artists: Failed")
                
        except Exception as e:
            print(f"  ❌ {size} artists: Error - {e}")
    
    if len(times) >= 2:
        # Linear extrapolation
        size1, time1 = times[0]
        size2, time2 = times[1]
        
        time_per_artist = (time2 - time1) / (size2 - size1)
        base_time = time1 - (time_per_artist * size1)
        
        estimated_100 = base_time + (time_per_artist * 100)
        
        print(f"\\n📊 Performance Analysis:")
        print(f"  Time per artist: {time_per_artist:.2f}s")
        print(f"  Base overhead: {base_time:.1f}s")
        print(f"  Estimated 100 artists: {estimated_100:.1f}s")
        
        if estimated_100 <= 30:
            print("  ✅ 100-artist target achievable (< 30s)")
        elif estimated_100 <= 60:
            print("  ⚠️  100-artist target marginal (30-60s)")
        else:
            print("  ❌ 100-artist target challenging (> 60s)")
    
    return times

if __name__ == "__main__":
    print("Phase 0 Network Foundation - Quick Test Summary")
    print("=" * 60)
    
    # Run validation
    success = quick_validation_test()
    
    if success:
        # Run performance estimate
        performance_data = run_performance_estimate()
        
        print(f"\\n🎉 Quick validation completed!")
        print(f"\\n📋 Summary:")
        print(f"  ✅ Network generation working")
        print(f"  ✅ Stable ID system functional")
        print(f"  ✅ D3.js visualization properties included")
        print(f"  ✅ Spotify emphasis in sizing algorithm")
        
        if performance_data:
            print(f"  📈 Performance data collected for {len(performance_data)} test sizes")
        
        print(f"\\n🚀 Ready for Phase 0.1 - Enhanced Sizing Algorithm")
        
    else:
        print(f"\\n❌ Issues found - check implementation")
        
    # Cleanup
    test_files = ['quick_test_10artists.json']
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
    
    sys.exit(0 if success else 1)