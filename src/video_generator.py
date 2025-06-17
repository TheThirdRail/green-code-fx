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
from typing import Callable, Optional
import time

import pygame
import structlog

try:
    from .config import config
    from .performance_profiler import profiler
    from .progress_estimator import progress_estimator
    from .error_recovery import error_recovery_service, ErrorContext
    from .text_processor import text_processor
except ImportError:
    # Handle direct execution
    from config import config
    from performance_profiler import profiler
    from progress_estimator import progress_estimator
    from error_recovery import error_recovery_service, ErrorContext
    from text_processor import text_processor


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

        logger.info(
            "Video generator initialized",
            resolution=f"{config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}",
            sdl_driver=os.environ.get("SDL_VIDEODRIVER"),
        )

    def generate_typing_effect(
        self,
        job_id: str,
        duration: int,
        source_file: str,
        output_format: str = "mp4",
        font_family: str = "jetbrains",
        font_size: int = None,
        text_color: str = "#00FF00",
        typing_speed: int = None,
        custom_text: Optional[str] = None,
        uploaded_file_path: Optional[str] = None,
        fps: int = None,
        resolution: str = None,
        progress_callback: Optional[Callable[[int], None]] = None,
        typo_probability: float = None,
        error_delay: float = None,
    ) -> str:
        """
        Generate typing code effect video with customization options.

        Args:
            job_id: Unique job identifier
            duration: Video duration in seconds
            source_file: Source code file to display. Ignored if custom_text or
                uploaded_file_path is provided.
            output_format: Output format ('mp4' or 'png')
            font_family: Font family to use ('jetbrains', 'courier', etc.)
            font_size: Font size in points (defaults to config value)
            text_color: Text color in hex format (#RRGGBB)
            typing_speed: Typing speed in words per minute (defaults to config value)
            custom_text: Custom text to display instead of source file
            uploaded_file_path: Path to uploaded text file
            fps: Frame rate in frames per second (defaults to config value)
            resolution: Video resolution ('1080p', '1440p', '4k', defaults to config)
            progress_callback: Optional progress callback function
            typo_probability: Chance of a typo per character
            error_delay: Seconds to wait before correcting a typo

        Returns:
            Path to generated video file
        """
        # Use default font size if not provided
        if font_size is None:
            font_size = config.TYPING_FONT_SIZE

        # Use default typing speed if not provided
        if typing_speed is None:
            typing_speed = config.TYPING_WPM

        # Use default FPS if not provided
        if fps is None:
            fps = config.TARGET_FPS

        if typo_probability is None:
            typo_probability = config.TYPING_TYPO_PROBABILITY
        if error_delay is None:
            error_delay = config.TYPING_ERROR_DELAY_SECONDS

        # Parse resolution and get dimensions
        if resolution is None:
            resolution = "4k"

        video_width, video_height = self._get_resolution_dimensions(resolution)

        # Calculate character delay from WPM (Words Per Minute)
        # Average word length is ~5 characters, so chars per minute = WPM * 5
        chars_per_minute = typing_speed * 5
        chars_per_second = chars_per_minute / 60
        char_delay_ms = int(1000 / chars_per_second)

        error_delay_frames = int(error_delay * fps)

        # Convert hex color to RGB
        text_color_rgb = config.hex_to_rgb(text_color)

        # Update screen size if resolution is different from current
        if (video_width, video_height) != (config.VIDEO_WIDTH, config.VIDEO_HEIGHT):
            self.screen = pygame.display.set_mode((video_width, video_height))
            logger.info(
                "Updated screen resolution",
                new_resolution=f"{video_width}x{video_height}",
                previous_resolution=f"{config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}",
            )

        logger.info(
            "Starting typing effect generation",
            job_id=job_id,
            duration=duration,
            source_file=source_file,
            font_family=font_family,
            font_size=font_size,
            text_color=text_color,
            typing_speed=typing_speed,
            char_delay_ms=char_delay_ms,
            fps=fps,
            resolution=f"{video_width}x{video_height}",
            typo_probability=typo_probability,
            error_delay_frames=error_delay_frames,
        )

        # Start overall profiling
        profiler.start_operation(
            "typing_effect_total",
            job_id=job_id,
            duration=duration,
            source_file=source_file,
            font_family=font_family,
            font_size=font_size,
        )

        if progress_callback:
            progress_callback(5)

        try:
            # Load text content (priority: uploaded file > custom text > source file)
            profiler.start_operation("load_text_content")

            # Load and process text with smart text processing
            if uploaded_file_path:
                # Load from uploaded file
                with open(uploaded_file_path, "r", encoding="utf-8") as f:
                    text_content = f.read()
                filename = Path(uploaded_file_path).name
                content_source = f"uploaded file: {filename}"
            elif custom_text:
                # Use custom text
                text_content = custom_text
                filename = None
                content_source = "custom text input"
            else:
                # Load from source file
                source_path = config.ASSETS_DIR / source_file
                if not source_path.exists():
                    raise FileNotFoundError(f"Source file not found: {source_path}")

                with open(source_path, "r", encoding="utf-8") as f:
                    text_content = f.read()
                filename = source_file
                content_source = f"source file: {source_file}"

            # Process text with language detection and syntax highlighting
            processed_text = text_processor.process_text(
                text=text_content, filename=filename, typing_speed=typing_speed
            )

            # Extract lines for typing effect
            code_lines = [line.rstrip() for line in processed_text.lines]

            # Precompute positions for simulated typos
            import string

            typo_positions = {}
            typo_chars = string.ascii_letters + string.digits + string.punctuation
            for idx, line in enumerate(code_lines):
                if random.random() < typo_probability and len(line) > 3:
                    pos = random.randint(0, max(0, len(line) - 2))
                    wrong = random.choice(typo_chars)
                    if wrong == line[pos]:
                        alt_choices = [c for c in typo_chars if c != line[pos]]
                        wrong = random.choice(alt_choices)
                    typo_positions[(idx, pos)] = wrong

            logger.info(
                "Text processed with smart features",
                job_id=job_id,
                language=processed_text.language_info.name,
                confidence=processed_text.language_info.confidence,
                detection_method=processed_text.language_info.detection_method,
                total_tokens=len(processed_text.tokens),
                estimated_typing_time=processed_text.estimated_typing_time,
            )

            # Store processed text for syntax highlighting
            self.processed_text = processed_text

            profiler.end_operation(
                "load_text_content",
                lines_loaded=len(code_lines),
                content_source=content_source,
            )

            if progress_callback:
                progress_callback(10)

            # Load font
            profiler.start_operation(
                "load_font", font_family=font_family, font_size=font_size
            )
            font_path = config.get_font_path(font_family)
            if font_path and font_path.exists():
                font = pygame.font.Font(str(font_path), font_size)
                font_loaded = True
            else:
                # Fallback to system fonts
                available_fonts = config.get_available_fonts()
                if (
                    font_family in available_fonts
                    and available_fonts[font_family]["type"] == "system"
                ):
                    font_name = available_fonts[font_family]["name"]
                    font = pygame.font.SysFont(font_name, font_size)
                else:
                    # Ultimate fallback
                    font = pygame.font.SysFont("Courier New", font_size)
                font_loaded = False
            profiler.end_operation(
                "load_font", font_loaded=font_loaded, font_family=font_family
            )

            # Calculate total frames needed
            total_frames = duration * fps
            frame_count = 0

            # Typing state
            current_line = 0
            current_char = 0
            typed_lines = []
            current_display_line = ""
            typing_state_inner = "normal"  # normal, post_typo, backspacing, correcting
            typo_buffer = ""
            typo_correct_char = ""
            typo_delay_counter = 0
            backspace_count = 0
            correction_index = 0
            typo_error_pos = 0

            # Scrolling state
            scroll_offset = 0  # Number of lines scrolled off the top
            line_height = font.get_linesize()
            max_visible_lines = min(
                config.TYPING_SCROLL_LINE_THRESHOLD,
                max(1, (video_height - 20) // line_height),
            )

            # Cursor state
            cursor_visible = True
            cursor_blink_timer = 0
            cursor_blink_interval = fps // (
                2 * config.TYPING_CURSOR_BLINK_HZ
            )  # Frames per blink

            # Looping state
            pause_timer = 0
            pause_duration_frames = config.TYPING_LOOP_PAUSE_SECONDS * fps
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
            pygame.time.set_timer(TYPE_EVENT, char_delay_ms)

            # Main generation loop
            profiler.start_operation("main_rendering_loop", total_frames=total_frames)
            running = True
            while running and frame_count < total_frames:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == TYPE_EVENT and loop_state == "typing":
                        if current_line < len(code_lines):
                            line = code_lines[current_line]
                            if typing_state_inner == "normal":
                                if (current_line, current_char) in typo_positions:
                                    wrong = typo_positions[(current_line, current_char)]
                                    current_display_line += wrong
                                    typo_correct_char = line[current_char]
                                    typo_error_pos = current_char
                                    current_char += 1
                                    typing_state_inner = "post_typo"
                                    typo_delay_counter = error_delay_frames
                                    typo_buffer = ""
                                else:
                                    current_display_line += line[current_char]
                                    current_char += 1
                            elif typing_state_inner == "post_typo":
                                if current_char < len(line):
                                    current_display_line += line[current_char]
                                    typo_buffer += line[current_char]
                                    current_char += 1
                                typo_delay_counter -= 1
                                if typo_delay_counter <= 0 or current_char >= len(line):
                                    typing_state_inner = "backspacing"
                                    backspace_count = len(typo_buffer) + 1
                                    current_char = typo_error_pos
                            elif typing_state_inner == "backspacing":
                                if backspace_count > 0 and current_display_line:
                                    current_display_line = current_display_line[:-1]
                                    backspace_count -= 1
                                if backspace_count <= 0:
                                    typing_state_inner = "correcting"
                                    correction_index = 0
                            elif typing_state_inner == "correcting":
                                if correction_index == 0:
                                    current_display_line += typo_correct_char
                                    correction_index += 1
                                elif correction_index <= len(typo_buffer):
                                    current_display_line += typo_buffer[
                                        correction_index - 1
                                    ]
                                    correction_index += 1
                                if correction_index > len(typo_buffer):
                                    typing_state_inner = "normal"
                                    typo_buffer = ""
                                    typo_correct_char = ""
                            if typing_state_inner == "normal" and current_char >= len(
                                line
                            ):
                                typed_lines.append(current_display_line)
                                current_display_line = ""
                                current_char = 0
                                current_line += 1
                        else:
                            loop_state = "paused"
                            pause_timer = 0
                            pygame.time.set_timer(TYPE_EVENT, 0)

                # Clear screen
                self.screen.fill(config.COLOR_BLACK)

                # Calculate scrolling if needed
                # Count completed lines plus current line being typed (if any)
                total_lines_to_display = len(typed_lines) + (
                    1 if current_line < len(code_lines) else 0
                )

                # Start scrolling immediately when we reach the maximum visible lines
                # This ensures the cursor stays at the bottom edge without delay
                if total_lines_to_display >= max_visible_lines:
                    scroll_offset = total_lines_to_display - max_visible_lines + 1
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

                    # Use syntax highlighting for complete lines
                    self.render_syntax_highlighted_text(
                        line, font, 10, y_offset, scroll_offset + visible_line_count
                    )
                    y_offset += line_height
                    visible_line_count += 1

                # Draw current partial line if visible
                if (
                    current_line < len(code_lines)
                    and visible_line_count < max_visible_lines
                    and len(typed_lines) - scroll_offset < max_visible_lines
                ):
                    partial_line = current_display_line
                    if partial_line:
                        # Use syntax highlighting for partial lines
                        self.render_syntax_highlighted_text(
                            partial_line, font, 10, y_offset, current_line
                        )

                    # Draw blinking cursor
                    cursor_blink_timer += 1
                    if cursor_blink_timer >= cursor_blink_interval:
                        cursor_visible = not cursor_visible
                        cursor_blink_timer = 0

                    if cursor_visible:
                        cursor_x = (
                            10 + font.size(partial_line)[0] if partial_line else 10
                        )
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

                    fade_surface = pygame.Surface((video_width, video_height))
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
                    pause_timer = 0
                    fade_timer = 0
                    loop_state = "typing"

                    # Restart typing timer
                    pygame.time.set_timer(TYPE_EVENT, char_delay_ms)

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
                self.clock.tick(fps)

            # Stop typing timer
            pygame.time.set_timer(TYPE_EVENT, 0)
            profiler.end_operation("main_rendering_loop", frames_generated=frame_count)

            if progress_callback:
                progress_callback(90)

            # Generate output file
            if output_format == "mp4":
                profiler.start_operation("video_assembly", format="mp4")
                output_file = self._assemble_video(job_id, frames_dir, "typing", fps)
                profiler.end_operation("video_assembly")
            elif output_format == "gif":
                profiler.start_operation("gif_assembly", format="gif")
                output_file = self._assemble_gif(job_id, frames_dir, "typing", fps)
                profiler.end_operation("gif_assembly")
            else:
                profiler.start_operation("png_archive", format="png")
                output_file = self._create_png_archive(job_id, frames_dir, "typing")
                profiler.end_operation("png_archive")

            if progress_callback:
                progress_callback(100)

            # Get total generation time from profiler
            total_generation_time = profiler.end_operation(
                "typing_effect_total",
                frames_generated=frame_count,
                output_file=output_file,
                success=True,
            )

            # Record metrics for progress estimation
            try:
                file_size = output_file.stat().st_size if output_file.exists() else 0
                generation_time = (
                    total_generation_time.duration if total_generation_time else 0
                )

                # Prepare parameters for recording
                estimation_parameters = {
                    "duration": duration,
                    "source_file": source_file,
                    "output_format": output_format,
                    "font_family": font_family,
                    "font_size": font_size,
                    "text_color": text_color,
                    "typing_speed": typing_speed,
                    "custom_text": custom_text,
                    "fps": fps,
                    "resolution": resolution,
                }

                progress_estimator.record_generation(
                    job_id=job_id,
                    effect_type="typing",
                    parameters=estimation_parameters,
                    generation_time=generation_time,
                    frame_count=frame_count,
                    file_size_bytes=file_size,
                    success=True,
                )
            except Exception as e:
                logger.warning(
                    "Failed to record generation metrics", job_id=job_id, error=str(e)
                )

            logger.info(
                "Typing effect generation completed",
                job_id=job_id,
                output_file=output_file,
                frames=frame_count,
            )

            return output_file

        except Exception as e:
            total_generation_time = profiler.end_operation(
                "typing_effect_total", error=str(e), success=False
            )

            # Record failed generation metrics
            try:
                generation_time = (
                    total_generation_time.duration if total_generation_time else 0
                )

                estimation_parameters = {
                    "duration": duration,
                    "source_file": source_file,
                    "output_format": output_format,
                    "font_family": font_family,
                    "font_size": font_size,
                    "text_color": text_color,
                    "typing_speed": typing_speed,
                    "custom_text": custom_text,
                    "fps": fps,
                    "resolution": resolution,
                }

                progress_estimator.record_generation(
                    job_id=job_id,
                    effect_type="typing",
                    parameters=estimation_parameters,
                    generation_time=generation_time,
                    frame_count=0,
                    file_size_bytes=0,
                    success=False,
                    error_message=str(e),
                )
            except Exception as record_error:
                logger.warning(
                    "Failed to record failed generation metrics",
                    job_id=job_id,
                    error=str(record_error),
                )

            logger.error("Typing effect generation failed", job_id=job_id, error=str(e))
            raise

    def render_syntax_highlighted_text(
        self, text: str, font: pygame.font.Font, x: int, y: int, line_number: int = 0
    ) -> int:
        """
        Render text with syntax highlighting support.

        Args:
            text: Text to render
            font: Pygame font object
            x: X position
            y: Y position
            line_number: Line number for token lookup

        Returns:
            Width of rendered text
        """
        if not hasattr(self, "processed_text") or not self.processed_text.tokens:
            # Fallback to plain text rendering
            text_surface = font.render(text, True, config.hex_to_rgb("#00FF00"))
            self.screen.blit(text_surface, (x, y))
            return text_surface.get_width()

        # Find tokens for this text
        current_x = x
        text_start = sum(
            len(line) + 1 for line in self.processed_text.lines[:line_number]
        )  # +1 for newlines
        text_end = text_start + len(text)

        # Find relevant tokens
        relevant_tokens = []
        for token in self.processed_text.tokens:
            if token.start_pos < text_end and token.end_pos > text_start:
                # Calculate overlap
                overlap_start = max(token.start_pos, text_start)
                overlap_end = min(token.end_pos, text_end)

                if overlap_start < overlap_end:
                    # Extract the overlapping text
                    token_text_start = overlap_start - token.start_pos
                    token_text_end = token_text_start + (overlap_end - overlap_start)
                    overlapping_text = token.text[token_text_start:token_text_end]

                    # Calculate position within the line
                    line_offset = overlap_start - text_start

                    relevant_tokens.append(
                        {
                            "text": overlapping_text,
                            "color": token.color,
                            "offset": line_offset,
                        }
                    )

        # Sort tokens by offset
        relevant_tokens.sort(key=lambda t: t["offset"])

        # Render tokens with colors
        last_offset = 0
        for token_info in relevant_tokens:
            offset = token_info["offset"]

            # Render any plain text before this token
            if offset > last_offset:
                plain_text = text[last_offset:offset]
                if plain_text:
                    color = config.hex_to_rgb("#00FF00")  # Default green
                    text_surface = font.render(plain_text, True, color)
                    self.screen.blit(text_surface, (current_x, y))
                    current_x += text_surface.get_width()

            # Render the colored token
            token_text = token_info["text"]
            if token_text:
                try:
                    color = config.hex_to_rgb(token_info["color"])
                except Exception:
                    color = config.hex_to_rgb("#00FF00")  # Fallback to green

                text_surface = font.render(token_text, True, color)
                self.screen.blit(text_surface, (current_x, y))
                current_x += text_surface.get_width()

            last_offset = offset + len(token_info["text"])

        # Render any remaining plain text
        if last_offset < len(text):
            remaining_text = text[last_offset:]
            if remaining_text:
                color = config.hex_to_rgb("#00FF00")  # Default green
                text_surface = font.render(remaining_text, True, color)
                self.screen.blit(text_surface, (current_x, y))
                current_x += text_surface.get_width()

        return current_x - x

    def _assemble_video(
        self, job_id: str, frames_dir: Path, effect_type: str, fps: int = None
    ) -> str:
        """
        Assemble PNG frames into MP4 video using FFmpeg with optimized settings.

        Uses CRF 18 (high quality) instead of lossless to significantly reduce file size
        while maintaining excellent quality for chroma-key content. The 'film' tune
        and 'medium' preset provide good compression efficiency.

        Args:
            job_id: Unique job identifier for output naming
            frames_dir: Directory containing PNG frame sequence
            effect_type: Type of effect for filename generation
            fps: Frame rate for the video (defaults to config value)

        Returns:
            Path to the generated MP4 file
        """
        # Use default FPS if not provided
        if fps is None:
            fps = config.TARGET_FPS

        output_file = config.OUTPUT_DIR / f"{job_id}_{effect_type}.mp4"

        # FFmpeg command optimized for chroma-key content
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-framerate",
            str(fps),
            "-i",
            str(frames_dir / "frame_%06d.png"),
            "-c:v",
            "libx264",
            "-crf",
            str(config.VIDEO_CRF),  # High quality, optimized file size
            "-preset",
            config.VIDEO_PRESET,  # Encoding speed vs compression balance
            "-profile:v",
            config.VIDEO_PROFILE,  # H.264 profile
            "-level:v",
            config.VIDEO_LEVEL,  # H.264 level for 4K
            "-tune",
            config.VIDEO_TUNE,  # Optimize for film content
            "-pix_fmt",
            config.VIDEO_PIXEL_FORMAT,
            "-movflags",
            "+faststart",  # Optimize for web streaming
            str(output_file),
        ]

        logger.info(
            "Assembling video with FFmpeg", job_id=job_id, output_file=output_file
        )

        # Create error context for recovery
        context = ErrorContext(
            operation="ffmpeg_video_assembly",
            job_id=job_id,
            parameters={"output_format": "mp4", "frames_dir": str(frames_dir)},
            attempt_number=1,
            timestamp=time.time(),
            duration_before_error=0,
        )

        def ffmpeg_operation():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info("Video assembly completed", job_id=job_id)
                return result
            except subprocess.CalledProcessError as e:
                logger.error("FFmpeg failed", job_id=job_id, error=e.stderr)
                raise RuntimeError(f"Video assembly failed: {e.stderr}")

        try:
            # Execute with error recovery
            error_recovery_service.execute_retry_strategy(
                operation=ffmpeg_operation,
                context=context,
                max_retries=2,
                base_delay=2.0,
            )

            # Clean up frame files on success
            import shutil

            shutil.rmtree(frames_dir)

            return str(output_file)

        except Exception as e:
            # Analyze error and provide recovery recommendations
            error_report = error_recovery_service.analyze_error(e, context)
            logger.error(
                "Video assembly failed after recovery attempts",
                job_id=job_id,
                error_id=error_report.error_id,
                category=error_report.category.value,
                user_message=error_report.user_message,
            )
            raise

    def _assemble_gif(
        self, job_id: str, frames_dir: Path, effect_type: str, fps: int = None
    ) -> str:
        """
        Assemble PNG frames into GIF using FFmpeg with optimized settings.

        Creates a high-quality GIF with optimized palette and compression.
        Uses a two-pass approach for better quality and smaller file size.

        Args:
            job_id: Unique job identifier for output naming
            frames_dir: Directory containing PNG frame sequence
            effect_type: Type of effect for filename generation
            fps: Frame rate for the GIF (defaults to config value)

        Returns:
            Path to the generated GIF file
        """
        # Use default FPS if not provided
        if fps is None:
            fps = config.TARGET_FPS

        output_file = config.OUTPUT_DIR / f"{job_id}_{effect_type}.gif"
        palette_file = config.TEMP_DIR / f"{job_id}_palette.png"

        # Ensure temp directory exists
        config.TEMP_DIR.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Assembling GIF with FFmpeg", job_id=job_id, output_file=output_file
        )

        # Create error context for recovery
        context = ErrorContext(
            operation="ffmpeg_gif_assembly",
            job_id=job_id,
            parameters={"output_format": "gif", "frames_dir": str(frames_dir)},
            attempt_number=1,
            timestamp=time.time(),
            duration_before_error=0,
        )

        def gif_operation():
            try:
                # First pass: Generate optimized palette
                palette_cmd = [
                    "ffmpeg",
                    "-y",
                    "-framerate",
                    str(fps),
                    "-i",
                    str(frames_dir / "frame_%06d.png"),
                    "-vf",
                    "palettegen=max_colors=256:reserve_transparent=0",
                    str(palette_file),
                ]

                subprocess.run(palette_cmd, capture_output=True, text=True, check=True)

                # Second pass: Create GIF using the generated palette
                gif_cmd = [
                    "ffmpeg",
                    "-y",
                    "-framerate",
                    str(fps),
                    "-i",
                    str(frames_dir / "frame_%06d.png"),
                    "-i",
                    str(palette_file),
                    "-lavfi",
                    "paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
                    "-loop",
                    "0",  # Infinite loop
                    str(output_file),
                ]

                subprocess.run(gif_cmd, capture_output=True, text=True, check=True)
                logger.info("GIF assembly completed", job_id=job_id)
                return True

            except subprocess.CalledProcessError as e:
                logger.error(
                    "FFmpeg GIF generation failed", job_id=job_id, error=e.stderr
                )
                raise RuntimeError(f"GIF assembly failed: {e.stderr}")

        try:
            # Execute with error recovery
            error_recovery_service.execute_retry_strategy(
                operation=gif_operation, context=context, max_retries=2, base_delay=2.0
            )

            # Clean up palette file on success
            if palette_file.exists():
                palette_file.unlink()

            # Clean up frame files
            import shutil

            shutil.rmtree(frames_dir)

            return str(output_file)

        except Exception as e:
            # Clean up on failure
            if palette_file.exists():
                palette_file.unlink()

            # Analyze error and provide recovery recommendations
            error_report = error_recovery_service.analyze_error(e, context)
            logger.error(
                "GIF assembly failed after recovery attempts",
                job_id=job_id,
                error_id=error_report.error_id,
                category=error_report.category.value,
                user_message=error_report.user_message,
            )
            raise

    def _create_png_archive(
        self, job_id: str, frames_dir: Path, effect_type: str
    ) -> str:
        """Create ZIP archive of PNG frames."""
        import zipfile

        output_file = config.OUTPUT_DIR / f"{job_id}_{effect_type}_frames.zip"

        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zipf:
            for frame_file in sorted(frames_dir.glob("*.png")):
                zipf.write(frame_file, frame_file.name)

        # Clean up frame files
        import shutil

        shutil.rmtree(frames_dir)

        logger.info("PNG archive created", job_id=job_id, output_file=output_file)
        return str(output_file)

    def _get_resolution_dimensions(self, resolution: str) -> tuple[int, int]:
        """
        Get video dimensions for the specified resolution.

        Args:
            resolution: Resolution string ('1080p', '1440p', '4k')

        Returns:
            Tuple of (width, height) in pixels
        """
        resolution_map = {
            "1080p": (1920, 1080),
            "1440p": (2560, 1440),
            "4k": (3840, 2160),
        }

        if resolution not in resolution_map:
            logger.warning(f"Unknown resolution '{resolution}', defaulting to 4K")
            return resolution_map["4k"]

        return resolution_map[resolution]

    def __del__(self):
        """Clean up Pygame resources."""
        try:
            pygame.quit()
        except Exception:
            pass
