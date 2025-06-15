# Green-Code FX Testing Documentation

This document describes the comprehensive testing infrastructure for the Green-Code FX UI Enhancement project, covering all aspects of testing from unit tests to browser automation.

## Testing Overview

The testing suite is organized into several categories to ensure comprehensive coverage:

- **Unit Tests**: Test individual components and functions
- **Integration Tests**: Test component interactions and workflows
- **Security Tests**: Test security vulnerabilities and validation
- **Performance Tests**: Test system performance under load
- **Browser Tests**: Test frontend UI across different browsers
- **Responsive Tests**: Test mobile and tablet compatibility

## Test Structure

```
tests/
├── test_api.py                      # Existing API tests
├── test_integration.py              # Existing integration tests
├── test_performance.py              # Existing performance tests
├── test_enhanced_typing_api.py      # Phase 6: Enhanced API unit tests
├── test_file_upload_integration.py  # Phase 6: File upload integration tests
├── test_frontend_browsers.py        # Phase 6: Cross-browser UI tests
├── test_responsive_design.py        # Phase 6: Responsive design tests
├── test_security_validation.py      # Phase 6: Security and validation tests
├── test_large_file_performance.py   # Phase 6: Large file performance tests
└── test_color_validation.py         # Phase 6: Color validation tests
```

## Running Tests

### Prerequisites

Install testing dependencies:
```bash
pip install -r requirements.txt
```

For browser testing, ensure Chrome and/or Firefox are installed with appropriate drivers.

### Quick Test Run

Run all Phase 6 tests:
```bash
python scripts/run_phase6_tests.py
```

### Individual Test Categories

**Unit Tests:**
```bash
pytest tests/test_enhanced_typing_api.py -v
pytest tests/test_color_validation.py -v
```

**Integration Tests:**
```bash
pytest tests/test_file_upload_integration.py -v
pytest tests/test_security_validation.py -v
```

**Performance Tests:**
```bash
pytest tests/test_large_file_performance.py -v
```

**Browser Tests:**
```bash
pytest tests/test_frontend_browsers.py -v
pytest tests/test_responsive_design.py -v
```

### Test Coverage

Generate coverage report:
```bash
pytest --cov=src --cov-report=html tests/
```

## Test Categories Detail

### 1. Enhanced Typing API Tests (`test_enhanced_typing_api.py`)

Tests the new enhanced typing API functionality:
- Custom font parameter validation
- Font size parameter handling
- Color parameter validation
- Custom text input processing
- File upload parameter handling
- Default parameter fallback
- Multipart form data handling
- Font API endpoint testing

**Key Test Cases:**
- Valid and invalid font families
- Font size boundary testing (12-72px)
- Hex color validation
- Custom text vs file upload conflict detection
- Default parameter application

### 2. File Upload Integration Tests (`test_file_upload_integration.py`)

Comprehensive file upload security and functionality testing:
- Valid text file upload processing
- File extension validation
- File size limit enforcement
- Malicious filename handling
- Unicode content processing
- Binary file rejection
- Concurrent upload handling
- File cleanup verification

**Security Focus:**
- Path traversal attack prevention
- Malicious file extension blocking
- File size bomb protection
- Unicode security issues
- Binary file disguised as text

### 3. Frontend Browser Tests (`test_frontend_browsers.py`)

Cross-browser compatibility testing using Selenium:
- Page loading verification
- Form element presence and functionality
- Text input method switching
- Font size slider operation
- Color picker functionality
- Character counter updates
- Form validation behavior
- Navigation link testing

**Supported Browsers:**
- Chrome (headless)
- Firefox (headless)

### 4. Responsive Design Tests (`test_responsive_design.py`)

Mobile and tablet compatibility testing:
- Multiple device viewport testing
- Mobile navigation toggle
- Form layout responsiveness
- Touch-friendly control sizing
- Text readability on mobile
- Horizontal scrolling prevention
- Landscape orientation support
- Accessibility compliance

**Device Viewports Tested:**
- Mobile Portrait: 375×667
- Mobile Landscape: 667×375
- Tablet Portrait: 768×1024
- Tablet Landscape: 1024×768
- Desktop Small: 1280×720
- Desktop Large: 1920×1080

### 5. Security Validation Tests (`test_security_validation.py`)

Comprehensive security testing:
- File upload security vulnerabilities
- XSS protection in text inputs
- SQL injection attempt handling
- Command injection prevention
- Color input validation security
- HTTP parameter pollution
- Header injection attempts
- Rate limiting verification

**Attack Vectors Tested:**
- Malicious file extensions
- Path traversal attacks
- Null byte injection
- Unicode security exploits
- Binary file disguising
- Various injection attacks

### 6. Large File Performance Tests (`test_large_file_performance.py`)

Performance testing with large files:
- Large text file upload performance
- Maximum size file handling
- Memory usage monitoring
- Concurrent upload performance
- Processing speed benchmarks
- Line count performance
- Unicode content performance
- Performance regression detection

**Performance Metrics:**
- Upload processing time
- Memory usage delta
- CPU utilization
- Concurrent handling capacity
- Baseline performance establishment

### 7. Color Validation Tests (`test_color_validation.py`)

Comprehensive color validation testing:
- Valid hex color format testing
- Invalid color format rejection
- Hex to RGB conversion accuracy
- Case insensitive validation
- Edge case color values
- Boundary value testing
- Malformed color handling
- Unicode character rejection

**Color Test Coverage:**
- All valid hex formats (#000000 to #FFFFFF)
- Invalid formats (missing #, wrong length, invalid chars)
- Edge cases (almost black/white, boundary values)
- Performance with many colors

## Test Configuration

### Environment Variables

```bash
# Test environment settings
FLASK_ENV=testing
SDL_VIDEODRIVER=dummy
API_HOST=localhost
API_PORT=8082
```

### Browser Configuration

Browser tests use headless mode by default. To run with visible browsers:
```python
# In test files, modify browser options
chrome_options.add_argument('--headless')  # Remove this line
```

### Performance Thresholds

Current performance expectations:
- File upload processing: < 10 seconds for 5MB files
- Memory usage: < 50MB delta for large files
- Browser test execution: < 15 seconds per test
- API response time: < 1 second for standard requests

## Continuous Integration

### GitHub Actions Integration

The test suite is designed to run in CI/CD environments:

```yaml
# Example GitHub Actions workflow
- name: Run Phase 6 Tests
  run: |
    pip install -r requirements.txt
    python scripts/run_phase6_tests.py
```

### Docker Testing

Run tests in Docker environment:
```bash
docker-compose exec video-fx-generator python scripts/run_phase6_tests.py
```

## Test Data Management

### Fixtures and Mocks

- **Mock Video Generator**: Prevents actual video generation during tests
- **Sample Text Files**: Temporary files for upload testing
- **Performance Monitor**: System resource monitoring
- **Browser Drivers**: Automated browser control

### Test Data Cleanup

All tests include proper cleanup:
- Temporary files are automatically removed
- Browser sessions are properly closed
- Mock objects are reset between tests
- Memory is garbage collected after performance tests

## Troubleshooting

### Common Issues

**Browser tests failing:**
- Ensure Chrome/Firefox is installed
- Check if application is running on localhost:8082
- Verify no firewall blocking browser drivers

**Performance tests timing out:**
- Increase timeout values for slower systems
- Check available system memory
- Ensure no other heavy processes running

**File upload tests failing:**
- Verify file system permissions
- Check temporary directory access
- Ensure sufficient disk space

### Debug Mode

Run tests with verbose output:
```bash
pytest tests/ -v -s --tb=long
```

Enable debug logging:
```bash
export FLASK_ENV=development
pytest tests/ -v
```

## Contributing

When adding new tests:

1. Follow existing naming conventions
2. Include comprehensive docstrings
3. Add appropriate fixtures and mocks
4. Update this documentation
5. Ensure tests are deterministic and isolated
6. Add performance assertions where appropriate
7. Include security considerations

## Test Metrics

Current test coverage targets:
- Unit test coverage: > 90%
- Integration test coverage: > 80%
- Security test coverage: 100% of attack vectors
- Browser compatibility: Chrome, Firefox
- Device compatibility: Mobile, Tablet, Desktop

---

For questions or issues with the testing infrastructure, refer to the project documentation or create an issue in the repository.
