#!/usr/bin/env python3
"""
Validation script for the performance profiling system.

This script validates that the performance profiling infrastructure is correctly
integrated without requiring pygame or actual video generation.
"""

import os
import sys
import time
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.performance_profiler import profiler, PerformanceProfiler
from src.config import config


def test_profiler_basic_functionality():
    """Test basic profiler functionality."""
    print("Testing basic profiler functionality...")
    
    # Create a test profiler
    test_profiler = PerformanceProfiler(enabled=True)
    
    # Test operation timing
    test_profiler.start_operation("test_operation", test_param="value")
    time.sleep(0.1)  # Simulate work
    result = test_profiler.end_operation("test_operation", result="success")
    
    assert result is not None, "Operation result should not be None"
    assert result.operation_name == "test_operation", "Operation name mismatch"
    assert result.duration >= 0.1, f"Duration too short: {result.duration}"
    assert result.metadata.get("result") == "success", "Metadata not preserved"
    
    print("✅ Basic profiler functionality works")


def test_profiler_decorator():
    """Test profiler decorator functionality."""
    print("Testing profiler decorator...")
    
    test_profiler = PerformanceProfiler(enabled=True)
    
    @test_profiler.time_operation("decorated_function", function_type="test")
    def test_function(duration):
        time.sleep(duration)
        return "completed"
    
    result = test_function(0.05)
    
    assert result == "completed", "Function result incorrect"
    
    # Check profiling results
    stats = test_profiler.get_operation_stats("decorated_function")
    assert stats["count"] == 1, "Operation count incorrect"
    assert stats["mean_duration"] >= 0.05, "Duration too short"
    
    print("✅ Profiler decorator works")


def test_profiler_analysis():
    """Test profiler analysis functionality."""
    print("Testing profiler analysis...")
    
    test_profiler = PerformanceProfiler(enabled=True)
    
    # Simulate multiple operations
    operations = [
        ("operation_a", 0.1),
        ("operation_b", 0.05),
        ("operation_a", 0.12),
        ("operation_c", 0.03),
    ]
    
    for op_name, duration in operations:
        test_profiler.start_operation(op_name)
        time.sleep(duration)
        test_profiler.end_operation(op_name)
    
    # Test analysis
    analysis = test_profiler.get_pipeline_analysis()
    
    assert "operations" in analysis, "Analysis missing operations"
    assert "operation_a" in analysis["operations"], "Operation A missing"
    assert "operation_b" in analysis["operations"], "Operation B missing"
    assert "operation_c" in analysis["operations"], "Operation C missing"
    
    # Check operation A stats (should have 2 calls)
    op_a_stats = analysis["operations"]["operation_a"]
    assert op_a_stats["count"] == 2, f"Operation A count wrong: {op_a_stats['count']}"
    
    print("✅ Profiler analysis works")


def test_profiler_report_generation():
    """Test profiler report generation."""
    print("Testing profiler report generation...")
    
    test_profiler = PerformanceProfiler(enabled=True)
    
    # Add some test data
    test_profiler.start_operation("report_test", category="testing")
    time.sleep(0.02)
    test_profiler.end_operation("report_test")
    
    # Generate report
    report = test_profiler.generate_report(include_raw_data=True)
    
    assert "GREEN-CODE FX PERFORMANCE PROFILING REPORT" in report, "Report header missing"
    assert "report_test" in report.upper(), "Operation not in report"
    assert "RAW TIMING DATA" in report, "Raw data section missing"
    
    print("✅ Report generation works")


def test_profiler_file_operations():
    """Test profiler file save operations."""
    print("Testing profiler file operations...")
    
    test_profiler = PerformanceProfiler(enabled=True)
    
    # Add test data
    test_profiler.start_operation("file_test")
    time.sleep(0.01)
    test_profiler.end_operation("file_test")
    
    # Test file saving
    report_path = test_profiler.save_report("test_performance_report.txt")
    json_path = test_profiler.save_json_data("test_performance_data.json")
    
    assert report_path.exists(), f"Report file not created: {report_path}"
    assert json_path.exists(), f"JSON file not created: {json_path}"
    
    # Verify file contents
    with open(report_path, 'r') as f:
        report_content = f.read()
        assert "file_test" in report_content.lower(), "Operation not in saved report"
    
    # Cleanup test files
    report_path.unlink(missing_ok=True)
    json_path.unlink(missing_ok=True)
    
    print("✅ File operations work")


def test_global_profiler_integration():
    """Test global profiler integration."""
    print("Testing global profiler integration...")
    
    # Reset global profiler
    profiler.reset()
    
    # Test global profiler usage
    profiler.start_operation("global_test", integration="test")
    time.sleep(0.01)
    result = profiler.end_operation("global_test")
    
    assert result is not None, "Global profiler result is None"
    assert result.operation_name == "global_test", "Global profiler operation name wrong"
    
    # Test analysis
    analysis = profiler.get_pipeline_analysis()
    assert "global_test" in analysis["operations"], "Global operation missing from analysis"
    
    print("✅ Global profiler integration works")


def test_configuration_integration():
    """Test configuration system integration."""
    print("Testing configuration integration...")
    
    # Test that config is accessible
    assert hasattr(config, 'OUTPUT_DIR'), "Config missing OUTPUT_DIR"
    assert hasattr(config, 'TEMP_DIR'), "Config missing TEMP_DIR"
    assert hasattr(config, 'TARGET_FPS'), "Config missing TARGET_FPS"
    
    # Test directory creation
    config.ensure_directories()
    assert config.OUTPUT_DIR.exists(), "Output directory not created"
    assert config.TEMP_DIR.exists(), "Temp directory not created"
    
    print("✅ Configuration integration works")


def validate_performance_test_structure():
    """Validate the performance test file structure."""
    print("Validating performance test structure...")
    
    # Check that performance test files exist
    test_files = [
        project_root / "tests" / "test_performance.py",
        project_root / "src" / "performance_profiler.py",
        project_root / "scripts" / "simple_performance_test.py",
    ]
    
    for test_file in test_files:
        assert test_file.exists(), f"Required file missing: {test_file}"
    
    # Check that the performance test file has the expected structure
    perf_test_file = project_root / "tests" / "test_performance.py"
    with open(perf_test_file, 'r') as f:
        content = f.read()
        
    required_elements = [
        "class TestTypingEffectPerformance",
        "test_typing_effect_small_file_performance",
        "test_typing_effect_medium_file_performance", 
        "test_typing_effect_large_file_performance",
        "test_detailed_bottleneck_analysis",
        "PerformanceBenchmark",
    ]
    
    for element in required_elements:
        assert element in content, f"Required element missing from test file: {element}"
    
    print("✅ Performance test structure is valid")


def main():
    """Main validation workflow."""
    print("Green-Code FX Performance System Validation")
    print("=" * 50)
    
    try:
        # Run all validation tests
        tests = [
            test_profiler_basic_functionality,
            test_profiler_decorator,
            test_profiler_analysis,
            test_profiler_report_generation,
            test_profiler_file_operations,
            test_global_profiler_integration,
            test_configuration_integration,
            validate_performance_test_structure,
        ]
        
        passed = 0
        total = len(tests)
        
        for test_func in tests:
            try:
                test_func()
                passed += 1
            except Exception as e:
                print(f"❌ {test_func.__name__} failed: {e}")
        
        # Summary
        print(f"\n{'='*50}")
        print(f"VALIDATION SUMMARY")
        print(f"{'='*50}")
        print(f"Tests Run: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print(f"\n🎉 All validation tests PASSED!")
            print(f"   Performance profiling system is ready for use")
            print(f"   To run actual performance benchmarks, install pygame and run:")
            print(f"   python scripts/simple_performance_test.py")
            return 0
        else:
            print(f"\n⚠️  Some validation tests FAILED!")
            print(f"   Fix the issues before running performance benchmarks")
            return 1
            
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
