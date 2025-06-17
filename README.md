# Green-Code FX - Containerized Video Effects Generator

A Docker-based system for generating high-quality 4K chroma-key video effects with both web UI and API access, specifically designed for:

1. **Typing Code Effect** - Simulates real-time code typing with customizable fonts, colors, and text input options

## ✨ Features

### 🌐 Web Interface
- **User-friendly web UI** at `http://localhost:8082`
- **Font customization** with multiple font family options
- **Color picker** with hex color input and validation
- **Text input options**: Custom text, file upload (.txt), or default code
- **Real-time preview** of typing effect settings
- **Drag-and-drop file upload** with progress tracking
- **Responsive design** for desktop, tablet, and mobile devices
- **Progress monitoring** with real-time job status updates

### 🔧 API Access
- **RESTful API** for programmatic access
- **Enhanced typing endpoint** with customization parameters
- **Job management** with status tracking and progress monitoring
- **File download** capabilities for generated videos

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- 4GB+ available RAM
- 10GB+ free disk space

### Build and Run

```bash
# Build the container
./scripts/build.sh

# Start the service
./scripts/run.sh

# Check health
./scripts/health-check.sh
```

The web interface and API will be available at `http://localhost:8082`

## 🌐 Web Interface Usage

### Accessing the Web UI

Open your browser and navigate to `http://localhost:8082` to access the user-friendly web interface.

### Using the Typing Effect Generator

1. **Choose Text Input Method:**
   - **Custom Text**: Enter your own code or text directly
   - **File Upload**: Upload a .txt file (max 10MB) with drag-and-drop support
   - **Default Code**: Use the built-in Snake game code example

2. **Customize Appearance:**
   - **Font Family**: Select from available fonts (JetBrains Mono recommended)
   - **Font Size**: Adjust from 12px to 72px using the slider
   - **Text Color**: Use the color picker or enter hex values (e.g., #00FF00)

3. **Set Duration**: Choose video length from 10 to 600 seconds

4. **Preview & Generate:**
   - Click "Preview" to see how your text will look
   - Click "Generate Video" to start the creation process
   - Monitor progress in real-time
   - Download your video when complete

### Mobile & Tablet Support

The web interface is fully responsive and optimized for:
- **Mobile devices** (portrait and landscape)
- **Tablets** (iPad and Android tablets)
- **Desktop browsers** (Chrome, Firefox, Safari, Edge)

## 📋 API Usage

### Health Check

```bash
curl http://localhost:8082/api/health
```

### Generate Typing Effect

#### Basic Usage
```bash
curl -X POST http://localhost:8082/api/generate/typing \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 90,
    "output_format": "mp4"
  }'
```

#### Enhanced Usage with Customization
```bash
curl -X POST http://localhost:8082/api/generate/typing \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 60,
    "font_family": "jetbrains",
    "font_size": 32,
    "text_color": "#00FF00",
    "custom_text": "print(\"Hello, World!\")\nfor i in range(10):\n    print(f\"Count: {i}\")",
    "output_format": "mp4"
  }'
```

#### File Upload Usage
```bash
curl -X POST http://localhost:8082/api/generate/typing \
  -F "duration=45" \
  -F "font_family=jetbrains" \
  -F "font_size=28" \
  -F "text_color=#FF0000" \
  -F "text_file=@my_code.txt" \
  -F "output_format=mp4"
```

Response:
```json
{
  "job_id": "typing_20240614_123456",
  "status": "queued",
  "estimated_duration": "45s"
}
```

#### Enhanced API Parameters

| Parameter | Type | Description | Default | Range/Options |
|-----------|------|-------------|---------|---------------|
| `duration` | integer | Video duration in seconds | 90 | 10-600 |
| `font_family` | string | Font family to use | "jetbrains" | Available fonts via `/api/fonts` |
| `font_size` | integer | Font size in pixels | 32 | 12-72 |
| `text_color` | string | Text color in hex format | "#00FF00" | Valid hex colors |
| `custom_text` | string | Custom text content | null | Max 50,000 characters |
| `text_file` | file | Text file upload (.txt only) | null | Max 10MB |
| `output_format` | string | Output video format | "mp4" | "mp4" |

**Note**: Use either `custom_text` OR `text_file`, not both.

### List Available Fonts

```bash
curl http://localhost:8082/api/fonts
```

### Check Job Status

```bash
curl http://localhost:8082/api/jobs/{job_id}
```

### Download Generated Video

```bash
curl -O http://localhost:8082/api/download/{filename}
```

## 🏗️ Architecture

- **Base**: Python 3.12 + Pygame + SDL2 (headless)
- **Web API**: Flask with async job processing
- **Video Assembly**: FFmpeg for H.264 encoding
- **Storage**: Volume-mounted persistent storage
- **Port**: 8082 (configurable)

## 📁 Project Structure

```
green-code-fx/
├── docker-compose.yml          # Service orchestration
├── Dockerfile                  # Container definition
├── requirements.txt            # Python dependencies
├── src/                        # Application source
│   ├── web_api.py             # Flask API server
│   ├── video_generator.py     # Core generation logic
│   ├── config.py              # Configuration management
│   ├── templates/             # HTML templates for web UI
│   │   ├── base.html          # Base template with navigation
│   │   └── index.html         # Main UI page
│   └── static/                # Static web assets
│       ├── css/               # Stylesheets
│       └── js/                # JavaScript files
├── assets/                     # Fonts and source files
│   ├── fonts/                 # Font files
│   └── snake_code.txt         # Default code content
├── output/                     # Generated videos
├── temp/                       # Temporary frame storage
├── tests/                      # Comprehensive test suite
│   ├── test_enhanced_typing_api.py      # Enhanced API tests
│   ├── test_file_upload_integration.py  # File upload tests
│   ├── test_frontend_browsers.py        # Browser UI tests
│   ├── test_responsive_design.py        # Mobile/tablet tests
│   ├── test_security_validation.py      # Security tests
│   ├── test_large_file_performance.py   # Performance tests
│   └── test_color_validation.py         # Color validation tests
├── scripts/                    # Utility scripts
│   ├── build.sh               # Container build script
│   ├── run.sh                 # Container run script
│   ├── health-check.sh        # Health verification
│   └── run_phase6_tests.py    # Test runner
└── docs/                       # Documentation
    ├── TESTING.md             # Testing documentation
    ├── TROUBLESHOOTING.md     # Troubleshooting guide
    └── OPERATIONS.md          # Operations manual
```

## ⚙️ Configuration

Key environment variables:

- `SDL_VIDEODRIVER=dummy` - Headless rendering
- `API_PORT=8082` - API server port
- `MAX_CONCURRENT_JOBS=2` - Job concurrency limit
- `VIDEO_OUTPUT_DIR=/app/output` - Output directory

## 🎨 Video Specifications

### Typing Effect
- **Resolution**: 3840×2160 (4K)
- **Frame Rate**: 60 FPS
- **Font**: JetBrains Mono 32px
- **Colors**: RGB(0,255,0) on black
- **Timing**: ~150 WPM typing speed



## 🔧 Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
export SDL_VIDEODRIVER=dummy

# Run API server
python -m src.web_api
```

### Testing

```bash
# Run all tests in container
docker-compose exec video-fx-generator pytest tests/

# Run Phase 6 comprehensive test suite
python scripts/run_phase6_tests.py

# Run specific test categories
pytest tests/test_enhanced_typing_api.py -v          # Enhanced API tests
pytest tests/test_file_upload_integration.py -v     # File upload tests
pytest tests/test_frontend_browsers.py -v           # Browser UI tests
pytest tests/test_responsive_design.py -v           # Mobile/tablet tests
pytest tests/test_security_validation.py -v         # Security tests
pytest tests/test_large_file_performance.py -v      # Performance tests

# Local testing
pytest tests/
```

## 📊 Monitoring

- Health endpoint: `/api/health`
- Container logs: `docker logs green-code-fx-generator`
- Resource usage: `docker stats green-code-fx-generator`

## 🎬 Video Compositing

Generated videos use pure green-on-black for easy chroma keying:

1. **Recommended**: Use "Screen" or "Add" blend mode (drops black, keeps green)
2. **Alternative**: Luma key (keys out black based on brightness)
3. **Avoid**: Green screen keying (would remove the green text)

## 🔒 Security

### Container Security
- Non-root container execution
- Read-only filesystem (except output/temp)
- Resource limits (4GB RAM, 2 CPU cores)
- Network isolation (only port 8082 exposed)

### Web UI Security
- File upload validation (type, size, content)
- Input sanitization and validation
- CORS protection for API endpoints
- XSS protection via template auto-escaping
- Rate limiting for API requests

### File Upload Security
- Only .txt files allowed
- Maximum file size: 10MB
- Malicious filename protection
- Path traversal attack prevention
- Binary file detection and rejection

## 📝 License

See individual font licenses in `assets/fonts/LICENSES`

## 🤝 Contributing

1. Follow the coding standards in `.augment-guidelines`
2. All commits must pass linting and tests
3. Use conventional commit messages
4. Update CHANGELOG.md for user-facing changes

---

For detailed technical specifications, see `.augment-guidelines`
