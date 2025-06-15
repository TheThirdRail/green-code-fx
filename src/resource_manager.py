"""
Resource monitoring and queue management for Green-Code FX.

This module provides system resource monitoring, job queue management,
and graceful degradation under resource pressure.
"""

import os
import psutil
import time
import threading
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from queue import PriorityQueue

import structlog

from .config import config

logger = structlog.get_logger()


class JobPriority(Enum):
    """Job priority levels."""
    LOW = 3
    NORMAL = 2
    HIGH = 1


class ResourceStatus(Enum):
    """System resource status levels."""
    HEALTHY = "healthy"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QueuedJob:
    """Represents a queued job with priority."""
    priority: JobPriority
    timestamp: float
    job_id: str
    effect_type: str
    parameters: Dict
    callback: callable
    
    def __lt__(self, other):
        """Priority queue comparison (lower number = higher priority)."""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.timestamp < other.timestamp


class ResourceMonitor:
    """Monitors system resources and determines pressure levels."""
    
    def __init__(self, check_interval: int = 10):
        """
        Initialize resource monitor.
        
        Args:
            check_interval: Seconds between resource checks
        """
        self.check_interval = check_interval
        self.current_status = ResourceStatus.HEALTHY
        self.metrics = {}
        self.running = False
        self.monitor_thread = None
        
        # Resource thresholds
        self.thresholds = {
            "cpu_moderate": 70.0,
            "cpu_high": 85.0,
            "cpu_critical": 95.0,
            "memory_moderate": 70.0,
            "memory_high": 85.0,
            "memory_critical": 95.0,
            "disk_moderate": 80.0,
            "disk_high": 90.0,
            "disk_critical": 95.0
        }
    
    def start_monitoring(self):
        """Start resource monitoring in background thread."""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                self._update_metrics()
                self._update_status()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error("Resource monitoring error", error=str(e))
                time.sleep(self.check_interval)
    
    def _update_metrics(self):
        """Update current resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage for output directory
            disk = psutil.disk_usage(str(config.OUTPUT_DIR))
            disk_percent = (disk.used / disk.total) * 100
            
            # Load average (Unix-like systems)
            load_avg = None
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()[0]  # 1-minute load average
            
            self.metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk_percent,
                "disk_free_gb": disk.free / (1024**3),
                "load_average": load_avg,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error("Failed to update metrics", error=str(e))
    
    def _update_status(self):
        """Update resource status based on current metrics."""
        if not self.metrics:
            return
        
        cpu = self.metrics.get("cpu_percent", 0)
        memory = self.metrics.get("memory_percent", 0)
        disk = self.metrics.get("disk_percent", 0)
        
        # Determine overall status (worst case)
        status = ResourceStatus.HEALTHY
        
        # Check CPU
        if cpu >= self.thresholds["cpu_critical"]:
            status = ResourceStatus.CRITICAL
        elif cpu >= self.thresholds["cpu_high"]:
            status = max(status, ResourceStatus.HIGH, key=lambda x: x.value)
        elif cpu >= self.thresholds["cpu_moderate"]:
            status = max(status, ResourceStatus.MODERATE, key=lambda x: x.value)
        
        # Check Memory
        if memory >= self.thresholds["memory_critical"]:
            status = ResourceStatus.CRITICAL
        elif memory >= self.thresholds["memory_high"]:
            status = max(status, ResourceStatus.HIGH, key=lambda x: x.value)
        elif memory >= self.thresholds["memory_moderate"]:
            status = max(status, ResourceStatus.MODERATE, key=lambda x: x.value)
        
        # Check Disk
        if disk >= self.thresholds["disk_critical"]:
            status = ResourceStatus.CRITICAL
        elif disk >= self.thresholds["disk_high"]:
            status = max(status, ResourceStatus.HIGH, key=lambda x: x.value)
        elif disk >= self.thresholds["disk_moderate"]:
            status = max(status, ResourceStatus.MODERATE, key=lambda x: x.value)
        
        # Log status changes
        if status != self.current_status:
            logger.info("Resource status changed", 
                       old_status=self.current_status.value,
                       new_status=status.value,
                       cpu=cpu, memory=memory, disk=disk)
        
        self.current_status = status
    
    def get_status(self) -> Tuple[ResourceStatus, Dict]:
        """Get current resource status and metrics."""
        return self.current_status, self.metrics.copy()


class JobQueueManager:
    """Manages job queue with priority and resource-aware scheduling."""
    
    def __init__(self, resource_monitor: ResourceMonitor):
        """Initialize job queue manager."""
        self.resource_monitor = resource_monitor
        self.job_queue = PriorityQueue()
        self.running_jobs = {}
        self.max_concurrent_jobs = config.MAX_CONCURRENT_JOBS
        self.queue_lock = threading.Lock()
        self.processor_thread = None
        self.running = False
    
    def start_processing(self):
        """Start job queue processing."""
        if self.running:
            return
        
        self.running = True
        self.processor_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.processor_thread.start()
        logger.info("Job queue processing started")
    
    def stop_processing(self):
        """Stop job queue processing."""
        self.running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
        logger.info("Job queue processing stopped")
    
    def queue_job(self, job_id: str, effect_type: str, parameters: Dict, 
                  callback: callable, priority: JobPriority = JobPriority.NORMAL) -> bool:
        """
        Queue a job for processing.
        
        Returns:
            True if job was queued, False if rejected due to resource pressure
        """
        status, metrics = self.resource_monitor.get_status()
        
        # Reject new jobs under critical resource pressure
        if status == ResourceStatus.CRITICAL:
            logger.warning("Job rejected due to critical resource pressure", 
                          job_id=job_id, status=status.value)
            return False
        
        # Adjust priority based on resource pressure
        if status == ResourceStatus.HIGH and priority == JobPriority.LOW:
            logger.info("Low priority job rejected due to high resource pressure", 
                       job_id=job_id)
            return False
        
        queued_job = QueuedJob(
            priority=priority,
            timestamp=time.time(),
            job_id=job_id,
            effect_type=effect_type,
            parameters=parameters,
            callback=callback
        )
        
        self.job_queue.put(queued_job)
        logger.info("Job queued", job_id=job_id, priority=priority.name, 
                   queue_size=self.job_queue.qsize())
        return True
    
    def _process_queue(self):
        """Process jobs from the queue."""
        while self.running:
            try:
                # Check if we can start new jobs
                if len(self.running_jobs) >= self._get_max_concurrent():
                    time.sleep(1)
                    continue
                
                # Get next job (blocks for up to 1 second)
                try:
                    job = self.job_queue.get(timeout=1)
                except:
                    continue  # Timeout, check again
                
                # Start job processing
                self._start_job(job)
                
            except Exception as e:
                logger.error("Job queue processing error", error=str(e))
                time.sleep(1)
    
    def _get_max_concurrent(self) -> int:
        """Get maximum concurrent jobs based on resource pressure."""
        status, _ = self.resource_monitor.get_status()
        
        if status == ResourceStatus.CRITICAL:
            return 0  # No new jobs
        elif status == ResourceStatus.HIGH:
            return max(1, self.max_concurrent_jobs // 2)
        elif status == ResourceStatus.MODERATE:
            return max(1, int(self.max_concurrent_jobs * 0.75))
        else:
            return self.max_concurrent_jobs
    
    def _start_job(self, job: QueuedJob):
        """Start processing a job."""
        with self.queue_lock:
            self.running_jobs[job.job_id] = job
        
        def job_wrapper():
            try:
                logger.info("Starting job", job_id=job.job_id, effect_type=job.effect_type)
                job.callback()
            except Exception as e:
                logger.error("Job execution failed", job_id=job.job_id, error=str(e))
            finally:
                with self.queue_lock:
                    self.running_jobs.pop(job.job_id, None)
                logger.info("Job completed", job_id=job.job_id)
        
        thread = threading.Thread(target=job_wrapper, daemon=True)
        thread.start()
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics."""
        with self.queue_lock:
            return {
                "queue_size": self.job_queue.qsize(),
                "running_jobs": len(self.running_jobs),
                "max_concurrent": self._get_max_concurrent(),
                "running_job_ids": list(self.running_jobs.keys())
            }


# Global instances
resource_monitor = ResourceMonitor()
job_queue_manager = JobQueueManager(resource_monitor)


def initialize_resource_management():
    """Initialize resource monitoring and queue management."""
    resource_monitor.start_monitoring()
    job_queue_manager.start_processing()
    logger.info("Resource management initialized")


def shutdown_resource_management():
    """Shutdown resource monitoring and queue management."""
    job_queue_manager.stop_processing()
    resource_monitor.stop_monitoring()
    logger.info("Resource management shutdown")


def get_resource_status() -> Dict:
    """Get current resource status and queue statistics."""
    status, metrics = resource_monitor.get_status()
    queue_stats = job_queue_manager.get_queue_stats()

    return {
        "resource_status": status.value,
        "metrics": metrics,
        "queue": queue_stats
    }


def queue_video_job(job_id: str, effect_type: str, parameters: Dict,
                   callback: callable, priority: JobPriority = JobPriority.NORMAL) -> bool:
    """Queue a video generation job with resource-aware scheduling."""
    return job_queue_manager.queue_job(job_id, effect_type, parameters, callback, priority)
