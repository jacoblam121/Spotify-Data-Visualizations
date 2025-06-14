#!/usr/bin/env python3
"""
Interactive Menu System for Phase A.2 Test Suite
===============================================
User-friendly interface for configuring and running comprehensive tests.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from manual_test_suite_a2 import TestConfig, ComprehensiveTestSuite

class InteractiveTestMenu:
    """Interactive menu system for test configuration and execution."""
    
    def __init__(self):
        """Initialize the interactive menu."""
        self.config = TestConfig()
        self.clear_screen()
        self.show_welcome()
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_welcome(self):
        """Display welcome message."""
        print("🧪" + "=" * 60)
        print("   Phase A.2 Artist Verification - Interactive Test Menu")
        print("=" * 63)
        print("   Configure and run comprehensive verification tests")
        print("   with an easy-to-use interactive interface")
        print("=" * 63)
    
    def display_menu(self):
        """Display the main menu options."""
        print(f"\n📋 Main Menu")
        print("-" * 40)
        print("1. 📊 Quick Test Setup")
        print("2. ⚙️  Advanced Configuration")
        print("3. 🎯 Test Category Selection")
        print("4. 📈 Performance Settings")
        print("5. 🔧 Quality Thresholds")
        print("6. 📄 View Current Configuration")
        print("7. 🚀 Run Tests")
        print("8. 💾 Save/Load Configuration")
        print("9. ❓ Help & Examples")
        print("0. 🚪 Exit")
        print("-" * 40)
    
    def get_user_choice(self, prompt: str = "Choose an option", valid_range: range = range(10)) -> int:
        """Get user choice with validation."""
        while True:
            try:
                choice = input(f"\n{prompt} ({valid_range.start}-{valid_range.stop-1}): ").strip()
                choice_num = int(choice)
                if choice_num in valid_range:
                    return choice_num
                else:
                    print(f"❌ Please enter a number between {valid_range.start} and {valid_range.stop-1}")
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
    
    def get_yes_no(self, prompt: str) -> bool:
        """Get yes/no input from user."""
        while True:
            try:
                response = input(f"{prompt} (y/n): ").strip().lower()
                if response in ['y', 'yes', '1', 'true']:
                    return True
                elif response in ['n', 'no', '0', 'false']:
                    return False
                else:
                    print("❌ Please enter 'y' for yes or 'n' for no")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
    
    def get_number_input(self, prompt: str, min_val: float = 0, max_val: float = float('inf'), 
                        default: Optional[float] = None, is_int: bool = False) -> float:
        """Get numeric input with validation."""
        while True:
            try:
                default_text = f" (default: {default})" if default is not None else ""
                user_input = input(f"{prompt}{default_text}: ").strip()
                
                if not user_input and default is not None:
                    return default
                
                value = int(user_input) if is_int else float(user_input)
                
                if min_val <= value <= max_val:
                    return value
                else:
                    print(f"❌ Value must be between {min_val} and {max_val}")
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
    
    def get_text_input(self, prompt: str, default: Optional[str] = None, 
                      valid_options: Optional[List[str]] = None) -> str:
        """Get text input with optional validation."""
        while True:
            try:
                default_text = f" (default: {default})" if default else ""
                options_text = f" ({'/'.join(valid_options)})" if valid_options else ""
                user_input = input(f"{prompt}{default_text}{options_text}: ").strip()
                
                if not user_input and default:
                    return default
                
                if valid_options and user_input not in valid_options:
                    print(f"❌ Please choose from: {', '.join(valid_options)}")
                    continue
                
                return user_input
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
    
    def quick_test_setup(self):
        """Quick setup for common test scenarios."""
        self.clear_screen()
        print("📊 Quick Test Setup")
        print("=" * 40)
        print("Choose a preset configuration:")
        print("\n1. 🚀 Development Testing (Fast)")
        print("   - Skip API and slow tests")
        print("   - Basic quality thresholds")
        print("   - Quick validation")
        
        print("\n2. 📈 Performance Focus")
        print("   - Strict timing requirements")
        print("   - Multiple iterations")
        print("   - Performance-only tests")
        
        print("\n3. 🎯 Production Readiness")
        print("   - High quality standards")
        print("   - Comprehensive testing")
        print("   - Strict pass rates")
        
        print("\n4. 🌐 International/Unicode Focus")
        print("   - Unicode handling tests")
        print("   - K-pop/J-pop artists")
        print("   - Character normalization")
        
        print("\n5. 🔍 Problematic Artists Only")
        print("   - Focus on known problem cases")
        print("   - Real-world validation")
        print("   - API-dependent tests")
        
        print("\n0. ← Back to Main Menu")
        
        choice = self.get_user_choice("Choose preset", range(6))
        
        if choice == 0:
            return
        elif choice == 1:
            self._apply_development_preset()
        elif choice == 2:
            self._apply_performance_preset()
        elif choice == 3:
            self._apply_production_preset()
        elif choice == 4:
            self._apply_unicode_preset()
        elif choice == 5:
            self._apply_problematic_preset()
        
        print(f"\n✅ Applied preset configuration!")
        input("Press Enter to continue...")
    
    def _apply_development_preset(self):
        """Apply development testing preset."""
        self.config.skip_api_tests = True
        self.config.skip_slow_tests = True
        self.config.skip_performance_tests = False
        self.config.performance_iterations = 3
        self.config.max_verification_time = 1.0
        self.config.min_pass_rate = 70.0
        self.config.max_failed_tests = 8
        self.config.show_progress = True
        print("🚀 Development preset applied: Fast, basic validation")
    
    def _apply_performance_preset(self):
        """Apply performance testing preset."""
        self.config.skip_api_tests = True
        self.config.skip_slow_tests = False
        self.config.skip_performance_tests = False
        self.config.performance_iterations = 10
        self.config.max_verification_time = 0.3
        self.config.max_batch_time_per_artist = 0.5
        self.config.performance_test_sample_size = 20
        self.config.min_pass_rate = 85.0
        print("📈 Performance preset applied: Strict timing requirements")
    
    def _apply_production_preset(self):
        """Apply production readiness preset."""
        self.config.skip_api_tests = False
        self.config.skip_slow_tests = False
        self.config.skip_performance_tests = False
        self.config.mbid_min_confidence = 0.98
        self.config.track_strong_min_confidence = 0.90
        self.config.heuristic_improvement_threshold = 0.80
        self.config.min_pass_rate = 95.0
        self.config.max_failed_tests = 2
        print("🎯 Production preset applied: High quality standards")
    
    def _apply_unicode_preset(self):
        """Apply Unicode/international testing preset."""
        self.config.skip_api_tests = False
        self.config.skip_slow_tests = False
        self.config.unicode_test_artists = ["*LUNA", "YOASOBI", "방탄소년단", "IVE", "TWICE"]
        self.config.detailed_track_analysis = True
        self.config.verbose_output = True
        print("🌐 Unicode preset applied: International character focus")
    
    def _apply_problematic_preset(self):
        """Apply problematic artists testing preset."""
        self.config.skip_api_tests = False
        self.config.use_api_for_real_tests = True
        self.config.problematic_artists = ["*LUNA", "YOASOBI", "IVE", "BTS", "Taylor Swift", "NewJeans"]
        self.config.heuristic_improvement_threshold = 0.70
        self.config.detailed_track_analysis = True
        print("🔍 Problematic artists preset applied: Real-world validation")
    
    def advanced_configuration(self):
        """Advanced configuration menu."""
        while True:
            self.clear_screen()
            print("⚙️ Advanced Configuration")
            print("=" * 40)
            print("1. 📁 Data Source Settings")
            print("2. 🔗 API Configuration")
            print("3. ⏱️  Timeout Settings")
            print("4. 📊 Sample Sizes")
            print("5. 🎨 Output Options")
            print("6. 🧪 Test Selection")
            print("0. ← Back to Main Menu")
            
            choice = self.get_user_choice("Choose configuration area", range(7))
            
            if choice == 0:
                break
            elif choice == 1:
                self._configure_data_source()
            elif choice == 2:
                self._configure_api()
            elif choice == 3:
                self._configure_timeouts()
            elif choice == 4:
                self._configure_sample_sizes()
            elif choice == 5:
                self._configure_output()
            elif choice == 6:
                self._configure_test_selection()
    
    def _configure_data_source(self):
        """Configure data source settings."""
        print("\n📁 Data Source Configuration")
        print("-" * 30)
        
        # Show current selection
        current_source = "Last.fm" if "lastfm" in self.config.data_path.lower() else "Spotify"
        print(f"Current data source: {current_source}")
        print(f"Current file: {self.config.data_path}")
        
        # Simple toggle between Last.fm and Spotify
        print(f"\nAvailable data sources:")
        print(f"1. 📊 Last.fm CSV (lastfm_data.csv)")
        print(f"   - Contains MBIDs for definitive matching")
        print(f"   - International character support")
        print(f"   - Artist listener counts")
        
        print(f"\n2. 🎵 Spotify JSON (spotify_data.json)")
        print(f"   - Extended streaming history")
        print(f"   - Track URIs for precise identification")
        print(f"   - Detailed play statistics")
        
        print(f"\n3. 🔧 Custom file path")
        
        choice = self.get_user_choice("Choose data source", range(1, 4))
        
        if choice == 1:
            self.config.data_path = "lastfm_data.csv"
            self.config.force_data_source = "lastfm"
            print("✅ Switched to Last.fm data source")
            
            # Check if file exists
            if not Path(self.config.data_path).exists():
                print(f"⚠️  Warning: {self.config.data_path} not found")
                print("   Make sure you have exported your Last.fm data")
                
        elif choice == 2:
            self.config.data_path = "spotify_data.json"
            self.config.force_data_source = "spotify"
            print("✅ Switched to Spotify data source")
            
            # Check if file exists
            if not Path(self.config.data_path).exists():
                print(f"⚠️  Warning: {self.config.data_path} not found")
                print("   Make sure you have your Spotify extended streaming history")
                
        elif choice == 3:
            new_path = self.get_text_input("Enter custom file path", self.config.data_path)
            if Path(new_path).exists():
                self.config.data_path = new_path
                # Auto-detect source based on extension
                if new_path.endswith('.csv'):
                    self.config.force_data_source = "lastfm"
                    print(f"✅ Custom Last.fm file: {new_path}")
                elif new_path.endswith('.json'):
                    self.config.force_data_source = "spotify"
                    print(f"✅ Custom Spotify file: {new_path}")
                else:
                    source = self.get_text_input("Data source type", None, ['lastfm', 'spotify'])
                    self.config.force_data_source = source
                    print(f"✅ Custom file with {source} format: {new_path}")
            else:
                print(f"⚠️  Warning: {new_path} does not exist")
                if self.get_yes_no("Use anyway?"):
                    self.config.data_path = new_path
        
        input("\nPress Enter to continue...")
    
    def _configure_api(self):
        """Configure API settings."""
        print("\n🔗 API Configuration")
        print("-" * 30)
        
        self.config.use_api_for_real_tests = self.get_yes_no("Enable API for real artist tests?")
        self.config.skip_api_tests = not self.get_yes_no("Run API-dependent tests?")
        
        if not self.config.skip_api_tests:
            self.config.api_timeout = self.get_number_input(
                "API timeout (seconds)", 5.0, 60.0, self.config.api_timeout
            )
            self.config.max_api_retries = int(self.get_number_input(
                "Max API retries", 1, 10, self.config.max_api_retries, is_int=True
            ))
        
        input("\nPress Enter to continue...")
    
    def _configure_timeouts(self):
        """Configure timeout settings."""
        print("\n⏱️ Timeout Configuration")
        print("-" * 30)
        
        self.config.max_verification_time = self.get_number_input(
            "Max verification time (seconds)", 0.1, 10.0, self.config.max_verification_time
        )
        
        self.config.max_batch_time_per_artist = self.get_number_input(
            "Max batch time per artist (seconds)", 0.1, 5.0, self.config.max_batch_time_per_artist
        )
        
        self.config.edge_case_timeout = self.get_number_input(
            "Edge case timeout (seconds)", 1.0, 30.0, self.config.edge_case_timeout
        )
        
        input("\nPress Enter to continue...")
    
    def _configure_sample_sizes(self):
        """Configure sample sizes."""
        print("\n📊 Sample Size Configuration")
        print("-" * 30)
        
        self.config.performance_iterations = int(self.get_number_input(
            "Performance test iterations", 1, 50, self.config.performance_iterations, is_int=True
        ))
        
        self.config.performance_test_sample_size = int(self.get_number_input(
            "Performance test sample size", 1, 100, self.config.performance_test_sample_size, is_int=True
        ))
        
        self.config.max_candidates_per_test = int(self.get_number_input(
            "Max candidates per test", 1, 20, self.config.max_candidates_per_test, is_int=True
        ))
        
        self.config.edge_case_long_name_length = int(self.get_number_input(
            "Long name test length", 10, 2000, self.config.edge_case_long_name_length, is_int=True
        ))
        
        input("\nPress Enter to continue...")
    
    def _configure_output(self):
        """Configure output options."""
        print("\n🎨 Output Configuration")
        print("-" * 30)
        
        self.config.verbose_output = self.get_yes_no("Enable verbose output?")
        self.config.show_progress = self.get_yes_no("Show progress indicators?")
        self.config.detailed_track_analysis = self.get_yes_no("Enable detailed track analysis?")
        self.config.colorized_output = self.get_yes_no("Enable colorized output?")
        
        self.config.save_results = self.get_yes_no("Save results to file?")
        if self.config.save_results:
            self.config.results_file = self.get_text_input(
                "Results filename", self.config.results_file
            )
        
        input("\nPress Enter to continue...")
    
    def _configure_test_selection(self):
        """Configure test selection options."""
        print("\n🧪 Test Selection Configuration")
        print("-" * 30)
        
        self.config.skip_slow_tests = self.get_yes_no("Skip slow tests?")
        self.config.skip_performance_tests = self.get_yes_no("Skip performance tests?")
        
        print(f"\nCurrent problematic artists: {', '.join(self.config.problematic_artists)}")
        if self.get_yes_no("Customize problematic artists list?"):
            print("Enter artists one by one (empty line to finish):")
            artists = []
            while True:
                artist = input(f"Artist {len(artists)+1} (or Enter to finish): ").strip()
                if not artist:
                    break
                artists.append(artist)
            
            if artists:
                self.config.problematic_artists = artists
                print(f"✅ Updated problematic artists: {', '.join(artists)}")
        
        input("\nPress Enter to continue...")
    
    def test_category_selection(self):
        """Test category selection menu."""
        self.clear_screen()
        print("🎯 Test Category Selection")
        print("=" * 40)
        print("Select which test categories to run:")
        print("\n1. 🔗 MBID Matching Tests")
        print("2. 🎵 Track Matching Tests")
        print("3. 🌐 Unicode/International Tests")
        print("4. ⚠️  Edge Case Tests")
        print("5. ⚡ Performance Tests")
        print("6. 📊 Data Source Tests")
        print("7. 🎯 Confidence Threshold Tests")
        print("8. 🎭 Real Problematic Artists Tests")
        print("\n9. ✅ Select All Categories")
        print("10. 🚀 Run Selected Categories")
        print("0. ← Back to Main Menu")
        
        selected_categories = set()
        
        while True:
            print(f"\nCurrently selected: {len(selected_categories)} categories")
            if selected_categories:
                category_names = {
                    1: "MBID", 2: "Track", 3: "Unicode", 4: "Edge", 
                    5: "Performance", 6: "Data", 7: "Confidence", 8: "Real"
                }
                selected_names = [category_names[i] for i in selected_categories]
                print(f"Selected: {', '.join(selected_names)}")
            
            choice = self.get_user_choice("Choose option", range(11))
            
            if choice == 0:
                return None
            elif choice == 9:
                selected_categories = set(range(1, 9))
                print("✅ All categories selected")
            elif choice == 10:
                if selected_categories:
                    return selected_categories
                else:
                    print("❌ No categories selected")
            elif 1 <= choice <= 8:
                if choice in selected_categories:
                    selected_categories.remove(choice)
                    print(f"❌ Deselected category {choice}")
                else:
                    selected_categories.add(choice)
                    print(f"✅ Selected category {choice}")
    
    def performance_settings(self):
        """Performance settings menu."""
        self.clear_screen()
        print("📈 Performance Settings")
        print("=" * 40)
        
        print(f"Current Performance Configuration:")
        print(f"  Iterations: {self.config.performance_iterations}")
        print(f"  Max verification time: {self.config.max_verification_time}s")
        print(f"  Max batch time per artist: {self.config.max_batch_time_per_artist}s")
        print(f"  Sample size: {self.config.performance_test_sample_size}")
        print(f"  Skip performance tests: {self.config.skip_performance_tests}")
        
        if self.get_yes_no("\nModify performance settings?"):
            print("\n⚙️ Performance Configuration")
            
            # Quick presets
            print("\nQuick presets:")
            print("1. 🚀 Fast (3 iterations, loose timing)")
            print("2. 📊 Standard (5 iterations, normal timing)")
            print("3. 🎯 Strict (10 iterations, tight timing)")
            print("4. 🔧 Custom settings")
            
            preset_choice = self.get_user_choice("Choose preset or custom", range(1, 5))
            
            if preset_choice == 1:
                self.config.performance_iterations = 3
                self.config.max_verification_time = 1.0
                self.config.max_batch_time_per_artist = 2.0
                print("🚀 Fast preset applied")
            elif preset_choice == 2:
                self.config.performance_iterations = 5
                self.config.max_verification_time = 0.5
                self.config.max_batch_time_per_artist = 1.0
                print("📊 Standard preset applied")
            elif preset_choice == 3:
                self.config.performance_iterations = 10
                self.config.max_verification_time = 0.3
                self.config.max_batch_time_per_artist = 0.5
                print("🎯 Strict preset applied")
            elif preset_choice == 4:
                self._configure_timeouts()
                self._configure_sample_sizes()
        
        input("\nPress Enter to continue...")
    
    def quality_thresholds(self):
        """Quality thresholds configuration."""
        self.clear_screen()
        print("🔧 Quality Thresholds")
        print("=" * 40)
        
        print(f"Current Quality Configuration:")
        print(f"  MBID confidence threshold: {self.config.mbid_min_confidence}")
        print(f"  Track confidence threshold: {self.config.track_strong_min_confidence}")
        print(f"  Improvement threshold: {self.config.heuristic_improvement_threshold}")
        print(f"  Minimum pass rate: {self.config.min_pass_rate}%")
        print(f"  Maximum failures: {self.config.max_failed_tests}")
        
        if self.get_yes_no("\nModify quality thresholds?"):
            print("\n🎯 Quality Threshold Configuration")
            
            # Quick presets
            print("\nQuick presets:")
            print("1. 🟢 Lenient (Lower thresholds, development-friendly)")
            print("2. 🟡 Standard (Balanced thresholds)")
            print("3. 🔴 Strict (High thresholds, production-ready)")
            print("4. 🔧 Custom thresholds")
            
            preset_choice = self.get_user_choice("Choose preset or custom", range(1, 5))
            
            if preset_choice == 1:
                self.config.mbid_min_confidence = 0.90
                self.config.track_strong_min_confidence = 0.75
                self.config.heuristic_improvement_threshold = 0.60
                self.config.min_pass_rate = 70.0
                self.config.max_failed_tests = 10
                print("🟢 Lenient preset applied")
            elif preset_choice == 2:
                self.config.mbid_min_confidence = 0.95
                self.config.track_strong_min_confidence = 0.85
                self.config.heuristic_improvement_threshold = 0.75
                self.config.min_pass_rate = 75.0
                self.config.max_failed_tests = 5
                print("🟡 Standard preset applied")
            elif preset_choice == 3:
                self.config.mbid_min_confidence = 0.98
                self.config.track_strong_min_confidence = 0.90
                self.config.heuristic_improvement_threshold = 0.85
                self.config.min_pass_rate = 95.0
                self.config.max_failed_tests = 2
                print("🔴 Strict preset applied")
            elif preset_choice == 4:
                print("\n🔧 Custom Threshold Configuration")
                
                self.config.mbid_min_confidence = self.get_number_input(
                    "MBID confidence threshold", 0.5, 1.0, self.config.mbid_min_confidence
                )
                
                self.config.track_strong_min_confidence = self.get_number_input(
                    "Track confidence threshold", 0.5, 1.0, self.config.track_strong_min_confidence
                )
                
                self.config.heuristic_improvement_threshold = self.get_number_input(
                    "Improvement threshold", 0.3, 1.0, self.config.heuristic_improvement_threshold
                )
                
                self.config.min_pass_rate = self.get_number_input(
                    "Minimum pass rate (%)", 0.0, 100.0, self.config.min_pass_rate
                )
                
                self.config.max_failed_tests = int(self.get_number_input(
                    "Maximum failures", 0, 50, self.config.max_failed_tests, is_int=True
                ))
                
                print("🔧 Custom thresholds applied")
        
        input("\nPress Enter to continue...")
    
    def view_configuration(self):
        """Display current configuration."""
        self.clear_screen()
        print("📄 Current Configuration")
        print("=" * 50)
        
        print(f"📁 Data Source:")
        print(f"   Path: {self.config.data_path}")
        print(f"   Force source: {self.config.force_data_source or 'Auto-detect'}")
        
        print(f"\n🔗 API Settings:")
        print(f"   Use API for real tests: {self.config.use_api_for_real_tests}")
        print(f"   Skip API tests: {self.config.skip_api_tests}")
        print(f"   API timeout: {self.config.api_timeout}s")
        print(f"   Max retries: {self.config.max_api_retries}")
        
        print(f"\n⏱️ Performance:")
        print(f"   Iterations: {self.config.performance_iterations}")
        print(f"   Max verification time: {self.config.max_verification_time}s")
        print(f"   Max batch time per artist: {self.config.max_batch_time_per_artist}s")
        print(f"   Sample size: {self.config.performance_test_sample_size}")
        
        print(f"\n🎯 Quality Thresholds:")
        print(f"   MBID confidence: {self.config.mbid_min_confidence}")
        print(f"   Track confidence: {self.config.track_strong_min_confidence}")
        print(f"   Improvement threshold: {self.config.heuristic_improvement_threshold}")
        print(f"   Min pass rate: {self.config.min_pass_rate}%")
        print(f"   Max failures: {self.config.max_failed_tests}")
        
        print(f"\n🧪 Test Selection:")
        print(f"   Skip slow tests: {self.config.skip_slow_tests}")
        print(f"   Skip API tests: {self.config.skip_api_tests}")
        print(f"   Skip performance tests: {self.config.skip_performance_tests}")
        
        print(f"\n🎨 Output:")
        print(f"   Verbose: {self.config.verbose_output}")
        print(f"   Progress: {self.config.show_progress}")
        print(f"   Save results: {self.config.save_results}")
        print(f"   Results file: {self.config.results_file}")
        
        print(f"\n🎭 Test Artists:")
        print(f"   Problematic: {', '.join(self.config.problematic_artists[:3])}{'...' if len(self.config.problematic_artists) > 3 else ''}")
        
        input("\nPress Enter to continue...")
    
    def run_tests_menu(self):
        """Test execution menu."""
        self.clear_screen()
        print("🚀 Run Tests")
        print("=" * 40)
        print("Choose test execution mode:")
        print("\n1. 🏃 Quick Tests (MBID + Track + Real)")
        print("2. 🎯 Selected Categories")
        print("3. 🔧 Full Test Suite")
        print("4. 📊 Performance Tests Only")
        print("5. 🌐 Unicode Tests Only")
        print("6. 🎭 Problematic Artists Only")
        print("0. ← Back to Main Menu")
        
        choice = self.get_user_choice("Choose execution mode", range(7))
        
        if choice == 0:
            return
        
        # Confirm configuration
        print(f"\n📋 Test Configuration Summary:")
        print(f"   Data source: {self.config.data_path}")
        print(f"   API tests: {'Enabled' if not self.config.skip_api_tests else 'Disabled'}")
        print(f"   Quality threshold: {self.config.min_pass_rate}% pass rate")
        print(f"   Performance threshold: {self.config.max_verification_time}s")
        
        if not self.get_yes_no("\nProceed with test execution?"):
            return
        
        # Execute tests
        suite = ComprehensiveTestSuite(self.config)
        
        try:
            if choice == 1:
                print("\n🏃 Running Quick Tests...")
                suite.test_mbid_matching()
                suite.test_track_matching()
                suite.test_real_problematic_artists()
            elif choice == 2:
                categories = self.test_category_selection()
                if categories:
                    self._run_selected_categories(suite, categories)
                else:
                    return
            elif choice == 3:
                print("\n🔧 Running Full Test Suite...")
                suite.run_all_tests()
                return  # run_all_tests handles final results
            elif choice == 4:
                print("\n📊 Running Performance Tests...")
                suite.test_performance()
            elif choice == 5:
                print("\n🌐 Running Unicode Tests...")
                suite.test_unicode_handling()
            elif choice == 6:
                print("\n🎭 Running Problematic Artists Tests...")
                suite.test_real_problematic_artists()
            
            suite.show_final_results()
            
        except KeyboardInterrupt:
            print("\n⏹️ Test execution interrupted by user")
        except Exception as e:
            print(f"\n❌ Test execution failed: {e}")
        
        input("\nPress Enter to return to main menu...")
    
    def _run_selected_categories(self, suite: ComprehensiveTestSuite, categories: set):
        """Run selected test categories."""
        category_map = {
            1: ("MBID Matching", suite.test_mbid_matching),
            2: ("Track Matching", suite.test_track_matching),
            3: ("Unicode Handling", suite.test_unicode_handling),
            4: ("Edge Cases", suite.test_edge_cases),
            5: ("Performance", suite.test_performance),
            6: ("Data Sources", suite.test_data_sources),
            7: ("Confidence Thresholds", suite.test_confidence_thresholds),
            8: ("Real Artists", suite.test_real_problematic_artists)
        }
        
        print(f"\n🎯 Running {len(categories)} selected categories...")
        
        for category_num in sorted(categories):
            if category_num in category_map:
                name, test_func = category_map[category_num]
                print(f"\n{'='*60}")
                print(f"Running: {name}")
                print('='*60)
                test_func()
    
    def save_load_configuration(self):
        """Save/load configuration menu."""
        self.clear_screen()
        print("💾 Save/Load Configuration")
        print("=" * 40)
        print("1. 💾 Save Current Configuration")
        print("2. 📁 Load Configuration")
        print("3. 🔄 Reset to Defaults")
        print("0. ← Back to Main Menu")
        
        choice = self.get_user_choice("Choose option", range(4))
        
        if choice == 0:
            return
        elif choice == 1:
            self._save_configuration()
        elif choice == 2:
            self._load_configuration()
        elif choice == 3:
            if self.get_yes_no("Reset all settings to defaults?"):
                self.config = TestConfig()
                print("✅ Configuration reset to defaults")
        
        input("\nPress Enter to continue...")
    
    def _save_configuration(self):
        """Save current configuration to file."""
        filename = self.get_text_input("Configuration filename", "test_config.json")
        
        try:
            import json
            config_dict = self.config.__dict__.copy()
            
            with open(filename, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            print(f"✅ Configuration saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
    
    def _load_configuration(self):
        """Load configuration from file."""
        filename = self.get_text_input("Configuration filename", "test_config.json")
        
        try:
            import json
            
            if not Path(filename).exists():
                print(f"❌ Configuration file {filename} not found")
                return
            
            with open(filename, 'r') as f:
                config_dict = json.load(f)
            
            # Update configuration
            for key, value in config_dict.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            print(f"✅ Configuration loaded from {filename}")
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
    
    def show_help(self):
        """Display help and examples."""
        self.clear_screen()
        print("❓ Help & Examples")
        print("=" * 40)
        
        print("📖 Quick Start Guide:")
        print("1. Choose '📊 Quick Test Setup' for common scenarios")
        print("2. Or use '⚙️ Advanced Configuration' for custom settings")
        print("3. Select '🚀 Run Tests' to execute")
        print("4. Review results and adjust configuration as needed")
        
        print(f"\n🎯 Test Categories Explained:")
        print("• MBID Matching: Tests MusicBrainz ID verification")
        print("• Track Matching: Tests song-based artist verification")
        print("• Unicode Handling: Tests international character support")
        print("• Edge Cases: Tests error handling and unusual inputs")
        print("• Performance: Tests speed and timing requirements")
        print("• Data Sources: Tests Last.fm vs Spotify handling")
        print("• Confidence: Tests threshold logic and scoring")
        print("• Real Artists: Tests known problematic cases")
        
        print(f"\n⚙️ Configuration Tips:")
        print("• Start with Quick Test Setup presets")
        print("• Use 'Development' preset for fast iteration")
        print("• Use 'Production' preset for final validation")
        print("• Skip API tests if you have rate limits")
        print("• Adjust timeouts based on your system performance")
        
        print(f"\n🔧 Troubleshooting:")
        print("• If tests fail, check data file path")
        print("• For API errors, try --skip-api mode")
        print("• For performance issues, increase timeout thresholds")
        print("• For confidence issues, lower quality thresholds")
        
        print(f"\n📊 Understanding Results:")
        print("• Pass rate >95%: Excellent, production ready")
        print("• Pass rate 75-95%: Good, meets standards")
        print("• Pass rate <75%: Needs improvement")
        print("• Confidence >0.95: MBID match (best)")
        print("• Confidence 0.85-0.95: Strong track evidence")
        print("• Confidence <0.85: Heuristic fallback")
        
        input("\nPress Enter to continue...")
    
    def run(self):
        """Main menu loop."""
        while True:
            self.display_menu()
            choice = self.get_user_choice()
            
            if choice == 0:
                print("\n👋 Thank you for using the Phase A.2 Test Suite!")
                break
            elif choice == 1:
                self.quick_test_setup()
            elif choice == 2:
                self.advanced_configuration()
            elif choice == 3:
                self.test_category_selection()
            elif choice == 4:
                self.performance_settings()
            elif choice == 5:
                self.quality_thresholds()
            elif choice == 6:
                self.view_configuration()
            elif choice == 7:
                self.run_tests_menu()
            elif choice == 8:
                self.save_load_configuration()
            elif choice == 9:
                self.show_help()

def main():
    """Main entry point for interactive menu."""
    try:
        menu = InteractiveTestMenu()
        menu.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please report this issue.")

if __name__ == "__main__":
    main()