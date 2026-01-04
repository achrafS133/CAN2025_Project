"""
Rate Limiting Middleware
Prevents API abuse and manages request quotas
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import time
from functools import wraps
from core.logger import app_logger, audit_logger


class RateLimiter:
    """
    Token bucket rate limiter for API calls
    Supports per-minute, per-hour, and per-day limits
    """

    def __init__(
        self,
        max_per_minute: int = 60,
        max_per_hour: int = 1000,
        max_per_day: int = 10000,
    ):
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        self.max_per_day = max_per_day

        # Request counters
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)
        self.day_requests: Dict[str, list] = defaultdict(list)

        app_logger.info(
            "rate_limiter_initialized",
            limits={
                "per_minute": max_per_minute,
                "per_hour": max_per_hour,
                "per_day": max_per_day,
            },
        )

    def _clean_old_requests(self, requests: list, window_seconds: int):
        """Remove requests older than the time window"""
        cutoff = time.time() - window_seconds
        return [req for req in requests if req > cutoff]

    def check_limit(self, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if user is within rate limits

        Args:
            user_id: User identifier

        Returns:
            (is_allowed, error_message)
        """
        current_time = time.time()

        # Clean old requests
        self.minute_requests[user_id] = self._clean_old_requests(
            self.minute_requests[user_id], 60
        )
        self.hour_requests[user_id] = self._clean_old_requests(
            self.hour_requests[user_id], 3600
        )
        self.day_requests[user_id] = self._clean_old_requests(
            self.day_requests[user_id], 86400
        )

        # Check per-minute limit
        if len(self.minute_requests[user_id]) >= self.max_per_minute:
            audit_logger.log_event(
                event_type="rate_limit_exceeded",
                user_id=user_id,
                action="api_call",
                resource="per_minute_limit",
                status="blocked",
            )
            return (
                False,
                f"Rate limit exceeded: {self.max_per_minute} requests per minute",
            )

        # Check per-hour limit
        if len(self.hour_requests[user_id]) >= self.max_per_hour:
            audit_logger.log_event(
                event_type="rate_limit_exceeded",
                user_id=user_id,
                action="api_call",
                resource="per_hour_limit",
                status="blocked",
            )
            return False, f"Rate limit exceeded: {self.max_per_hour} requests per hour"

        # Check per-day limit
        if len(self.day_requests[user_id]) >= self.max_per_day:
            audit_logger.log_event(
                event_type="rate_limit_exceeded",
                user_id=user_id,
                action="api_call",
                resource="per_day_limit",
                status="blocked",
            )
            return False, f"Rate limit exceeded: {self.max_per_day} requests per day"

        # Record this request
        self.minute_requests[user_id].append(current_time)
        self.hour_requests[user_id].append(current_time)
        self.day_requests[user_id].append(current_time)

        return True, None

    def get_remaining_quota(self, user_id: str) -> Dict[str, int]:
        """Get remaining request quota for user"""
        return {
            "per_minute": self.max_per_minute - len(self.minute_requests[user_id]),
            "per_hour": self.max_per_hour - len(self.hour_requests[user_id]),
            "per_day": self.max_per_day - len(self.day_requests[user_id]),
        }

    def reset_user_limits(self, user_id: str):
        """Reset all limits for a user (admin function)"""
        self.minute_requests[user_id] = []
        self.hour_requests[user_id] = []
        self.day_requests[user_id] = []

        app_logger.info("rate_limits_reset", user_id=user_id)


def rate_limit(limiter: RateLimiter, user_id: str = "default"):
    """
    Decorator for rate limiting functions

    Usage:
        @rate_limit(rate_limiter, user_id="user123")
        def my_function():
            pass
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            allowed, error_msg = limiter.check_limit(user_id)
            if not allowed:
                app_logger.warning(
                    "rate_limit_blocked",
                    user_id=user_id,
                    function=func.__name__,
                    message=error_msg,
                )
                raise RateLimitError(error_msg)
            return func(*args, **kwargs)

        return wrapper

    return decorator


class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded"""

    pass


# Global rate limiter instance
global_rate_limiter = RateLimiter()
