#!/usr/bin/env python3
"""
Test ANYUJIN-IVE Connection
===========================
Test the critical band member connection: ANYUJIN → IVE
This should be one of the strongest connections since ANYUJIN is a member of IVE.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI
from deezer_similarity_api import DeezerSimilarityAPI
from musicbrainz_similarity_api import MusicBrainzSimilarityAPI

def test_anyujin_ive_connection():
    """Test ANYUJIN-IVE connection across all APIs."""
    print("🎯 Testing ANYUJIN ↔ IVE Connection (Band Member Relationship)")
    print("=" * 65)
    
    # Initialize APIs
    try:
        config = AppConfig("configurations.txt")
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = None
        if lastfm_config['enabled'] and lastfm_config['api_key']:
            lastfm_api = LastfmAPI(
                lastfm_config['api_key'],
                lastfm_config['api_secret'],
                lastfm_config['cache_dir']
            )
            print("✅ Last.fm API initialized (PRIMARY)")
        
        deezer_api = DeezerSimilarityAPI()
        print("✅ Deezer API initialized (secondary)")
        
        musicbrainz_api = MusicBrainzSimilarityAPI()
        print("✅ MusicBrainz API initialized (relationships)")
        
    except Exception as e:
        print(f"❌ API initialization error: {e}")
        return
    
    # Test ANYUJIN → IVE
    print(f"\n🔍 Testing ANYUJIN → IVE:")
    
    # Last.fm test
    if lastfm_api:
        try:
            print(f"   🎶 Last.fm (PRIMARY):")
            lastfm_results = lastfm_api.get_similar_artists("ANYUJIN", limit=100)
            ive_found_lastfm = False
            ive_score_lastfm = 0.0
            
            for result in lastfm_results:
                if result['name'].lower() in ['ive', 'ive (아이브)', '아이브']:
                    ive_found_lastfm = True
                    ive_score_lastfm = result['match']
                    print(f"      ✅ FOUND: '{result['name']}' (score: {ive_score_lastfm:.3f})")
                    break
            
            if not ive_found_lastfm:
                print(f"      ❌ IVE not found in ANYUJIN's Last.fm results")
                # Show IVE-related results
                ive_related = [r for r in lastfm_results if 'ive' in r['name'].lower() or 'ive' in r['name']]
                if ive_related:
                    print(f"         IVE-related results found:")
                    for r in ive_related:
                        print(f"           • {r['name']} ({r['match']:.3f})")
                
        except Exception as e:
            print(f"      ❌ Last.fm error: {e}")
    
    # Deezer test
    try:
        print(f"   🎵 Deezer (secondary):")
        deezer_results = deezer_api.get_similar_artists("ANYUJIN", limit=100)
        ive_found_deezer = False
        ive_score_deezer = 0.0
        
        for result in deezer_results:
            if result['name'].lower() in ['ive', 'ive (아이브)', '아이브']:
                ive_found_deezer = True
                ive_score_deezer = result['match']
                print(f"      ✅ FOUND: '{result['name']}' (score: {ive_score_deezer:.3f})")
                break
        
        if not ive_found_deezer:
            print(f"      ❌ IVE not found in ANYUJIN's Deezer results")
            if deezer_results:
                print(f"         Top Deezer results: {', '.join([r['name'] for r in deezer_results[:5]])}")
            else:
                print(f"         No Deezer results returned for ANYUJIN")
        
    except Exception as e:
        print(f"      ❌ Deezer error: {e}")
    
    # MusicBrainz test
    try:
        print(f"   🎭 MusicBrainz (relationships):")
        mb_results = musicbrainz_api.get_relationship_based_similar_artists("ANYUJIN", limit=100)
        ive_found_mb = False
        ive_relationship_mb = ""
        
        for result in mb_results:
            if result['name'].lower() in ['ive', 'ive (아이브)', '아이브']:
                ive_found_mb = True
                ive_relationship_mb = result.get('musicbrainz_relationship', 'unknown')
                print(f"      ✅ FOUND: '{result['name']}' ({ive_relationship_mb})")
                break
        
        if not ive_found_mb:
            print(f"      ❌ IVE not found in ANYUJIN's MusicBrainz relationships")
            if mb_results:
                relationships_str = ', '.join([f"{r['name']} ({r.get('musicbrainz_relationship', 'unknown')})" for r in mb_results[:3]])
                print(f"         Top relationships: {relationships_str}")
            else:
                print(f"         No MusicBrainz relationships found for ANYUJIN")
        
    except Exception as e:
        print(f"      ❌ MusicBrainz error: {e}")
    
    # Test reverse direction: IVE → ANYUJIN
    print(f"\n🔄 Testing reverse direction: IVE → ANYUJIN:")
    
    # Last.fm reverse test
    if lastfm_api:
        try:
            print(f"   🎶 Last.fm reverse:")
            ive_results = lastfm_api.get_similar_artists("IVE", limit=100)
            anyujin_found_reverse = False
            anyujin_score_reverse = 0.0
            
            for result in ive_results:
                if 'anyujin' in result['name'].lower() or 'ahn yujin' in result['name'].lower():
                    anyujin_found_reverse = True
                    anyujin_score_reverse = result['match']
                    print(f"      ✅ FOUND: '{result['name']}' (score: {anyujin_score_reverse:.3f})")
                    break
            
            if not anyujin_found_reverse:
                print(f"      ❌ ANYUJIN not found in IVE's Last.fm results")
                # Show member-related results
                member_related = [r for r in ive_results if any(name in r['name'].lower() for name in ['yujin', 'wonyoung', 'gaeul', 'rei', 'liz', 'leeseo'])]
                if member_related:
                    print(f"         Member-related results:")
                    for r in member_related[:5]:
                        print(f"           • {r['name']} ({r['match']:.3f})")
                
        except Exception as e:
            print(f"      ❌ Last.fm reverse error: {e}")
    
    # Test alternative ANYUJIN spellings
    print(f"\n🔍 Testing alternative ANYUJIN spellings:")
    
    alternatives = ["An Yujin", "Ahn Yujin", "안유진", "Yujin", "Ahn Yu-jin"]
    
    for alt_name in alternatives:
        if lastfm_api:
            try:
                alt_results = lastfm_api.get_similar_artists(alt_name, limit=50)
                if alt_results:
                    # Check for IVE in results
                    ive_in_alt = any('ive' == r['name'].lower() for r in alt_results)
                    if ive_in_alt:
                        ive_result = next(r for r in alt_results if 'ive' == r['name'].lower())
                        print(f"   ✅ '{alt_name}' → IVE: {ive_result['match']:.3f}")
                    else:
                        # Check for IVE-related
                        ive_related = [r for r in alt_results if 'ive' in r['name'].lower()]
                        if ive_related:
                            ive_related_str = ', '.join([f"{r['name']} ({r['match']:.3f})" for r in ive_related[:3]])
                            print(f"   🔍 '{alt_name}': IVE-related found: {ive_related_str}")
                        else:
                            print(f"   ❌ '{alt_name}': No IVE connection")
                else:
                    print(f"   ❌ '{alt_name}': Not found in Last.fm")
            except Exception as e:
                print(f"   ❌ '{alt_name}': Error - {e}")
    
    # Summary
    print(f"\n📊 ANYUJIN-IVE Connection Summary:")
    print("=" * 35)
    print(f"This should be a STRONG connection since ANYUJIN is a member of IVE.")
    print(f"If connections are missing, this indicates:")
    print(f"1. API data quality issues for newer K-pop groups")
    print(f"2. Need for manual member-to-group connections")
    print(f"3. Importance of MusicBrainz relationship data")

if __name__ == "__main__":
    test_anyujin_ive_connection()