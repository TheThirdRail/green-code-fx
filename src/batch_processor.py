"""
Green-Code FX Batch Processing System
Handles batch video generation with queue management and progress tracking
"""

import json
import time
import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

try:
    from .config import config
    from .video_generator import VideoGenerator, JobStatus
    from .resource_manager import JobPriority, queue_video_job
    from .progress_estimator import progress_estimator
    import structlog
except ImportError:
    from config import config
    from video_generator import VideoGenerator, JobStatus
    from resource_manager import JobPriority, queue_video_job
    from progress_estimator import progress_estimator
    import structlog

logger = structlog.get_logger()


class BatchStatus(Enum):
    """Batch processing status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class BatchItemStatus(Enum):
    """Individual batch item status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class BatchItem:
    """Individual item in a batch."""
    item_id: str
    name: str
    effect_type: str
    parameters: Dict[str, Any]
    priority: JobPriority = JobPriority.NORMAL
    status: BatchItemStatus = BatchItemStatus.PENDING
    job_id: Optional[str] = None
    progress: int = 0
    error_message: Optional[str] = None
    output_file: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_duration: Optional[float] = None


@dataclass
class BatchJob:
    """Batch processing job container."""
    batch_id: str
    name: str
    description: str
    items: List[BatchItem]
    status: BatchStatus = BatchStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: int = 0
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    estimated_total_duration: Optional[float] = None
    actual_duration: Optional[float] = None
    auto_retry_failed: bool = True
    max_retries: int = 3
    concurrent_limit: int = 2


class BatchProcessor:
    """Manages batch video generation jobs."""
    
    def __init__(self):
        """Initialize batch processor."""
        self.active_batches: Dict[str, BatchJob] = {}
        self.batch_lock = threading.Lock()
        self.video_generator = VideoGenerator()
        self.processing_threads: Dict[str, threading.Thread] = {}
        
        # Load existing batches from storage
        self._load_batches()
        
        logger.info("Batch processor initialized")
    
    def create_batch(self, name: str, description: str, items: List[Dict[str, Any]], 
                    priority: JobPriority = JobPriority.NORMAL,
                    auto_retry_failed: bool = True, max_retries: int = 3,
                    concurrent_limit: int = 2) -> str:
        """
        Create a new batch processing job.
        
        Args:
            name: Batch name
            description: Batch description
            items: List of batch items with parameters
            priority: Batch priority level
            auto_retry_failed: Whether to automatically retry failed items
            max_retries: Maximum retry attempts per item
            concurrent_limit: Maximum concurrent items to process
            
        Returns:
            Batch ID
        """
        batch_id = f"batch_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Create batch items
        batch_items = []
        total_estimated_duration = 0
        
        for i, item_data in enumerate(items):
            item_id = f"{batch_id}_item_{i:03d}"
            
            # Estimate duration for this item
            estimated_duration = progress_estimator.estimate_generation_time(
                item_id, item_data.get("effect_type", "typing"), item_data.get("parameters", {})
            ).estimated_seconds
            
            batch_item = BatchItem(
                item_id=item_id,
                name=item_data.get("name", f"Item {i+1}"),
                effect_type=item_data.get("effect_type", "typing"),
                parameters=item_data.get("parameters", {}),
                priority=JobPriority(item_data.get("priority", priority.value)),
                created_at=datetime.now().isoformat(),
                estimated_duration=estimated_duration
            )
            
            batch_items.append(batch_item)
            total_estimated_duration += estimated_duration
        
        # Create batch job
        batch_job = BatchJob(
            batch_id=batch_id,
            name=name,
            description=description,
            items=batch_items,
            priority=priority,
            created_at=datetime.now().isoformat(),
            total_items=len(batch_items),
            estimated_total_duration=total_estimated_duration,
            auto_retry_failed=auto_retry_failed,
            max_retries=max_retries,
            concurrent_limit=concurrent_limit
        )
        
        with self.batch_lock:
            self.active_batches[batch_id] = batch_job
        
        # Save to storage
        self._save_batch(batch_job)
        
        logger.info("Batch created", batch_id=batch_id, name=name, 
                   total_items=len(batch_items), estimated_duration=total_estimated_duration)
        
        return batch_id
    
    def start_batch(self, batch_id: str) -> bool:
        """
        Start processing a batch.
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            True if batch started successfully
        """
        with self.batch_lock:
            batch_job = self.active_batches.get(batch_id)
            if not batch_job:
                logger.error("Batch not found", batch_id=batch_id)
                return False
            
            if batch_job.status != BatchStatus.PENDING:
                logger.warning("Batch not in pending status", batch_id=batch_id, 
                             status=batch_job.status.value)
                return False
            
            batch_job.status = BatchStatus.RUNNING
            batch_job.started_at = datetime.now().isoformat()
        
        # Start processing thread
        thread = threading.Thread(target=self._process_batch, args=(batch_id,), daemon=True)
        self.processing_threads[batch_id] = thread
        thread.start()
        
        logger.info("Batch processing started", batch_id=batch_id)
        return True
    
    def pause_batch(self, batch_id: str) -> bool:
        """Pause batch processing."""
        with self.batch_lock:
            batch_job = self.active_batches.get(batch_id)
            if batch_job and batch_job.status == BatchStatus.RUNNING:
                batch_job.status = BatchStatus.PAUSED
                logger.info("Batch paused", batch_id=batch_id)
                return True
        return False
    
    def resume_batch(self, batch_id: str) -> bool:
        """Resume paused batch processing."""
        with self.batch_lock:
            batch_job = self.active_batches.get(batch_id)
            if batch_job and batch_job.status == BatchStatus.PAUSED:
                batch_job.status = BatchStatus.RUNNING
                logger.info("Batch resumed", batch_id=batch_id)
                return True
        return False
    
    def cancel_batch(self, batch_id: str) -> bool:
        """Cancel batch processing."""
        with self.batch_lock:
            batch_job = self.active_batches.get(batch_id)
            if batch_job and batch_job.status in [BatchStatus.RUNNING, BatchStatus.PAUSED]:
                batch_job.status = BatchStatus.CANCELLED
                batch_job.completed_at = datetime.now().isoformat()
                logger.info("Batch cancelled", batch_id=batch_id)
                return True
        return False
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch status and progress."""
        with self.batch_lock:
            batch_job = self.active_batches.get(batch_id)
            if not batch_job:
                return None
            
            # Calculate progress
            if batch_job.total_items > 0:
                batch_job.progress = int((batch_job.completed_items / batch_job.total_items) * 100)
            
            return {
                "batch_id": batch_job.batch_id,
                "name": batch_job.name,
                "description": batch_job.description,
                "status": batch_job.status.value,
                "priority": batch_job.priority.value,
                "progress": batch_job.progress,
                "total_items": batch_job.total_items,
                "completed_items": batch_job.completed_items,
                "failed_items": batch_job.failed_items,
                "created_at": batch_job.created_at,
                "started_at": batch_job.started_at,
                "completed_at": batch_job.completed_at,
                "estimated_total_duration": batch_job.estimated_total_duration,
                "actual_duration": batch_job.actual_duration,
                "items": [self._item_to_dict(item) for item in batch_job.items]
            }
    
    def list_batches(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all batches with optional status filter."""
        with self.batch_lock:
            batches = []
            for batch_job in self.active_batches.values():
                if status_filter and batch_job.status.value != status_filter:
                    continue
                
                batch_summary = {
                    "batch_id": batch_job.batch_id,
                    "name": batch_job.name,
                    "description": batch_job.description,
                    "status": batch_job.status.value,
                    "priority": batch_job.priority.value,
                    "progress": batch_job.progress,
                    "total_items": batch_job.total_items,
                    "completed_items": batch_job.completed_items,
                    "failed_items": batch_job.failed_items,
                    "created_at": batch_job.created_at,
                    "estimated_total_duration": batch_job.estimated_total_duration
                }
                batches.append(batch_summary)
            
            return sorted(batches, key=lambda x: x["created_at"], reverse=True)
    
    def delete_batch(self, batch_id: str) -> bool:
        """Delete a batch (only if completed, failed, or cancelled)."""
        with self.batch_lock:
            batch_job = self.active_batches.get(batch_id)
            if not batch_job:
                return False
            
            if batch_job.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED]:
                del self.active_batches[batch_id]
                self._delete_batch_storage(batch_id)
                logger.info("Batch deleted", batch_id=batch_id)
                return True
            
        return False

    def _process_batch(self, batch_id: str):
        """Process all items in a batch."""
        try:
            with self.batch_lock:
                batch_job = self.active_batches.get(batch_id)
                if not batch_job:
                    return

            start_time = time.time()
            running_items = {}  # Track currently running items

            logger.info("Starting batch processing", batch_id=batch_id,
                       total_items=batch_job.total_items)

            while True:
                with self.batch_lock:
                    batch_job = self.active_batches.get(batch_id)
                    if not batch_job or batch_job.status in [BatchStatus.CANCELLED, BatchStatus.COMPLETED]:
                        break

                    # Check if we can start new items
                    if (batch_job.status == BatchStatus.RUNNING and
                        len(running_items) < batch_job.concurrent_limit):

                        # Find next pending item
                        next_item = None
                        for item in batch_job.items:
                            if item.status == BatchItemStatus.PENDING:
                                next_item = item
                                break

                        if next_item:
                            # Start processing this item
                            next_item.status = BatchItemStatus.QUEUED
                            next_item.started_at = datetime.now().isoformat()

                            # Queue the job
                            job_id = f"{batch_id}_{next_item.item_id}"
                            next_item.job_id = job_id

                            # Create progress callback
                            def create_progress_callback(item_id):
                                def progress_callback(progress):
                                    self._update_item_progress(batch_id, item_id, progress)
                                return progress_callback

                            # Create completion callback
                            def create_completion_callback(item_id):
                                def completion_callback(success, output_file=None, error=None):
                                    self._handle_item_completion(batch_id, item_id, success, output_file, error)
                                    if item_id in running_items:
                                        del running_items[item_id]
                                return completion_callback

                            # For now, simulate job processing (will integrate with actual video generation)
                            next_item.status = BatchItemStatus.RUNNING
                            running_items[next_item.item_id] = next_item

                            # Start a thread to simulate processing
                            def process_item():
                                try:
                                    # Simulate processing time
                                    duration = next_item.estimated_duration or 30
                                    for i in range(101):
                                        if batch_job.status == BatchStatus.CANCELLED:
                                            break
                                        time.sleep(duration / 100)
                                        self._update_item_progress(batch_id, next_item.item_id, i)

                                    # Simulate completion
                                    if batch_job.status != BatchStatus.CANCELLED:
                                        output_file = f"{next_item.item_id}_output.mp4"
                                        self._handle_item_completion(batch_id, next_item.item_id, True, output_file)

                                except Exception as e:
                                    self._handle_item_completion(batch_id, next_item.item_id, False, None, str(e))
                                finally:
                                    if next_item.item_id in running_items:
                                        del running_items[next_item.item_id]

                            thread = threading.Thread(target=process_item, daemon=True)
                            thread.start()

                            logger.info("Batch item started", batch_id=batch_id,
                                      item_id=next_item.item_id)

                # Check if all items are processed
                with self.batch_lock:
                    batch_job = self.active_batches.get(batch_id)
                    if batch_job:
                        pending_count = sum(1 for item in batch_job.items
                                          if item.status in [BatchItemStatus.PENDING, BatchItemStatus.QUEUED, BatchItemStatus.RUNNING])

                        if pending_count == 0:
                            # All items processed
                            batch_job.status = BatchStatus.COMPLETED
                            batch_job.completed_at = datetime.now().isoformat()
                            batch_job.actual_duration = time.time() - start_time

                            logger.info("Batch processing completed", batch_id=batch_id,
                                      completed_items=batch_job.completed_items,
                                      failed_items=batch_job.failed_items,
                                      duration=batch_job.actual_duration)
                            break

                # Sleep before next iteration
                time.sleep(1)

        except Exception as e:
            logger.error("Batch processing error", batch_id=batch_id, error=str(e))
            with self.batch_lock:
                batch_job = self.active_batches.get(batch_id)
                if batch_job:
                    batch_job.status = BatchStatus.FAILED
                    batch_job.completed_at = datetime.now().isoformat()

        finally:
            # Clean up processing thread reference
            if batch_id in self.processing_threads:
                del self.processing_threads[batch_id]

    def _update_item_progress(self, batch_id: str, item_id: str, progress: int):
        """Update progress for a specific batch item."""
        with self.batch_lock:
            batch_job = self.active_batches.get(batch_id)
            if batch_job:
                for item in batch_job.items:
                    if item.item_id == item_id:
                        item.progress = progress
                        break

    def _handle_item_completion(self, batch_id: str, item_id: str, success: bool,
                               output_file: Optional[str] = None, error: Optional[str] = None):
        """Handle completion of a batch item."""
        with self.batch_lock:
            batch_job = self.active_batches.get(batch_id)
            if not batch_job:
                return

            for item in batch_job.items:
                if item.item_id == item_id:
                    if success:
                        item.status = BatchItemStatus.COMPLETED
                        item.progress = 100
                        item.output_file = output_file
                        item.completed_at = datetime.now().isoformat()
                        batch_job.completed_items += 1
                        logger.info("Batch item completed", batch_id=batch_id,
                                  item_id=item_id, output_file=output_file)
                    else:
                        item.status = BatchItemStatus.FAILED
                        item.error_message = error
                        item.completed_at = datetime.now().isoformat()
                        batch_job.failed_items += 1
                        logger.warning("Batch item failed", batch_id=batch_id,
                                     item_id=item_id, error=error)
                    break

    def _item_to_dict(self, item: BatchItem) -> Dict[str, Any]:
        """Convert BatchItem to dictionary."""
        return {
            "item_id": item.item_id,
            "name": item.name,
            "effect_type": item.effect_type,
            "status": item.status.value,
            "priority": item.priority.value,
            "progress": item.progress,
            "job_id": item.job_id,
            "error_message": item.error_message,
            "output_file": item.output_file,
            "created_at": item.created_at,
            "started_at": item.started_at,
            "completed_at": item.completed_at,
            "estimated_duration": item.estimated_duration
        }

    def _save_batch(self, batch_job: BatchJob):
        """Save batch to persistent storage."""
        try:
            batch_dir = config.OUTPUT_DIR / "batches"
            batch_dir.mkdir(exist_ok=True)

            batch_file = batch_dir / f"{batch_job.batch_id}.json"
            with open(batch_file, 'w') as f:
                json.dump(asdict(batch_job), f, indent=2, default=str)

        except Exception as e:
            logger.error("Failed to save batch", batch_id=batch_job.batch_id, error=str(e))

    def _load_batches(self):
        """Load existing batches from storage."""
        try:
            batch_dir = config.OUTPUT_DIR / "batches"
            if not batch_dir.exists():
                return

            for batch_file in batch_dir.glob("*.json"):
                try:
                    with open(batch_file, 'r') as f:
                        batch_data = json.load(f)

                    # Convert back to BatchJob object
                    batch_job = self._dict_to_batch_job(batch_data)
                    self.active_batches[batch_job.batch_id] = batch_job

                except Exception as e:
                    logger.error("Failed to load batch", file=str(batch_file), error=str(e))

        except Exception as e:
            logger.error("Failed to load batches", error=str(e))

    def _dict_to_batch_job(self, data: Dict[str, Any]) -> BatchJob:
        """Convert dictionary to BatchJob object."""
        items = []
        for item_data in data.get("items", []):
            item = BatchItem(
                item_id=item_data["item_id"],
                name=item_data["name"],
                effect_type=item_data["effect_type"],
                parameters=item_data["parameters"],
                priority=JobPriority(item_data.get("priority", "normal")),
                status=BatchItemStatus(item_data.get("status", "pending")),
                job_id=item_data.get("job_id"),
                progress=item_data.get("progress", 0),
                error_message=item_data.get("error_message"),
                output_file=item_data.get("output_file"),
                created_at=item_data.get("created_at"),
                started_at=item_data.get("started_at"),
                completed_at=item_data.get("completed_at"),
                estimated_duration=item_data.get("estimated_duration")
            )
            items.append(item)

        return BatchJob(
            batch_id=data["batch_id"],
            name=data["name"],
            description=data["description"],
            items=items,
            status=BatchStatus(data.get("status", "pending")),
            priority=JobPriority(data.get("priority", "normal")),
            created_at=data.get("created_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            progress=data.get("progress", 0),
            total_items=data.get("total_items", 0),
            completed_items=data.get("completed_items", 0),
            failed_items=data.get("failed_items", 0),
            estimated_total_duration=data.get("estimated_total_duration"),
            actual_duration=data.get("actual_duration"),
            auto_retry_failed=data.get("auto_retry_failed", True),
            max_retries=data.get("max_retries", 3),
            concurrent_limit=data.get("concurrent_limit", 2)
        )

    def _delete_batch_storage(self, batch_id: str):
        """Delete batch from persistent storage."""
        try:
            batch_dir = config.OUTPUT_DIR / "batches"
            batch_file = batch_dir / f"{batch_id}.json"
            if batch_file.exists():
                batch_file.unlink()
        except Exception as e:
            logger.error("Failed to delete batch storage", batch_id=batch_id, error=str(e))


# Global batch processor instance
batch_processor = BatchProcessor()
