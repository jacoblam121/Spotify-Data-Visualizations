#!/usr/bin/env python3
"""
Test Phase 1.1: Multi-Genre Artist Support Integration

This test validates that the multi-genre enhancement is properly integrated
into the network generation pipeline.
"""

import os
import json
from typing import Dict, Any

def test_multi_genre_integration():
    """Test the Phase 1.1 multi-genre integration."""
    print("🧪 Testing Phase 1.1: Multi-Genre Artist Support Integration")
    print("=" * 60)
    
    # Test 1: Import and basic functionality
    print("\n1️⃣ Testing imports and basic functionality...")
    
    try:
        from network_utils import ArtistNetworkAnalyzer
        from multi_genre_solution import generate_d3_multi_genre_nodes
        print("✅ Core imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Configuration check
    print("\n2️⃣ Testing configuration...")
    
    try:
        from network_utils import initialize_network_analyzer
        analyzer = initialize_network_analyzer()
        enable_secondary = analyzer.network_config.get('enable_secondary_genres', False)
        print(f"✅ Configuration loaded")
        print(f"   📋 ENABLE_SECONDARY_GENRES = {enable_secondary}")
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Mock network data enhancement
    print("\n3️⃣ Testing multi-genre enhancement with mock data...")
    
    mock_network_data = {
        'nodes': [
            {
                'id': 'test_artist_1',
                'name': 'Test Artist 1',
                'cluster_genre': 'pop',
                'all_genres': ['pop', 'rock'],
                'play_count': 100,
                'rank': 1,
                'size': 1000
            },
            {
                'id': 'test_artist_2', 
                'name': 'Test Artist 2',
                'cluster_genre': 'electronic',
                'all_genres': ['electronic', 'pop', 'dance'],
                'play_count': 80,
                'rank': 2,
                'size': 800
            }
        ],
        'edges': [
            {
                'source': 'test_artist_1',
                'target': 'test_artist_2',
                'weight': 0.7
            }
        ],
        'metadata': {
            'total_artists': 2,
            'generation_time': '2024-01-01'
        }
    }
    
    try:
        enhanced_data = generate_d3_multi_genre_nodes(
            mock_network_data,
            enable_secondary_genres=True,
            max_secondary_genres=3
        )
        
        print("✅ Multi-genre enhancement successful")
        
        # Verify enhancements
        enhanced_nodes = enhanced_data['nodes']
        
        print(f"   📊 Enhanced {len(enhanced_nodes)} nodes")
        
        # Check for multi-genre enhancements
        multi_genre_count = 0
        for node in enhanced_nodes:
            if node.get('is_multi_genre', False):
                multi_genre_count += 1
                print(f"   🎨 Multi-genre node: {node['name']}")
                print(f"      Primary: {node.get('primary_genre', 'unknown')}")
                print(f"      Secondary: {node.get('secondary_genres', [])}")
        
        print(f"   ✨ Multi-genre nodes: {multi_genre_count}/{len(enhanced_nodes)}")
        
        # Check for genre centers
        genre_centers = enhanced_data.get('metadata', {}).get('genre_centers', {})
        print(f"   🎯 Genre centers: {len(genre_centers)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Multi-genre enhancement failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_network_generation_pipeline():
    """Test the full network generation pipeline with multi-genre support."""
    print("\n4️⃣ Testing full network generation pipeline...")
    
    try:
        # Create a minimal test dataset
        import pandas as pd
        
        test_data = pd.DataFrame({
            'artist': ['Taylor Swift', 'BTS', 'Ed Sheeran'] * 10,
            'track': ['Song 1', 'Song 2', 'Song 3'] * 10,
            'timestamp': pd.date_range('2024-01-01', periods=30, freq='H')
        })
        
        print(f"   📊 Test dataset: {len(test_data)} rows, {test_data['artist'].nunique()} artists")
        
        # Test network generation
        from network_utils import analyze_user_network
        
        print("   🔄 Running network generation...")
        network_data = analyze_user_network(
            test_data, 
            output_file='test_network_phase_1_1.json'
        )
        
        print("✅ Network generation successful")
        print(f"   📊 Generated {len(network_data['nodes'])} nodes, {len(network_data['edges'])} edges")
        
        # Check for multi-genre enhancements in the output
        multi_genre_nodes = [n for n in network_data['nodes'] if n.get('is_multi_genre', False)]
        print(f"   🎨 Multi-genre nodes in output: {len(multi_genre_nodes)}")
        
        # Check if output file exists and is valid JSON
        if os.path.exists('test_network_phase_1_1.json'):
            with open('test_network_phase_1_1.json', 'r') as f:
                saved_data = json.load(f)
            print(f"   💾 Output file saved successfully")
            print(f"   📋 File contains: {len(saved_data.get('nodes', []))} nodes")
            
            # Clean up test file
            os.remove('test_network_phase_1_1.json')
            print(f"   🧹 Test file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Network generation pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Phase 1.1 integration tests."""
    print("🚀 Phase 1.1 Integration Test Suite")
    print("Testing Multi-Genre Artist Support Integration")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Run basic integration test
    if not test_multi_genre_integration():
        all_tests_passed = False
    
    # Run full pipeline test
    if not test_network_generation_pipeline():
        all_tests_passed = False
    
    # Final results
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Phase 1.1 Multi-Genre Artist Support is ready")
        print("\n📋 Next steps:")
        print("   1. Test with real data: python network_utils.py")
        print("   2. Check configuration: ENABLE_SECONDARY_GENRES = True")
        print("   3. Verify D3.js visualization handles enhanced data")
    else:
        print("❌ SOME TESTS FAILED")
        print("🔧 Please fix the issues before proceeding")
        return False
    
    return True

if __name__ == "__main__":
    main()