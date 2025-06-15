#!/usr/bin/env python3
"""
Performance testing runner for Green-Code FX video effects generator.

This script runs comprehensive performance benchmarks and generates detailed
reports for typing effect generation speed analysis.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import config


def setup_environment():
    """Set up environment for performance testing."""
    # Ensure headless operation
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    # Ensure directories exist
    config.ensure_directories()
    
    print("Environment configured for performance testing")
    print(f"  SDL Video Driver: {os.environ.get('SDL_VIDEODRIVER')}")
    print(f"  Output Directory: {config.OUTPUT_DIR}")
    print(f"  Temp Directory: {config.TEMP_DIR}")


def run_performance_tests():
    """Run the performance test suite."""
    print("\n" + "="*80)
    print("RUNNING GREEN-CODE FX PERFORMANCE BENCHMARKS")
    print("="*80)
    
    # Change to project root for pytest
    os.chdir(project_root)
    
    # Run specific performance tests
    test_commands = [
        # Typing effect performance tests
        ["python", "-m", "pytest", "tests/test_performance.py::TestTypingEffectPerformance::test_typing_effect_small_file_performance", "-v", "-s"],
        ["python", "-m", "pytest", "tests/test_performance.py::TestTypingEffectPerformance::test_typing_effect_medium_file_performance", "-v", "-s"],
        ["python", "-m", "pytest", "tests/test_performance.py::TestTypingEffectPerformance::test_typing_effect_large_file_performance", "-v", "-s"],

        # Matrix effect performance tests
        ["python", "-m", "pytest", "tests/test_performance.py::TestMatrixEffectPerformance::test_matrix_effect_short_duration_performance", "-v", "-s"],
        ["python", "-m", "pytest", "tests/test_performance.py::TestMatrixEffectPerformance::test_matrix_effect_standard_duration_performance", "-v", "-s"],
        ["python", "-m", "pytest", "tests/test_performance.py::TestMatrixEffectPerformance::test_matrix_effect_extended_duration_performance", "-v", "-s"],

        # Detailed bottleneck analysis
        ["python", "-m", "pytest", "tests/test_performance.py::TestTypingEffectPerformance::test_detailed_bottleneck_analysis", "-v", "-s"],
        ["python", "-m", "pytest", "tests/test_performance.py::TestMatrixEffectPerformance::test_matrix_effect_bottleneck_analysis", "-v", "-s"],
    ]
    
    results = []
    
    for i, cmd in enumerate(test_commands, 1):
        print(f"\n[{i}/{len(test_commands)}] Running: {' '.join(cmd)}")
        print("-" * 60)
        
        try:
            result = subprocess.run(cmd, capture_output=False, text=True, check=False)
            results.append((cmd, result.returncode))
            
            if result.returncode == 0:
                print(f"✅ Test passed")
            else:
                print(f"❌ Test failed with return code {result.returncode}")
                
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            results.append((cmd, -1))
    
    return results


def generate_summary_report(results):
    """Generate a summary report of all test results."""
    print("\n" + "="*80)
    print("PERFORMANCE BENCHMARK SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, code in results if code == 0)
    total = len(results)
    
    print(f"Tests Run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print(f"\nDetailed Results:")
    for cmd, code in results:
        test_name = cmd[-1].split("::")[-1] if "::" in cmd[-1] else cmd[-1]
        status = "PASS" if code == 0 else "FAIL"
        print(f"  {status}: {test_name}")
    
    # List generated reports
    print(f"\nGenerated Reports:")
    report_files = [
        "typing_effect_performance_report.txt",
        "typing_effect_bottleneck_analysis.txt",
        "typing_effect_bottleneck_data.json",
        "matrix_effect_performance_report.txt",
        "matrix_effect_bottleneck_analysis.txt",
        "matrix_effect_bottleneck_data.json"
    ]
    
    for report_file in report_files:
        report_path = config.OUTPUT_DIR / report_file
        if report_path.exists():
            print(f"  ✅ {report_path}")
        else:
            print(f"  ❌ {report_file} (not found)")
    
    return passed == total


def main():
    """Main performance testing workflow."""
    print("Green-Code FX Performance Testing Suite")
    print("=" * 50)
    
    try:
        # Setup
        setup_environment()
        
        # Run tests
        results = run_performance_tests()
        
        # Generate summary
        all_passed = generate_summary_report(results)
        
        # Final status
        if all_passed:
            print(f"\n🎉 All performance benchmarks PASSED!")
            print(f"   Typing effect generation meets ≤2x realtime requirement")
            print(f"   Matrix effect generation meets ≤1.5x realtime requirement")
            return 0
        else:
            print(f"\n⚠️  Some performance benchmarks FAILED!")
            print(f"   Review the detailed reports for optimization opportunities")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Performance testing interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Performance testing failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
