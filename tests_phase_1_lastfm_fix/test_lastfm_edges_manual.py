#!/usr/bin/env python3
"""
Manual Test for Last.fm Similarity Edges - Phase 1
===================================================

This script allows you to manually test the Last.fm integration fix.
Run this to verify that artist similarity edges are being created properly.

Usage:
    python test_lastfm_edges_manual.py [num_artists] [similarity_threshold]

Examples:
    python test_lastfm_edges_manual.py 5 0.3     # 5 artists, 0.3 similarity threshold
    python test_lastfm_edges_manual.py 10 0.5    # 10 artists, 0.5 similarity threshold
    python test_lastfm_edges_manual.py           # Default: 8 artists, 0.4 threshold
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from network_utils import ArtistNetworkAnalyzer, prepare_dataframe_for_network_analysis
from data_processor import clean_and_filter_data
from config_loader import AppConfig


def test_lastfm_edges(num_artists=8, similarity_threshold=0.4):
    """
    Test Last.fm similarity edge creation with your actual listening data.
    
    Args:
        num_artists: Number of top artists to include in network
        similarity_threshold: Minimum similarity score to create edges (0.0-1.0)
    """
    print("🧪 Last.fm Similarity Edges - Manual Test")
    print("=" * 55)
    print(f"Parameters: {num_artists} artists, {similarity_threshold:.1f} similarity threshold")
    print()
    
    try:
        # Change to parent directory so relative paths work correctly
        original_cwd = Path.cwd()
        project_root = Path(__file__).parent.parent
        import os
        os.chdir(project_root)
        
        # Load configuration
        config = AppConfig("configurations.txt")
        
        # Check data source
        data_source = config.get('DataSource', 'SOURCE')
        if data_source != 'spotify':
            print("❌ Error: This test requires Spotify data source")
            print("   Update SOURCE = spotify in configurations.txt")
            return False
        
        print("📁 Loading your listening data...")
        
        # Load and prepare data
        df = clean_and_filter_data(config)
        df = prepare_dataframe_for_network_analysis(df)
        
        print(f"✅ Loaded {len(df):,} plays from {df['artist'].nunique()} unique artists")
        
        timeframe = f"{df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}"
        print(f"📅 Timeframe: {timeframe}")
        print()
        
        # Initialize network analyzer
        print("🔧 Initializing network analyzer...")
        analyzer = ArtistNetworkAnalyzer(config)
        
        # Get top artists preview
        top_artists = df.groupby('artist').size().sort_values(ascending=False).head(num_artists)
        print(f"🎵 Top {num_artists} artists in your data:")
        for i, (artist, plays) in enumerate(top_artists.items(), 1):
            print(f"  {i:2d}. {artist} ({plays:,} plays)")
        print()
        
        # Generate network
        print("🕸️  Generating artist similarity network...")
        print("   (This may take 1-2 minutes due to API calls)")
        
        network_data = analyzer.create_network_data(
            df,
            top_n_artists=num_artists,
            min_plays_threshold=5,
            min_similarity_threshold=similarity_threshold
        )
        
        # Results
        print()
        print("📊 Network Generation Results:")
        print(f"   Nodes (artists): {len(network_data['nodes'])}")
        print(f"   Edges (similarities): {len(network_data['edges'])}")
        print()
        
        if network_data['edges']:
            print("🔗 Artist Similarity Relationships:")
            for i, edge in enumerate(network_data['edges'], 1):
                similarity_pct = edge['weight'] * 100
                print(f"   {i:2d}. {edge['source']} ↔ {edge['target']}")
                print(f"       Similarity: {edge['weight']:.3f} ({similarity_pct:.1f}%)")
            print()
            
            # Save the network
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"manual_test_network_{num_artists}artists_{timestamp}.json"
            filepath = Path(__file__).parent / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(network_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Network saved: {filename}")
            print()
            
            # Success summary
            print("✅ SUCCESS: Last.fm similarity edges are working!")
            print(f"   - API calls completed successfully")
            print(f"   - {len(network_data['edges'])} similarity relationships found")
            print(f"   - Network data saved for visualization")
            
            return True
            
        else:
            print("❌ NO EDGES CREATED")
            print("   Possible reasons:")
            print(f"   - Similarity threshold too high ({similarity_threshold:.1f})")
            print("   - Artists don't have similar artists in Last.fm")
            print("   - Last.fm API issue")
            print()
            print("💡 Try running with lower threshold:")
            print(f"   python {Path(__file__).name} {num_artists} 0.2")
            
            return False
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        print("💡 Troubleshooting:")
        print("   1. Check that configurations.txt exists")
        print("   2. Verify Spotify data file exists")
        print("   3. Ensure Last.fm API credentials are set")
        return False
    
    finally:
        # Restore original working directory
        try:
            os.chdir(original_cwd)
        except:
            pass


def main():
    """Main function with command line argument parsing."""
    # Default parameters
    num_artists = 8
    similarity_threshold = 0.4
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        try:
            num_artists = int(sys.argv[1])
            if num_artists < 3 or num_artists > 50:
                print("❌ Number of artists must be between 3 and 50")
                return
        except ValueError:
            print("❌ Invalid number of artists. Must be an integer.")
            return
    
    if len(sys.argv) > 2:
        try:
            similarity_threshold = float(sys.argv[2])
            if similarity_threshold < 0.0 or similarity_threshold > 1.0:
                print("❌ Similarity threshold must be between 0.0 and 1.0")
                return
        except ValueError:
            print("❌ Invalid similarity threshold. Must be a number between 0.0 and 1.0")
            return
    
    # Run the test
    success = test_lastfm_edges(num_artists, similarity_threshold)
    
    print()
    if success:
        print("🎉 Test completed successfully!")
        print("   Your Last.fm integration is working correctly.")
    else:
        print("❌ Test failed. Check the output above for details.")


if __name__ == "__main__":
    main()