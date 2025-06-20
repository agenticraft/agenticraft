"""Production-ready decorators for AgentiCraft.

Simplified from Agentic Framework to provide essential decorators
for resilient multi-agent applications.
"""

import asyncio
import functools
import time
import logging
from typing import Any, Callable, Optional, TypeVar, Union, Type, Tuple
from datetime import datetime, timedelta
import random
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

# Type for decorated functions
F = TypeVar('F', bound=Callable[..., Any])


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass


class TimeoutError(Exception):
    """Raised when operation times out."""
    pass


def retry(
    *,
    attempts: int = 3,
    delay: float = 1.0,
    backoff: str = "exponential",
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Callable[[F], F]:
    """Retry decorator with configurable backoff strategies.
    
    Args:
        attempts: Maximum number of attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff strategy ("fixed", "exponential", "linear")
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback called on each retry with (exception, attempt)
        
    Example:
        ```python
        @retry(attempts=3, backoff="exponential")
        async def unstable_api_call():
            return await external_api.fetch()
        ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == attempts - 1:
                        logger.error(f"{func.__name__} failed after {attempts} attempts: {e}")
                        raise
                    
                    # Calculate delay
                    if backoff == "exponential":
                        wait_time = min(delay * (2 ** attempt), max_delay)
                    elif backoff == "linear":
                        wait_time = min(delay * (attempt + 1), max_delay)
                    else:  # fixed
                        wait_time = delay
                    
                    # Add jitter to prevent thundering herd
                    wait_time *= (0.8 + random.random() * 0.4)
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{attempts}), "
                        f"retrying in {wait_time:.1f}s: {e}"
                    )
                    
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    await asyncio.sleep(wait_time)
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == attempts - 1:
                        logger.error(f"{func.__name__} failed after {attempts} attempts: {e}")
                        raise
                    
                    # Calculate delay
                    if backoff == "exponential":
                        wait_time = min(delay * (2 ** attempt), max_delay)
                    elif backoff == "linear":
                        wait_time = min(delay * (attempt + 1), max_delay)
                    else:  # fixed
                        wait_time = delay
                    
                    # Add jitter
                    wait_time *= (0.8 + random.random() * 0.4)
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{attempts}), "
                        f"retrying in {wait_time:.1f}s: {e}"
                    )
                    
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    time.sleep(wait_time)
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
    
    return decorator


def timeout(
    *,
    seconds: float,
    error_message: Optional[str] = None
) -> Callable[[F], F]:
    """Timeout decorator for async and sync functions.
    
    Args:
        seconds: Timeout duration in seconds
        error_message: Custom error message
        
    Example:
        ```python
        @timeout(seconds=30)
        async def long_running_task():
            await process_data()
        ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                msg = error_message or f"{func.__name__} timed out after {seconds}s"
                logger.error(msg)
                raise TimeoutError(msg)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # For sync functions, we need to run in a thread with timeout
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=seconds)
                except concurrent.futures.TimeoutError:
                    msg = error_message or f"{func.__name__} timed out after {seconds}s"
                    logger.error(msg)
                    raise TimeoutError(msg)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
    
    return decorator


def cache(
    *,
    ttl: float = 300,
    maxsize: int = 128,
    key_func: Optional[Callable[..., str]] = None
) -> Callable[[F], F]:
    """Simple TTL cache decorator.
    
    Args:
        ttl: Time-to-live in seconds
        maxsize: Maximum cache size
        key_func: Optional function to generate cache key
        
    Example:
        ```python
        @cache(ttl=60, maxsize=100)
        async def get_user_data(user_id: str):
            return await database.fetch_user(user_id)
        ```
    """
    def decorator(func: F) -> F:
        cache_data = {}
        cache_times = {}
        
        def make_key(args, kwargs):
            if key_func:
                return key_func(*args, **kwargs)
            # Simple key generation
            return f"{args}:{sorted(kwargs.items())}"
        
        def is_expired(key: str) -> bool:
            if key not in cache_times:
                return True
            return time.time() - cache_times[key] > ttl
        
        def evict_oldest():
            if not cache_times:
                return
            oldest_key = min(cache_times, key=cache_times.get)
            del cache_data[oldest_key]
            del cache_times[oldest_key]
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            key = make_key(args, kwargs)
            
            # Check cache
            if key in cache_data and not is_expired(key):
                logger.debug(f"Cache hit for {func.__name__}")
                return cache_data[key]
            
            # Remove expired entry
            if key in cache_data:
                del cache_data[key]
                del cache_times[key]
            
            # Evict if at capacity
            while len(cache_data) >= maxsize:
                evict_oldest()
            
            # Call function and cache
            logger.debug(f"Cache miss for {func.__name__}")
            result = await func(*args, **kwargs)
            cache_data[key] = result
            cache_times[key] = time.time()
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            key = make_key(args, kwargs)
            
            # Check cache
            if key in cache_data and not is_expired(key):
                logger.debug(f"Cache hit for {func.__name__}")
                return cache_data[key]
            
            # Remove expired entry
            if key in cache_data:
                del cache_data[key]
                del cache_times[key]
            
            # Evict if at capacity
            while len(cache_data) >= maxsize:
                evict_oldest()
            
            # Call function and cache
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            cache_data[key] = result
            cache_times[key] = time.time()
            
            return result
        
        # Add cache control methods
        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper.cache_clear = lambda: (cache_data.clear(), cache_times.clear())  # type: ignore
        wrapper.cache_info = lambda: {"size": len(cache_data), "ttl": ttl, "maxsize": maxsize}  # type: ignore
        
        return wrapper  # type: ignore
    
    return decorator


def rate_limit(
    *,
    calls: int = 60,
    period: float = 60.0,
    key_func: Optional[Callable[..., str]] = None,
    raise_on_limit: bool = True
) -> Callable[[F], F]:
    """Rate limiting decorator using sliding window.
    
    Args:
        calls: Maximum number of calls allowed
        period: Time period in seconds
        key_func: Optional function to generate rate limit key (for per-user limits)
        raise_on_limit: If True, raise exception; if False, wait
        
    Example:
        ```python
        @rate_limit(calls=100, period=60)
        async def api_endpoint(user_id: str):
            return await process_request(user_id)
        ```
    """
    def decorator(func: F) -> F:
        # Track call times per key
        call_windows = defaultdict(lambda: deque())
        
        def make_key(args, kwargs):
            if key_func:
                return key_func(*args, **kwargs)
            return "default"
        
        def check_and_update_limit(key: str) -> Optional[float]:
            """Check rate limit and return wait time if exceeded."""
            now = time.time()
            window = call_windows[key]
            
            # Remove old calls outside the window
            while window and window[0] <= now - period:
                window.popleft()
            
            # Check if limit exceeded
            if len(window) >= calls:
                if raise_on_limit:
                    oldest_call = window[0]
                    reset_time = oldest_call + period
                    wait_time = reset_time - now
                    return wait_time
                else:
                    # Calculate wait time
                    oldest_call = window[0]
                    return (oldest_call + period) - now
            
            # Record this call
            window.append(now)
            return None
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            key = make_key(args, kwargs)
            wait_time = check_and_update_limit(key)
            
            if wait_time is not None:
                if raise_on_limit:
                    raise RateLimitExceeded(
                        f"Rate limit exceeded for {func.__name__}. "
                        f"Try again in {wait_time:.1f} seconds."
                    )
                else:
                    logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    # Retry after waiting
                    return await async_wrapper(*args, **kwargs)
            
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            key = make_key(args, kwargs)
            wait_time = check_and_update_limit(key)
            
            if wait_time is not None:
                if raise_on_limit:
                    raise RateLimitExceeded(
                        f"Rate limit exceeded for {func.__name__}. "
                        f"Try again in {wait_time:.1f} seconds."
                    )
                else:
                    logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
                    time.sleep(wait_time)
                    # Retry after waiting
                    return sync_wrapper(*args, **kwargs)
            
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
    
    return decorator


def fallback(
    *,
    default: Any = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    callback: Optional[Callable[[Exception], Any]] = None
) -> Callable[[F], F]:
    """Fallback decorator that returns default value on exception.
    
    Args:
        default: Default value to return on exception
        exceptions: Tuple of exceptions to catch
        callback: Optional callback to generate fallback value from exception
        
    Example:
        ```python
        @fallback(default=[], exceptions=(APIError,))
        async def fetch_data():
            return await unstable_api.get_data()
        ```
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                logger.warning(f"{func.__name__} failed, using fallback: {e}")
                if callback:
                    return callback(e)
                return default
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                logger.warning(f"{func.__name__} failed, using fallback: {e}")
                if callback:
                    return callback(e)
                return default
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
    
    return decorator


def measure_time(
    *,
    log_level: str = "INFO",
    include_args: bool = False
) -> Callable[[F], F]:
    """Measure and log execution time.
    
    Args:
        log_level: Logging level for timing messages
        include_args: Whether to include function arguments in log
        
    Example:
        ```python
        @measure_time(log_level="DEBUG")
        async def process_batch(items):
            await heavy_computation(items)
        ```
    """
    def decorator(func: F) -> F:
        log_func = getattr(logger, log_level.lower(), logger.info)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start
                
                msg = f"{func.__name__} completed in {duration:.3f}s"
                if include_args:
                    msg += f" (args={args}, kwargs={kwargs})"
                log_func(msg)
                
                return result
            except Exception as e:
                duration = time.perf_counter() - start
                logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start
                
                msg = f"{func.__name__} completed in {duration:.3f}s"
                if include_args:
                    msg += f" (args={args}, kwargs={kwargs})"
                log_func(msg)
                
                return result
            except Exception as e:
                duration = time.perf_counter() - start
                logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
    
    return decorator


def synchronized(lock: Optional[asyncio.Lock] = None) -> Callable[[F], F]:
    """Synchronize function execution with a lock.
    
    Args:
        lock: Optional lock to use (creates one if not provided)
        
    Example:
        ```python
        shared_lock = asyncio.Lock()
        
        @synchronized(shared_lock)
        async def critical_section():
            await modify_shared_resource()
        ```
    """
    _lock = lock or asyncio.Lock()
    
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            async with _lock:
                return await func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            raise ValueError("synchronized decorator only works with async functions")
    
    return decorator


# Composite decorators for common patterns

def resilient(
    *,
    retry_attempts: int = 3,
    timeout_seconds: float = 30,
    fallback_value: Any = None,
    cache_ttl: Optional[float] = None
) -> Callable[[F], F]:
    """Composite decorator for resilient function execution.
    
    Combines retry, timeout, fallback, and optional caching.
    
    Args:
        retry_attempts: Number of retry attempts
        timeout_seconds: Timeout for each attempt
        fallback_value: Value to return if all attempts fail
        cache_ttl: Optional cache TTL in seconds
        
    Example:
        ```python
        @resilient(retry_attempts=3, timeout_seconds=10, fallback_value=[])
        async def fetch_critical_data():
            return await external_service.get_data()
        ```
    """
    def decorator(func: F) -> F:
        # Build decorator chain
        decorated = func
        
        # Add timeout
        decorated = timeout(seconds=timeout_seconds)(decorated)
        
        # Add retry
        decorated = retry(attempts=retry_attempts, backoff="exponential")(decorated)
        
        # Add fallback
        decorated = fallback(default=fallback_value)(decorated)
        
        # Add cache if requested
        if cache_ttl:
            decorated = cache(ttl=cache_ttl)(decorated)
        
        return decorated  # type: ignore
    
    return decorator
