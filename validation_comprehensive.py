#!/usr/bin/env python3
"""
Comprehensive Validation of Phase A.2 Verification System
==========================================================
Tests the verification pipeline at scale to identify edge cases and validate performance.
"""

import sys
import json
import time
import logging
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from artist_verification import ArtistVerifier
from lastfm_utils import LastfmAPI
from config_loader import AppConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

class VerificationValidator:
    """Comprehensive validator for the verification system."""
    
    def __init__(self):
        """Initialize validator with Last.fm data."""
        print("🔍 Comprehensive Verification Validator")
        print("=" * 50)
        
        # Initialize verifier
        self.verifier = ArtistVerifier("lastfm_data.csv")
        
        # Initialize Last.fm API
        try:
            config = AppConfig()
            lastfm_config = config.get_lastfm_config()
            
            if lastfm_config['enabled'] and lastfm_config['api_key']:
                self.lastfm_api = LastfmAPI(
                    lastfm_config['api_key'],
                    lastfm_config['api_secret'],
                    lastfm_config['cache_dir']
                )
                print("✅ Last.fm API initialized")
            else:
                self.lastfm_api = None
                print("⚠️  Last.fm API not available")
                
        except Exception as e:
            self.lastfm_api = None
            print(f"⚠️  Could not initialize Last.fm API: {e}")
        
        # Statistics tracking
        self.stats = {
            'total_verifications': 0,
            'tier_distribution': defaultdict(int),
            'confidence_scores': [],
            'verification_times': [],
            'mbid_coverage': {'with_mbid': 0, 'without_mbid': 0},
            'problematic_artists': [],
            'track_evidence_stats': []
        }
    
    def validate_tier_distribution(self, sample_artists: List[str], max_candidates: int = 5) -> Dict:
        """
        Validate how often each verification tier is used.
        
        Args:
            sample_artists: List of artist names to test
            max_candidates: Maximum candidates to test per artist
        """
        print(f"\n🧪 Testing Tier Distribution ({len(sample_artists)} artists)")
        print("=" * 50)
        
        results = []
        
        for i, artist in enumerate(sample_artists, 1):
            if i % 10 == 0:
                print(f"   Progress: {i}/{len(sample_artists)} artists tested")
            
            start_time = time.time()
            
            try:
                # Get candidates from API
                candidates = self._get_test_candidates(artist, max_candidates)
                
                if not candidates:
                    continue
                
                # Run verification
                result = self.verifier.verify_artist_candidates(artist, candidates, self.lastfm_api)
                
                verification_time = time.time() - start_time
                
                # Track statistics
                self.stats['total_verifications'] += 1
                self.stats['tier_distribution'][result.verification_method] += 1
                self.stats['confidence_scores'].append(result.confidence_score)
                self.stats['verification_times'].append(verification_time)
                
                # Check MBID coverage in candidates
                candidates_with_mbid = sum(1 for c in candidates if c.get('mbid', '').strip())
                self.stats['mbid_coverage']['with_mbid'] += candidates_with_mbid
                self.stats['mbid_coverage']['without_mbid'] += len(candidates) - candidates_with_mbid
                
                # Track problematic cases (low confidence)
                if result.confidence_score < 0.5:
                    self.stats['problematic_artists'].append({
                        'artist': artist,
                        'confidence': result.confidence_score,
                        'method': result.verification_method,
                        'chosen': result.chosen_profile.get('name', 'Unknown')
                    })
                
                # Track track evidence for detailed analysis
                if hasattr(result.debug_info, 'get') and 'track_evidence' in result.debug_info:
                    self.stats['track_evidence_stats'].append(result.debug_info['track_evidence'])
                
                results.append({
                    'artist': artist,
                    'confidence': result.confidence_score,
                    'method': result.verification_method,
                    'time': verification_time,
                    'candidates_with_mbid': candidates_with_mbid,
                    'total_candidates': len(candidates)
                })
                
            except Exception as e:
                logger.warning(f"Error testing {artist}: {e}")
                continue
        
        return results
    
    def analyze_confidence_distribution(self) -> Dict:
        """Analyze the distribution of confidence scores."""
        print(f"\n📊 Confidence Score Analysis")
        print("=" * 50)
        
        if not self.stats['confidence_scores']:
            print("❌ No confidence scores to analyze")
            return {}
        
        scores = self.stats['confidence_scores']
        
        # Calculate percentiles
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        
        percentiles = {
            'min': sorted_scores[0],
            'p25': sorted_scores[n//4],
            'p50': sorted_scores[n//2],
            'p75': sorted_scores[3*n//4],
            'max': sorted_scores[-1],
            'mean': sum(scores) / len(scores)
        }
        
        # Bin the scores
        bins = {
            '0.95-1.00 (MBID)': len([s for s in scores if s >= 0.95]),
            '0.85-0.94 (Strong Track)': len([s for s in scores if 0.85 <= s < 0.95]),
            '0.70-0.84 (Track-based)': len([s for s in scores if 0.70 <= s < 0.85]),
            '0.50-0.69 (Weak)': len([s for s in scores if 0.50 <= s < 0.70]),
            '0.00-0.49 (Poor)': len([s for s in scores if s < 0.50])
        }
        
        print("📈 Confidence Score Distribution:")
        for bin_range, count in bins.items():
            percentage = (count / len(scores)) * 100
            print(f"   {bin_range}: {count:3d} ({percentage:5.1f}%)")
        
        print(f"\n📋 Percentiles:")
        for label, value in percentiles.items():
            print(f"   {label.upper()}: {value:.3f}")
        
        return {'percentiles': percentiles, 'bins': bins}
    
    def analyze_tier_effectiveness(self) -> Dict:
        """Analyze how effective each verification tier is."""
        print(f"\n⚡ Tier Effectiveness Analysis")
        print("=" * 50)
        
        total = self.stats['total_verifications']
        if total == 0:
            print("❌ No verifications to analyze")
            return {}
        
        print("🎯 Verification Method Distribution:")
        for method, count in self.stats['tier_distribution'].items():
            percentage = (count / total) * 100
            print(f"   {method}: {count:3d} ({percentage:5.1f}%)")
        
        # Analyze MBID coverage
        mbid_stats = self.stats['mbid_coverage']
        total_candidates = mbid_stats['with_mbid'] + mbid_stats['without_mbid']
        
        if total_candidates > 0:
            mbid_coverage = (mbid_stats['with_mbid'] / total_candidates) * 100
            print(f"\n🔗 MBID Coverage in API Candidates:")
            print(f"   With MBID: {mbid_stats['with_mbid']} ({mbid_coverage:.1f}%)")
            print(f"   Without MBID: {mbid_stats['without_mbid']} ({100-mbid_coverage:.1f}%)")
        
        return self.stats['tier_distribution']
    
    def analyze_performance(self) -> Dict:
        """Analyze verification performance."""
        print(f"\n⚡ Performance Analysis")
        print("=" * 50)
        
        times = self.stats['verification_times']
        if not times:
            print("❌ No timing data to analyze")
            return {}
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"⏱️  Verification Times:")
        print(f"   Average: {avg_time:.3f}s")
        print(f"   Maximum: {max_time:.3f}s")
        print(f"   Minimum: {min_time:.3f}s")
        print(f"   Total tests: {len(times)}")
        
        # Performance categories
        fast_count = len([t for t in times if t < 0.1])
        medium_count = len([t for t in times if 0.1 <= t < 0.5])
        slow_count = len([t for t in times if t >= 0.5])
        
        print(f"\n⚡ Performance Distribution:")
        print(f"   Fast (<0.1s): {fast_count} ({fast_count/len(times)*100:.1f}%)")
        print(f"   Medium (0.1-0.5s): {medium_count} ({medium_count/len(times)*100:.1f}%)")
        print(f"   Slow (>0.5s): {slow_count} ({slow_count/len(times)*100:.1f}%)")
        
        return {'avg_time': avg_time, 'max_time': max_time, 'min_time': min_time}
    
    def identify_problematic_cases(self) -> List[Dict]:
        """Identify artists with consistently low confidence scores."""
        print(f"\n🚨 Problematic Cases Analysis")
        print("=" * 50)
        
        problematic = self.stats['problematic_artists']
        
        if not problematic:
            print("✅ No problematic cases found (all confidence > 0.5)")
            return []
        
        print(f"⚠️  Found {len(problematic)} low-confidence verifications:")
        
        for case in problematic[:10]:  # Show top 10
            print(f"   {case['artist']}: {case['confidence']:.3f} ({case['method']}) -> {case['chosen']}")
        
        if len(problematic) > 10:
            print(f"   ... and {len(problematic) - 10} more")
        
        return problematic
    
    def _get_test_candidates(self, artist: str, max_candidates: int) -> List[Dict]:
        """Get test candidates for an artist."""
        if not self.lastfm_api:
            # Return mock candidates if no API
            return [
                {'name': artist, 'listeners': 100000, 'mbid': '', 'url': 'mock1'},
                {'name': f"{artist}_variant", 'listeners': 50000, 'mbid': '', 'url': 'mock2'}
            ]
        
        try:
            # Use enhanced matching to get realistic candidates
            candidates = []
            
            # Get self info
            self_info = self.lastfm_api.get_artist_info(artist, use_enhanced_matching=True)
            if self_info:
                candidates.append({
                    'name': self_info.get('name', artist),
                    'listeners': int(self_info.get('listeners', 0)),
                    'mbid': self_info.get('mbid', ''),
                    'url': self_info.get('url', '')
                })
            
            # Get similar artists for additional candidates
            similar = self.lastfm_api.get_similar_artists(artist, use_enhanced_matching=True)
            for sim_artist in similar[:max_candidates-1]:
                candidates.append({
                    'name': sim_artist.get('name', ''),
                    'listeners': int(sim_artist.get('_canonical_listeners', 0)),
                    'mbid': sim_artist.get('mbid', ''),
                    'url': sim_artist.get('url', '')
                })
            
            return candidates[:max_candidates]
            
        except Exception as e:
            logger.debug(f"Error getting candidates for {artist}: {e}")
            return []
    
    def run_comprehensive_validation(self, sample_size: int = 50) -> Dict:
        """Run the complete validation suite."""
        print(f"🚀 Starting Comprehensive Validation (sample size: {sample_size})")
        print("=" * 60)
        
        # Get sample artists from user data
        sample_artists = list(self.verifier.user_tracks_by_artist.keys())[:sample_size]
        
        print(f"📊 Test Dataset:")
        print(f"   Total artists in user data: {len(self.verifier.user_tracks_by_artist)}")
        print(f"   Artists with MBIDs: {len(self.verifier.user_artist_mbids)}")
        print(f"   Sample size for testing: {len(sample_artists)}")
        
        # Run tier distribution test
        results = self.validate_tier_distribution(sample_artists)
        
        # Analyze results
        confidence_analysis = self.analyze_confidence_distribution()
        tier_analysis = self.analyze_tier_effectiveness()
        performance_analysis = self.analyze_performance()
        problematic_cases = self.identify_problematic_cases()
        
        # Summary
        print(f"\n🏁 Validation Complete")
        print("=" * 50)
        
        mbid_tier_count = self.stats['tier_distribution'].get('MBID_MATCH', 0)
        track_tier_count = self.stats['tier_distribution'].get('STRONG_TRACK_MATCH', 0)
        total_high_confidence = mbid_tier_count + track_tier_count
        
        if self.stats['total_verifications'] > 0:
            high_conf_percentage = (total_high_confidence / self.stats['total_verifications']) * 100
            print(f"🎯 High-Confidence Matches: {total_high_confidence}/{self.stats['total_verifications']} ({high_conf_percentage:.1f}%)")
        
        # Check if system is ready for network generation
        ready_for_network = (
            self.stats['total_verifications'] > 10 and
            high_conf_percentage > 30 and  # At least 30% high confidence
            len(problematic_cases) < self.stats['total_verifications'] * 0.3  # Less than 30% problematic
        )
        
        print(f"🌐 Ready for Network Generation: {'✅ YES' if ready_for_network else '❌ NO'}")
        
        return {
            'ready_for_network': ready_for_network,
            'total_tests': self.stats['total_verifications'],
            'high_confidence_percentage': high_conf_percentage if self.stats['total_verifications'] > 0 else 0,
            'problematic_count': len(problematic_cases),
            'confidence_analysis': confidence_analysis,
            'tier_analysis': tier_analysis,
            'performance_analysis': performance_analysis
        }

def main():
    """Main validation runner."""
    validator = VerificationValidator()
    
    # Run validation with reasonable sample size
    sample_size = 30  # Adjust based on API limits and time constraints
    
    results = validator.run_comprehensive_validation(sample_size)
    
    # Save results for analysis
    output_file = Path(__file__).parent / "validation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📝 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()