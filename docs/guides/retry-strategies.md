# Retry Strategies and Error Handling Guide

This guide covers best practices for making your AgentiCraft workflows resilient and production-ready using decorators and error handling patterns.

## Table of Contents

1. [Overview](#overview)
2. [Available Decorators](#available-decorators)
3. [Retry Strategies](#retry-strategies)
4. [Error Handling Patterns](#error-handling-patterns)
5. [Production Best Practices](#production-best-practices)
6. [Examples](#examples)

## Overview

AgentiCraft provides a comprehensive set of decorators to handle common production scenarios:

- **Transient failures**: Network issues, API rate limits
- **Long-running operations**: Timeouts and cancellation
- **Resource optimization**: Caching and rate limiting
- **Graceful degradation**: Fallback mechanisms

## Available Decorators

### 1. `@retry` - Automatic Retry with Backoff

Retries failed operations with configurable backoff strategies.

```python
from agenticraft.utils.decorators import retry

@retry(
    attempts=3,                    # Maximum retry attempts
    delay=1.0,                     # Initial delay in seconds
    backoff="exponential",         # Backoff strategy
    max_delay=60.0,               # Maximum delay between retries
    exceptions=(APIError,),        # Specific exceptions to retry
    on_retry=lambda e, n: print(f"Retry {n}: {e}")  # Callback
)
async def unstable_api_call():
    return await external_api.fetch()
```

**Backoff Strategies:**
- `"fixed"`: Same delay between retries
- `"linear"`: Linear increase (delay * attempt)
- `"exponential"`: Exponential increase (delay * 2^attempt)

### 2. `@timeout` - Operation Timeouts

Prevents operations from running indefinitely.

```python
from agenticraft.utils.decorators import timeout, TimeoutError

@timeout(seconds=30, error_message="Custom timeout message")
async def long_running_task():
    await process_large_dataset()
```

### 3. `@cache` - Result Caching

Caches function results with time-to-live (TTL).

```python
from agenticraft.utils.decorators import cache

@cache(
    ttl=300,          # Cache for 5 minutes
    maxsize=128,      # Maximum cache entries
    key_func=lambda user_id, **kw: f"user:{user_id}"  # Custom key
)
async def get_user_data(user_id: str):
    return await database.fetch_user(user_id)

# Cache control
get_user_data.cache_clear()  # Clear cache
info = get_user_data.cache_info()  # Get cache stats
```

### 4. `@rate_limit` - API Rate Limiting

Enforces rate limits using a sliding window algorithm.

```python
from agenticraft.utils.decorators import rate_limit, RateLimitExceeded

@rate_limit(
    calls=100,                     # Maximum calls
    period=60.0,                   # Time period in seconds
    key_func=lambda user_id, **kw: user_id,  # Per-user limits
    raise_on_limit=True            # Raise exception or wait
)
async def api_endpoint(user_id: str):
    return await process_request(user_id)
```

### 5. `@fallback` - Graceful Degradation

Returns default values on failure.

```python
from agenticraft.utils.decorators import fallback

@fallback(
    default=[],                    # Default return value
    exceptions=(DatabaseError,),   # Specific exceptions
    callback=lambda e: log_error(e) or []  # Dynamic fallback
)
async def fetch_recommendations():
    return await recommendation_engine.get()
```

### 6. `@measure_time` - Performance Monitoring

Logs execution time for performance tracking.

```python
from agenticraft.utils.decorators import measure_time

@measure_time(log_level="INFO", include_args=True)
async def process_batch(batch_id: str, items: list):
    return await heavy_computation(items)
```

### 7. `@resilient` - All-in-One Resilience

Combines retry, timeout, fallback, and caching.

```python
from agenticraft.utils.decorators import resilient

@resilient(
    retry_attempts=3,
    timeout_seconds=30,
    fallback_value={"status": "degraded"},
    cache_ttl=300  # Optional caching
)
async def critical_operation():
    return await complex_workflow()
```

## Retry Strategies

### Choosing the Right Strategy

1. **Fixed Backoff**
   - Use for: Rate-limited APIs with known limits
   - Example: API allows 1 request per second

```python
@retry(attempts=5, delay=1.0, backoff="fixed")
async def rate_limited_api():
    return await api.call()
```

2. **Linear Backoff**
   - Use for: Gradually increasing load
   - Example: Database recovery scenarios

```python
@retry(attempts=4, delay=2.0, backoff="linear", max_delay=10.0)
async def database_operation():
    return await db.query()
```

3. **Exponential Backoff**
   - Use for: Network issues, distributed systems
   - Example: Cloud service calls

```python
@retry(
    attempts=5, 
    delay=0.5, 
    backoff="exponential", 
    max_delay=30.0
)
async def cloud_service_call():
    return await aws.invoke()
```

### Jitter for Thundering Herd Prevention

All retry strategies automatically add jitter (±20%) to prevent synchronized retries:

```python
# Actual delay = calculated_delay * (0.8 + random() * 0.4)
```

## Error Handling Patterns

### 1. Selective Exception Handling

Only retry specific exceptions:

```python
from aiohttp import ClientError
from asyncio import TimeoutError

@retry(
    attempts=3,
    exceptions=(ClientError, TimeoutError),  # Only network errors
    on_retry=lambda e, n: logger.warning(f"Network issue: {e}")
)
async def fetch_external_data():
    async with aiohttp.ClientSession() as session:
        return await session.get(url)
```

### 2. Cascading Fallbacks

Multiple levels of fallback:

```python
@timeout(seconds=5)
@fallback(default=get_from_cache())
async def get_live_data():
    return await primary_source.fetch()

@fallback(default=get_static_data())
async def get_from_cache():
    return await cache.get("data")

def get_static_data():
    return {"status": "static", "data": [...]}
```

### 3. Circuit Breaker Pattern

Prevent cascading failures:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure = None
        self.is_open = False
    
    async def call(self, func, *args, **kwargs):
        if self.is_open:
            if time.time() - self.last_failure > self.timeout:
                self.is_open = False
                self.failure_count = 0
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
            
            raise e
```

### 4. Bulkhead Pattern

Isolate failures:

```python
from asyncio import Semaphore

class BulkheadExecutor:
    def __init__(self, max_concurrent=10):
        self.semaphore = Semaphore(max_concurrent)
    
    @resilient(retry_attempts=3, timeout_seconds=30)
    async def execute(self, func, *args, **kwargs):
        async with self.semaphore:
            return await func(*args, **kwargs)

# Usage
bulkhead = BulkheadExecutor(max_concurrent=5)
results = await asyncio.gather(*[
    bulkhead.execute(process_item, item)
    for item in items
])
```

## Production Best Practices

### 1. Layered Timeouts

Set timeouts at multiple levels:

```python
# HTTP client timeout
client_timeout = aiohttp.ClientTimeout(total=10)

# Function timeout
@timeout(seconds=15)
async def fetch_data():
    async with aiohttp.ClientSession(timeout=client_timeout) as session:
        return await session.get(url)

# Workflow timeout
@timeout(seconds=60)
async def complete_workflow():
    data = await fetch_data()
    return await process(data)
```

### 2. Observability

Add logging and metrics:

```python
from agenticraft.utils.decorators import retry, measure_time

@measure_time(log_level="INFO")
@retry(
    attempts=3,
    on_retry=lambda e, n: metrics.increment("retry_count", tags={"attempt": n})
)
async def monitored_operation():
    try:
        result = await risky_operation()
        metrics.increment("operation_success")
        return result
    except Exception as e:
        metrics.increment("operation_failure", tags={"error": type(e).__name__})
        raise
```

### 3. Graceful Degradation

Provide reduced functionality instead of failing:

```python
class ResilientService:
    @cache(ttl=300)  # Cache for 5 minutes
    async def get_full_data(self):
        return await self._fetch_all_data()
    
    @fallback(default=lambda e: self.get_cached_data())
    async def _fetch_all_data(self):
        # Try to get fresh data
        return await external_api.fetch_all()
    
    async def get_cached_data(self):
        # Return partial/stale data
        return {
            "data": await cache.get("last_known_good"),
            "status": "degraded",
            "cached_at": datetime.utcnow()
        }
```

### 4. Health Checks

Implement comprehensive health checks:

```python
class HealthChecker:
    @timeout(seconds=5)
    @fallback(default={"status": "unknown"})
    async def check_dependency(self, name: str, check_func):
        start = time.time()
        try:
            await check_func()
            return {
                "status": "healthy",
                "latency": time.time() - start
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "latency": time.time() - start
            }
    
    async def check_all(self):
        checks = await asyncio.gather(
            self.check_dependency("database", db.ping),
            self.check_dependency("cache", cache.ping),
            self.check_dependency("api", api.health),
            return_exceptions=True
        )
        
        return {
            "status": "healthy" if all(c["status"] == "healthy" for c in checks) else "degraded",
            "checks": dict(zip(["database", "cache", "api"], checks))
        }
```

## Examples

### Complete Resilient Workflow

```python
from agenticraft.workflows import ResearchTeam
from agenticraft.utils.decorators import retry, timeout, cache, rate_limit

class ProductionResearchTeam(ResearchTeam):
    """Production-ready research team with full resilience."""
    
    @rate_limit(calls=10, period=60)  # 10 researches per minute
    @cache(ttl=3600)  # Cache for 1 hour
    @timeout(seconds=300)  # 5 minute timeout
    @retry(attempts=3, backoff="exponential")
    async def research(self, topic: str, **kwargs):
        """Research with full production hardening."""
        try:
            # Log start
            logger.info(f"Starting research: {topic}")
            
            # Execute with monitoring
            with metrics.timer("research_duration"):
                result = await super().research(topic, **kwargs)
            
            # Log success
            logger.info(f"Research completed: {topic}")
            metrics.increment("research_success")
            
            return result
            
        except Exception as e:
            # Log failure
            logger.error(f"Research failed: {topic}", exc_info=True)
            metrics.increment("research_failure", tags={"error": type(e).__name__})
            
            # Try fallback to cached or degraded result
            return await self.get_fallback_research(topic)
    
    @fallback(default={"status": "degraded", "source": "cache"})
    async def get_fallback_research(self, topic: str):
        """Get cached or simplified research results."""
        # Try cache first
        cached = await cache.get(f"research:{topic}")
        if cached:
            return {**cached, "from_cache": True}
        
        # Simple research as last resort
        return {
            "topic": topic,
            "summary": "Research temporarily unavailable",
            "status": "degraded"
        }
```

### Testing Resilience

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_retry_behavior():
    """Test that retry decorator works correctly."""
    mock_func = AsyncMock(side_effect=[
        Exception("First failure"),
        Exception("Second failure"),
        {"success": True}  # Third attempt succeeds
    ])
    
    @retry(attempts=3, delay=0.1)
    async def flaky_function():
        return await mock_func()
    
    result = await flaky_function()
    
    assert result == {"success": True}
    assert mock_func.call_count == 3

@pytest.mark.asyncio
async def test_timeout_behavior():
    """Test that timeout decorator works correctly."""
    @timeout(seconds=0.1)
    async def slow_function():
        await asyncio.sleep(1.0)
        return "Should not reach here"
    
    with pytest.raises(TimeoutError):
        await slow_function()
```

## Summary

By applying these decorators and patterns, you can transform your AgentiCraft workflows from prototypes into production-ready systems that:

1. **Handle failures gracefully** with automatic retries
2. **Prevent hanging** with comprehensive timeouts
3. **Optimize performance** with intelligent caching
4. **Protect resources** with rate limiting
5. **Degrade gracefully** with fallback mechanisms
6. **Provide observability** with logging and metrics

Remember: The goal is not to prevent all failures but to handle them gracefully and maintain service availability even under adverse conditions.
