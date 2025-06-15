#!/usr/bin/env python3
"""
Phase 6 Testing and Quality Assurance Test Runner

This script runs all Phase 6 tests for the Green-Code FX UI Enhancement project,
including unit tests, integration tests, browser tests, and performance tests.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_command(command, description, timeout=300):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=project_root
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ SUCCESS ({duration:.2f}s)")
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
        else:
            print(f"❌ FAILED ({duration:.2f}s)")
            print("STDOUT:")
            print(result.stdout)
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT after {timeout}s")
        return False
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    
    required_packages = [
        'pytest',
        'pytest-cov',
        'pytest-html',
        'pytest-mock',
        'selenium',
        'flask',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    return True

def run_unit_tests():
    """Run unit tests for enhanced typing API."""
    commands = [
        ("python -m pytest tests/test_enhanced_typing_api.py -v --tb=short", 
         "Enhanced Typing API Unit Tests"),
        ("python -m pytest tests/test_color_validation.py -v --tb=short", 
         "Color Validation Tests"),
    ]
    
    results = []
    for command, description in commands:
        success = run_command(command, description)
        results.append((description, success))
    
    return results

def run_integration_tests():
    """Run integration tests for file upload functionality."""
    commands = [
        ("python -m pytest tests/test_file_upload_integration.py -v --tb=short", 
         "File Upload Integration Tests"),
        ("python -m pytest tests/test_security_validation.py -v --tb=short", 
         "Security Validation Tests"),
    ]
    
    results = []
    for command, description in commands:
        success = run_command(command, description)
        results.append((description, success))
    
    return results

def run_performance_tests():
    """Run performance tests for large file handling."""
    commands = [
        ("python -m pytest tests/test_large_file_performance.py -v --tb=short -x", 
         "Large File Performance Tests"),
    ]
    
    results = []
    for command, description in commands:
        success = run_command(command, description, timeout=600)  # Longer timeout for performance tests
        results.append((description, success))
    
    return results

def run_browser_tests():
    """Run browser tests for frontend UI."""
    print("\n⚠️  Browser tests require Chrome/Firefox and may be skipped if browsers are not available")
    
    commands = [
        ("python -m pytest tests/test_frontend_browsers.py -v --tb=short -x", 
         "Frontend Browser Tests"),
        ("python -m pytest tests/test_responsive_design.py -v --tb=short -x", 
         "Responsive Design Tests"),
    ]
    
    results = []
    for command, description in commands:
        success = run_command(command, description, timeout=600)  # Longer timeout for browser tests
        results.append((description, success))
    
    return results

def run_existing_tests():
    """Run existing test suite to ensure no regressions."""
    commands = [
        ("python -m pytest tests/test_api.py -v --tb=short", 
         "Existing API Tests"),
        ("python -m pytest tests/test_integration.py -v --tb=short -x", 
         "Existing Integration Tests"),
    ]
    
    results = []
    for command, description in commands:
        success = run_command(command, description)
        results.append((description, success))
    
    return results

def generate_test_report(all_results):
    """Generate a summary test report."""
    print(f"\n{'='*80}")
    print("PHASE 6 TESTING SUMMARY REPORT")
    print(f"{'='*80}")
    
    total_tests = 0
    passed_tests = 0
    
    for category, results in all_results.items():
        print(f"\n{category}:")
        print("-" * len(category))
        
        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} {test_name}")
            total_tests += 1
            if success:
                passed_tests += 1
    
    print(f"\n{'='*80}")
    print(f"OVERALL RESULTS: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        failed_tests = total_tests - passed_tests
        print(f"⚠️  {failed_tests} tests failed")
        return False

def main():
    """Main test runner function."""
    print("🚀 Starting Phase 6 Testing and Quality Assurance")
    print(f"Project root: {project_root}")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        return 1
    
    # Run all test categories
    all_results = {}
    
    print("\n📋 Running Unit Tests...")
    all_results["Unit Tests"] = run_unit_tests()
    
    print("\n🔗 Running Integration Tests...")
    all_results["Integration Tests"] = run_integration_tests()
    
    print("\n⚡ Running Performance Tests...")
    all_results["Performance Tests"] = run_performance_tests()
    
    print("\n🌐 Running Browser Tests...")
    all_results["Browser Tests"] = run_browser_tests()
    
    print("\n🔄 Running Existing Tests (Regression Check)...")
    all_results["Regression Tests"] = run_existing_tests()
    
    # Generate summary report
    success = generate_test_report(all_results)
    
    if success:
        print("\n✅ Phase 6 Testing completed successfully!")
        return 0
    else:
        print("\n❌ Phase 6 Testing completed with failures.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
