# Multi-stage build for Green-Code FX video effects generator
# Optimized for headless Pygame rendering in containerized environment

# ============================================================================
# Stage 1: Base dependencies and system packages
# ============================================================================
FROM python:3.12-slim-bullseye as base

# Set environment variables for container optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for Pygame, SDL2, and FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    # SDL2 and graphics libraries for headless rendering
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libportmidi-dev \
    # FFmpeg for video assembly
    ffmpeg \
    # System utilities
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ============================================================================
# Stage 2: Python dependencies
# ============================================================================
FROM base as dependencies

# Create application user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 3: Runtime environment
# ============================================================================
FROM dependencies as runtime

# Copy application source code
COPY src/ ./src/
COPY assets/ ./assets/

# Create necessary directories with proper permissions
RUN mkdir -p /app/output /app/temp /app/logs && \
    chown -R appuser:appuser /app

# Copy utility scripts
COPY scripts/ ./scripts/
RUN chmod +x ./scripts/*.sh

# Set environment variables for headless operation
ENV SDL_VIDEODRIVER=dummy \
    DISPLAY=:99 \
    VIDEO_OUTPUT_DIR=/app/output \
    ASSETS_DIR=/app/assets \
    TEMP_DIR=/app/temp \
    API_HOST=0.0.0.0 \
    API_PORT=8082 \
    MAX_CONCURRENT_JOBS=2 \
    FLASK_ENV=production

# Switch to non-root user
USER appuser

# Expose API port
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8082/api/health || exit 1

# Default command starts the Flask API server
CMD ["python", "-m", "src.web_api"]
