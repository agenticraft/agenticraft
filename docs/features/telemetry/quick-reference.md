# Telemetry Examples Quick Reference

## 🚀 Getting Started

Choose an example based on your needs:

### For Learning
1. **Start Here** → `basic_telemetry.py`
   ```bash
   python examples/telemetry/basic_telemetry.py
   ```

### For Development
2. **Custom Telemetry** → `custom_instrumentation.py`
   ```bash
   python examples/telemetry/custom_instrumentation.py
   ```

### For Production
3. **Jaeger Integration** → `otlp_jaeger_example.py`
   ```bash
   # First, start Jaeger
   docker run -d --name jaeger \
     -p 16686:16686 \
     -p 4317:4317 \
     jaegertracing/all-in-one:latest
   
   # Then run the example
   python examples/telemetry/otlp_jaeger_example.py
   ```

4. **Prometheus Metrics** → `prometheus_metrics.py`
   ```bash
   python examples/telemetry/prometheus_metrics.py
   # Metrics available at http://localhost:8000/metrics
   ```

## 📊 Example Overview

| Example | Purpose | Key Features | Difficulty |
|---------|---------|--------------|------------|
| `basic_telemetry.py` | Introduction | Console output, simple traces | Beginner |
| `custom_instrumentation.py` | Advanced patterns | Custom spans, metrics, decorators | Advanced |
| `integration_example.py` | Framework integration | Auto-instrumentation, handlers | Intermediate |
| `otlp_jaeger_example.py` | Production tracing | Distributed traces, Jaeger UI | Intermediate |
| `performance_monitoring.py` | Performance analysis | Latency tracking, overhead measurement | Advanced |
| `prometheus_metrics.py` | Metrics export | Prometheus scraping, Grafana dashboards | Intermediate |

## 🔧 Common Patterns

### Basic Setup
```python
from agenticraft.telemetry.integration import TelemetryConfig

telemetry = TelemetryConfig(
    enabled=True,
    traces_enabled=True,
    metrics_enabled=True,
    exporter_type="console",  # or "otlp", "prometheus"
    service_name="my_service"
)
telemetry.initialize()
```

### Custom Span
```python
from agenticraft.telemetry import create_span

with create_span("my_operation") as span:
    span.set_attribute("user_id", "123")
    # Your code here
```

### Record Metrics
```python
from agenticraft.telemetry import LatencyTimer

with LatencyTimer("api_call", endpoint="/users"):
    # Your code here
    pass
```

## 🎯 Use Cases

### Development & Debugging
- Use `basic_telemetry.py` for console output
- Use `custom_instrumentation.py` for detailed tracing

### Performance Optimization
- Use `performance_monitoring.py` to identify bottlenecks
- Measure telemetry overhead impact

### Production Monitoring
- Use `otlp_jaeger_example.py` for distributed tracing
- Use `prometheus_metrics.py` for metrics dashboards

### Integration Testing
- Use `integration_example.py` to verify auto-instrumentation
- No code changes needed!

## 📈 Metrics Available

All examples expose these metrics:
- `agenticraft_tokens_total` - Token usage by provider/model
- `agenticraft_latency` - Operation latency histogram
- `agenticraft_errors_total` - Error counts by operation
- `agenticraft_agent_operations` - Agent operation counts

## 🔍 Viewing Results

### Console Export
- Output printed directly to terminal
- Great for development and debugging

### Jaeger UI
- Open http://localhost:16686
- Select service: `agenticraft_demo`
- View distributed traces

### Prometheus
- Scrape endpoint: http://localhost:8000/metrics
- Import Grafana dashboard from `agenticraft_dashboard.json`

## 💡 Tips

1. **Start Simple**: Begin with console export before moving to production exporters
2. **Use Auto-Instrumentation**: Let the framework handle basic telemetry
3. **Add Custom Spans**: For business-critical operations
4. **Monitor Overhead**: Use performance example to measure impact
5. **Export Wisely**: Choose exporter based on your infrastructure

## 🚨 Troubleshooting

### No Output?
- Check `enabled=True` in TelemetryConfig
- Ensure `telemetry.initialize()` is called
- Verify exporter configuration

### Missing Traces?
- Check `traces_enabled=True`
- Ensure proper shutdown with `shutdown_tracer()`
- For OTLP, verify endpoint is reachable

### Performance Impact?
- Use sampling for high-volume services
- Batch exports with OTLP
- Monitor with `performance_monitoring.py`

## 🔄 Handler Pattern

AgentiCraft uses handlers for extending functionality:

```python
# For WorkflowAgent
def my_handler(agent, step, context):
    """Process data from context."""
    data = context.get("data", [])
    result = process(data)
    context["result"] = result
    return f"Processed {len(data)} items"

workflow_agent.register_handler("process", my_handler)
```

For basic agents, use natural language instructions instead of tools.

---

**Need Help?** Check the full documentation at `/docs/features/telemetry/`
