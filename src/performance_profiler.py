"""
Performance profiling utilities for Green-Code FX video generation pipeline.

This module provides detailed performance analysis of individual pipeline stages
to identify bottlenecks and optimization opportunities.
"""

import time
import functools
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from pathlib import Path
import json

import structlog

from .config import config


logger = structlog.get_logger()


@dataclass
class ProfileResult:
    """Performance profiling result for a single operation."""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds."""
        return self.duration * 1000


class PerformanceProfiler:
    """
    Performance profiler for video generation pipeline.
    
    Provides detailed timing analysis of individual operations to identify
    bottlenecks and optimization opportunities.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize performance profiler.
        
        Args:
            enabled: Whether profiling is enabled
        """
        self.enabled = enabled
        self.results: List[ProfileResult] = []
        self.active_operations: Dict[str, float] = {}
        self.session_start = time.perf_counter()
    
    def start_operation(self, operation_name: str, **metadata) -> None:
        """
        Start timing an operation.
        
        Args:
            operation_name: Name of the operation being timed
            **metadata: Additional metadata to store with the result
        """
        if not self.enabled:
            return
        
        start_time = time.perf_counter()
        self.active_operations[operation_name] = start_time
        
        logger.debug("Performance: Started operation", 
                    operation=operation_name, 
                    metadata=metadata)
    
    def end_operation(self, operation_name: str, **metadata) -> Optional[ProfileResult]:
        """
        End timing an operation and record the result.
        
        Args:
            operation_name: Name of the operation being timed
            **metadata: Additional metadata to store with the result
            
        Returns:
            ProfileResult if operation was being timed, None otherwise
        """
        if not self.enabled or operation_name not in self.active_operations:
            return None
        
        end_time = time.perf_counter()
        start_time = self.active_operations.pop(operation_name)
        duration = end_time - start_time
        
        result = ProfileResult(
            operation_name=operation_name,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            metadata=metadata
        )
        
        self.results.append(result)
        
        logger.info("Performance: Completed operation",
                   operation=operation_name,
                   duration_ms=result.duration_ms,
                   metadata=metadata)
        
        return result
    
    def time_operation(self, operation_name: str, **metadata):
        """
        Decorator to time a function or method.
        
        Args:
            operation_name: Name of the operation being timed
            **metadata: Additional metadata to store with the result
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                self.start_operation(operation_name, **metadata)
                try:
                    result = func(*args, **kwargs)
                    self.end_operation(operation_name, success=True, **metadata)
                    return result
                except Exception as e:
                    self.end_operation(operation_name, success=False, error=str(e), **metadata)
                    raise
            return wrapper
        return decorator
    
    def get_operation_stats(self, operation_name: str) -> Dict[str, float]:
        """
        Get statistical analysis for a specific operation.
        
        Args:
            operation_name: Name of the operation to analyze
            
        Returns:
            Dictionary with timing statistics
        """
        operation_results = [r for r in self.results if r.operation_name == operation_name]
        
        if not operation_results:
            return {}
        
        durations = [r.duration for r in operation_results]
        
        return {
            "count": len(durations),
            "total_duration": sum(durations),
            "mean_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_duration_ms": sum(durations) * 1000,
            "mean_duration_ms": (sum(durations) / len(durations)) * 1000
        }
    
    def get_pipeline_analysis(self) -> Dict[str, Any]:
        """
        Get comprehensive pipeline performance analysis.
        
        Returns:
            Dictionary with detailed pipeline analysis
        """
        if not self.results:
            return {"error": "No profiling results available"}
        
        # Group results by operation
        operations = {}
        for result in self.results:
            op_name = result.operation_name
            if op_name not in operations:
                operations[op_name] = []
            operations[op_name].append(result)
        
        # Calculate statistics for each operation
        analysis = {
            "session_duration": time.perf_counter() - self.session_start,
            "total_operations": len(self.results),
            "unique_operations": len(operations),
            "operations": {}
        }
        
        total_time = 0
        for op_name, op_results in operations.items():
            durations = [r.duration for r in op_results]
            op_total = sum(durations)
            total_time += op_total
            
            analysis["operations"][op_name] = {
                "count": len(durations),
                "total_duration": op_total,
                "mean_duration": op_total / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "percentage_of_total": 0  # Will be calculated after total_time is known
            }
        
        # Calculate percentages
        if total_time > 0:
            for op_name in analysis["operations"]:
                op_total = analysis["operations"][op_name]["total_duration"]
                analysis["operations"][op_name]["percentage_of_total"] = (op_total / total_time) * 100
        
        analysis["total_measured_time"] = total_time
        
        return analysis
    
    def generate_report(self, include_raw_data: bool = False) -> str:
        """
        Generate a comprehensive performance report.
        
        Args:
            include_raw_data: Whether to include raw timing data
            
        Returns:
            Formatted performance report
        """
        analysis = self.get_pipeline_analysis()
        
        if "error" in analysis:
            return f"Performance Report Error: {analysis['error']}"
        
        report = []
        report.append("=" * 80)
        report.append("GREEN-CODE FX PERFORMANCE PROFILING REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Session overview
        report.append("SESSION OVERVIEW:")
        report.append(f"  Total Session Duration: {analysis['session_duration']:.3f}s")
        report.append(f"  Total Operations: {analysis['total_operations']}")
        report.append(f"  Unique Operation Types: {analysis['unique_operations']}")
        report.append(f"  Total Measured Time: {analysis['total_measured_time']:.3f}s")
        report.append("")
        
        # Operation breakdown
        report.append("OPERATION BREAKDOWN:")
        report.append("-" * 60)
        
        # Sort operations by total time (descending)
        sorted_ops = sorted(
            analysis["operations"].items(),
            key=lambda x: x[1]["total_duration"],
            reverse=True
        )
        
        for op_name, stats in sorted_ops:
            report.append(f"\n{op_name.upper()}:")
            report.append(f"  Count: {stats['count']}")
            report.append(f"  Total Time: {stats['total_duration']:.3f}s ({stats['percentage_of_total']:.1f}%)")
            report.append(f"  Mean Time: {stats['mean_duration']:.3f}s")
            report.append(f"  Min Time: {stats['min_duration']:.3f}s")
            report.append(f"  Max Time: {stats['max_duration']:.3f}s")
        
        # Performance insights
        report.append("\n")
        report.append("PERFORMANCE INSIGHTS:")
        report.append("-" * 40)
        
        if sorted_ops:
            # Identify bottlenecks
            top_operation = sorted_ops[0]
            report.append(f"  Primary Bottleneck: {top_operation[0]} ({top_operation[1]['percentage_of_total']:.1f}% of total time)")
            
            # Identify frequent operations
            most_frequent = max(sorted_ops, key=lambda x: x[1]['count'])
            report.append(f"  Most Frequent Operation: {most_frequent[0]} ({most_frequent[1]['count']} calls)")
            
            # Calculate efficiency metrics
            overhead_ratio = (analysis['session_duration'] - analysis['total_measured_time']) / analysis['session_duration']
            report.append(f"  Measurement Overhead: {overhead_ratio * 100:.1f}%")
        
        if include_raw_data:
            report.append("\n")
            report.append("RAW TIMING DATA:")
            report.append("-" * 40)
            for result in self.results:
                report.append(f"  {result.operation_name}: {result.duration:.6f}s")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, filename: Optional[str] = None) -> Path:
        """
        Save performance report to file.
        
        Args:
            filename: Optional filename, defaults to timestamped name
            
        Returns:
            Path to the saved report file
        """
        if filename is None:
            timestamp = int(time.time())
            filename = f"performance_report_{timestamp}.txt"
        
        report_path = config.OUTPUT_DIR / filename
        report_content = self.generate_report(include_raw_data=True)
        
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        logger.info("Performance report saved", file_path=str(report_path))
        return report_path
    
    def save_json_data(self, filename: Optional[str] = None) -> Path:
        """
        Save raw profiling data as JSON for further analysis.
        
        Args:
            filename: Optional filename, defaults to timestamped name
            
        Returns:
            Path to the saved JSON file
        """
        if filename is None:
            timestamp = int(time.time())
            filename = f"performance_data_{timestamp}.json"
        
        data_path = config.OUTPUT_DIR / filename
        
        # Convert results to JSON-serializable format
        json_data = {
            "session_start": self.session_start,
            "session_duration": time.perf_counter() - self.session_start,
            "results": [
                {
                    "operation_name": r.operation_name,
                    "start_time": r.start_time,
                    "end_time": r.end_time,
                    "duration": r.duration,
                    "metadata": r.metadata
                }
                for r in self.results
            ],
            "analysis": self.get_pipeline_analysis()
        }
        
        with open(data_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        logger.info("Performance data saved", file_path=str(data_path))
        return data_path
    
    def reset(self) -> None:
        """Reset profiler state for a new session."""
        self.results.clear()
        self.active_operations.clear()
        self.session_start = time.perf_counter()
        
        logger.info("Performance profiler reset")


# Global profiler instance
profiler = PerformanceProfiler(enabled=True)
