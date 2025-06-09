"""
Visual test for artist similarity data.
Creates an HTML report showing your top artists and their similar artists.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from config_loader import AppConfig
from lastfm_utils import LastfmAPI
from data_processor import clean_and_filter_data


def generate_similarity_report(output_file='similarity_report.html'):
    """Generate HTML report of artist similarities."""
    print("Generating artist similarity report...")
    
    # Change to main directory for proper file paths
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        # Load configuration
        config = AppConfig('configurations.txt')
        
        # Initialize Last.fm API
        lastfm_config = config.get_lastfm_config()
        if not lastfm_config['enabled'] or not lastfm_config['api_key']:
            print("❌ Last.fm API not configured")
            return
            
        api = LastfmAPI(
            lastfm_config['api_key'], 
            lastfm_config['api_secret'], 
            lastfm_config['cache_dir']
        )
        
        # Load and process data
        print("Loading your music data...")
        df = clean_and_filter_data(config)
        
        if df is None or df.empty:
            print("❌ No data loaded. Please check:")
            print(f"   - Data source: {config.get('DataSource', 'SOURCE')}")
            print(f"   - Data files exist in the main directory")
            print("   - Configuration is correct")
            return
        
        print(f"✅ Loaded {len(df)} rows of data")
        
        # Determine if we're in artist or track mode
        mode = config.get('VisualizationMode', 'MODE', fallback='tracks')
        
        if mode == 'artists' or mode == 'both':
            # Artist mode - use artist column directly
            if 'artist' in df.columns:
                artist_plays = df.groupby('artist').size().sort_values(ascending=False)
            else:
                print("Error: No 'artist' column found in data")
                return
        else:
            # Track mode - extract artists from track data
            if 'artist' in df.columns:
                artist_plays = df.groupby('artist').size().sort_values(ascending=False)
            elif 'track' in df.columns:
                # Try to extract artist from track info if formatted as "Artist - Track"
                df['extracted_artist'] = df['track'].str.split(' - ').str[0]
                artist_plays = df.groupby('extracted_artist').size().sort_values(ascending=False)
            else:
                print("Error: Could not extract artist information from data")
                return
        
        # Get top N artists
        top_n = min(20, len(artist_plays))  # Limit to 20 for reasonable report size
        top_artists = artist_plays.head(top_n)
        
        print(f"Found {len(artist_plays)} unique artists in your data")
        print(f"Generating report for top {top_n} artists...")
        
        # Build similarity data
        similarity_data = []
        
        for i, (artist, play_count) in enumerate(top_artists.items()):
            print(f"Fetching similar artists for {i+1}/{top_n}: {artist}")
            
            # Get similar artists
            similar = api.get_similar_artists(artist_name=artist, limit=10)
            
            # Get artist info for additional context
            info = api.get_artist_info(artist_name=artist)
            
            artist_data = {
                'name': artist,
                'play_count': int(play_count),
                'rank': i + 1,
                'similar_artists': similar[:10],  # Top 10 similar
                'info': info,
                'has_similar': len(similar) > 0
            }
            
            similarity_data.append(artist_data)
        
        # Generate HTML report
        print("Generating HTML report...")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Artist Similarity Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .artist-card {{
                    background: white;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .artist-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                    border-bottom: 2px solid #333;
                    padding-bottom: 10px;
                }}
                .artist-name {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                }}
                .play-count {{
                    font-size: 18px;
                    color: #666;
                }}
                .artist-info {{
                    margin-bottom: 15px;
                    color: #666;
                    font-size: 14px;
                }}
                .similar-artists {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                    gap: 10px;
                }}
                .similar-artist {{
                    background: #f8f8f8;
                    padding: 10px;
                    border-radius: 4px;
                    border-left: 4px solid #4CAF50;
                }}
                .similarity-score {{
                    font-weight: bold;
                    color: #4CAF50;
                    float: right;
                }}
                .no-data {{
                    color: #999;
                    font-style: italic;
                }}
                .stats {{
                    background: #e8f5e9;
                    padding: 15px;
                    border-radius: 4px;
                    margin-bottom: 30px;
                    text-align: center;
                }}
                .legend {{
                    background: white;
                    padding: 15px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                }}
                .score-high {{ color: #2e7d32; }}
                .score-medium {{ color: #f57c00; }}
                .score-low {{ color: #d32f2f; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Artist Similarity Analysis</h1>
                <p>Generated from your listening history</p>
                <p>{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            
            <div class="stats">
                <h3>Summary Statistics</h3>
                <p>Total unique artists: {len(artist_plays)}</p>
                <p>Artists analyzed: {len(similarity_data)}</p>
                <p>Total plays in dataset: {df.shape[0]}</p>"""
        
        # Add date range if index is datetime
        if hasattr(df.index, 'min') and hasattr(df.index.min(), 'strftime'):
            try:
                start_date = df.index.min().strftime('%Y-%m-%d')
                end_date = df.index.max().strftime('%Y-%m-%d')
                html_content += f"<p>Date range: {start_date} to {end_date}</p>"
            except:
                html_content += "<p>Date range: Unable to determine</p>"
        else:
            html_content += "<p>Date range: Not available</p>"
        
        html_content += """
            </div>
            
            <div class="legend">
                <h3>Similarity Score Legend</h3>
                <span class="score-high">■ High (0.7-1.0)</span> &nbsp;&nbsp;
                <span class="score-medium">■ Medium (0.4-0.7)</span> &nbsp;&nbsp;
                <span class="score-low">■ Low (0.0-0.4)</span>
            </div>
        """
        
        # Add artist cards
        for artist_data in similarity_data:
            artist = artist_data['name']
            play_count = artist_data['play_count']
            rank = artist_data['rank']
            similar = artist_data['similar_artists']
            info = artist_data['info']
            
            html_content += f"""
            <div class="artist-card">
                <div class="artist-header">
                    <div class="artist-name">#{rank}. {artist}</div>
                    <div class="play-count">{play_count} plays</div>
                </div>
            """
            
            # Add artist info if available
            if info:
                tags = ', '.join([tag['name'] for tag in info.get('tags', [])[:5]])
                if tags:
                    html_content += f'<div class="artist-info">Tags: {tags}</div>'
            
            # Add similar artists
            if similar:
                html_content += '<div class="similar-artists">'
                for sim in similar:
                    score = sim['match']
                    score_class = 'score-high' if score >= 0.7 else 'score-medium' if score >= 0.4 else 'score-low'
                    html_content += f"""
                    <div class="similar-artist">
                        <span>{sim['name']}</span>
                        <span class="similarity-score {score_class}">{score:.3f}</span>
                    </div>
                    """
                html_content += '</div>'
            else:
                html_content += '<div class="no-data">No similar artists found</div>'
            
            html_content += '</div>'
        
        html_content += """
        </body>
        </html>
        """
        
        # Write HTML file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nReport generated: {output_file}")
        print(f"Open this file in a web browser to view the similarity analysis.")
        
        # Generate summary statistics
        total_similar = sum(len(a['similar_artists']) for a in similarity_data)
        artists_with_data = sum(1 for a in similarity_data if a['has_similar'])
        
        print(f"\nSummary:")
        print(f"- Artists analyzed: {len(similarity_data)}")
        print(f"- Artists with similarity data: {artists_with_data}")
        print(f"- Total similar artist relationships: {total_similar}")
        
        # Find artists that appear as similar to multiple of your top artists
        similar_counts = {}
        for artist_data in similarity_data:
            for sim in artist_data['similar_artists']:
                sim_name = sim['name']
                if sim_name not in similar_counts:
                    similar_counts[sim_name] = []
                similar_counts[sim_name].append({
                    'to_artist': artist_data['name'],
                    'score': sim['match']
                })
        
        # Find artists that connect multiple of your favorites
        connected_artists = {k: v for k, v in similar_counts.items() if len(v) > 1}
        if connected_artists:
            print(f"\nArtists that connect multiple of your favorites:")
            sorted_connected = sorted(connected_artists.items(), key=lambda x: len(x[1]), reverse=True)
            for artist, connections in sorted_connected[:10]:
                avg_score = sum(c['score'] for c in connections) / len(connections)
                connected_to = ', '.join(c['to_artist'] for c in connections[:3])
                if len(connections) > 3:
                    connected_to += f" and {len(connections)-3} more"
                print(f"  - {artist}: connects {len(connections)} artists (avg score: {avg_score:.3f})")
                print(f"    Connected to: {connected_to}")
    
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        
    finally:
        # Restore original directory
        os.chdir(original_dir)


def generate_json_export(output_file='similarity_data.json'):
    """Export similarity data as JSON for further processing."""
    print("\nExporting similarity data to JSON...")
    
    # Change to main directory for proper file paths
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        # Load configuration
        config = AppConfig('configurations.txt')
        
        # Initialize Last.fm API
        lastfm_config = config.get_lastfm_config()
        api = LastfmAPI(
            lastfm_config['api_key'], 
            lastfm_config['api_secret'], 
            lastfm_config['cache_dir']
        )
        
        # Load data
        df = clean_and_filter_data(config)
        if df is None or df.empty:
            print("❌ No data available for JSON export")
            return
            
        artist_plays = df.groupby('artist').size().sort_values(ascending=False)
        top_artists = artist_plays.head(50)  # Top 50 for JSON export
        
        # Build network data
        network_data = {
            'nodes': [],
            'edges': [],
            'metadata': {
                'generated': datetime.now().isoformat(),
                'total_artists': len(artist_plays),
                'artists_included': len(top_artists)
            }
        }
        
        # Add nodes
        for artist, play_count in top_artists.items():
            network_data['nodes'].append({
                'id': artist,
                'play_count': int(play_count),
                'in_library': True
            })
        
        # Add edges (similarity relationships)
        for artist, play_count in top_artists.items():
            similar = api.get_similar_artists(artist_name=artist, limit=20)
            
            for sim in similar:
                # Only add edge if similar artist is also in top artists
                if sim['name'] in top_artists.index:
                    network_data['edges'].append({
                        'source': artist,
                        'target': sim['name'],
                        'weight': sim['match']
                    })
        
        # Write JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, ensure_ascii=False, indent=2)
        
        print(f"Network data exported to: {output_file}")
        print(f"Nodes: {len(network_data['nodes'])}")
        print(f"Edges: {len(network_data['edges'])}")
        
    except Exception as e:
        print(f"❌ Error exporting JSON: {e}")
        
    finally:
        # Restore original directory
        os.chdir(original_dir)


if __name__ == "__main__":
    print("Artist Similarity Visualization Test")
    print("=" * 50)
    
    # Generate HTML report
    generate_similarity_report()
    
    # Optionally generate JSON export
    response = input("\nGenerate JSON export for network visualization? (y/n): ")
    if response.lower() == 'y':
        generate_json_export()