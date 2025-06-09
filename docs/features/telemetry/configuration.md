# Telemetry Configuration Guide

Comprehensive guide for configuring AgentiCraft's telemetry system for different environments and use cases.

## Configuration Methods

AgentiCraft telemetry can be configured through multiple methods, with the following precedence:

1. **Direct Python configuration** (highest priority)
2. **Environment variables**
3. **Configuration files** (`.env`, `config.yaml`)
4. **Default values** (lowest priority)

## Basic Configuration

### Python Configuration

```python
from agenticraft.telemetry import TelemetryConfig

# Minimal configuration
telemetry = TelemetryConfig(enabled=True)
telemetry.initialize()

# Full configuration
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    service_name="my-agent-service",
    service_version="1.0.0",
    deployment_environment="production",
    otlp_endpoint="localhost:4317",
    otlp_headers={"api-key": "your-key"},
    sample_rate=0.1,
    auto_instrument=True,
    batch_size=1024,
    export_interval_ms=5000,
    max_queue_size=2048,
    resource_attributes={
        "service.namespace": "ai-agents",
        "cloud.provider": "aws",
        "cloud.region": "us-east-1"
    }
)
telemetry.initialize()
```

### Environment Variables

```bash
# Basic settings
export AGENTICRAFT_TELEMETRY_ENABLED=true
export AGENTICRAFT_EXPORTER_TYPE=otlp
export AGENTICRAFT_SERVICE_NAME=my-agent-service
export AGENTICRAFT_SERVICE_VERSION=1.0.0
export AGENTICRAFT_DEPLOYMENT_ENVIRONMENT=production

# OTLP settings
export AGENTICRAFT_OTLP_ENDPOINT=localhost:4317
export AGENTICRAFT_OTLP_HEADERS='{"api-key": "your-key"}'
export AGENTICRAFT_OTLP_COMPRESSION=gzip
export AGENTICRAFT_OTLP_TIMEOUT=10000
export AGENTICRAFT_OTLP_PROTOCOL=grpc

# Sampling
export AGENTICRAFT_SAMPLE_RATE=0.1
export AGENTICRAFT_SAMPLE_PARENT_BASED=true

# Performance
export AGENTICRAFT_BATCH_SIZE=1024
export AGENTICRAFT_EXPORT_INTERVAL_MS=5000
export AGENTICRAFT_MAX_QUEUE_SIZE=2048
export AGENTICRAFT_MAX_EXPORT_ATTEMPTS=5

# Prometheus
export AGENTICRAFT_PROMETHEUS_PORT=8000
export AGENTICRAFT_PROMETHEUS_HOST=0.0.0.0

# Console exporter
export AGENTICRAFT_CONSOLE_PRETTY_PRINT=true
export AGENTICRAFT_CONSOLE_COLORS=true

# Debug
export AGENTICRAFT_TELEMETRY_DEBUG=true
export OTEL_LOG_LEVEL=debug
```

### Configuration File (.env)

```ini
# .env file
AGENTICRAFT_TELEMETRY_ENABLED=true
AGENTICRAFT_EXPORTER_TYPE=otlp
AGENTICRAFT_SERVICE_NAME=agent-production
AGENTICRAFT_OTLP_ENDPOINT=telemetry.company.com:4317
AGENTICRAFT_SAMPLE_RATE=0.1
```

### Configuration File (config.yaml)

```yaml
# config.yaml
telemetry:
  enabled: true
  exporter_type: otlp
  service:
    name: my-agent-service
    version: 1.0.0
    environment: production
  otlp:
    endpoint: localhost:4317
    headers:
      api-key: your-key
    compression: gzip
    timeout: 10000
  sampling:
    rate: 0.1
    parent_based: true
  performance:
    batch_size: 1024
    export_interval_ms: 5000
    max_queue_size: 2048
  resource_attributes:
    service.namespace: ai-agents
    cloud.provider: aws
    cloud.region: us-east-1
```

## Environment-Specific Configurations

### Development Environment

```python
# Development configuration with console output
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="console",
    console_pretty_print=True,
    console_colors=True,
    debug=True,
    sample_rate=1.0,  # Sample everything in dev
    auto_instrument=True
)
```

### Testing Environment

```python
# Testing configuration - minimal overhead
telemetry = TelemetryConfig(
    enabled=False,  # Usually disabled in tests
    # Or use in-memory exporter for testing
    exporter_type="memory",
    sample_rate=1.0
)
```

### Staging Environment

```python
# Staging configuration - similar to production
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    service_name="agent-staging",
    deployment_environment="staging",
    otlp_endpoint="staging-telemetry.company.com:4317",
    sample_rate=0.5,  # Higher sampling than production
    batch_size=512,
    export_interval_ms=3000
)
```

### Production Environment

```python
# Production configuration - optimized for performance
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    service_name="agent-production",
    service_version=os.getenv("APP_VERSION", "1.0.0"),
    deployment_environment="production",
    otlp_endpoint="telemetry.company.com:4317",
    otlp_headers={
        "api-key": os.getenv("TELEMETRY_API_KEY"),
        "x-service-auth": os.getenv("SERVICE_AUTH_TOKEN")
    },
    sample_rate=0.1,  # Sample 10% in production
    batch_size=2048,
    export_interval_ms=10000,
    max_queue_size=4096,
    max_export_attempts=3,
    resource_attributes={
        "service.namespace": "ai-platform",
        "cloud.provider": "aws",
        "cloud.region": os.getenv("AWS_REGION", "us-east-1"),
        "deployment.version": os.getenv("DEPLOYMENT_VERSION"),
        "k8s.pod.name": os.getenv("HOSTNAME"),
        "k8s.namespace": os.getenv("K8S_NAMESPACE")
    }
)
```

## Exporter Configurations

### Console Exporter

Best for development and debugging.

```python
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="console",
    console_pretty_print=True,      # Human-readable format
    console_colors=True,            # Colorized output
    console_show_hidden=False,      # Show internal spans
    console_max_width=120,          # Maximum line width
    console_indent_size=2,          # Indentation spaces
    console_show_timestamps=True,   # Include timestamps
    console_show_duration=True      # Show span duration
)
```

Output format:
```
[2025-06-14 10:23:45.123] agent.execute (1.234s)
  ├─ agent.name: ResearchAgent
  ├─ agent.operation: execute
  ├─ input.length: 45
  ├─ [10:23:45.200] tool.execute (0.800s)
  │  ├─ tool.name: web_search
  │  └─ results.count: 10
  └─ output.length: 1250
```

### OTLP Exporter

For production use with OpenTelemetry collectors.

```python
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    
    # Endpoint configuration
    otlp_endpoint="localhost:4317",      # gRPC endpoint
    # or for HTTP:
    # otlp_endpoint="http://localhost:4318/v1/traces",
    
    # Authentication
    otlp_headers={
        "api-key": "your-api-key",
        "x-service-name": "agent-service"
    },
    
    # Protocol settings
    otlp_protocol="grpc",               # or "http/protobuf"
    otlp_compression="gzip",            # or "none", "deflate"
    otlp_timeout=10000,                 # milliseconds
    
    # Retry configuration
    otlp_retry_enabled=True,
    otlp_retry_max_attempts=5,
    otlp_retry_initial_interval=1000,   # ms
    otlp_retry_max_interval=32000,      # ms
    otlp_retry_max_elapsed_time=120000, # ms
    
    # TLS configuration
    otlp_insecure=False,                # Use TLS
    otlp_certificate_path="/path/to/cert.pem",
    otlp_client_key_path="/path/to/key.pem",
    otlp_client_certificate_path="/path/to/client-cert.pem"
)
```

### Prometheus Exporter

For metrics scraping by Prometheus.

```python
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="prometheus",
    
    # Server configuration
    prometheus_port=8000,
    prometheus_host="0.0.0.0",     # Bind to all interfaces
    prometheus_path="/metrics",     # Metrics endpoint path
    
    # Metric configuration
    prometheus_namespace="agenticraft",
    prometheus_subsystem="agents",
    
    # Histogram buckets
    prometheus_histogram_buckets={
        "latency": [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        "token_count": [10, 50, 100, 500, 1000, 5000, 10000]
    },
    
    # Labels to include
    prometheus_default_labels={
        "environment": "production",
        "region": "us-east-1"
    }
)
```

Prometheus configuration:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'agenticraft'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 15s
    metrics_path: '/metrics'
```

### Multiple Exporters

Export to multiple destinations simultaneously.

```python
from agenticraft.telemetry import TelemetryConfig, CompositeExporter

telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="composite",
    exporters=[
        {
            "type": "console",
            "config": {"pretty_print": True}
        },
        {
            "type": "otlp",
            "config": {
                "endpoint": "localhost:4317",
                "headers": {"api-key": "key1"}
            }
        },
        {
            "type": "prometheus",
            "config": {"port": 8000}
        }
    ]
)
```

## Sampling Configuration

### Basic Sampling

```python
# Fixed rate sampling - 10% of traces
telemetry = TelemetryConfig(
    sample_rate=0.1
)

# Always sample
telemetry = TelemetryConfig(
    sample_rate=1.0
)

# Never sample (metrics still collected)
telemetry = TelemetryConfig(
    sample_rate=0.0
)
```

### Advanced Sampling

```python
from agenticraft.telemetry import (
    TelemetryConfig, 
    CompositeSampler,
    RateLimitingSampler,
    AttributeBasedSampler
)

# Rate limiting sampler - max 100 traces per second
rate_limiter = RateLimitingSampler(max_traces_per_second=100)

# Attribute-based sampling
attribute_sampler = AttributeBasedSampler(
    rules=[
        # Always sample errors
        {"attribute": "error", "value": True, "sample_rate": 1.0},
        # Sample 50% of high-priority operations
        {"attribute": "priority", "value": "high", "sample_rate": 0.5},
        # Sample 1% of low-priority operations
        {"attribute": "priority", "value": "low", "sample_rate": 0.01},
        # Default sampling rate
        {"default": True, "sample_rate": 0.1}
    ]
)

# Composite sampler
telemetry = TelemetryConfig(
    sampler=CompositeSampler([rate_limiter, attribute_sampler])
)
```

### Parent-Based Sampling

```python
# Honor parent sampling decision
telemetry = TelemetryConfig(
    sample_parent_based=True,
    sample_rate=0.1  # For root spans
)
```

## Performance Tuning

### Batch Processing

```python
telemetry = TelemetryConfig(
    # Batch configuration
    batch_size=2048,                # Spans per batch
    export_interval_ms=10000,       # Export every 10 seconds
    max_queue_size=8192,           # Maximum queued spans
    
    # Export behavior
    max_export_attempts=3,          # Retry failed exports
    export_timeout_ms=30000,        # Export timeout
    
    # Memory limits
    max_span_attributes=128,        # Max attributes per span
    max_span_events=128,           # Max events per span
    max_span_links=128,            # Max links per span
    max_attribute_length=4096      # Max attribute value length
)
```

### Resource Optimization

```python
# Minimal resource usage
telemetry = TelemetryConfig(
    # Reduce memory usage
    batch_size=256,
    max_queue_size=1024,
    export_interval_ms=30000,      # Export less frequently
    
    # Limit span data
    max_span_attributes=32,
    max_attribute_length=1024,
    
    # Aggressive sampling
    sample_rate=0.01,              # 1% sampling
    
    # Disable features
    auto_instrument_tools=False,
    auto_instrument_memory=False,
    record_token_usage=False
)
```

## Security Configuration

### API Key Management

```python
# Using environment variables (recommended)
telemetry = TelemetryConfig(
    otlp_headers={
        "api-key": os.getenv("TELEMETRY_API_KEY"),
        "x-api-secret": os.getenv("TELEMETRY_API_SECRET")
    }
)

# Using key vault
from azure.keyvault.secrets import SecretClient

client = SecretClient(vault_url, credential)
api_key = client.get_secret("telemetry-api-key").value

telemetry = TelemetryConfig(
    otlp_headers={"api-key": api_key}
)
```

### Data Privacy

```python
from agenticraft.telemetry import TelemetryConfig, AttributeFilter

# Filter sensitive attributes
telemetry = TelemetryConfig(
    attribute_filters=[
        # Remove PII
        AttributeFilter(
            action="remove",
            attributes=["user.email", "user.id", "user.name"]
        ),
        # Hash sensitive values
        AttributeFilter(
            action="hash",
            attributes=["session.id", "request.ip"]
        ),
        # Redact patterns
        AttributeFilter(
            action="redact",
            pattern=r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
            replacement="***-**-****"
        )
    ]
)
```

## Kubernetes Configuration

### ConfigMap

```yaml
# telemetry-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: agenticraft-telemetry
data:
  AGENTICRAFT_TELEMETRY_ENABLED: "true"
  AGENTICRAFT_EXPORTER_TYPE: "otlp"
  AGENTICRAFT_OTLP_ENDPOINT: "otel-collector.observability:4317"
  AGENTICRAFT_SERVICE_NAME: "agent-service"
  AGENTICRAFT_SAMPLE_RATE: "0.1"
```

### Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-service
spec:
  template:
    spec:
      containers:
      - name: agent
        image: agent-service:latest
        envFrom:
        - configMapRef:
            name: agenticraft-telemetry
        env:
        - name: AGENTICRAFT_SERVICE_VERSION
          value: "1.0.0"
        - name: AGENTICRAFT_OTLP_HEADERS
          valueFrom:
            secretKeyRef:
              name: telemetry-secrets
              key: api-key
```

## Docker Configuration

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  agent-service:
    image: agent-service:latest
    environment:
      AGENTICRAFT_TELEMETRY_ENABLED: "true"
      AGENTICRAFT_EXPORTER_TYPE: "otlp"
      AGENTICRAFT_OTLP_ENDPOINT: "otel-collector:4317"
      AGENTICRAFT_SERVICE_NAME: "agent-service"
      AGENTICRAFT_SAMPLE_RATE: "0.1"
    depends_on:
      - otel-collector

  otel-collector:
    image: otel/opentelemetry-collector:latest
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
    volumes:
      - ./otel-config.yaml:/etc/otel-collector-config.yaml
    command: ["--config=/etc/otel-collector-config.yaml"]
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Set telemetry defaults
ENV AGENTICRAFT_TELEMETRY_ENABLED=true \
    AGENTICRAFT_EXPORTER_TYPE=otlp \
    AGENTICRAFT_SERVICE_NAME=agent-service

# Run application
CMD ["python", "-m", "agenticraft"]
```

## Debugging Configuration

### Enable Debug Logging

```python
import logging

# Enable debug logging for telemetry
logging.getLogger("agenticraft.telemetry").setLevel(logging.DEBUG)
logging.getLogger("opentelemetry").setLevel(logging.DEBUG)

telemetry = TelemetryConfig(
    enabled=True,
    debug=True,
    debug_include_internal_spans=True,
    debug_print_exports=True
)
```

### Troubleshooting Exporter

```python
# Use troubleshooting exporter to diagnose issues
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="debug",
    debug_export_path="/tmp/telemetry-debug.json",
    debug_include_failed_exports=True
)
```

## Configuration Validation

```python
from agenticraft.telemetry import TelemetryConfig, validate_config

# Validate configuration before initialization
config = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    otlp_endpoint="localhost:4317"
)

errors = validate_config(config)
if errors:
    print("Configuration errors:", errors)
else:
    config.initialize()
```

## Best Practices

1. **Use environment variables for sensitive data**
   ```python
   telemetry = TelemetryConfig(
       otlp_headers={"api-key": os.getenv("TELEMETRY_API_KEY")}
   )
   ```

2. **Set appropriate sampling rates**
   - Development: 100% (1.0)
   - Staging: 50% (0.5)
   - Production: 1-10% (0.01-0.1)

3. **Configure batch sizes based on traffic**
   - Low traffic: 256-512
   - Medium traffic: 1024-2048
   - High traffic: 4096-8192

4. **Use resource attributes for filtering**
   ```python
   telemetry = TelemetryConfig(
       resource_attributes={
           "service.namespace": "ai-platform",
           "deployment.environment": "production",
           "team": "ai-agents"
       }
   )
   ```

5. **Monitor telemetry health**
   ```python
   from agenticraft.telemetry import get_telemetry_stats
   
   stats = get_telemetry_stats()
   print(f"Spans exported: {stats.spans_exported}")
   print(f"Export failures: {stats.export_failures}")
   ```
