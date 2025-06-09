"""
Simple similarity test that works with your actual data.
Generates a basic HTML report of artist similarities.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from config_loader import AppConfig
from lastfm_utils import LastfmAPI


def test_with_actual_data():
    """Test similarity functionality with actual user data."""
    print("Simple Artist Similarity Test")
    print("=" * 50)
    
    # Work from the main directory
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
            return False
            
        api = LastfmAPI(
            lastfm_config['api_key'], 
            lastfm_config['api_secret'], 
            lastfm_config['cache_dir']
        )
        
        # Try to load data
        print("🔍 Checking data availability...")
        
        from data_processor import clean_and_filter_data
        df = clean_and_filter_data(config)
        
        if df is None or df.empty:
            print("❌ No data available, using sample artists instead")
            test_artists = ["Taylor Swift", "BLACKPINK", "BTS", "Ariana Grande", "Paramore"]
        else:
            print(f"✅ Found {len(df)} rows of data")
            
            # Get top artists from your data
            if 'artist' in df.columns:
                top_artists = df.groupby('artist').size().sort_values(ascending=False).head(10)
                test_artists = list(top_artists.index)
                print(f"🎵 Using your top {len(test_artists)} artists")
                
                # Show them
                for i, (artist, plays) in enumerate(top_artists.head(5).items(), 1):
                    print(f"   {i}. {artist} ({plays} plays)")
                if len(test_artists) > 5:
                    print(f"   ... and {len(test_artists)-5} more")
            else:
                print("❌ No artist column found, using sample artists")
                test_artists = ["Taylor Swift", "BLACKPINK", "BTS", "Ariana Grande", "Paramore"]
        
        # Test similarity for these artists
        print(f"\n🔗 Testing similarities for {len(test_artists)} artists...")
        
        similarity_results = {}
        
        for i, artist in enumerate(test_artists, 1):
            print(f"   {i}/{len(test_artists)}: {artist}")
            similar = api.get_similar_artists(artist_name=artist, limit=10)
            similarity_results[artist] = similar
        
        # Generate simple report
        generate_simple_report(similarity_results, test_artists)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    finally:
        os.chdir(original_dir)


def generate_simple_report(similarity_results, test_artists):
    """Generate a simple HTML report."""
    print(f"\n📄 Generating report...")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Artist Similarity Report - {datetime.now().strftime('%Y-%m-%d')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .artist {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .artist-name {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
            .similar {{ background: white; padding: 8px; margin: 3px 0; border-left: 3px solid #4CAF50; }}
            .score {{ float: right; color: #4CAF50; font-weight: bold; }}
            .network-edge {{ color: #ff5722; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Artist Similarity Analysis</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Artists analyzed: {len(similarity_results)}</p>
    """
    
    # Network connections within your artists
    connections = []
    
    for artist, similar_list in similarity_results.items():
        html_content += f"""
        <div class="artist">
            <div class="artist-name">{artist}</div>
        """
        
        if similar_list:
            html_content += f"<p>Similar artists ({len(similar_list)} found):</p>"
            
            for sim in similar_list[:8]:  # Show top 8
                # Check if this similar artist is also in your test list
                is_network_connection = sim['name'] in test_artists
                css_class = "similar network-edge" if is_network_connection else "similar"
                
                html_content += f"""
                <div class="{css_class}">
                    {sim['name']}
                    <span class="score">{sim['match']:.3f}</span>
                </div>
                """
                
                if is_network_connection:
                    connections.append({
                        'from': artist,
                        'to': sim['name'],
                        'score': sim['match']
                    })
        else:
            html_content += "<p>No similar artists found</p>"
        
        html_content += "</div>"
    
    # Add network summary
    if connections:
        html_content += f"""
        <div style="background: #e8f5e9; padding: 15px; border-radius: 5px; margin-top: 20px;">
            <h3>🕸️ Network Connections Found</h3>
            <p>These are connections between your artists (highlighted in red above):</p>
            <ul>
        """
        
        for conn in connections:
            html_content += f"<li>{conn['from']} → {conn['to']} (score: {conn['score']:.3f})</li>"
        
        html_content += f"""
            </ul>
            <p><strong>Total network edges: {len(connections)}</strong></p>
            <p>This shows how your favorite artists are connected through similarity!</p>
        </div>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    # Write file
    output_file = 'artist_similarity_report.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Report saved: {output_file}")
    
    if connections:
        print(f"🕸️  Found {len(connections)} network connections!")
        print("Top connections:")
        sorted_connections = sorted(connections, key=lambda x: x['score'], reverse=True)
        for conn in sorted_connections[:5]:
            print(f"   {conn['from']} → {conn['to']} ({conn['score']:.3f})")
    else:
        print("ℹ️  No direct connections found between your artists")
        print("   This is normal - try with more artists or different genres")


if __name__ == "__main__":
    success = test_with_actual_data()
    
    if success:
        print(f"\n✅ Test completed successfully!")
        print("Open 'artist_similarity_report.html' in a browser to see results")
    else:
        print(f"\n❌ Test failed")