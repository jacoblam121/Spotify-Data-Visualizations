#!/usr/bin/env python3
"""
Phase 1.1.1 Visualization Test Suite
====================================

Manual test suite for comparing the three existing D3.js network visualizations.
This script provides a configurable test framework to validate features and functionality.
"""

import json
import os
import webbrowser
import time
from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path


@dataclass
class TestResult:
    """Test result container"""
    test_name: str
    file_tested: str
    passed: bool
    notes: str
    score: int  # 1-10


@dataclass
class VisualizationFile:
    """Visualization file metadata"""
    name: str
    path: str
    description: str
    expected_features: List[str]


class VisualizationTestSuite:
    """Test suite for visualization analysis"""
    
    def __init__(self, project_root: str = ".."):
        self.project_root = Path(project_root)
        self.results: List[TestResult] = []
        
        # Define the files to test
        self.visualizations = [
            VisualizationFile(
                name="Basic Network",
                path="network_d3.html",
                description="Simple proof-of-concept visualization",
                expected_features=[
                    "force_simulation", "hover_tooltips", "drag_nodes", 
                    "basic_styling", "hardcoded_data"
                ]
            ),
            VisualizationFile(
                name="Enhanced Network", 
                path="real_network_d3.html",
                description="Enhanced version with controls and modern UI",
                expected_features=[
                    "force_simulation", "sidebar_controls", "zoom_pan", 
                    "modern_styling", "responsive_design", "force_sliders",
                    "click_to_center", "genre_legend"
                ]
            ),
            VisualizationFile(
                name="Corrected Network",
                path="corrected_network_d3.html", 
                description="Production-ready with corrected data and full features",
                expected_features=[
                    "force_simulation", "sidebar_controls", "zoom_pan",
                    "modern_styling", "responsive_design", "force_sliders",
                    "edge_labels", "statistics_panel", "corrections_panel",
                    "connection_highlighting", "external_links", "rich_tooltips"
                ]
            )
        ]
        
        # Test configuration
        self.test_config = {
            "auto_open_browser": True,
            "test_duration_seconds": 30,
            "detailed_analysis": True,
            "score_threshold": 7  # Minimum score to pass
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        print("🧪 Starting Phase 1.1.1 Visualization Test Suite")
        print("=" * 60)
        
        # Check file existence
        self._check_file_existence()
        
        # Run manual tests for each visualization
        for viz in self.visualizations:
            self._test_visualization(viz)
        
        # Generate comparison report
        report = self._generate_report()
        
        # Save results
        self._save_results(report)
        
        return report
    
    def _check_file_existence(self):
        """Check if all visualization files exist"""
        print("\n📁 Checking file existence...")
        
        missing_files = []
        for viz in self.visualizations:
            file_path = self.project_root / viz.path
            if file_path.exists():
                print(f"✅ {viz.path}")
            else:
                print(f"❌ {viz.path} - NOT FOUND")
                missing_files.append(viz.path)
        
        if missing_files:
            raise FileNotFoundError(f"Missing files: {missing_files}")
    
    def _test_visualization(self, viz: VisualizationFile):
        """Test individual visualization with manual validation"""
        print(f"\n🎯 Testing: {viz.name}")
        print(f"📄 File: {viz.path}")
        print(f"📝 Description: {viz.description}")
        print("-" * 50)
        
        file_path = self.project_root / viz.path
        
        # Auto-open in browser if configured
        if self.test_config["auto_open_browser"]:
            print(f"🌐 Opening {viz.path} in browser...")
            webbrowser.open(f"file://{file_path.absolute()}")
            time.sleep(2)  # Give browser time to load
        
        # Manual testing prompts
        print(f"\n📋 Manual Test Checklist for {viz.name}:")
        print("Please test the following features manually:")
        
        feature_results = {}
        for i, feature in enumerate(viz.expected_features, 1):
            feature_name = feature.replace("_", " ").title()
            print(f"  {i}. {feature_name}")
        
        print(f"\nTake {self.test_config['test_duration_seconds']} seconds to thoroughly test...")
        
        if self.test_config["detailed_analysis"]:
            # Collect detailed feedback
            print("\n🔍 Detailed Analysis:")
            
            # UI/UX Assessment
            ui_score = self._get_score_input("UI/UX Quality (1-10)")
            feature_results["ui_ux"] = ui_score
            
            # Functionality Assessment  
            functionality_score = self._get_score_input("Functionality (1-10)")
            feature_results["functionality"] = functionality_score
            
            # Performance Assessment
            performance_score = self._get_score_input("Performance/Responsiveness (1-10)")
            feature_results["performance"] = performance_score
            
            # Data Visualization Assessment
            dataviz_score = self._get_score_input("Data Visualization Quality (1-10)")
            feature_results["data_visualization"] = dataviz_score
            
            # Overall Assessment
            overall_score = self._get_score_input("Overall Score (1-10)")
            feature_results["overall"] = overall_score
            
            # Additional notes
            notes = input("📝 Additional notes or observations: ").strip()
            
            # Calculate if test passed
            avg_score = sum(feature_results.values()) / len(feature_results)
            passed = avg_score >= self.test_config["score_threshold"]
            
            # Record result
            result = TestResult(
                test_name=f"Manual Test - {viz.name}",
                file_tested=viz.path,
                passed=passed,
                notes=notes,
                score=int(avg_score)
            )
            
            self.results.append(result)
            
            print(f"✅ Test completed. Average score: {avg_score:.1f}/10")
        else:
            # Simple pass/fail
            passed = input(f"\n✅ Did {viz.name} work correctly? (y/n): ").lower().startswith('y')
            notes = input("📝 Brief notes: ").strip()
            
            result = TestResult(
                test_name=f"Simple Test - {viz.name}",
                file_tested=viz.path,
                passed=passed,
                notes=notes,
                score=8 if passed else 3
            )
            
            self.results.append(result)
    
    def _get_score_input(self, prompt: str) -> int:
        """Get score input with validation"""
        while True:
            try:
                score = int(input(f"{prompt}: "))
                if 1 <= score <= 10:
                    return score
                else:
                    print("Please enter a score between 1 and 10")
            except ValueError:
                print("Please enter a valid number")
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        print("\n📊 Generating Test Report...")
        
        report = {
            "test_summary": {
                "total_tests": len(self.results),
                "passed_tests": sum(1 for r in self.results if r.passed),
                "failed_tests": sum(1 for r in self.results if not r.passed),
                "average_score": sum(r.score for r in self.results) / len(self.results) if self.results else 0
            },
            "detailed_results": [],
            "recommendations": [],
            "file_ranking": []
        }
        
        # Detailed results
        for result in self.results:
            report["detailed_results"].append({
                "test_name": result.test_name,
                "file": result.file_tested,
                "passed": result.passed,
                "score": result.score,
                "notes": result.notes
            })
        
        # File ranking by score
        file_scores = {}
        for result in self.results:
            if result.file_tested not in file_scores:
                file_scores[result.file_tested] = []
            file_scores[result.file_tested].append(result.score)
        
        for file, scores in file_scores.items():
            avg_score = sum(scores) / len(scores)
            report["file_ranking"].append({
                "file": file,
                "average_score": avg_score,
                "total_tests": len(scores)
            })
        
        # Sort by score
        report["file_ranking"].sort(key=lambda x: x["average_score"], reverse=True)
        
        # Generate recommendations
        best_file = report["file_ranking"][0] if report["file_ranking"] else None
        if best_file:
            report["recommendations"].append(
                f"Recommended base file: {best_file['file']} (score: {best_file['average_score']:.1f}/10)"
            )
        
        if report["test_summary"]["failed_tests"] > 0:
            report["recommendations"].append(
                "Some tests failed. Review failed tests before proceeding to Phase 1.1.2"
            )
        else:
            report["recommendations"].append(
                "All tests passed. Ready to proceed to Phase 1.1.2"
            )
        
        return report
    
    def _save_results(self, report: Dict[str, Any]):
        """Save test results to files"""
        results_dir = self.project_root / "tests_phase_1_1_1"
        results_dir.mkdir(exist_ok=True)
        
        # Save JSON report
        json_file = results_dir / "test_results.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Save human-readable report
        txt_file = results_dir / "test_report.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("Phase 1.1.1 Visualization Test Results\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("SUMMARY:\n")
            f.write(f"Total Tests: {report['test_summary']['total_tests']}\n")
            f.write(f"Passed: {report['test_summary']['passed_tests']}\n")
            f.write(f"Failed: {report['test_summary']['failed_tests']}\n")
            f.write(f"Average Score: {report['test_summary']['average_score']:.1f}/10\n\n")
            
            f.write("FILE RANKING:\n")
            for i, file_data in enumerate(report['file_ranking'], 1):
                f.write(f"{i}. {file_data['file']} - {file_data['average_score']:.1f}/10\n")
            
            f.write("\nRECOMMENDATIONS:\n")
            for rec in report['recommendations']:
                f.write(f"• {rec}\n")
            
            f.write("\nDETAILED RESULTS:\n")
            for result in report['detailed_results']:
                f.write(f"\nTest: {result['test_name']}\n")
                f.write(f"File: {result['file']}\n")
                f.write(f"Result: {'PASS' if result['passed'] else 'FAIL'}\n")
                f.write(f"Score: {result['score']}/10\n")
                f.write(f"Notes: {result['notes']}\n")
        
        print(f"📄 Results saved to:")
        print(f"  - {json_file}")
        print(f"  - {txt_file}")
    
    def print_summary(self):
        """Print test summary"""
        if not self.results:
            print("No tests have been run yet.")
            return
        
        print("\n📈 TEST SUMMARY")
        print("=" * 30)
        
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        avg_score = sum(r.score for r in self.results) / total
        
        print(f"Tests Run: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Average Score: {avg_score:.1f}/10")
        
        print("\nFile Scores:")
        file_scores = {}
        for result in self.results:
            if result.file_tested not in file_scores:
                file_scores[result.file_tested] = []
            file_scores[result.file_tested].append(result.score)
        
        for file, scores in file_scores.items():
            avg = sum(scores) / len(scores)
            print(f"  {file}: {avg:.1f}/10")


def main():
    """Run the test suite"""
    test_suite = VisualizationTestSuite()
    
    print("🔧 Visualization Test Suite Configuration")
    print("-" * 40)
    print("Current settings:")
    for key, value in test_suite.test_config.items():
        print(f"  {key}: {value}")
    
    # Allow configuration changes
    if input("\nChange configuration? (y/n): ").lower().startswith('y'):
        test_suite.test_config["auto_open_browser"] = input("Auto-open browser? (y/n): ").lower().startswith('y')
        test_suite.test_config["detailed_analysis"] = input("Detailed analysis? (y/n): ").lower().startswith('y')
        
        if test_suite.test_config["detailed_analysis"]:
            try:
                duration = int(input("Test duration (seconds, default 30): ") or "30")
                test_suite.test_config["test_duration_seconds"] = duration
            except ValueError:
                pass
    
    # Run tests
    try:
        report = test_suite.run_all_tests()
        test_suite.print_summary()
        
        print(f"\n🎉 Test suite completed successfully!")
        print(f"📊 Recommended file: {report['file_ranking'][0]['file']}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test suite interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        raise


if __name__ == "__main__":
    main()