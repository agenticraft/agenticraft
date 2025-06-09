# Telemetry Troubleshooting Guide

This guide helps you resolve common issues with AgentiCraft telemetry.

## 🔧 Installation & Dependencies

### Required Dependencies

#### Base Telemetry (Console Export)
The base telemetry with console export works with core OpenTelemetry packages:
```bash
pip install opentelemetry-api opentelemetry-sdk
```

#### Additional Exporters (Optional)

1. **OTLP Export** (for Jaeger, Grafana, etc.):
```bash
pip install opentelemetry-exporter-otlp opentelemetry-exporter-otlp-proto-grpc
```

2. **Jaeger Export** (legacy Thrift protocol):
```bash
pip install opentelemetry-exporter-jaeger
```

3. **Prometheus Export**:
```bash
pip install opentelemetry-exporter-prometheus
```

### Full Installation
To install all telemetry dependencies:
```bash
pip install agenticraft[telemetry]
```

Or manually:
```bash
pip install \
    opentelemetry-api \
    opentelemetry-sdk \
    opentelemetry-instrumentation \
    opentelemetry-exporter-otlp \
    opentelemetry-exporter-otlp-proto-grpc \
    opentelemetry-exporter-jaeger \
    opentelemetry-exporter-prometheus
```

## 🚨 Common Issues

### Import Errors

#### "No module named 'opentelemetry'"
**Solution**: Install base packages
```bash
pip install opentelemetry-api opentelemetry-sdk
```

#### "OTLP exporter not available"
**Solution**: Install OTLP exporter
```bash
pip install opentelemetry-exporter-otlp
```

#### "Prometheus exporter not available"
**Solution**: Install Prometheus exporter
```bash
pip install opentelemetry-exporter-prometheus
```

### Configuration Issues

#### No telemetry output
**Check**:
- Ensure `enabled=True` in TelemetryConfig
- Call `telemetry.initialize()` after configuration
- Verify exporter configuration matches your setup

#### Missing traces in Jaeger
**Check**:
- Jaeger is running: `docker ps | grep jaeger`
- OTLP endpoint is correct (default: `localhost:4317`)
- Call shutdown functions to flush final traces:
  ```python
  from agenticraft.telemetry import shutdown_tracer, shutdown_metrics
  shutdown_tracer()
  shutdown_metrics()
  ```

#### Port already in use (Prometheus)
**Solution**: Change port in configuration
```python
telemetry = TelemetryConfig(
    exporter_type="prometheus",
    prometheus_port=8001  # Different port
)
```

### Performance Issues

#### High telemetry overhead
**Solutions**:
- Enable sampling for high-volume services:
  ```python
  telemetry = TelemetryConfig(
      sampling_rate=0.1  # Sample 10% of traces
  )
  ```
- Use batch export with OTLP
- Profile with `performance_monitoring.py` example

#### Memory usage growing
**Check**:
- Ensure proper shutdown on application exit
- Use bounded queues for exporters
- Monitor with `performance_monitoring.py`

## 🔍 Debugging Steps

### 1. Verify Installation
```bash
# Check installed packages
pip list | grep opentelemetry

# Expected output (versions may vary):
# opentelemetry-api                    1.20.0
# opentelemetry-sdk                    1.20.0
# opentelemetry-instrumentation        0.41b0
# ...
```

### 2. Test Basic Functionality
```python
# test_telemetry.py
from agenticraft.telemetry.integration import TelemetryConfig

telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="console"
)
telemetry.initialize()
print("✅ Telemetry initialized successfully!")
```

### 3. Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed telemetry operations
```

### 4. Test Specific Exporters
```python
# Test OTLP
telemetry = TelemetryConfig(
    exporter_type="otlp",
    otlp_endpoint="localhost:4317"
)

# Test Prometheus
telemetry = TelemetryConfig(
    exporter_type="prometheus",
    prometheus_port=8000
)
```

## 📞 Getting Help

If you're still experiencing issues:

1. Check the [examples](../../../examples/telemetry/) for working code
2. Review the [configuration guide](configuration.md)
3. Enable debug logging to see detailed errors
4. Open an issue on GitHub with:
   - Error messages
   - Your configuration
   - Steps to reproduce

## 🎯 Quick Fixes

### Reset Everything
```bash
# Uninstall all telemetry packages
pip uninstall -y $(pip list | grep opentelemetry | awk '{print $1}')

# Reinstall
pip install agenticraft[telemetry]
```

### Minimal Working Example
```python
from agenticraft import Agent
from agenticraft.telemetry.integration import TelemetryConfig

# Minimal config - console output only
telemetry = TelemetryConfig(enabled=True)
telemetry.initialize()

# Test with agent
agent = Agent(name="Test")
response = agent.run("Hello")
print(response.content)
```

This should produce console output showing traces and metrics.
