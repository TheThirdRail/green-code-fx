"""
Rate limiting middleware for Green-Code FX API.

This module provides in-memory rate limiting functionality to protect the API
from abuse and ensure fair resource allocation across clients.
"""

import time
import threading
from collections import defaultdict, deque
from typing import Dict, Tuple, Optional
from functools import wraps

import structlog
from flask import request, jsonify, g

from .config import config

logger = structlog.get_logger()


class RateLimiter:
    """In-memory rate limiter using sliding window algorithm."""
    
    def __init__(self, requests_per_minute: int = 10, cleanup_interval: int = 300):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute per client
            cleanup_interval: Seconds between cleanup of old entries
        """
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute window
        self.cleanup_interval = cleanup_interval
        
        # Client request tracking: {client_ip: deque of timestamps}
        self.client_requests: Dict[str, deque] = defaultdict(deque)
        self.lock = threading.RLock()
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
        logger.info("Rate limiter initialized", 
                   requests_per_minute=requests_per_minute,
                   window_size=self.window_size)
    
    def _start_cleanup_thread(self):
        """Start background thread to clean up old entries."""
        def cleanup():
            while True:
                try:
                    time.sleep(self.cleanup_interval)
                    self._cleanup_old_entries()
                except Exception as e:
                    logger.error("Rate limiter cleanup error", error=str(e))
        
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_old_entries(self):
        """Remove old request entries to prevent memory leaks."""
        current_time = time.time()
        cutoff_time = current_time - self.window_size
        
        with self.lock:
            clients_to_remove = []
            
            for client_ip, requests in self.client_requests.items():
                # Remove old requests
                while requests and requests[0] < cutoff_time:
                    requests.popleft()
                
                # Mark empty clients for removal
                if not requests:
                    clients_to_remove.append(client_ip)
            
            # Remove empty client entries
            for client_ip in clients_to_remove:
                del self.client_requests[client_ip]
        
        if clients_to_remove:
            logger.debug("Rate limiter cleanup completed", 
                        removed_clients=len(clients_to_remove))
    
    def _get_client_identifier(self) -> str:
        """Get client identifier for rate limiting."""
        # Try to get real IP from headers (for reverse proxy setups)
        client_ip = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
        if not client_ip:
            client_ip = request.headers.get('X-Real-IP', '')
        if not client_ip:
            client_ip = request.remote_addr or 'unknown'
        
        return client_ip
    
    def is_allowed(self, client_ip: Optional[str] = None) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is allowed for the client.
        
        Args:
            client_ip: Client IP address (auto-detected if None)
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        if client_ip is None:
            client_ip = self._get_client_identifier()
        
        current_time = time.time()
        cutoff_time = current_time - self.window_size
        
        with self.lock:
            requests = self.client_requests[client_ip]
            
            # Remove old requests
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            
            # Check if limit exceeded
            current_count = len(requests)
            is_allowed = current_count < self.requests_per_minute
            
            if is_allowed:
                # Add current request
                requests.append(current_time)
            
            # Calculate reset time (when oldest request expires)
            reset_time = None
            if requests:
                reset_time = int(requests[0] + self.window_size)
            
            rate_limit_info = {
                "limit": self.requests_per_minute,
                "remaining": max(0, self.requests_per_minute - current_count - (1 if is_allowed else 0)),
                "reset": reset_time,
                "retry_after": None
            }
            
            if not is_allowed and requests:
                # Calculate retry after (when next slot becomes available)
                rate_limit_info["retry_after"] = int(requests[0] + self.window_size - current_time)
            
            return is_allowed, rate_limit_info
    
    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics."""
        with self.lock:
            total_clients = len(self.client_requests)
            total_requests = sum(len(requests) for requests in self.client_requests.values())
            
            return {
                "total_clients": total_clients,
                "total_active_requests": total_requests,
                "requests_per_minute_limit": self.requests_per_minute,
                "window_size_seconds": self.window_size
            }


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=config.RATE_LIMIT_PER_MINUTE)


def rate_limit_decorator(f):
    """Decorator to apply rate limiting to Flask routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check rate limit
        is_allowed, rate_info = rate_limiter.is_allowed()
        
        # Add rate limit headers to response
        g.rate_limit_info = rate_info
        
        if not is_allowed:
            logger.warning("Rate limit exceeded", 
                          client_ip=rate_limiter._get_client_identifier(),
                          limit=rate_info["limit"],
                          retry_after=rate_info.get("retry_after"))
            
            response = jsonify({
                "error": "Rate limit exceeded",
                "message": f"Maximum {rate_info['limit']} requests per minute allowed",
                "retry_after": rate_info.get("retry_after")
            })
            response.status_code = 429
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            if rate_info.get("reset"):
                response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
            if rate_info.get("retry_after"):
                response.headers["Retry-After"] = str(rate_info["retry_after"])
            
            return response
        
        return f(*args, **kwargs)
    
    return decorated_function


def add_rate_limit_headers(response):
    """Add rate limit headers to response."""
    if hasattr(g, 'rate_limit_info'):
        rate_info = g.rate_limit_info
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        if rate_info.get("reset"):
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
    
    return response


def get_rate_limit_status() -> Dict[str, any]:
    """Get current rate limit status for the requesting client."""
    is_allowed, rate_info = rate_limiter.is_allowed()
    client_ip = rate_limiter._get_client_identifier()
    
    return {
        "client_ip": client_ip,
        "is_allowed": is_allowed,
        "rate_limit": rate_info,
        "global_stats": rate_limiter.get_stats()
    }
