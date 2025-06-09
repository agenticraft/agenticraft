# Telemetry & Observability Guide

AgentiCraft provides comprehensive telemetry and observability features built on OpenTelemetry standards, enabling you to monitor, debug, and optimize your AI agent applications in production.

## Overview

The telemetry system provides:
- **Distributed Tracing**: Track request flows across multiple agents and services
- **Metrics Collection**: Monitor performance, token usage, and error rates
- **Multiple Exporters**: Support for Jaeger, Prometheus, console output, and more
- **Auto-instrumentation**: Automatic tracking with minimal code changes
- **Low Overhead**: Less than 1% performance impact when enabled

## Quick Start

### Basic Setup

```python
from agenticraft.telemetry import TelemetryConfig

# Enable telemetry with console output (development)
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="console",
    service_name="my-agent-app"
)
telemetry.initialize()

# Your agents are now automatically instrumented!
from agenticraft import Agent

agent = Agent(name="MyAgent")
response = await agent.arun("Hello, world!")
```

### Production Setup with OTLP

```python
from agenticraft.telemetry import TelemetryConfig

# Configure for production with Jaeger
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    otlp_endpoint="localhost:4317",
    service_name="production-agent-app",
    auto_instrument=True,
    sample_rate=0.1  # Sample 10% of requests
)
telemetry.initialize()
```

## Core Concepts

### Spans and Traces

A **span** represents a single operation within your application. Multiple spans form a **trace** that shows the complete request flow.

```python
from agenticraft.telemetry import create_span

# Automatic span creation
agent = Agent(name="ResearchAgent")
response = await agent.arun("Research AI trends")  # Creates spans automatically

# Manual span creation for custom operations
with create_span("custom.data_processing") as span:
    span.set_attribute("data.size", len(data))
    span.set_attribute("data.type", "research")
    
    processed_data = process_data(data)
    
    span.set_attribute("data.processed_items", len(processed_data))
```

### Metrics

AgentiCraft automatically collects key metrics:

```python
from agenticraft.telemetry import record_metric, MetricType

# Automatic metrics (collected by framework)
# - agenticraft.tokens.used
# - agenticraft.latency.ms
# - agenticraft.errors.count
# - agenticraft.memory.hits

# Custom metrics
record_metric(
    "custom.processing.items",
    value=42,
    metric_type=MetricType.COUNTER,
    attributes={"processor": "research"}
)

record_metric(
    "custom.queue.size",
    value=queue.size(),
    metric_type=MetricType.GAUGE
)
```

## Configuration Options

### TelemetryConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | bool | False | Enable/disable telemetry |
| `exporter_type` | str | "console" | Exporter type: "console", "otlp", "prometheus" |
| `service_name` | str | "agenticraft" | Service name for identification |
| `otlp_endpoint` | str | "localhost:4317" | OTLP collector endpoint |
| `prometheus_port` | int | 8000 | Port for Prometheus metrics |
| `auto_instrument` | bool | True | Enable automatic instrumentation |
| `sample_rate` | float | 1.0 | Sampling rate (0.0-1.0) |
| `batch_size` | int | 512 | Batch size for span export |
| `export_interval_ms` | int | 5000 | Export interval in milliseconds |

### Environment Variables

```bash
# Enable telemetry
export AGENTICRAFT_TELEMETRY_ENABLED=true

# Configure exporter
export AGENTICRAFT_EXPORTER_TYPE=otlp
export AGENTICRAFT_OTLP_ENDPOINT=localhost:4317

# Set service name
export AGENTICRAFT_SERVICE_NAME=my-agent-app

# Configure sampling
export AGENTICRAFT_SAMPLE_RATE=0.1
```

## Exporters

### Console Exporter (Development)

Outputs telemetry data to console for debugging:

```python
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="console",
    console_pretty_print=True
)
```

Output example:
```
[TRACE] agent.execute (duration: 1250ms)
  ├─ agent.name: ResearchAgent
  ├─ agent.operation: execute
  ├─ llm.provider: openai
  ├─ llm.model: gpt-4
  └─ tokens.total: 850
```

### OTLP Exporter (Production)

Sends data to OpenTelemetry collectors or Jaeger:

```python
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    otlp_endpoint="localhost:4317",
    otlp_headers={"api-key": "your-key"}  # Optional auth
)
```

### Prometheus Exporter (Metrics)

Exposes metrics endpoint for Prometheus scraping:

```python
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="prometheus",
    prometheus_port=8000
)
```

Access metrics at `http://localhost:8000/metrics`

## Auto-Instrumentation

When `auto_instrument=True`, AgentiCraft automatically tracks:

### Agent Operations
- Agent initialization
- Message processing
- Tool execution
- Memory operations

### LLM Provider Calls
- Request/response tracking
- Token usage
- Latency measurements
- Error tracking

### Tool Execution
- Tool discovery
- Execution time
- Input/output size
- Success/failure rates

### Memory Operations
- Store/retrieve operations
- Search queries
- Hit/miss rates
- Operation latency

## Custom Instrumentation

### Creating Custom Spans

```python
from agenticraft.telemetry import create_span

async def analyze_document(doc: str):
    with create_span("document.analysis") as span:
        # Add attributes
        span.set_attribute("document.size", len(doc))
        span.set_attribute("document.type", "pdf")
        
        # Track events
        span.add_event("Starting analysis")
        
        try:
            result = await perform_analysis(doc)
            span.set_attribute("analysis.success", True)
            span.set_attribute("analysis.findings", len(result))
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            raise
```

### Using Decorators

```python
from agenticraft.telemetry.decorators import trace_method

class DataProcessor:
    @trace_method("data.process")
    async def process(self, data: List[str]):
        # Automatically traced!
        return [item.upper() for item in data]
    
    @trace_method("data.validate", 
                  attributes={"validator": "strict"})
    async def validate(self, data: Any):
        # Custom attributes included
        return is_valid(data)
```

### Context Propagation

```python
from agenticraft.telemetry import get_current_span, create_span

# Parent operation
with create_span("parent.operation") as parent:
    parent.set_attribute("request.id", request_id)
    
    # Child operations inherit context
    async def child_operation():
        with create_span("child.operation") as child:
            # Automatically linked to parent
            child.set_attribute("child.data", "value")
            
    await child_operation()
```

## Metrics Deep Dive

### Token Usage Metrics

```python
# Automatically collected per provider/model
agenticraft.tokens.prompt     # Prompt tokens
agenticraft.tokens.completion # Completion tokens  
agenticraft.tokens.total      # Total tokens

# Attributes:
# - provider: openai, anthropic, ollama
# - model: gpt-4, claude-3, etc.
# - agent: agent name
```

### Latency Metrics

```python
# Operation latency histograms
agenticraft.latency.agent      # Agent operations
agenticraft.latency.tool       # Tool execution
agenticraft.latency.memory     # Memory operations
agenticraft.latency.provider   # LLM provider calls

# Percentiles available: p50, p90, p95, p99
```

### Error Metrics

```python
# Error counters by operation
agenticraft.errors.count

# Attributes:
# - operation: agent.execute, tool.run, etc.
# - error_type: exception class name
# - agent: agent name (if applicable)
```

### Custom Business Metrics

```python
from agenticraft.telemetry import create_histogram, create_counter

# Create custom metrics
doc_counter = create_counter(
    "documents.processed",
    description="Number of documents processed"
)

processing_time = create_histogram(
    "processing.duration",
    description="Document processing time",
    unit="ms"
)

# Use in your code
async def process_document(doc):
    start = time.time()
    
    # Process document
    result = await analyze(doc)
    
    # Record metrics
    doc_counter.add(1, {"doc_type": doc.type})
    processing_time.record(
        (time.time() - start) * 1000,
        {"doc_type": doc.type, "size_bucket": get_size_bucket(doc)}
    )
    
    return result
```

## Grafana Dashboard

AgentiCraft includes a pre-configured Grafana dashboard. Import it from:

```bash
agenticraft/telemetry/grafana_dashboard.json
```

Dashboard panels include:
- Request rate and latency
- Token usage by provider/model
- Error rate and types
- Memory hit rates
- Agent performance comparison
- Tool execution metrics

## Performance Considerations

### Overhead

Telemetry adds minimal overhead:
- **Disabled**: 0% overhead
- **Enabled with sampling**: <1% overhead
- **Full tracing**: 1-2% overhead

### Optimization Tips

1. **Use Sampling in Production**
   ```python
   telemetry = TelemetryConfig(
       sample_rate=0.1  # Sample 10% of requests
   )
   ```

2. **Batch Exports**
   ```python
   telemetry = TelemetryConfig(
       batch_size=1024,
       export_interval_ms=10000  # Export every 10s
   )
   ```

3. **Disable in Tests**
   ```python
   # In test configuration
   telemetry = TelemetryConfig(enabled=False)
   ```

4. **Filter Sensitive Data**
   ```python
   from agenticraft.telemetry import add_span_processor
   
   def filter_sensitive_attributes(span):
       # Remove sensitive data
       span.attributes.pop("user.email", None)
       span.attributes.pop("api.key", None)
   
   add_span_processor(filter_sensitive_attributes)
   ```

## Troubleshooting

### Common Issues

**No telemetry data appearing:**
- Check telemetry is enabled: `AGENTICRAFT_TELEMETRY_ENABLED=true`
- Verify exporter endpoint is reachable
- Check for errors in console output
- Ensure `telemetry.initialize()` is called

**High memory usage:**
- Reduce batch size
- Increase export interval
- Enable sampling
- Check for span leaks in custom code

**Missing spans:**
- Verify auto-instrumentation is enabled
- Check sampling rate (might be filtering spans)
- Ensure async context is properly propagated
- Look for exceptions that might interrupt tracing

### Debug Mode

Enable debug logging:

```python
import logging

logging.getLogger("agenticraft.telemetry").setLevel(logging.DEBUG)

telemetry = TelemetryConfig(
    enabled=True,
    debug=True  # Extra debug output
)
```

## Examples

See the `examples/telemetry/` directory for complete examples:

- **basic_telemetry.py**: Simple telemetry setup
- **otlp_jaeger_example.py**: Jaeger integration
- **prometheus_metrics.py**: Metrics endpoint setup
- **custom_instrumentation.py**: Custom spans and metrics
- **performance_monitoring.py**: Performance analysis

## Best Practices

1. **Use Semantic Naming**
   ```python
   # Good
   with create_span("document.analyze.pdf"):
   
   # Bad  
   with create_span("process"):
   ```

2. **Add Meaningful Attributes**
   ```python
   span.set_attribute("document.pages", page_count)
   span.set_attribute("document.language", "en")
   span.set_attribute("analysis.algorithm", "nlp-v2")
   ```

3. **Track Business Metrics**
   ```python
   # Track what matters to your application
   record_metric("revenue.processed", amount)
   record_metric("users.active", count)
   record_metric("quality.score", score)
   ```

4. **Use Span Events for Milestones**
   ```python
   with create_span("long.operation") as span:
       span.add_event("Phase 1 complete")
       # ... more work ...
       span.add_event("Phase 2 complete")
   ```

5. **Handle Errors Properly**
   ```python
   try:
       result = await risky_operation()
   except Exception as e:
       span.record_exception(e)
       span.set_status(StatusCode.ERROR)
       # Still raise the exception
       raise
   ```

## Next Steps

- [API Reference](api-reference.md) - Detailed API documentation
- [Configuration Guide](configuration.md) - Advanced configuration options
- [Integration Guide](integration.md) - Integrate with monitoring tools
- [Metrics Reference](metrics-reference.md) - Complete metrics catalog
- [Performance Guide](performance.md) - Optimization and best practices
