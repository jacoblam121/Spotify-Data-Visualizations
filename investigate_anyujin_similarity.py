#!/usr/bin/env python3
"""
Investigate why the high-listener AnYujin profile has no similarity data
"""

from lastfm_utils import LastfmAPI
from config_loader import AppConfig

def investigate_anyujin_similarity():
    """Investigate the AnYujin similarity data issue."""
    
    print("🔍 Investigating AnYujin Similarity Data Issue")
    print("=" * 50)
    
    config = AppConfig()
    lastfm_config = config.get_lastfm_config()
    api = LastfmAPI(lastfm_config['api_key'], lastfm_config['api_secret'])
    
    print("1️⃣ Testing all ANYUJIN variants for artist info and similarity:")
    print("-" * 50)
    
    variants = [
        'ANYUJIN',
        'AnYujin', 
        'Ahn Yujin',
        'An Yujin', 
        '안유진',
        'ANYUJIN (IVE)',
        'Yujin'
    ]
    
    profiles = []
    
    for variant in variants:
        print(f"\n🧪 Testing '{variant}':")
        
        # Get artist info
        try:
            info_params = {'artist': variant}
            info_response = api._make_request('artist.getinfo', info_params)
            
            if info_response and 'artist' in info_response:
                artist = info_response['artist']
                canonical_name = artist['name']
                listeners = int(artist['stats']['listeners'])
                playcount = int(artist['stats']['playcount'])
                mbid = artist.get('mbid', '')
                
                print(f"   ✅ Exists: '{canonical_name}'")
                print(f"   👥 Listeners: {listeners:,}")
                print(f"   🎵 Playcount: {playcount:,}")
                if mbid:
                    print(f"   🆔 MBID: {mbid}")
                
                # Test similarity
                similar_params = {'artist': variant, 'limit': '10'}
                similar_response = api._make_request('artist.getsimilar', similar_params)
                
                similar_count = 0
                similar_artists = []
                
                if similar_response and 'similarartists' in similar_response:
                    similar_data = similar_response['similarartists'].get('artist', [])
                    if isinstance(similar_data, list):
                        similar_count = len(similar_data)
                        similar_artists = [s['name'] for s in similar_data[:3]]
                    elif similar_data:  # Single artist as dict
                        similar_count = 1
                        similar_artists = [similar_data['name']]
                
                print(f"   🔗 Similar artists: {similar_count}")
                if similar_artists:
                    print(f"   📝 Sample: {similar_artists}")
                
                profiles.append({
                    'variant': variant,
                    'canonical_name': canonical_name,
                    'listeners': listeners,
                    'playcount': playcount,
                    'mbid': mbid,
                    'similar_count': similar_count,
                    'similar_artists': similar_artists
                })
                
            else:
                print(f"   ❌ Not found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n2️⃣ Analysis Summary:")
    print("-" * 50)
    
    if profiles:
        # Group by canonical name to see which variants point to the same artist
        canonical_groups = {}
        for profile in profiles:
            canonical = profile['canonical_name']
            if canonical not in canonical_groups:
                canonical_groups[canonical] = []
            canonical_groups[canonical].append(profile)
        
        print(f"Found {len(canonical_groups)} unique artist profiles:")
        
        for canonical_name, group in canonical_groups.items():
            listeners = group[0]['listeners']
            similar_count = group[0]['similar_count']
            variants = [p['variant'] for p in group]
            
            print(f"\n🎯 '{canonical_name}' ({listeners:,} listeners, {similar_count} similar)")
            print(f"   Accessible via: {variants}")
            
            if similar_count == 0:
                print(f"   ⚠️  NO SIMILARITY DATA - investigating why...")
                
                # Try different approaches to get similarity
                test_methods = [
                    ('Direct artist name', canonical_name),
                    ('Original query', group[0]['variant'])
                ]
                if group[0]['mbid']:
                    test_methods.append(('MBID query', group[0]['mbid']))
                
                for method_name, query in test_methods:
                    if query is None:
                        continue
                        
                    try:
                        if method_name == 'MBID query':
                            # Test MBID-based similarity lookup
                            similar_params = {'mbid': query, 'limit': '10'}
                        else:
                            similar_params = {'artist': query, 'limit': '10'}
                        
                        similar_response = api._make_request('artist.getsimilar', similar_params)
                        
                        if similar_response and 'similarartists' in similar_response:
                            similar_data = similar_response['similarartists'].get('artist', [])
                            count = len(similar_data) if isinstance(similar_data, list) else (1 if similar_data else 0)
                            print(f"      {method_name}: {count} similar artists")
                        else:
                            print(f"      {method_name}: No data or error")
                            
                    except Exception as e:
                        print(f"      {method_name}: Error - {e}")
        
        # Find the profile that should be used (highest listeners + has similarity data)
        profiles_with_similarity = [p for p in profiles if p['similar_count'] > 0]
        
        if profiles_with_similarity:
            best_profile = max(profiles_with_similarity, key=lambda x: x['listeners'])
            print(f"\n🏆 RECOMMENDED PROFILE:")
            print(f"   Name: '{best_profile['canonical_name']}'")
            print(f"   Listeners: {best_profile['listeners']:,}")
            print(f"   Similar artists: {best_profile['similar_count']}")
            print(f"   Access via: '{best_profile['variant']}'")
        else:
            print(f"\n❌ NO PROFILES WITH SIMILARITY DATA FOUND")
            highest_listeners = max(profiles, key=lambda x: x['listeners'])
            print(f"   Highest listener profile: '{highest_listeners['canonical_name']}' ({highest_listeners['listeners']:,})")
            print(f"   But this profile has no similarity data")

if __name__ == "__main__":
    investigate_anyujin_similarity()