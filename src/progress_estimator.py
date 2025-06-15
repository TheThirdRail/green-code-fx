"""
Intelligent Progress Estimation Service for Green-Code FX.

This module provides smart time estimation for video generation based on historical data,
text characteristics, and generation parameters. It tracks generation metrics and uses
machine learning-inspired algorithms to provide accurate completion time estimates.
"""

import json
import time
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib
import structlog

try:
    from .config import config
except ImportError:
    # Handle direct execution
    from config import config


logger = structlog.get_logger()


@dataclass
class GenerationMetrics:
    """Data class for storing generation metrics."""
    job_id: str
    effect_type: str
    text_length: int
    line_count: int
    duration_seconds: int
    font_size: int
    typing_speed: int
    output_format: str
    generation_time: float
    frame_count: int
    file_size_bytes: int
    timestamp: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class EstimationResult:
    """Data class for estimation results."""
    estimated_seconds: float
    confidence_level: float
    based_on_samples: int
    factors_considered: List[str]
    fallback_used: bool = False


class ProgressEstimator:
    """
    Intelligent progress estimation service.
    
    This service tracks historical generation data and provides smart time estimates
    for new video generation requests based on similar past generations.
    """
    
    def __init__(self):
        """Initialize the progress estimator."""
        self.data_file = config.OUTPUT_DIR / "generation_metrics.json"
        self.max_history_days = 30  # Keep 30 days of history
        self.min_samples_for_estimation = 3  # Minimum samples needed for reliable estimation
        self.metrics_cache: List[GenerationMetrics] = []
        self.cache_loaded = False
        
        # Ensure data directory exists
        config.ensure_directories()
        
        logger.info("Progress estimator initialized", 
                   data_file=str(self.data_file),
                   max_history_days=self.max_history_days)
    
    def _load_historical_data(self) -> None:
        """Load historical generation data from disk."""
        if self.cache_loaded:
            return
        
        try:
            if not self.data_file.exists():
                self.metrics_cache = []
                self.cache_loaded = True
                return
            
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            # Convert JSON data back to GenerationMetrics objects
            self.metrics_cache = []
            for item in data.get("metrics", []):
                try:
                    metrics = GenerationMetrics(**item)
                    # Only keep recent data
                    if self._is_recent_data(metrics.timestamp):
                        self.metrics_cache.append(metrics)
                except (TypeError, ValueError) as e:
                    logger.warning("Skipping invalid metrics entry", error=str(e), entry=item)
            
            self.cache_loaded = True
            logger.info("Historical data loaded", 
                       total_metrics=len(self.metrics_cache),
                       data_file=str(self.data_file))
            
        except Exception as e:
            logger.error("Failed to load historical data", error=str(e))
            self.metrics_cache = []
            self.cache_loaded = True
    
    def _is_recent_data(self, timestamp: float) -> bool:
        """Check if data is within the retention period."""
        cutoff_time = time.time() - (self.max_history_days * 24 * 3600)
        return timestamp > cutoff_time
    
    def _save_historical_data(self) -> None:
        """Save historical generation data to disk."""
        try:
            # Filter out old data before saving
            recent_metrics = [m for m in self.metrics_cache if self._is_recent_data(m.timestamp)]
            self.metrics_cache = recent_metrics
            
            data = {
                "version": "1.0",
                "last_updated": time.time(),
                "metrics": [asdict(m) for m in self.metrics_cache]
            }
            
            # Write to temporary file first, then rename for atomic operation
            temp_file = self.data_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            temp_file.rename(self.data_file)
            
            logger.debug("Historical data saved", 
                        metrics_count=len(self.metrics_cache),
                        data_file=str(self.data_file))
            
        except Exception as e:
            logger.error("Failed to save historical data", error=str(e))
    
    def record_generation(self, job_id: str, effect_type: str, parameters: Dict[str, Any], 
                         generation_time: float, frame_count: int, file_size_bytes: int,
                         success: bool, error_message: Optional[str] = None) -> None:
        """
        Record a completed generation for future estimation.
        
        Args:
            job_id: Unique job identifier
            effect_type: Type of effect (typing, matrix)
            parameters: Generation parameters
            generation_time: Total generation time in seconds
            frame_count: Number of frames generated
            file_size_bytes: Output file size in bytes
            success: Whether generation was successful
            error_message: Error message if generation failed
        """
        self._load_historical_data()
        
        try:
            # Extract relevant parameters for estimation
            text_length = len(parameters.get("custom_text", "")) or self._estimate_text_length(parameters)
            line_count = text_length // 80 if text_length > 0 else 50  # Rough estimate
            
            metrics = GenerationMetrics(
                job_id=job_id,
                effect_type=effect_type,
                text_length=text_length,
                line_count=line_count,
                duration_seconds=parameters.get("duration", 90),
                font_size=parameters.get("font_size", 32),
                typing_speed=parameters.get("typing_speed", 150),
                output_format=parameters.get("output_format", "mp4"),
                generation_time=generation_time,
                frame_count=frame_count,
                file_size_bytes=file_size_bytes,
                timestamp=time.time(),
                success=success,
                error_message=error_message
            )
            
            self.metrics_cache.append(metrics)
            self._save_historical_data()
            
            logger.info("Generation metrics recorded", 
                       job_id=job_id,
                       generation_time=generation_time,
                       success=success)
            
        except Exception as e:
            logger.error("Failed to record generation metrics", 
                        job_id=job_id, error=str(e))
    
    def _estimate_text_length(self, parameters: Dict[str, Any]) -> int:
        """Estimate text length from parameters when custom text is not provided."""
        source_file = parameters.get("source_file", "snake_code.txt")
        
        # Default estimates for known source files
        default_lengths = {
            "snake_code.txt": 2500,
            "default": 2000
        }
        
        return default_lengths.get(source_file, default_lengths["default"])

    def estimate_generation_time(self, effect_type: str, parameters: Dict[str, Any]) -> EstimationResult:
        """
        Estimate generation time for a new video generation request.

        Args:
            effect_type: Type of effect (typing, matrix)
            parameters: Generation parameters

        Returns:
            EstimationResult with time estimate and confidence metrics
        """
        self._load_historical_data()

        try:
            # Extract parameters for comparison
            text_length = len(parameters.get("custom_text", "")) or self._estimate_text_length(parameters)
            duration = parameters.get("duration", 90)
            font_size = parameters.get("font_size", 32)
            typing_speed = parameters.get("typing_speed", 150)
            output_format = parameters.get("output_format", "mp4")

            # Find similar historical generations
            similar_generations = self._find_similar_generations(
                effect_type, text_length, duration, font_size, typing_speed, output_format
            )

            if len(similar_generations) >= self.min_samples_for_estimation:
                # Use historical data for estimation
                return self._calculate_smart_estimate(similar_generations, parameters)
            else:
                # Use fallback estimation
                return self._calculate_fallback_estimate(effect_type, parameters)

        except Exception as e:
            logger.error("Failed to estimate generation time", error=str(e))
            return self._calculate_fallback_estimate(effect_type, parameters)

    def _find_similar_generations(self, effect_type: str, text_length: int, duration: int,
                                 font_size: int, typing_speed: int, output_format: str) -> List[GenerationMetrics]:
        """Find historically similar generations for estimation."""
        similar = []

        for metrics in self.metrics_cache:
            if not metrics.success or metrics.effect_type != effect_type:
                continue

            # Calculate similarity score based on multiple factors
            similarity_score = self._calculate_similarity_score(
                metrics, text_length, duration, font_size, typing_speed, output_format
            )

            # Include generations with similarity score > 0.7
            if similarity_score > 0.7:
                similar.append(metrics)

        # Sort by similarity (most similar first)
        similar.sort(key=lambda m: self._calculate_similarity_score(
            m, text_length, duration, font_size, typing_speed, output_format
        ), reverse=True)

        return similar[:10]  # Use top 10 most similar

    def _calculate_similarity_score(self, metrics: GenerationMetrics, text_length: int,
                                   duration: int, font_size: int, typing_speed: int,
                                   output_format: str) -> float:
        """Calculate similarity score between current request and historical data."""
        score = 0.0

        # Text length similarity (30% weight)
        if text_length > 0 and metrics.text_length > 0:
            length_ratio = min(text_length, metrics.text_length) / max(text_length, metrics.text_length)
            score += 0.3 * length_ratio

        # Duration similarity (25% weight)
        duration_ratio = min(duration, metrics.duration_seconds) / max(duration, metrics.duration_seconds)
        score += 0.25 * duration_ratio

        # Font size similarity (15% weight)
        font_ratio = min(font_size, metrics.font_size) / max(font_size, metrics.font_size)
        score += 0.15 * font_ratio

        # Typing speed similarity (15% weight)
        speed_ratio = min(typing_speed, metrics.typing_speed) / max(typing_speed, metrics.typing_speed)
        score += 0.15 * speed_ratio

        # Output format match (15% weight)
        if output_format == metrics.output_format:
            score += 0.15

        return score

    def _calculate_smart_estimate(self, similar_generations: List[GenerationMetrics],
                                 parameters: Dict[str, Any]) -> EstimationResult:
        """Calculate smart estimate based on similar historical generations."""
        generation_times = [m.generation_time for m in similar_generations]

        # Use weighted average based on recency and similarity
        weights = []
        for i, metrics in enumerate(similar_generations):
            # More recent data gets higher weight
            recency_weight = 1.0 - (time.time() - metrics.timestamp) / (self.max_history_days * 24 * 3600)
            recency_weight = max(0.1, recency_weight)  # Minimum weight of 0.1

            # More similar data gets higher weight
            similarity_weight = self._calculate_similarity_score(
                metrics,
                len(parameters.get("custom_text", "")) or self._estimate_text_length(parameters),
                parameters.get("duration", 90),
                parameters.get("font_size", 32),
                parameters.get("typing_speed", 150),
                parameters.get("output_format", "mp4")
            )

            weights.append(recency_weight * similarity_weight)

        # Calculate weighted average
        weighted_sum = sum(time * weight for time, weight in zip(generation_times, weights))
        total_weight = sum(weights)
        estimated_time = weighted_sum / total_weight if total_weight > 0 else statistics.mean(generation_times)

        # Calculate confidence based on data consistency and sample size
        std_dev = statistics.stdev(generation_times) if len(generation_times) > 1 else 0
        mean_time = statistics.mean(generation_times)
        coefficient_of_variation = std_dev / mean_time if mean_time > 0 else 1

        # Higher confidence for more consistent data and larger sample sizes
        consistency_factor = max(0.1, 1.0 - coefficient_of_variation)
        sample_size_factor = min(1.0, len(similar_generations) / 10)  # Max confidence at 10+ samples
        confidence = consistency_factor * sample_size_factor

        factors_considered = [
            "historical_data",
            "text_length",
            "duration",
            "font_size",
            "typing_speed",
            "output_format",
            "recency_weighting"
        ]

        return EstimationResult(
            estimated_seconds=estimated_time,
            confidence_level=confidence,
            based_on_samples=len(similar_generations),
            factors_considered=factors_considered,
            fallback_used=False
        )

    def _calculate_fallback_estimate(self, effect_type: str, parameters: Dict[str, Any]) -> EstimationResult:
        """Calculate fallback estimate when insufficient historical data is available."""
        duration = parameters.get("duration", 90)
        text_length = len(parameters.get("custom_text", "")) or self._estimate_text_length(parameters)
        output_format = parameters.get("output_format", "mp4")

        # Base estimation formula
        if effect_type == "typing":
            # Typing effect: roughly 1.5-2x realtime for MP4, 2-3x for GIF
            base_multiplier = 2.0 if output_format == "gif" else 1.5

            # Adjust for text length (longer text = more processing)
            text_factor = 1.0 + (text_length / 10000) * 0.5  # +50% for every 10k characters

            estimated_time = duration * base_multiplier * text_factor
        else:
            # Matrix effect: roughly 1.2-1.8x realtime
            base_multiplier = 1.8 if output_format == "gif" else 1.2
            estimated_time = duration * base_multiplier

        # Add safety margin
        estimated_time *= 1.2

        return EstimationResult(
            estimated_seconds=estimated_time,
            confidence_level=0.3,  # Low confidence for fallback
            based_on_samples=0,
            factors_considered=["duration", "effect_type", "output_format", "text_length"],
            fallback_used=True
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about historical data and estimation accuracy."""
        self._load_historical_data()

        if not self.metrics_cache:
            return {"total_generations": 0, "message": "No historical data available"}

        successful_generations = [m for m in self.metrics_cache if m.success]

        stats = {
            "total_generations": len(self.metrics_cache),
            "successful_generations": len(successful_generations),
            "effect_types": {},
            "average_generation_time": 0,
            "data_age_days": 0
        }

        if successful_generations:
            # Calculate averages by effect type
            by_effect = defaultdict(list)
            for metrics in successful_generations:
                by_effect[metrics.effect_type].append(metrics.generation_time)

            for effect_type, times in by_effect.items():
                stats["effect_types"][effect_type] = {
                    "count": len(times),
                    "average_time": statistics.mean(times),
                    "min_time": min(times),
                    "max_time": max(times)
                }

            stats["average_generation_time"] = statistics.mean([m.generation_time for m in successful_generations])

            # Calculate data age
            oldest_timestamp = min(m.timestamp for m in self.metrics_cache)
            stats["data_age_days"] = (time.time() - oldest_timestamp) / (24 * 3600)

        return stats


# Global progress estimator instance
progress_estimator = ProgressEstimator()
