#!/usr/bin/env python3
"""
Similarity Data Debug Suite
===========================

Interactive testing tool for debugging Last.fm similarity data issues.
Helps identify why certain artist connections are missing.
"""

import json
import os
import sys
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

# Add project root to path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from lastfm_utils import LastfmAPI
    from config_loader import AppConfig
    from artist_data_fetcher import EnhancedArtistDataFetcher
except ImportError as e:
    print(f"⚠️  Could not import project modules: {e}")
    print("Make sure you're running from the project root directory")


@dataclass
class SimilarityResult:
    """Container for similarity test results"""
    artist: str
    similar_artists: List[Dict]
    success: bool
    error: Optional[str] = None
    cache_hit: bool = False
    api_response_time: float = 0.0


class SimilarityDebugger:
    """Debug tool for similarity data issues"""
    
    def __init__(self):
        self.config = None
        self.lastfm_api = None
        self.artist_fetcher = None
        self.cache_dir = None
        
        # Load configuration
        self.load_config()
        
        # Test cases for known issues
        self.problem_cases = [
            ("TWICE", "IU"),
            ("Paramore", "Tonight Alive"),
            ("BLACKPINK", "TWICE"),
            ("Taylor Swift", "Paramore"),
            ("IU", "TWICE"),
            ("BOL4", "IU")
        ]
    
    def load_config(self):
        """Load configuration and initialize APIs"""
        try:
            config_file = Path("configurations.txt")
            if not config_file.exists():
                config_file = Path("../configurations.txt")
            
            if config_file.exists():
                self.config = AppConfig(str(config_file))
                lastfm_config = self.config.get_lastfm_config()
                
                if lastfm_config['enabled'] and lastfm_config['api_key']:
                    self.lastfm_api = LastfmAPI(
                        lastfm_config['api_key'],
                        lastfm_config['api_secret'],
                        lastfm_config['cache_dir']
                    )
                    self.cache_dir = Path(lastfm_config['cache_dir'])
                    
                    self.artist_fetcher = EnhancedArtistDataFetcher(self.config)
                    print("✅ Configuration loaded successfully")
                else:
                    print("⚠️  Last.fm API not configured")
            else:
                print("⚠️  Configuration file not found")
                
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
    
    def test_single_artist(self, artist_name: str, limit: int = 50) -> SimilarityResult:
        """Test similarity data for a single artist"""
        print(f"\n🔍 Testing artist: '{artist_name}'")
        
        if not self.lastfm_api:
            return SimilarityResult(artist_name, [], False, "Last.fm API not available")
        
        start_time = time.time()
        
        try:
            # Check if data is cached
            cache_hit = self._check_cache(artist_name)
            
            # Get similar artists
            similar_artists = self.lastfm_api.get_similar_artists(artist_name, limit=limit)
            
            api_time = time.time() - start_time
            
            print(f"   📊 Found {len(similar_artists)} similar artists")
            print(f"   ⏱️  Response time: {api_time:.2f}s")
            print(f"   💾 Cache hit: {cache_hit}")
            
            if similar_artists:
                print(f"   🎯 Top 5 similar:")
                for i, similar in enumerate(similar_artists[:5], 1):
                    print(f"      {i}. {similar['name']} (similarity: {similar['match']:.3f})")
            
            return SimilarityResult(
                artist=artist_name,
                similar_artists=similar_artists,
                success=True,
                cache_hit=cache_hit,
                api_response_time=api_time
            )
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return SimilarityResult(artist_name, [], False, str(e))
    
    def test_bidirectional_similarity(self, artist_a: str, artist_b: str) -> Dict:
        """Test similarity in both directions between two artists"""
        print(f"\n🔄 Testing bidirectional similarity: '{artist_a}' ↔ '{artist_b}'")
        
        # Test A → B
        result_a = self.test_single_artist(artist_a)
        similarity_a_to_b = 0.0
        found_a_to_b = False
        
        if result_a.success:
            for similar in result_a.similar_artists:
                if self._names_match(similar['name'], artist_b):
                    similarity_a_to_b = similar['match']
                    found_a_to_b = True
                    break
        
        # Test B → A
        result_b = self.test_single_artist(artist_b)
        similarity_b_to_a = 0.0
        found_b_to_a = False
        
        if result_b.success:
            for similar in result_b.similar_artists:
                if self._names_match(similar['name'], artist_a):
                    similarity_b_to_a = similar['match']
                    found_b_to_a = True
                    break
        
        # Results
        print(f"   📈 {artist_a} → {artist_b}: {similarity_a_to_b:.3f} {'✅' if found_a_to_b else '❌'}")
        print(f"   📉 {artist_b} → {artist_a}: {similarity_b_to_a:.3f} {'✅' if found_b_to_a else '❌'}")
        
        max_similarity = max(similarity_a_to_b, similarity_b_to_a)
        bidirectional_found = found_a_to_b or found_b_to_a
        
        if bidirectional_found:
            print(f"   🎯 Best similarity: {max_similarity:.3f}")
        else:
            print(f"   ⚠️  No bidirectional connection found!")
        
        return {
            'artist_a': artist_a,
            'artist_b': artist_b,
            'a_to_b': similarity_a_to_b,
            'b_to_a': similarity_b_to_a,
            'found_a_to_b': found_a_to_b,
            'found_b_to_a': found_b_to_a,
            'max_similarity': max_similarity,
            'bidirectional_found': bidirectional_found
        }
    
    def test_problem_cases(self):
        """Test known problematic artist pairs"""
        print("\n🚨 Testing Known Problem Cases")
        print("=" * 50)
        
        results = []
        for artist_a, artist_b in self.problem_cases:
            result = self.test_bidirectional_similarity(artist_a, artist_b)
            results.append(result)
            time.sleep(0.2)  # Rate limiting
        
        # Summary
        print(f"\n📊 PROBLEM CASE SUMMARY")
        print("-" * 30)
        
        found_connections = sum(1 for r in results if r['bidirectional_found'])
        total_cases = len(results)
        
        print(f"Connections found: {found_connections}/{total_cases}")
        
        for result in results:
            status = "✅" if result['bidirectional_found'] else "❌"
            similarity = result['max_similarity']
            print(f"{status} {result['artist_a']} ↔ {result['artist_b']}: {similarity:.3f}")
        
        return results
    
    def analyze_cache_contents(self):
        """Analyze what's in the Last.fm cache"""
        print(f"\n💾 Analyzing Cache Contents")
        print("=" * 30)
        
        if not self.cache_dir or not self.cache_dir.exists():
            print("❌ Cache directory not found")
            return
        
        cache_files = list(self.cache_dir.glob("*.json"))
        
        if not cache_files:
            print("⚠️  No cache files found")
            return
        
        print(f"📁 Cache directory: {self.cache_dir}")
        print(f"📊 Cache files: {len(cache_files)}")
        
        # Analyze main cache file
        main_cache = self.cache_dir / "lastfm_cache.json"
        if main_cache.exists():
            try:
                with open(main_cache) as f:
                    cache_data = json.load(f)
                
                print(f"🗂️  Cached artists: {len(cache_data)}")
                
                # Show sample cached artists
                sample_artists = list(cache_data.keys())[:10]
                print(f"📝 Sample cached artists:")
                for artist in sample_artists:
                    entry = cache_data[artist]
                    similar_count = len(entry.get('similar', {}).get('artist', []))
                    print(f"   - {artist}: {similar_count} similar artists")
                
                # Check if our problem artists are cached
                print(f"\n🔍 Problem artists in cache:")
                problem_artists = set()
                for a, b in self.problem_cases:
                    problem_artists.add(a.lower())
                    problem_artists.add(b.lower())
                
                for artist in problem_artists:
                    variants = [artist, artist.upper(), artist.title()]
                    found = False
                    for variant in variants:
                        if variant in cache_data:
                            similar_count = len(cache_data[variant].get('similar', {}).get('artist', []))
                            print(f"   ✅ {variant}: {similar_count} similar artists")
                            found = True
                            break
                    if not found:
                        print(f"   ❌ {artist}: Not in cache")
                
            except Exception as e:
                print(f"❌ Error reading cache: {e}")
        else:
            print("⚠️  Main cache file not found")
    
    def test_name_matching(self):
        """Test artist name matching logic"""
        print(f"\n🔤 Testing Name Matching Logic")
        print("=" * 35)
        
        test_cases = [
            ("IU", ["IU", "아이유", "iu", "I.U."]),
            ("TWICE", ["TWICE", "twice", "Twice"]),
            ("BOL4", ["BOL4", "Bolbbalgan4", "볼빨간사춘기", "bol4"]),
            ("Paramore", ["Paramore", "paramore", "PARAMORE"]),
            ("Tonight Alive", ["Tonight Alive", "tonight alive", "TONIGHT ALIVE"])
        ]
        
        for canonical, variants in test_cases:
            print(f"\n🎯 Testing '{canonical}':")
            for variant in variants:
                match = self._names_match(canonical, variant)
                print(f"   '{variant}' → {canonical}: {'✅' if match else '❌'}")
    
    def interactive_artist_search(self):
        """Interactive mode for testing specific artists"""
        print(f"\n🎮 Interactive Artist Search")
        print("=" * 30)
        print("Enter artist names to test their similarity data.")
        print("Type 'quit' to exit, 'problems' to test known issues, 'cache' to analyze cache.")
        
        while True:
            try:
                user_input = input("\n🎵 Enter artist name (or command): ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'problems':
                    self.test_problem_cases()
                elif user_input.lower() == 'cache':
                    self.analyze_cache_contents()
                elif user_input.lower() == 'names':
                    self.test_name_matching()
                else:
                    # Test the artist
                    result = self.test_single_artist(user_input)
                    
                    if result.success and result.similar_artists:
                        # Ask if user wants to test connections to specific artists
                        print(f"\n💡 Test connection to specific artist? (Enter name or press Enter to skip)")
                        target = input("🔗 Target artist: ").strip()
                        
                        if target:
                            self.test_bidirectional_similarity(user_input, target)
            
            except KeyboardInterrupt:
                print(f"\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _check_cache(self, artist_name: str) -> bool:
        """Check if artist data is in cache"""
        if not self.cache_dir:
            return False
        
        main_cache = self.cache_dir / "lastfm_cache.json"
        if not main_cache.exists():
            return False
        
        try:
            with open(main_cache) as f:
                cache_data = json.load(f)
            return artist_name in cache_data
        except:
            return False
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Simple name matching logic (can be enhanced)"""
        name1_clean = name1.lower().strip()
        name2_clean = name2.lower().strip()
        
        # Exact match
        if name1_clean == name2_clean:
            return True
        
        # Contains match
        if name1_clean in name2_clean or name2_clean in name1_clean:
            return True
        
        # Common K-pop variations
        kpop_variants = {
            'iu': ['iu', '아이유', 'i.u.'],
            'twice': ['twice'],
            'bol4': ['bol4', 'bolbbalgan4', '볼빨간사춘기'],
            'blackpink': ['blackpink', 'black pink']
        }
        
        for canonical, variants in kpop_variants.items():
            if name1_clean in variants and name2_clean in variants:
                return True
        
        return False


def main():
    """Main CLI interface"""
    print("🔍 Similarity Data Debug Suite")
    print("=" * 40)
    
    debugger = SimilarityDebugger()
    
    if not debugger.lastfm_api:
        print("❌ Cannot proceed without Last.fm API configuration")
        print("Please check your configurations.txt file")
        return
    
    # Show menu
    while True:
        print(f"\n📋 MENU:")
        print("1. Test specific artist")
        print("2. Test bidirectional similarity")
        print("3. Test known problem cases")
        print("4. Analyze cache contents") 
        print("5. Test name matching")
        print("6. Interactive mode")
        print("0. Exit")
        
        try:
            choice = input("\n🎯 Choose option (0-6): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                artist = input("🎵 Enter artist name: ").strip()
                if artist:
                    debugger.test_single_artist(artist)
            elif choice == '2':
                artist_a = input("🎵 Enter first artist: ").strip()
                artist_b = input("🎵 Enter second artist: ").strip()
                if artist_a and artist_b:
                    debugger.test_bidirectional_similarity(artist_a, artist_b)
            elif choice == '3':
                debugger.test_problem_cases()
            elif choice == '4':
                debugger.analyze_cache_contents()
            elif choice == '5':
                debugger.test_name_matching()
            elif choice == '6':
                debugger.interactive_artist_search()
            else:
                print("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print(f"\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()