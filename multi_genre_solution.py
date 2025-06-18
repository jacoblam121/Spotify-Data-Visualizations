#!/usr/bin/env python3
"""
Multi-Genre Visualization Solution
=================================
Handles artists that span multiple genres using multiple approaches.
"""

from typing import Dict, List, Tuple
import json

def generate_d3_multi_genre_nodes(network_data: Dict, max_secondary_genres: int = 2, enable_secondary_genres: bool = True) -> Dict:
    """
    Enhance network data with multi-genre node styling information.
    
    Args:
        network_data: Standard network data dict
        max_secondary_genres: Maximum secondary genres to show per node
        enable_secondary_genres: Whether to include secondary genre support
        
    Returns:
        Enhanced network data with optional multi-genre styling
    """
    enhanced_nodes = []
    
    for node in network_data.get('nodes', []):
        # Get multi-genre information (if available)
        all_genres = node.get('all_genres', [])
        primary_genre = node.get('cluster_genre', 'other')
        
        # Create enhanced node with multi-genre styling options
        enhanced_node = node.copy()
        
        # Approach 1: Multi-stroke borders (primary implementation)
        # Respect configuration setting for secondary genres
        if enable_secondary_genres:
            secondary_genres = [g for g in all_genres[:max_secondary_genres+1] if g != primary_genre][:max_secondary_genres]
        else:
            secondary_genres = []  # Clean single-genre approach
        
        enhanced_node.update({
            'primary_genre': primary_genre,
            'secondary_genres': secondary_genres[:max_secondary_genres],
            'genre_count': len([primary_genre] + secondary_genres),
            'is_multi_genre': len(secondary_genres) > 0,
            
            # Styling information for D3.js
            'styling': {
                'primary_color': get_genre_color(primary_genre),
                'secondary_colors': [get_genre_color(g) for g in secondary_genres],
                'border_style': 'multi' if len(secondary_genres) > 0 else 'single',
                'border_width': 2 + len(secondary_genres),  # Thicker border for multi-genre
            },
            
            # Force layout positioning hints
            'gravity_targets': [primary_genre] + secondary_genres,
            'gravity_weights': [1.0] + [0.3] * len(secondary_genres)  # Primary genre has strongest pull
        })
        
        enhanced_nodes.append(enhanced_node)
    
    # Update network data
    enhanced_network = network_data.copy()
    enhanced_network['nodes'] = enhanced_nodes
    
    # Add genre gravity centers for force layout
    enhanced_network['genre_centers'] = generate_genre_centers()
    
    return enhanced_network

def generate_genre_centers(canvas_width: int = 1200, canvas_height: int = 800) -> Dict:
    """
    Generate gravity center positions for each genre in the force layout.
    
    Args:
        canvas_width: D3.js canvas width
        canvas_height: D3.js canvas height
        
    Returns:
        Dict mapping genre -> {x, y} coordinates
    """
    from simplified_genre_colors import GENRE_COLORS
    
    # Arrange genres in a circular pattern for natural clustering
    import math
    
    core_genres = ['pop', 'rock', 'metal', 'electronic', 'asian', 'latin', 
                   'country', 'r&b', 'hip-hop', 'indie', 'world', 'classical']
    
    center_x = canvas_width / 2
    center_y = canvas_height / 2
    radius = min(canvas_width, canvas_height) * 0.3  # 30% of canvas size
    
    genre_centers = {}
    
    for i, genre in enumerate(core_genres):
        angle = (2 * math.pi * i) / len(core_genres)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        genre_centers[genre] = {
            'x': x,
            'y': y,
            'color': GENRE_COLORS.get(genre, '#C0C0C0')
        }
    
    # Add fallback center
    genre_centers['other'] = {
        'x': center_x,
        'y': center_y,
        'color': GENRE_COLORS.get('other', '#C0C0C0')
    }
    
    return genre_centers

def generate_d3_force_config() -> Dict:
    """
    Generate D3.js force simulation configuration for multi-genre layout.
    
    Returns:
        Configuration object for d3-force
    """
    return {
        'forces': {
            'link': {
                'strength': 0.1,
                'distance': 50
            },
            'charge': {
                'strength': -100,
                'distance_max': 200
            },
            'center': {
                'strength': 0.05
            },
            'collision': {
                'radius': 15,
                'strength': 0.7
            },
            'genre_gravity': {
                'strength': 0.02,  # Weak pull to avoid dominating link forces
                'primary_multiplier': 1.0,
                'secondary_multiplier': 0.3
            }
        },
        'alpha': {
            'initial': 1.0,
            'decay': 0.01,
            'min': 0.001
        }
    }

def generate_d3_styling_css() -> str:
    """Generate CSS for multi-genre node styling."""
    return """
    /* Multi-Genre Node Styling */
    .node {
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .node.single-genre {
        stroke: #ffffff;
        stroke-width: 1.5px;
    }
    
    .node.multi-genre {
        stroke: #ffffff;
        stroke-width: 2px;
        filter: drop-shadow(0 0 3px rgba(255,255,255,0.3));
    }
    
    .node:hover {
        stroke: #ffff00;
        stroke-width: 3px;
        filter: drop-shadow(0 0 8px rgba(255,255,0,0.6));
    }
    
    /* Multi-stroke border effect (achieved with nested circles) */
    .node-border-1 {
        stroke-width: 6px;
        opacity: 0.8;
    }
    
    .node-border-2 {
        stroke-width: 4px;
        opacity: 0.6;
    }
    
    .node-core {
        stroke-width: 2px;
        opacity: 1.0;
    }
    
    /* Genre gravity centers (invisible guides) */
    .genre-center {
        fill: none;
        stroke: #333;
        stroke-width: 1px;
        stroke-dasharray: 2,2;
        opacity: 0.2;
    }
    
    /* Legend styling */
    .legend-multi-genre {
        position: absolute;
        bottom: 20px;
        left: 20px;
        background: rgba(0,0,0,0.8);
        border: 1px solid #fff;
        padding: 10px;
        border-radius: 5px;
        color: #fff;
        font-size: 12px;
    }
    
    .legend-example {
        display: inline-block;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        margin-right: 5px;
        vertical-align: middle;
    }
    """

def get_genre_color(genre: str) -> str:
    """Get color for genre (imported from simplified_genre_colors)."""
    from simplified_genre_colors import get_genre_color as get_color
    return get_color(genre)

def test_multi_genre_solution():
    """Test the multi-genre visualization solution."""
    print("🎨 Testing Multi-Genre Visualization Solution")
    print("=" * 44)
    
    # Mock network data
    test_network = {
        'nodes': [
            {
                'id': 'luna',
                'name': '*Luna',
                'cluster_genre': 'electronic',
                'all_genres': ['electronic', 'asian', 'k-pop']
            },
            {
                'id': 'paramore',
                'name': 'Paramore', 
                'cluster_genre': 'rock',
                'all_genres': ['rock', 'pop', 'alternative']
            },
            {
                'id': 'taylor_swift',
                'name': 'Taylor Swift',
                'cluster_genre': 'pop',
                'all_genres': ['pop']  # Single genre
            }
        ],
        'edges': []
    }
    
    print("🧪 Testing multi-genre node enhancement...")
    enhanced_network = generate_d3_multi_genre_nodes(test_network)
    
    for node in enhanced_network['nodes']:
        print(f"\n🎯 {node['name']}:")
        print(f"   Primary: {node['primary_genre']} ({node['styling']['primary_color']})")
        print(f"   Secondary: {node['secondary_genres']}")
        print(f"   Multi-genre: {node['is_multi_genre']}")
        print(f"   Border style: {node['styling']['border_style']}")
        print(f"   Gravity targets: {node['gravity_targets']}")
    
    print(f"\n📍 Genre Centers Generated:")
    centers = enhanced_network['genre_centers']
    for genre, pos in list(centers.items())[:5]:  # Show first 5
        print(f"   {genre}: ({pos['x']:.0f}, {pos['y']:.0f}) - {pos['color']}")
    
    print(f"\n⚙️ Force Configuration:")
    force_config = generate_d3_force_config()
    print(f"   Genre gravity strength: {force_config['forces']['genre_gravity']['strength']}")
    print(f"   Primary vs secondary: {force_config['forces']['genre_gravity']['primary_multiplier']} vs {force_config['forces']['genre_gravity']['secondary_multiplier']}")
    
    print(f"\n✅ Multi-genre solution ready for D3.js implementation!")

if __name__ == "__main__":
    test_multi_genre_solution()