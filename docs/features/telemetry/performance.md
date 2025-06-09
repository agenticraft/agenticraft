# Telemetry Performance Guide

Optimize AgentiCraft telemetry for minimal overhead and maximum insight.

## Performance Overview

AgentiCraft's telemetry is designed for production use with minimal impact:

| Configuration | Overhead | Use Case |
|--------------|----------|----------|
| Disabled | 0% | Testing, benchmarking |
| Basic (10% sampling) | <1% | Production default |
| Full (100% sampling) | 1-2% | Development, debugging |
| Debug mode | 2-5% | Troubleshooting only |

## Benchmarks

### Operation Overhead

Measured on typical hardware (Intel Xeon, 16 cores, 32GB RAM):

```python
# Baseline (no telemetry)
Agent execution: 50ms

# With telemetry
Basic telemetry (10% sampling): 50.3ms (+0.6%)
Full telemetry (100% sampling): 50.8ms (+1.6%)
Debug telemetry: 52.5ms (+5%)
```

### Memory Impact

```python
# Memory overhead per component
Base telemetry: ~10MB
Per 1000 spans in queue: ~5MB
Per exporter: ~2-5MB
Metrics storage: ~20MB (fixed)
```

## Optimization Strategies

### 1. Sampling Configuration

#### Basic Sampling

```python
# Production: Sample 10% of requests
telemetry = TelemetryConfig(
    enabled=True,
    sample_rate=0.1
)
```

#### Adaptive Sampling

```python
from agenticraft.telemetry import AdaptiveSampler

# Adjust sampling based on load
sampler = AdaptiveSampler(
    min_rate=0.01,      # Minimum 1%
    max_rate=1.0,       # Maximum 100%
    target_rps=1000,    # Target requests/second
    adjustment_period=60 # Adjust every minute
)

telemetry = TelemetryConfig(
    enabled=True,
    sampler=sampler
)
```

#### Priority-Based Sampling

```python
from agenticraft.telemetry import PrioritySampler

# Sample based on request priority
sampler = PrioritySampler(
    rules=[
        {"attribute": "priority", "value": "critical", "rate": 1.0},
        {"attribute": "priority", "value": "high", "rate": 0.5},
        {"attribute": "priority", "value": "normal", "rate": 0.1},
        {"attribute": "priority", "value": "low", "rate": 0.01}
    ],
    default_rate=0.1
)

telemetry = TelemetryConfig(sampler=sampler)
```

### 2. Batch Processing Optimization

#### Optimal Batch Sizes

```python
# For different traffic patterns

# Low traffic (<100 RPS)
telemetry = TelemetryConfig(
    batch_size=256,
    export_interval_ms=10000  # Export every 10s
)

# Medium traffic (100-1000 RPS)
telemetry = TelemetryConfig(
    batch_size=1024,
    export_interval_ms=5000   # Export every 5s
)

# High traffic (>1000 RPS)
telemetry = TelemetryConfig(
    batch_size=4096,
    export_interval_ms=2000,  # Export every 2s
    max_queue_size=16384
)
```

#### Dynamic Batching

```python
from agenticraft.telemetry import DynamicBatchConfig

# Automatically adjust batch parameters
telemetry = TelemetryConfig(
    dynamic_batching=DynamicBatchConfig(
        min_batch_size=128,
        max_batch_size=4096,
        min_interval_ms=1000,
        max_interval_ms=10000,
        target_queue_utilization=0.7
    )
)
```

### 3. Attribute Optimization

#### Limit Attribute Size

```python
from agenticraft.telemetry import AttributeLimiter

# Prevent large attributes from impacting performance
telemetry = TelemetryConfig(
    attribute_processors=[
        AttributeLimiter(
            max_length=1024,        # Truncate long strings
            max_array_items=100,    # Limit array sizes
            truncate_marker="..."   # Indicate truncation
        )
    ]
)
```

#### Selective Attributes

```python
# Only include essential attributes in production
if environment == "production":
    telemetry = TelemetryConfig(
        attribute_filters=[
            # Only keep specific attributes
            {"action": "keep", "attributes": [
                "agent.name", "error.type", "status", 
                "provider", "model"
            ]},
            # Remove all others
            {"action": "remove", "pattern": ".*"}
        ]
    )
```

### 4. Exporter Optimization

#### Async Export

```python
# Use async exporters for better performance
telemetry = TelemetryConfig(
    exporter_type="otlp",
    async_export=True,
    export_timeout_ms=30000,
    max_export_attempts=3
)
```

#### Connection Pooling

```python
# Reuse connections for OTLP
telemetry = TelemetryConfig(
    otlp_connection_pool_size=10,
    otlp_keepalive=True,
    otlp_keepalive_time_ms=10000
)
```

#### Compression

```python
# Enable compression for network efficiency
telemetry = TelemetryConfig(
    otlp_compression="gzip",  # Reduces payload by ~70%
    compression_level=6       # Balance speed/size
)
```

### 5. Memory Management

#### Span Limits

```python
# Prevent memory bloat from large spans
telemetry = TelemetryConfig(
    max_span_attributes=64,      # Limit attributes per span
    max_span_events=128,         # Limit events per span
    max_span_links=32,           # Limit span links
    max_attribute_length=2048    # Truncate long values
)
```

#### Queue Management

```python
# Configure queue behavior under pressure
telemetry = TelemetryConfig(
    max_queue_size=8192,
    queue_overflow_strategy="drop_oldest",  # or "drop_newest", "block"
    queue_warning_threshold=0.8  # Warn at 80% full
)
```

#### Memory Monitoring

```python
from agenticraft.telemetry import MemoryMonitor

# Monitor telemetry memory usage
monitor = MemoryMonitor(
    warning_threshold_mb=100,
    critical_threshold_mb=500,
    check_interval_seconds=60
)

monitor.on_warning = lambda usage: logger.warning(f"High telemetry memory: {usage}MB")
monitor.on_critical = lambda usage: telemetry.emergency_flush()
```

## Performance Profiling

### Measuring Telemetry Overhead

```python
import time
from agenticraft.telemetry import TelemetryConfig, measure_overhead

# Measure overhead for your workload
def sample_workload():
    agent = Agent(name="test")
    return agent.run("Hello world")

overhead = measure_overhead(
    workload=sample_workload,
    iterations=1000,
    telemetry_config=TelemetryConfig(enabled=True, sample_rate=0.1)
)

print(f"Telemetry overhead: {overhead.percentage}%")
print(f"Additional latency: {overhead.latency_ms}ms")
```

### Continuous Monitoring

```python
from agenticraft.telemetry import PerformanceMonitor

# Monitor telemetry performance in production
perf_monitor = PerformanceMonitor(
    target_overhead_percent=1.0,
    check_interval_seconds=300
)

@perf_monitor.on_threshold_exceeded
def handle_high_overhead(metrics):
    # Automatically reduce sampling
    current_rate = telemetry.get_sample_rate()
    new_rate = max(0.01, current_rate * 0.5)
    telemetry.set_sample_rate(new_rate)
    logger.warning(f"Reduced sampling to {new_rate} due to overhead")
```

## Production Configurations

### Minimal Overhead Configuration

```python
# <0.5% overhead for high-performance systems
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    
    # Aggressive sampling
    sample_rate=0.01,  # 1% sampling
    
    # Large batches, infrequent exports
    batch_size=8192,
    export_interval_ms=30000,  # 30 seconds
    
    # Minimal attributes
    auto_instrument_tools=False,
    auto_instrument_memory=False,
    include_system_metrics=False,
    
    # Efficient export
    otlp_compression="gzip",
    async_export=True,
    
    # Memory limits
    max_queue_size=8192,
    max_span_attributes=32
)
```

### Balanced Configuration

```python
# ~1% overhead with good observability
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    
    # Moderate sampling
    sample_rate=0.1,  # 10% sampling
    
    # Balanced batching
    batch_size=2048,
    export_interval_ms=5000,  # 5 seconds
    
    # Standard instrumentation
    auto_instrument=True,
    
    # Compression enabled
    otlp_compression="gzip",
    
    # Reasonable limits
    max_span_attributes=64,
    max_queue_size=16384
)
```

### Debug Configuration

```python
# 2-5% overhead, maximum visibility
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="console",
    
    # Full sampling
    sample_rate=1.0,
    
    # Frequent exports
    batch_size=128,
    export_interval_ms=1000,
    
    # All instrumentation
    auto_instrument=True,
    include_internal_spans=True,
    include_system_metrics=True,
    
    # No limits
    max_span_attributes=256,
    console_pretty_print=True
)
```

## Optimization Checklist

### Before Production

- [ ] Set appropriate sampling rate (usually 0.01-0.1)
- [ ] Configure batch size based on traffic
- [ ] Enable compression for network exporters
- [ ] Set memory limits to prevent bloat
- [ ] Remove debug attributes
- [ ] Test overhead with production workload
- [ ] Configure queue overflow strategy
- [ ] Set up monitoring for telemetry health

### Performance Tuning

- [ ] Monitor actual overhead percentage
- [ ] Check queue utilization
- [ ] Review attribute cardinality
- [ ] Optimize export intervals
- [ ] Enable connection pooling
- [ ] Configure timeouts appropriately
- [ ] Use async operations where possible
- [ ] Implement circuit breakers

### Memory Optimization

- [ ] Limit span attributes
- [ ] Set maximum queue size
- [ ] Configure attribute length limits
- [ ] Enable queue monitoring
- [ ] Implement memory alerts
- [ ] Use efficient serialization
- [ ] Clean up completed spans
- [ ] Monitor garbage collection

## Advanced Techniques

### Circuit Breaker Pattern

```python
from agenticraft.telemetry import CircuitBreaker

# Disable telemetry under extreme load
circuit_breaker = CircuitBreaker(
    failure_threshold=0.5,      # 50% export failures
    timeout_duration=60,        # Reset after 60 seconds
    half_open_requests=10       # Test with 10 requests
)

telemetry = TelemetryConfig(
    circuit_breaker=circuit_breaker,
    fallback_action="disable"   # or "console", "local_file"
)
```

### Tiered Sampling

```python
from agenticraft.telemetry import TieredSampler

# Different sampling rates at different levels
sampler = TieredSampler([
    # Always sample the first span in a trace
    {"level": "root", "rate": 0.1},
    
    # Sample child spans less frequently
    {"level": "child", "rate": 0.01},
    
    # Rarely sample deep spans
    {"level": "deep", "min_depth": 5, "rate": 0.001}
])

telemetry = TelemetryConfig(sampler=sampler)
```

### Resource-Based Throttling

```python
from agenticraft.telemetry import ResourceThrottler

# Reduce telemetry under resource pressure
throttler = ResourceThrottler(
    cpu_threshold=80,           # Reduce at 80% CPU
    memory_threshold=75,        # Reduce at 75% memory
    reduction_factor=0.5,       # Cut sampling in half
    check_interval=30           # Check every 30 seconds
)

telemetry = TelemetryConfig(
    resource_throttler=throttler
)
```

## Benchmarking Your Configuration

```python
from agenticraft.telemetry import benchmark_configuration

# Test different configurations
configurations = [
    TelemetryConfig(enabled=False),
    TelemetryConfig(enabled=True, sample_rate=0.01),
    TelemetryConfig(enabled=True, sample_rate=0.1),
    TelemetryConfig(enabled=True, sample_rate=1.0)
]

# Run benchmark
results = benchmark_configuration(
    configurations=configurations,
    workload=your_typical_workload,
    iterations=10000,
    warmup_iterations=1000
)

# Display results
for config, result in results.items():
    print(f"Configuration: {config}")
    print(f"  Overhead: {result.overhead_percent}%")
    print(f"  P50 latency: {result.p50_ms}ms")
    print(f"  P99 latency: {result.p99_ms}ms")
    print(f"  Memory usage: {result.memory_mb}MB")
```

## Troubleshooting Performance Issues

### High CPU Usage

1. Check sampling rate
2. Reduce batch frequency
3. Disable console exporter in production
4. Check for span loops

### High Memory Usage

1. Reduce queue size
2. Limit span attributes
3. Enable memory limits
4. Check for span leaks

### Network Congestion

1. Enable compression
2. Increase batch size
3. Reduce export frequency
4. Use local collector

### Export Timeouts

1. Increase timeout values
2. Reduce batch size
3. Check network latency
4. Use async exports

## Best Practices Summary

1. **Start Conservative**: Begin with low sampling (1-10%)
2. **Monitor Overhead**: Track actual impact in production
3. **Use Batching**: Efficient batching reduces overhead
4. **Enable Compression**: Reduces network usage by ~70%
5. **Limit Attributes**: Prevent cardinality explosion
6. **Async Operations**: Use async exports when possible
7. **Resource Limits**: Set memory and queue limits
8. **Gradual Rollout**: Increase sampling gradually
9. **Profile First**: Benchmark with your workload
10. **Have Fallbacks**: Plan for telemetry failures

## Next Steps

- [Configuration Guide](configuration.md) - Detailed configuration options
- [Integration Guide](integration.md) - Platform-specific optimizations
- [Metrics Reference](metrics-reference.md) - Understanding overhead metrics
