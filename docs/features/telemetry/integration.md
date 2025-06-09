# Telemetry Integration Guide

This guide covers how to integrate AgentiCraft's telemetry with popular monitoring and observability platforms.

## Table of Contents

- [Jaeger Integration](#jaeger-integration)
- [Grafana + Prometheus](#grafana--prometheus)
- [DataDog Integration](#datadog-integration)
- [New Relic Integration](#new-relic-integration)
- [AWS X-Ray Integration](#aws-x-ray-integration)
- [Azure Monitor Integration](#azure-monitor-integration)
- [Google Cloud Trace](#google-cloud-trace)
- [Elastic APM](#elastic-apm)
- [Custom Collectors](#custom-collectors)

## Jaeger Integration

Jaeger is a distributed tracing platform that works seamlessly with OpenTelemetry.

### Quick Start with Docker

```bash
# Run Jaeger all-in-one
docker run -d --name jaeger \
  -p 5775:5775/udp \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14250:14250 \
  -p 14268:14268 \
  -p 14269:14269 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

### Configure AgentiCraft

```python
from agenticraft.telemetry import TelemetryConfig

telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    otlp_endpoint="localhost:4317",
    service_name="agenticraft-app"
)
telemetry.initialize()
```

### Docker Compose Setup

```yaml
version: '3.8'

services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    environment:
      COLLECTOR_OTLP_ENABLED: "true"
    ports:
      - "16686:16686"  # Jaeger UI
      - "4317:4317"    # OTLP gRPC receiver
      - "4318:4318"    # OTLP HTTP receiver

  agent-app:
    image: your-app:latest
    environment:
      AGENTICRAFT_TELEMETRY_ENABLED: "true"
      AGENTICRAFT_EXPORTER_TYPE: "otlp"
      AGENTICRAFT_OTLP_ENDPOINT: "jaeger:4317"
    depends_on:
      - jaeger
```

### Production Setup

For production, use the Jaeger Operator on Kubernetes:

```yaml
apiVersion: jaegertracing.io/v1
kind: Jaeger
metadata:
  name: agenticraft-tracing
spec:
  strategy: production
  storage:
    type: elasticsearch
    options:
      es:
        server-urls: https://elasticsearch:9200
  query:
    serviceType: LoadBalancer
```

## Grafana + Prometheus

Complete observability stack with metrics and dashboards.

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'agenticraft'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### AgentiCraft Configuration

```python
from agenticraft.telemetry import TelemetryConfig

# Enable Prometheus metrics
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="prometheus",
    prometheus_port=8000,
    service_name="agenticraft-app"
)
telemetry.initialize()
```

### Docker Compose Stack

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin

  agent-app:
    image: your-app:latest
    ports:
      - "8000:8000"  # Prometheus metrics
    environment:
      AGENTICRAFT_TELEMETRY_ENABLED: "true"
      AGENTICRAFT_EXPORTER_TYPE: "prometheus"
      AGENTICRAFT_PROMETHEUS_PORT: "8000"

volumes:
  prometheus-data:
  grafana-data:
```

### Import AgentiCraft Dashboard

1. Open Grafana at http://localhost:3000
2. Go to Dashboards → Import
3. Upload `/agenticraft/telemetry/grafana_dashboard.json`
4. Select Prometheus as the data source

### Custom Grafana Queries

```promql
# Request rate by agent
rate(agenticraft_agent_requests_total[5m])

# Average latency by operation
histogram_quantile(0.95, 
  rate(agenticraft_latency_bucket[5m])
)

# Token usage by model
sum by (model) (
  rate(agenticraft_tokens_total[5m])
)

# Error rate
rate(agenticraft_errors_total[5m]) / 
rate(agenticraft_requests_total[5m])
```

## DataDog Integration

### Using OpenTelemetry Collector

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

exporters:
  datadog:
    api:
      key: ${DD_API_KEY}
      site: datadoghq.com  # or datadoghq.eu
    metrics:
      endpoint: https://api.datadoghq.com
    traces:
      endpoint: https://trace.agent.datadoghq.com

processors:
  batch:
    timeout: 10s

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [datadog]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [datadog]
```

### Direct DataDog Integration

```python
# Install datadog exporter
# pip install opentelemetry-exporter-datadog

from agenticraft.telemetry import TelemetryConfig
from opentelemetry.exporter.datadog import DatadogSpanExporter

# Configure with DataDog exporter
telemetry = TelemetryConfig(
    enabled=True,
    custom_exporter=DatadogSpanExporter(
        agent_url="http://localhost:8126",
        service="agenticraft-app",
        env="production"
    )
)
telemetry.initialize()
```

### DataDog Agent Configuration

```yaml
# datadog.yaml
apm_config:
  enabled: true
  apm_non_local_traffic: true

otlp_config:
  receiver:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
```

## New Relic Integration

### OpenTelemetry Exporter

```python
# Install New Relic exporter
# pip install opentelemetry-exporter-otlp

from agenticraft.telemetry import TelemetryConfig

telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    otlp_endpoint="https://otlp.nr-data.net:4317",
    otlp_headers={
        "api-key": "${NEW_RELIC_LICENSE_KEY}"
    },
    service_name="agenticraft-app",
    resource_attributes={
        "service.instance.id": "${HOSTNAME}",
        "environment": "production"
    }
)
telemetry.initialize()
```

### New Relic Agent

```python
# Alternative: Use New Relic Python agent
import newrelic.agent

newrelic.agent.initialize('newrelic.ini')

@newrelic.agent.background_task()
def process_with_agent():
    # Your AgentiCraft code
    pass
```

## AWS X-Ray Integration

### Using AWS Distro for OpenTelemetry

```python
# Install AWS OTEL Python
# pip install aws-opentelemetry-distro

from agenticraft.telemetry import TelemetryConfig
import boto3

# Configure for X-Ray
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    otlp_endpoint="localhost:4317",
    service_name="agenticraft-app",
    resource_attributes={
        "service.name": "agenticraft-app",
        "service.namespace": "ai-agents",
        "aws.deployment.environment": "production"
    }
)
telemetry.initialize()
```

### AWS OTEL Collector Config

```yaml
# aws-otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

exporters:
  awsxray:
    region: us-east-1
  awsemf:
    region: us-east-1
    namespace: AgentiCraft

processors:
  batch/traces:
    timeout: 1s
    send_batch_size: 50
  batch/metrics:
    timeout: 60s

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch/traces]
      exporters: [awsxray]
    metrics:
      receivers: [otlp]
      processors: [batch/metrics]
      exporters: [awsemf]
```

### ECS Task Definition

```json
{
  "family": "agenticraft-app",
  "taskRoleArn": "arn:aws:iam::account:role/TaskRole",
  "containerDefinitions": [
    {
      "name": "agenticraft-app",
      "image": "your-ecr-repo/agenticraft:latest",
      "environment": [
        {
          "name": "AGENTICRAFT_TELEMETRY_ENABLED",
          "value": "true"
        },
        {
          "name": "AGENTICRAFT_OTLP_ENDPOINT",
          "value": "localhost:4317"
        }
      ]
    },
    {
      "name": "aws-otel-collector",
      "image": "amazon/aws-otel-collector:latest",
      "command": ["--config", "/etc/ecs/otel-config.yaml"],
      "environment": [
        {
          "name": "AWS_REGION",
          "value": "us-east-1"
        }
      ]
    }
  ]
}
```

## Azure Monitor Integration

### Application Insights Setup

```python
# Install Azure Monitor exporter
# pip install azure-monitor-opentelemetry-exporter

from agenticraft.telemetry import TelemetryConfig
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

# Configure with Azure Monitor
telemetry = TelemetryConfig(
    enabled=True,
    custom_exporter=AzureMonitorTraceExporter(
        connection_string="${APPLICATIONINSIGHTS_CONNECTION_STRING}"
    ),
    service_name="agenticraft-app"
)
telemetry.initialize()
```

### Using OpenTelemetry Collector

```yaml
# otel-collector-azure.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

exporters:
  azuremonitor:
    instrumentation_key: ${INSTRUMENTATION_KEY}
    endpoint: https://dc.services.visualstudio.com/v2/track

processors:
  batch:
  memory_limiter:
    check_interval: 1s
    limit_mib: 512

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [azuremonitor]
```

## Google Cloud Trace

### Direct Integration

```python
# Install Google Cloud Trace exporter
# pip install opentelemetry-exporter-gcp-trace

from agenticraft.telemetry import TelemetryConfig
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

# Configure with Cloud Trace
telemetry = TelemetryConfig(
    enabled=True,
    custom_exporter=CloudTraceSpanExporter(
        project_id="${GCP_PROJECT_ID}"
    ),
    service_name="agenticraft-app"
)
telemetry.initialize()
```

### Using Google Cloud Run

```dockerfile
# Dockerfile for Cloud Run
FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy app
COPY . /app
WORKDIR /app

# Configure for Cloud Trace
ENV AGENTICRAFT_TELEMETRY_ENABLED=true
ENV GOOGLE_CLOUD_PROJECT=${GCP_PROJECT_ID}

# Run
CMD ["python", "-m", "agenticraft"]
```

### GKE Configuration

```yaml
# gke-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agenticraft-app
spec:
  template:
    spec:
      serviceAccountName: agenticraft-sa
      containers:
      - name: app
        image: gcr.io/project/agenticraft:latest
        env:
        - name: AGENTICRAFT_TELEMETRY_ENABLED
          value: "true"
        - name: GOOGLE_APPLICATION_CREDENTIALS
          value: /var/secrets/google/key.json
        volumeMounts:
        - name: google-cloud-key
          mountPath: /var/secrets/google
      volumes:
      - name: google-cloud-key
        secret:
          secretName: gcp-key
```

## Elastic APM

### Direct Integration

```python
# Install Elastic APM
# pip install elastic-apm opentelemetry-exporter-otlp

from agenticraft.telemetry import TelemetryConfig

telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    otlp_endpoint="${ELASTIC_APM_SERVER_URL}",
    otlp_headers={
        "Authorization": "Bearer ${ELASTIC_APM_SECRET_TOKEN}"
    },
    service_name="agenticraft-app",
    service_version="1.0.0",
    deployment_environment="production"
)
telemetry.initialize()
```

### Elastic Stack Docker Compose

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false
    ports:
      - "9200:9200"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200

  apm-server:
    image: docker.elastic.co/apm/apm-server:8.11.0
    ports:
      - "8200:8200"
    environment:
      - output.elasticsearch.hosts=["elasticsearch:9200"]
    command: >
      apm-server -e
        -E apm-server.rum.enabled=true
        -E setup.kibana.host=kibana:5601
```

## Custom Collectors

### Building a Custom Collector

```python
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from typing import Sequence
from opentelemetry.sdk.trace import ReadableSpan

class CustomSpanExporter(SpanExporter):
    """Custom span exporter for proprietary systems."""
    
    def __init__(self, endpoint: str, api_key: str):
        self.endpoint = endpoint
        self.api_key = api_key
        
    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export spans to custom backend."""
        try:
            # Convert spans to your format
            data = self._convert_spans(spans)
            
            # Send to your backend
            response = requests.post(
                self.endpoint,
                json=data,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if response.status_code == 200:
                return SpanExportResult.SUCCESS
            else:
                return SpanExportResult.FAILURE
                
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return SpanExportResult.FAILURE
            
    def shutdown(self) -> None:
        """Cleanup resources."""
        pass
        
    def _convert_spans(self, spans: Sequence[ReadableSpan]) -> dict:
        """Convert OpenTelemetry spans to custom format."""
        return {
            "spans": [
                {
                    "traceId": span.context.trace_id,
                    "spanId": span.context.span_id,
                    "name": span.name,
                    "startTime": span.start_time,
                    "endTime": span.end_time,
                    "attributes": dict(span.attributes),
                    "events": [
                        {
                            "name": event.name,
                            "timestamp": event.timestamp,
                            "attributes": dict(event.attributes)
                        }
                        for event in span.events
                    ]
                }
                for span in spans
            ]
        }

# Use with AgentiCraft
from agenticraft.telemetry import TelemetryConfig

telemetry = TelemetryConfig(
    enabled=True,
    custom_exporter=CustomSpanExporter(
        endpoint="https://telemetry.company.com/v1/spans",
        api_key="your-api-key"
    )
)
telemetry.initialize()
```

### OpenTelemetry Collector Plugin

```go
// custom_exporter.go
package customexporter

import (
    "context"
    "go.opentelemetry.io/collector/component"
    "go.opentelemetry.io/collector/exporter"
    "go.opentelemetry.io/collector/pdata/ptrace"
)

type customExporter struct {
    config *Config
}

func (e *customExporter) pushTraces(ctx context.Context, td ptrace.Traces) error {
    // Convert and send traces to your backend
    return nil
}

func createTracesExporter(
    ctx context.Context,
    set exporter.CreateSettings,
    cfg component.Config,
) (exporter.Traces, error) {
    config := cfg.(*Config)
    return &customExporter{config: config}, nil
}
```

## Integration Best Practices

### 1. Use Environment-Specific Endpoints

```python
import os

environment = os.getenv("ENVIRONMENT", "development")

endpoints = {
    "development": "localhost:4317",
    "staging": "staging-collector.company.com:4317",
    "production": "prod-collector.company.com:4317"
}

telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="otlp",
    otlp_endpoint=endpoints[environment]
)
```

### 2. Implement Health Checks

```python
from agenticraft.telemetry import get_telemetry_health

@app.route("/health/telemetry")
def telemetry_health():
    health = get_telemetry_health()
    
    if health.is_healthy:
        return {"status": "healthy", "details": health.to_dict()}, 200
    else:
        return {"status": "unhealthy", "details": health.to_dict()}, 503
```

### 3. Multi-Backend Resilience

```python
from agenticraft.telemetry import TelemetryConfig, FallbackExporter

# Configure with fallback
telemetry = TelemetryConfig(
    enabled=True,
    exporter_type="fallback",
    exporters=[
        {
            "type": "otlp",
            "endpoint": "primary-collector:4317",
            "timeout": 5000
        },
        {
            "type": "otlp",
            "endpoint": "backup-collector:4317",
            "timeout": 5000
        },
        {
            "type": "console",  # Last resort
            "pretty_print": False
        }
    ]
)
```

### 4. Security Considerations

```python
# Encrypt sensitive attributes
from agenticraft.telemetry import AttributeEncryptor

telemetry = TelemetryConfig(
    enabled=True,
    attribute_processors=[
        AttributeEncryptor(
            keys=["user.email", "api.key"],
            encryption_key=os.getenv("TELEMETRY_ENCRYPTION_KEY")
        )
    ]
)
```

### 5. Cost Management

```python
# Implement cost-aware sampling
from agenticraft.telemetry import CostAwareSampler

telemetry = TelemetryConfig(
    enabled=True,
    sampler=CostAwareSampler(
        base_rate=0.1,
        high_value_paths=["/api/v1/critical"],
        high_value_rate=1.0,
        monthly_budget_traces=1_000_000
    )
)
```

## Monitoring the Monitors

### Telemetry Pipeline Monitoring

```python
# Monitor your telemetry pipeline
from agenticraft.telemetry import TelemetryMetrics

@app.route("/metrics/telemetry")
def telemetry_metrics():
    metrics = TelemetryMetrics.get_current()
    
    return {
        "spans_created": metrics.spans_created,
        "spans_exported": metrics.spans_exported,
        "export_errors": metrics.export_errors,
        "queue_size": metrics.queue_size,
        "last_export_timestamp": metrics.last_export_timestamp,
        "export_latency_p99": metrics.export_latency_p99
    }
```

### Alerting Rules

```yaml
# prometheus-alerts.yml
groups:
  - name: telemetry
    rules:
      - alert: TelemetryExportFailure
        expr: rate(agenticraft_telemetry_export_errors[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High telemetry export failure rate"
          
      - alert: TelemetryQueueFull
        expr: agenticraft_telemetry_queue_size > 8000
        for: 2m
        annotations:
          summary: "Telemetry queue is backing up"
          
      - alert: TelemetryHighLatency
        expr: histogram_quantile(0.99, agenticraft_telemetry_export_duration) > 5
        for: 5m
        annotations:
          summary: "Telemetry export latency is high"
```

## Troubleshooting Common Issues

### No Data in Backend

1. Check exporter configuration:
   ```python
   from agenticraft.telemetry import get_telemetry_config
   
   config = get_telemetry_config()
   print(f"Enabled: {config.enabled}")
   print(f"Exporter: {config.exporter_type}")
   print(f"Endpoint: {config.otlp_endpoint}")
   ```

2. Enable debug logging:
   ```python
   import logging
   logging.getLogger("opentelemetry").setLevel(logging.DEBUG)
   ```

3. Test connectivity:
   ```bash
   telnet ${OTLP_ENDPOINT_HOST} ${OTLP_ENDPOINT_PORT}
   ```

### High Memory Usage

1. Reduce batch size:
   ```python
   telemetry = TelemetryConfig(batch_size=256)
   ```

2. Increase export frequency:
   ```python
   telemetry = TelemetryConfig(export_interval_ms=1000)
   ```

3. Enable sampling:
   ```python
   telemetry = TelemetryConfig(sample_rate=0.1)
   ```

### Data Not Correlated

1. Ensure context propagation:
   ```python
   from agenticraft.telemetry import get_current_context
   
   context = get_current_context()
   # Pass context to async operations
   ```

2. Check service naming:
   ```python
   # Consistent service names across instances
   telemetry = TelemetryConfig(
       service_name="agenticraft-api",
       service_namespace="ai-platform"
   )
   ```

## Next Steps

- Review [Metrics Reference](metrics-reference.md) for available metrics
- Check [Performance Guide](performance.md) for optimization tips
- See [Examples](../../examples/telemetry/) for real-world usage
