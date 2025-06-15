"""
Integration tests for Green-Code FX video effects generator.

These tests verify end-to-end functionality including API endpoints,
video generation workflows, and system integration.
"""

import os
import sys
import time
import json
import requests
import pytest
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import config


class TestAPIIntegration:
    """Integration tests for the Flask API."""
    
    @pytest.fixture(scope="class")
    def api_base_url(self):
        """Base URL for API testing."""
        return f"http://localhost:{config.API_PORT}"
    
    @pytest.fixture(scope="class")
    def setup_environment(self):
        """Setup test environment."""
        # Ensure output directories exist
        config.ensure_directories()
        yield
        # Cleanup after tests
        self._cleanup_test_files()
    
    def _cleanup_test_files(self):
        """Clean up test-generated files."""
        output_dir = config.OUTPUT_DIR
        for pattern in ["test_*", "integration_*"]:
            for file_path in output_dir.glob(pattern):
                try:
                    file_path.unlink()
                except Exception:
                    pass
    
    def test_health_endpoint(self, api_base_url, setup_environment):
        """Test health check endpoint."""
        response = requests.get(f"{api_base_url}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "active_jobs" in data
        assert "queue_length" in data
        assert "timestamp" in data
    
    def test_rate_limit_endpoint(self, api_base_url, setup_environment):
        """Test rate limit status endpoint."""
        response = requests.get(f"{api_base_url}/api/rate-limit")
        assert response.status_code == 200
        
        data = response.json()
        assert "client_ip" in data
        assert "is_allowed" in data
        assert "rate_limit" in data
        assert "global_stats" in data
    
    def test_resource_status_endpoint(self, api_base_url, setup_environment):
        """Test resource status endpoint."""
        response = requests.get(f"{api_base_url}/api/resources")
        assert response.status_code == 200
        
        data = response.json()
        assert "resource_status" in data
        assert "metrics" in data
        assert "queue" in data
        
        # Verify metrics structure
        metrics = data["metrics"]
        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "disk_percent" in metrics
    
    def test_typing_effect_generation_workflow(self, api_base_url, setup_environment):
        """Test complete typing effect generation workflow."""
        # 1. Submit job
        job_data = {
            "duration": 10,  # Short duration for testing
            "source_file": "snake_code.txt",
            "output_format": "mp4"
        }
        
        response = requests.post(f"{api_base_url}/api/generate/typing", json=job_data)
        assert response.status_code == 202
        
        submit_data = response.json()
        assert "job_id" in submit_data
        assert submit_data["status"] == "queued"
        
        job_id = submit_data["job_id"]
        
        # 2. Monitor job progress
        max_wait_time = 120  # 2 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            response = requests.get(f"{api_base_url}/api/jobs/{job_id}")
            assert response.status_code == 200
            
            job_status = response.json()
            status = job_status.get("status")
            
            if status == "completed":
                # 3. Verify completion
                assert "output_file" in job_status
                assert "download_url" in job_status
                assert job_status["progress"] == 100
                break
            elif status == "failed":
                pytest.fail(f"Job failed: {job_status.get('error', 'Unknown error')}")
            
            time.sleep(2)
        else:
            pytest.fail(f"Job did not complete within {max_wait_time} seconds")
        
        # 4. Test file download
        download_url = job_status["download_url"]
        response = requests.get(f"{api_base_url}{download_url}")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "video/mp4"
        
        # Verify file size is reasonable (should be > 1MB for 10s video)
        content_length = int(response.headers.get("content-length", 0))
        assert content_length > 1024 * 1024  # > 1MB
    
    def test_matrix_effect_generation_workflow(self, api_base_url, setup_environment):
        """Test complete Matrix effect generation workflow."""
        # 1. Submit job
        job_data = {
            "duration": 5,  # Short duration for testing
            "loop_seamless": True,
            "output_format": "mp4"
        }
        
        response = requests.post(f"{api_base_url}/api/generate/matrix", json=job_data)
        assert response.status_code == 202
        
        submit_data = response.json()
        assert "job_id" in submit_data
        assert submit_data["status"] == "queued"
        
        job_id = submit_data["job_id"]
        
        # 2. Monitor job progress
        max_wait_time = 180  # 3 minutes max (Matrix is slower)
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            response = requests.get(f"{api_base_url}/api/jobs/{job_id}")
            assert response.status_code == 200
            
            job_status = response.json()
            status = job_status.get("status")
            
            if status == "completed":
                # 3. Verify completion
                assert "output_file" in job_status
                assert "download_url" in job_status
                assert job_status["progress"] == 100
                break
            elif status == "failed":
                pytest.fail(f"Job failed: {job_status.get('error', 'Unknown error')}")
            
            time.sleep(3)
        else:
            pytest.fail(f"Job did not complete within {max_wait_time} seconds")
        
        # 4. Test file download
        download_url = job_status["download_url"]
        response = requests.get(f"{api_base_url}{download_url}")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "video/mp4"
        
        # Verify file size is reasonable
        content_length = int(response.headers.get("content-length", 0))
        assert content_length > 512 * 1024  # > 512KB
    
    def test_concurrent_job_handling(self, api_base_url, setup_environment):
        """Test handling of concurrent jobs."""
        job_ids = []
        
        # Submit multiple jobs
        for i in range(3):
            job_data = {
                "duration": 8,
                "source_file": "snake_code.txt",
                "output_format": "mp4"
            }
            
            response = requests.post(f"{api_base_url}/api/generate/typing", json=job_data)
            assert response.status_code == 202
            
            submit_data = response.json()
            job_ids.append(submit_data["job_id"])
        
        # Monitor all jobs
        max_wait_time = 300  # 5 minutes for multiple jobs
        start_time = time.time()
        completed_jobs = set()
        
        while time.time() - start_time < max_wait_time and len(completed_jobs) < len(job_ids):
            for job_id in job_ids:
                if job_id in completed_jobs:
                    continue
                
                response = requests.get(f"{api_base_url}/api/jobs/{job_id}")
                assert response.status_code == 200
                
                job_status = response.json()
                status = job_status.get("status")
                
                if status == "completed":
                    completed_jobs.add(job_id)
                elif status == "failed":
                    pytest.fail(f"Job {job_id} failed: {job_status.get('error', 'Unknown error')}")
            
            time.sleep(3)
        
        assert len(completed_jobs) == len(job_ids), f"Only {len(completed_jobs)}/{len(job_ids)} jobs completed"
    
    def test_invalid_job_parameters(self, api_base_url, setup_environment):
        """Test API validation with invalid parameters."""
        # Test invalid duration for typing effect
        response = requests.post(f"{api_base_url}/api/generate/typing", json={
            "duration": 5,  # Too short (min 10)
            "output_format": "mp4"
        })
        assert response.status_code == 400
        
        # Test invalid output format
        response = requests.post(f"{api_base_url}/api/generate/typing", json={
            "duration": 30,
            "output_format": "avi"  # Not supported
        })
        assert response.status_code == 400
        
        # Test invalid duration for Matrix effect
        response = requests.post(f"{api_base_url}/api/generate/matrix", json={
            "duration": 150,  # Too long (max 120)
            "output_format": "mp4"
        })
        assert response.status_code == 400
    
    def test_nonexistent_job_status(self, api_base_url, setup_environment):
        """Test querying status of nonexistent job."""
        response = requests.get(f"{api_base_url}/api/jobs/nonexistent_job_id")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
    
    def test_nonexistent_file_download(self, api_base_url, setup_environment):
        """Test downloading nonexistent file."""
        response = requests.get(f"{api_base_url}/api/download/nonexistent_file.mp4")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
    
    def test_rate_limiting_enforcement(self, api_base_url, setup_environment):
        """Test that rate limiting is enforced."""
        # Make requests rapidly to trigger rate limiting
        responses = []
        for i in range(15):  # More than the 10/minute limit
            response = requests.post(f"{api_base_url}/api/generate/typing", json={
                "duration": 10,
                "output_format": "mp4"
            })
            responses.append(response)
        
        # Should have some 429 responses
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0, "Rate limiting was not enforced"
        
        # Check rate limit headers
        for response in rate_limited_responses:
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "Retry-After" in response.headers


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"])
