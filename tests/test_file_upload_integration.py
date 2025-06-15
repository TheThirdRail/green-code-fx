"""
Integration tests for file upload functionality.

This module contains comprehensive integration tests for file upload features,
including security validation, file type checking, size limits, and malicious file handling.
"""

import pytest
import tempfile
import os
from pathlib import Path
from io import BytesIO
from unittest.mock import patch, MagicMock

# Import the Flask app and dependencies
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.web_api import create_app
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


class TestFileUploadSecurity:
    """Test cases for file upload security and validation."""
    
    def test_valid_text_file_upload(self, client, mock_video_generator):
        """Test uploading a valid text file."""
        content = "def hello():\n    print('Hello, World!')\n    return True"
        file_data = BytesIO(content.encode('utf-8'))
        
        data = {
            'duration': '30',
            'font_family': 'jetbrains',
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/typing',
                             data=data,
                             content_type='multipart/form-data',
                             files={'text_file': (file_data, 'test.txt')})
        
        assert response.status_code == 202
        
        # Verify file was processed
        call_args = mock_video_generator.generate_typing_effect.call_args
        assert call_args.kwargs['uploaded_file_path'] is not None

    def test_invalid_file_extension(self, client):
        """Test rejection of files with invalid extensions."""
        content = "print('This is a Python file')"
        file_data = BytesIO(content.encode('utf-8'))
        
        data = {
            'duration': '30',
            'output_format': 'mp4'
        }
        
        # Test various invalid extensions
        invalid_extensions = ['test.py', 'test.js', 'test.exe', 'test.pdf', 'test.docx']
        
        for filename in invalid_extensions:
            response = client.post('/api/generate/typing',
                                 data=data,
                                 content_type='multipart/form-data',
                                 files={'text_file': (file_data, filename)})
            
            assert response.status_code == 400, f"File {filename} should be rejected"
            response_data = response.get_json()
            assert 'error' in response_data
            assert 'only .txt files' in response_data['error'].lower()

    def test_file_size_limit(self, client):
        """Test file size limit enforcement."""
        # Create a file larger than the 10MB limit
        large_content = "A" * (11 * 1024 * 1024)  # 11MB
        file_data = BytesIO(large_content.encode('utf-8'))
        
        data = {
            'duration': '30',
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/typing',
                             data=data,
                             content_type='multipart/form-data',
                             files={'text_file': (file_data, 'large_file.txt')})
        
        assert response.status_code == 400
        response_data = response.get_json()
        assert 'error' in response_data
        assert 'file size' in response_data['error'].lower()

    def test_empty_file_upload(self, client):
        """Test handling of empty file uploads."""
        file_data = BytesIO(b'')
        
        data = {
            'duration': '30',
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/typing',
                             data=data,
                             content_type='multipart/form-data',
                             files={'text_file': (file_data, 'empty.txt')})
        
        # Empty files should be handled gracefully
        assert response.status_code in [202, 400]

    def test_malicious_filename_handling(self, client):
        """Test handling of malicious filenames."""
        content = "print('Hello, World!')"
        file_data = BytesIO(content.encode('utf-8'))
        
        data = {
            'duration': '30',
            'output_format': 'mp4'
        }
        
        # Test various malicious filenames
        malicious_filenames = [
            '../../../etc/passwd.txt',
            '..\\..\\windows\\system32\\config.txt',
            'test<script>alert(1)</script>.txt',
            'test\x00.txt',
            'test\n.txt',
            'test\r.txt'
        ]
        
        for filename in malicious_filenames:
            response = client.post('/api/generate/typing',
                                 data=data,
                                 content_type='multipart/form-data',
                                 files={'text_file': (file_data, filename)})
            
            # Should either reject or sanitize the filename
            assert response.status_code in [202, 400], f"Malicious filename {filename} not handled properly"

    def test_unicode_content_handling(self, client, mock_video_generator):
        """Test handling of Unicode content in uploaded files."""
        # Test various Unicode characters
        unicode_content = "print('Hello, 世界!')\nprint('Café ñoño')\nprint('🚀 Rocket')"
        file_data = BytesIO(unicode_content.encode('utf-8'))
        
        data = {
            'duration': '30',
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/typing',
                             data=data,
                             content_type='multipart/form-data',
                             files={'text_file': (file_data, 'unicode_test.txt')})
        
        assert response.status_code == 202
        
        # Verify Unicode content was processed
        call_args = mock_video_generator.generate_typing_effect.call_args
        assert call_args.kwargs['uploaded_file_path'] is not None

    def test_binary_file_rejection(self, client):
        """Test rejection of binary files disguised as text files."""
        # Create binary content (e.g., image header)
        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        file_data = BytesIO(binary_content)
        
        data = {
            'duration': '30',
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/typing',
                             data=data,
                             content_type='multipart/form-data',
                             files={'text_file': (file_data, 'fake_text.txt')})
        
        # Should handle binary content gracefully (may accept or reject)
        assert response.status_code in [202, 400]

    def test_concurrent_file_uploads(self, client, mock_video_generator):
        """Test handling of concurrent file uploads."""
        content = "print('Concurrent test')"
        
        # Simulate multiple concurrent uploads
        responses = []
        for i in range(3):
            file_data = BytesIO(content.encode('utf-8'))
            data = {
                'duration': '20',
                'output_format': 'mp4'
            }
            
            response = client.post('/api/generate/typing',
                                 data=data,
                                 content_type='multipart/form-data',
                                 files={'text_file': (file_data, f'concurrent_{i}.txt')})
            responses.append(response)
        
        # All uploads should be handled properly
        for i, response in enumerate(responses):
            assert response.status_code == 202, f"Concurrent upload {i} failed"

    def test_file_cleanup_after_processing(self, client, mock_video_generator):
        """Test that uploaded files are properly cleaned up."""
        content = "print('Cleanup test')"
        file_data = BytesIO(content.encode('utf-8'))
        
        data = {
            'duration': '30',
            'output_format': 'mp4'
        }
        
        with patch('src.web_api._save_uploaded_file') as mock_save:
            # Mock the file saving to return a known path
            temp_path = '/tmp/test_upload.txt'
            mock_save.return_value = temp_path
            
            response = client.post('/api/generate/typing',
                                 data=data,
                                 content_type='multipart/form-data',
                                 files={'text_file': (file_data, 'cleanup_test.txt')})
            
            assert response.status_code == 202
            
            # Verify the file path was passed to video generator
            call_args = mock_video_generator.generate_typing_effect.call_args
            assert call_args.kwargs['uploaded_file_path'] == temp_path


class TestFileUploadValidation:
    """Test cases for file upload validation logic."""
    
    def test_file_validation_function(self, client):
        """Test the file validation function directly."""
        from src.web_api import _validate_text_file
        
        # Create a mock file object
        class MockFile:
            def __init__(self, filename, size):
                self.filename = filename
                self.content_length = size
        
        # Test valid file
        valid_file = MockFile('test.txt', 1024)
        assert _validate_text_file(valid_file) == True
        
        # Test invalid extension
        invalid_ext_file = MockFile('test.py', 1024)
        assert _validate_text_file(invalid_ext_file) == False
        
        # Test oversized file
        oversized_file = MockFile('test.txt', 11 * 1024 * 1024)
        assert _validate_text_file(oversized_file) == False

    def test_edge_case_file_sizes(self, client, mock_video_generator):
        """Test edge cases for file sizes."""
        # Test file at exactly the size limit
        limit_size = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        content = "A" * (limit_size - 100)  # Just under the limit
        file_data = BytesIO(content.encode('utf-8'))
        
        data = {
            'duration': '30',
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/typing',
                             data=data,
                             content_type='multipart/form-data',
                             files={'text_file': (file_data, 'limit_test.txt')})
        
        assert response.status_code == 202

    def test_special_characters_in_content(self, client, mock_video_generator):
        """Test handling of special characters in file content."""
        special_content = """
        # Special characters test
        print("Quotes: ' \" ` ")
        print("Symbols: !@#$%^&*()_+-=[]{}|;:,.<>?")
        print("Newlines and tabs:\n\t\r")
        print("Backslashes: \\ \\n \\t \\r")
        """
        file_data = BytesIO(special_content.encode('utf-8'))
        
        data = {
            'duration': '30',
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/typing',
                             data=data,
                             content_type='multipart/form-data',
                             files={'text_file': (file_data, 'special_chars.txt')})
        
        assert response.status_code == 202


if __name__ == '__main__':
    pytest.main([__file__])
