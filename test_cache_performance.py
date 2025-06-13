#!/usr/bin/env python3
"""
Test script to verify cache performance by running network generation twice.
The second run should be much faster if caching is working properly.
"""

import os
import sys
import time
os.chdir('/home/jacob/Spotify-Data-Visualizations')

import pandas as pd
from data_processor import clean_and_filter_data
from network_utils import initialize_network_analyzer, prepare_dataframe_for_network_analysis

def test_cache_performance():
    """Test cache performance by running network generation twice."""
    print("🧪 Testing Cache Performance - Two Consecutive Runs")
    print("=" * 60)
    
    # Load data once
    print("📂 Loading data...")
    try:
        from config_loader import AppConfig
        config = AppConfig()
        df = clean_and_filter_data(config)
        df_network = prepare_dataframe_for_network_analysis(df)
        print(f"   ✅ Loaded {len(df_network)} plays")
    except Exception as e:
        print(f"   ❌ Failed to load data: {e}")
        return
    
    # Initialize analyzer
    analyzer = initialize_network_analyzer()
    
    # Use a smaller test (20 artists) for faster testing
    print(f"\n🕸️  Testing with 20 artists for faster results...")
    
    def run_network_generation(run_number):
        """Run network generation and measure time."""
        print(f"\n{'='*20} RUN {run_number} {'='*20}")
        start_time = time.time()
        
        try:
            network_data = analyzer.create_network_data(
                df_network, 
                top_n_artists=20,  # Smaller test for speed
                min_plays_threshold=5,
                min_similarity_threshold=0.2
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✅ Run {run_number} completed in {duration:.1f} seconds")
            print(f"   Nodes: {len(network_data['nodes'])}")
            print(f"   Edges: {len(network_data['edges'])}")
            
            return duration, network_data
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            print(f"❌ Run {run_number} failed after {duration:.1f} seconds: {e}")
            return duration, None
    
    # Run 1 - Will populate cache
    duration1, network1 = run_network_generation(1)
    
    # Short pause
    time.sleep(2)
    
    # Run 2 - Should use cache
    duration2, network2 = run_network_generation(2)
    
    # Compare results
    print(f"\n📊 PERFORMANCE COMPARISON")
    print("=" * 60)
    print(f"🏃‍♂️ Run 1 (cold cache): {duration1:.1f} seconds")
    print(f"🚀 Run 2 (warm cache): {duration2:.1f} seconds")
    
    if duration2 > 0:
        speedup = duration1 / duration2
        improvement = ((duration1 - duration2) / duration1) * 100
        
        print(f"⚡ Speedup: {speedup:.1f}x faster")
        print(f"📈 Improvement: {improvement:.1f}% faster")
        
        if speedup > 2:
            print("✅ Cache is working effectively!")
        elif speedup > 1.2:
            print("⚠️  Cache is helping but could be more effective")
        else:
            print("❌ Cache doesn't seem to be working properly")
    
    # Compare results to ensure consistency
    if network1 and network2:
        edges1 = len(network1['edges'])
        edges2 = len(network2['edges'])
        
        if edges1 == edges2:
            print("✅ Both runs produced identical edge counts")
        else:
            print(f"⚠️  Edge counts differ: Run 1 = {edges1}, Run 2 = {edges2}")

if __name__ == "__main__":
    test_cache_performance()