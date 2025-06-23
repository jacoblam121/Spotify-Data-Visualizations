#!/usr/bin/env python3
"""
Enhanced Network Data Generator with Spotify API Integration

This script enhances network data by automatically fetching artist photos
and metadata from Spotify API using the existing album_art_utils.py infrastructure.
It replaces the manual photo mapping with automatic API calls while being
completely non-destructive to the bar chart race functionality.
"""

import json
import sys
import os

# Import the existing album_art_utils with our new function
import album_art_utils

def main():
    """Enhance network data with automatic Spotify API integration."""
    
    input_file = "static/test_integrated_network_small.json"
    output_file = "static/test_integrated_network_spotify.json"
    
    print(f"🚀 Enhancing network data with Spotify API integration")
    print(f"📂 Input: {input_file}")
    print(f"📂 Output: {output_file}")
    
    try:
        # Load real network data
        with open(input_file, 'r', encoding='utf-8') as f:
            network_data = json.load(f)
        
        print(f"📊 Loaded {len(network_data.get('nodes', []))} nodes")
        
        # Initialize album_art_utils configuration if needed
        from config_loader import AppConfig
        config = AppConfig()
        album_art_utils.initialize_from_config(config)
        
        # Enhance each node with Spotify API data
        enhanced_count = 0
        failed_count = 0
        
        for node in network_data.get('nodes', []):
            artist_name = node.get('name', '')
            node_id = node.get('id', '')
            
            print(f"\n🎵 Processing: {artist_name}")
            
            # Get artist info from Spotify API
            artist_info = album_art_utils.get_spotify_artist_info(artist_name)
            if artist_info:
                # Add Spotify metadata
                node['listener_count'] = artist_info.get('followers', 100000)
                node['genres_lastfm'] = artist_info.get('genres', ['other'])
                node['spotify_artist_id'] = artist_info.get('spotify_artist_id')
                node['popularity'] = artist_info.get('popularity', 0)
                
                # Get local cached photo path
                photo_path = album_art_utils.get_artist_photo_path(artist_name)
                if photo_path:
                    # Convert to static URL for frontend
                    node['photo_url'] = f"/static/{photo_path}"
                    print(f"  ✅ Photo cached: {photo_path}")
                else:
                    node['photo_url'] = None
                    print(f"  ⚠️  No photo available")
                
                enhanced_count += 1
                print(f"  ✅ Enhanced with Spotify data")
                print(f"     Genres: {node['genres_lastfm']}")
                print(f"     Followers: {node['listener_count']:,}")
                print(f"     Popularity: {node['popularity']}")
                
            else:
                # Provide default values for unknown artists
                node['listener_count'] = 50000  # Conservative default
                node['genres_lastfm'] = ["other"]
                node['photo_url'] = None
                node['spotify_artist_id'] = None
                node['popularity'] = 0
                failed_count += 1
                print(f"  ❌ No Spotify data found - using defaults")
        
        # Ensure edges are preserved as links for frontend compatibility
        if 'edges' in network_data and 'links' not in network_data:
            network_data['links'] = network_data['edges']
            print("🔗 Converted edges to links for frontend compatibility")
        
        # Add metadata about enhancement
        if 'metadata' not in network_data:
            network_data['metadata'] = {}
        
        network_data['metadata']['enhanced_with_spotify'] = True
        network_data['metadata']['spotify_enhancement_timestamp'] = album_art_utils.time.time()
        network_data['metadata']['nodes_enhanced'] = enhanced_count
        network_data['metadata']['nodes_failed'] = failed_count
        
        # Save enhanced data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Enhancement complete!")
        print(f"   📊 Nodes enhanced: {enhanced_count}")
        print(f"   ❌ Nodes failed: {failed_count}")
        print(f"   💾 Saved to: {output_file}")
        
        # Summary statistics
        nodes = network_data.get('nodes', [])
        links = network_data.get('links', network_data.get('edges', []))
        nodes_with_photos = len([n for n in nodes if n.get('photo_url')])
        nodes_with_spotify_data = len([n for n in nodes if n.get('spotify_artist_id')])
        
        print(f"\n📊 Enhanced network summary:")
        print(f"   - Total nodes: {len(nodes)}")
        print(f"   - Total links: {len(links)}")
        print(f"   - Nodes with photos: {nodes_with_photos}")
        print(f"   - Nodes with Spotify data: {nodes_with_spotify_data}")
        print(f"   - Artist photos cached in: artist_art_cache/")
        
        return True
        
    except Exception as e:
        print(f"❌ Error enhancing network data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Spotify API integration complete!")
        print("📱 Artist photos are now cached locally and served through Flask")
        print("🌐 No more CORS issues - all images served from /static/artist_art_cache/")
        print("🔧 The bar chart race functionality remains completely unaffected")
    else:
        print("\n❌ Failed to enhance network data with Spotify API")
        sys.exit(1)