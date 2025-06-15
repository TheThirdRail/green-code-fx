"""
Performance testing for large text file handling.

This module contains performance tests for handling large text files,
measuring processing times, memory usage, and system resource consumption.
"""

import pytest
import time
import tempfile
import os
import psutil
import threading
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


@pytest.fixture
def performance_monitor():
    """Monitor system performance during tests."""
    class PerformanceMonitor:
        def __init__(self):
            self.process = psutil.Process()
            self.start_memory = None
            self.start_cpu = None
            self.start_time = None
        
        def start(self):
            self.start_memory = self.process.memory_info().rss
            self.start_cpu = self.process.cpu_percent()
            self.start_time = time.time()
        
        def stop(self):
            end_time = time.time()
            end_memory = self.process.memory_info().rss
            end_cpu = self.process.cpu_percent()
            
            return {
                'duration': end_time - self.start_time,
                'memory_delta': end_memory - self.start_memory,
                'cpu_usage': end_cpu,
                'peak_memory': end_memory
            }
    
    return PerformanceMonitor()


class TestLargeFilePerformance:
    """Test cases for large file performance."""
    
    def test_large_text_file_upload(self, client, mock_video_generator, performance_monitor):
        """Test uploading and processing large text files."""
        # Create a large text file (5MB)
        large_content = self._generate_large_code_content(5 * 1024 * 1024)
        file_data = BytesIO(large_content.encode('utf-8'))
        
        data = {
            'duration': '30',
            'font_family': 'jetbrains',
            'output_format': 'mp4'
        }
        
        performance_monitor.start()
        
        response = client.post('/api/generate/typing',
                             data=data,
                             content_type='multipart/form-data',
                             files={'text_file': (file_data, 'large_file.txt')})
        
        perf_stats = performance_monitor.stop()
        
        assert response.status_code == 202
        
        # Performance assertions
        assert perf_stats['duration'] < 10.0, f"Upload took too long: {perf_stats['duration']:.2f}s"
        assert perf_stats['memory_delta'] < 50 * 1024 * 1024, f"Memory usage too high: {perf_stats['memory_delta']} bytes"
        
        # Verify file was processed
        call_args = mock_video_generator.generate_typing_effect.call_args
        assert call_args.kwargs['uploaded_file_path'] is not None

    def test_maximum_size_file(self, client, mock_video_generator, performance_monitor):
        """Test handling file at maximum allowed size."""
        # Create file at maximum size (10MB)
        max_size = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        large_content = self._generate_large_code_content(max_size - 1000)  # Just under limit
        file_data = BytesIO(large_content.encode('utf-8'))
        
        data = {
            'duration': '30',
            'output_format': 'mp4'
        }
        
        performance_monitor.start()
        
        response = client.post('/api/generate/typing',
                             data=data,
                             content_type='multipart/form-data',
                             files={'text_file': (file_data, 'max_size.txt')})
        
        perf_stats = performance_monitor.stop()
        
        assert response.status_code == 202
        
        # Performance should still be reasonable
        assert perf_stats['duration'] < 15.0, f"Max size upload took too long: {perf_stats['duration']:.2f}s"

    def test_large_custom_text_input(self, client, mock_video_generator, performance_monitor):
        """Test performance with large custom text input."""
        # Create large custom text (1MB)
        large_text = self._generate_large_code_content(1024 * 1024)
        
        data = {
            'duration': 30,
            'custom_text': large_text,
            'font_family': 'jetbrains',
            'output_format': 'mp4'
        }
        
        performance_monitor.start()
        
        response = client.post('/api/generate/typing',
                             data=large_text.encode('utf-8'),  # Simulate large payload
                             content_type='application/json')
        
        perf_stats = performance_monitor.stop()
        
        # Should handle large JSON payload
        assert response.status_code in [202, 400]  # May reject if too large
        
        if response.status_code == 202:
            assert perf_stats['duration'] < 5.0, f"Large text processing took too long: {perf_stats['duration']:.2f}s"

    def test_concurrent_large_file_uploads(self, client, mock_video_generator):
        """Test concurrent uploads of large files."""
        def upload_large_file(file_size_mb, results):
            content = self._generate_large_code_content(file_size_mb * 1024 * 1024)
            file_data = BytesIO(content.encode('utf-8'))
            
            data = {
                'duration': '20',
                'output_format': 'mp4'
            }
            
            start_time = time.time()
            response = client.post('/api/generate/typing',
                                 data=data,
                                 content_type='multipart/form-data',
                                 files={'text_file': (file_data, f'concurrent_{file_size_mb}mb.txt')})
            end_time = time.time()
            
            results.append({
                'status_code': response.status_code,
                'duration': end_time - start_time,
                'file_size_mb': file_size_mb
            })
        
        # Test concurrent uploads
        results = []
        threads = []
        
        for size_mb in [1, 2, 3]:  # 1MB, 2MB, 3MB files
            thread = threading.Thread(target=upload_large_file, args=(size_mb, results))
            threads.append(thread)
        
        # Start all uploads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Verify results
        assert len(results) == 3
        for result in results:
            assert result['status_code'] == 202
            assert result['duration'] < 10.0, f"Upload of {result['file_size_mb']}MB took too long"
        
        # Total time should be reasonable for concurrent processing
        assert total_time < 15.0, f"Concurrent uploads took too long: {total_time:.2f}s"

    def test_memory_usage_with_large_files(self, client, mock_video_generator):
        """Test memory usage patterns with large files."""
        import gc
        
        # Get baseline memory
        gc.collect()
        process = psutil.Process()
        baseline_memory = process.memory_info().rss
        
        # Upload progressively larger files
        file_sizes = [1, 2, 5]  # MB
        memory_usage = []
        
        for size_mb in file_sizes:
            content = self._generate_large_code_content(size_mb * 1024 * 1024)
            file_data = BytesIO(content.encode('utf-8'))
            
            data = {
                'duration': '20',
                'output_format': 'mp4'
            }
            
            response = client.post('/api/generate/typing',
                                 data=data,
                                 content_type='multipart/form-data',
                                 files={'text_file': (file_data, f'memory_test_{size_mb}mb.txt')})
            
            current_memory = process.memory_info().rss
            memory_delta = current_memory - baseline_memory
            memory_usage.append(memory_delta)
            
            assert response.status_code == 202
            
            # Force garbage collection
            gc.collect()
        
        # Memory usage should not grow excessively
        max_memory_delta = max(memory_usage)
        assert max_memory_delta < 100 * 1024 * 1024, f"Memory usage too high: {max_memory_delta} bytes"

    def test_file_processing_speed(self, client, mock_video_generator):
        """Test file processing speed benchmarks."""
        test_cases = [
            {'size_mb': 0.1, 'max_time': 1.0},
            {'size_mb': 0.5, 'max_time': 2.0},
            {'size_mb': 1.0, 'max_time': 3.0},
            {'size_mb': 2.0, 'max_time': 5.0},
        ]
        
        for test_case in test_cases:
            content = self._generate_large_code_content(int(test_case['size_mb'] * 1024 * 1024))
            file_data = BytesIO(content.encode('utf-8'))
            
            data = {
                'duration': '20',
                'output_format': 'mp4'
            }
            
            start_time = time.time()
            response = client.post('/api/generate/typing',
                                 data=data,
                                 content_type='multipart/form-data',
                                 files={'text_file': (file_data, f'speed_test_{test_case["size_mb"]}mb.txt')})
            processing_time = time.time() - start_time
            
            assert response.status_code == 202
            assert processing_time < test_case['max_time'], \
                f"Processing {test_case['size_mb']}MB took {processing_time:.2f}s (max: {test_case['max_time']}s)"

    def test_line_count_performance(self, client, mock_video_generator):
        """Test performance with files having many lines."""
        # Create file with many short lines
        lines = ['print(f"Line {i}")' for i in range(10000)]  # 10k lines
        content = '\n'.join(lines)
        file_data = BytesIO(content.encode('utf-8'))
        
        data = {
            'duration': '30',
            'output_format': 'mp4'
        }
        
        start_time = time.time()
        response = client.post('/api/generate/typing',
                             data=data,
                             content_type='multipart/form-data',
                             files={'text_file': (file_data, 'many_lines.txt')})
        processing_time = time.time() - start_time
        
        assert response.status_code == 202
        assert processing_time < 5.0, f"Many lines processing took too long: {processing_time:.2f}s"

    def test_unicode_performance(self, client, mock_video_generator):
        """Test performance with Unicode-heavy content."""
        # Create content with various Unicode characters
        unicode_content = ""
        for i in range(1000):
            unicode_content += f"print('Unicode test: 世界 🌍 café ñoño αβγ δεζ {i}')\n"
        
        file_data = BytesIO(unicode_content.encode('utf-8'))
        
        data = {
            'duration': '30',
            'output_format': 'mp4'
        }
        
        start_time = time.time()
        response = client.post('/api/generate/typing',
                             data=data,
                             content_type='multipart/form-data',
                             files={'text_file': (file_data, 'unicode_test.txt')})
        processing_time = time.time() - start_time
        
        assert response.status_code == 202
        assert processing_time < 3.0, f"Unicode processing took too long: {processing_time:.2f}s"

    def _generate_large_code_content(self, target_size_bytes):
        """Generate large code content for testing."""
        base_code = '''def fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a, b):
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

# Example usage
calc = Calculator()
print(calc.add(5, 3))
print(calc.multiply(4, 7))

for i in range(10):
    print(f"Fibonacci({i}) = {fibonacci(i)}")

'''
        
        content = ""
        while len(content.encode('utf-8')) < target_size_bytes:
            content += base_code
            content += f"\n# Generated content block {len(content) // len(base_code)}\n"
        
        # Trim to exact size if needed
        while len(content.encode('utf-8')) > target_size_bytes:
            content = content[:-1]
        
        return content


class TestPerformanceRegression:
    """Test cases for performance regression detection."""
    
    def test_baseline_performance(self, client, mock_video_generator):
        """Establish baseline performance metrics."""
        # Standard test file
        content = "print('Hello, World!')\nfor i in range(100):\n    print(f'Count: {i}')"
        file_data = BytesIO(content.encode('utf-8'))
        
        data = {
            'duration': '20',
            'output_format': 'mp4'
        }
        
        # Run multiple times to get average
        times = []
        for _ in range(5):
            start_time = time.time()
            response = client.post('/api/generate/typing',
                                 data=data,
                                 content_type='multipart/form-data',
                                 files={'text_file': (file_data, 'baseline.txt')})
            processing_time = time.time() - start_time
            times.append(processing_time)
            
            assert response.status_code == 202
            
            # Reset file pointer
            file_data.seek(0)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Baseline should be very fast
        assert avg_time < 1.0, f"Baseline average time too slow: {avg_time:.2f}s"
        assert max_time < 2.0, f"Baseline max time too slow: {max_time:.2f}s"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
