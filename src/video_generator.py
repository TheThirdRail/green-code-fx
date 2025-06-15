"""
Core video generation module for Green-Code FX effects.

This module implements the actual video generation logic for both typing
and Matrix rain effects using Pygame with headless SDL rendering.
"""

import os
import random
import subprocess
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, List
import time

import pygame
import structlog

try:
    from .config import config
    from .performance_profiler import profiler
except ImportError:
    # Handle direct execution
    from config import config
    from performance_profiler import profiler


logger = structlog.get_logger()


class JobStatus(Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoGenerator:
    """Main video generator class for both effects."""
    
    def __init__(self):
        """Initialize the video generator."""
        # Set SDL video driver for headless operation
        os.environ["SDL_VIDEODRIVER"] = config.SDL_VIDEODRIVER
        
        # Initialize Pygame
        pygame.init()
        pygame.font.init()
        
        # Create display surface (headless)
        self.screen = pygame.display.set_mode((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
        pygame.display.set_caption("Green-Code FX Generator")
        
        # Hide mouse cursor
        pygame.mouse.set_visible(False)
        
        # Initialize clock for frame rate control
        self.clock = pygame.time.Clock()
        
        logger.info("Video generator initialized", 
                   resolution=f"{config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}",
                   sdl_driver=os.environ.get("SDL_VIDEODRIVER"))
    
    def generate_typing_effect(
        self,
        job_id: str,
        duration: int,
        source_file: str,
        output_format: str = "mp4",
        font_family: str = "jetbrains",
        font_size: int = None,
        text_color: str = "#00FF00",
        custom_text: Optional[str] = None,
        uploaded_file_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> str:
        """
        Generate typing code effect video with customization options.

        Args:
            job_id: Unique job identifier
            duration: Video duration in seconds
            source_file: Source code file to display (ignored if custom_text or uploaded_file_path provided)
            output_format: Output format ('mp4' or 'png')
            font_family: Font family to use ('jetbrains', 'courier', etc.)
            font_size: Font size in pixels (defaults to config value)
            text_color: Text color in hex format (#RRGGBB)
            custom_text: Custom text to display instead of source file
            uploaded_file_path: Path to uploaded text file
            progress_callback: Optional progress callback function

        Returns:
            Path to generated video file
        """
        # Use default font size if not provided
        if font_size is None:
            font_size = config.TYPING_FONT_SIZE

        # Convert hex color to RGB
        text_color_rgb = config.hex_to_rgb(text_color)

        logger.info("Starting typing effect generation",
                   job_id=job_id, duration=duration, source_file=source_file,
                   font_family=font_family, font_size=font_size, text_color=text_color)

        # Start overall profiling
        profiler.start_operation("typing_effect_total",
                                job_id=job_id,
                                duration=duration,
                                source_file=source_file,
                                font_family=font_family,
                                font_size=font_size)

        if progress_callback:
            progress_callback(5)

        try:
            # Load text content (priority: uploaded file > custom text > source file)
            profiler.start_operation("load_text_content")

            if uploaded_file_path:
                # Load from uploaded file
                with open(uploaded_file_path, 'r', encoding='utf-8') as f:
                    code_lines = [line.rstrip() for line in f.readlines()]
                content_source = f"uploaded file: {Path(uploaded_file_path).name}"
            elif custom_text:
                # Use custom text
                code_lines = [line.rstrip() for line in custom_text.splitlines()]
                content_source = "custom text input"
            else:
                # Load from source file
                source_path = config.ASSETS_DIR / source_file
                if not source_path.exists():
                    raise FileNotFoundError(f"Source file not found: {source_path}")

                with open(source_path, 'r', encoding='utf-8') as f:
                    code_lines = [line.rstrip() for line in f.readlines()]
                content_source = f"source file: {source_file}"

            profiler.end_operation("load_text_content",
                                 lines_loaded=len(code_lines),
                                 content_source=content_source)
            
            if progress_callback:
                progress_callback(10)

            # Load font
            profiler.start_operation("load_font", font_family=font_family, font_size=font_size)
            font_path = config.get_font_path(font_family)
            if font_path and font_path.exists():
                font = pygame.font.Font(str(font_path), font_size)
                font_loaded = True
            else:
                # Fallback to system fonts
                available_fonts = config.get_available_fonts()
                if font_family in available_fonts and available_fonts[font_family]["type"] == "system":
                    font_name = available_fonts[font_family]["name"]
                    font = pygame.font.SysFont(font_name, font_size)
                else:
                    # Ultimate fallback
                    font = pygame.font.SysFont("Courier New", font_size)
                font_loaded = False
            profiler.end_operation("load_font", font_loaded=font_loaded, font_family=font_family)
            
            # Calculate total frames needed
            total_frames = duration * config.TARGET_FPS
            frame_count = 0
            
            # Typing state
            current_line = 0
            current_char = 0
            typed_lines = []

            # Scrolling state
            scroll_offset = 0  # Number of lines scrolled off the top
            line_height = font.get_linesize()
            max_visible_lines = config.TYPING_SCROLL_LINE_THRESHOLD

            # Cursor state
            cursor_visible = True
            cursor_blink_timer = 0
            cursor_blink_interval = config.TARGET_FPS // (2 * config.TYPING_CURSOR_BLINK_HZ)  # Frames per blink

            # Looping state
            typing_complete = False
            pause_timer = 0
            pause_duration_frames = config.TYPING_LOOP_PAUSE_SECONDS * config.TARGET_FPS
            fade_timer = 0
            fade_duration_frames = config.TYPING_FADE_FRAMES
            loop_state = "typing"  # "typing", "paused", "fading", "restarting"

            # Create output directory for frames
            frames_dir = config.TEMP_DIR / f"{job_id}_frames"
            frames_dir.mkdir(exist_ok=True)

            if progress_callback:
                progress_callback(15)

            # Set up typing timer
            TYPE_EVENT = pygame.USEREVENT + 1
            pygame.time.set_timer(TYPE_EVENT, config.TYPING_CHAR_DELAY_MS)
            
            # Main generation loop
            profiler.start_operation("main_rendering_loop", total_frames=total_frames)
            running = True
            while running and frame_count < total_frames:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == TYPE_EVENT and loop_state == "typing":
                        # Add next character only during typing state
                        if current_line < len(code_lines):
                            line = code_lines[current_line]
                            if current_char < len(line):
                                current_char += 1
                            else:
                                # End of line reached
                                typed_lines.append(line)
                                current_line += 1
                                current_char = 0
                        else:
                            # All lines done - start pause phase
                            typing_complete = True
                            loop_state = "paused"
                            pause_timer = 0
                            pygame.time.set_timer(TYPE_EVENT, 0)  # Stop typing timer
                
                # Clear screen
                self.screen.fill(config.COLOR_BLACK)

                # Calculate scrolling if needed
                total_lines_to_display = len(typed_lines) + (1 if current_line < len(code_lines) else 0)
                if total_lines_to_display > max_visible_lines:
                    scroll_offset = total_lines_to_display - max_visible_lines
                else:
                    scroll_offset = 0

                # Draw all fully typed lines with scrolling
                y_offset = 10
                visible_line_count = 0

                for i, line in enumerate(typed_lines):
                    # Skip lines that are scrolled off the top
                    if i < scroll_offset:
                        continue

                    # Stop drawing if we've reached the bottom of the screen
                    if visible_line_count >= max_visible_lines:
                        break

                    text_surface = font.render(line, True, text_color_rgb)
                    self.screen.blit(text_surface, (10, y_offset))
                    y_offset += line_height
                    visible_line_count += 1

                # Draw current partial line if visible
                if (current_line < len(code_lines) and
                    visible_line_count < max_visible_lines and
                    len(typed_lines) - scroll_offset < max_visible_lines):

                    partial_line = code_lines[current_line][:current_char]
                    if partial_line:
                        text_surface = font.render(partial_line, True, text_color_rgb)
                        self.screen.blit(text_surface, (10, y_offset))

                    # Draw blinking cursor
                    cursor_blink_timer += 1
                    if cursor_blink_timer >= cursor_blink_interval:
                        cursor_visible = not cursor_visible
                        cursor_blink_timer = 0

                    if cursor_visible:
                        cursor_x = 10 + font.size(partial_line)[0] if partial_line else 10
                        cursor_rect = pygame.Rect(cursor_x, y_offset, 2, font_size)
                        pygame.draw.rect(self.screen, text_color_rgb, cursor_rect)

                # Handle loop state transitions
                if loop_state == "paused":
                    pause_timer += 1
                    if pause_timer >= pause_duration_frames:
                        loop_state = "fading"
                        fade_timer = 0

                elif loop_state == "fading":
                    # Apply fade-to-black overlay
                    fade_timer += 1
                    fade_alpha = int((fade_timer / fade_duration_frames) * 255)
                    fade_alpha = min(fade_alpha, 255)

                    fade_surface = pygame.Surface((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
                    fade_surface.fill(config.COLOR_BLACK)
                    fade_surface.set_alpha(fade_alpha)
                    self.screen.blit(fade_surface, (0, 0))

                    if fade_timer >= fade_duration_frames:
                        loop_state = "restarting"

                elif loop_state == "restarting":
                    # Reset all state for next loop
                    current_line = 0
                    current_char = 0
                    typed_lines = []
                    scroll_offset = 0
                    cursor_visible = True
                    cursor_blink_timer = 0
                    typing_complete = False
                    pause_timer = 0
                    fade_timer = 0
                    loop_state = "typing"

                    # Restart typing timer
                    pygame.time.set_timer(TYPE_EVENT, config.TYPING_CHAR_DELAY_MS)

                # Update display
                pygame.display.flip()
                
                # Save frame for both PNG sequence and MP4 generation
                profiler.start_operation("save_frame", frame_number=frame_count)
                frame_path = frames_dir / f"frame_{frame_count:06d}.png"
                pygame.image.save(self.screen, str(frame_path))
                profiler.end_operation("save_frame")
                
                # Update progress
                if progress_callback and frame_count % 60 == 0:  # Update every second
                    progress = 15 + int((frame_count / total_frames) * 70)
                    progress_callback(min(progress, 85))
                
                frame_count += 1
                self.clock.tick(config.TARGET_FPS)
            
            # Stop typing timer
            pygame.time.set_timer(TYPE_EVENT, 0)
            profiler.end_operation("main_rendering_loop", frames_generated=frame_count)

            if progress_callback:
                progress_callback(90)

            # Generate output file
            if output_format == "mp4":
                profiler.start_operation("video_assembly", format="mp4")
                output_file = self._assemble_video(job_id, frames_dir, "typing")
                profiler.end_operation("video_assembly")
            else:
                profiler.start_operation("png_archive", format="png")
                output_file = self._create_png_archive(job_id, frames_dir, "typing")
                profiler.end_operation("png_archive")
            
            if progress_callback:
                progress_callback(100)

            profiler.end_operation("typing_effect_total",
                                 frames_generated=frame_count,
                                 output_file=output_file,
                                 success=True)

            logger.info("Typing effect generation completed",
                       job_id=job_id, output_file=output_file, frames=frame_count)

            return output_file

        except Exception as e:
            profiler.end_operation("typing_effect_total",
                                 error=str(e),
                                 success=False)
            logger.error("Typing effect generation failed", job_id=job_id, error=str(e))
            raise
    

    def _assemble_video(self, job_id: str, frames_dir: Path, effect_type: str) -> str:
        """
        Assemble PNG frames into MP4 video using FFmpeg with optimized settings.

        Uses CRF 18 (high quality) instead of lossless to significantly reduce file size
        while maintaining excellent quality for chroma-key content. The 'film' tune
        and 'medium' preset provide good compression efficiency.

        Args:
            job_id: Unique job identifier for output naming
            frames_dir: Directory containing PNG frame sequence
            effect_type: Type of effect for filename generation

        Returns:
            Path to the generated MP4 file
        """
        output_file = config.OUTPUT_DIR / f"{job_id}_{effect_type}.mp4"
        
        # FFmpeg command optimized for chroma-key content
        cmd = [
            "ffmpeg", "-y",  # Overwrite output file
            "-framerate", str(config.TARGET_FPS),
            "-i", str(frames_dir / "frame_%06d.png"),
            "-c:v", "libx264",
            "-crf", str(config.VIDEO_CRF),  # High quality, optimized file size
            "-preset", config.VIDEO_PRESET,  # Encoding speed vs compression balance
            "-profile:v", config.VIDEO_PROFILE,  # H.264 profile
            "-level:v", config.VIDEO_LEVEL,  # H.264 level for 4K
            "-tune", config.VIDEO_TUNE,  # Optimize for film content
            "-pix_fmt", config.VIDEO_PIXEL_FORMAT,
            "-movflags", "+faststart",  # Optimize for web streaming
            str(output_file)
        ]
        
        logger.info("Assembling video with FFmpeg", job_id=job_id, output_file=output_file)
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("Video assembly completed", job_id=job_id)
            
            # Clean up frame files
            import shutil
            shutil.rmtree(frames_dir)
            
            return str(output_file)
            
        except subprocess.CalledProcessError as e:
            logger.error("FFmpeg failed", job_id=job_id, error=e.stderr)
            raise RuntimeError(f"Video assembly failed: {e.stderr}")
    
    def _create_png_archive(self, job_id: str, frames_dir: Path, effect_type: str) -> str:
        """Create ZIP archive of PNG frames."""
        import zipfile
        
        output_file = config.OUTPUT_DIR / f"{job_id}_{effect_type}_frames.zip"
        
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for frame_file in sorted(frames_dir.glob("*.png")):
                zipf.write(frame_file, frame_file.name)
        
        # Clean up frame files
        import shutil
        shutil.rmtree(frames_dir)
        
        logger.info("PNG archive created", job_id=job_id, output_file=output_file)
        return str(output_file)
    


    def __del__(self):
        """Clean up Pygame resources."""
        try:
            pygame.quit()
        except:
            pass
