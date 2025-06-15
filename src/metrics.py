"""
Prometheus metrics collection for Green-Code FX.

This module provides comprehensive metrics collection for monitoring
video generation performance, system resources, and API usage.
"""

import time
import threading
from typing import Dict, Any, Optional
from functools import wraps

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Info,
        generate_latest, CONTENT_TYPE_LATEST,
        CollectorRegistry, REGISTRY
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Define dummy types for when prometheus is not available
    CollectorRegistry = None
    REGISTRY = None

import structlog

from .config import config

logger = structlog.get_logger()


class MetricsCollector:
    """Collects and exposes Prometheus metrics for the application."""
    
    def __init__(self, registry: Optional[Any] = None):
        """Initialize metrics collector."""
        self.registry = registry or REGISTRY
        self.enabled = PROMETHEUS_AVAILABLE and config.METRICS_ENABLED
        
        if not self.enabled:
            logger.warning("Prometheus metrics disabled", 
                          prometheus_available=PROMETHEUS_AVAILABLE,
                          metrics_enabled=config.METRICS_ENABLED)
            return
        
        # Application info
        self.app_info = Info(
            'green_code_fx_info',
            'Application information',
            registry=self.registry
        )
        self.app_info.info({
            'version': config.APP_VERSION,
            'environment': config.ENVIRONMENT
        })
        
        # Video generation metrics
        self.video_generation_total = Counter(
            'green_code_fx_video_generation_total',
            'Total number of video generation requests',
            ['effect_type', 'status'],
            registry=self.registry
        )
        
        self.video_generation_duration = Histogram(
            'green_code_fx_video_generation_duration_seconds',
            'Time spent generating videos',
            ['effect_type'],
            buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1200],
            registry=self.registry
        )
        
        self.video_generation_size = Histogram(
            'green_code_fx_video_size_bytes',
            'Size of generated video files',
            ['effect_type', 'format'],
            buckets=[1e6, 5e6, 10e6, 50e6, 100e6, 500e6, 1e9],
            registry=self.registry
        )
        
        # Queue metrics
        self.queue_size = Gauge(
            'green_code_fx_queue_size',
            'Number of jobs in queue',
            registry=self.registry
        )
        
        self.active_jobs = Gauge(
            'green_code_fx_active_jobs',
            'Number of currently running jobs',
            registry=self.registry
        )
        
        self.queue_wait_time = Histogram(
            'green_code_fx_queue_wait_time_seconds',
            'Time jobs spend waiting in queue',
            buckets=[1, 5, 10, 30, 60, 300, 600],
            registry=self.registry
        )
        
        # API metrics
        self.http_requests_total = Counter(
            'green_code_fx_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'green_code_fx_http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5],
            registry=self.registry
        )
        
        # Rate limiting metrics
        self.rate_limit_hits = Counter(
            'green_code_fx_rate_limit_hits_total',
            'Number of rate limit violations',
            ['client_type'],
            registry=self.registry
        )
        
        # System resource metrics
        self.cpu_usage = Gauge(
            'green_code_fx_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'green_code_fx_memory_usage_percent',
            'Memory usage percentage',
            registry=self.registry
        )
        
        self.disk_usage = Gauge(
            'green_code_fx_disk_usage_percent',
            'Disk usage percentage',
            registry=self.registry
        )
        
        self.disk_free_bytes = Gauge(
            'green_code_fx_disk_free_bytes',
            'Free disk space in bytes',
            registry=self.registry
        )
        
        # Performance metrics
        self.frame_generation_rate = Histogram(
            'green_code_fx_frame_generation_rate_fps',
            'Frame generation rate in FPS',
            ['effect_type'],
            buckets=[10, 30, 60, 120, 240],
            registry=self.registry
        )
        
        self.performance_ratio = Histogram(
            'green_code_fx_performance_ratio',
            'Generation time vs realtime ratio',
            ['effect_type'],
            buckets=[0.5, 1, 1.5, 2, 3, 5, 10],
            registry=self.registry
        )
        
        logger.info("Prometheus metrics collector initialized")
    
    def record_video_generation(self, effect_type: str, duration: float, 
                               status: str, file_size: Optional[int] = None,
                               output_format: str = "mp4"):
        """Record video generation metrics."""
        if not self.enabled:
            return
        
        self.video_generation_total.labels(
            effect_type=effect_type,
            status=status
        ).inc()
        
        if status == "success":
            self.video_generation_duration.labels(
                effect_type=effect_type
            ).observe(duration)
            
            if file_size:
                self.video_generation_size.labels(
                    effect_type=effect_type,
                    format=output_format
                ).observe(file_size)
    
    def record_queue_metrics(self, queue_size: int, active_jobs: int):
        """Record queue metrics."""
        if not self.enabled:
            return
        
        self.queue_size.set(queue_size)
        self.active_jobs.set(active_jobs)
    
    def record_queue_wait_time(self, wait_time: float):
        """Record time a job spent waiting in queue."""
        if not self.enabled:
            return
        
        self.queue_wait_time.observe(wait_time)
    
    def record_http_request(self, method: str, endpoint: str, 
                           status_code: int, duration: float):
        """Record HTTP request metrics."""
        if not self.enabled:
            return
        
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()
        
        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_rate_limit_hit(self, client_type: str = "unknown"):
        """Record rate limit violation."""
        if not self.enabled:
            return
        
        self.rate_limit_hits.labels(client_type=client_type).inc()
    
    def update_system_metrics(self, cpu_percent: float, memory_percent: float,
                             disk_percent: float, disk_free_bytes: int):
        """Update system resource metrics."""
        if not self.enabled:
            return
        
        self.cpu_usage.set(cpu_percent)
        self.memory_usage.set(memory_percent)
        self.disk_usage.set(disk_percent)
        self.disk_free_bytes.set(disk_free_bytes)
    
    def record_performance_metrics(self, effect_type: str, 
                                  generation_time: float, video_duration: float,
                                  frame_count: int):
        """Record performance metrics."""
        if not self.enabled:
            return
        
        # Calculate performance ratio
        performance_ratio = generation_time / video_duration
        self.performance_ratio.labels(effect_type=effect_type).observe(performance_ratio)
        
        # Calculate frame generation rate
        if generation_time > 0:
            fps = frame_count / generation_time
            self.frame_generation_rate.labels(effect_type=effect_type).observe(fps)
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        if not self.enabled:
            return "# Metrics disabled\n"
        
        return generate_latest(self.registry).decode('utf-8')


# Global metrics collector instance
metrics = MetricsCollector()


def track_video_generation(effect_type: str):
    """Decorator to track video generation metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not metrics.enabled:
                return func(*args, **kwargs)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Try to get file size if result is a file path
                file_size = None
                if isinstance(result, str):
                    try:
                        from pathlib import Path
                        file_path = config.OUTPUT_DIR / result
                        if file_path.exists():
                            file_size = file_path.stat().st_size
                    except Exception:
                        pass
                
                metrics.record_video_generation(
                    effect_type=effect_type,
                    duration=duration,
                    status="success",
                    file_size=file_size
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_video_generation(
                    effect_type=effect_type,
                    duration=duration,
                    status="error"
                )
                raise
        
        return wrapper
    return decorator


def track_http_request(func):
    """Decorator to track HTTP request metrics."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not metrics.enabled:
            return func(*args, **kwargs)
        
        from flask import request, g
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Get status code from response
            status_code = 200
            if hasattr(result, 'status_code'):
                status_code = result.status_code
            elif isinstance(result, tuple) and len(result) > 1:
                status_code = result[1]
            
            metrics.record_http_request(
                method=request.method,
                endpoint=request.endpoint or "unknown",
                status_code=status_code,
                duration=duration
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_http_request(
                method=request.method,
                endpoint=request.endpoint or "unknown", 
                status_code=500,
                duration=duration
            )
            raise
    
    return wrapper


def update_system_metrics_from_resource_monitor():
    """Update system metrics from resource monitor."""
    try:
        from .resource_manager import resource_monitor
        status, system_metrics = resource_monitor.get_status()
        
        if system_metrics:
            metrics.update_system_metrics(
                cpu_percent=system_metrics.get("cpu_percent", 0),
                memory_percent=system_metrics.get("memory_percent", 0),
                disk_percent=system_metrics.get("disk_percent", 0),
                disk_free_bytes=int(system_metrics.get("disk_free_gb", 0) * 1024**3)
            )
    except Exception as e:
        logger.error("Failed to update system metrics", error=str(e))


def start_metrics_updater():
    """Start background thread to update metrics periodically."""
    if not metrics.enabled:
        return
    
    def update_loop():
        while True:
            try:
                update_system_metrics_from_resource_monitor()
                time.sleep(30)  # Update every 30 seconds
            except Exception as e:
                logger.error("Metrics update error", error=str(e))
                time.sleep(30)
    
    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()
    logger.info("Metrics updater started")
