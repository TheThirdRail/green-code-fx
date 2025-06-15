#!/usr/bin/env python3
"""
Container startup performance testing script for Green-Code FX.

This script tests Docker container startup time to ensure it meets the <30 seconds requirement.
"""

import os
import sys
import time
import subprocess
import requests
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, timeout=60):
    """Run a shell command with timeout."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout} seconds"


def wait_for_health_check(max_wait_time=60, check_interval=2):
    """Wait for the container health check to pass."""
    print(f"Waiting for health check (max {max_wait_time}s)...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get("http://localhost:8082/api/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") == "healthy":
                    elapsed = time.time() - start_time
                    print(f"✅ Health check passed after {elapsed:.2f}s")
                    return True, elapsed
        except (requests.exceptions.RequestException, json.JSONDecodeError):
            pass
        
        time.sleep(check_interval)
    
    elapsed = time.time() - start_time
    print(f"❌ Health check failed after {elapsed:.2f}s")
    return False, elapsed


def test_container_startup():
    """Test container startup performance."""
    print("=" * 60)
    print("CONTAINER STARTUP PERFORMANCE TEST")
    print("=" * 60)
    print("Target: Container ready in <30 seconds")
    print()
    
    # Clean up any existing containers
    print("🧹 Cleaning up existing containers...")
    run_command("docker-compose down -v --remove-orphans", timeout=30)
    
    # Build the container (if needed)
    print("🔨 Building container (if needed)...")
    build_start = time.time()
    success, stdout, stderr = run_command("docker-compose build --no-cache", timeout=300)
    build_time = time.time() - build_start
    
    if not success:
        print(f"❌ Container build failed after {build_time:.2f}s")
        print(f"Error: {stderr}")
        return False, build_time, 0, 0
    
    print(f"✅ Container built in {build_time:.2f}s")
    
    # Start the container and measure startup time
    print("🚀 Starting container...")
    startup_start = time.time()
    
    success, stdout, stderr = run_command("docker-compose up -d", timeout=60)
    if not success:
        startup_time = time.time() - startup_start
        print(f"❌ Container startup failed after {startup_time:.2f}s")
        print(f"Error: {stderr}")
        return False, build_time, startup_time, 0
    
    container_up_time = time.time() - startup_start
    print(f"✅ Container started in {container_up_time:.2f}s")
    
    # Wait for health check to pass
    health_passed, health_time = wait_for_health_check(max_wait_time=45)
    
    total_ready_time = startup_start + health_time - startup_start
    
    # Display results
    print()
    print("=" * 60)
    print("STARTUP PERFORMANCE RESULTS")
    print("=" * 60)
    print(f"Build Time:           {build_time:.2f}s")
    print(f"Container Up Time:    {container_up_time:.2f}s")
    print(f"Health Check Time:    {health_time:.2f}s")
    print(f"Total Ready Time:     {total_ready_time:.2f}s")
    print(f"Target:               <30.00s")
    print()
    
    if health_passed and total_ready_time < 30:
        print("🎉 PASS: Container startup meets <30s requirement")
        status = True
    else:
        print("⚠️  FAIL: Container startup exceeds 30s requirement")
        status = False
    
    # Test basic API functionality
    if health_passed:
        print()
        print("🧪 Testing basic API functionality...")
        try:
            # Test health endpoint
            response = requests.get("http://localhost:8082/api/health", timeout=10)
            health_data = response.json()
            print(f"✅ Health endpoint: {health_data.get('status', 'unknown')}")
            
            # Test job status endpoint (should return empty list)
            response = requests.get("http://localhost:8082/api/jobs", timeout=10)
            if response.status_code == 200:
                print("✅ Jobs endpoint: accessible")
            else:
                print(f"⚠️  Jobs endpoint: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ API test failed: {e}")
            status = False
    
    return status, build_time, container_up_time, total_ready_time


def analyze_startup_bottlenecks():
    """Analyze container startup bottlenecks."""
    print()
    print("=" * 60)
    print("STARTUP BOTTLENECK ANALYSIS")
    print("=" * 60)
    
    # Check container logs for startup timing
    print("📋 Analyzing container logs...")
    success, logs, stderr = run_command("docker-compose logs video-fx-generator", timeout=30)
    
    if success and logs:
        lines = logs.split('\n')
        startup_events = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in [
                'starting', 'initialized', 'ready', 'listening', 'server', 'health'
            ]):
                startup_events.append(line.strip())
        
        if startup_events:
            print("Key startup events:")
            for event in startup_events[-10:]:  # Last 10 events
                print(f"  {event}")
        else:
            print("No specific startup events found in logs")
    else:
        print("Could not retrieve container logs")
    
    # Check image size
    print()
    print("📦 Analyzing image size...")
    success, output, stderr = run_command("docker images green-code-fx-generator", timeout=10)
    if success:
        print("Image information:")
        for line in output.split('\n')[:2]:  # Header + image info
            print(f"  {line}")
    
    # Optimization recommendations
    print()
    print("🔧 OPTIMIZATION RECOMMENDATIONS:")
    print("  1. Use multi-stage builds to reduce image size")
    print("  2. Optimize Python package installation order")
    print("  3. Pre-compile Python bytecode")
    print("  4. Use .dockerignore to exclude unnecessary files")
    print("  5. Consider using Alpine Linux base image")
    print("  6. Cache frequently used dependencies")


def cleanup():
    """Clean up test containers."""
    print()
    print("🧹 Cleaning up test containers...")
    run_command("docker-compose down -v --remove-orphans", timeout=30)


def main():
    """Main container startup testing workflow."""
    try:
        # Run startup performance test
        success, build_time, startup_time, ready_time = test_container_startup()
        
        # Analyze bottlenecks
        analyze_startup_bottlenecks()
        
        # Generate summary report
        print()
        print("=" * 60)
        print("FINAL SUMMARY")
        print("=" * 60)
        
        if success:
            print("✅ Container startup performance: PASS")
            print(f"   Ready time: {ready_time:.2f}s (target: <30s)")
            return 0
        else:
            print("❌ Container startup performance: FAIL")
            print(f"   Ready time: {ready_time:.2f}s (target: <30s)")
            print("   Review optimization recommendations above")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Container startup test interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Container startup test failed: {e}")
        return 1
    finally:
        cleanup()


if __name__ == "__main__":
    sys.exit(main())
