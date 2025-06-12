#!/usr/bin/env python3
"""
Visualization Comparison Tool
Tests different graph visualization libraries as Gephi alternatives.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import json

def create_sample_network_data():
    """Create sample network data for testing visualizations."""
    # Sample artist data with the improved resolution
    nodes_data = [
        {'id': 'taylor-swift', 'display_name': 'Taylor Swift', 'listeners': 5160232, 'genre': 'pop'},
        {'id': 'paramore', 'display_name': 'Paramore', 'listeners': 4779115, 'genre': 'rock'},
        {'id': 'blackpink', 'display_name': 'BLACKPINK', 'listeners': 1558082, 'genre': 'k-pop'},
        {'id': 'twice', 'display_name': 'TWICE', 'listeners': 1388675, 'genre': 'k-pop'},
        {'id': 'the-killers', 'display_name': 'The Killers', 'listeners': 6183625, 'genre': 'rock'},
        {'id': 'bmth', 'display_name': 'Bring Me The Horizon', 'listeners': 2441949, 'genre': 'metal'},
        {'id': 'dreamcatcher', 'display_name': 'Dreamcatcher', 'listeners': 494541, 'genre': 'k-pop'},
        {'id': 'iu', 'display_name': 'IU', 'listeners': 913058, 'genre': 'k-pop'},
    ]
    
    # Sample edges (similarity relationships)
    edges_data = [
        {'source': 'paramore', 'target': 'the-killers', 'weight': 0.75, 'type': 'rock'},
        {'source': 'paramore', 'target': 'bmth', 'weight': 0.65, 'type': 'rock'},
        {'source': 'blackpink', 'target': 'twice', 'weight': 0.85, 'type': 'k-pop'},
        {'source': 'blackpink', 'target': 'dreamcatcher', 'weight': 0.55, 'type': 'k-pop'},
        {'source': 'twice', 'target': 'iu', 'weight': 0.70, 'type': 'k-pop'},
        {'source': 'the-killers', 'target': 'bmth', 'weight': 0.45, 'type': 'rock'},
    ]
    
    nodes_df = pd.DataFrame(nodes_data)
    edges_df = pd.DataFrame(edges_data)
    
    return nodes_df, edges_df

def test_pygraphistry(nodes_df: pd.DataFrame, edges_df: pd.DataFrame):
    """Test pygraphistry visualization."""
    print("\n🔹 Testing PyGraphistry...")
    
    try:
        import graphistry
        
        # Check if we can use local mode (no account needed)
        print("  📊 Creating graphistry visualization...")
        
        # Bind the data
        g = graphistry.bind(
            source='source', 
            destination='target',
            edge_weight='weight',
            node='id'
        )
        
        # Add node data
        g = g.nodes(nodes_df.set_index('id'))
        
        # Create the plot (this will work in local mode)
        try:
            # This creates a local HTML file
            url = g.plot(edges_df, render=False)
            print(f"  ✅ GraphIstry plot created")
            print(f"  📁 Local file mode - check for HTML output")
            
            # Try to save as HTML
            html_content = g._ipython_display_()
            if html_content:
                with open('network_graphistry.html', 'w') as f:
                    f.write(str(html_content))
                print(f"  💾 Saved as: network_graphistry.html")
                
        except Exception as e:
            print(f"  ⚠️  Plot generation: {e}")
            print("  💡 Note: Full GraphIstry features require account/API key")
            
    except ImportError:
        print("  ❌ GraphIstry not installed")
    except Exception as e:
        print(f"  ❌ GraphIstry error: {e}")

def test_plotly_network(nodes_df: pd.DataFrame, edges_df: pd.DataFrame):
    """Test Plotly network visualization."""
    print("\n🔹 Testing Plotly Network...")
    
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        import networkx as nx
        from math import sqrt
        
        # Create NetworkX graph for layout
        G = nx.Graph()
        
        # Add nodes with attributes
        for _, node in nodes_df.iterrows():
            G.add_node(node['id'], **node.to_dict())
        
        # Add edges
        for _, edge in edges_df.iterrows():
            G.add_edge(edge['source'], edge['target'], weight=edge['weight'])
        
        # Calculate layout
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Prepare edge traces
        edge_x = []
        edge_y = []
        edge_info = []
        
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
        
        color_map = {'pop': 'red', 'rock': 'blue', 'k-pop': 'purple', 'metal': 'orange'}
        
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
            node_colors.append(color_map.get(node_info['genre'], 'gray'))
            
            # Size by listeners (normalized)
            size = max(10, min(50, sqrt(node_info['listeners']) / 1000))
            node_sizes.append(size)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[G.nodes[node]['display_name'] for node in G.nodes()],
            textposition="middle center",
            hovertext=node_text,
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white')
            )
        )
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title="Artist Similarity Network",
                           titlefont_size=16,
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Artist relationships based on Last.fm similarity",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002 ) ],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                       )
        
        # Save as HTML
        fig.write_html("network_plotly.html")
        print(f"  ✅ Plotly network created")
        print(f"  💾 Saved as: network_plotly.html")
        print(f"  🌐 Open in browser for interactive visualization")
        
    except ImportError as e:
        print(f"  ❌ Missing dependency: {e}")
    except Exception as e:
        print(f"  ❌ Plotly error: {e}")

def test_bokeh_network(nodes_df: pd.DataFrame, edges_df: pd.DataFrame):
    """Test Bokeh network visualization."""
    print("\n🔹 Testing Bokeh Network...")
    
    try:
        from bokeh.plotting import figure, save, output_file
        from bokeh.models import HoverTool, GraphRenderer, StaticLayoutProvider, Oval
        from bokeh.palettes import Category10
        import networkx as nx
        
        # Create NetworkX graph
        G = nx.Graph()
        for _, node in nodes_df.iterrows():
            G.add_node(node['id'], **node.to_dict())
        for _, edge in edges_df.iterrows():
            G.add_edge(edge['source'], edge['target'], weight=edge['weight'])
        
        # Calculate layout
        layout = nx.spring_layout(G, k=3, iterations=50)
        
        # Create plot
        plot = figure(width=800, height=600, 
                     title="Artist Network - Bokeh",
                     x_range=(-2, 2), y_range=(-2, 2),
                     tools="pan,wheel_zoom,box_zoom,reset,save")
        
        # Create graph renderer
        graph = GraphRenderer()
        
        # Node data
        node_ids = list(G.nodes())
        graph.node_renderer.data_source.data = dict(
            index=node_ids,
            names=[G.nodes[node]['display_name'] for node in node_ids],
            listeners=[G.nodes[node]['listeners'] for node in node_ids],
            genres=[G.nodes[node]['genre'] for node in node_ids]
        )
        
        # Edge data  
        edges_start = []
        edges_end = []
        for edge in G.edges():
            edges_start.append(edge[0])
            edges_end.append(edge[1])
        
        graph.edge_renderer.data_source.data = dict(
            start=edges_start,
            end=edges_end
        )
        
        # Layout
        graph.layout_provider = StaticLayoutProvider(graph_layout=layout)
        
        # Add hover tool
        hover = HoverTool(tooltips=[
            ("Artist", "@names"),
            ("Listeners", "@listeners"),
            ("Genre", "@genres")
        ])
        plot.add_tools(hover)
        
        # Add graph to plot
        plot.renderers.append(graph)
        
        # Save
        output_file("network_bokeh.html")
        save(plot)
        
        print(f"  ✅ Bokeh network created")
        print(f"  💾 Saved as: network_bokeh.html")
        
    except ImportError as e:
        print(f"  ❌ Missing dependency: {e}")
        print(f"  💡 Install with: pip install bokeh")
    except Exception as e:
        print(f"  ❌ Bokeh error: {e}")

def create_simple_d3_network(nodes_df: pd.DataFrame, edges_df: pd.DataFrame):
    """Create a simple D3.js network visualization."""
    print("\n🔹 Creating D3.js Network...")
    
    try:
        # Convert to D3-friendly format
        nodes_list = []
        for _, node in nodes_df.iterrows():
            nodes_list.append({
                'id': node['id'],
                'name': node['display_name'],
                'listeners': int(node['listeners']),
                'genre': node['genre'],
                'size': max(5, min(25, np.sqrt(node['listeners']) / 2000))
            })
        
        edges_list = []
        for _, edge in edges_df.iterrows():
            edges_list.append({
                'source': edge['source'],
                'target': edge['target'],
                'weight': float(edge['weight'])
            })
        
        # Create HTML with embedded D3.js
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Artist Network - D3.js</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        .node {{ fill: steelblue; stroke: white; stroke-width: 2px; cursor: pointer; }}
        .link {{ stroke: #999; stroke-opacity: 0.6; }}
        .node text {{ font: 12px sans-serif; text-anchor: middle; fill: white; }}
        .tooltip {{ position: absolute; padding: 10px; background: rgba(0,0,0,0.8); color: white; border-radius: 5px; pointer-events: none; }}
    </style>
</head>
<body>
    <h2>Artist Similarity Network</h2>
    <svg width="900" height="600"></svg>
    <div class="tooltip" style="opacity: 0;"></div>
    
    <script>
        const nodes = {json.dumps(nodes_list)};
        const links = {json.dumps(edges_list)};
        
        const svg = d3.select("svg");
        const width = +svg.attr("width");
        const height = +svg.attr("height");
        
        const color = d3.scaleOrdinal(d3.schemeCategory10);
        
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2));
        
        const tooltip = d3.select(".tooltip");
        
        const link = svg.append("g")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("class", "link")
            .attr("stroke-width", d => Math.sqrt(d.weight) * 3);
        
        const node = svg.append("g")
            .selectAll("circle")
            .data(nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("r", d => d.size)
            .attr("fill", d => color(d.genre))
            .on("mouseover", function(event, d) {{
                tooltip.transition().duration(200).style("opacity", .9);
                tooltip.html(d.name + "<br/>Listeners: " + d.listeners.toLocaleString() + "<br/>Genre: " + d.genre)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 28) + "px");
            }})
            .on("mouseout", function(d) {{
                tooltip.transition().duration(500).style("opacity", 0);
            }});
        
        const text = svg.append("g")
            .selectAll("text")
            .data(nodes)
            .enter().append("text")
            .text(d => d.name)
            .attr("font-size", "10px")
            .attr("text-anchor", "middle");
        
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
    </script>
</body>
</html>"""
        
        with open('network_d3.html', 'w') as f:
            f.write(html_content)
        
        print(f"  ✅ D3.js network created")
        print(f"  💾 Saved as: network_d3.html")
        print(f"  🎯 Features: Interactive dragging, hover tooltips, force layout")
        
    except Exception as e:
        print(f"  ❌ D3.js creation error: {e}")

def main():
    """Run visualization comparison tests."""
    print("🎨 VISUALIZATION COMPARISON - Gephi Alternatives")
    print("=" * 60)
    
    # Create sample data
    nodes_df, edges_df = create_sample_network_data()
    print(f"📊 Sample data: {len(nodes_df)} nodes, {len(edges_df)} edges")
    
    # Test different visualizations
    test_plotly_network(nodes_df, edges_df)
    test_pygraphistry(nodes_df, edges_df) 
    test_bokeh_network(nodes_df, edges_df)
    create_simple_d3_network(nodes_df, edges_df)
    
    print(f"\n📋 SUMMARY:")
    print(f"Generated visualization files:")
    print(f"  • network_plotly.html  - Plotly (recommended for interactivity)")
    print(f"  • network_d3.html      - D3.js (recommended for customization)")
    print(f"  • network_bokeh.html   - Bokeh (if installed)")
    print(f"  • network_graphistry.html - GraphIstry (if configured)")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"  🥇 Plotly: Best balance of features, performance, and ease of use")
    print(f"  🥈 D3.js: Most flexible, completely self-contained")
    print(f"  🥉 GraphIstry: Great for large networks (requires account)")
    
    print(f"\n🚀 Next step: Open the HTML files in your browser!")

if __name__ == "__main__":
    main()