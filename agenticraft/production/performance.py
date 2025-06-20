"""
Performance optimization utilities for AgentiCraft.

This module provides tools for optimizing performance including:
- Caching strategies
- Connection pooling
- Async optimizations
- Resource management
"""
import asyncio
import functools
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from datetime import datetime, timedelta
import logging
from collections import OrderedDict
import weakref

logger = logging.getLogger(__name__)

T = TypeVar('T')


class LRUCache:
    """Least Recently Used cache implementation."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: Optional[float] = None):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items in cache
            ttl_seconds: Time to live for cache entries
        """
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[Any, float] = {}
        self._hits = 0
        self._misses = 0
        
    def get(self, key: Any) -> Optional[Any]:
        """Get item from cache."""
        # Check if exists and not expired
        if key in self._cache:
            if self.ttl:
                if time.time() - self._timestamps[key] > self.ttl:
                    # Expired
                    del self._cache[key]
                    del self._timestamps[key]
                    self._misses += 1
                    return None
                    
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
            
        self._misses += 1
        return None
        
    def put(self, key: Any, value: Any):
        """Put item in cache."""
        # Remove if already exists
        if key in self._cache:
            del self._cache[key]
            
        # Add to end
        self._cache[key] = value
        self._timestamps[key] = time.time()
        
        # Remove oldest if over limit
        if len(self._cache) > self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            del self._timestamps[oldest_key]
            
    def clear(self):
        """Clear cache."""
        self._cache.clear()
        self._timestamps.clear()
        
    @property
    def hit_rate(self) -> float:
        """Get cache hit rate."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0
        
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
            "ttl": self.ttl
        }


def cached(
    max_size: int = 128,
    ttl_seconds: Optional[float] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator for caching function results.
    
    Args:
        max_size: Maximum cache size
        ttl_seconds: Cache TTL
        key_func: Function to generate cache key from arguments
    """
    def decorator(func: Callable) -> Callable:
        # Create cache
        cache = LRUCache(max_size=max_size, ttl_seconds=ttl_seconds)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = (args, tuple(sorted(kwargs.items())))
                
            # Check cache
            result = cache.get(cache_key)
            if result is not None:
                return result
                
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            cache.put(cache_key, result)
            
            return result
            
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = (args, tuple(sorted(kwargs.items())))
                
            # Check cache
            result = cache.get(cache_key)
            if result is not None:
                return result
                
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.put(cache_key, result)
            
            return result
            
        # Add cache access
        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper.cache = cache
        
        return wrapper
        
    return decorator


class ConnectionPool:
    """Generic connection pool for reusable resources."""
    
    def __init__(
        self,
        factory: Callable[[], Any],
        max_size: int = 10,
        min_size: int = 2,
        timeout: float = 30.0
    ):
        """
        Initialize connection pool.
        
        Args:
            factory: Function to create new connections
            max_size: Maximum pool size
            min_size: Minimum pool size
            timeout: Connection timeout
        """
        self.factory = factory
        self.max_size = max_size
        self.min_size = min_size
        self.timeout = timeout
        
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._size = 0
        self._acquiring = 0
        self._closed = False
        
    async def initialize(self):
        """Initialize pool with minimum connections."""
        for _ in range(self.min_size):
            conn = await self._create_connection()
            await self._pool.put(conn)
            
    async def _create_connection(self) -> Any:
        """Create new connection."""
        self._size += 1
        return await asyncio.wait_for(
            self.factory(),
            timeout=self.timeout
        )
        
    async def acquire(self) -> Any:
        """Acquire connection from pool."""
        if self._closed:
            raise RuntimeError("Pool is closed")
            
        self._acquiring += 1
        
        try:
            # Try to get from pool
            try:
                conn = self._pool.get_nowait()
                return conn
            except asyncio.QueueEmpty:
                pass
                
            # Create new if under limit
            if self._size < self.max_size:
                return await self._create_connection()
                
            # Wait for available connection
            return await asyncio.wait_for(
                self._pool.get(),
                timeout=self.timeout
            )
            
        finally:
            self._acquiring -= 1
            
    async def release(self, conn: Any):
        """Release connection back to pool."""
        if self._closed:
            await self._close_connection(conn)
            return
            
        try:
            self._pool.put_nowait(conn)
        except asyncio.QueueFull:
            # Pool is full, close connection
            await self._close_connection(conn)
            self._size -= 1
            
    async def _close_connection(self, conn: Any):
        """Close a connection."""
        if hasattr(conn, 'close'):
            await conn.close()
        elif hasattr(conn, 'disconnect'):
            await conn.disconnect()
            
    async def close(self):
        """Close all connections and pool."""
        self._closed = True
        
        # Close all connections in pool
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                await self._close_connection(conn)
            except asyncio.QueueEmpty:
                break
                
    def stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            "size": self._size,
            "available": self._pool.qsize(),
            "acquiring": self._acquiring,
            "max_size": self.max_size,
            "closed": self._closed
        }


class AsyncBatcher:
    """Batch async operations for efficiency."""
    
    def __init__(
        self,
        batch_func: Callable[[list], Any],
        max_batch_size: int = 100,
        max_wait_time: float = 0.1
    ):
        """
        Initialize async batcher.
        
        Args:
            batch_func: Function to process batch
            max_batch_size: Maximum items per batch
            max_wait_time: Maximum time to wait for batch
        """
        self.batch_func = batch_func
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        
        self._queue: asyncio.Queue = asyncio.Queue()
        self._batch_task: Optional[asyncio.Task] = None
        self._futures: Dict[Any, asyncio.Future] = {}
        
    async def start(self):
        """Start batch processing."""
        self._batch_task = asyncio.create_task(self._process_batches())
        
    async def stop(self):
        """Stop batch processing."""
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
                
    async def add(self, item: Any) -> Any:
        """Add item to batch and wait for result."""
        future = asyncio.Future()
        self._futures[id(item)] = future
        
        await self._queue.put(item)
        
        return await future
        
    async def _process_batches(self):
        """Process batches continuously."""
        while True:
            batch = []
            batch_ids = []
            
            try:
                # Collect batch
                deadline = time.time() + self.max_wait_time
                
                while len(batch) < self.max_batch_size:
                    timeout = max(0, deadline - time.time())
                    
                    try:
                        item = await asyncio.wait_for(
                            self._queue.get(),
                            timeout=timeout
                        )
                        batch.append(item)
                        batch_ids.append(id(item))
                        
                    except asyncio.TimeoutError:
                        break
                        
                if batch:
                    # Process batch
                    try:
                        results = await self.batch_func(batch)
                        
                        # Distribute results
                        for i, item_id in enumerate(batch_ids):
                            if item_id in self._futures:
                                future = self._futures.pop(item_id)
                                if isinstance(results, list) and i < len(results):
                                    future.set_result(results[i])
                                else:
                                    future.set_result(results)
                                    
                    except Exception as e:
                        # Distribute error
                        for item_id in batch_ids:
                            if item_id in self._futures:
                                future = self._futures.pop(item_id)
                                future.set_exception(e)
                                
            except asyncio.CancelledError:
                # Clean up pending futures
                for future in self._futures.values():
                    future.cancel()
                raise
                
            except Exception as e:
                logger.error(f"Batch processing error: {e}")


class ResourceManager:
    """Manage resource allocation and limits."""
    
    def __init__(self):
        """Initialize resource manager."""
        self._resources: Dict[str, Dict[str, Any]] = {}
        self._limits: Dict[str, Dict[str, Any]] = {}
        self._usage: Dict[str, Dict[str, float]] = {}
        
    def register_resource(
        self,
        name: str,
        limits: Dict[str, float],
        current_usage: Optional[Dict[str, float]] = None
    ):
        """Register a resource with limits."""
        self._limits[name] = limits
        self._usage[name] = current_usage or {k: 0.0 for k in limits}
        
    def can_allocate(self, name: str, requirements: Dict[str, float]) -> bool:
        """Check if resource allocation is possible."""
        if name not in self._limits:
            return True  # No limits defined
            
        limits = self._limits[name]
        usage = self._usage[name]
        
        for resource, required in requirements.items():
            if resource in limits:
                if usage.get(resource, 0) + required > limits[resource]:
                    return False
                    
        return True
        
    def allocate(self, name: str, requirements: Dict[str, float]) -> bool:
        """Allocate resources."""
        if not self.can_allocate(name, requirements):
            return False
            
        usage = self._usage[name]
        for resource, amount in requirements.items():
            usage[resource] = usage.get(resource, 0) + amount
            
        return True
        
    def release(self, name: str, resources: Dict[str, float]):
        """Release allocated resources."""
        if name in self._usage:
            usage = self._usage[name]
            for resource, amount in resources.items():
                usage[resource] = max(0, usage.get(resource, 0) - amount)
                
    def get_usage(self, name: str) -> Dict[str, float]:
        """Get current resource usage."""
        return self._usage.get(name, {}).copy()
        
    def get_utilization(self, name: str) -> Dict[str, float]:
        """Get resource utilization percentage."""
        if name not in self._limits:
            return {}
            
        limits = self._limits[name]
        usage = self._usage[name]
        
        return {
            resource: (usage.get(resource, 0) / limit) * 100
            for resource, limit in limits.items()
            if limit > 0
        }


# Global instances
_connection_pools: Dict[str, ConnectionPool] = {}
_resource_manager = ResourceManager()


def get_connection_pool(name: str) -> Optional[ConnectionPool]:
    """Get named connection pool."""
    return _connection_pools.get(name)


def register_connection_pool(
    name: str,
    factory: Callable,
    max_size: int = 10,
    min_size: int = 2
) -> ConnectionPool:
    """Register a new connection pool."""
    pool = ConnectionPool(factory, max_size, min_size)
    _connection_pools[name] = pool
    return pool


def get_resource_manager() -> ResourceManager:
    """Get global resource manager."""
    return _resource_manager
