"""
Advanced Error Recovery Service for Green-Code FX.

This module provides intelligent error categorization, automatic retry mechanisms,
fallback strategies, and comprehensive error diagnostics for robust video generation.
"""

import time
import json
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

try:
    from .config import config
except ImportError:
    # Handle direct execution
    from config import config


logger = structlog.get_logger()


class ErrorCategory(Enum):
    """Error categories for intelligent handling."""
    NETWORK = "network"
    VALIDATION = "validation"
    RESOURCE = "resource"
    SYSTEM = "system"
    FFMPEG = "ffmpeg"
    PYGAME = "pygame"
    FILE_IO = "file_io"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""
    RETRY = "retry"
    FALLBACK = "fallback"
    ABORT = "abort"
    REDUCE_QUALITY = "reduce_quality"
    ALTERNATIVE_METHOD = "alternative_method"


@dataclass
class ErrorContext:
    """Context information for error analysis."""
    operation: str
    job_id: Optional[str]
    parameters: Dict[str, Any]
    attempt_number: int
    timestamp: float
    duration_before_error: float


@dataclass
class RecoveryAction:
    """Recovery action recommendation."""
    strategy: RecoveryStrategy
    description: str
    parameters: Dict[str, Any]
    confidence: float
    estimated_success_rate: float


@dataclass
class ErrorReport:
    """Comprehensive error report."""
    error_id: str
    category: ErrorCategory
    original_error: str
    context: ErrorContext
    recovery_actions: List[RecoveryAction]
    user_message: str
    technical_details: Dict[str, Any]
    timestamp: float


class ErrorRecoveryService:
    """
    Advanced error recovery service with intelligent categorization and recovery strategies.
    """
    
    def __init__(self):
        """Initialize the error recovery service."""
        self.error_patterns = self._load_error_patterns()
        self.recovery_strategies = self._load_recovery_strategies()
        self.error_history: List[ErrorReport] = []
        self.max_history_size = 100
        
        logger.info("Error recovery service initialized")
    
    def _load_error_patterns(self) -> Dict[ErrorCategory, List[str]]:
        """Load error patterns for categorization."""
        return {
            ErrorCategory.NETWORK: [
                "connection", "timeout", "network", "unreachable", "dns", "socket"
            ],
            ErrorCategory.VALIDATION: [
                "invalid", "validation", "format", "parameter", "missing", "required"
            ],
            ErrorCategory.RESOURCE: [
                "memory", "disk", "space", "resource", "limit", "quota", "permission"
            ],
            ErrorCategory.SYSTEM: [
                "system", "os", "platform", "environment", "path", "directory"
            ],
            ErrorCategory.FFMPEG: [
                "ffmpeg", "codec", "format", "encoding", "video", "audio", "stream"
            ],
            ErrorCategory.PYGAME: [
                "pygame", "display", "surface", "font", "render", "sdl"
            ],
            ErrorCategory.FILE_IO: [
                "file", "read", "write", "open", "close", "exists", "io"
            ],
            ErrorCategory.TIMEOUT: [
                "timeout", "expired", "deadline", "time", "duration"
            ]
        }
    
    def _load_recovery_strategies(self) -> Dict[ErrorCategory, List[RecoveryAction]]:
        """Load recovery strategies for each error category."""
        return {
            ErrorCategory.NETWORK: [
                RecoveryAction(
                    strategy=RecoveryStrategy.RETRY,
                    description="Retry with exponential backoff",
                    parameters={"max_retries": 3, "base_delay": 2.0},
                    confidence=0.8,
                    estimated_success_rate=0.7
                )
            ],
            ErrorCategory.VALIDATION: [
                RecoveryAction(
                    strategy=RecoveryStrategy.ABORT,
                    description="Fix validation errors and retry",
                    parameters={},
                    confidence=0.9,
                    estimated_success_rate=0.0
                )
            ],
            ErrorCategory.RESOURCE: [
                RecoveryAction(
                    strategy=RecoveryStrategy.REDUCE_QUALITY,
                    description="Reduce output quality to save resources",
                    parameters={"quality_reduction": 0.8},
                    confidence=0.7,
                    estimated_success_rate=0.6
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.RETRY,
                    description="Wait and retry when resources are available",
                    parameters={"max_retries": 2, "base_delay": 10.0},
                    confidence=0.6,
                    estimated_success_rate=0.5
                )
            ],
            ErrorCategory.FFMPEG: [
                RecoveryAction(
                    strategy=RecoveryStrategy.ALTERNATIVE_METHOD,
                    description="Try alternative FFmpeg parameters",
                    parameters={"use_fallback_codec": True},
                    confidence=0.8,
                    estimated_success_rate=0.7
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.REDUCE_QUALITY,
                    description="Reduce video quality settings",
                    parameters={"crf_increase": 5, "preset_faster": True},
                    confidence=0.9,
                    estimated_success_rate=0.8
                )
            ],
            ErrorCategory.PYGAME: [
                RecoveryAction(
                    strategy=RecoveryStrategy.ALTERNATIVE_METHOD,
                    description="Try alternative rendering method",
                    parameters={"use_software_rendering": True},
                    confidence=0.7,
                    estimated_success_rate=0.6
                )
            ],
            ErrorCategory.FILE_IO: [
                RecoveryAction(
                    strategy=RecoveryStrategy.RETRY,
                    description="Retry file operation",
                    parameters={"max_retries": 3, "base_delay": 1.0},
                    confidence=0.8,
                    estimated_success_rate=0.7
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.ALTERNATIVE_METHOD,
                    description="Use alternative file path",
                    parameters={"use_temp_directory": True},
                    confidence=0.6,
                    estimated_success_rate=0.5
                )
            ],
            ErrorCategory.TIMEOUT: [
                RecoveryAction(
                    strategy=RecoveryStrategy.RETRY,
                    description="Retry with increased timeout",
                    parameters={"timeout_multiplier": 2.0, "max_retries": 2},
                    confidence=0.7,
                    estimated_success_rate=0.6
                )
            ],
            ErrorCategory.UNKNOWN: [
                RecoveryAction(
                    strategy=RecoveryStrategy.RETRY,
                    description="Generic retry with backoff",
                    parameters={"max_retries": 2, "base_delay": 5.0},
                    confidence=0.4,
                    estimated_success_rate=0.3
                )
            ]
        }
    
    def categorize_error(self, error: Exception, context: ErrorContext) -> ErrorCategory:
        """Categorize an error based on its message and context."""
        error_message = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Check error patterns
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern in error_message or pattern in error_type:
                    return category
        
        # Context-based categorization
        if "ffmpeg" in context.operation.lower():
            return ErrorCategory.FFMPEG
        elif "pygame" in context.operation.lower() or "render" in context.operation.lower():
            return ErrorCategory.PYGAME
        elif "file" in context.operation.lower() or "save" in context.operation.lower():
            return ErrorCategory.FILE_IO
        
        return ErrorCategory.UNKNOWN
    
    def analyze_error(self, error: Exception, context: ErrorContext) -> ErrorReport:
        """Analyze an error and generate a comprehensive recovery report."""
        error_id = f"err_{int(time.time())}_{context.job_id or 'unknown'}"
        category = self.categorize_error(error, context)
        
        # Get recovery actions for this category
        recovery_actions = self.recovery_strategies.get(category, [])
        
        # Adjust recovery actions based on attempt number
        adjusted_actions = self._adjust_recovery_actions(recovery_actions, context.attempt_number)
        
        # Generate user-friendly message
        user_message = self._generate_user_message(error, category, context)
        
        # Collect technical details
        technical_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "operation": context.operation,
            "attempt_number": context.attempt_number,
            "duration_before_error": context.duration_before_error
        }
        
        report = ErrorReport(
            error_id=error_id,
            category=category,
            original_error=str(error),
            context=context,
            recovery_actions=adjusted_actions,
            user_message=user_message,
            technical_details=technical_details,
            timestamp=time.time()
        )
        
        # Store in history
        self._store_error_report(report)
        
        logger.error("Error analyzed and categorized",
                    error_id=error_id,
                    category=category.value,
                    operation=context.operation,
                    recovery_actions=len(adjusted_actions))
        
        return report

    def _adjust_recovery_actions(self, actions: List[RecoveryAction], attempt_number: int) -> List[RecoveryAction]:
        """Adjust recovery actions based on attempt number and history."""
        adjusted_actions = []

        for action in actions:
            # Reduce confidence and success rate for repeated attempts
            confidence_penalty = 0.1 * (attempt_number - 1)
            success_penalty = 0.15 * (attempt_number - 1)

            adjusted_action = RecoveryAction(
                strategy=action.strategy,
                description=action.description,
                parameters=action.parameters.copy(),
                confidence=max(0.1, action.confidence - confidence_penalty),
                estimated_success_rate=max(0.1, action.estimated_success_rate - success_penalty)
            )

            # Adjust parameters for retries
            if action.strategy == RecoveryStrategy.RETRY:
                adjusted_action.parameters["max_retries"] = max(1,
                    action.parameters.get("max_retries", 3) - attempt_number + 1)
                adjusted_action.parameters["base_delay"] = (
                    action.parameters.get("base_delay", 1.0) * (1.5 ** (attempt_number - 1))
                )

            adjusted_actions.append(adjusted_action)

        # Sort by confidence and success rate
        adjusted_actions.sort(key=lambda a: a.confidence * a.estimated_success_rate, reverse=True)

        return adjusted_actions

    def _generate_user_message(self, error: Exception, category: ErrorCategory, context: ErrorContext) -> str:
        """Generate a user-friendly error message."""
        base_messages = {
            ErrorCategory.NETWORK: "Network connection issue. Please check your internet connection and try again.",
            ErrorCategory.VALIDATION: "Invalid input detected. Please check your settings and try again.",
            ErrorCategory.RESOURCE: "System resources are currently limited. Try reducing video quality or duration.",
            ErrorCategory.SYSTEM: "System configuration issue detected. Please contact support if this persists.",
            ErrorCategory.FFMPEG: "Video processing error occurred. Trying alternative encoding methods.",
            ErrorCategory.PYGAME: "Graphics rendering issue detected. Attempting alternative rendering method.",
            ErrorCategory.FILE_IO: "File operation failed. Checking file permissions and disk space.",
            ErrorCategory.TIMEOUT: "Operation timed out. Retrying with extended timeout.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Our system will attempt automatic recovery."
        }

        base_message = base_messages.get(category, base_messages[ErrorCategory.UNKNOWN])

        # Add attempt-specific information
        if context.attempt_number > 1:
            base_message += f" (Attempt {context.attempt_number})"

        return base_message

    def _store_error_report(self, report: ErrorReport) -> None:
        """Store error report in history."""
        self.error_history.append(report)

        # Maintain history size limit
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]

    def get_recovery_recommendation(self, error_id: str) -> Optional[RecoveryAction]:
        """Get the best recovery recommendation for a specific error."""
        for report in self.error_history:
            if report.error_id == error_id:
                if report.recovery_actions:
                    return report.recovery_actions[0]  # Return highest confidence action
                break
        return None

    def execute_retry_strategy(self, operation: Callable, context: ErrorContext,
                              max_retries: int = 3, base_delay: float = 1.0) -> Any:
        """Execute an operation with intelligent retry strategy."""
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                # Update context for this attempt
                context.attempt_number = attempt
                context.timestamp = time.time()

                # Execute the operation
                result = operation()

                # Log successful recovery if this wasn't the first attempt
                if attempt > 1:
                    logger.info("Operation succeeded after retry",
                               operation=context.operation,
                               attempt=attempt,
                               job_id=context.job_id)

                return result

            except Exception as error:
                last_error = error

                # Analyze the error
                error_report = self.analyze_error(error, context)

                # Check if we should continue retrying
                if attempt == max_retries:
                    logger.error("Operation failed after all retries",
                                operation=context.operation,
                                attempts=attempt,
                                job_id=context.job_id,
                                final_error=str(error))
                    break

                # Calculate delay with exponential backoff and jitter
                delay = base_delay * (2 ** (attempt - 1))
                jitter = delay * 0.1 * (0.5 - time.time() % 1)  # Add some randomness
                total_delay = delay + jitter

                logger.warning("Operation failed, retrying",
                              operation=context.operation,
                              attempt=attempt,
                              next_attempt_in=total_delay,
                              error=str(error))

                # Wait before retrying
                time.sleep(total_delay)

        # All retries failed
        raise last_error

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and insights."""
        if not self.error_history:
            return {"total_errors": 0, "message": "No error data available"}

        # Calculate statistics
        total_errors = len(self.error_history)
        category_counts = {}
        operation_counts = {}
        recent_errors = []

        cutoff_time = time.time() - (24 * 3600)  # Last 24 hours

        for report in self.error_history:
            # Category statistics
            category = report.category.value
            category_counts[category] = category_counts.get(category, 0) + 1

            # Operation statistics
            operation = report.context.operation
            operation_counts[operation] = operation_counts.get(operation, 0) + 1

            # Recent errors
            if report.timestamp > cutoff_time:
                recent_errors.append({
                    "error_id": report.error_id,
                    "category": category,
                    "operation": operation,
                    "timestamp": report.timestamp,
                    "user_message": report.user_message
                })

        return {
            "total_errors": total_errors,
            "recent_errors_24h": len(recent_errors),
            "category_breakdown": category_counts,
            "operation_breakdown": operation_counts,
            "recent_errors": recent_errors[-10:],  # Last 10 recent errors
            "most_common_category": max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None,
            "most_problematic_operation": max(operation_counts.items(), key=lambda x: x[1])[0] if operation_counts else None
        }


# Global error recovery service instance
error_recovery_service = ErrorRecoveryService()
