#!/usr/bin/env python3
"""
Simple Matrix effect performance testing script for Green-Code FX.

This script provides a quick way to benchmark Matrix rain effect generation
performance without the full pytest framework overhead.
"""

import os
import sys
import time
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.video_generator import VideoGenerator
from src.config import config
from src.performance_profiler import profiler


def setup_environment():
    """Setup the testing environment."""
    # Ensure headless operation
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    
    # Ensure output directories exist
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    config.TEMP_DIR.mkdir(exist_ok=True)
    
    print(f"Environment setup complete:")
    print(f"  SDL Video Driver: {os.environ.get('SDL_VIDEODRIVER', 'default')}")
    print(f"  Output Directory: {config.OUTPUT_DIR}")
    print(f"  Temp Directory: {config.TEMP_DIR}")


def cleanup_test_files(job_id: str):
    """Clean up test files after benchmark."""
    output_dir = config.OUTPUT_DIR
    temp_dir = config.TEMP_DIR
    
    for pattern in [f"{job_id}*", f"matrix_perf*"]:
        for file_path in output_dir.glob(pattern):
            file_path.unlink(missing_ok=True)
        for file_path in temp_dir.glob(pattern):
            if file_path.is_dir():
                import shutil
                shutil.rmtree(file_path, ignore_errors=True)
            else:
                file_path.unlink(missing_ok=True)


def run_matrix_performance_test(test_name: str, duration: int):
    """Run a single Matrix effect performance test."""
    print(f"\n{'='*60}")
    print(f"RUNNING: {test_name}")
    print(f"{'='*60}")
    print(f"  Duration: {duration}s")
    print(f"  Target: ≤1.5x realtime")
    
    # Create video generator
    video_generator = VideoGenerator()
    
    job_id = f"matrix_perf_test_{test_name.lower().replace(' ', '_')}"
    
    try:
        # Reset profiler for clean analysis
        profiler.reset()
        
        # Measure total generation time
        start_time = time.perf_counter()
        result = video_generator.generate_matrix_rain(
            job_id=job_id,
            duration=duration,
            loop_seamless=True,
            output_format="png"  # Skip FFmpeg for pure rendering performance
        )
        total_time = time.perf_counter() - start_time
        
        # Calculate performance metrics
        realtime_duration = duration
        generation_ratio = total_time / realtime_duration
        
        print(f"\nRESULTS:")
        print(f"  Generation Time: {total_time:.3f}s")
        print(f"  Ratio: {generation_ratio:.2f}x realtime")
        print(f"  Status: {'PASS' if generation_ratio <= 1.5 else 'FAIL'}")
        
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
        
        return generation_ratio <= 1.5, generation_ratio
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False, float('inf')
        
    finally:
        # Cleanup
        cleanup_test_files(job_id)


def run_matrix_bottleneck_analysis():
    """Run detailed bottleneck analysis for Matrix effect."""
    print(f"\n{'='*60}")
    print(f"MATRIX EFFECT BOTTLENECK ANALYSIS")
    print(f"{'='*60}")
    
    # Create video generator
    video_generator = VideoGenerator()
    
    job_id = "matrix_bottleneck_analysis"
    
    try:
        # Reset profiler for clean analysis
        profiler.reset()
        
        duration = 10  # Medium duration for detailed analysis
        
        print(f"Analyzing {duration}s Matrix generation...")
        
        # Generate video with profiling
        start_time = time.perf_counter()
        result = video_generator.generate_matrix_rain(
            job_id=job_id,
            duration=duration,
            loop_seamless=True,
            output_format="png"
        )
        total_time = time.perf_counter() - start_time
        
        # Calculate performance metrics
        generation_ratio = total_time / duration
        
        print(f"\nPERFORMANCE SUMMARY:")
        print(f"  Total Time: {total_time:.3f}s")
        print(f"  Ratio: {generation_ratio:.2f}x realtime")
        print(f"  Requirement: ≤1.5x realtime")
        print(f"  Status: {'PASS' if generation_ratio <= 1.5 else 'FAIL'}")
        
        # Generate detailed profiling report
        profiling_report = profiler.generate_report(include_raw_data=False)
        print(f"\n{profiling_report}")
        
        # Save profiling data
        profiler.save_report("matrix_simple_bottleneck_analysis.txt")
        profiler.save_json_data("matrix_simple_bottleneck_data.json")
        
        # Analyze bottlenecks
        analysis = profiler.get_pipeline_analysis()
        
        if "operations" in analysis:
            sorted_ops = sorted(
                analysis["operations"].items(),
                key=lambda x: x[1]["total_duration"],
                reverse=True
            )
            
            print(f"\nTOP BOTTLENECKS:")
            for i, (op_name, stats) in enumerate(sorted_ops[:5]):
                print(f"  {i+1}. {op_name}: {stats['percentage_of_total']:.1f}% "
                      f"({stats['total_duration']:.3f}s)")
            
            # Matrix-specific recommendations
            print(f"\nOPTIMIZATION RECOMMENDATIONS:")
            main_loop_stats = analysis["operations"].get("main_rendering_loop", {})
            if main_loop_stats.get("percentage_of_total", 0) > 70:
                print(f"  - Main rendering loop dominates ({main_loop_stats['percentage_of_total']:.1f}%)")
                print(f"  - Consider optimizing column processing and character rendering")
                print(f"  - Reduce per-character font rendering calls")
            
            frame_save_stats = analysis["operations"].get("save_frame", {})
            if frame_save_stats.get("percentage_of_total", 0) > 20:
                print(f"  - Frame saving overhead ({frame_save_stats['percentage_of_total']:.1f}%)")
                print(f"  - Consider faster image formats or compression")
            
            font_load_stats = analysis["operations"].get("load_font", {})
            if font_load_stats.get("percentage_of_total", 0) > 5:
                print(f"  - Font loading overhead ({font_load_stats['percentage_of_total']:.1f}%)")
                print(f"  - Consider font caching for multiple sizes")
        
        return generation_ratio <= 1.5
        
    except Exception as e:
        print(f"❌ Bottleneck analysis failed: {e}")
        return False
        
    finally:
        # Cleanup
        cleanup_test_files(job_id)


def main():
    """Main Matrix effect performance testing workflow."""
    print("Green-Code FX Matrix Effect Performance Benchmark")
    print("=" * 60)
    
    try:
        # Setup
        setup_environment()
        
        # Run performance tests
        tests = [
            ("Short Duration Test", 5),
            ("Standard Duration Test", 15),
            ("Extended Duration Test", 30),
        ]
        
        results = []
        
        for test_name, duration in tests:
            passed, ratio = run_matrix_performance_test(test_name, duration)
            results.append((test_name, passed, ratio))
        
        # Run bottleneck analysis
        print(f"\n" + "="*60)
        bottleneck_passed = run_matrix_bottleneck_analysis()
        
        # Summary
        print(f"\n" + "="*60)
        print(f"FINAL SUMMARY")
        print(f"="*60)
        
        all_passed = True
        for test_name, passed, ratio in results:
            status = "PASS" if passed else "FAIL"
            print(f"  {status}: {test_name} ({ratio:.2f}x realtime)")
            if not passed:
                all_passed = False
        
        bottleneck_status = "PASS" if bottleneck_passed else "FAIL"
        print(f"  {bottleneck_status}: Bottleneck Analysis")
        if not bottleneck_passed:
            all_passed = False
        
        if all_passed:
            print(f"\n🎉 All Matrix effect benchmarks PASSED!")
            print(f"   Matrix generation meets ≤1.5x realtime requirement")
            return 0
        else:
            print(f"\n⚠️  Some Matrix effect benchmarks FAILED!")
            print(f"   Matrix generation does not meet ≤1.5x realtime requirement")
            print(f"   Review the bottleneck analysis for optimization opportunities")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Matrix performance testing interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Matrix performance testing failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
