"""Monitoring endpoints for health checks and metrics."""

import time
import psutil
import platform
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Response
from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST
)

from agenticraft import __version__ as agenticraft_version


# Create router
router = APIRouter()

# Prometheus metrics
request_count = Counter(
    "agenticraft_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"]
)

request_duration = Histogram(
    "agenticraft_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"]
)

active_agents = Gauge(
    "agenticraft_active_agents",
    "Number of active agents"
)

system_info = Info(
    "agenticraft_system",
    "System information"
)

# Set system info
system_info.info({
    "python_version": platform.python_version(),
    "platform": platform.platform(),
    "agenticraft_version": agenticraft_version,
})


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns service health status and basic system info.
    """
    # Check system resources
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    
    # Determine health status
    status = "healthy"
    issues = []
    
    if cpu_percent > 90:
        status = "degraded"
        issues.append(f"High CPU usage: {cpu_percent}%")
    
    if memory.percent > 90:
        status = "degraded"
        issues.append(f"High memory usage: {memory.percent}%")
    
    if disk.percent > 90:
        status = "degraded"
        issues.append(f"Low disk space: {disk.percent}% used")
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": agenticraft_version,
        "uptime_seconds": time.time() - startup_time,
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
        },
        "issues": issues,
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    
    Returns 200 if service is ready to accept traffic.
    """
    # Add any readiness checks here
    # For example, check database connection, external services, etc.
    
    return {"ready": True}


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    
    Returns 200 if service is alive.
    """
    return {"alive": True}


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Exposes metrics in Prometheus format.
    """
    # Update active agents metric (example)
    active_agents.set(3)  # In reality, track actual agent count
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/info")
async def service_info():
    """
    Service information endpoint.
    
    Returns detailed service and system information.
    """
    return {
        "service": {
            "name": "AgentiCraft API",
            "version": "1.0.0",
            "agenticraft_version": agenticraft_version,
            "environment": "production",
            "started_at": datetime.fromtimestamp(startup_time).isoformat(),
            "uptime_seconds": time.time() - startup_time,
        },
        "system": {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        },
        "capabilities": {
            "agents": ["simple", "reasoning", "workflow"],
            "tools": ["search", "calculator"],
            "providers": ["openai", "anthropic", "ollama"],
            "telemetry": True,
            "plugins": True,
        },
    }


@router.get("/debug/config")
async def debug_config():
    """
    Debug endpoint for configuration (development only).
    
    Should be disabled in production.
    """
    # Only return in development mode
    import os
    if os.getenv("ENVIRONMENT", "development") != "development":
        return {"error": "Not available in production"}
    
    return {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "service_name": os.getenv("SERVICE_NAME", "agenticraft-api"),
        "telemetry_enabled": os.getenv("ENABLE_TELEMETRY", "true"),
        "cors_origins": os.getenv("CORS_ORIGINS", "*"),
        "rate_limit": "100 requests/minute",
        "auth": "API Key",
    }


# Track startup time
startup_time = time.time()


# Export router with prefix
monitoring_router = router
