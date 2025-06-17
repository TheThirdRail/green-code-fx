"""
Test suite for enhanced typing API functionality.

This module contains comprehensive unit tests for the enhanced typing effect API,
including custom font selection, color customization, text input options, and file upload.
"""

import json
import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from io import BytesIO

# Import the Flask app and dependencies
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
    """Mock the VideoGenerator class to avoid actual video generation."""
    with patch('src.web_api.VideoGenerator') as mock_gen:
        mock_instance = MagicMock()
        mock_gen.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_text_file():
    """Create a temporary text file for testing file uploads."""
    content = "def hello_world():\n    print('Hello, World!')\n    return True\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestEnhancedTypingAPI:
    """Test cases for enhanced typing API parameters."""
    
    def test_custom_font_parameter(self, client, mock_video_generator):
        """Test typing effect generation with custom font."""
        payload = {
            'duration': 30,
            'font_family': 'jetbrains',
            'font_size': 24,
            'text_color': '#FF0000',
            'output_format': 'mp4'
        }

        response = client.post('/api/generate/typing',
                             data=json.dumps(payload),
                             content_type='application/json')

        assert response.status_code == 202
        data = json.loads(response.data)
        assert 'job_id' in data
        assert data['status'] == 'queued'
        
        # Verify the video generator was called with correct parameters
        mock_video_generator.generate_typing_effect.assert_called_once()
        call_args = mock_video_generator.generate_typing_effect.call_args
        assert call_args.kwargs['font_family'] == 'jetbrains'
        assert call_args.kwargs['font_size'] == 24
        assert call_args.kwargs['text_color'] == '#FF0000'

    def test_typo_probability_parameter(self, client, mock_video_generator):
        """Test typing effect generation with custom typo probability."""
        payload = {
            'duration': 30,
            'typo_probability': 0.05,
            'output_format': 'mp4'
        }

        response = client.post('/api/generate/typing',
                             data=json.dumps(payload),
                             content_type='application/json')

        assert response.status_code == 202
        call_args = mock_video_generator.generate_typing_effect.call_args
        assert call_args.kwargs['typo_probability'] == 0.05

    def test_custom_text_parameter(self, client, mock_video_generator):
        """Test typing effect generation with custom text input."""
        custom_text = "print('Hello, World!')\nprint('Custom text test')"
        payload = {
            'duration': 20,
            'custom_text': custom_text,
            'font_family': 'jetbrains',
            'output_format': 'mp4'
        }

        response = client.post('/api/generate/typing',
                             data=json.dumps(payload),
                             content_type='application/json')

        assert response.status_code == 202
        data = json.loads(response.data)
        assert 'job_id' in data
        
        # Verify custom text was passed correctly
        call_args = mock_video_generator.generate_typing_effect.call_args
        assert call_args.kwargs['custom_text'] == custom_text

    def test_file_upload_parameter(self, client, mock_video_generator, sample_text_file):
        """Test typing effect generation with file upload."""
        with open(sample_text_file, 'rb') as f:
            file_data = f.read()
        
        data = {
            'duration': '25',
            'font_family': 'jetbrains',
            'font_size': '32',
            'text_color': '#00FF00',
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/typing',
                             data=data,
                             content_type='multipart/form-data',
                             files={'text_file': (BytesIO(file_data), 'test.txt')})

        assert response.status_code == 202
        response_data = json.loads(response.data)
        assert 'job_id' in response_data
        
        # Verify file upload was handled
        call_args = mock_video_generator.generate_typing_effect.call_args
        assert call_args.kwargs['uploaded_file_path'] is not None

    def test_color_validation(self, client):
        """Test color parameter validation."""
        # Test valid hex colors
        valid_colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFFFF', '#000000']
        for color in valid_colors:
            payload = {
                'duration': 15,
                'text_color': color,
                'output_format': 'mp4'
            }
            response = client.post('/api/generate/typing',
                                 data=json.dumps(payload),
                                 content_type='application/json')
            assert response.status_code == 202, f"Valid color {color} should be accepted"

    def test_font_size_validation(self, client):
        """Test font size parameter validation."""
        # Test valid font sizes
        valid_sizes = [12, 24, 32, 48, 72]
        for size in valid_sizes:
            payload = {
                'duration': 15,
                'font_size': size,
                'output_format': 'mp4'
            }
            response = client.post('/api/generate/typing',
                                 data=json.dumps(payload),
                                 content_type='application/json')
            assert response.status_code == 202, f"Valid font size {size} should be accepted"

    def test_duration_validation(self, client):
        """Test duration parameter validation."""
        # Test invalid durations
        invalid_durations = [5, 0, -1, 700]
        for duration in invalid_durations:
            payload = {
                'duration': duration,
                'output_format': 'mp4'
            }
            response = client.post('/api/generate/typing',
                                 data=json.dumps(payload),
                                 content_type='application/json')
            assert response.status_code == 400, f"Invalid duration {duration} should be rejected"

    def test_conflicting_text_inputs(self, client, sample_text_file):
        """Test that custom_text and file upload cannot be used together."""
        with open(sample_text_file, 'rb') as f:
            file_data = f.read()
        
        data = {
            'duration': '20',
            'custom_text': 'print("This should conflict")',
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/typing',
                             data=data,
                             content_type='multipart/form-data',
                             files={'text_file': (BytesIO(file_data), 'test.txt')})

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'error' in response_data
        assert 'both custom_text and text_file' in response_data['error'].lower()

    def test_default_parameters(self, client, mock_video_generator):
        """Test that default parameters are applied when not specified."""
        payload = {
            'duration': 30,
            'output_format': 'mp4'
        }

        response = client.post('/api/generate/typing',
                             data=json.dumps(payload),
                             content_type='application/json')

        assert response.status_code == 202
        
        # Verify default parameters were used
        call_args = mock_video_generator.generate_typing_effect.call_args
        assert call_args.kwargs['font_family'] == 'jetbrains'
        assert call_args.kwargs['font_size'] == config.TYPING_FONT_SIZE
        assert call_args.kwargs['text_color'] == '#00FF00'

    def test_multipart_form_data_handling(self, client, mock_video_generator):
        """Test handling of multipart form data without file upload."""
        data = {
            'duration': '45',
            'font_family': 'jetbrains',
            'font_size': '28',
            'text_color': '#0000FF',
            'custom_text': 'print("Form data test")',
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/typing',
                             data=data,
                             content_type='multipart/form-data')

        assert response.status_code == 202
        
        # Verify parameters were correctly parsed from form data
        call_args = mock_video_generator.generate_typing_effect.call_args
        assert call_args.kwargs['duration'] == 45
        assert call_args.kwargs['font_size'] == 28
        assert call_args.kwargs['text_color'] == '#0000FF'
        assert call_args.kwargs['custom_text'] == 'print("Form data test")'


class TestFontAPI:
    """Test cases for font listing API."""
    
    def test_fonts_endpoint(self, client):
        """Test the fonts listing endpoint."""
        response = client.get('/api/fonts')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'fonts' in data
        assert 'default' in data
        assert data['default'] == 'jetbrains'
        
        # Verify font structure
        fonts = data['fonts']
        assert isinstance(fonts, list)
        assert len(fonts) > 0
        
        # Check that jetbrains font is included
        jetbrains_font = next((f for f in fonts if f['id'] == 'jetbrains'), None)
        assert jetbrains_font is not None
        assert jetbrains_font['name'] == 'JetBrains Mono'
        assert jetbrains_font['type'] == 'bundled'


if __name__ == '__main__':
    pytest.main([__file__])
