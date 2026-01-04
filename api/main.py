"""
CAN 2025 Guardian - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time

from api.v1.routes import auth, threats, ai, analytics, streams, alerts
from api.middleware import rate_limit_middleware, logging_middleware
from core.config import settings
from core.logger import app_logger

# Create FastAPI app
app = FastAPI(
    title="CAN 2025 Guardian API",
    description="Advanced Security Operations Center API for Africa Cup of Nations 2025",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production: ["https://your-frontend.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Custom middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Apply rate limiting and logging middleware
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(logging_middleware)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(threats.router, prefix="/api/v1/threats", tags=["Threat Detection"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI Chatbot"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(streams.router, prefix="/api/v1/streams", tags=["Video Streams"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts & Costs"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "message": "CAN 2025 Guardian API",
        "version": "2.0.0",
        "docs": "/api/docs",
        "status": "operational",
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "api": "operational",
            "database": "operational",  # Add actual DB check
            "cache": "operational",  # Add actual cache check
        },
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    app_logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
    )
    return JSONResponse(
        status_code=500, content={"detail": "Internal server error", "error": str(exc)}
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    app_logger.info("api_startup", version="2.0.0")

    # Initialize services
    # camera_manager initialization
    # database connection pool
    # cache connection


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    app_logger.info("api_shutdown")

    # Cleanup resources
    # camera_manager.stop_all()
    # close database connections
    # close cache connections


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
