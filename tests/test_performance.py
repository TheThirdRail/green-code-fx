"""
Performance benchmarking tests for Green-Code FX video effects generator.

This module provides comprehensive performance testing for typing and Matrix effects,
measuring generation speeds against PRD requirements and identifying bottlenecks.
"""

import os
import time
import tempfile
import statistics
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pytest
import psutil

# Import the modules to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.video_generator import VideoGenerator
from src.config import config
from src.performance_profiler import profiler


class PerformanceBenchmark:
    """Performance benchmarking utilities for video generation."""
    
    def __init__(self):
        """Initialize performance benchmark utilities."""
        self.results: Dict[str, List[float]] = {}
        self.system_info = self._get_system_info()
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get system information for benchmark context."""
        return {
            "cpu_count": str(psutil.cpu_count()),
            "cpu_freq": f"{psutil.cpu_freq().current:.0f}MHz" if psutil.cpu_freq() else "Unknown",
            "memory_total": f"{psutil.virtual_memory().total / (1024**3):.1f}GB",
            "python_version": sys.version.split()[0],
            "platform": sys.platform
        }
    
    def time_function(self, func_name: str, func, *args, **kwargs) -> Tuple[any, float]:
        """
        Time a function execution with high precision.
        
        Args:
            func_name: Name for storing results
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Tuple of (function_result, execution_time_seconds)
        """
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        execution_time = end_time - start_time
        
        if func_name not in self.results:
            self.results[func_name] = []
        self.results[func_name].append(execution_time)
        
        return result, execution_time
    
    def get_statistics(self, func_name: str) -> Dict[str, float]:
        """
        Get statistical analysis of timing results.
        
        Args:
            func_name: Name of the timed function
            
        Returns:
            Dictionary with timing statistics
        """
        if func_name not in self.results or not self.results[func_name]:
            return {}
        
        times = self.results[func_name]
        return {
            "count": len(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "min": min(times),
            "max": max(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0.0
        }
    
    def generate_report(self) -> str:
        """
        Generate a comprehensive performance report.
        
        Returns:
            Formatted performance report string
        """
        report = ["=" * 80]
        report.append("GREEN-CODE FX PERFORMANCE BENCHMARK REPORT")
        report.append("=" * 80)
        report.append("")
        
        # System information
        report.append("SYSTEM INFORMATION:")
        for key, value in self.system_info.items():
            report.append(f"  {key.replace('_', ' ').title()}: {value}")
        report.append("")
        
        # Performance results
        report.append("PERFORMANCE RESULTS:")
        report.append("-" * 40)
        
        for func_name, stats in [(name, self.get_statistics(name)) for name in self.results.keys()]:
            if not stats:
                continue
                
            report.append(f"\n{func_name.upper()}:")
            report.append(f"  Runs: {stats['count']}")
            report.append(f"  Mean: {stats['mean']:.3f}s")
            report.append(f"  Median: {stats['median']:.3f}s")
            report.append(f"  Min: {stats['min']:.3f}s")
            report.append(f"  Max: {stats['max']:.3f}s")
            if stats['stdev'] > 0:
                report.append(f"  Std Dev: {stats['stdev']:.3f}s")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


class TestTypingEffectPerformance:
    """Performance tests for typing effect generation."""
    
    @pytest.fixture
    def benchmark(self):
        """Create a performance benchmark instance."""
        return PerformanceBenchmark()
    
    @pytest.fixture
    def video_generator(self):
        """Create a video generator instance with headless SDL."""
        # Ensure headless operation
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        return VideoGenerator()
    
    def create_test_source_file(self, line_count: int, chars_per_line: int = 80) -> Path:
        """
        Create a test source code file with specified characteristics.
        
        Args:
            line_count: Number of lines to generate
            chars_per_line: Average characters per line
            
        Returns:
            Path to the created test file
        """
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
    
    def test_typing_effect_small_file_performance(self, benchmark, video_generator):
        """Test performance with small source file (50 lines)."""
        # Create test file
        test_file = self.create_test_source_file(50, 60)
        
        try:
            # Test short duration for quick benchmark
            duration = 10  # 10 seconds
            job_id = "perf_test_small"
            
            # Measure total generation time
            result, total_time = benchmark.time_function(
                "typing_small_total",
                video_generator.generate_typing_effect,
                job_id=job_id,
                duration=duration,
                source_file=test_file.name,
                output_format="png"  # Skip FFmpeg for pure rendering performance
            )
            
            # Calculate performance metrics
            realtime_duration = duration
            generation_ratio = total_time / realtime_duration
            
            print(f"\nSmall File Performance:")
            print(f"  Duration: {duration}s")
            print(f"  Generation Time: {total_time:.3f}s")
            print(f"  Ratio: {generation_ratio:.2f}x realtime")
            print(f"  Target: ≤2.0x realtime")
            print(f"  Status: {'PASS' if generation_ratio <= 2.0 else 'FAIL'}")
            
            # Verify requirement
            assert generation_ratio <= 2.0, f"Generation too slow: {generation_ratio:.2f}x > 2.0x realtime"
            
        finally:
            # Cleanup
            test_file.unlink(missing_ok=True)
            # Clean up any generated files
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
    
    def test_typing_effect_medium_file_performance(self, benchmark, video_generator):
        """Test performance with medium source file (200 lines)."""
        # Create test file
        test_file = self.create_test_source_file(200, 80)
        
        try:
            duration = 15  # 15 seconds
            job_id = "perf_test_medium"
            
            # Measure total generation time
            result, total_time = benchmark.time_function(
                "typing_medium_total",
                video_generator.generate_typing_effect,
                job_id=job_id,
                duration=duration,
                source_file=test_file.name,
                output_format="png"
            )
            
            # Calculate performance metrics
            realtime_duration = duration
            generation_ratio = total_time / realtime_duration
            
            print(f"\nMedium File Performance:")
            print(f"  Duration: {duration}s")
            print(f"  Generation Time: {total_time:.3f}s")
            print(f"  Ratio: {generation_ratio:.2f}x realtime")
            print(f"  Target: ≤2.0x realtime")
            print(f"  Status: {'PASS' if generation_ratio <= 2.0 else 'FAIL'}")
            
            # Verify requirement
            assert generation_ratio <= 2.0, f"Generation too slow: {generation_ratio:.2f}x > 2.0x realtime"
            
        finally:
            # Cleanup
            test_file.unlink(missing_ok=True)
            # Clean up generated files
            self._cleanup_test_files(job_id)
    
    def test_typing_effect_large_file_performance(self, benchmark, video_generator):
        """Test performance with large source file (500 lines)."""
        # Create test file
        test_file = self.create_test_source_file(500, 100)
        
        try:
            duration = 20  # 20 seconds
            job_id = "perf_test_large"
            
            # Measure total generation time
            result, total_time = benchmark.time_function(
                "typing_large_total",
                video_generator.generate_typing_effect,
                job_id=job_id,
                duration=duration,
                source_file=test_file.name,
                output_format="png"
            )
            
            # Calculate performance metrics
            realtime_duration = duration
            generation_ratio = total_time / realtime_duration
            
            print(f"\nLarge File Performance:")
            print(f"  Duration: {duration}s")
            print(f"  Generation Time: {total_time:.3f}s")
            print(f"  Ratio: {generation_ratio:.2f}x realtime")
            print(f"  Target: ≤2.0x realtime")
            print(f"  Status: {'PASS' if generation_ratio <= 2.0 else 'FAIL'}")
            
            # Verify requirement
            assert generation_ratio <= 2.0, f"Generation too slow: {generation_ratio:.2f}x > 2.0x realtime"
            
        finally:
            # Cleanup
            test_file.unlink(missing_ok=True)
            self._cleanup_test_files(job_id)
    
    def _cleanup_test_files(self, job_id: str):
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
    
    def test_detailed_bottleneck_analysis(self, video_generator):
        """Perform detailed bottleneck analysis using the performance profiler."""
        # Reset profiler for clean analysis
        profiler.reset()

        # Create test file
        test_file = self.create_test_source_file(100, 80)

        try:
            duration = 5  # Short duration for detailed analysis
            job_id = "bottleneck_analysis"

            print(f"\nPerforming detailed bottleneck analysis...")

            # Generate video with profiling
            start_time = time.perf_counter()
            result = video_generator.generate_typing_effect(
                job_id=job_id,
                duration=duration,
                source_file=test_file.name,
                output_format="png"  # Skip FFmpeg for pure rendering analysis
            )
            total_time = time.perf_counter() - start_time

            # Generate detailed profiling report
            profiling_report = profiler.generate_report(include_raw_data=False)
            print(f"\n{profiling_report}")

            # Save profiling data
            profiler.save_report("typing_effect_bottleneck_analysis.txt")
            profiler.save_json_data("typing_effect_bottleneck_data.json")

            # Analyze bottlenecks
            analysis = profiler.get_pipeline_analysis()

            print(f"\nBOTTLENECK ANALYSIS:")
            print(f"  Total Generation Time: {total_time:.3f}s")
            print(f"  Target Duration: {duration}s")
            print(f"  Performance Ratio: {total_time/duration:.2f}x realtime")
            print(f"  Target Requirement: ≤2.0x realtime")
            print(f"  Status: {'PASS' if total_time/duration <= 2.0 else 'FAIL'}")

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

            # Performance recommendations
            print(f"\nPERFORMANCE RECOMMENDATIONS:")
            if "operations" in analysis:
                main_loop_stats = analysis["operations"].get("main_rendering_loop", {})
                if main_loop_stats.get("percentage_of_total", 0) > 70:
                    print(f"  - Main rendering loop is the primary bottleneck ({main_loop_stats['percentage_of_total']:.1f}%)")
                    print(f"  - Consider optimizing pygame rendering operations")
                    print(f"  - Reduce font rendering calls or cache text surfaces")

                frame_save_stats = analysis["operations"].get("save_frame", {})
                if frame_save_stats.get("percentage_of_total", 0) > 20:
                    print(f"  - Frame saving is significant bottleneck ({frame_save_stats['percentage_of_total']:.1f}%)")
                    print(f"  - Consider using faster image formats or compression")

                font_load_stats = analysis["operations"].get("load_font", {})
                if font_load_stats.get("percentage_of_total", 0) > 5:
                    print(f"  - Font loading overhead detected ({font_load_stats['percentage_of_total']:.1f}%)")
                    print(f"  - Consider font caching or preloading")

            # Verify performance requirement
            assert total_time/duration <= 2.0, f"Performance requirement not met: {total_time/duration:.2f}x > 2.0x realtime"

        finally:
            # Cleanup
            test_file.unlink(missing_ok=True)
            self._cleanup_test_files(job_id)

    def test_generate_performance_report(self, benchmark):
        """Generate and display comprehensive performance report."""
        # This test should run after the other performance tests
        report = benchmark.generate_report()
        print(f"\n{report}")

        # Save report to file
        report_file = config.OUTPUT_DIR / "typing_effect_performance_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)

        print(f"\nPerformance report saved to: {report_file}")




class TestLoadTesting:
    """Load testing for concurrent video generation."""

    @pytest.fixture
    def video_generator(self):
        """Create a video generator instance with headless SDL."""
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        return VideoGenerator()

    def test_concurrent_typing_jobs(self, video_generator):
        """Test multiple concurrent typing effect jobs."""
        import threading
        import time

        num_jobs = 3
        duration = 10  # Short duration for testing
        results = {}

        def generate_job(job_id):
            try:
                start_time = time.perf_counter()
                video_generator.generate_typing_effect(
                    job_id=f"load_test_typing_{job_id}",
                    duration=duration,
                    source_file="snake_code.txt",
                    output_format="png"  # Skip FFmpeg for faster testing
                )
                end_time = time.perf_counter()
                results[job_id] = {
                    "success": True,
                    "duration": end_time - start_time,
                    "ratio": (end_time - start_time) / duration
                }
            except Exception as e:
                results[job_id] = {
                    "success": False,
                    "error": str(e)
                }

        # Start concurrent jobs
        threads = []
        start_time = time.perf_counter()

        for i in range(num_jobs):
            thread = threading.Thread(target=generate_job, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all jobs to complete
        for thread in threads:
            thread.join(timeout=300)  # 5 minute timeout per job

        total_time = time.perf_counter() - start_time

        # Analyze results
        successful_jobs = [r for r in results.values() if r.get("success")]
        failed_jobs = [r for r in results.values() if not r.get("success")]

        print(f"\nLOAD TEST RESULTS - CONCURRENT TYPING JOBS:")
        print(f"  Total Jobs: {num_jobs}")
        print(f"  Successful: {len(successful_jobs)}")
        print(f"  Failed: {len(failed_jobs)}")
        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Average Job Time: {sum(r['duration'] for r in successful_jobs) / len(successful_jobs):.2f}s")
        print(f"  Average Ratio: {sum(r['ratio'] for r in successful_jobs) / len(successful_jobs):.2f}x realtime")

        # Verify all jobs succeeded
        assert len(failed_jobs) == 0, f"Failed jobs: {failed_jobs}"

        # Verify performance is reasonable (allowing for overhead)
        avg_ratio = sum(r['ratio'] for r in successful_jobs) / len(successful_jobs)
        assert avg_ratio <= 3.0, f"Average performance too slow: {avg_ratio:.2f}x > 3.0x realtime"




if __name__ == "__main__":
    # Run performance tests directly
    pytest.main([__file__, "-v", "-s"])
