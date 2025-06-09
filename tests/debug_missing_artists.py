"""
Debug Missing Artists: KISS OF LIFE and JEON SOMI
================================================

Investigates the exact name variants needed for these artists based on their Last.fm URLs:
- https://www.last.fm/music/Kiss+of+Life
- https://www.last.fm/music/JEON+SOMI
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import AppConfig
from lastfm_utils import LastfmAPI


def test_specific_artists():
    """Test specific failing artists with many variants."""
    print("🔍 Testing Specific Failing Artists")
    print("=" * 50)
    
    try:
        config = AppConfig('configurations.txt')
        lastfm_config = config.get_lastfm_config()
        
        lastfm_api = LastfmAPI(
            lastfm_config['api_key'],
            lastfm_config['api_secret'],
            lastfm_config['cache_dir']
        )
        
        # Test artists with many possible variants
        test_cases = {
            'KISS OF LIFE': [
                'KISS OF LIFE',
                'Kiss of Life',  # From URL
                'Kiss Of Life',
                'kiss of life',
                'KISS OF LIFE (band)',
                'Kiss of Life (band)',
                'KISS OF LIFE (K-pop)',
                'Kiss of Life (K-pop)',
                'KISS OF LIFE (group)',
                'Kiss of Life (group)',
                'KIOF',  # Common abbreviation
                'KOL',   # Another abbreviation
                'Kiss Of Life (키스 오브 라이프)',
                '키스 오브 라이프',
                'KISS OF LIFE (키스 오브 라이프)',
            ],
            'JEON SOMI': [
                'JEON SOMI',
                'Jeon Somi',  # From URL pattern
                'jeon somi',
                'SOMI',       # Single name
                'Somi',
                'somi',
                'JEON SOMI (soloist)',
                'Jeon Somi (soloist)',
                'JEON SOMI (K-pop)',
                'Jeon Somi (K-pop)',
                'JEON SOMI (singer)',
                'Jeon Somi (singer)',
                'Ennik Somi Douma',  # Real name
                'SOMI (전소미)',
                '전소미',
                'JEON SOMI (전소미)',
                'Jeon Somi (전소미)',
            ]
        }
        
        successful_variants = {}
        
        for artist_name, variants in test_cases.items():
            print(f"\n🎯 Testing: {artist_name}")
            print(f"   Testing {len(variants)} variants...")
            
            successful_variants[artist_name] = []
            
            for i, variant in enumerate(variants, 1):
                print(f"   {i:2d}. '{variant}'", end=" ")
                
                try:
                    # Test artist info first (faster)
                    artist_info = lastfm_api.get_artist_info(variant, use_enhanced_matching=False)
                    
                    if artist_info and artist_info.get('listeners', 0) > 100:  # Must have decent listener count
                        print(f"✅ INFO ({artist_info['listeners']:,} listeners)")
                        
                        # Test similar artists
                        similar = lastfm_api.get_similar_artists(variant, limit=5, use_enhanced_matching=False)
                        if similar:
                            print(f"      🎯 SIMILAR: {len(similar)} found")
                            successful_variants[artist_name].append({
                                'variant': variant,
                                'listeners': artist_info['listeners'],
                                'similar_count': len(similar),
                                'top_similar': [s['name'] for s in similar[:3]]
                            })
                        else:
                            print(f"      ⚠️  SIMILAR: None found")
                    else:
                        print(f"❌")
                        
                except Exception as e:
                    print(f"❌ ({str(e)[:30]})")
        
        # Summary
        print(f"\n📊 RESULTS SUMMARY")
        print("=" * 50)
        
        for artist_name, results in successful_variants.items():
            print(f"\n🎵 {artist_name}:")
            if results:
                print(f"   ✅ {len(results)} working variants found:")
                for result in results:
                    print(f"      '{result['variant']}' → {result['listeners']:,} listeners, {result['similar_count']} similar")
                    print(f"         Top similar: {', '.join(result['top_similar'])}")
            else:
                print(f"   ❌ No working variants found")
        
        return successful_variants
        
    except Exception as e:
        print(f"❌ Error testing artists: {e}")
        import traceback
        traceback.print_exc()
        return {}


def generate_comprehensive_variants(artist_name):
    """Generate comprehensive variants for any artist name."""
    variants = [artist_name]  # Original first
    
    name_clean = artist_name.strip()
    name_words = name_clean.split()
    
    # Basic case variations
    variants.extend([
        name_clean.title(),
        name_clean.lower(),
        name_clean.upper()
    ])
    
    # Add/remove "The"
    if name_clean.lower().startswith('the '):
        variants.append(name_clean[4:])
    else:
        variants.append(f"The {name_clean}")
    
    # Common suffixes for disambiguation
    suffixes = ['(band)', '(artist)', '(group)', '(singer)', '(K-pop)', '(soloist)']
    for suffix in suffixes:
        variants.extend([
            f"{name_clean} {suffix}",
            f"{name_clean.title()} {suffix}",
            f"{name_clean.lower()} {suffix}"
        ])
    
    # If multiple words, try abbreviations
    if len(name_words) > 1:
        # First letter abbreviation
        abbrev = ''.join(word[0].upper() for word in name_words if word)
        if len(abbrev) >= 2:
            variants.append(abbrev)
        
        # Two letter per word (if reasonable length)
        if len(name_words) <= 3:
            abbrev2 = ''.join(word[:2].upper() for word in name_words if word)
            if 2 <= len(abbrev2) <= 6:
                variants.append(abbrev2)
    
    # If it's a full name (First Last), try just first name
    if len(name_words) == 2 and all(word.isalpha() for word in name_words):
        variants.append(name_words[0])
        variants.append(name_words[0].upper())
        variants.append(name_words[0].lower())
    
    # Special patterns for specific cases
    name_upper = name_clean.upper()
    
    # KISS OF LIFE specific
    if 'KISS OF LIFE' in name_upper:
        variants.extend([
            'Kiss of Life',
            'KIOF',
            'KOL',
            'Kiss Of Life (키스 오브 라이프)',
            '키스 오브 라이프'
        ])
    
    # JEON SOMI specific  
    if 'JEON SOMI' in name_upper or 'SOMI' in name_upper:
        variants.extend([
            'Jeon Somi',
            'SOMI',
            'Somi',
            'Ennik Somi Douma',
            'SOMI (전소미)',
            '전소미',
            'JEON SOMI (전소미)'
        ])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_variants = []
    for variant in variants:
        if variant not in seen:
            seen.add(variant)
            unique_variants.append(variant)
    
    return unique_variants


def test_comprehensive_variant_generation():
    """Test the comprehensive variant generation."""
    print(f"\n🧪 Testing Comprehensive Variant Generation")
    print("=" * 50)
    
    test_artists = ['KISS OF LIFE', 'JEON SOMI', 'The Beatles', 'twenty one pilots']
    
    for artist in test_artists:
        variants = generate_comprehensive_variants(artist)
        print(f"\n🎵 {artist} → {len(variants)} variants:")
        for i, variant in enumerate(variants, 1):
            print(f"   {i:2d}. '{variant}'")


def main():
    print("=" * 70)
    print("MISSING ARTISTS DEBUG - COMPREHENSIVE INVESTIGATION")
    print("=" * 70)
    
    # Test specific failing artists
    results = test_specific_artists()
    
    # Test variant generation
    test_comprehensive_variant_generation()
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("=" * 50)
    
    if results:
        print("1. Add these working variants to the K-pop patterns:")
        for artist_name, variants in results.items():
            if variants:
                best_variants = [v['variant'] for v in variants[:3]]  # Top 3
                print(f"   '{artist_name}': {best_variants}")
    
    print("2. Implement comprehensive variant generation as fallback")
    print("3. Add fuzzy string matching for even better coverage")
    print("4. Consider URL-based validation as final check")


if __name__ == "__main__":
    # Change to main directory for proper file access
    original_dir = os.getcwd()
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(main_dir)
    
    try:
        main()
    finally:
        os.chdir(original_dir)