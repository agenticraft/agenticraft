# Telemetry API Reference

Complete API documentation for AgentiCraft's telemetry system.

## Core Classes

### TelemetryConfig

Configuration class for telemetry initialization.

```python
class TelemetryConfig:
    """Telemetry configuration and initialization.
    
    Args:
        enabled (bool): Enable/disable telemetry. Default: False
        exporter_type (str): Type of exporter to use. Options: "console", "otlp", "prometheus"
        service_name (str): Service name for identification. Default: "agenticraft"
        otlp_endpoint (str): OTLP collector endpoint. Default: "localhost:4317"
        otlp_headers (dict): Optional headers for OTLP exporter
        prometheus_port (int): Port for Prometheus metrics endpoint. Default: 8000
        auto_instrument (bool): Enable automatic instrumentation. Default: True
        sample_rate (float): Sampling rate (0.0-1.0). Default: 1.0
        batch_size (int): Batch size for span export. Default: 512
        export_interval_ms (int): Export interval in milliseconds. Default: 5000
        console_pretty_print (bool): Pretty print console output. Default: True
        debug (bool): Enable debug logging. Default: False
    """
    
    def initialize(self) -> None:
        """Initialize telemetry with configured settings."""
        
    def shutdown(self) -> None:
        """Shutdown telemetry and flush remaining data."""
```

### Example Usage

```python
from agenticraft.telemetry import TelemetryConfig

# Development configuration
config = TelemetryConfig(
    enabled=True,
    exporter_type="console",
    debug=True
)
config.initialize()

# Production configuration
config = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    otlp_endpoint="telemetry.company.com:4317",
    otlp_headers={"Authorization": "Bearer token"},
    sample_rate=0.1,
    auto_instrument=True
)
config.initialize()

# Cleanup on shutdown
config.shutdown()
```

## Tracing API

### create_span

Create a new span for tracing operations.

```python
def create_span(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None,
    links: Optional[List[Link]] = None
) -> Span:
    """Create a new span.
    
    Args:
        name: Span name (use dot notation: "component.operation")
        kind: Span kind (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
        attributes: Initial span attributes
        links: Links to other spans
        
    Returns:
        OpenTelemetry Span object
        
    Example:
        with create_span("database.query", attributes={"db.name": "users"}):
            result = await db.query("SELECT * FROM users")
    """
```

### get_current_span

Get the currently active span.

```python
def get_current_span() -> Optional[Span]:
    """Get the current active span.
    
    Returns:
        Current span or None if no span is active
        
    Example:
        span = get_current_span()
        if span:
            span.add_event("Processing started")
    """
```

### Span Methods

```python
class Span:
    """OpenTelemetry span with extended functionality."""
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the span."""
        
    def set_attributes(self, attributes: Dict[str, Any]) -> None:
        """Set multiple attributes at once."""
        
    def add_event(
        self, 
        name: str, 
        attributes: Optional[Dict[str, Any]] = None,
        timestamp: Optional[int] = None
    ) -> None:
        """Add an event to the span timeline."""
        
    def set_status(self, status: Status) -> None:
        """Set the span status (OK, ERROR)."""
        
    def record_exception(
        self,
        exception: Exception,
        attributes: Optional[Dict[str, Any]] = None,
        timestamp: Optional[int] = None,
        escaped: bool = False
    ) -> None:
        """Record an exception with stacktrace."""
```

### Example: Comprehensive Span Usage

```python
from agenticraft.telemetry import create_span
from opentelemetry.trace import StatusCode

async def process_document(doc_id: str, content: str):
    with create_span(
        "document.process",
        attributes={
            "document.id": doc_id,
            "document.size": len(content),
            "processor.version": "2.0"
        }
    ) as span:
        try:
            # Track progress
            span.add_event("Validation started")
            validate_document(content)
            span.add_event("Validation completed")
            
            # Process document
            span.add_event("Processing started")
            result = await heavy_processing(content)
            
            # Add result attributes
            span.set_attributes({
                "result.score": result.score,
                "result.category": result.category,
                "processing.duration_ms": result.duration
            })
            
            span.add_event("Processing completed successfully")
            span.set_status(StatusCode.OK)
            
            return result
            
        except ValidationError as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, "Validation failed")
            raise
            
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, "Processing failed")
            raise
```

## Metrics API

### record_metric

Record a metric value.

```python
def record_metric(
    name: str,
    value: Union[int, float],
    metric_type: MetricType = MetricType.COUNTER,
    attributes: Optional[Dict[str, Any]] = None,
    unit: str = ""
) -> None:
    """Record a metric value.
    
    Args:
        name: Metric name (use dot notation)
        value: Metric value
        metric_type: Type of metric (COUNTER, GAUGE, HISTOGRAM)
        attributes: Metric attributes/labels
        unit: Unit of measurement
        
    Example:
        record_metric(
            "documents.processed",
            value=1,
            metric_type=MetricType.COUNTER,
            attributes={"type": "pdf", "size": "large"}
        )
    """
```

### MetricType Enum

```python
class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"      # Monotonically increasing value
    GAUGE = "gauge"          # Point-in-time value
    HISTOGRAM = "histogram"  # Distribution of values
```

### Creating Metric Instruments

```python
def create_counter(
    name: str,
    description: str = "",
    unit: str = ""
) -> Counter:
    """Create a counter metric.
    
    Args:
        name: Metric name
        description: Human-readable description
        unit: Unit of measurement
        
    Returns:
        Counter instrument
        
    Example:
        request_counter = create_counter(
            "http.requests",
            description="Total HTTP requests",
            unit="1"
        )
        request_counter.add(1, {"method": "GET", "status": 200})
    """

def create_histogram(
    name: str,
    description: str = "",
    unit: str = "",
    boundaries: Optional[List[float]] = None
) -> Histogram:
    """Create a histogram metric.
    
    Args:
        name: Metric name
        description: Human-readable description
        unit: Unit of measurement
        boundaries: Histogram bucket boundaries
        
    Returns:
        Histogram instrument
        
    Example:
        latency_histogram = create_histogram(
            "http.request.duration",
            description="HTTP request latency",
            unit="ms",
            boundaries=[0, 10, 25, 50, 100, 250, 500, 1000]
        )
        latency_histogram.record(42.5, {"endpoint": "/api/users"})
    """

def create_gauge(
    name: str,
    description: str = "",
    unit: str = ""
) -> ObservableGauge:
    """Create a gauge metric.
    
    Args:
        name: Metric name
        description: Human-readable description
        unit: Unit of measurement
        
    Returns:
        ObservableGauge instrument
        
    Example:
        def get_queue_size():
            return queue.size()
            
        queue_gauge = create_gauge(
            "queue.size",
            description="Current queue size"
        )
        queue_gauge.add_callback(get_queue_size)
    """
```

### Automatic Metrics

AgentiCraft automatically records these metrics:

```python
# Token usage
"agenticraft.tokens.prompt"      # Prompt tokens used
"agenticraft.tokens.completion"  # Completion tokens used
"agenticraft.tokens.total"       # Total tokens used

# Latency
"agenticraft.latency.agent"      # Agent operation latency
"agenticraft.latency.tool"       # Tool execution latency
"agenticraft.latency.provider"   # LLM provider latency
"agenticraft.latency.memory"     # Memory operation latency

# Errors
"agenticraft.errors.count"       # Error count by operation

# Memory
"agenticraft.memory.hits"        # Memory cache hits
"agenticraft.memory.misses"      # Memory cache misses
"agenticraft.memory.operations"  # Total memory operations
```

## Decorators

### @trace_method

Decorator for tracing class methods.

```python
from agenticraft.telemetry.decorators import trace_method

class DocumentProcessor:
    @trace_method("processor.analyze")
    async def analyze(self, document: str) -> dict:
        """This method is automatically traced."""
        return {"length": len(document)}
    
    @trace_method(
        "processor.validate",
        attributes={"validator": "strict", "version": "2.0"}
    )
    def validate(self, document: str) -> bool:
        """Traced with custom attributes."""
        return len(document) > 0
```

### @trace_function

Decorator for tracing standalone functions.

```python
from agenticraft.telemetry.decorators import trace_function

@trace_function("utils.calculate_score")
def calculate_score(data: dict) -> float:
    """This function is automatically traced."""
    return sum(data.values()) / len(data)

@trace_function(
    "utils.process_batch",
    capture_args=True,  # Include function arguments as span attributes
    capture_result=True  # Include return value as span attribute
)
async def process_batch(items: List[str]) -> int:
    """Traced with argument and result capture."""
    processed = [item.upper() for item in items]
    return len(processed)
```

### @timed_metric

Decorator for recording execution time metrics.

```python
from agenticraft.telemetry.decorators import timed_metric

@timed_metric("custom.processing.duration", unit="ms")
async def process_data(data: dict) -> dict:
    """Execution time is automatically recorded."""
    await asyncio.sleep(0.1)
    return {"processed": True}

@timed_metric(
    "api.request.duration",
    attributes_from_args=["endpoint", "method"]
)
def handle_request(endpoint: str, method: str, data: dict) -> dict:
    """Metric includes endpoint and method as attributes."""
    return {"status": "ok"}
```

## Context Propagation

### set_span_in_context

Manually set span in context.

```python
from agenticraft.telemetry import set_span_in_context

span = create_span("parent.operation")
context = set_span_in_context(span)

# Use context for child operations
async with context:
    await child_operation()  # Will be linked to parent
```

### extract_context / inject_context

For distributed tracing across services.

```python
from agenticraft.telemetry import extract_context, inject_context

# Service A - Inject context into headers
headers = {}
inject_context(headers)
response = await http_client.post(url, headers=headers)

# Service B - Extract context from headers
context = extract_context(request.headers)
with context:
    # This span is linked to Service A's span
    with create_span("service_b.handle_request"):
        process_request()
```

## Integration Helpers

### instrument_agent

Automatically instrument an agent instance.

```python
from agenticraft.telemetry import instrument_agent
from agenticraft import Agent

agent = Agent(name="MyAgent")
instrument_agent(agent)  # Now all operations are traced
```

### instrument_tool

Automatically instrument a tool instance.

```python
from agenticraft.telemetry import instrument_tool
from agenticraft.tools import WebSearchTool

tool = WebSearchTool()
instrument_tool(tool)  # Tool execution is now traced
```

### instrument_provider

Automatically instrument an LLM provider.

```python
from agenticraft.telemetry import instrument_provider
from agenticraft.providers import OpenAIProvider

provider = OpenAIProvider()
instrument_provider(provider)  # All LLM calls are traced
```

## Advanced Usage

### Custom Span Processors

```python
from agenticraft.telemetry import add_span_processor
from opentelemetry.sdk.trace import SpanProcessor

class CustomSpanProcessor(SpanProcessor):
    def on_start(self, span, parent_context):
        # Called when span starts
        span.set_attribute("custom.timestamp", time.time())
    
    def on_end(self, span):
        # Called when span ends
        if span.status.status_code == StatusCode.ERROR:
            # Handle errors
            alert_on_error(span)

add_span_processor(CustomSpanProcessor())
```

### Custom Exporters

```python
from agenticraft.telemetry import add_exporter
from opentelemetry.sdk.trace.export import SpanExporter

class CustomExporter(SpanExporter):
    def export(self, spans):
        # Send spans to custom backend
        for span in spans:
            send_to_backend(span)
        return SpanExportResult.SUCCESS

add_exporter(CustomExporter())
```

### Sampling Strategies

```python
from agenticraft.telemetry import set_sampler
from opentelemetry.sdk.trace.sampling import (
    TraceIdRatioBased,
    ParentBased,
    AlwaysOff,
    AlwaysOn
)

# Sample 10% of traces
set_sampler(TraceIdRatioBased(0.1))

# Sample based on parent
set_sampler(ParentBased(root=TraceIdRatioBased(0.1)))

# Custom sampler
class CustomSampler(Sampler):
    def should_sample(self, context, trace_id, name, kind, attributes, links):
        # Sample high-priority operations
        if attributes.get("priority") == "high":
            return SamplingResult(Decision.RECORD_AND_SAMPLE)
        return SamplingResult(Decision.DROP)

set_sampler(CustomSampler())
```

## Error Handling

All telemetry operations are designed to fail gracefully:

```python
# Telemetry errors won't crash your application
with create_span("operation") as span:
    try:
        span.set_attribute("key", value)  # Safe even if telemetry fails
    except Exception:
        # Telemetry errors are logged but don't propagate
        pass
```

To handle telemetry errors explicitly:

```python
from agenticraft.telemetry import set_error_handler

def handle_telemetry_error(error: Exception):
    logger.error(f"Telemetry error: {error}")
    # Could send to monitoring system
    
set_error_handler(handle_telemetry_error)
```

## Performance Tips

1. **Use batch processing**:
   ```python
   config = TelemetryConfig(
       batch_size=1024,
       export_interval_ms=10000
   )
   ```

2. **Limit attribute size**:
   ```python
   # Truncate large values
   span.set_attribute("data", data[:1000] if len(data) > 1000 else data)
   ```

3. **Use sampling in production**:
   ```python
   config = TelemetryConfig(sample_rate=0.1)  # 10% sampling
   ```

4. **Avoid high-cardinality attributes**:
   ```python
   # Bad - too many unique values
   span.set_attribute("user_id", user_id)
   
   # Good - bounded cardinality
   span.set_attribute("user_tier", get_user_tier(user_id))
   ```

## Thread Safety

All telemetry APIs are thread-safe and can be used in multi-threaded applications:

```python
import threading

def worker(worker_id):
    with create_span(f"worker.{worker_id}"):
        # Each thread gets its own span context
        process_task()

threads = [
    threading.Thread(target=worker, args=(i,))
    for i in range(10)
]
for t in threads:
    t.start()
```

## Async Safety

Telemetry properly handles async context propagation:

```python
async def parent_operation():
    with create_span("parent"):
        # Context is preserved across await
        await child_operation()
        
        # Even with concurrent operations
        await asyncio.gather(
            child_operation(),
            child_operation(),
            child_operation()
        )

async def child_operation():
    # Automatically linked to parent
    with create_span("child"):
        await asyncio.sleep(0.1)
```
