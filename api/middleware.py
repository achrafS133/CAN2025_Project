"""
API Middleware
Rate limiting, logging, and request processing
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time

from core.rate_limiter import global_rate_limiter, RateLimitError
from core.logger import app_logger, audit_logger


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    # Skip OPTIONS preflight requests (CORS)
    if request.method == "OPTIONS":
        return await call_next(request)

    # Extract user ID from request (from auth token or IP)
    user_id = request.client.host  # Use IP as fallback

    # Skip rate limiting for health check
    if request.url.path in [
        "/health",
        "/",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
    ]:
        return await call_next(request)

    # Check rate limit
    try:
        allowed, error_msg = global_rate_limiter.check_limit(user_id)
        if not allowed:
            raise HTTPException(status_code=429, detail=error_msg)
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))

    response = await call_next(request)

    # Add rate limit headers
    quota = global_rate_limiter.get_remaining_quota(user_id)
    response.headers["X-RateLimit-Remaining-Minute"] = str(quota["per_minute"])
    response.headers["X-RateLimit-Remaining-Hour"] = str(quota["per_hour"])
    response.headers["X-RateLimit-Remaining-Day"] = str(quota["per_day"])

    return response


async def logging_middleware(request: Request, call_next):
    """Logging middleware for all requests"""
    # Skip OPTIONS preflight requests (CORS)
    if request.method == "OPTIONS":
        return await call_next(request)

    start_time = time.time()

    # Log request
    app_logger.info(
        "api_request",
        method=request.method,
        path=request.url.path,
        client=request.client.host,
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = (time.time() - start_time) * 1000  # ms

    # Log response
    app_logger.info(
        "api_response",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration,
    )

    # Audit log for important endpoints
    if request.url.path.startswith("/api/v1/threats") or request.url.path.startswith(
        "/api/v1/alerts"
    ):
        audit_logger.log_event(
            event_type="api_access",
            action=request.method,
            resource=request.url.path,
            status="success" if response.status_code < 400 else "error",
            ip_address=request.client.host,
        )

    return response
