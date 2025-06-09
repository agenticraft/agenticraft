# 📊 AgentiCraft Telemetry Examples

This directory contains comprehensive examples demonstrating AgentiCraft's production-ready observability features using OpenTelemetry.

## 🎯 Overview

AgentiCraft provides built-in telemetry for distributed tracing, metrics collection, and performance monitoring. These examples show how to:

- Enable automatic instrumentation with zero code changes
- Add custom telemetry for business-specific metrics
- Export data to various backends (Jaeger, Prometheus, etc.)
- Monitor performance with minimal overhead (<1%)

## 📁 Examples

### 1. **basic_telemetry.py** - Getting Started
The simplest example showing console-based telemetry output.

**Run it:**
```bash
python examples/telemetry/basic_telemetry.py
```

**You'll learn:**
- How to enable telemetry
- Automatic span creation
- Token usage tracking
- Console export for debugging

### 2. **custom_instrumentation.py** - Advanced Telemetry
Shows how to add custom telemetry to your business logic.

**Run it:**
```bash
python examples/telemetry/custom_instrumentation.py
```

**You'll learn:**
- Creating custom spans with attributes
- Recording business metrics
- Exception tracking
- Using the `@trace_operation` decorator
- Manual span creation

### 3. **integration_example.py** - Framework Integration
Demonstrates automatic instrumentation across all AgentiCraft components.

**Run it:**
```bash
python examples/telemetry/integration_example.py
```

**You'll learn:**
- Auto-instrumentation of agents
- WorkflowAgent with handlers
- Nested span relationships
- Zero-config telemetry

### 4. **otlp_jaeger_example.py** - Production Tracing
Shows distributed tracing with Jaeger for production environments.

**Setup Jaeger:**
```bash
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest
```

**Run it:**
```bash
python examples/telemetry/otlp_jaeger_example.py
```

**View traces:**
Open http://localhost:16686 and select service "agenticraft_demo"

**You'll learn:**
- OTLP export configuration
- Distributed trace visualization
- Error tracking in traces
- Complex workflow tracing

### 5. **prometheus_metrics.py** - Metrics Export
Exposes metrics for Prometheus scraping and Grafana dashboards.

**Run it:**
```bash
python examples/telemetry/prometheus_metrics.py
# Metrics available at http://localhost:8000/metrics
```

**You'll learn:**
- Prometheus metrics endpoint
- Grafana dashboard setup
- Real-time metrics collection
- Multiple metric types

### 6. **performance_monitoring.py** - Performance Analysis
Measures telemetry overhead and provides optimization insights.

**Run it:**
```bash
python examples/telemetry/performance_monitoring.py
```

**You'll learn:**
- Measuring telemetry overhead
- Latency percentiles (P50, P90, P99)
- Performance comparison
- Optimization recommendations

## 🚀 Quick Start

### Basic Setup

```python
from agenticraft.telemetry.integration import TelemetryConfig

# Configure telemetry
telemetry = TelemetryConfig(
    enabled=True,
    traces_enabled=True,
    metrics_enabled=True,
    exporter_type="console",  # or "otlp", "prometheus"
    service_name="my_service"
)

# Initialize
telemetry.initialize()

# Use agents normally - telemetry is automatic!
agent = Agent(name="MyAgent", model="gpt-4o-mini")
response = await agent.arun("Hello!")
```

### Custom Instrumentation

```python
from agenticraft.telemetry import create_span, set_span_attributes

# Add custom spans
with create_span("business.operation") as span:
    span.set_attribute("user.id", "123")
    span.add_event("Processing started")
    
    # Your business logic here
    result = process_data()
    
    span.set_attribute("items.processed", len(result))
```

## 📈 Available Metrics

All examples automatically collect:

- **agenticraft_tokens_total** - Token usage by provider/model
- **agenticraft_latency** - Operation latency histograms
- **agenticraft_errors_total** - Error counts by operation
- **agenticraft_agent_operations** - Agent operation counts
- **agenticraft_workflow_steps** - Workflow execution metrics

## 🔧 Configuration Options

### Environment Variables
```bash
AGENTICRAFT_TELEMETRY_ENABLED=true
AGENTICRAFT_EXPORTER_TYPE=otlp
AGENTICRAFT_OTLP_ENDPOINT=localhost:4317
AGENTICRAFT_SERVICE_NAME=my-agent-app
```

### Exporter Types
- **console** - Development debugging (default)
- **otlp** - Production (Jaeger, collectors)
- **prometheus** - Metrics scraping

## 🧪 Testing the Examples

### Quick Test
Validate core telemetry functionality without external dependencies:
```bash
python quick_telemetry_test.py
```

### Full Test Suite
Run all examples and generate a comprehensive report:
```bash
python test_all_telemetry.py
```

### Individual Example Testing
```bash
# Basic console telemetry
python examples/telemetry/basic_telemetry.py

# Custom instrumentation
python examples/telemetry/custom_instrumentation.py

# Auto-instrumentation
python examples/telemetry/integration_example.py

# OTLP/Jaeger (requires Jaeger running)
docker run -d --name jaeger -p 16686:16686 -p 4317:4317 jaegertracing/all-in-one:latest
python examples/telemetry/otlp_jaeger_example.py

# Performance monitoring
python examples/telemetry/performance_monitoring.py

# Prometheus metrics
python examples/telemetry/prometheus_metrics.py
# Then check http://localhost:8000/metrics
```

## 📊 Handler Pattern

AgentiCraft uses handlers for extending functionality with WorkflowAgent:

```python
# Define handler
def process_handler(agent, step, context):
    data = context.get("data", [])
    result = process(data)
    context["result"] = result
    return f"Processed {len(data)} items"

# Register and use
workflow_agent.register_handler("process", process_handler)
workflow.add_step("step1", handler="process")
```

## 🏆 Best Practices

1. **Start Simple**: Use console export during development
2. **Auto-Instrument First**: Let the framework handle basic telemetry
3. **Add Business Context**: Use custom spans for critical operations
4. **Monitor Overhead**: Keep telemetry overhead <1%
5. **Export Appropriately**: Choose the right exporter for your infrastructure

## 📚 Additional Resources

- **Quick Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command cheat sheet
- **Tool Patterns**: [TOOL_PATTERNS_VISUAL.md](TOOL_PATTERNS_VISUAL.md) - Visual guide to handlers
- **Usage Guide**: [TOOL_USAGE_GUIDE.md](TOOL_USAGE_GUIDE.md) - Detailed handler documentation
- **Full Documentation**: [/docs/features/telemetry/](../../docs/features/telemetry/)

## 🐛 Troubleshooting

### No telemetry output?
- Ensure `enabled=True` in TelemetryConfig
- Call `telemetry.initialize()`
- Check exporter configuration

### High overhead?
- Use sampling for high-volume services
- Batch exports with OTLP
- Profile with `performance_monitoring.py`

### Can't see traces in Jaeger?
- Verify Jaeger is running: `docker ps`
- Check OTLP endpoint is correct
- Ensure proper shutdown for final exports

---

**Happy Monitoring!** 🎉 These examples demonstrate how AgentiCraft provides enterprise-grade observability out of the box with minimal configuration.
