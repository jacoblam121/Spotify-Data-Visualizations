#!/usr/bin/env python3
"""
Phase 1.1.1 Test Runner
=======================

Main test runner that executes both automated and manual tests for visualization analysis.
"""

import sys
import json
import argparse
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from automated_structure_test import AutomatedStructureTest
from visualization_test_suite import VisualizationTestSuite


def load_config(config_file: str = "test_config.json") -> dict:
    """Load test configuration"""
    config_path = Path(__file__).parent / config_file
    
    if not config_path.exists():
        print(f"⚠️  Config file not found: {config_file}")
        print("Using default configuration...")
        return {}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_automated_tests() -> dict:
    """Run automated structure tests"""
    print("🤖 RUNNING AUTOMATED TESTS")
    print("=" * 50)
    
    test = AutomatedStructureTest()
    results = test.run_analysis()
    
    return results


def run_manual_tests(config: dict) -> dict:
    """Run manual visualization tests"""
    print("\n👤 RUNNING MANUAL TESTS")
    print("=" * 50)
    
    test_suite = VisualizationTestSuite()
    
    # Apply configuration
    if 'test_execution' in config:
        test_suite.test_config.update(config['test_execution'])
    
    results = test_suite.run_all_tests()
    
    return results


def generate_final_report(automated_results: dict, manual_results: dict, config: dict):
    """Generate final comprehensive report"""
    print("\n📋 GENERATING FINAL REPORT")
    print("=" * 50)
    
    # Combine results
    final_report = {
        "phase": "1.1.1",
        "test_type": "Visualization Analysis",
        "timestamp": manual_results.get("timestamp", "unknown"),
        "automated_analysis": automated_results,
        "manual_testing": manual_results,
        "final_recommendations": []
    }
    
    # Automated scoring
    automated_scores = {}
    for filename, analysis in automated_results.items():
        if analysis.exists:
            score = 0
            score += analysis.node_count * 0.5
            score += analysis.edge_count * 1.0
            score += 2 if analysis.has_sidebar else 0
            score += 2 if analysis.has_controls else 0
            score += 1 if analysis.has_zoom else 0
            score += 1 if analysis.has_tooltips else 0
            score += len(analysis.css_features) * 0.5
            score += len(analysis.js_features) * 0.5
            automated_scores[filename] = min(score / 5, 10)  # Normalize to 10
    
    # Manual scoring
    manual_scores = {}
    if 'detailed_results' in manual_results:
        for result in manual_results['detailed_results']:
            filename = result['file']
            if filename not in manual_scores:
                manual_scores[filename] = []
            manual_scores[filename].append(result['score'])
    
    # Average manual scores
    manual_avg_scores = {}
    for filename, scores in manual_scores.items():
        manual_avg_scores[filename] = sum(scores) / len(scores)
    
    # Combined scoring
    combined_scores = {}
    all_files = set(automated_scores.keys()) | set(manual_avg_scores.keys())
    
    for filename in all_files:
        auto_score = automated_scores.get(filename, 0)
        manual_score = manual_avg_scores.get(filename, 0)
        
        # Weight: 30% automated, 70% manual
        combined_score = (auto_score * 0.3) + (manual_score * 0.7)
        combined_scores[filename] = combined_score
    
    # Sort by combined score
    ranked_files = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Generate recommendations
    if ranked_files:
        best_file = ranked_files[0]
        final_report["final_recommendations"].append(
            f"🏆 RECOMMENDED FILE: {best_file[0]} (combined score: {best_file[1]:.1f}/10)"
        )
        
        print(f"\n🎯 FINAL RECOMMENDATION")
        print(f"Best file for Phase 1.1.2: {best_file[0]}")
        print(f"Combined score: {best_file[1]:.1f}/10")
        
        print(f"\nAll rankings:")
        for i, (filename, score) in enumerate(ranked_files, 1):
            print(f"  {i}. {filename} - {score:.1f}/10")
    
    # Add specific recommendations based on analysis
    if any(score >= 8 for score in combined_scores.values()):
        final_report["final_recommendations"].append(
            "✅ HIGH QUALITY: At least one visualization scored 8+/10. Ready for Phase 1.1.2."
        )
    else:
        final_report["final_recommendations"].append(
            "⚠️  MODERATE QUALITY: Consider additional improvements before Phase 1.1.2."
        )
    
    # Save final report
    output_dir = Path("tests_phase_1_1_1")
    output_dir.mkdir(exist_ok=True)
    
    report_file = output_dir / "final_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False, default=str)
    
    # Save human-readable summary
    summary_file = output_dir / "PHASE_1_1_1_SUMMARY.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("# Phase 1.1.1 - Visualization Analysis Summary\n\n")
        f.write("## Final Recommendations\n\n")
        for rec in final_report["final_recommendations"]:
            f.write(f"- {rec}\n")
        
        f.write("\n## File Rankings\n\n")
        for i, (filename, score) in enumerate(ranked_files, 1):
            f.write(f"{i}. **{filename}** - {score:.1f}/10\n")
        
        f.write("\n## Detailed Scores\n\n")
        f.write("| File | Automated | Manual | Combined |\n")
        f.write("|------|-----------|--------|---------|\n")
        for filename in all_files:
            auto = automated_scores.get(filename, 0)
            manual = manual_avg_scores.get(filename, 0)
            combined = combined_scores.get(filename, 0)
            f.write(f"| {filename} | {auto:.1f} | {manual:.1f} | {combined:.1f} |\n")
        
        f.write("\n## Next Steps\n\n")
        if ranked_files:
            f.write(f"1. Use **{ranked_files[0][0]}** as the base for Phase 1.1.2\n")
            f.write("2. Extract hardcoded data and implement dynamic loading\n")
            f.write("3. Preserve all existing features and styling\n")
            f.write("4. Test with actual network JSON files\n")
    
    print(f"\n📄 Final reports saved:")
    print(f"  - {report_file}")
    print(f"  - {summary_file}")
    
    return final_report


def main():
    """Main test execution"""
    parser = argparse.ArgumentParser(description="Phase 1.1.1 Visualization Test Suite")
    parser.add_argument("--automated-only", action="store_true", help="Run only automated tests")
    parser.add_argument("--manual-only", action="store_true", help="Run only manual tests")
    parser.add_argument("--config", default="test_config.json", help="Configuration file")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    print("🧪 PHASE 1.1.1 VISUALIZATION TEST SUITE")
    print("=" * 60)
    print(f"Configuration: {args.config}")
    print(f"Test mode: {'Automated only' if args.automated_only else 'Manual only' if args.manual_only else 'Full suite'}")
    
    automated_results = {}
    manual_results = {}
    
    try:
        if not args.manual_only:
            automated_results = run_automated_tests()
        
        if not args.automated_only:
            manual_results = run_manual_tests(config)
        
        if automated_results or manual_results:
            final_report = generate_final_report(automated_results, manual_results, config)
            
            print(f"\n🎉 Phase 1.1.1 testing completed successfully!")
            print(f"📊 Ready to proceed to Phase 1.1.2")
        else:
            print(f"\n❌ No tests were run")
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        raise


if __name__ == "__main__":
    main()