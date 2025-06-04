"""
AgentiCraft FastAPI Application Template.

This template demonstrates how to build a production-ready API with AgentiCraft agents.
It includes middleware for auth, rate limiting, CORS, and monitoring endpoints.
"""

import os
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agenticraft import __version__ as agenticraft_version
from agenticraft.telemetry import setup_telemetry

from .agents import agent_router
from .middleware import RateLimitMiddleware, AuthMiddleware
from .monitoring import monitoring_router


# Environment configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "agenticraft-api")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ENABLE_TELEMETRY = os.getenv("ENABLE_TELEMETRY", "true").lower() == "true"
OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    if ENABLE_TELEMETRY:
        setup_telemetry(
            service_name=SERVICE_NAME,
            environment=ENVIRONMENT,
            otlp_endpoint=OTLP_ENDPOINT,
        )
        print(f"✅ Telemetry initialized for {SERVICE_NAME}")
    
    print(f"✅ AgentiCraft API v{agenticraft_version} started")
    
    yield
    
    # Shutdown
    print("👋 AgentiCraft API shutting down")


# Create FastAPI app
app = FastAPI(
    title="AgentiCraft API",
    description="Production-ready AI Agent API powered by AgentiCraft",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RateLimitMiddleware, calls=100, period=60)  # 100 calls per minute
app.add_middleware(AuthMiddleware, skip_paths=["/health", "/metrics", "/docs", "/redoc"])

# Include routers
app.include_router(agent_router, prefix="/agents", tags=["agents"])
app.include_router(monitoring_router, prefix="", tags=["monitoring"])


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AgentiCraft API",
        "version": "1.0.0",
        "agenticraft_version": agenticraft_version,
        "status": "running",
        "environment": ENVIRONMENT,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unexpected errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if ENVIRONMENT == "development" else "An error occurred",
            "path": str(request.url),
        },
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=ENVIRONMENT == "development",
        log_level="info",
    )
