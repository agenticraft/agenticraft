"""Middleware components for the FastAPI application."""

import time
import secrets
from typing import Callable, List, Optional

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware.
    
    In production, consider using Redis or another distributed cache.
    """
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.cache = {}  # In production, use Redis
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client identifier (IP address or API key)
        client_id = request.client.host if request.client else "unknown"
        
        # Check rate limit
        now = time.time()
        key = f"rate_limit:{client_id}"
        
        if key in self.cache:
            calls, reset_time = self.cache[key]
            if now < reset_time:
                if calls >= self.calls:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Rate limit exceeded",
                            "retry_after": int(reset_time - now),
                        },
                        headers={
                            "X-RateLimit-Limit": str(self.calls),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(int(reset_time)),
                        }
                    )
                self.cache[key] = (calls + 1, reset_time)
            else:
                self.cache[key] = (1, now + self.period)
        else:
            self.cache[key] = (1, now + self.period)
        
        # Add rate limit headers
        calls, reset_time = self.cache[key]
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.calls - calls))
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        
        return response


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Simple API key authentication middleware.
    
    In production, consider using JWT tokens or OAuth2.
    """
    
    def __init__(self, app, skip_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.skip_paths = skip_paths or []
        # In production, load from secure storage
        self.api_keys = {
            "demo-key-123": "demo-user",
            # Add more API keys here
        }
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip auth for certain paths
        path = request.url.path
        if any(path.startswith(skip_path) for skip_path in self.skip_paths):
            return await call_next(request)
        
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"error": "Missing API key"},
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        # Validate API key
        if api_key not in self.api_keys:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid API key"},
            )
        
        # Add user info to request state
        request.state.user = self.api_keys[api_key]
        
        return await call_next(request)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request for tracing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or secrets.token_urlsafe(16)
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Add response timing information."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        return response


__all__ = [
    "RateLimitMiddleware",
    "AuthMiddleware",
    "RequestIdMiddleware",
    "TimingMiddleware",
]
