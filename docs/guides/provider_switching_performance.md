# Provider Switching Performance Optimization Guide

## Overview

This guide covers performance considerations and optimization strategies for provider switching in AgentiCraft v0.1.1.

## Performance Metrics

### Provider Switching Overhead

| Operation | Time | Impact |
|-----------|------|--------|
| Provider instance creation | ~1ms | Negligible |
| Credential validation | ~10ms | Minimal |
| First API call (cold) | 100-500ms | Noticeable |
| Subsequent API calls | Provider-dependent | Varies |

### Provider Response Times

| Provider | Model | First Token | Full Response | Tokens/sec |
|----------|-------|-------------|---------------|------------|
| OpenAI | GPT-3.5 | 200-500ms | 0.5-2s | 50-100 |
| OpenAI | GPT-4 | 500-2000ms | 2-10s | 20-40 |
| Anthropic | Claude-3-Opus | 300-1000ms | 2-5s | 30-60 |
| Anthropic | Claude-3-Sonnet | 200-500ms | 1-3s | 40-80 |
| Ollama | Llama2 (M1 Mac) | 50-200ms | 0.5-5s | 10-50 |
| Ollama | Llama2 (GPU) | 10-50ms | 0.1-1s | 100-500 |

## Optimization Strategies

### 1. Provider Instance Caching

Currently, AgentiCraft creates a new provider instance on each switch. For frequent switching, implement caching:

```python
class CachedProviderAgent(Agent):
    """Agent with provider instance caching."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._provider_cache = {}
        self._cache_size = 5  # Maximum cached providers
    
    def set_provider(self, provider_name: str, **kwargs):
        """Set provider with caching."""
        cache_key = f"{provider_name}:{kwargs.get('model', 'default')}"
        
        # Check cache
        if cache_key in self._provider_cache:
            self._provider = self._provider_cache[cache_key]
            self.config.model = kwargs.get('model', self.config.model)
            return
        
        # Create new provider
        super().set_provider(provider_name, **kwargs)
        
        # Cache it
        self._provider_cache[cache_key] = self._provider
        
        # Evict oldest if cache is full
        if len(self._provider_cache) > self._cache_size:
            oldest = next(iter(self._provider_cache))
            del self._provider_cache[oldest]
```

### 2. Connection Pooling

For high-throughput applications, use connection pooling:

```python
import httpx

# Global connection pools
_connection_pools = {
    "openai": httpx.AsyncClient(
        limits=httpx.Limits(max_connections=100, max_keepalive=20),
        timeout=httpx.Timeout(30.0)
    ),
    "anthropic": httpx.AsyncClient(
        limits=httpx.Limits(max_connections=50, max_keepalive=10),
        timeout=httpx.Timeout(60.0)
    ),
}

class PooledProvider(BaseProvider):
    """Provider using connection pooling."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = _connection_pools.get(self.name)
```

### 3. Parallel Provider Warm-up

Pre-warm providers during initialization:

```python
class FastStartAgent(Agent):
    """Agent with pre-warmed providers."""
    
    async def initialize_providers(self, providers: List[Tuple[str, str]]):
        """Pre-warm multiple providers in parallel."""
        import asyncio
        
        async def warm_provider(provider_name: str, model: str):
            try:
                self.set_provider(provider_name, model=model)
                # Make a minimal request to establish connection
                await self.arun("Hi", max_tokens=1)
            except Exception:
                pass  # Ignore warm-up failures
        
        # Warm all providers in parallel
        await asyncio.gather(*[
            warm_provider(provider, model)
            for provider, model in providers
        ])

# Usage
agent = FastStartAgent()
await agent.initialize_providers([
    ("openai", "gpt-3.5-turbo"),
    ("anthropic", "claude-3-sonnet-20240229"),
    ("ollama", "llama2")
])
```

### 4. Smart Model Selection

Choose models based on task requirements:

```python
class PerformanceOptimizedAgent:
    """Agent that selects models for optimal performance."""
    
    # Model performance profiles
    MODEL_PROFILES = {
        # (provider, model): (latency_ms, tokens_per_sec, cost_per_1k)
        ("openai", "gpt-3.5-turbo"): (500, 75, 0.002),
        ("openai", "gpt-4"): (2000, 30, 0.03),
        ("anthropic", "claude-3-haiku-20240307"): (300, 100, 0.00025),
        ("anthropic", "claude-3-sonnet-20240229"): (1000, 60, 0.003),
        ("ollama", "llama2"): (100, 30, 0),
    }
    
    def select_optimal_model(
        self,
        max_latency_ms: int = 5000,
        min_quality_score: float = 0.7,
        max_cost_per_1k: float = 0.01
    ) -> Tuple[str, str]:
        """Select optimal model based on constraints."""
        candidates = []
        
        for (provider, model), (latency, tps, cost) in self.MODEL_PROFILES.items():
            if (latency <= max_latency_ms and cost <= max_cost_per_1k):
                # Simple quality score (you'd want a better metric)
                quality = 0.5 if "3.5" in model or "llama" in model else 0.9
                if quality >= min_quality_score:
                    candidates.append((provider, model, latency, cost))
        
        # Sort by latency (or implement more complex scoring)
        candidates.sort(key=lambda x: x[2])
        
        if candidates:
            return candidates[0][0], candidates[0][1]
        return "openai", "gpt-3.5-turbo"  # Default fallback
```

### 5. Response Caching

Cache responses for identical queries:

```python
from functools import lru_cache
import hashlib

class CachedAgent(Agent):
    """Agent with response caching."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._response_cache = {}
        self._cache_ttl = 3600  # 1 hour
    
    def _get_cache_key(self, prompt: str, provider: str, model: str) -> str:
        """Generate cache key for prompt."""
        content = f"{provider}:{model}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def arun(self, prompt: str, **kwargs) -> AgentResponse:
        """Run with caching."""
        # Check if caching is appropriate
        if kwargs.get("temperature", 0.7) > 0.1:
            # Don't cache non-deterministic responses
            return await super().arun(prompt, **kwargs)
        
        # Check cache
        provider_name = self.provider.__class__.__name__.lower().replace("provider", "")
        cache_key = self._get_cache_key(prompt, provider_name, self.config.model)
        
        if cache_key in self._response_cache:
            cached = self._response_cache[cache_key]
            if time.time() - cached["timestamp"] < self._cache_ttl:
                return cached["response"]
        
        # Get fresh response
        response = await super().arun(prompt, **kwargs)
        
        # Cache it
        self._response_cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
        
        return response
```

### 6. Batch Processing

Process multiple requests efficiently:

```python
class BatchProcessingAgent(Agent):
    """Agent optimized for batch processing."""
    
    async def arun_batch(
        self,
        prompts: List[str],
        max_concurrent: int = 5
    ) -> List[AgentResponse]:
        """Process multiple prompts concurrently."""
        import asyncio
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_one(prompt: str) -> AgentResponse:
            async with semaphore:
                return await self.arun(prompt)
        
        # Process all prompts concurrently with rate limiting
        responses = await asyncio.gather(*[
            process_one(prompt) for prompt in prompts
        ])
        
        return responses

# Usage
agent = BatchProcessingAgent()
prompts = ["Question 1", "Question 2", "Question 3", ...]
responses = await agent.arun_batch(prompts, max_concurrent=3)
```

## Monitoring Performance

### Basic Metrics Collection

```python
import time
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class PerformanceMetrics:
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    first_token_ms: float
    success: bool

class MonitoredAgent(Agent):
    """Agent with performance monitoring."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metrics: List[PerformanceMetrics] = []
    
    async def arun(self, prompt: str, **kwargs) -> AgentResponse:
        """Run with performance monitoring."""
        start_time = time.perf_counter()
        first_token_time = None
        
        try:
            # For streaming responses (future)
            if kwargs.get("stream"):
                # Track time to first token
                pass
            
            response = await super().arun(prompt, **kwargs)
            
            # Record metrics
            latency = (time.perf_counter() - start_time) * 1000
            
            metrics = PerformanceMetrics(
                provider=self.provider.__class__.__name__,
                model=self.config.model,
                prompt_tokens=response.metadata.get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=response.metadata.get("usage", {}).get("completion_tokens", 0),
                latency_ms=latency,
                first_token_ms=first_token_time or latency,
                success=True
            )
            
            self.metrics.append(metrics)
            return response
            
        except Exception as e:
            # Record failure
            latency = (time.perf_counter() - start_time) * 1000
            metrics = PerformanceMetrics(
                provider=self.provider.__class__.__name__,
                model=self.config.model,
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=latency,
                first_token_ms=latency,
                success=False
            )
            self.metrics.append(metrics)
            raise
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not self.metrics:
            return {}
        
        by_provider = {}
        for metric in self.metrics:
            key = f"{metric.provider}/{metric.model}"
            if key not in by_provider:
                by_provider[key] = {
                    "count": 0,
                    "success_count": 0,
                    "total_latency": 0,
                    "total_tokens": 0,
                    "latencies": []
                }
            
            stats = by_provider[key]
            stats["count"] += 1
            if metric.success:
                stats["success_count"] += 1
            stats["total_latency"] += metric.latency_ms
            stats["total_tokens"] += metric.prompt_tokens + metric.completion_tokens
            stats["latencies"].append(metric.latency_ms)
        
        # Calculate statistics
        summary = {}
        for key, stats in by_provider.items():
            latencies = sorted(stats["latencies"])
            summary[key] = {
                "requests": stats["count"],
                "success_rate": stats["success_count"] / stats["count"],
                "avg_latency_ms": stats["total_latency"] / stats["count"],
                "p50_latency_ms": latencies[len(latencies) // 2] if latencies else 0,
                "p95_latency_ms": latencies[int(len(latencies) * 0.95)] if latencies else 0,
                "total_tokens": stats["total_tokens"],
                "tokens_per_request": stats["total_tokens"] / stats["count"]
            }
        
        return summary
```

### OpenTelemetry Integration

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer(__name__)

class TelemetryAgent(Agent):
    """Agent with OpenTelemetry integration."""
    
    async def arun(self, prompt: str, **kwargs) -> AgentResponse:
        """Run with distributed tracing."""
        provider_name = self.provider.__class__.__name__
        
        with tracer.start_as_current_span(
            "agent.run",
            attributes={
                "agent.name": self.name,
                "provider.name": provider_name,
                "model.name": self.config.model,
                "prompt.length": len(prompt),
            }
        ) as span:
            try:
                response = await super().arun(prompt, **kwargs)
                
                # Add response attributes
                span.set_attributes({
                    "response.length": len(response.content),
                    "tokens.prompt": response.metadata.get("usage", {}).get("prompt_tokens", 0),
                    "tokens.completion": response.metadata.get("usage", {}).get("completion_tokens", 0),
                })
                
                span.set_status(Status(StatusCode.OK))
                return response
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
```

## Best Practices Summary

1. **Cache Provider Instances** for frequently used configurations
2. **Use Connection Pooling** for high-throughput applications  
3. **Pre-warm Providers** during initialization
4. **Select Models Intelligently** based on task requirements
5. **Implement Response Caching** for deterministic queries
6. **Process in Batches** when handling multiple requests
7. **Monitor Performance** to identify bottlenecks
8. **Use Distributed Tracing** for production debugging

## Benchmarking Script

```python
# benchmark_providers.py
import asyncio
import time
from statistics import mean, stdev

from agenticraft import Agent

async def benchmark_provider(provider: str, model: str, prompts: List[str]) -> Dict:
    """Benchmark a specific provider/model combination."""
    agent = Agent()
    agent.set_provider(provider, model=model)
    
    latencies = []
    errors = 0
    
    for prompt in prompts:
        try:
            start = time.perf_counter()
            await agent.arun(prompt)
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)
        except Exception:
            errors += 1
    
    return {
        "provider": provider,
        "model": model,
        "requests": len(prompts),
        "errors": errors,
        "avg_latency_ms": mean(latencies) if latencies else 0,
        "std_dev_ms": stdev(latencies) if len(latencies) > 1 else 0,
        "min_latency_ms": min(latencies) if latencies else 0,
        "max_latency_ms": max(latencies) if latencies else 0,
    }

# Run benchmarks
async def main():
    test_prompts = [
        "What is 2+2?",
        "Explain quantum computing in one sentence",
        "Write a haiku about programming",
    ]
    
    configurations = [
        ("openai", "gpt-3.5-turbo"),
        ("openai", "gpt-4"),
        ("anthropic", "claude-3-sonnet-20240229"),
        ("ollama", "llama2"),
    ]
    
    results = []
    for provider, model in configurations:
        try:
            result = await benchmark_provider(provider, model, test_prompts)
            results.append(result)
            print(f"{provider}/{model}: {result['avg_latency_ms']:.0f}ms avg")
        except Exception as e:
            print(f"{provider}/{model}: Failed - {e}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
```

This completes the performance optimization guide for provider switching in AgentiCraft v0.1.1.
