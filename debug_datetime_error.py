#!/usr/bin/env python3
"""Debug the datetime error in network caching."""

import traceback
import pandas as pd

def test_basic_caching():
    """Test basic network caching to isolate the datetime error."""
    try:
        from config_loader import AppConfig
        from network_utils import ArtistNetworkAnalyzer
        
        print("Creating test DataFrame...")
        # Simple test data
        test_data = {
            'artist': ['A', 'B', 'C'] * 5,
            'timestamp': pd.date_range('2023-01-01', periods=15, freq='D')
        }
        df = pd.DataFrame(test_data)
        
        print(f"DataFrame dtypes:")
        print(df.dtypes)
        print(f"Sample data:")
        print(df.head(3))
        
        print("\nTesting data hash creation...")
        config = AppConfig()
        analyzer = ArtistNetworkAnalyzer(config)
        
        # Test the hash creation directly
        hash_result = analyzer._create_data_hash(df)
        print(f"Data hash: {hash_result}")
        
        print("\nCreating network data...")
        network_data = analyzer.create_network_data(
            df,
            top_n_artists=2,
            min_plays_threshold=1,
            min_similarity_threshold=0.1
        )
        
        print(f"Network created successfully!")
        print(f"Nodes: {len(network_data['nodes'])}")
        print(f"Edges: {len(network_data['edges'])}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        
        # Try to identify where the datetime error occurs
        print(f"\nError type: {type(e)}")
        print(f"Error args: {e.args}")

if __name__ == "__main__":
    test_basic_caching()