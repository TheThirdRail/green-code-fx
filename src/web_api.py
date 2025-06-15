"""
Flask web API for Green-Code FX video effects generator.

This module provides a RESTful API for triggering video generation jobs,
monitoring their progress, and downloading completed videos.
"""

import os
import uuid
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify, send_file, abort, render_template
from flask_cors import CORS
import structlog

try:
    from .config import config
    from .video_generator import VideoGenerator, JobStatus
    from .rate_limiter import rate_limit_decorator, add_rate_limit_headers, get_rate_limit_status
    from .graceful_shutdown import initialize_shutdown_handler
    from .resource_manager import (initialize_resource_management, shutdown_resource_management,
                                  get_resource_status, queue_video_job, JobPriority)
    from .metrics import metrics, track_http_request, start_metrics_updater
except ImportError:
    # Handle direct execution
    from config import config
    from video_generator import VideoGenerator, JobStatus
    from rate_limiter import rate_limit_decorator, add_rate_limit_headers, get_rate_limit_status
    from graceful_shutdown import initialize_shutdown_handler
    from resource_manager import (initialize_resource_management, shutdown_resource_management,
                                  get_resource_status, queue_video_job, JobPriority)
    from metrics import metrics, track_http_request, start_metrics_updater


# Configure structured logging
logger = structlog.get_logger()

# Global job tracking
active_jobs: Dict[str, Dict[str, Any]] = {}
job_lock = threading.Lock()


def create_app() -> Flask:
    """Create and configure the Flask application."""
    # Configure Flask with template and static directories
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # Configure CORS - add localhost for frontend access
    cors_origins = config.CORS_ORIGINS + ["http://localhost:8082"]
    CORS(app, origins=cors_origins)

    # Configure logging
    if config.DEBUG:
        app.logger.setLevel("DEBUG")

    # Add rate limit headers to all responses
    @app.after_request
    def after_request(response):
        return add_rate_limit_headers(response)

    return app


app = create_app()


# ============================================================================
# Utility Functions
# ============================================================================

def generate_job_id(effect_type: str) -> str:
    """Generate a unique job ID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{effect_type}_{timestamp}_{unique_id}"


def cleanup_old_jobs() -> None:
    """Clean up old completed jobs and temporary files."""
    cutoff_time = datetime.now() - timedelta(hours=config.CLEANUP_TEMP_FILES_HOURS)
    
    with job_lock:
        jobs_to_remove = []
        for job_id, job_data in active_jobs.items():
            if job_data.get("completed_at"):
                completed_at = datetime.fromisoformat(job_data["completed_at"])
                if completed_at < cutoff_time:
                    jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del active_jobs[job_id]
            logger.info("Cleaned up old job", job_id=job_id)


def get_disk_space() -> str:
    """Get available disk space in the output directory."""
    try:
        import shutil
        total, used, free = shutil.disk_usage(config.OUTPUT_DIR)
        free_gb = free // (1024**3)
        return f"{free_gb}GB available"
    except Exception:
        return "Unknown"


# ============================================================================
# Frontend UI Routes
# ============================================================================

@app.route("/", methods=["GET"])
def index():
    """Main UI route for the typing effect generator."""
    try:
        return render_template('index.html', version=config.APP_VERSION)
    except Exception as e:
        logger.error("Failed to render index template", error=str(e))
        return jsonify({"error": "Failed to load UI"}), 500


# ============================================================================
# API Routes
# ============================================================================

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    try:
        # Count active jobs
        with job_lock:
            active_count = sum(1 for job in active_jobs.values()
                             if job.get("status") == JobStatus.RUNNING.value)
            queue_count = sum(1 for job in active_jobs.values()
                            if job.get("status") == JobStatus.QUEUED.value)

        return jsonify({
            "status": "healthy",
            "version": config.APP_VERSION,
            "active_jobs": active_count,
            "queue_length": queue_count,
            "disk_space": get_disk_space(),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route("/api/rate-limit", methods=["GET"])
def rate_limit_status():
    """Get current rate limit status for the requesting client."""
    try:
        status = get_rate_limit_status()
        return jsonify(status)
    except Exception as e:
        logger.error("Rate limit status check failed", error=str(e))
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/resources", methods=["GET"])
def resource_status():
    """Get current system resource status and queue information."""
    try:
        status = get_resource_status()
        return jsonify(status)
    except Exception as e:
        logger.error("Resource status check failed", error=str(e))
        return jsonify({"error": "Internal server error"}), 500


@app.route("/metrics", methods=["GET"])
def prometheus_metrics():
    """Prometheus metrics endpoint."""
    try:
        from .metrics import CONTENT_TYPE_LATEST
        metrics_data = metrics.get_metrics()
        return metrics_data, 200, {'Content-Type': CONTENT_TYPE_LATEST}
    except Exception as e:
        logger.error("Metrics endpoint failed", error=str(e))
        return "# Metrics unavailable\n", 500, {'Content-Type': 'text/plain'}


@app.route("/api/generate/typing", methods=["POST"])
@rate_limit_decorator
@track_http_request
def generate_typing_effect():
    """Generate typing code effect video with customization options."""
    try:
        # Handle both JSON and form data (for file uploads)
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            # Convert string values to appropriate types
            if 'duration' in data:
                data['duration'] = int(data['duration'])
            if 'font_size' in data:
                data['font_size'] = int(data['font_size'])
        else:
            data = request.get_json() or {}

        # Validate basic parameters
        duration = data.get("duration", 90)
        source_file = data.get("source_file", "snake_code.txt")
        output_format = data.get("output_format", "mp4")

        # Validate new customization parameters
        font_family = data.get("font_family", "jetbrains")
        font_size = data.get("font_size", config.TYPING_FONT_SIZE)
        text_color = data.get("text_color", "#00FF00")  # Default green
        custom_text = data.get("custom_text", None)

        # Basic validation
        if duration < 10 or duration > 600:
            return jsonify({"error": "Duration must be between 10 and 600 seconds"}), 400

        if output_format not in ["mp4", "png"]:
            return jsonify({"error": "Output format must be 'mp4' or 'png'"}), 400

        # Validate font size
        if not (config.TYPING_FONT_SIZE_MIN <= font_size <= config.TYPING_FONT_SIZE_MAX):
            return jsonify({
                "error": f"Font size must be between {config.TYPING_FONT_SIZE_MIN} and {config.TYPING_FONT_SIZE_MAX}"
            }), 400

        # Validate font family
        available_fonts = config.get_available_fonts()
        if font_family not in available_fonts:
            return jsonify({
                "error": f"Invalid font family. Available fonts: {list(available_fonts.keys())}"
            }), 400

        # Validate color format
        if not config.validate_hex_color(text_color):
            return jsonify({
                "error": "Invalid color format. Use hex format #RRGGBB (e.g., #00FF00)"
            }), 400

        # Handle file upload for custom text
        uploaded_file_path = None
        if 'text_file' in request.files:
            file = request.files['text_file']
            if file.filename != '':
                # Validate file
                if not _validate_text_file(file):
                    return jsonify({
                        "error": "Invalid file. Only .txt files up to 10MB are allowed."
                    }), 400

                # Save uploaded file temporarily
                uploaded_file_path = _save_uploaded_file(file)

        # Validate text input - either custom_text or file upload, not both
        if custom_text and uploaded_file_path:
            return jsonify({
                "error": "Cannot specify both custom_text and text_file. Choose one."
            }), 400

        # Validate custom text length if provided
        if custom_text and len(custom_text) > 50000:  # 50KB text limit
            return jsonify({
                "error": "Custom text too long. Maximum 50,000 characters allowed."
            }), 400

        # Generate job ID
        job_id = generate_job_id("typing")
        
        # Create job entry
        job_data = {
            "job_id": job_id,
            "effect_type": "typing",
            "status": JobStatus.QUEUED.value,
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "parameters": {
                "duration": duration,
                "source_file": source_file,
                "output_format": output_format,
                "font_family": font_family,
                "font_size": font_size,
                "text_color": text_color,
                "custom_text": custom_text,
                "uploaded_file_path": uploaded_file_path
            },
            "estimated_duration": f"{duration * 2}s"  # Rough estimate
        }
        
        with job_lock:
            active_jobs[job_id] = job_data
        
        # Start video generation in background thread
        def generate_video():
            try:
                generator = VideoGenerator()
                generator.generate_typing_effect(
                    job_id=job_id,
                    duration=duration,
                    source_file=source_file,
                    output_format=output_format,
                    font_family=font_family,
                    font_size=font_size,
                    text_color=text_color,
                    custom_text=custom_text,
                    uploaded_file_path=uploaded_file_path,
                    progress_callback=lambda p: update_job_progress(job_id, p)
                )
            except Exception as e:
                logger.error("Video generation failed", job_id=job_id, error=str(e))
                update_job_status(job_id, JobStatus.FAILED, error=str(e))
            finally:
                # Clean up uploaded file if it exists
                if uploaded_file_path and Path(uploaded_file_path).exists():
                    try:
                        Path(uploaded_file_path).unlink()
                        logger.info("Cleaned up uploaded file", file_path=uploaded_file_path)
                    except Exception as e:
                        logger.warning("Failed to clean up uploaded file",
                                     file_path=uploaded_file_path, error=str(e))
        
        thread = threading.Thread(target=generate_video)
        thread.daemon = True
        thread.start()
        
        logger.info("Typing effect job queued", job_id=job_id, duration=duration)
        
        return jsonify({
            "job_id": job_id,
            "status": JobStatus.QUEUED.value,
            "estimated_duration": job_data["estimated_duration"]
        }), 202
        
    except Exception as e:
        logger.error("Failed to queue typing effect", error=str(e))
        return jsonify({"error": "Internal server error"}), 500



@app.route("/api/jobs/<job_id>", methods=["GET"])
def get_job_status(job_id: str):
    """Get status of a specific job."""
    with job_lock:
        job_data = active_jobs.get(job_id)
    
    if not job_data:
        return jsonify({"error": "Job not found"}), 404
    
    # Add download URL if completed
    if job_data.get("status") == JobStatus.COMPLETED.value and job_data.get("output_file"):
        output_file = Path(job_data["output_file"]).name
        job_data["download_url"] = f"/api/download/{output_file}"
        
        # Add file size if available
        try:
            file_path = config.OUTPUT_DIR / output_file
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                job_data["file_size"] = f"{size_mb:.1f}MB"
        except Exception:
            pass
    
    return jsonify(job_data)


@app.route("/api/download/<filename>", methods=["GET"])
def download_file(filename: str):
    """Download a generated video file."""
    try:
        file_path = config.OUTPUT_DIR / filename
        
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        # Security check: ensure file is in output directory
        if not str(file_path.resolve()).startswith(str(config.OUTPUT_DIR.resolve())):
            return jsonify({"error": "Access denied"}), 403
        
        # Check file size limit
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > config.MAX_DOWNLOAD_SIZE_MB:
            return jsonify({"error": "File too large"}), 413
        
        # Determine MIME type
        mime_type = "video/mp4" if filename.endswith(".mp4") else "application/octet-stream"
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mime_type
        )
        
    except Exception as e:
        logger.error("Download failed", filename=filename, error=str(e))
        return jsonify({"error": "Download failed"}), 500


# ============================================================================
# Helper Functions
# ============================================================================

def update_job_progress(job_id: str, progress: int) -> None:
    """Update job progress."""
    with job_lock:
        if job_id in active_jobs:
            active_jobs[job_id]["progress"] = progress
            active_jobs[job_id]["updated_at"] = datetime.now().isoformat()


def update_job_status(job_id: str, status: JobStatus, **kwargs) -> None:
    """Update job status and additional fields."""
    with job_lock:
        if job_id in active_jobs:
            active_jobs[job_id]["status"] = status.value
            active_jobs[job_id]["updated_at"] = datetime.now().isoformat()
            
            if status == JobStatus.COMPLETED:
                active_jobs[job_id]["completed_at"] = datetime.now().isoformat()
                active_jobs[job_id]["progress"] = 100
            elif status == JobStatus.FAILED:
                active_jobs[job_id]["error"] = kwargs.get("error", "Unknown error")
            
            # Add any additional fields
            for key, value in kwargs.items():
                if key != "error":  # Already handled above
                    active_jobs[job_id][key] = value


# ============================================================================
# File Upload Helper Functions
# ============================================================================

def _validate_text_file(file) -> bool:
    """Validate uploaded text file."""
    import os
    from werkzeug.utils import secure_filename

    # Check if file has a filename
    if not file.filename:
        return False

    # Secure the filename
    filename = secure_filename(file.filename)
    if not filename:
        return False

    # Check file extension
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in config.ALLOWED_TEXT_EXTENSIONS:
        return False

    # Check file size (read content to check size)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning

    max_size_bytes = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        return False

    return True


def _save_uploaded_file(file) -> str:
    """Save uploaded file to temporary location and return path."""
    import os
    import tempfile
    from werkzeug.utils import secure_filename

    # Create secure filename
    filename = secure_filename(file.filename)

    # Create temporary file
    temp_dir = config.TEMP_DIR
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique temporary filename
    temp_fd, temp_path = tempfile.mkstemp(
        suffix=f"_{filename}",
        prefix="upload_",
        dir=str(temp_dir)
    )

    try:
        # Save file content
        with os.fdopen(temp_fd, 'wb') as temp_file:
            file.save(temp_file)

        logger.info("Uploaded file saved",
                   original_filename=filename,
                   temp_path=temp_path)

        return temp_path
    except Exception as e:
        # Clean up on error
        try:
            os.close(temp_fd)
            os.unlink(temp_path)
        except:
            pass
        raise e


# ============================================================================
# Preview Generation API Endpoints
# ============================================================================

@app.route("/api/preview", methods=["POST"])
@rate_limit_decorator
@track_http_request
def generate_preview():
    """Generate a text preview for the typing effect."""
    try:
        # Handle both JSON and form data
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            if 'font_size' in data:
                data['font_size'] = int(data['font_size'])
        else:
            data = request.get_json() or {}

        # Get parameters
        font_family = data.get("font_family", "jetbrains")
        font_size = data.get("font_size", config.TYPING_FONT_SIZE)
        text_color = data.get("text_color", "#00FF00")
        custom_text = data.get("custom_text", None)
        text_input_method = data.get("textInputMethod", "default")

        # Validate parameters
        if not config.validate_hex_color(text_color):
            return jsonify({
                "error": "Invalid color format. Use hex format #RRGGBB (e.g., #00FF00)"
            }), 400

        available_fonts = config.get_available_fonts()
        if font_family not in available_fonts:
            return jsonify({
                "error": f"Invalid font family. Available fonts: {list(available_fonts.keys())}"
            }), 400

        # Get preview text based on input method
        preview_text = ""
        if text_input_method == "custom" and custom_text:
            # Limit preview text length
            preview_text = custom_text[:1000]
        elif text_input_method == "file" and 'text_file' in request.files:
            file = request.files['text_file']
            if file.filename != '':
                if not _validate_text_file(file):
                    return jsonify({
                        "error": "Invalid file. Only .txt files up to 10MB are allowed."
                    }), 400

                # Read file content for preview
                try:
                    file_content = file.read().decode('utf-8')
                    preview_text = file_content[:1000]  # Limit preview
                    file.seek(0)  # Reset file pointer
                except UnicodeDecodeError:
                    return jsonify({
                        "error": "File must be valid UTF-8 text"
                    }), 400
        else:
            # Default snake game code
            preview_text = """// Default Snake Game Code
class Snake {
    constructor() {
        this.body = [{x: 10, y: 10}];
        this.direction = {x: 0, y: 0};
        this.score = 0;
    }

    update() {
        const head = {
            x: this.body[0].x + this.direction.x,
            y: this.body[0].y + this.direction.y
        };
        this.body.unshift(head);

        if (!this.hasEatenFood()) {
            this.body.pop();
        }
    }

    hasEatenFood() {
        return this.body[0].x === food.x && this.body[0].y === food.y;
    }

    draw(ctx) {
        ctx.fillStyle = '#00FF00';
        this.body.forEach(segment => {
            ctx.fillRect(segment.x * 20, segment.y * 20, 20, 20);
        });
    }
}"""

        return jsonify({
            "preview_text": preview_text,
            "font_family": font_family,
            "font_size": font_size,
            "text_color": text_color,
            "character_count": len(preview_text),
            "line_count": len(preview_text.split('\n'))
        }), 200

    except Exception as e:
        logger.error("Failed to generate preview", error=str(e))
        return jsonify({"error": "Failed to generate preview"}), 500


# ============================================================================
# Font Discovery API Endpoints
# ============================================================================

@app.route("/api/fonts", methods=["GET"])
@track_http_request
def list_available_fonts():
    """List all available fonts for typing effect."""
    try:
        fonts_dict = config.get_available_fonts()

        # Convert to format expected by frontend
        fonts_list = []
        for font_id, font_info in fonts_dict.items():
            fonts_list.append({
                "id": font_id,
                "name": font_info["name"],
                "type": font_info["type"]
            })

        return jsonify({
            "fonts": fonts_list,
            "default": "jetbrains"
        }), 200
    except Exception as e:
        logger.error("Failed to list fonts", error=str(e))
        return jsonify({"error": "Failed to retrieve font list"}), 500


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    # Set up SDL for headless operation
    os.environ["SDL_VIDEODRIVER"] = config.SDL_VIDEODRIVER

    # Validate configuration
    config.validate_config()

    # Initialize resource management
    initialize_resource_management()

    # Initialize metrics collection
    start_metrics_updater()

    # Initialize graceful shutdown handler
    shutdown_handler = initialize_shutdown_handler(active_jobs, job_lock)
    shutdown_handler.register_shutdown_callback(shutdown_resource_management)

    # Load any previously saved job state
    saved_jobs = shutdown_handler.load_job_state()
    if saved_jobs:
        with job_lock:
            active_jobs.update(saved_jobs)
        logger.info("Restored job state", recovered_jobs=len(saved_jobs))

    # Start cleanup thread
    cleanup_thread = threading.Thread(target=lambda: None)  # Placeholder for periodic cleanup
    cleanup_thread.daemon = True
    cleanup_thread.start()

    logger.info(
        "Starting Green-Code FX API server",
        host=config.API_HOST,
        port=config.API_PORT,
        environment=config.ENVIRONMENT
    )

    # Run the Flask application
    app.run(
        host=config.API_HOST,
        port=config.API_PORT,
        debug=config.DEBUG,
        threaded=True
    )
