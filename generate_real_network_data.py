#!/usr/bin/env python3
"""
Generate real network data from spotify_data.json using all_time configuration.
This replaces the hardcoded sample data with actual user data.
"""

import os
import sys
import json
from config_loader import AppConfig
from data_processor import clean_and_filter_data
from network_utils import ArtistNetworkAnalyzer, prepare_dataframe_for_network_analysis

def main():
    """Generate real network data for the web visualization."""
    print("🚀 Generating real network data from Spotify data...")
    
    # Load configuration
    config = AppConfig('configurations.txt')
    print("✅ Configuration loaded")
    
    # Load and process Spotify data 
    print("📊 Loading Spotify data...")
    try:
        df = clean_and_filter_data(config)
        if df is None or df.empty:
            print("❌ No data loaded from Spotify files")
            return False
            
        print(f"✅ Loaded {len(df)} records from Spotify data")
        
        # Developer sanity check: verify a specific, high-count artist is present
        ive_data = df[df['artist'].str.contains('IVE', case=False, na=False)]
        if not ive_data.empty:
            ive_plays = len(ive_data)
            print(f"🎯 Found IVE with {ive_plays} plays (should be around 6,143)")
        else:
            print("⚠️ IVE not found in dataset")
            
    except Exception as e:
        print(f"❌ Error loading Spotify data: {e}")
        return False
    
    # Prepare data for network analysis
    print("🔧 Preparing data for network analysis...")
    try:
        df_network = prepare_dataframe_for_network_analysis(df)
        print("✅ Data prepared for network analysis")
    except Exception as e:
        print(f"❌ Error preparing network data: {e}")
        return False
    
    # Initialize network analyzer
    print("🕸️ Initializing network analyzer...")
    try:
        analyzer = ArtistNetworkAnalyzer(config)
        print("✅ Network analyzer initialized")
    except Exception as e:
        print(f"❌ Error initializing analyzer: {e}")
        return False
    
    # Generate network
    print("🔗 Generating artist network...")
    try:
        # Use configuration settings for network generation
        network_config = config.get_network_visualization_config()
        top_n = network_config['top_n_artists']
        min_similarity = network_config['min_similarity_threshold']
        min_plays = network_config['min_plays_threshold']
        
        print(f"   - Top N artists: {top_n}")
        print(f"   - Min similarity: {min_similarity}")
        print(f"   - Min plays: {min_plays}")
        
        # Generate the network (this is the key step)
        network_data = analyzer.create_network_data(
            df_network, 
            top_n_artists=top_n,
            min_similarity_threshold=min_similarity,
            min_plays_threshold=min_plays
        )
        
        if network_data is None:
            print("❌ Failed to generate network data")
            return False
            
        print("✅ Network generated successfully")
        
        # The network_data is already a dict, we just need to convert to JSON string
        print("📄 Converting to JSON format...")
        json_data = json.dumps(network_data, ensure_ascii=False, indent=2)
        
        print("✅ JSON conversion successful")
        
    except Exception as e:
        print(f"❌ Error generating network: {e}")
        return False
    
    # Save to file that the web interface can load
    output_file = "static/artist_network_data.json"
    print(f"💾 Saving network data to {output_file}...")
    
    try:
        # Ensure the static directory exists
        os.makedirs("static", exist_ok=True)
        
        # Save the JSON data
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_data)
            
        print(f"✅ Network data saved to {output_file}")
        
        # Parse and display summary (use the in-memory data directly)
        nodes = network_data.get('nodes', [])
        links = network_data.get('links', network_data.get('edges', []))  # Check for both 'links' and 'edges'
        
        print(f"📊 Network summary:")
        print(f"   - Nodes: {len(nodes)}")
        print(f"   - Links: {len(links)}")
        
        # Check for IVE in the network data
        ive_node = next((node for node in nodes if 'ive' in node.get('id', '').lower()), None)
        if ive_node:
            play_count = ive_node.get('play_count', 0)
            print(f"🎯 IVE found in network with {play_count} plays")
            if play_count > 6000:
                print("✅ IVE play count looks correct!")
            else:
                print("⚠️ IVE play count seems low")
        else:
            print("⚠️ IVE not found in generated network")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving network data: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Success! Real network data generated.")
        print("Now the web visualization can load real data instead of sample data.")
    else:
        print("\n❌ Failed to generate network data.")
        sys.exit(1)