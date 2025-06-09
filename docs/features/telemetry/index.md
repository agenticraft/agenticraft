# Telemetry & Observability Documentation

Complete documentation for AgentiCraft's telemetry and observability features.

## 📚 Documentation Index

### Getting Started
- **Overview** - This page provides an overview and quick start guide for telemetry features
  - Quick setup examples
  - Core concepts (spans, traces, metrics)
  - Basic configuration
  - Auto-instrumentation overview

### Reference Documentation
- **[API Reference](api-reference.md)** - Complete API documentation
  - Core classes and methods
  - Tracing API details
  - Metrics API details
  - Decorators and helpers
  - Code examples for each API

- **[Metrics Reference](metrics-reference.md)** - Comprehensive metrics catalog
  - All automatic metrics
  - Metric naming conventions
  - Custom metric creation
  - Prometheus queries
  - Grafana dashboard examples

### Configuration & Deployment
- **[Configuration Guide](configuration.md)** - Detailed configuration options
  - All configuration parameters
  - Environment variables
  - Configuration files
  - Environment-specific setups
  - Security configuration

- **[Integration Guide](integration.md)** - Platform integration instructions
  - Jaeger setup
  - Grafana + Prometheus
  - DataDog, New Relic, AWS X-Ray
  - Azure Monitor, Google Cloud Trace
  - Elastic APM
  - Custom collectors

- **[Performance Guide](performance.md)** - Optimization and tuning
  - Performance benchmarks
  - Sampling strategies
  - Memory management
  - Production configurations
  - Troubleshooting guide

- **[Troubleshooting Guide](troubleshooting.md)** - Common issues and solutions
  - Installation and dependencies
  - Import errors and fixes
  - Configuration issues
  - Performance problems
  - Debugging steps

## 🚀 Quick Links

### For Developers
1. Start with this overview page for quick setup
2. Use the [API Reference](api-reference.md) while coding
3. Check [Performance Guide](performance.md) before production

### For DevOps/SRE
1. Review [Configuration Guide](configuration.md) for deployment
2. Follow [Integration Guide](integration.md) for your platform
3. Set up alerts using [Metrics Reference](metrics-reference.md)

### For Monitoring Teams
1. Import Grafana dashboards from `/agenticraft/telemetry/grafana_dashboard.json`
2. Configure Prometheus using examples in [Integration Guide](integration.md)
3. Set up alerts based on [Metrics Reference](metrics-reference.md)

## 📊 Feature Status

| Component | Implementation | Tests | Documentation | Examples |
|-----------|---------------|-------|---------------|----------|
| Core Telemetry | ✅ Complete | ✅ 95%+ | ✅ Complete | ✅ 5 examples |
| OpenTelemetry Integration | ✅ Complete | ✅ Complete | ✅ Complete | ✅ Complete |
| Console Exporter | ✅ Complete | ✅ Complete | ✅ Complete | ✅ Complete |
| OTLP Exporter | ✅ Complete | ✅ Complete | ✅ Complete | ✅ Complete |
| Prometheus Exporter | ✅ Complete | ✅ Complete | ✅ Complete | ✅ Complete |
| Auto-instrumentation | ✅ Complete | ✅ Complete | ✅ Complete | ✅ Complete |
| Grafana Dashboard | ✅ Complete | N/A | ✅ Complete | ✅ Included |

## 📝 Examples

All telemetry examples are located in `/examples/telemetry/`:

1. **basic_telemetry.py** - Simple telemetry setup and usage
2. **otlp_jaeger_example.py** - Jaeger integration with distributed tracing
3. **prometheus_metrics.py** - Metrics endpoint and Prometheus setup
4. **custom_instrumentation.py** - Creating custom spans and metrics
5. **performance_monitoring.py** - Performance analysis and optimization

## 🔧 Configuration Templates

### Development
```python
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="console",
    console_pretty_print=True,
    sample_rate=1.0
)
```

### Production
```python
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    otlp_endpoint="telemetry.company.com:4317",
    sample_rate=0.1,
    batch_size=2048,
    otlp_compression="gzip"
)
```

## 🎯 Common Tasks

### Enable Telemetry
```python
from agenticraft.telemetry import TelemetryConfig

telemetry = TelemetryConfig(enabled=True)
telemetry.initialize()
```

### Add Custom Metrics
```python
from agenticraft.telemetry import create_counter

counter = create_counter("custom.operations")
counter.add(1, {"operation": "process"})
```

### Create Custom Spans
```python
from agenticraft.telemetry import create_span

with create_span("custom.operation") as span:
    span.set_attribute("custom.value", 42)
    # Your code here
```

### Export to Jaeger
```bash
docker run -d -p 16686:16686 -p 4317:4317 jaegertracing/all-in-one:latest
```

```python
telemetry = TelemetryConfig(
    exporter_type="otlp",
    otlp_endpoint="localhost:4317"
)
```

## 🆘 Support

For telemetry-related questions:

1. Check the [Troubleshooting sections](performance.md#troubleshooting-performance-issues) in each guide
2. Review [example code](../../../examples/telemetry/) for working implementations
3. Enable debug mode: `TelemetryConfig(debug=True)`
4. Check AgentiCraft logs for telemetry-related messages

## 📈 What's Next?

The telemetry system is fully implemented and production-ready. Future enhancements may include:

- Additional exporters (Zipkin, AWS X-Ray native)
- Advanced sampling strategies
- Built-in anomaly detection
- Automatic performance optimization
- Enhanced security features

---

**Last Updated**: June 2025 | **AgentiCraft Version**: 0.2.0-alpha
