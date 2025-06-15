#!/usr/bin/env python3
"""
Simple check for performance profiling integration.

This script validates that the performance profiling code is correctly
integrated into the video generator without requiring external dependencies.
"""

import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_file_exists(file_path, description):
    """Check if a file exists and report the result."""
    if file_path.exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (NOT FOUND)")
        return False


def check_code_integration():
    """Check that performance profiling is integrated into the video generator."""
    print("Checking performance profiling integration...")
    
    video_gen_file = project_root / "src" / "video_generator.py"
    
    if not video_gen_file.exists():
        print(f"❌ Video generator file not found: {video_gen_file}")
        return False
    
    with open(video_gen_file, 'r') as f:
        content = f.read()
    
    # Check for profiler imports
    required_imports = [
        "from .performance_profiler import profiler",
    ]
    
    # Check for profiler usage
    required_profiler_calls = [
        "profiler.start_operation",
        "profiler.end_operation",
        "typing_effect_total",
        "load_source_file",
        "load_font",
        "main_rendering_loop",
        "save_frame",
        "video_assembly",
    ]
    
    missing_imports = []
    missing_calls = []
    
    for import_stmt in required_imports:
        if import_stmt not in content:
            missing_imports.append(import_stmt)
    
    for call in required_profiler_calls:
        if call not in content:
            missing_calls.append(call)
    
    if missing_imports:
        print(f"❌ Missing imports in video_generator.py:")
        for imp in missing_imports:
            print(f"   - {imp}")
    else:
        print(f"✅ All required imports present in video_generator.py")
    
    if missing_calls:
        print(f"❌ Missing profiler calls in video_generator.py:")
        for call in missing_calls:
            print(f"   - {call}")
    else:
        print(f"✅ All required profiler calls present in video_generator.py")
    
    return len(missing_imports) == 0 and len(missing_calls) == 0


def check_test_structure():
    """Check that performance test structure is correct."""
    print("Checking performance test structure...")
    
    test_file = project_root / "tests" / "test_performance.py"
    
    if not test_file.exists():
        print(f"❌ Performance test file not found: {test_file}")
        return False
    
    with open(test_file, 'r') as f:
        content = f.read()
    
    required_elements = [
        "class PerformanceBenchmark",
        "class TestTypingEffectPerformance",
        "test_typing_effect_small_file_performance",
        "test_typing_effect_medium_file_performance",
        "test_typing_effect_large_file_performance",
        "test_detailed_bottleneck_analysis",
        "from src.performance_profiler import profiler",
    ]
    
    missing_elements = []
    
    for element in required_elements:
        if element not in content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ Missing elements in test_performance.py:")
        for element in missing_elements:
            print(f"   - {element}")
        return False
    else:
        print(f"✅ All required elements present in test_performance.py")
        return True


def check_profiler_structure():
    """Check that performance profiler structure is correct."""
    print("Checking performance profiler structure...")
    
    profiler_file = project_root / "src" / "performance_profiler.py"
    
    if not profiler_file.exists():
        print(f"❌ Performance profiler file not found: {profiler_file}")
        return False
    
    with open(profiler_file, 'r') as f:
        content = f.read()
    
    required_elements = [
        "class PerformanceProfiler",
        "class ProfileResult",
        "def start_operation",
        "def end_operation",
        "def time_operation",
        "def get_pipeline_analysis",
        "def generate_report",
        "def save_report",
        "profiler = PerformanceProfiler",
    ]
    
    missing_elements = []
    
    for element in required_elements:
        if element not in content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ Missing elements in performance_profiler.py:")
        for element in missing_elements:
            print(f"   - {element}")
        return False
    else:
        print(f"✅ All required elements present in performance_profiler.py")
        return True


def main():
    """Main validation workflow."""
    print("Green-Code FX Performance Integration Check")
    print("=" * 50)
    
    checks = [
        # File existence checks
        (lambda: check_file_exists(project_root / "src" / "performance_profiler.py", "Performance Profiler"), "Performance Profiler File"),
        (lambda: check_file_exists(project_root / "tests" / "test_performance.py", "Performance Tests"), "Performance Tests File"),
        (lambda: check_file_exists(project_root / "scripts" / "simple_performance_test.py", "Simple Performance Test"), "Simple Test Script"),
        (lambda: check_file_exists(project_root / "scripts" / "run_performance_tests.py", "Performance Test Runner"), "Test Runner Script"),
        
        # Code integration checks
        (check_profiler_structure, "Profiler Structure"),
        (check_code_integration, "Video Generator Integration"),
        (check_test_structure, "Test Structure"),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_func, description in checks:
        try:
            print(f"\n{'-'*30}")
            print(f"Checking: {description}")
            print(f"{'-'*30}")
            
            if check_func():
                passed += 1
                print(f"✅ {description}: PASS")
            else:
                print(f"❌ {description}: FAIL")
                
        except Exception as e:
            print(f"❌ {description}: ERROR - {e}")
    
    # Summary
    print(f"\n{'='*50}")
    print(f"INTEGRATION CHECK SUMMARY")
    print(f"{'='*50}")
    print(f"Checks Run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print(f"\n🎉 All integration checks PASSED!")
        print(f"   Performance profiling system is properly integrated")
        print(f"   Ready for benchmarking once dependencies are installed")
        
        print(f"\nNext Steps:")
        print(f"1. Install dependencies: pip install -r requirements.txt")
        print(f"2. Run performance tests: python scripts/simple_performance_test.py")
        print(f"3. Review generated reports in output/ directory")
        
        return 0
    else:
        print(f"\n⚠️  Some integration checks FAILED!")
        print(f"   Fix the issues before running performance benchmarks")
        return 1


if __name__ == "__main__":
    sys.exit(main())
