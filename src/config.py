"""
Configuration management for Green-Code FX video effects generator.

This module centralizes all configuration settings for the containerized
video generation system, supporting both environment variables and defaults.
"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Central configuration class for the video effects generator."""
    
    # ========================================================================
    # Core Application Settings
    # ========================================================================
    
    # Application metadata
    APP_NAME: str = "Green-Code FX Generator"
    APP_VERSION: str = "1.0.0"
    
    # Environment
    ENVIRONMENT: str = os.getenv("FLASK_ENV", "production")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # ========================================================================
    # Video Generation Settings
    # ========================================================================
    
    # Display settings for 4K output
    VIDEO_WIDTH: int = 3840
    VIDEO_HEIGHT: int = 2160
    TARGET_FPS: int = 60
    
    # Typing effect settings
    TYPING_WPM: int = 150  # Words per minute
    TYPING_CHAR_DELAY_MS: int = 80  # Milliseconds per character
    TYPING_CURSOR_BLINK_HZ: float = 1.0  # Cursor blink frequency
    TYPING_FONT_SIZE: int = 32
    TYPING_SCROLL_LINE_THRESHOLD: int = 92  # Start scrolling after this many lines
    TYPING_LOOP_PAUSE_SECONDS: int = 2
    TYPING_FADE_FRAMES: int = 30
    
    # Matrix rain effect settings
    MATRIX_FONT_SIZES: tuple = (16, 32, 48)  # Far, mid, near
    MATRIX_COLUMN_SPACING: int = 16
    MATRIX_TRAIL_OPACITY: int = 25  # 10% opacity for trailing effect
    MATRIX_LOOP_DURATION_FRAMES: int = 900  # 15 seconds at 60fps
    MATRIX_RESET_VARIANCE_PX: int = 200
    
    # Colors (RGB tuples)
    COLOR_BLACK: tuple = (0, 0, 0)
    COLOR_GREEN: tuple = (0, 255, 0)
    COLOR_BRIGHT_GREEN: tuple = (191, 255, 0)  # #BFFF00
    COLOR_DARK_GREEN: tuple = (0, 128, 0)      # #008000
    
    # ========================================================================
    # File System Paths
    # ========================================================================
    
    # Base directories
    BASE_DIR: Path = Path(__file__).parent.parent
    SRC_DIR: Path = BASE_DIR / "src"
    
    # Asset directories
    ASSETS_DIR: Path = Path(os.getenv("ASSETS_DIR", str(BASE_DIR / "assets")))
    FONTS_DIR: Path = ASSETS_DIR / "fonts"
    
    # Output directories
    OUTPUT_DIR: Path = Path(os.getenv("VIDEO_OUTPUT_DIR", str(BASE_DIR / "output")))
    TEMP_DIR: Path = Path(os.getenv("TEMP_DIR", str(BASE_DIR / "temp")))
    
    # Source files
    SNAKE_CODE_FILE: Path = ASSETS_DIR / "snake_code.txt"
    
    # Font files
    JETBRAINS_MONO_FONT: Path = FONTS_DIR / "JetBrainsMono-Regular.ttf"
    MATRIX_KATAKANA_FONT: Path = FONTS_DIR / "matrix-katakana.ttf"
    
    # ========================================================================
    # API Configuration
    # ========================================================================
    
    # Server settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8082"))
    
    # Job management
    MAX_CONCURRENT_JOBS: int = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))
    JOB_TIMEOUT_SECONDS: int = 3600  # 1 hour max per job
    
    # File serving
    MAX_DOWNLOAD_SIZE_MB: int = 1000  # 1GB max download
    CLEANUP_TEMP_FILES_HOURS: int = 1  # Auto-cleanup temp files after 1 hour
    
    # ========================================================================
    # Video Encoding Configuration
    # ========================================================================

    # H.264 encoding settings optimized for chroma-key content
    VIDEO_CRF: int = int(os.getenv("VIDEO_CRF", "18"))  # High quality, smaller than lossless
    VIDEO_PRESET: str = os.getenv("VIDEO_PRESET", "medium")  # Balance speed vs compression
    VIDEO_PROFILE: str = os.getenv("VIDEO_PROFILE", "high")  # H.264 profile
    VIDEO_LEVEL: str = os.getenv("VIDEO_LEVEL", "4.1")  # H.264 level for 4K

    # Additional encoding options for chroma-key optimization
    VIDEO_TUNE: str = os.getenv("VIDEO_TUNE", "film")  # Optimize for film content
    VIDEO_PIXEL_FORMAT: str = os.getenv("VIDEO_PIXEL_FORMAT", "yuv420p")

    # ========================================================================
    # SDL and Pygame Configuration
    # ========================================================================

    # Headless rendering
    SDL_VIDEODRIVER: str = os.getenv("SDL_VIDEODRIVER", "dummy")
    
    # ========================================================================
    # Logging Configuration
    # ========================================================================
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    
    # ========================================================================
    # Security Settings
    # ========================================================================
    
    # CORS settings
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 10

    # ========================================================================
    # Monitoring and Metrics Configuration
    # ========================================================================

    # Prometheus metrics
    METRICS_ENABLED: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required directories exist."""
        directories = [
            cls.OUTPUT_DIR,
            cls.TEMP_DIR,
            cls.ASSETS_DIR,
            cls.FONTS_DIR,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration and required files."""
        # Check required directories
        if not cls.ASSETS_DIR.exists():
            raise FileNotFoundError(f"Assets directory not found: {cls.ASSETS_DIR}")
        
        # Check required files
        if not cls.SNAKE_CODE_FILE.exists():
            print(f"Warning: Snake code file not found: {cls.SNAKE_CODE_FILE}")
        
        return True
    
    @classmethod
    def get_font_path(cls, font_name: str) -> Optional[Path]:
        """Get path to a specific font file."""
        font_mapping = {
            "jetbrains": cls.JETBRAINS_MONO_FONT,
            "matrix": cls.MATRIX_KATAKANA_FONT,
        }
        
        font_path = font_mapping.get(font_name.lower())
        if font_path and font_path.exists():
            return font_path
        
        return None


# Global configuration instance
config = Config()

# Ensure directories exist on import
config.ensure_directories()
