#!/usr/bin/env python3
"""
Genre Color Scheme for D3.js Network Visualization
=================================================
Vivid colors optimized for black background visualization.
"""

# Vivid genre colors optimized for black backgrounds with accessibility
GENRE_COLORS = {
    # Primary genres - maximum contrast and distinctiveness
    'pop': '#FF1493',           # Deep Pink - vibrant pop
    'rock': '#FF4500',          # Orange Red - fiery rock  
    'k-pop': '#00FFFF',         # Cyan - modern K-pop
    'j-pop': '#FFB6C1',         # Light Pink - softer J-pop (distinct from pop)
    'hip-hop': '#FFD700',       # Gold - prestigious hip-hop
    'electronic': '#00FF7F',    # Spring Green - electric (distinct from lime)
    'r&b': '#9370DB',           # Medium Purple - soulful R&B
    'metal': '#DC143C',         # Crimson - intense metal
    
    # Secondary genres - maximum separation from primaries
    'indie': '#ADFF2F',         # Green Yellow - alternative indie
    'alternative': '#FF6347',   # Tomato - edgy alternative  
    'country': '#F0E68C',       # Khaki - earthy country
    'folk': '#98FB98',          # Pale Green - organic folk
    'jazz': '#4169E1',          # Royal Blue - sophisticated jazz
    'classical': '#DDA0DD',     # Plum - refined classical
    'reggae': '#32CD32',        # Lime Green - vibrant reggae
    'punk': '#FF0000',          # Pure Red - aggressive punk
    
    # Specialty/Other - neutral tones
    'other': '#C0C0C0',         # Silver - neutral unclassified
    'unknown': '#808080'        # Gray - fallback
}

# Colorblind-friendly alternatives (optional)
COLORBLIND_SAFE_COLORS = {
    'pop': '#E31A1C',           # Red
    'rock': '#FF7F00',          # Orange  
    'k-pop': '#1F78B4',         # Blue
    'j-pop': '#B2DF8A',         # Light Green
    'hip-hop': '#FDBF6F',       # Light Orange
    'electronic': '#33A02C',    # Green
    'r&b': '#CAB2D6',           # Light Purple
    'metal': '#FB9A99',         # Light Red
    'other': '#C0C0C0',         # Silver
    'unknown': '#808080'        # Gray
}

# Color intensity levels for different confidence/importance
COLOR_VARIANTS = {
    'high': 1.0,      # Full intensity for primary nodes
    'medium': 0.8,    # Slightly dimmed for secondary nodes  
    'low': 0.6        # More dimmed for low-confidence nodes
}

# D3.js compatible color scale function
def get_d3_color_scale():
    """Generate D3.js color scale definition."""
    return {
        'type': 'ordinal',
        'domain': list(GENRE_COLORS.keys()),
        'range': list(GENRE_COLORS.values())
    }

def get_genre_color(genre: str, intensity: str = 'high', colorblind_safe: bool = False) -> str:
    """
    Get color for a specific genre with optional intensity adjustment.
    
    Args:
        genre: Genre name (e.g., 'k-pop', 'rock')
        intensity: Color intensity ('high', 'medium', 'low')
        colorblind_safe: Use colorblind-friendly palette
        
    Returns:
        Hex color code
    """
    color_palette = COLORBLIND_SAFE_COLORS if colorblind_safe else GENRE_COLORS
    base_color = color_palette.get(genre.lower(), color_palette.get('other', '#C0C0C0'))
    
    if intensity == 'high':
        return base_color
    
    # Convert hex to RGB for intensity adjustment
    hex_color = base_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Apply intensity multiplier
    multiplier = COLOR_VARIANTS[intensity]
    adjusted_rgb = tuple(int(c * multiplier) for c in rgb)
    
    # Convert back to hex
    return f"#{adjusted_rgb[0]:02x}{adjusted_rgb[1]:02x}{adjusted_rgb[2]:02x}"

def generate_genre_legend():
    """Generate genre legend data for D3.js."""
    return [
        {
            'genre': genre,
            'color': color,
            'description': get_genre_description(genre)
        }
        for genre, color in GENRE_COLORS.items()
        if genre not in ['other', 'unknown']
    ]

def get_genre_description(genre: str) -> str:
    """Get human-readable description for genre."""
    descriptions = {
        'pop': 'Popular Music',
        'rock': 'Rock & Alternative Rock',
        'k-pop': 'Korean Pop',
        'j-pop': 'Japanese Pop', 
        'hip-hop': 'Hip-Hop & Rap',
        'electronic': 'Electronic & EDM',
        'r&b': 'R&B & Soul',
        'metal': 'Metal & Hard Rock',
        'indie': 'Indie & Alternative',
        'alternative': 'Alternative Music',
        'country': 'Country Music',
        'folk': 'Folk & Acoustic',
        'jazz': 'Jazz & Blues',
        'classical': 'Classical Music',
        'reggae': 'Reggae & Ska',
        'punk': 'Punk Rock'
    }
    return descriptions.get(genre, genre.title())

# CSS styles for black background visualization
def generate_css_styles():
    """Generate CSS styles for the visualization."""
    return """
    /* Black background network visualization styles */
    body {
        background-color: #000000;
        color: #FFFFFF;
        font-family: 'Arial', sans-serif;
        margin: 0;
        padding: 0;
    }
    
    .network-container {
        width: 100vw;
        height: 100vh;
        background-color: #000000;
    }
    
    .node {
        stroke: #FFFFFF;
        stroke-width: 1.5px;
        cursor: pointer;
    }
    
    .node:hover {
        stroke: #FFFF00;
        stroke-width: 3px;
    }
    
    .link {
        stroke: #333333;
        stroke-opacity: 0.6;
        stroke-width: 1px;
    }
    
    .link.highlighted {
        stroke: #FFFFFF;
        stroke-opacity: 0.9;
        stroke-width: 2px;
    }
    
    .node-label {
        fill: #FFFFFF;
        font-size: 10px;
        text-anchor: middle;
        pointer-events: none;
    }
    
    .legend {
        position: absolute;
        top: 20px;
        right: 20px;
        background-color: rgba(0, 0, 0, 0.8);
        border: 1px solid #FFFFFF;
        padding: 15px;
        border-radius: 5px;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        margin: 5px 0;
    }
    
    .legend-color {
        width: 15px;
        height: 15px;
        margin-right: 10px;
        border-radius: 50%;
    }
    
    .controls {
        position: absolute;
        top: 20px;
        left: 20px;
        background-color: rgba(0, 0, 0, 0.8);
        border: 1px solid #FFFFFF;
        padding: 15px;
        border-radius: 5px;
    }
    
    .control-button {
        background-color: #333333;
        color: #FFFFFF;
        border: 1px solid #FFFFFF;
        padding: 8px 12px;
        margin: 2px;
        border-radius: 3px;
        cursor: pointer;
    }
    
    .control-button:hover {
        background-color: #555555;
    }
    """

def test_genre_colors():
    """Test the genre color system."""
    print("🎨 Testing Genre Color System")
    print("=" * 30)
    
    print("\n🌈 Genre Colors (optimized for black background):")
    for genre, color in GENRE_COLORS.items():
        description = get_genre_description(genre)
        print(f"   {genre:12} {color:8} - {description}")
    
    print(f"\n🎯 D3.js Color Scale:")
    scale = get_d3_color_scale()
    print(f"   Type: {scale['type']}")
    print(f"   Genres: {len(scale['domain'])} total")
    
    print(f"\n✨ Color Intensity Examples:")
    test_genre = 'k-pop'
    for intensity in ['high', 'medium', 'low']:
        color = get_genre_color(test_genre, intensity)
        print(f"   {test_genre} ({intensity}): {color}")
    
    print(f"\n📊 Legend Data:")
    legend = generate_genre_legend()
    for item in legend[:5]:  # Show first 5
        print(f"   {item['genre']}: {item['color']} - {item['description']}")
    
    print(f"\n✅ Genre color system ready for D3.js!")

if __name__ == "__main__":
    test_genre_colors()