#!/usr/bin/env python3
"""
Manual Artist Connections
=========================
Add obvious connections that Last.fm similarity data misses
"""

# Manual connections for obvious relationships
MANUAL_CONNECTIONS = {
    # Band members to their bands
    "anyujin": [
        ("IVE", 1.0, "band_member"),
        ("Ahn Yujin", 1.0, "same_person")
    ],
    "ahn yujin": [
        ("IVE", 1.0, "band_member"),
        ("ANYUJIN", 1.0, "same_person")
    ],
    
    # K-pop interconnections (based on music knowledge)
    "iu": [
        ("TWICE", 0.3, "kpop_genre"),
        ("IVE", 0.25, "kpop_genre")
    ],
    
    "twice": [
        ("IU", 0.3, "kpop_genre"),
        ("IVE", 0.4, "kpop_genre"),
        ("BLACKPINK", 0.5, "girl_group")
    ],
    
    "ive": [
        ("TWICE", 0.4, "girl_group"),
        ("BLACKPINK", 0.35, "girl_group"),
        ("IU", 0.25, "kpop_genre"),
        ("ANYUJIN", 1.0, "member"),
        ("Ahn Yujin", 1.0, "member")
    ],
    
    # Rock connections
    "paramore": [
        ("Tonight Alive", 0.4, "female_rock")  # Boost existing connection
    ],
    
    "tonight alive": [
        ("Paramore", 0.4, "female_rock")  # Boost existing connection
    ]
}

def get_manual_connections(artist_name: str) -> list:
    """Get manual connections for an artist"""
    artist_key = artist_name.lower().strip()
    return MANUAL_CONNECTIONS.get(artist_key, [])

def add_manual_connections_to_network(network_data: dict, min_threshold: float = 0.2) -> dict:
    """Add manual connections to existing network data"""
    
    if not network_data.get('nodes') or not network_data.get('edges'):
        return network_data
    
    # Create lookup for existing nodes
    node_lookup = {node['name'].lower(): node for node in network_data['nodes']}
    node_ids = {node['name'].lower(): node['id'] for node in network_data['nodes']}
    
    # Track existing edges to avoid duplicates
    existing_edges = set()
    for edge in network_data.get('edges', []):
        source = edge.get('source', '').lower()
        target = edge.get('target', '').lower()
        existing_edges.add((source, target))
        existing_edges.add((target, source))  # bidirectional
    
    manual_edges_added = 0
    
    # Add manual connections
    for node in network_data['nodes']:
        artist_name = node['name']
        artist_id = node['id']
        
        manual_connections = get_manual_connections(artist_name)
        
        for target_name, similarity, relationship_type in manual_connections:
            if similarity < min_threshold:
                continue
            
            # Find target in our network
            target_key = target_name.lower()
            if target_key in node_lookup:
                target_id = node_ids[target_key]
                
                # Check if edge already exists
                edge_key = (artist_id.lower(), target_id.lower())
                if edge_key not in existing_edges:
                    
                    # Add the edge
                    new_edge = {
                        'source': artist_id,
                        'target': target_id,
                        'weight': similarity,
                        'lastfm_similarity': 0.0,  # Manual, not from Last.fm
                        'manual_similarity': similarity,
                        'relationship_type': f'manual_{relationship_type}',
                        'manual_connection': True
                    }
                    
                    network_data['edges'].append(new_edge)
                    existing_edges.add(edge_key)
                    existing_edges.add((target_id.lower(), artist_id.lower()))
                    manual_edges_added += 1
                    
                    print(f"➕ Added manual connection: {artist_name} ↔ {target_name} ({similarity:.2f}, {relationship_type})")
    
    # Update metadata
    if 'metadata' in network_data:
        network_data['metadata']['manual_edges_added'] = manual_edges_added
        network_data['metadata']['total_edges_after_manual'] = len(network_data['edges'])
        
        if 'edge_types' not in network_data['metadata']:
            network_data['metadata']['edge_types'] = {}
        network_data['metadata']['edge_types']['manual_connections'] = manual_edges_added
    
    print(f"✅ Added {manual_edges_added} manual connections")
    
    return network_data

if __name__ == "__main__":
    """Test manual connections"""
    print("🔗 Manual Artist Connections")
    print("=" * 30)
    
    test_artists = ["ANYUJIN", "IVE", "TWICE", "IU", "Paramore"]
    
    for artist in test_artists:
        connections = get_manual_connections(artist)
        if connections:
            print(f"\n🎵 {artist}:")
            for target, similarity, relationship in connections:
                print(f"   → {target} ({similarity:.2f}, {relationship})")
        else:
            print(f"\n🎵 {artist}: No manual connections")
    
    print(f"\n💡 Use add_manual_connections_to_network() to enhance your network data")