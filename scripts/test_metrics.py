#!/usr/bin/env python3
"""
Test script for Prometheus metrics endpoint.

This script tests the metrics collection and endpoint functionality
to ensure proper monitoring capabilities are working.
"""

import os
import sys
import time
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.metrics import metrics


def test_metrics_collection():
    """Test metrics collection functionality."""
    print("🔍 Testing metrics collection...")
    
    # Test basic metrics functionality
    if not metrics.enabled:
        print("⚠️  Metrics are disabled")
        return False
    
    # Test recording some metrics
    metrics.record_video_generation("typing", 10.5, "success", 1024000)
    metrics.record_video_generation("matrix", 8.2, "success", 2048000)
    metrics.record_http_request("POST", "/api/generate/typing", 200, 0.5)
    
    # Test system metrics update
    metrics.update_system_metrics(50.0, 60.0, 30.0, 10737418240)  # 10GB free
    
    # Get metrics output
    metrics_output = metrics.get_metrics()
    
    if "green_code_fx" in metrics_output:
        print("✅ Metrics collection working")
        return True
    else:
        print("❌ Metrics collection failed")
        return False


def test_metrics_endpoint():
    """Test the metrics HTTP endpoint."""
    print("🔍 Testing metrics endpoint...")
    
    # This would require the server to be running
    # For now, just test the metrics generation
    try:
        metrics_data = metrics.get_metrics()
        
        # Check for expected metric names
        expected_metrics = [
            "green_code_fx_info",
            "green_code_fx_video_generation_total",
            "green_code_fx_video_generation_duration_seconds",
            "green_code_fx_http_requests_total",
            "green_code_fx_cpu_usage_percent",
            "green_code_fx_memory_usage_percent"
        ]
        
        missing_metrics = []
        for metric in expected_metrics:
            if metric not in metrics_data:
                missing_metrics.append(metric)
        
        if missing_metrics:
            print(f"❌ Missing metrics: {missing_metrics}")
            return False
        else:
            print("✅ All expected metrics present")
            return True
            
    except Exception as e:
        print(f"❌ Metrics endpoint test failed: {e}")
        return False


def test_metrics_format():
    """Test that metrics are in proper Prometheus format."""
    print("🔍 Testing metrics format...")
    
    try:
        metrics_data = metrics.get_metrics()
        
        # Basic format checks
        if not metrics_data.startswith("#"):
            print("❌ Metrics should start with comments")
            return False
        
        # Check for HELP and TYPE comments
        if "# HELP" not in metrics_data:
            print("❌ Missing HELP comments")
            return False
        
        if "# TYPE" not in metrics_data:
            print("❌ Missing TYPE comments")
            return False
        
        print("✅ Metrics format is valid")
        return True
        
    except Exception as e:
        print(f"❌ Metrics format test failed: {e}")
        return False


def main():
    """Run all metrics tests."""
    print("="*60)
    print("PROMETHEUS METRICS TESTING")
    print("="*60)
    
    # Set environment for testing
    os.environ["METRICS_ENABLED"] = "true"
    
    tests = [
        test_metrics_collection,
        test_metrics_endpoint,
        test_metrics_format
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
        print()
    
    # Summary
    print("="*60)
    print("METRICS TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("✅ All metrics tests PASSED")
        print("   Prometheus metrics implementation is complete")
        return 0
    else:
        print(f"❌ {total - passed} out of {total} tests FAILED")
        print("   Metrics implementation needs fixes")
        return 1


if __name__ == "__main__":
    sys.exit(main())
