"""
Test suite for Green-Code FX web API.

This module contains unit and integration tests for the Flask web API,
ensuring proper functionality of all endpoints and error handling.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os
from pathlib import Path

# Import the Flask app
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.web_api import create_app, active_jobs, job_lock
from src.config import config


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mock_video_generator():
    """Mock the VideoGenerator class."""
    with patch('src.web_api.VideoGenerator') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


class TestHealthEndpoint:
    """Test cases for the health check endpoint."""
    
    def test_health_check_success(self, client):
        """Test successful health check."""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'healthy'
        assert data['version'] == config.APP_VERSION
        assert 'active_jobs' in data
        assert 'queue_length' in data
        assert 'disk_space' in data
        assert 'timestamp' in data
    
    def test_health_check_with_active_jobs(self, client):
        """Test health check with active jobs."""
        # Add a mock job
        with job_lock:
            active_jobs['test_job'] = {'status': 'running'}
        
        response = client.get('/api/health')
        data = json.loads(response.data)
        
        assert data['active_jobs'] >= 1
        
        # Clean up
        with job_lock:
            active_jobs.clear()


class TestTypingEffectEndpoint:
    """Test cases for the typing effect generation endpoint."""
    
    def test_generate_typing_effect_success(self, client, mock_video_generator):
        """Test successful typing effect generation request."""
        payload = {
            'duration': 90,
            'source_file': 'snake_code.txt',
            'output_format': 'mp4'
        }

        response = client.post('/api/generate/typing',
                             data=json.dumps(payload),
                             content_type='application/json')

        assert response.status_code == 202
        data = json.loads(response.data)

        assert 'job_id' in data
        assert data['status'] == 'queued'
        assert 'estimated_duration' in data
        assert data['job_id'].startswith('typing_')

    def test_generate_typing_effect_with_customization(self, client, mock_video_generator):
        """Test typing effect generation with custom parameters."""
        payload = {
            'duration': 60,
            'font_family': 'jetbrains',
            'font_size': 24,
            'text_color': '#FF0000',
            'custom_text': 'print("Hello, World!")\nprint("Custom text test")',
            'output_format': 'mp4'
        }

        response = client.post('/api/generate/typing',
                             data=json.dumps(payload),
                             content_type='application/json')

        assert response.status_code == 202
        data = json.loads(response.data)

        assert 'job_id' in data
        assert data['status'] == 'queued'
        assert data['job_id'].startswith('typing_')

    def test_generate_typing_effect_invalid_font_size(self, client):
        """Test typing effect generation with invalid font size."""
        payload = {
            'duration': 60,
            'font_size': 100,  # Too large
            'output_format': 'mp4'
        }

        response = client.post('/api/generate/typing',
                             data=json.dumps(payload),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Font size must be between' in data['error']

    def test_generate_typing_effect_invalid_color(self, client):
        """Test typing effect generation with invalid color format."""
        payload = {
            'duration': 60,
            'text_color': 'invalid-color',
            'output_format': 'mp4'
        }

        response = client.post('/api/generate/typing',
                             data=json.dumps(payload),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid color format' in data['error']

    def test_generate_typing_effect_invalid_font_family(self, client):
        """Test typing effect generation with invalid font family."""
        payload = {
            'duration': 60,
            'font_family': 'nonexistent-font',
            'output_format': 'mp4'
        }

        response = client.post('/api/generate/typing',
                             data=json.dumps(payload),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid font family' in data['error']


class TestFontDiscoveryEndpoint:
    """Test cases for the font discovery endpoint."""

    def test_list_available_fonts(self, client):
        """Test listing available fonts."""
        response = client.get('/api/fonts')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'fonts' in data
        assert 'default' in data
        assert data['default'] == 'jetbrains'
        assert isinstance(data['fonts'], dict)

        # Should have at least jetbrains font
        assert 'jetbrains' in data['fonts']
        assert 'name' in data['fonts']['jetbrains']
        assert 'type' in data['fonts']['jetbrains']
    
    def test_generate_typing_effect_invalid_duration(self, client):
        """Test typing effect with invalid duration."""
        payload = {
            'duration': 5,  # Too short
            'source_file': 'snake_code.txt',
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/typing',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_generate_typing_effect_invalid_format(self, client):
        """Test typing effect with invalid output format."""
        payload = {
            'duration': 90,
            'source_file': 'snake_code.txt',
            'output_format': 'avi'  # Not supported
        }
        
        response = client.post('/api/generate/typing',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_generate_typing_effect_no_payload(self, client):
        """Test typing effect with no JSON payload."""
        response = client.post('/api/generate/typing')
        
        # Should use defaults and succeed
        assert response.status_code == 202


class TestMatrixEffectEndpoint:
    """Test cases for the Matrix rain effect generation endpoint."""
    
    def test_generate_matrix_effect_success(self, client, mock_video_generator):
        """Test successful Matrix effect generation request."""
        payload = {
            'duration': 15,
            'loop_seamless': True,
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/matrix',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 202
        data = json.loads(response.data)
        
        assert 'job_id' in data
        assert data['status'] == 'queued'
        assert 'estimated_duration' in data
        assert data['job_id'].startswith('matrix_')
    
    def test_generate_matrix_effect_invalid_duration(self, client):
        """Test Matrix effect with invalid duration."""
        payload = {
            'duration': 2,  # Too short
            'loop_seamless': True,
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/matrix',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestJobStatusEndpoint:
    """Test cases for job status endpoint."""
    
    def test_get_job_status_success(self, client):
        """Test successful job status retrieval."""
        # Add a mock job
        job_id = 'test_job_123'
        with job_lock:
            active_jobs[job_id] = {
                'job_id': job_id,
                'status': 'running',
                'progress': 50,
                'effect_type': 'typing'
            }
        
        response = client.get(f'/api/jobs/{job_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['job_id'] == job_id
        assert data['status'] == 'running'
        assert data['progress'] == 50
        
        # Clean up
        with job_lock:
            active_jobs.clear()
    
    def test_get_job_status_not_found(self, client):
        """Test job status for non-existent job."""
        response = client.get('/api/jobs/nonexistent_job')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_job_status_completed_with_file(self, client):
        """Test job status for completed job with output file."""
        job_id = 'completed_job_123'
        with job_lock:
            active_jobs[job_id] = {
                'job_id': job_id,
                'status': 'completed',
                'progress': 100,
                'effect_type': 'typing',
                'output_file': '/app/output/test_video.mp4'
            }
        
        response = client.get(f'/api/jobs/{job_id}')
        data = json.loads(response.data)
        
        assert 'download_url' in data
        assert data['download_url'] == '/api/download/test_video.mp4'
        
        # Clean up
        with job_lock:
            active_jobs.clear()


class TestDownloadEndpoint:
    """Test cases for file download endpoint."""
    
    def test_download_file_not_found(self, client):
        """Test download of non-existent file."""
        response = client.get('/api/download/nonexistent.mp4')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('src.web_api.send_file')
    def test_download_file_success(self, mock_send_file, client):
        """Test successful file download."""
        # Create a temporary file in the output directory
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b'fake video content')
            tmp_path = Path(tmp.name)
        
        # Mock the output directory to point to our temp file's directory
        with patch.object(config, 'OUTPUT_DIR', tmp_path.parent):
            mock_send_file.return_value = 'mocked response'
            
            response = client.get(f'/api/download/{tmp_path.name}')
            
            # Should call send_file
            mock_send_file.assert_called_once()
        
        # Clean up
        os.unlink(tmp_path)


class TestErrorHandling:
    """Test cases for error handling and edge cases."""
    
    def test_invalid_json_payload(self, client):
        """Test handling of invalid JSON payload."""
        response = client.post('/api/generate/typing',
                             data='invalid json',
                             content_type='application/json')
        
        # Should handle gracefully and use defaults
        assert response.status_code in [202, 400]
    
    def test_missing_content_type(self, client):
        """Test handling of missing content type."""
        response = client.post('/api/generate/typing',
                             data='{"duration": 90}')
        
        # Should handle gracefully
        assert response.status_code in [202, 400]


if __name__ == '__main__':
    pytest.main([__file__])
