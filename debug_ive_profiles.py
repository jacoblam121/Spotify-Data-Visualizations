#!/usr/bin/env python3
"""
Debug IVE Last.fm profiles to see why we're getting 3K instead of 838K listeners
"""

from lastfm_utils import LastfmAPI
from config_loader import AppConfig

def debug_ive_profiles():
    """Debug IVE Last.fm profile discrepancy."""
    
    print("🔍 Debug IVE Last.fm Profile Discrepancy")
    print("=" * 45)
    
    config = AppConfig()
    lastfm_config = config.get_lastfm_config()
    api = LastfmAPI(lastfm_config['api_key'], lastfm_config['api_secret'])
    
    print("1️⃣ Testing all IVE variants for artist.getinfo:")
    print("-" * 50)
    
    ive_variants = [
        'IVE',
        'ive', 
        'Ive',
        'IVE (아이브)',
        '아이브',
        'IVE (girl group)',
        'IVE (K-pop)',
        'IVE 아이브'
    ]
    
    profiles_found = []
    
    for variant in ive_variants:
        print(f"\n🧪 Testing getinfo for '{variant}':")
        try:
            params = {'artist': variant}
            response = api._make_request('artist.getinfo', params)
            if response and 'artist' in response:
                artist = response['artist']
                canonical_name = artist['name']
                listeners = int(artist['stats']['listeners'])
                playcount = int(artist['stats']['playcount'])
                mbid = artist.get('mbid', '')
                
                print(f"   ✅ Found: '{canonical_name}'")
                print(f"   👥 Listeners: {listeners:,}")
                print(f"   🎵 Playcount: {playcount:,}")
                if mbid:
                    print(f"   🆔 MBID: {mbid}")
                
                # Test similarity count
                similar_params = {'artist': variant, 'limit': '10'}
                similar_response = api._make_request('artist.getsimilar', similar_params)
                similar_count = 0
                if similar_response and 'similarartists' in similar_response:
                    similar_data = similar_response['similarartists'].get('artist', [])
                    similar_count = len(similar_data) if isinstance(similar_data, list) else (1 if similar_data else 0)
                
                print(f"   🔗 Similar artists: {similar_count}")
                
                profiles_found.append({
                    'variant': variant,
                    'canonical_name': canonical_name,
                    'listeners': listeners,
                    'playcount': playcount,
                    'mbid': mbid,
                    'similar_count': similar_count
                })
                
            else:
                print(f"   ❌ Not found")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n2️⃣ Analysis of profiles found:")
    print("-" * 50)
    
    if profiles_found:
        # Group by canonical name
        canonical_groups = {}
        for profile in profiles_found:
            canonical = profile['canonical_name']
            if canonical not in canonical_groups:
                canonical_groups[canonical] = []
            canonical_groups[canonical].append(profile)
        
        print(f"Found {len(canonical_groups)} unique profiles:")
        
        for canonical_name, group in canonical_groups.items():
            listeners = group[0]['listeners']
            similar_count = group[0]['similar_count']
            variants = [p['variant'] for p in group]
            mbid = group[0]['mbid']
            
            marker = "🔥" if listeners > 100000 else "⚠️" if listeners > 10000 else "❓"
            
            print(f"\n{marker} '{canonical_name}'")
            print(f"   👥 Listeners: {listeners:,}")
            print(f"   🔗 Similar artists: {similar_count}")
            print(f"   📝 Accessible via: {variants}")
            if mbid:
                print(f"   🆔 MBID: {mbid}")
        
        # Find the highest listener profile
        highest_profile = max(profiles_found, key=lambda x: x['listeners'])
        print(f"\n🏆 HIGHEST LISTENER PROFILE:")
        print(f"   Name: '{highest_profile['canonical_name']}'")
        print(f"   Listeners: {highest_profile['listeners']:,}")
        print(f"   Access via: '{highest_profile['variant']}'")
        print(f"   Similar artists: {highest_profile['similar_count']}")
        
        if highest_profile['listeners'] != 3094:
            print(f"\n❗ DISCREPANCY FOUND:")
            print(f"   System is using 3,094 listeners")
            print(f"   But highest profile has {highest_profile['listeners']:,} listeners")
            print(f"   This suggests canonical resolution is choosing wrong profile!")
    
    print(f"\n3️⃣ Testing canonical resolution process:")
    print("-" * 50)
    
    # Test what canonical resolution actually chooses
    print("Running canonical resolution for 'IVE'...")
    try:
        results = api.get_similar_artists('IVE', limit=10, use_enhanced_matching=True)
        print(f"Enhanced matching returned: {len(results)} results")
        
        # Check metadata to see which variant was chosen
        if results and results[0].get('_matched_variant'):
            chosen_variant = results[0]['_matched_variant']
            chosen_listeners = results[0].get('_canonical_listeners', 'unknown')
            print(f"Canonical resolution chose: '{chosen_variant}' ({chosen_listeners:,} listeners)")
            
            # Compare with our manual findings
            manual_match = next((p for p in profiles_found if p['canonical_name'] == chosen_variant), None)
            if manual_match:
                print(f"Manual verification: {manual_match['listeners']:,} listeners")
                if manual_match['listeners'] != chosen_listeners:
                    print(f"⚠️  MISMATCH: Canonical says {chosen_listeners}, manual says {manual_match['listeners']}")
    
    except Exception as e:
        print(f"Error testing canonical resolution: {e}")

if __name__ == "__main__":
    debug_ive_profiles()