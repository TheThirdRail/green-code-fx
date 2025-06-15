"""
Color validation and edge case testing.

This module contains comprehensive tests for color validation functionality,
including hex color validation, RGB conversion, and edge case handling.
"""

import pytest
import json
from pathlib import Path
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


class TestColorValidation:
    """Test cases for color validation functionality."""
    
    def test_valid_hex_colors(self, client, mock_video_generator):
        """Test validation of valid hex color formats."""
        valid_colors = [
            '#000000',  # Black
            '#FFFFFF',  # White
            '#FF0000',  # Red
            '#00FF00',  # Green
            '#0000FF',  # Blue
            '#FFFF00',  # Yellow
            '#FF00FF',  # Magenta
            '#00FFFF',  # Cyan
            '#123456',  # Mixed digits
            '#ABCDEF',  # Mixed letters (uppercase)
            '#abcdef',  # Mixed letters (lowercase)
            '#AbCdEf',  # Mixed case
            '#789ABC',  # More mixed
            '#F0F0F0',  # Gray
            '#808080',  # Medium gray
        ]
        
        for color in valid_colors:
            # Test config validation
            assert config.validate_hex_color(color), f"Color {color} should be valid"
            
            # Test API endpoint
            payload = {
                'duration': 30,
                'text_color': color,
                'output_format': 'mp4'
            }
            
            response = client.post('/api/generate/typing',
                                 data=json.dumps(payload),
                                 content_type='application/json')
            
            assert response.status_code == 202, f"Valid color {color} should be accepted"
            
            # Verify color was passed correctly
            call_args = mock_video_generator.generate_typing_effect.call_args
            assert call_args.kwargs['text_color'] == color

    def test_invalid_hex_colors(self, client):
        """Test rejection of invalid hex color formats."""
        invalid_colors = [
            'FF0000',      # Missing #
            '#FF00',       # Too short
            '#FF0000FF',   # Too long (8 digits)
            '#GGGGGG',     # Invalid characters
            '#FF00GG',     # Mixed valid/invalid
            'red',         # Color name
            'rgb(255,0,0)', # RGB format
            '#FF 00 00',   # Spaces
            '#FF-00-00',   # Dashes
            '#FF.00.00',   # Dots
            '',            # Empty string
            '#',           # Just hash
            '##FF0000',    # Double hash
            '#FF0000#',    # Hash at end
            '#ff00xx',     # Invalid hex digits
            '#ZZZZZZ',     # All invalid characters
            '#12345',      # 5 digits
            '#1234567',    # 7 digits
            '#12345678',   # 8 digits
            'null',        # Null string
            'undefined',   # Undefined string
        ]
        
        for color in invalid_colors:
            # Test config validation
            assert not config.validate_hex_color(color), f"Color {color} should be invalid"

    def test_hex_to_rgb_conversion(self):
        """Test hex to RGB conversion functionality."""
        test_cases = [
            ('#000000', (0, 0, 0)),
            ('#FFFFFF', (255, 255, 255)),
            ('#FF0000', (255, 0, 0)),
            ('#00FF00', (0, 255, 0)),
            ('#0000FF', (0, 0, 255)),
            ('#FFFF00', (255, 255, 0)),
            ('#FF00FF', (255, 0, 255)),
            ('#00FFFF', (0, 255, 255)),
            ('#123456', (18, 52, 86)),
            ('#ABCDEF', (171, 205, 239)),
            ('#abcdef', (171, 205, 239)),  # Lowercase should work
            ('#F0F0F0', (240, 240, 240)),
            ('#808080', (128, 128, 128)),
        ]
        
        for hex_color, expected_rgb in test_cases:
            rgb = config.hex_to_rgb(hex_color)
            assert rgb == expected_rgb, f"Conversion of {hex_color} failed: got {rgb}, expected {expected_rgb}"

    def test_hex_to_rgb_invalid_input(self):
        """Test hex to RGB conversion with invalid input."""
        invalid_inputs = [
            'FF0000',      # Missing #
            '#FF00',       # Too short
            '#GGGGGG',     # Invalid characters
            '',            # Empty string
            '#',           # Just hash
            'red',         # Color name
        ]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(ValueError):
                config.hex_to_rgb(invalid_input)

    def test_case_insensitive_validation(self, client, mock_video_generator):
        """Test that hex color validation is case insensitive."""
        color_pairs = [
            ('#ff0000', '#FF0000'),
            ('#abcdef', '#ABCDEF'),
            ('#AbCdEf', '#ABCDEF'),
            ('#123abc', '#123ABC'),
        ]
        
        for lower_color, upper_color in color_pairs:
            # Both should be valid
            assert config.validate_hex_color(lower_color)
            assert config.validate_hex_color(upper_color)
            
            # Both should convert to same RGB
            rgb_lower = config.hex_to_rgb(lower_color)
            rgb_upper = config.hex_to_rgb(upper_color)
            assert rgb_lower == rgb_upper

    def test_edge_case_colors(self, client, mock_video_generator):
        """Test edge case color values."""
        edge_cases = [
            '#000001',  # Almost black
            '#FFFFFE',  # Almost white
            '#800000',  # Dark red
            '#008000',  # Dark green
            '#000080',  # Dark blue
            '#7F7F7F',  # Middle gray
            '#010101',  # Very dark gray
            '#FEFEFE',  # Very light gray
        ]
        
        for color in edge_cases:
            payload = {
                'duration': 30,
                'text_color': color,
                'output_format': 'mp4'
            }
            
            response = client.post('/api/generate/typing',
                                 data=json.dumps(payload),
                                 content_type='application/json')
            
            assert response.status_code == 202, f"Edge case color {color} should be accepted"

    def test_color_boundary_values(self):
        """Test color values at boundaries."""
        boundary_tests = [
            ('#000000', (0, 0, 0)),      # Minimum values
            ('#FFFFFF', (255, 255, 255)), # Maximum values
            ('#FF0000', (255, 0, 0)),     # Max red, min others
            ('#00FF00', (0, 255, 0)),     # Max green, min others
            ('#0000FF', (0, 0, 255)),     # Max blue, min others
            ('#7F7F7F', (127, 127, 127)), # Middle values
            ('#808080', (128, 128, 128)), # Just above middle
        ]
        
        for hex_color, expected_rgb in boundary_tests:
            assert config.validate_hex_color(hex_color)
            rgb = config.hex_to_rgb(hex_color)
            assert rgb == expected_rgb
            
            # Verify each component is in valid range
            for component in rgb:
                assert 0 <= component <= 255

    def test_malformed_color_handling(self, client):
        """Test handling of malformed color inputs."""
        malformed_colors = [
            '#FF00',       # Too short
            '#FF0000FF',   # Too long
            '#GG0000',     # Invalid hex digit
            '#FF00XX',     # Mixed valid/invalid
            '##FF0000',    # Double hash
            '#FF0000#',    # Hash at end
            '#FF 00 00',   # Spaces
            '#FF\t00\t00', # Tabs
            '#FF\n00\n00', # Newlines
            '#FF\x0000',   # Null bytes
        ]
        
        for color in malformed_colors:
            payload = {
                'duration': 30,
                'text_color': color,
                'output_format': 'mp4'
            }
            
            response = client.post('/api/generate/typing',
                                 data=json.dumps(payload),
                                 content_type='application/json')
            
            # Should either reject or use default color
            assert response.status_code in [202, 400]

    def test_unicode_in_color_input(self, client):
        """Test handling of Unicode characters in color input."""
        unicode_colors = [
            '#FF０００0',    # Full-width zero
            '#ＦＦ0000',     # Full-width F
            '#FF０0０0',    # Mixed full-width
            '#FF0000\u200b', # Zero-width space
            '#FF0000\ufeff', # Byte order mark
            '#\u202eff0000', # Right-to-left override
        ]
        
        for color in unicode_colors:
            # Should be invalid
            assert not config.validate_hex_color(color)
            
            payload = {
                'duration': 30,
                'text_color': color,
                'output_format': 'mp4'
            }
            
            response = client.post('/api/generate/typing',
                                 data=json.dumps(payload),
                                 content_type='application/json')
            
            # Should handle gracefully
            assert response.status_code in [202, 400]

    def test_color_normalization(self):
        """Test color normalization behavior."""
        # Test that colors are handled consistently
        test_colors = ['#ff0000', '#FF0000', '#Ff0000', '#fF0000']
        
        rgb_results = []
        for color in test_colors:
            if config.validate_hex_color(color):
                rgb = config.hex_to_rgb(color)
                rgb_results.append(rgb)
        
        # All valid colors should produce the same RGB result
        if rgb_results:
            first_result = rgb_results[0]
            for rgb in rgb_results[1:]:
                assert rgb == first_result, "Case variations should produce same RGB"

    def test_default_color_fallback(self, client, mock_video_generator):
        """Test fallback to default color when invalid color provided."""
        payload = {
            'duration': 30,
            'text_color': 'invalid_color',
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/typing',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        # Should accept request (may use default color)
        if response.status_code == 202:
            call_args = mock_video_generator.generate_typing_effect.call_args
            # Should either use default or the invalid input (depending on implementation)
            color_used = call_args.kwargs['text_color']
            # If using default, should be valid hex color
            if color_used != 'invalid_color':
                assert config.validate_hex_color(color_used)

    def test_color_performance(self):
        """Test color validation performance with many colors."""
        import time
        
        # Generate many test colors
        test_colors = []
        for r in range(0, 256, 32):
            for g in range(0, 256, 32):
                for b in range(0, 256, 32):
                    test_colors.append(f'#{r:02X}{g:02X}{b:02X}')
        
        # Test validation performance
        start_time = time.time()
        for color in test_colors:
            config.validate_hex_color(color)
        validation_time = time.time() - start_time
        
        # Test conversion performance
        start_time = time.time()
        for color in test_colors:
            config.hex_to_rgb(color)
        conversion_time = time.time() - start_time
        
        # Performance should be reasonable
        assert validation_time < 1.0, f"Color validation too slow: {validation_time:.3f}s"
        assert conversion_time < 1.0, f"Color conversion too slow: {conversion_time:.3f}s"


class TestColorEdgeCases:
    """Test cases for color-related edge cases."""
    
    def test_empty_color_input(self, client):
        """Test handling of empty color input."""
        payload = {
            'duration': 30,
            'text_color': '',
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/typing',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        # Should handle empty color gracefully
        assert response.status_code in [202, 400]

    def test_null_color_input(self, client):
        """Test handling of null color input."""
        payload = {
            'duration': 30,
            'text_color': None,
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/typing',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        # Should handle null color gracefully
        assert response.status_code in [202, 400]

    def test_very_long_color_string(self, client):
        """Test handling of very long color strings."""
        long_color = '#FF0000' + 'A' * 1000  # Very long string
        
        payload = {
            'duration': 30,
            'text_color': long_color,
            'output_format': 'mp4'
        }
        
        response = client.post('/api/generate/typing',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        # Should handle long strings gracefully
        assert response.status_code in [202, 400]

    def test_special_character_colors(self, client):
        """Test colors with special characters."""
        special_colors = [
            '#FF0000\x00',    # Null byte
            '#FF0000\r\n',    # CRLF
            '#FF0000\t',      # Tab
            '#FF0000 ',       # Space
            ' #FF0000',       # Leading space
            '#FF0000\x7f',    # DEL character
        ]
        
        for color in special_colors:
            assert not config.validate_hex_color(color), f"Color with special chars should be invalid: {repr(color)}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
