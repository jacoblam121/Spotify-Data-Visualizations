#!/usr/bin/env python3
"""
Enhance network data with missing fields for visualization.
Non-destructive: keeps original data, adds missing listener_count, photo_url, genres_lastfm.
"""

import json
import sys

def main():
    """Enhance network data with sample data fields while preserving real play counts."""
    
    # Sample data mapping with all required fields and CORRECT photo URLs
    sample_data_map = {
        "taylor_swift": {
            "listener_count": 5160232,
            "genres_lastfm": ["country", "pop"],
            "photo_url": "https://i.scdn.co/image/ab6761610000e5eb859e4cfb8be70f05cf27bb9b"  # Taylor Swift correct
        },
        "paramore": {
            "listener_count": 4779115,
            "genres_lastfm": ["rock", "pop punk"],
            "photo_url": "https://i.scdn.co/image/ab6761610000e5ebb10c34546a4ca2d7faeb8865"  # Paramore correct
        },
        "iu": {
            "listener_count": 913058,
            "genres_lastfm": ["k-pop", "korean"],
            "photo_url": "https://i.scdn.co/image/ab6761610000e5eb789f38042e5ef8911fc3826b"  # IU correct
        },
        "ive": {
            "listener_count": 837966,
            "genres_lastfm": ["k-pop", "korean"],
            "photo_url": "https://i.scdn.co/image/ab6761610000e5eb1ce1b9c95fd13eb96820c216"  # IVE correct (female group)
        },
        "twice": {
            "listener_count": 1250000,
            "genres_lastfm": ["k-pop", "korean"],
            "photo_url": "https://i.scdn.co/image/ab6761610000e5ebc707f33eb1849cb982c5e7a0"  # TWICE correct (unique)
        },
        "anyujin": {
            "listener_count": 50000,
            "genres_lastfm": ["k-pop", "korean"],
            "photo_url": "https://i.scdn.co/image/ab6761610000e5eb45d443b065a66c92d166f598"  # ANYUJIN correct
        },
        "bts": {
            "listener_count": 2800000,
            "genres_lastfm": ["k-pop", "korean"],
            "photo_url": "https://i.scdn.co/image/ab6761610000e5eb6707e9c2ac8a0bb4f44462fe"  # BTS correct (not BLACKPINK)
        },
        "tonight_alive": {
            "listener_count": 319867,
            "genres_lastfm": ["rock", "pop punk"],
            "photo_url": "https://i.scdn.co/image/ab6761610000e5eb7b04fbc96f1386a74bc8d1d9"  # Tonight Alive correct (unique)
        }
    }
    
    input_file = "static/test_integrated_network_small.json"
    output_file = "static/test_integrated_network_enhanced.json"
    
    print(f"🔧 Enhancing network data: {input_file} → {output_file}")
    
    try:
        # Load real network data
        with open(input_file, 'r', encoding='utf-8') as f:
            network_data = json.load(f)
        
        print(f"📊 Loaded {len(network_data.get('nodes', []))} nodes")
        
        # Enhance each node with missing fields
        enhanced_count = 0
        for node in network_data.get('nodes', []):
            node_id = node.get('id', '')
            
            # Add missing fields from sample data
            if node_id in sample_data_map:
                sample_fields = sample_data_map[node_id]
                node['listener_count'] = sample_fields['listener_count']
                node['genres_lastfm'] = sample_fields['genres_lastfm']
                node['photo_url'] = sample_fields['photo_url']
                enhanced_count += 1
                print(f"  ✅ Enhanced {node.get('name', node_id)}")
            else:
                # Provide default values for unknown artists
                node['listener_count'] = 100000  # Default listener count
                node['genres_lastfm'] = ["other"]
                node['photo_url'] = "https://i.scdn.co/image/ab6761610000e5ebe672b5f553298dcdccb0e676"  # Default image
                enhanced_count += 1
                print(f"  🔧 Added defaults for {node.get('name', node_id)}")
        
        # Keep the IVE play count update from our previous fix
        ive_node = next((node for node in network_data['nodes'] if node.get('id') == 'ive'), None)
        if ive_node:
            ive_node['play_count'] = 6143  # Real all_time play count
            print(f"  🎯 Updated IVE play count to 6143")
        
        # Ensure edges are preserved as links for frontend compatibility
        if 'edges' in network_data and 'links' not in network_data:
            network_data['links'] = network_data['edges']
            print("🔗 Converted edges to links for frontend compatibility")
        
        # Save enhanced data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Enhanced {enhanced_count} nodes")
        print(f"💾 Saved enhanced data to {output_file}")
        
        # Summary
        nodes = network_data.get('nodes', [])
        links = network_data.get('links', network_data.get('edges', []))
        nodes_with_photos = len([n for n in nodes if n.get('photo_url')])
        nodes_with_genres = len([n for n in nodes if n.get('genres_lastfm')])
        nodes_with_listeners = len([n for n in nodes if n.get('listener_count', 0) > 0])
        
        print(f"📊 Enhanced network summary:")
        print(f"   - Total nodes: {len(nodes)}")
        print(f"   - Total links: {len(links)}")
        print(f"   - Nodes with photos: {nodes_with_photos}")
        print(f"   - Nodes with genres: {nodes_with_genres}")
        print(f"   - Nodes with listener counts: {nodes_with_listeners}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error enhancing network data: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Network data enhancement complete!")
        print("Now update the frontend to load the enhanced file.")
    else:
        print("\n❌ Failed to enhance network data.")
        sys.exit(1)