#!/usr/bin/env python3
"""
Manual Artist Verification CLI Tool
====================================
Interactive tool for manually verifying artist resolution decisions.
Helps validate the verification system and tune scoring parameters.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from artist_verification import ArtistVerifier
from lastfm_utils import LastfmAPI
from config_loader import AppConfig

class ManualVerificationTool:
    """Interactive tool for manual artist verification."""
    
    def __init__(self):
        """Initialize the manual verification tool."""
        print("🔍 Manual Artist Verification Tool")
        print("=" * 40)
        
        # Initialize verifier with Last.fm data
        self.verifier = ArtistVerifier("lastfm_data.csv")
        
        # Initialize Last.fm API for fetching candidates
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
                print("⚠️  Last.fm API not available - using mock data only")
                
        except Exception as e:
            self.lastfm_api = None
            print(f"⚠️  Could not initialize Last.fm API: {e}")
    
    def verify_artist_interactive(self, artist_name: str):
        """
        Interactively verify an artist with detailed output and user feedback.
        
        Args:
            artist_name: Name of artist to verify
        """
        print(f"\n🎯 Verifying Artist: '{artist_name}'")
        print("=" * 50)
        
        # Step 1: Get candidates from Last.fm
        candidates = self._get_artist_candidates(artist_name)
        
        if not candidates:
            print("❌ No candidates found")
            return
        
        print(f"📊 Found {len(candidates)} candidate profiles:")
        print()
        
        # Step 2: Show all candidates
        for i, candidate in enumerate(candidates, 1):
            name = candidate.get('name', 'Unknown')
            listeners = candidate.get('listeners', 0)
            url = candidate.get('url', '')
            mbid = candidate.get('mbid', '')
            
            print(f"[{i}] {name}")
            print(f"    Listeners: {listeners:,}")
            if mbid:
                print(f"    MBID: {mbid}")
            print(f"    URL: {url}")
            print()
        
        # Step 3: Run verification
        print("🤖 Running automatic verification...")
        result = self.verifier.verify_artist_candidates(
            artist_name, candidates, self.lastfm_api
        )
        
        # Step 4: Show detailed results
        self._display_verification_results(result)
        
        # Step 5: Get user feedback
        self._get_user_feedback(artist_name, candidates, result)
    
    def _get_artist_candidates(self, artist_name: str) -> List[Dict]:
        """Get candidate profiles for an artist."""
        if not self.lastfm_api:
            print("⚠️  Using mock candidates (no Last.fm API)")
            return self._get_mock_candidates(artist_name)
        
        try:
            # Use the enhanced matching system that already works in the network generator
            # This gets better candidates than raw search
            similar_artists = self.lastfm_api.get_similar_artists(artist_name, use_enhanced_matching=True)
            
            candidates = []
            
            # Add the query artist itself as first candidate (most important)
            try:
                self_info = self.lastfm_api.get_artist_info(artist_name, use_enhanced_matching=True)
                if self_info:
                    candidates.append({
                        'name': self_info.get('name', artist_name),
                        'listeners': int(self_info.get('listeners', 0)),
                        'playcount': int(self_info.get('playcount', 0)),
                        'url': self_info.get('url', ''),
                        'mbid': self_info.get('mbid', ''),
                        'source': 'self_lookup'
                    })
            except Exception as e:
                print(f"⚠️  Could not get self info for {artist_name}: {e}")
            
            # Add similar artists as additional candidates (for comparison)
            for artist in similar_artists[:5]:  # Limit to top 5 similar
                candidates.append({
                    'name': artist.get('name', ''),
                    'listeners': int(artist.get('_canonical_listeners', 0)),
                    'playcount': int(artist.get('playcount', 0)),
                    'url': artist.get('url', ''),
                    'mbid': artist.get('mbid', ''),
                    'source': 'similar_artist'
                })
            
            if not candidates:
                print("⚠️  No candidates found via enhanced matching, trying basic search...")
                return self._try_basic_search(artist_name)
            
            return candidates
            
        except Exception as e:
            print(f"❌ Error fetching candidates: {e}")
            return self._get_mock_candidates(artist_name)
    
    def _try_basic_search(self, artist_name: str) -> List[Dict]:
        """Try basic search as fallback."""
        try:
            # Sanitize the search query for special characters
            clean_query = artist_name.replace('*', '').strip()
            if not clean_query:
                clean_query = artist_name
            
            search_results = self.lastfm_api.search_artists(clean_query, limit=5)
            
            candidates = []
            for artist in search_results:
                candidates.append({
                    'name': artist.get('name', ''),
                    'listeners': int(artist.get('listeners', 0)),
                    'playcount': int(artist.get('playcount', 0)),
                    'url': artist.get('url', ''),
                    'mbid': artist.get('mbid', ''),
                    'source': 'basic_search'
                })
            
            return candidates
            
        except Exception as e:
            print(f"❌ Basic search also failed: {e}")
            return self._get_mock_candidates(artist_name)
    
    def _get_mock_candidates(self, artist_name: str) -> List[Dict]:
        """Get mock candidates for testing when API is unavailable."""
        # Check if we have a golden test case for this artist
        golden_files_dir = Path(__file__).parent / "tests" / "golden_files"
        
        test_files = {
            "*luna": "luna_test_case.json",
            "*Luna": "luna_test_case.json",
            "*LUNA": "luna_test_case.json",
            "luna": "luna_test_case.json", 
            "YOASOBI": "yoasobi_test_case.json",
            "yoasobi": "yoasobi_test_case.json",
            "IVE": "ive_test_case.json",
            "ive": "ive_test_case.json"
        }
        
        test_file = test_files.get(artist_name)
        if not test_file:
            test_file = test_files.get(artist_name.lower())
        
        if test_file and (golden_files_dir / test_file).exists():
            try:
                with open(golden_files_dir / test_file, 'r', encoding='utf-8') as f:
                    test_case = json.load(f)
                print(f"✅ Using golden test case: {test_file}")
                return test_case["mock_candidates"]
            except Exception as e:
                print(f"⚠️  Could not load test case: {e}")
        
        # Return realistic mock data for unknown artists
        print(f"⚠️  No test case for '{artist_name}', using generic mock data")
        return [
            {
                'name': artist_name,
                'listeners': 100000,
                'url': f'https://last.fm/music/{artist_name}',
                'mbid': '',
                'source': 'mock_fallback'
            },
            {
                'name': artist_name.lower(),
                'listeners': 50000,
                'url': f'https://last.fm/music/{artist_name.lower()}',
                'mbid': '',
                'source': 'mock_fallback'
            }
        ]
    
    def _display_verification_results(self, result):
        """Display detailed verification results."""
        print("🔬 Verification Results:")
        print("-" * 25)
        
        chosen = result.chosen_profile
        print(f"✅ Selected: {chosen.get('name', 'Unknown')}")
        print(f"   Listeners: {chosen.get('listeners', 0):,}")
        print(f"   Confidence: {result.confidence_score:.3f}")
        print(f"   Method: {result.verification_method}")
        
        if result.track_matches:
            print(f"   Track matches: {len(result.track_matches)}")
            for match in result.track_matches[:3]:  # Show first 3
                print(f"     '{match.user_track}' ↔ '{match.api_track}' ({match.similarity:.2f})")
        
        # Show scoring breakdown for all candidates
        print(f"\n📊 All Candidates Scored:")
        for i, candidate in enumerate(result.all_candidates, 1):
            name = candidate.get('name', 'Unknown')
            listeners = candidate.get('listeners', 0)
            
            if candidate == chosen:
                marker = "👑"
            else:
                marker = f"[{i}]"
            
            print(f"   {marker} {name} ({listeners:,} listeners)")
        
        if result.debug_info:
            print(f"\n🔧 Debug Info:")
            debug = result.debug_info
            if 'track_score' in debug:
                print(f"   Track score: {debug['track_score']:.3f}")
            if 'name_score' in debug:
                print(f"   Name score: {debug['name_score']:.3f}")
            if 'listener_score' in debug:
                print(f"   Listener score: {debug['listener_score']:.3f}")
    
    def _get_user_feedback(self, artist_name: str, candidates: List[Dict], result):
        """Get user feedback on the verification result."""
        print(f"\n❓ Is this the correct artist profile?")
        print(f"   Selected: {result.chosen_profile.get('name', 'Unknown')}")
        print(f"   Confidence: {result.confidence_score:.3f}")
        
        while True:
            response = input("\n[Y]es / [N]o / [O]verride / [S]kip: ").strip().lower()
            
            if response in ['y', 'yes']:
                print("✅ User confirmed: Selection is correct")
                self._log_feedback(artist_name, result, "correct", None)
                break
            elif response in ['n', 'no']:
                print("❌ User rejected: Selection is incorrect")
                self._ask_for_correct_choice(artist_name, candidates, result)
                break
            elif response in ['o', 'override']:
                self._manual_override(artist_name, candidates, result)
                break
            elif response in ['s', 'skip']:
                print("⏭️  Skipped feedback")
                break
            else:
                print("Please enter Y, N, O, or S")
    
    def _ask_for_correct_choice(self, artist_name: str, candidates: List[Dict], result):
        """Ask user which candidate is correct when they reject the selection."""
        print("\n📝 Which candidate should have been selected?")
        
        for i, candidate in enumerate(candidates, 1):
            name = candidate.get('name', 'Unknown')
            listeners = candidate.get('listeners', 0)
            print(f"   [{i}] {name} ({listeners:,} listeners)")
        
        print(f"   [0] None of the above")
        
        while True:
            try:
                choice = int(input(f"\nEnter choice (0-{len(candidates)}): ").strip())
                
                if choice == 0:
                    print("User indicated none of the candidates are correct")
                    self._log_feedback(artist_name, result, "none_correct", None)
                    break
                elif 1 <= choice <= len(candidates):
                    correct_candidate = candidates[choice - 1]
                    print(f"✅ User selected: {correct_candidate.get('name', 'Unknown')}")
                    self._log_feedback(artist_name, result, "incorrect", correct_candidate)
                    break
                else:
                    print(f"Please enter a number between 0 and {len(candidates)}")
            except ValueError:
                print("Please enter a valid number")
    
    def _manual_override(self, artist_name: str, candidates: List[Dict], result):
        """Allow user to manually override the selection."""
        print(f"\n🎛️  Manual Override - Select the correct candidate:")
        
        for i, candidate in enumerate(candidates, 1):
            name = candidate.get('name', 'Unknown')
            listeners = candidate.get('listeners', 0)
            print(f"   [{i}] {name} ({listeners:,} listeners)")
        
        while True:
            try:
                choice = int(input(f"\nEnter choice (1-{len(candidates)}): ").strip())
                
                if 1 <= choice <= len(candidates):
                    override_candidate = candidates[choice - 1]
                    print(f"🎯 Override: Selected {override_candidate.get('name', 'Unknown')}")
                    self._log_feedback(artist_name, result, "override", override_candidate)
                    break
                else:
                    print(f"Please enter a number between 1 and {len(candidates)}")
            except ValueError:
                print("Please enter a valid number")
    
    def _log_feedback(self, artist_name: str, result, feedback_type: str, correct_candidate: Optional[Dict]):
        """Log user feedback for analysis."""
        feedback_log = {
            'timestamp': str(Path(__file__).stat().st_mtime),  # Simple timestamp
            'artist_name': artist_name,
            'system_choice': result.chosen_profile.get('name', 'Unknown'),
            'system_confidence': result.confidence_score,
            'system_method': result.verification_method,
            'feedback_type': feedback_type,
            'user_choice': correct_candidate.get('name', 'None') if correct_candidate else 'None',
            'track_matches': [match.to_dict() if hasattr(match, 'to_dict') else str(match) for match in result.track_matches],
            'debug_info': result.debug_info
        }
        
        # Save to feedback log file
        feedback_file = Path(__file__).parent / "verification_feedback.jsonl"
        
        with open(feedback_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback_log) + '\n')
        
        print(f"📝 Feedback logged to {feedback_file}")

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Manual Artist Verification Tool")
    parser.add_argument("artist", nargs='?', help="Artist name to verify")
    parser.add_argument("--test", action="store_true", help="Run with test cases")
    parser.add_argument("--batch", help="File with list of artists to verify")
    
    args = parser.parse_args()
    
    tool = ManualVerificationTool()
    
    if args.test:
        # Run with known problematic test cases
        test_artists = ["*luna", "YOASOBI", "IVE"]
        for artist in test_artists:
            tool.verify_artist_interactive(artist)
            
    elif args.batch:
        # Batch processing from file
        try:
            with open(args.batch, 'r', encoding='utf-8') as f:
                artists = [line.strip() for line in f if line.strip()]
            
            for artist in artists:
                tool.verify_artist_interactive(artist)
                
        except FileNotFoundError:
            print(f"❌ Batch file not found: {args.batch}")
            sys.exit(1)
            
    elif args.artist:
        # Single artist verification
        tool.verify_artist_interactive(args.artist)
        
    else:
        # Interactive mode
        print("\n🎤 Interactive Mode - Enter artist names to verify")
        print("Type 'quit' to exit")
        
        while True:
            try:
                artist_name = input("\nArtist name: ").strip()
                
                if artist_name.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                if artist_name:
                    tool.verify_artist_interactive(artist_name)
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break

if __name__ == "__main__":
    main()