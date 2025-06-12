#!/usr/bin/env python3
"""
Simple, fast network visualization creator.
Alternative to slow Gephi - creates interactive HTML visualizations quickly.
"""

import pandas as pd
import numpy as np
import json
import networkx as nx
from typing import Dict, List
from math import sqrt


def create_plotly_network(nodes_df: pd.DataFrame, edges_df: pd.DataFrame, 
                         output_file: str = "network_plotly.html"):
    """Create a Plotly network visualization - fixed version."""
    
    try:
        import plotly.graph_objects as go
        
        # Create NetworkX graph for layout
        G = nx.Graph()
        
        # Add nodes with attributes
        for _, node in nodes_df.iterrows():
            G.add_node(node['id'], **node.to_dict())
        
        # Add edges
        for _, edge in edges_df.iterrows():
            G.add_edge(edge['source'], edge['target'], weight=edge['weight'])
        
        # Calculate layout
        pos = nx.spring_layout(G, k=3, iterations=50, seed=42)
        
        # Prepare edge traces
        edge_x = []
        edge_y = []
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='rgba(125,125,125,0.5)'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Prepare node traces
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []
        
        color_map = {'pop': '#ff6b6b', 'rock': '#4ecdc4', 'k-pop': '#a8e6cf', 'metal': '#ffa726'}
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Node info
            node_info = G.nodes[node]
            node_text.append(f"{node_info['display_name']}<br>"
                           f"Listeners: {node_info['listeners']:,}<br>"
                           f"Genre: {node_info['genre']}")
            
            # Color by genre
            node_colors.append(color_map.get(node_info['genre'], '#gray'))
            
            # Size by listeners (normalized)
            size = max(15, min(50, sqrt(node_info['listeners']) / 1500))
            node_sizes.append(size)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[G.nodes[node]['display_name'] for node in G.nodes()],
            textposition="middle center",
            textfont=dict(size=12, color='white'),
            hovertext=node_text,
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white')
            )
        )
        
        # Create figure with fixed layout
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=dict(
                    text="Artist Similarity Network",
                    x=0.5,
                    font=dict(size=20)
                ),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=40, l=40, r=40, t=80),
                annotations=[
                    dict(
                        text="Interactive network - hover for details, drag to explore",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002,
                        font=dict(color="gray", size=12)
                    )
                ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
        )
        
        # Save as HTML
        fig.write_html(output_file)
        print(f"✅ Plotly network saved: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Plotly error: {e}")
        return False


def create_enhanced_d3_network(nodes_df: pd.DataFrame, edges_df: pd.DataFrame, 
                              output_file: str = "network_d3_enhanced.html"):
    """Create an enhanced D3.js network with better styling and features."""
    
    # Convert to D3-friendly format
    nodes_list = []
    for _, node in nodes_df.iterrows():
        nodes_list.append({
            'id': node['id'],
            'name': node['display_name'],
            'listeners': int(node['listeners']),
            'genre': node['genre'],
            'size': max(8, min(30, np.sqrt(node['listeners']) / 2000))
        })
    
    edges_list = []
    for _, edge in edges_df.iterrows():
        edges_list.append({
            'source': edge['source'],
            'target': edge['target'],
            'weight': float(edge['weight'])
        })
    
    # Create enhanced HTML with better styling
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Artist Network - Enhanced D3.js</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            overflow: hidden;
        }}
        .container {{ 
            display: flex; 
            height: 100vh; 
        }}
        .sidebar {{ 
            width: 250px; 
            background: rgba(0,0,0,0.3); 
            padding: 20px; 
            backdrop-filter: blur(10px);
        }}
        .main {{ 
            flex: 1; 
            position: relative; 
        }}
        h1 {{ 
            margin: 0 0 20px 0; 
            font-size: 24px; 
            font-weight: 300; 
        }}
        .controls {{ 
            margin: 20px 0; 
        }}
        .control-group {{ 
            margin: 15px 0; 
        }}
        label {{ 
            display: block; 
            margin-bottom: 5px; 
            font-size: 14px; 
        }}
        input[type="range"] {{ 
            width: 100%; 
            margin: 5px 0; 
        }}
        .node {{ 
            cursor: pointer; 
            transition: all 0.3s ease;
        }}
        .node:hover {{ 
            stroke-width: 4px; 
            filter: drop-shadow(0 0 10px rgba(255,255,255,0.8));
        }}
        .link {{ 
            stroke: rgba(255,255,255,0.4); 
            stroke-opacity: 0.6; 
            transition: all 0.3s ease;
        }}
        .link:hover {{ 
            stroke-opacity: 1; 
            stroke-width: 3px;
        }}
        .tooltip {{ 
            position: absolute; 
            padding: 12px; 
            background: rgba(0,0,0,0.9); 
            color: white; 
            border-radius: 8px; 
            pointer-events: none; 
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
        }}
        .genre-legend {{ 
            margin-top: 20px; 
        }}
        .legend-item {{ 
            display: flex; 
            align-items: center; 
            margin: 8px 0; 
            font-size: 13px;
        }}
        .legend-color {{ 
            width: 16px; 
            height: 16px; 
            border-radius: 50%; 
            margin-right: 10px; 
        }}
        svg {{ 
            width: 100%; 
            height: 100%; 
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h1>🎵 Artist Network</h1>
            
            <div class="controls">
                <div class="control-group">
                    <label>Force Strength</label>
                    <input type="range" id="forceStrength" min="50" max="500" value="300">
                </div>
                <div class="control-group">
                    <label>Link Distance</label>
                    <input type="range" id="linkDistance" min="50" max="200" value="100">
                </div>
            </div>
            
            <div class="genre-legend">
                <h3>Genres</h3>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ff6b6b;"></div>
                    Pop
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #4ecdc4;"></div>
                    Rock
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #a8e6cf;"></div>
                    K-Pop
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ffa726;"></div>
                    Metal
                </div>
            </div>
        </div>
        
        <div class="main">
            <svg></svg>
            <div class="tooltip" style="opacity: 0;"></div>
        </div>
    </div>
    
    <script>
        const nodes = {json.dumps(nodes_list)};
        const links = {json.dumps(edges_list)};
        
        const svg = d3.select("svg");
        const width = window.innerWidth - 250;
        const height = window.innerHeight;
        
        svg.attr("width", width).attr("height", height);
        
        // Color scale for genres
        const colorMap = {{
            'pop': '#ff6b6b',
            'rock': '#4ecdc4', 
            'k-pop': '#a8e6cf',
            'metal': '#ffa726'
        }};
        
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(d => d.size + 5));
        
        const tooltip = d3.select(".tooltip");
        
        // Create gradient definitions
        const defs = svg.append("defs");
        const gradient = defs.append("radialGradient")
            .attr("id", "nodeGradient");
        gradient.append("stop")
            .attr("offset", "0%")
            .attr("stop-color", "white")
            .attr("stop-opacity", 0.3);
        gradient.append("stop")
            .attr("offset", "100%")
            .attr("stop-color", "white")
            .attr("stop-opacity", 0);
        
        const link = svg.append("g")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("class", "link")
            .attr("stroke-width", d => Math.sqrt(d.weight) * 4);
        
        const node = svg.append("g")
            .selectAll("circle")
            .data(nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("r", d => d.size)
            .attr("fill", d => colorMap[d.genre] || '#gray')
            .attr("stroke", "white")
            .attr("stroke-width", 2)
            .on("mouseover", function(event, d) {{
                d3.select(this).attr("fill", "url(#nodeGradient)");
                tooltip.transition().duration(200).style("opacity", 1);
                tooltip.html(`
                    <strong>${{d.name}}</strong><br/>
                    Listeners: ${{d.listeners.toLocaleString()}}<br/>
                    Genre: ${{d.genre}}
                `)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 40) + "px");
            }})
            .on("mouseout", function(event, d) {{
                d3.select(this).attr("fill", colorMap[d.genre] || '#gray');
                tooltip.transition().duration(500).style("opacity", 0);
            }})
            .on("click", function(event, d) {{
                // Center on clicked node
                const transform = d3.zoomIdentity
                    .translate(width / 2 - d.x, height / 2 - d.y)
                    .scale(1.5);
                svg.transition().duration(750)
                    .call(zoom.transform, transform);
            }});
        
        const text = svg.append("g")
            .selectAll("text")
            .data(nodes)
            .enter().append("text")
            .text(d => d.name)
            .attr("font-size", "11px")
            .attr("text-anchor", "middle")
            .attr("fill", "white")
            .attr("font-weight", "bold")
            .attr("text-shadow", "1px 1px 2px rgba(0,0,0,0.8)")
            .style("pointer-events", "none");
        
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", function(event) {{
                svg.selectAll("g").attr("transform", event.transform);
            }});
        
        svg.call(zoom);
        
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
            
            text
                .attr("x", d => d.x)
                .attr("y", d => d.y + 4);
        }});
        
        // Drag functionality
        node.call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));
        
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}
        
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        
        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
        
        // Control handlers
        d3.select("#forceStrength").on("input", function() {{
            simulation.force("charge").strength(-this.value);
            simulation.alpha(0.3).restart();
        }});
        
        d3.select("#linkDistance").on("input", function() {{
            simulation.force("link").distance(this.value);
            simulation.alpha(0.3).restart();
        }});
    </script>
</body>
</html>"""
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Enhanced D3.js network saved: {output_file}")
    return True


def create_network_from_real_data(top_n: int = 15, threshold: float = 0.08):
    """Create network visualization from real Last.fm data."""
    
    print(f"🎯 Creating network visualization from real data...")
    print(f"📊 Parameters: {top_n} artists, threshold {threshold}")
    
    try:
        # Use our optimized resolution
        from fix_artist_resolution import OptimizedLastFmClient
        from validate_graph import validate_artist_network
        
        # Generate real network data
        result = validate_artist_network(top_n, threshold)
        if not result:
            print("❌ Failed to generate network data")
            return False
        
        network_data, validation_results, graph = result
        
        # Convert to DataFrame format
        nodes_data = []
        for node in network_data['nodes']:
            nodes_data.append({
                'id': node['id'].lower().replace(' ', '-'),
                'display_name': node['name'],
                'listeners': node['play_count'],  # Using play count as proxy
                'genre': 'unknown'  # We'll add genre detection later
            })
        
        edges_data = []
        for edge in network_data['edges']:
            edges_data.append({
                'source': edge['source'].lower().replace(' ', '-'),
                'target': edge['target'].lower().replace(' ', '-'),
                'weight': edge['weight']
            })
        
        nodes_df = pd.DataFrame(nodes_data)
        edges_df = pd.DataFrame(edges_data)
        
        print(f"📈 Network: {len(nodes_df)} nodes, {len(edges_df)} edges")
        
        # Create visualizations
        plotly_success = create_plotly_network(nodes_df, edges_df, "real_network_plotly.html")
        d3_success = create_enhanced_d3_network(nodes_df, edges_df, "real_network_d3.html")
        
        if plotly_success or d3_success:
            print(f"\n🎉 SUCCESS! Network visualizations created:")
            if plotly_success:
                print(f"  📊 real_network_plotly.html - Interactive Plotly version")
            if d3_success:
                print(f"  🎨 real_network_d3.html - Enhanced D3.js version")
            print(f"\n💡 Open these files in your browser - much faster than Gephi!")
            return True
        else:
            print("❌ All visualizations failed")
            return False
            
    except Exception as e:
        print(f"❌ Error creating real network: {e}")
        return False


if __name__ == "__main__":
    print("🚀 FAST NETWORK VISUALIZATION CREATOR")
    print("=" * 50)
    
    # Option 1: Create from real data
    print("\n1️⃣ Creating from real listening data...")
    success = create_network_from_real_data(15, 0.08)
    
    if success:
        print(f"\n✅ Real network visualizations created!")
        print(f"🌐 Open the HTML files in your browser")
        print(f"📱 They're interactive - drag nodes, hover for details, zoom & pan")
        print(f"⚡ Much faster than Gephi!")
    else:
        print(f"\n⚠️ Real data failed, creating sample visualization...")
        
        # Option 2: Create sample network
        from test_visualizations import create_sample_network_data
        nodes_df, edges_df = create_sample_network_data()
        
        create_plotly_network(nodes_df, edges_df, "sample_network_plotly.html")
        create_enhanced_d3_network(nodes_df, edges_df, "sample_network_d3.html")
        
        print(f"📊 Sample visualizations created!")
        print(f"  • sample_network_plotly.html")
        print(f"  • sample_network_d3.html")