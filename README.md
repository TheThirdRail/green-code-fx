# Green-Code FX - Containerized Video Effects Generator

A Docker-based system for generating high-quality 4K chroma-key video effects, specifically designed for:

1. **Typing Code Effect** - Simulates real-time code typing with customizable speed and styling
2. **Matrix Rain Effect** - Creates the iconic digital rain effect with depth and seamless looping

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

The API will be available at `http://localhost:8082`

## 📋 API Usage

### Health Check

```bash
curl http://localhost:8082/api/health
```

### Generate Typing Effect

```bash
curl -X POST http://localhost:8082/api/generate/typing \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 90,
    "source_file": "snake_code.txt",
    "output_format": "mp4"
  }'
```

### Generate Matrix Rain

```bash
curl -X POST http://localhost:8082/api/generate/matrix \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 15,
    "loop_seamless": true,
    "output_format": "mp4"
  }'
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
│   └── config.py              # Configuration management
├── assets/                     # Fonts and source files
├── output/                     # Generated videos
├── scripts/                    # Utility scripts
└── docs/                       # Documentation
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

### Matrix Rain
- **Resolution**: 3840×2160 (4K)
- **Frame Rate**: 60 FPS
- **Fonts**: Multi-depth (16px, 32px, 48px)
- **Colors**: Bright green (#BFFF00) fading to dark green
- **Duration**: Seamless 15-second loops

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
# Run in container
docker-compose exec video-fx-generator pytest tests/

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

- Non-root container execution
- Read-only filesystem (except output/temp)
- Resource limits (4GB RAM, 2 CPU cores)
- Network isolation (only port 8082 exposed)

## 📝 License

See individual font licenses in `assets/fonts/LICENSES`

## 🤝 Contributing

1. Follow the coding standards in `.augment-guidelines`
2. All commits must pass linting and tests
3. Use conventional commit messages
4. Update CHANGELOG.md for user-facing changes

---

For detailed technical specifications, see `.augment-guidelines`
