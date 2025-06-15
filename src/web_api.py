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

from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
import structlog

from .config import config
from .video_generator import VideoGenerator, JobStatus
from .rate_limiter import rate_limit_decorator, add_rate_limit_headers, get_rate_limit_status
from .graceful_shutdown import initialize_shutdown_handler
from .resource_manager import (initialize_resource_management, shutdown_resource_management,
                              get_resource_status, queue_video_job, JobPriority)
from .metrics import metrics, track_http_request, start_metrics_updater


# Configure structured logging
logger = structlog.get_logger()

# Global job tracking
active_jobs: Dict[str, Dict[str, Any]] = {}
job_lock = threading.Lock()


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configure CORS
    CORS(app, origins=config.CORS_ORIGINS)

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
    """Generate typing code effect video."""
    try:
        data = request.get_json() or {}
        
        # Validate input
        duration = data.get("duration", 90)
        source_file = data.get("source_file", "snake_code.txt")
        output_format = data.get("output_format", "mp4")
        
        if duration < 10 or duration > 600:
            return jsonify({"error": "Duration must be between 10 and 600 seconds"}), 400
        
        if output_format not in ["mp4", "png"]:
            return jsonify({"error": "Output format must be 'mp4' or 'png'"}), 400
        
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
                "output_format": output_format
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
                    progress_callback=lambda p: update_job_progress(job_id, p)
                )
            except Exception as e:
                logger.error("Video generation failed", job_id=job_id, error=str(e))
                update_job_status(job_id, JobStatus.FAILED, error=str(e))
        
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


@app.route("/api/generate/matrix", methods=["POST"])
@rate_limit_decorator
@track_http_request
def generate_matrix_effect():
    """Generate Matrix rain effect video."""
    try:
        data = request.get_json() or {}
        
        # Validate input
        duration = data.get("duration", 15)
        loop_seamless = data.get("loop_seamless", True)
        output_format = data.get("output_format", "mp4")
        
        if duration < 5 or duration > 120:
            return jsonify({"error": "Duration must be between 5 and 120 seconds"}), 400
        
        if output_format not in ["mp4", "png"]:
            return jsonify({"error": "Output format must be 'mp4' or 'png'"}), 400
        
        # Generate job ID
        job_id = generate_job_id("matrix")
        
        # Create job entry
        job_data = {
            "job_id": job_id,
            "effect_type": "matrix",
            "status": JobStatus.QUEUED.value,
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "parameters": {
                "duration": duration,
                "loop_seamless": loop_seamless,
                "output_format": output_format
            },
            "estimated_duration": f"{duration * 1.5}s"  # Rough estimate
        }
        
        with job_lock:
            active_jobs[job_id] = job_data
        
        # Start video generation in background thread
        def generate_video():
            try:
                generator = VideoGenerator()
                generator.generate_matrix_rain(
                    job_id=job_id,
                    duration=duration,
                    loop_seamless=loop_seamless,
                    output_format=output_format,
                    progress_callback=lambda p: update_job_progress(job_id, p)
                )
            except Exception as e:
                logger.error("Video generation failed", job_id=job_id, error=str(e))
                update_job_status(job_id, JobStatus.FAILED, error=str(e))
        
        thread = threading.Thread(target=generate_video)
        thread.daemon = True
        thread.start()
        
        logger.info("Matrix effect job queued", job_id=job_id, duration=duration)
        
        return jsonify({
            "job_id": job_id,
            "status": JobStatus.QUEUED.value,
            "estimated_duration": job_data["estimated_duration"]
        }), 202
        
    except Exception as e:
        logger.error("Failed to queue matrix effect", error=str(e))
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
