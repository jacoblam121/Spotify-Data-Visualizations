"""
Basic test for Last.fm API functionality without requiring data files.
Tests core functionality with known artists.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from config_loader import AppConfig
from lastfm_utils import LastfmAPI


def test_basic_functionality():
    """Test basic Last.fm functionality with known artists."""
    print("Testing Last.fm API Basic Functionality")
    print("=" * 50)
    
    # Load configuration
    config = AppConfig('../configurations.txt')
    lastfm_config = config.get_lastfm_config()
    
    if not lastfm_config['enabled']:
        print("❌ Last.fm integration is disabled in configuration")
        return False
        
    if not lastfm_config['api_key']:
        print("❌ No Last.fm API key configured")
        return False
    
    # Initialize API
    api = LastfmAPI(
        lastfm_config['api_key'], 
        lastfm_config['api_secret'], 
        lastfm_config['cache_dir']
    )
    
    # Test artists that should have good similarity data
    test_artists = [
        "Taylor Swift",
        "BLACKPINK", 
        "BTS",
        "Ariana Grande",
        "The Beatles"
    ]
    
    print(f"\nTesting with {len(test_artists)} popular artists...")
    
    similarity_results = {}
    
    for artist in test_artists:
        print(f"\n🔍 Testing: {artist}")
        
        # Get similar artists
        similar = api.get_similar_artists(artist_name=artist, limit=10)
        
        if similar:
            print(f"  ✅ Found {len(similar)} similar artists")
            # Show top 3
            for i, sim in enumerate(similar[:3], 1):
                print(f"    {i}. {sim['name']} (score: {sim['match']:.3f})")
            
            similarity_results[artist] = similar
        else:
            print(f"  ❌ No similar artists found")
            
        # Get artist info
        info = api.get_artist_info(artist_name=artist)
        if info:
            print(f"  📊 Listeners: {info['listeners']:,}, Plays: {info['playcount']:,}")
            if info['tags']:
                tags = ', '.join([tag['name'] for tag in info['tags'][:3]])
                print(f"  🏷️  Tags: {tags}")
        else:
            print(f"  ❌ No artist info found")
    
    # Generate simple network data structure
    print(f"\n🕸️  Generating basic network data...")
    
    network_data = {
        'nodes': [],
        'edges': [],
        'metadata': {
            'generated': datetime.now().isoformat(),
            'test_artists': len(test_artists)
        }
    }
    
    # Add nodes for test artists
    for artist in test_artists:
        if artist in similarity_results:
            network_data['nodes'].append({
                'id': artist,
                'type': 'primary',
                'similar_count': len(similarity_results[artist])
            })
    
    # Add edges for similarities between test artists
    edge_count = 0
    for artist, similar_list in similarity_results.items():
        for sim in similar_list:
            # Only add edge if similar artist is also in our test list
            if sim['name'] in test_artists:
                network_data['edges'].append({
                    'source': artist,
                    'target': sim['name'],
                    'weight': sim['match']
                })
                edge_count += 1
    
    print(f"  📈 Network data: {len(network_data['nodes'])} nodes, {len(network_data['edges'])} edges")
    
    # Save test results
    output_file = 'lastfm_test_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'similarity_results': similarity_results,
            'network_data': network_data
        }, f, ensure_ascii=False, indent=2)
    
    print(f"  💾 Results saved to: {output_file}")
    
    # Generate simple HTML report
    generate_basic_html_report(similarity_results, 'lastfm_test_report.html')
    
    return True


def generate_basic_html_report(similarity_results, output_file):
    """Generate a simple HTML report of similarity results."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Last.fm API Test Results - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .artist {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .artist-name {{ font-size: 20px; font-weight: bold; color: #333; margin-bottom: 10px; }}
            .similar {{ background: white; padding: 8px; margin: 5px 0; border-left: 3px solid #4CAF50; }}
            .score {{ float: right; color: #4CAF50; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Last.fm API Test Results</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Artists tested: {len(similarity_results)}</p>
    """
    
    for artist, similar_list in similarity_results.items():
        html_content += f"""
        <div class="artist">
            <div class="artist-name">{artist}</div>
            <p>Found {len(similar_list)} similar artists:</p>
        """
        
        for sim in similar_list[:10]:  # Show top 10
            html_content += f"""
            <div class="similar">
                {sim['name']}
                <span class="score">{sim['match']:.3f}</span>
            </div>
            """
        
        html_content += '</div>'
    
    html_content += """
    </body>
    </html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"  📄 HTML report saved to: {output_file}")


def test_cache_performance():
    """Test cache performance with repeated requests."""
    print(f"\n⚡ Testing cache performance...")
    
    config = AppConfig('../configurations.txt')
    lastfm_config = config.get_lastfm_config()
    api = LastfmAPI(
        lastfm_config['api_key'], 
        lastfm_config['api_secret'], 
        lastfm_config['cache_dir']
    )
    
    import time
    
    test_artist = "Taylor Swift"
    
    # First request (API call)
    start = time.time()
    result1 = api.get_similar_artists(artist_name=test_artist, limit=20)
    api_time = time.time() - start
    
    # Second request (cache hit)
    start = time.time() 
    result2 = api.get_similar_artists(artist_name=test_artist, limit=20)
    cache_time = time.time() - start
    
    print(f"  API call time: {api_time:.3f}s")
    print(f"  Cache hit time: {cache_time:.3f}s")
    print(f"  Speed improvement: {api_time/cache_time:.1f}x faster")
    print(f"  Results identical: {result1 == result2}")


if __name__ == "__main__":
    print("Last.fm API Basic Functionality Test")
    print("This test works without requiring your music data files")
    print()
    
    success = test_basic_functionality()
    
    if success:
        test_cache_performance()
        print(f"\n✅ All tests completed successfully!")
        print("Check the generated HTML report to see similarity results.")
    else:
        print(f"\n❌ Tests failed. Check configuration.")