#!/usr/bin/env python3
"""
Simple performance test runner for Green-Code FX typing effect.

This script runs a basic performance benchmark without pytest dependencies
to validate the typing effect generation speed against PRD requirements.
"""

import os
import sys
import time
import tempfile
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.video_generator import VideoGenerator
from src.config import config
from src.performance_profiler import profiler


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


def create_test_source_file(line_count: int, chars_per_line: int = 80) -> Path:
    """Create a test source code file with specified characteristics."""
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    
    # Generate realistic code content
    code_patterns = [
        "def function_name(param1, param2):",
        "    if condition:",
        "        return process_data(param1)",
        "    else:",
        "        raise ValueError('Invalid input')",
        "",
        "class ExampleClass:",
        "    def __init__(self, value):",
        "        self.value = value",
        "        self.processed = False",
        "",
        "    def process(self):",
        "        if not self.processed:",
        "            self.value = transform(self.value)",
        "            self.processed = True",
        "        return self.value",
    ]
    
    for i in range(line_count):
        line = code_patterns[i % len(code_patterns)]
        # Pad or truncate to approximate target length
        if len(line) < chars_per_line:
            line += " " * (chars_per_line - len(line) - 10) + f"# Line {i+1}"
        elif len(line) > chars_per_line:
            line = line[:chars_per_line-3] + "..."
        
        temp_file.write(line + "\n")
    
    temp_file.close()
    return Path(temp_file.name)


def cleanup_test_files(job_id: str):
    """Clean up test files after benchmark."""
    output_dir = config.OUTPUT_DIR
    temp_dir = config.TEMP_DIR
    
    for pattern in [f"{job_id}*", f"perf_test*"]:
        for file_path in output_dir.glob(pattern):
            file_path.unlink(missing_ok=True)
        for file_path in temp_dir.glob(pattern):
            if file_path.is_dir():
                import shutil
                shutil.rmtree(file_path, ignore_errors=True)
            else:
                file_path.unlink(missing_ok=True)


def run_performance_test(test_name: str, line_count: int, duration: int):
    """Run a single performance test."""
    print(f"\n{'='*60}")
    print(f"RUNNING: {test_name}")
    print(f"{'='*60}")
    print(f"  Source Lines: {line_count}")
    print(f"  Duration: {duration}s")
    print(f"  Target: ≤2.0x realtime")
    
    # Create video generator
    video_generator = VideoGenerator()
    
    # Create test file
    test_file = create_test_source_file(line_count, 80)
    job_id = f"perf_test_{test_name.lower().replace(' ', '_')}"
    
    try:
        # Reset profiler for clean analysis
        profiler.reset()
        
        # Measure total generation time
        start_time = time.perf_counter()
        result = video_generator.generate_typing_effect(
            job_id=job_id,
            duration=duration,
            source_file=test_file.name,
            output_format="png"  # Skip FFmpeg for pure rendering performance
        )
        total_time = time.perf_counter() - start_time
        
        # Calculate performance metrics
        realtime_duration = duration
        generation_ratio = total_time / realtime_duration
        
        print(f"\nRESULTS:")
        print(f"  Generation Time: {total_time:.3f}s")
        print(f"  Ratio: {generation_ratio:.2f}x realtime")
        print(f"  Status: {'PASS' if generation_ratio <= 2.0 else 'FAIL'}")
        
        # Generate profiling report
        analysis = profiler.get_pipeline_analysis()
        if "operations" in analysis:
            print(f"\nPIPELINE BREAKDOWN:")
            sorted_ops = sorted(
                analysis["operations"].items(),
                key=lambda x: x[1]["total_duration"],
                reverse=True
            )
            
            for op_name, stats in sorted_ops[:5]:  # Top 5 operations
                print(f"  {op_name}: {stats['percentage_of_total']:.1f}% "
                      f"({stats['total_duration']:.3f}s)")
        
        return generation_ratio <= 2.0, generation_ratio
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False, float('inf')
        
    finally:
        # Cleanup
        test_file.unlink(missing_ok=True)
        cleanup_test_files(job_id)


def run_detailed_bottleneck_analysis():
    """Run detailed bottleneck analysis."""
    print(f"\n{'='*60}")
    print(f"DETAILED BOTTLENECK ANALYSIS")
    print(f"{'='*60}")
    
    # Create video generator
    video_generator = VideoGenerator()
    
    # Create test file
    test_file = create_test_source_file(100, 80)
    job_id = "bottleneck_analysis"
    
    try:
        # Reset profiler for clean analysis
        profiler.reset()
        
        duration = 5  # Short duration for detailed analysis
        
        print(f"Analyzing {duration}s generation with 100-line source file...")
        
        # Generate video with profiling
        start_time = time.perf_counter()
        result = video_generator.generate_typing_effect(
            job_id=job_id,
            duration=duration,
            source_file=test_file.name,
            output_format="png"
        )
        total_time = time.perf_counter() - start_time
        
        # Generate detailed profiling report
        profiling_report = profiler.generate_report(include_raw_data=False)
        print(f"\n{profiling_report}")
        
        # Save profiling data
        report_path = profiler.save_report("typing_effect_bottleneck_analysis.txt")
        data_path = profiler.save_json_data("typing_effect_bottleneck_data.json")
        
        print(f"\nReports saved:")
        print(f"  Text Report: {report_path}")
        print(f"  JSON Data: {data_path}")
        
        # Performance analysis
        generation_ratio = total_time / duration
        print(f"\nPERFORMANCE SUMMARY:")
        print(f"  Total Time: {total_time:.3f}s")
        print(f"  Ratio: {generation_ratio:.2f}x realtime")
        print(f"  Requirement: ≤2.0x realtime")
        print(f"  Status: {'PASS' if generation_ratio <= 2.0 else 'FAIL'}")
        
        return generation_ratio <= 2.0
        
    except Exception as e:
        print(f"❌ Bottleneck analysis failed: {e}")
        return False
        
    finally:
        # Cleanup
        test_file.unlink(missing_ok=True)
        cleanup_test_files(job_id)


def main():
    """Main performance testing workflow."""
    print("Green-Code FX Typing Effect Performance Benchmark")
    print("=" * 60)
    
    try:
        # Setup
        setup_environment()
        
        # Run performance tests
        tests = [
            ("Small File Test", 50, 10),
            ("Medium File Test", 200, 15),
            ("Large File Test", 500, 20),
        ]
        
        results = []
        
        for test_name, line_count, duration in tests:
            passed, ratio = run_performance_test(test_name, line_count, duration)
            results.append((test_name, passed, ratio))
        
        # Run detailed analysis
        print(f"\n" + "="*60)
        analysis_passed = run_detailed_bottleneck_analysis()
        
        # Summary
        print(f"\n{'='*60}")
        print(f"PERFORMANCE BENCHMARK SUMMARY")
        print(f"{'='*60}")
        
        passed_count = sum(1 for _, passed, _ in results if passed)
        total_count = len(results)
        
        print(f"Basic Tests: {passed_count}/{total_count} passed")
        print(f"Detailed Analysis: {'PASS' if analysis_passed else 'FAIL'}")
        
        print(f"\nDetailed Results:")
        for test_name, passed, ratio in results:
            status = "PASS" if passed else "FAIL"
            print(f"  {status}: {test_name} ({ratio:.2f}x realtime)")
        
        # Overall result
        all_passed = passed_count == total_count and analysis_passed
        
        if all_passed:
            print(f"\n🎉 All performance benchmarks PASSED!")
            print(f"   Typing effect generation meets ≤2x realtime requirement")
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
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
