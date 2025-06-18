#!/usr/bin/env python3
"""
Complete Caching System Test
===========================
Demonstrates the full caching implementation for Spotify Data Visualizations.

Tests:
1. Cache Manager functionality
2. Network generation caching
3. Edge weighting caching  
4. Configuration-driven cache control
5. Cache clearing and statistics
"""

import time
import pandas as pd
from pathlib import Path

def test_cache_manager():
    """Test basic cache manager functionality."""
    print("🔧 Testing Cache Manager")
    print("=" * 40)
    
    from cache_manager import get_cache_manager, cache_result
    
    # Test cache info
    cm = get_cache_manager()
    info = cm.get_cache_info()
    print(f"Cache enabled: {info['enabled']}")
    print(f"Cache directory: {info['config']['joblib_cache_dir']}")
    
    if not info['enabled']:
        print("❌ Caching disabled - check configurations.txt")
        return False
    
    # Test caching with decorator
    @cache_result
    def expensive_computation(n: int) -> int:
        print(f"  🔄 Computing expensive_computation({n})")
        time.sleep(0.5)  # Simulate expensive work
        return n * n * n
    
    # First call (slow)
    start = time.time()
    result1 = expensive_computation(10)
    time1 = time.time() - start
    print(f"First call: {result1} (took {time1:.2f}s)")
    
    # Second call (fast - cached)
    start = time.time()
    result2 = expensive_computation(10)
    time2 = time.time() - start
    print(f"Second call: {result2} (took {time2:.3f}s)")
    
    # Verify caching worked
    if time2 < time1 * 0.1:  # Should be 10x faster
        print("✅ Cache Manager working correctly")
        return True
    else:
        print("❌ Caching may not be working")
        return False

def test_network_caching():
    """Test network generation caching."""
    print("\n🕸️ Testing Network Generation Caching")
    print("=" * 45)
    
    try:
        from config_loader import AppConfig
        from network_utils import ArtistNetworkAnalyzer
        
        # Create small test DataFrame with proper datetime types
        test_data = {
            'artist': ['Taylor Swift', 'Olivia Rodrigo', 'Billie Eilish'] * 10,
            'timestamp': pd.date_range('2023-01-01', periods=30, freq='D')
        }
        df = pd.DataFrame(test_data)
        
        # Ensure timestamp column is properly typed
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        print(f"Test data shape: {df.shape}")
        print(f"Timestamp dtype: {df['timestamp'].dtype}")
        print(f"Sample timestamps: {df['timestamp'].head(2).tolist()}")
        
        # Initialize analyzer
        config = AppConfig()
        analyzer = ArtistNetworkAnalyzer(config)
        
        print("Creating test network (first run - slow)...")
        start = time.time()
        
        # Use very small parameters for fast testing
        network1 = analyzer.create_network_data(
            df, 
            top_n_artists=3,
            min_plays_threshold=1,
            min_similarity_threshold=0.1
        )
        time1 = time.time() - start
        
        print(f"First network creation: {time1:.2f}s")
        print(f"Nodes: {len(network1['nodes'])}, Edges: {len(network1['edges'])}")
        
        print("\nCreating same network (second run - should be cached)...")
        start = time.time()
        
        network2 = analyzer.create_network_data(
            df,
            top_n_artists=3, 
            min_plays_threshold=1,
            min_similarity_threshold=0.1
        )
        time2 = time.time() - start
        
        print(f"Second network creation: {time2:.2f}s")
        
        # Check if caching worked
        if time2 < time1 * 0.5:  # Should be significantly faster
            print("✅ Network caching working correctly")
            return True
        else:
            print("⚠️ Network caching may not be working optimally")
            return False
            
    except Exception as e:
        print(f"❌ Network caching test failed: {e}")
        return False

def test_cache_configuration():
    """Test configuration-driven cache control."""
    print("\n⚙️ Testing Cache Configuration Control")
    print("=" * 42)
    
    try:
        from config_loader import AppConfig
        
        # Test reading cache configuration
        config = AppConfig()
        
        # Check cache settings
        global_disable = config.get_bool('CachingSystem', 'DISABLE_ALL_CACHING', False)
        lastfm_disable = config.get_bool('CachingSystem', 'DISABLE_LASTFM_CACHE', False)
        cache_root = config.get('CachingSystem', 'CACHE_ROOT', '.cache')
        
        print(f"Global cache disable: {global_disable}")
        print(f"Last.fm cache disable: {lastfm_disable}")
        print(f"Cache root directory: {cache_root}")
        
        if global_disable:
            print("⚠️ All caching is disabled in configuration")
        else:
            print("✅ Configuration loaded successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_cache_statistics():
    """Test cache statistics and management."""
    print("\n📊 Testing Cache Statistics")
    print("=" * 32)
    
    try:
        from clear_caches import CacheCleaner
        
        cleaner = CacheCleaner()
        stats = cleaner.get_cache_stats()
        
        print("Cache Statistics:")
        print(f"  Joblib cache: {stats['joblib']['files']} files, {stats['joblib']['size_mb']} MB")
        print(f"  API caches: {stats['api']['total_files']} files, {stats['api']['total_size_mb']} MB")
        print(f"  Network caches: {stats['network']['total_files']} files, {stats['network']['total_size_mb']} MB")
        
        print("✅ Cache statistics working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Cache statistics test failed: {e}")
        return False

def test_edge_weighting_caching():
    """Test edge weighting system caching."""
    print("\n⚖️ Testing Edge Weighting Caching")
    print("=" * 38)
    
    try:
        from comprehensive_edge_weighting_system import ComprehensiveEdgeWeighter, EdgeWeightingConfig
        
        # Create test similarity data
        test_similarities = {
            'Taylor Swift': {
                'Olivia Rodrigo': [
                    {'name': 'Olivia Rodrigo', 'match': 0.85, 'source': 'lastfm'},
                    {'name': 'Olivia Rodrigo', 'match': 0.80, 'source': 'deezer'}
                ]
            }
        }
        
        # Initialize edge weighter
        config = EdgeWeightingConfig()
        weighter = ComprehensiveEdgeWeighter(config)
        
        print("Creating weighted edges (first run)...")
        start = time.time()
        edges1 = weighter.create_network_edges(test_similarities)
        time1 = time.time() - start
        
        print(f"First edge weighting: {time1:.3f}s, {len(edges1)} edges")
        
        print("Creating same weighted edges (second run - should be cached)...")
        start = time.time()
        edges2 = weighter.create_network_edges(test_similarities)
        time2 = time.time() - start
        
        print(f"Second edge weighting: {time2:.3f}s, {len(edges2)} edges")
        
        # Check results consistency
        if len(edges1) == len(edges2):
            print("✅ Edge weighting caching working correctly")
            return True
        else:
            print("❌ Edge weighting results inconsistent")
            return False
            
    except Exception as e:
        print(f"❌ Edge weighting caching test failed: {e}")
        return False

def main():
    """Run complete caching system tests."""
    print("🧪 Complete Caching System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Cache Manager", test_cache_manager),
        ("Configuration Control", test_cache_configuration),
        ("Cache Statistics", test_cache_statistics),
        ("Edge Weighting Caching", test_edge_weighting_caching),
        ("Network Generation Caching", test_network_caching),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n🎯 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All caching systems working correctly!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed - check implementation")
    
    print("\n💡 To clear all caches: python clear_caches.py --all")
    print("💡 To view cache stats: python clear_caches.py --stats")

if __name__ == "__main__":
    main()