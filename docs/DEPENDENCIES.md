# Green-Code FX Dependencies Documentation

This document provides comprehensive information about all dependencies used in the Green-Code FX project, including their purposes, versions, and licensing information.

## Overview

Green-Code FX uses a carefully curated set of dependencies to provide video generation, web interface, and testing capabilities while maintaining security and performance standards.

## Core Dependencies

### Graphics and Video Generation

#### pygame (≥2.5.0, <3.0.0)
- **Purpose**: Headless graphics rendering and video frame generation
- **License**: LGPL 2.1
- **Usage**: Core video generation engine, font rendering, graphics operations
- **Critical**: Yes - Required for all video generation functionality

#### SDL2 (via pygame)
- **Purpose**: Low-level graphics and audio library
- **License**: zlib License
- **Usage**: Headless rendering with dummy video driver
- **Configuration**: `SDL_VIDEODRIVER=dummy` for container environments

### Web Framework

#### Flask (≥2.3.0, <3.0.0)
- **Purpose**: Web framework for API and UI serving
- **License**: BSD 3-Clause
- **Usage**: REST API endpoints, template rendering, static file serving
- **Features**: Job management, file upload handling, status monitoring

#### Flask-CORS (≥4.0.0, <5.0.0)
- **Purpose**: Cross-Origin Resource Sharing support
- **License**: MIT
- **Usage**: Enable frontend access to API endpoints
- **Configuration**: Configurable origins for security

### Data Handling

#### pydantic (≥2.0.0, <3.0.0)
- **Purpose**: Data validation and serialization
- **License**: MIT
- **Usage**: API request/response validation, configuration management
- **Features**: Type checking, automatic validation, JSON schema generation

#### requests (≥2.31.0, <3.0.0)
- **Purpose**: HTTP client library
- **License**: Apache 2.0
- **Usage**: Health checks, external API calls, testing
- **Features**: Session management, timeout handling, SSL verification

### Monitoring and Logging

#### structlog (≥23.0.0, <24.0.0)
- **Purpose**: Structured logging framework
- **License**: MIT
- **Usage**: JSON-formatted logs, contextual logging, debugging
- **Features**: Processor chains, context binding, performance logging

#### prometheus-client (≥0.17.0, <1.0.0)
- **Purpose**: Metrics collection and monitoring
- **License**: Apache 2.0
- **Usage**: Performance metrics, resource monitoring, alerting
- **Features**: Custom metrics, HTTP exposition, time series data

#### psutil (≥5.9.0, <6.0.0)
- **Purpose**: System and process monitoring
- **License**: BSD 3-Clause
- **Usage**: Resource usage monitoring, performance testing
- **Features**: CPU, memory, disk usage tracking

### Configuration Management

#### python-dotenv (≥1.0.0, <2.0.0)
- **Purpose**: Environment variable management
- **License**: BSD 3-Clause
- **Usage**: Configuration loading from .env files
- **Features**: Development/production configuration separation

#### python-dateutil (≥2.8.0, <3.0.0)
- **Purpose**: Date and time utilities
- **License**: Apache 2.0 / BSD 3-Clause
- **Usage**: Timestamp handling, job scheduling, log formatting
- **Features**: Timezone handling, parsing, formatting

### File System Utilities

#### pathlib2 (≥2.3.0, <3.0.0)
- **Purpose**: Enhanced path handling (Python 3.12 compatibility)
- **License**: MIT
- **Usage**: Cross-platform path operations, file management
- **Features**: Path manipulation, file system operations

---

## Development Dependencies

### Testing Framework

#### pytest (≥7.4.0, <8.0.0)
- **Purpose**: Testing framework
- **License**: MIT
- **Usage**: Unit tests, integration tests, test discovery
- **Features**: Fixtures, parametrization, plugins

#### pytest-cov (≥4.1.0, <5.0.0)
- **Purpose**: Test coverage reporting
- **License**: MIT
- **Usage**: Code coverage analysis, coverage reports
- **Features**: HTML reports, coverage thresholds

#### pytest-html (≥3.2.0, <4.0.0)
- **Purpose**: HTML test reports
- **License**: Mozilla Public License 2.0
- **Usage**: Generate comprehensive test reports
- **Features**: Test results visualization, failure details

#### pytest-mock (≥3.11.0, <4.0.0)
- **Purpose**: Mocking utilities for tests
- **License**: MIT
- **Usage**: Mock external dependencies, isolate tests
- **Features**: Fixture-based mocking, automatic cleanup

### Browser Testing

#### selenium (≥4.15.0, <5.0.0)
- **Purpose**: Web browser automation
- **License**: Apache 2.0
- **Usage**: Cross-browser UI testing, responsive design validation
- **Features**: Chrome/Firefox support, headless testing
- **Requirements**: Browser drivers (ChromeDriver, GeckoDriver)

### Code Quality

#### black (≥23.0.0, <24.0.0)
- **Purpose**: Code formatting
- **License**: MIT
- **Usage**: Automatic code formatting, style consistency
- **Configuration**: Line length 100, consistent formatting

#### flake8 (≥6.0.0, <7.0.0)
- **Purpose**: Code linting and style checking
- **License**: MIT
- **Usage**: PEP 8 compliance, error detection
- **Features**: Plugin system, configurable rules

#### mypy (≥1.5.0, <2.0.0)
- **Purpose**: Static type checking
- **License**: MIT
- **Usage**: Type hint validation, error prevention
- **Features**: Gradual typing, IDE integration

### Type Hints

#### types-requests (≥2.31.0)
- **Purpose**: Type hints for requests library
- **License**: Apache 2.0
- **Usage**: Better IDE support, type checking
- **Features**: Complete type coverage for requests

---

## System Dependencies

### Container Runtime

#### Docker (≥20.10.0)
- **Purpose**: Containerization platform
- **License**: Apache 2.0
- **Usage**: Application packaging, deployment, isolation
- **Features**: Multi-stage builds, volume mounting, networking

#### Docker Compose (≥2.0.0)
- **Purpose**: Multi-container orchestration
- **License**: Apache 2.0
- **Usage**: Service orchestration, development environment
- **Features**: Service dependencies, volume management

### Video Processing

#### FFmpeg (≥6.0)
- **Purpose**: Video encoding and processing
- **License**: LGPL 2.1+ / GPL 2+
- **Usage**: Frame assembly, video encoding, format conversion
- **Features**: H.264 encoding, 4K support, lossless compression

### Fonts

#### JetBrains Mono (v2.304)
- **Purpose**: Primary monospace font for code display
- **License**: SIL Open Font License 1.1
- **Usage**: Typing effect text rendering
- **Features**: Programming ligatures, excellent readability

---

## Version Management

### Python Version Requirement

- **Minimum**: Python 3.12
- **Recommended**: Python 3.12.x (latest patch version)
- **Compatibility**: Tested on Python 3.12.0+

### Dependency Version Strategy

- **Core Dependencies**: Conservative version ranges for stability
- **Development Dependencies**: More flexible ranges for latest features
- **Security Updates**: Regular updates for security-critical packages
- **Breaking Changes**: Careful evaluation before major version updates

### Version Pinning Policy

- **Production**: Pin exact versions for reproducible builds
- **Development**: Use version ranges for flexibility
- **Testing**: Test against minimum and maximum supported versions
- **Security**: Immediate updates for security vulnerabilities

---

## Installation Instructions

### Standard Installation

```bash
# Install all dependencies
pip install -r requirements.txt

# Development installation with editable mode
pip install -e .
```

### Docker Installation

```bash
# Build container with all dependencies
docker-compose build

# Run with dependency isolation
docker-compose up
```

### Browser Testing Setup

```bash
# Install Chrome/Chromium
# Ubuntu/Debian:
sudo apt-get install chromium-browser

# Install ChromeDriver
# Download from: https://chromedriver.chromium.org/

# Install Firefox (optional)
sudo apt-get install firefox

# Install GeckoDriver
# Download from: https://github.com/mozilla/geckodriver/releases
```

---

## Security Considerations

### Dependency Security

- **Regular Updates**: Dependencies are updated monthly for security patches
- **Vulnerability Scanning**: Automated scanning for known vulnerabilities
- **License Compliance**: All dependencies use permissive or compatible licenses
- **Supply Chain**: Dependencies sourced from trusted repositories (PyPI, GitHub)

### Runtime Security

- **Container Isolation**: Dependencies run in isolated container environment
- **Non-root Execution**: All processes run as non-root user
- **Resource Limits**: Memory and CPU limits prevent resource exhaustion
- **Network Isolation**: Minimal network exposure (port 8082 only)

---

## Troubleshooting

### Common Issues

#### pygame Installation Issues
```bash
# Ubuntu/Debian
sudo apt-get install python3-dev libsdl2-dev

# macOS
brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf

# Windows
# Use pre-compiled wheels from PyPI
```

#### Selenium Browser Issues
```bash
# Verify browser installation
google-chrome --version
firefox --version

# Verify driver installation
chromedriver --version
geckodriver --version

# Update drivers if needed
```

#### FFmpeg Issues
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from: https://ffmpeg.org/download.html
```

### Performance Optimization

- **Memory Usage**: Monitor with psutil, optimize for large files
- **CPU Usage**: Parallel processing for video generation
- **Disk Usage**: Automatic cleanup of temporary files
- **Network Usage**: Efficient file upload handling

---

## License Summary

All dependencies use permissive licenses compatible with the project:

- **MIT License**: Most JavaScript and Python packages
- **Apache 2.0**: Enterprise-grade packages (requests, prometheus-client)
- **BSD 3-Clause**: System utilities (psutil, Flask)
- **LGPL 2.1**: Graphics libraries (pygame, FFmpeg)
- **SIL OFL 1.1**: Fonts (JetBrains Mono)

No GPL-licensed dependencies are used to maintain licensing flexibility.

---

For questions about dependencies or installation issues, see the [Troubleshooting Guide](TROUBLESHOOTING.md) or check the individual package documentation.
