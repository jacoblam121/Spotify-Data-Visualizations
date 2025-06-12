#!/usr/bin/env python3
"""
Standalone Test for Problematic Artists
Tests specific artists that are showing issues in the Last.fm fetching.
"""

import os
import time
from dotenv import load_dotenv
from lastfm_utils import LastfmAPI
from config_loader import AppConfig

def test_problematic_artists():
    """Test the specific artists mentioned in the error logs."""
    print("🔍 Testing Problematic Artists - Standalone Test")
    print("=" * 60)
    
    # Load configuration
    load_dotenv()
    config = AppConfig('configurations.txt')
    lastfm_config = config.get_lastfm_config()
    
    # Check API credentials
    if not lastfm_config['api_key']:
        print("❌ No Last.fm API key found")
        print("💡 Add your Last.fm API key to .env file or configurations.txt")
        return False
    
    print(f"✅ Last.fm API Key: {lastfm_config['api_key'][:8]}...")
    
    # Initialize API
    api = LastfmAPI(
        lastfm_config['api_key'],
        lastfm_config['api_secret'], 
        lastfm_config['cache_dir']
    )
    
    # Test cases from error logs
    test_artists = [
        {
            'name': 'ive',
            'description': 'K-pop group IVE - showing errors before finding IVE (아이브)',
            'expected_result': 'Should resolve to IVE (아이브) with ~3K+ listeners'
        },
        {
            'name': 'anyujin', 
            'description': 'K-pop soloist An Yujin - showing errors before finding variants',
            'expected_result': 'Should resolve to Ahn Yujin variant with 80+ listeners'
        },
        {
            'name': 'BLACKPINK',
            'description': 'Control test - popular K-pop group',
            'expected_result': 'Should resolve quickly without errors'
        },
        {
            'name': 'Taylor Swift',
            'description': 'Control test - popular Western artist',
            'expected_result': 'Should resolve quickly without errors'
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_artists, 1):
        artist_name = test_case['name']
        description = test_case['description']
        expected = test_case['expected_result']
        
        print(f"\n{i}/{len(test_artists)}: Testing '{artist_name}'")
        print(f"   Description: {description}")
        print(f"   Expected: {expected}")
        
        start_time = time.time()
        
        try:
            # Test similar artists (this is where the errors occur)
            print("   🔍 Getting similar artists...")
            similar_artists = api.get_similar_artists(artist_name, limit=10)
            
            # Test artist info
            print("   📊 Getting artist info...")  
            artist_info = api.get_artist_info(artist_name)
            
            elapsed = time.time() - start_time
            
            if similar_artists:
                print(f"   ✅ Similar artists: Found {len(similar_artists)} artists")
                print(f"   📈 Top similar: {similar_artists[0]['name']} (match: {similar_artists[0]['match']:.3f})")
            else:
                print(f"   ❌ Similar artists: None found")
            
            if artist_info:
                listeners = artist_info.get('listeners', 0)
                canonical_name = artist_info.get('name', 'Unknown')
                print(f"   ✅ Artist info: {canonical_name} ({listeners:,} listeners)")
                
                # Check for metadata about resolution method
                if '_matched_variant' in artist_info:
                    print(f"   🎯 Matched variant: '{artist_info['_matched_variant']}'")
                    print(f"   🔧 Resolution method: {artist_info.get('_resolution_method', 'unknown')}")
            else:
                print(f"   ❌ Artist info: Not found")
                canonical_name = "Not found"
                listeners = 0
            
            print(f"   ⏱️  Time taken: {elapsed:.2f} seconds")
            
            # Determine result
            success = bool(similar_artists or artist_info)
            status = "✅ PASS" if success else "❌ FAIL"
            
            results.append({
                'artist': artist_name,
                'success': success,
                'similar_count': len(similar_artists) if similar_artists else 0,
                'listeners': listeners,
                'canonical_name': canonical_name,
                'time_taken': elapsed
            })
            
            print(f"   {status}")
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   ❌ ERROR: {e}")
            print(f"   ⏱️  Time taken: {elapsed:.2f} seconds")
            
            results.append({
                'artist': artist_name,
                'success': False,
                'similar_count': 0,
                'listeners': 0,
                'canonical_name': 'Error',
                'time_taken': elapsed,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    success_rate = (successful / total) * 100 if total > 0 else 0
    
    print(f"Overall Success Rate: {successful}/{total} ({success_rate:.1f}%)")
    print(f"Average Time per Artist: {sum(r['time_taken'] for r in results) / len(results):.2f}s")
    
    print(f"\nDetailed Results:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        artist = result['artist']
        canonical = result['canonical_name']
        listeners = result['listeners']
        time_taken = result['time_taken']
        
        print(f"  {status} {artist:<12} -> {canonical} ({listeners:,} listeners, {time_taken:.1f}s)")
        
        if 'error' in result:
            print(f"      Error: {result['error']}")
    
    # Specific checks for problematic artists
    print(f"\n🎯 Specific Issue Analysis:")
    
    ive_result = next((r for r in results if r['artist'] == 'ive'), None)
    if ive_result and ive_result['success']:
        if 'IVE' in ive_result['canonical_name'] and ive_result['listeners'] > 1000:
            print(f"  ✅ IVE issue RESOLVED: Found '{ive_result['canonical_name']}' with {ive_result['listeners']:,} listeners")
        else:
            print(f"  ⚠️  IVE concern: Found '{ive_result['canonical_name']}' but may not be correct artist")
    else:
        print(f"  ❌ IVE issue PERSISTS: Still cannot resolve")
    
    anyujin_result = next((r for r in results if r['artist'] == 'anyujin'), None)
    if anyujin_result and anyujin_result['success']:
        if anyujin_result['listeners'] > 50:  # Low threshold since this is a less popular artist
            print(f"  ✅ AnYujin issue RESOLVED: Found '{anyujin_result['canonical_name']}' with {anyujin_result['listeners']:,} listeners")
        else:
            print(f"  ⚠️  AnYujin concern: Found '{anyujin_result['canonical_name']}' but very low listener count")
    else:
        print(f"  ❌ AnYujin issue PERSISTS: Still cannot resolve")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if success_rate < 75:
        print(f"  • API errors are occurring - check error patterns in logs")
        print(f"  • Consider implementing retry logic with exponential backoff")
        print(f"  • May need to review artist name variant generation")
    
    if any(r['time_taken'] > 10 for r in results):
        print(f"  • Some queries are taking very long - consider timeout optimization")
        print(f"  • Implement more aggressive caching")
    
    print(f"\n🔧 Next Steps:")
    print(f"  1. If tests pass: The fetching system is working correctly")
    print(f"  2. If tests fail: Check API credentials and network connectivity")
    print(f"  3. If errors persist: Run with detailed logging to see exact API calls")
    
    return success_rate >= 75

if __name__ == "__main__":
    success = test_problematic_artists()
    exit(0 if success else 1)