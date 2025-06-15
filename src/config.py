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
    TYPING_FONT_SIZE: int = 32  # Default font size in points
    TYPING_FONT_SIZE_MIN: int = 8   # Minimum allowed font size in points
    TYPING_FONT_SIZE_MAX: int = 150 # Maximum allowed font size in points
    TYPING_SCROLL_LINE_THRESHOLD: int = 92  # Start scrolling after this many lines
    TYPING_LOOP_PAUSE_SECONDS: int = 2
    TYPING_FADE_FRAMES: int = 30
    

    
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

    # File upload settings
    MAX_UPLOAD_SIZE_MB: int = 10  # Maximum file upload size in MB
    ALLOWED_TEXT_EXTENSIONS: set = {'.txt'}  # Allowed file extensions for text upload
    
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
        }

        font_path = font_mapping.get(font_name.lower())
        if font_path and font_path.exists():
            return font_path

        return None

    @classmethod
    def get_available_fonts(cls) -> dict:
        """Get list of available fonts with their display names and paths."""
        available_fonts = {}

        # Check bundled fonts
        font_mapping = {
            "jetbrains": {
                "name": "JetBrains Mono",
                "path": cls.JETBRAINS_MONO_FONT,
                "type": "bundled"
            }
        }

        for font_id, font_info in font_mapping.items():
            if font_info["path"].exists():
                available_fonts[font_id] = font_info

        # Add common system fonts as fallbacks
        system_fonts = {
            "courier": {
                "name": "Courier New",
                "path": None,  # System font
                "type": "system"
            },
            "consolas": {
                "name": "Consolas",
                "path": None,  # System font
                "type": "system"
            },
            "monaco": {
                "name": "Monaco",
                "path": None,  # System font
                "type": "system"
            }
        }

        available_fonts.update(system_fonts)
        return available_fonts

    @classmethod
    def validate_hex_color(cls, color_str: str) -> bool:
        """Validate hex color format (#RRGGBB)."""
        import re
        hex_pattern = r'^#[0-9A-Fa-f]{6}$'
        return bool(re.match(hex_pattern, color_str))

    @classmethod
    def hex_to_rgb(cls, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        if not cls.validate_hex_color(hex_color):
            raise ValueError(f"Invalid hex color format: {hex_color}")

        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# Global configuration instance
config = Config()

# Ensure directories exist on import
config.ensure_directories()
