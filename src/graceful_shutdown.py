"""
Graceful shutdown handling for Green-Code FX API server.

This module provides signal handling and job state persistence to ensure
running video generation jobs can complete before container shutdown.
"""

import os
import signal
import time
import json
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Callable

import structlog

from .config import config

logger = structlog.get_logger()


class GracefulShutdownHandler:
    """Handles graceful shutdown of the application with job completion."""
    
    def __init__(self, 
                 job_tracker: Dict[str, Dict[str, Any]], 
                 job_lock: threading.Lock,
                 max_shutdown_wait: int = 300):
        """
        Initialize graceful shutdown handler.
        
        Args:
            job_tracker: Reference to active jobs dictionary
            job_lock: Lock for job tracker access
            max_shutdown_wait: Maximum seconds to wait for jobs to complete
        """
        self.job_tracker = job_tracker
        self.job_lock = job_lock
        self.max_shutdown_wait = max_shutdown_wait
        self.shutdown_requested = False
        self.shutdown_callbacks: list = []
        
        # Job state persistence
        self.state_file = config.OUTPUT_DIR / "job_state.json"
        
        # Register signal handlers
        self._register_signal_handlers()
        
        logger.info("Graceful shutdown handler initialized", 
                   max_wait=max_shutdown_wait)
    
    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown."""
        # Handle SIGTERM (Docker stop)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Handle SIGINT (Ctrl+C)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # On Windows, also handle SIGBREAK
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        logger.info("Shutdown signal received", signal=signal_name)
        
        if not self.shutdown_requested:
            self.shutdown_requested = True
            # Start shutdown in separate thread to avoid blocking signal handler
            shutdown_thread = threading.Thread(target=self._perform_shutdown)
            shutdown_thread.daemon = True
            shutdown_thread.start()
    
    def _perform_shutdown(self):
        """Perform graceful shutdown sequence."""
        logger.info("Starting graceful shutdown sequence")
        
        try:
            # 1. Stop accepting new jobs (this would be handled by Flask)
            logger.info("Stopping acceptance of new jobs")
            
            # 2. Save current job state
            self._save_job_state()
            
            # 3. Wait for running jobs to complete
            self._wait_for_jobs_completion()
            
            # 4. Execute shutdown callbacks
            self._execute_shutdown_callbacks()
            
            # 5. Final cleanup
            self._final_cleanup()
            
            logger.info("Graceful shutdown completed successfully")
            
        except Exception as e:
            logger.error("Error during graceful shutdown", error=str(e))
        finally:
            # Force exit if we reach here
            os._exit(0)
    
    def _save_job_state(self):
        """Save current job state to disk for recovery."""
        try:
            with self.job_lock:
                # Create a serializable copy of job state
                job_state = {}
                for job_id, job_data in self.job_tracker.items():
                    # Only save jobs that are not completed or failed
                    if job_data.get("status") in ["queued", "running"]:
                        job_state[job_id] = {
                            "job_id": job_data.get("job_id"),
                            "effect_type": job_data.get("effect_type"),
                            "status": job_data.get("status"),
                            "progress": job_data.get("progress", 0),
                            "created_at": job_data.get("created_at"),
                            "parameters": job_data.get("parameters", {}),
                            "estimated_duration": job_data.get("estimated_duration")
                        }
                
                # Save to file
                with open(self.state_file, 'w') as f:
                    json.dump({
                        "timestamp": time.time(),
                        "jobs": job_state
                    }, f, indent=2)
                
                logger.info("Job state saved", 
                           active_jobs=len(job_state),
                           state_file=str(self.state_file))
                
        except Exception as e:
            logger.error("Failed to save job state", error=str(e))
    
    def _wait_for_jobs_completion(self):
        """Wait for running jobs to complete."""
        start_time = time.time()
        
        while time.time() - start_time < self.max_shutdown_wait:
            with self.job_lock:
                running_jobs = [
                    job_id for job_id, job_data in self.job_tracker.items()
                    if job_data.get("status") == "running"
                ]
            
            if not running_jobs:
                logger.info("All jobs completed, proceeding with shutdown")
                break
            
            logger.info("Waiting for jobs to complete", 
                       running_jobs=len(running_jobs),
                       job_ids=running_jobs[:3])  # Log first 3 job IDs
            
            time.sleep(2)  # Check every 2 seconds
        
        else:
            # Timeout reached
            with self.job_lock:
                remaining_jobs = [
                    job_id for job_id, job_data in self.job_tracker.items()
                    if job_data.get("status") == "running"
                ]
            
            logger.warning("Shutdown timeout reached, forcing shutdown", 
                          remaining_jobs=len(remaining_jobs),
                          timeout=self.max_shutdown_wait)
    
    def _execute_shutdown_callbacks(self):
        """Execute registered shutdown callbacks."""
        for callback in self.shutdown_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error("Shutdown callback failed", error=str(e))
    
    def _final_cleanup(self):
        """Perform final cleanup operations."""
        try:
            # Clean up temporary files older than 1 hour
            temp_dir = config.TEMP_DIR
            if temp_dir.exists():
                current_time = time.time()
                for item in temp_dir.iterdir():
                    try:
                        if item.is_file():
                            age = current_time - item.stat().st_mtime
                            if age > 3600:  # 1 hour
                                item.unlink()
                        elif item.is_dir():
                            # Remove empty directories
                            try:
                                item.rmdir()
                            except OSError:
                                pass  # Directory not empty
                    except Exception:
                        pass  # Ignore individual file errors
            
            logger.info("Final cleanup completed")
            
        except Exception as e:
            logger.error("Final cleanup failed", error=str(e))
    
    def register_shutdown_callback(self, callback: Callable[[], None]):
        """Register a callback to be executed during shutdown."""
        self.shutdown_callbacks.append(callback)
        logger.debug("Shutdown callback registered")
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self.shutdown_requested
    
    def load_job_state(self) -> Optional[Dict[str, Any]]:
        """Load previously saved job state."""
        try:
            if not self.state_file.exists():
                return None
            
            with open(self.state_file, 'r') as f:
                state_data = json.load(f)
            
            # Check if state is recent (within last hour)
            state_age = time.time() - state_data.get("timestamp", 0)
            if state_age > 3600:  # 1 hour
                logger.info("Job state file too old, ignoring", age_hours=state_age/3600)
                return None
            
            jobs = state_data.get("jobs", {})
            logger.info("Job state loaded", 
                       recovered_jobs=len(jobs),
                       state_age_minutes=state_age/60)
            
            return jobs
            
        except Exception as e:
            logger.error("Failed to load job state", error=str(e))
            return None
    
    def clear_job_state(self):
        """Clear saved job state file."""
        try:
            if self.state_file.exists():
                self.state_file.unlink()
                logger.info("Job state file cleared")
        except Exception as e:
            logger.error("Failed to clear job state", error=str(e))


# Global shutdown handler instance (will be initialized in web_api.py)
shutdown_handler: Optional[GracefulShutdownHandler] = None


def initialize_shutdown_handler(job_tracker: Dict[str, Dict[str, Any]], 
                               job_lock: threading.Lock) -> GracefulShutdownHandler:
    """Initialize the global shutdown handler."""
    global shutdown_handler
    shutdown_handler = GracefulShutdownHandler(job_tracker, job_lock)
    return shutdown_handler


def get_shutdown_handler() -> Optional[GracefulShutdownHandler]:
    """Get the global shutdown handler instance."""
    return shutdown_handler
