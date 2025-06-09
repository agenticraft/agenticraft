# Telemetry Metrics Reference

Complete reference for all metrics collected by AgentiCraft's telemetry system.

## Metric Naming Convention

All AgentiCraft metrics follow a consistent naming pattern:

```
agenticraft.<component>.<measurement>.<unit>
```

Examples:
- `agenticraft.agent.requests.total`
- `agenticraft.tokens.used.count`
- `agenticraft.latency.provider.milliseconds`

## Automatic Metrics

These metrics are automatically collected when telemetry is enabled.

### Agent Metrics

#### agenticraft.agent.requests.total
- **Type**: Counter
- **Unit**: 1 (count)
- **Description**: Total number of agent requests
- **Attributes**:
  - `agent.name`: Name of the agent
  - `agent.type`: Type of agent (base, reasoning, workflow, etc.)
  - `status`: Success or failure

#### agenticraft.agent.latency.milliseconds
- **Type**: Histogram
- **Unit**: milliseconds
- **Description**: Agent request processing time
- **Attributes**:
  - `agent.name`: Name of the agent
  - `agent.type`: Type of agent
  - `operation`: Operation performed (execute, plan, reason)
- **Buckets**: [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]

#### agenticraft.agent.errors.total
- **Type**: Counter
- **Unit**: 1 (count)
- **Description**: Total number of agent errors
- **Attributes**:
  - `agent.name`: Name of the agent
  - `error.type`: Exception class name
  - `operation`: Operation that failed

#### agenticraft.agent.active.count
- **Type**: Gauge
- **Unit**: 1 (count)
- **Description**: Number of currently active agents
- **Attributes**:
  - `agent.type`: Type of agent

### Token Usage Metrics

#### agenticraft.tokens.prompt.total
- **Type**: Counter
- **Unit**: 1 (tokens)
- **Description**: Total prompt tokens consumed
- **Attributes**:
  - `provider`: LLM provider (openai, anthropic, ollama)
  - `model`: Model name (gpt-4, claude-3, etc.)
  - `agent.name`: Agent that made the request

#### agenticraft.tokens.completion.total
- **Type**: Counter
- **Unit**: 1 (tokens)
- **Description**: Total completion tokens generated
- **Attributes**:
  - `provider`: LLM provider
  - `model`: Model name
  - `agent.name`: Agent that made the request

#### agenticraft.tokens.total.total
- **Type**: Counter
- **Unit**: 1 (tokens)
- **Description**: Total tokens (prompt + completion)
- **Attributes**:
  - `provider`: LLM provider
  - `model`: Model name
  - `agent.name`: Agent that made the request

#### agenticraft.tokens.cost.dollars
- **Type**: Counter
- **Unit**: dollars
- **Description**: Estimated cost of token usage
- **Attributes**:
  - `provider`: LLM provider
  - `model`: Model name
  - `agent.name`: Agent that made the request

### Provider Metrics

#### agenticraft.provider.requests.total
- **Type**: Counter
- **Unit**: 1 (count)
- **Description**: Total provider API requests
- **Attributes**:
  - `provider`: Provider name
  - `model`: Model name
  - `status`: Success or failure

#### agenticraft.provider.latency.milliseconds
- **Type**: Histogram
- **Unit**: milliseconds
- **Description**: Provider API response time
- **Attributes**:
  - `provider`: Provider name
  - `model`: Model name
  - `operation`: Type of operation (complete, stream, embed)
- **Buckets**: [50, 100, 250, 500, 1000, 2500, 5000, 10000, 25000]

#### agenticraft.provider.errors.total
- **Type**: Counter
- **Unit**: 1 (count)
- **Description**: Provider API errors
- **Attributes**:
  - `provider`: Provider name
  - `error.type`: Error type (rate_limit, timeout, api_error)
  - `status_code`: HTTP status code (if applicable)

#### agenticraft.provider.rate_limit.remaining
- **Type**: Gauge
- **Unit**: 1 (requests)
- **Description**: Remaining rate limit
- **Attributes**:
  - `provider`: Provider name
  - `limit_type`: requests_per_minute, tokens_per_minute

### Tool Metrics

#### agenticraft.tool.executions.total
- **Type**: Counter
- **Unit**: 1 (count)
- **Description**: Total tool executions
- **Attributes**:
  - `tool.name`: Name of the tool
  - `tool.category`: Tool category
  - `status`: Success or failure

#### agenticraft.tool.latency.milliseconds
- **Type**: Histogram
- **Unit**: milliseconds
- **Description**: Tool execution time
- **Attributes**:
  - `tool.name`: Name of the tool
  - `tool.category`: Tool category
- **Buckets**: [10, 50, 100, 500, 1000, 5000, 10000, 30000]

#### agenticraft.tool.errors.total
- **Type**: Counter
- **Unit**: 1 (count)
- **Description**: Tool execution errors
- **Attributes**:
  - `tool.name`: Name of the tool
  - `error.type`: Exception class name

#### agenticraft.tool.input.size.bytes
- **Type**: Histogram
- **Unit**: bytes
- **Description**: Size of tool input data
- **Attributes**:
  - `tool.name`: Name of the tool
- **Buckets**: [100, 1000, 10000, 100000, 1000000]

#### agenticraft.tool.output.size.bytes
- **Type**: Histogram
- **Unit**: bytes
- **Description**: Size of tool output data
- **Attributes**:
  - `tool.name`: Name of the tool
- **Buckets**: [100, 1000, 10000, 100000, 1000000]

### Memory Metrics

#### agenticraft.memory.operations.total
- **Type**: Counter
- **Unit**: 1 (count)
- **Description**: Total memory operations
- **Attributes**:
  - `operation`: store, retrieve, search, delete
  - `memory.type`: simple, vector, graph
  - `status`: Success or failure

#### agenticraft.memory.latency.milliseconds
- **Type**: Histogram
- **Unit**: milliseconds
- **Description**: Memory operation latency
- **Attributes**:
  - `operation`: store, retrieve, search, delete
  - `memory.type`: simple, vector, graph
- **Buckets**: [1, 5, 10, 25, 50, 100, 250, 500]

#### agenticraft.memory.size.items
- **Type**: Gauge
- **Unit**: 1 (items)
- **Description**: Number of items in memory
- **Attributes**:
  - `memory.type`: simple, vector, graph

#### agenticraft.memory.size.bytes
- **Type**: Gauge
- **Unit**: bytes
- **Description**: Memory storage size
- **Attributes**:
  - `memory.type`: simple, vector, graph

#### agenticraft.memory.hits.total
- **Type**: Counter
- **Unit**: 1 (count)
- **Description**: Memory cache hits
- **Attributes**:
  - `memory.type`: simple, vector, graph

#### agenticraft.memory.misses.total
- **Type**: Counter
- **Unit**: 1 (count)
- **Description**: Memory cache misses
- **Attributes**:
  - `memory.type`: simple, vector, graph

### Workflow Metrics

#### agenticraft.workflow.executions.total
- **Type**: Counter
- **Unit**: 1 (count)
- **Description**: Total workflow executions
- **Attributes**:
  - `workflow.name`: Name of the workflow
  - `status`: Success, failure, cancelled

#### agenticraft.workflow.latency.milliseconds
- **Type**: Histogram
- **Unit**: milliseconds
- **Description**: Workflow execution time
- **Attributes**:
  - `workflow.name`: Name of the workflow
- **Buckets**: [100, 500, 1000, 5000, 10000, 30000, 60000, 300000]

#### agenticraft.workflow.steps.total
- **Type**: Counter
- **Unit**: 1 (count)
- **Description**: Total workflow steps executed
- **Attributes**:
  - `workflow.name`: Name of the workflow
  - `step.name`: Name of the step
  - `status`: Success or failure

#### agenticraft.workflow.active.count
- **Type**: Gauge
- **Unit**: 1 (count)
- **Description**: Currently active workflows
- **Attributes**:
  - `workflow.name`: Name of the workflow

### Reasoning Metrics

#### agenticraft.reasoning.operations.total
- **Type**: Counter
- **Unit**: 1 (count)
- **Description**: Total reasoning operations
- **Attributes**:
  - `pattern`: chain_of_thought, tree_of_thoughts, react
  - `status`: Success or failure

#### agenticraft.reasoning.latency.milliseconds
- **Type**: Histogram
- **Unit**: milliseconds
- **Description**: Reasoning operation time
- **Attributes**:
  - `pattern`: Reasoning pattern used
- **Buckets**: [100, 500, 1000, 2500, 5000, 10000, 25000]

#### agenticraft.reasoning.steps.count
- **Type**: Histogram
- **Unit**: 1 (steps)
- **Description**: Number of reasoning steps
- **Attributes**:
  - `pattern`: Reasoning pattern used
- **Buckets**: [1, 2, 3, 5, 10, 20, 50, 100]

#### agenticraft.reasoning.confidence.ratio
- **Type**: Histogram
- **Unit**: ratio (0-1)
- **Description**: Reasoning confidence score
- **Attributes**:
  - `pattern`: Reasoning pattern used
- **Buckets**: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]

### Streaming Metrics

#### agenticraft.streaming.chunks.total
- **Type**: Counter
- **Unit**: 1 (count)
- **Description**: Total stream chunks sent
- **Attributes**:
  - `provider`: LLM provider
  - `model`: Model name

#### agenticraft.streaming.latency.first_chunk.milliseconds
- **Type**: Histogram
- **Unit**: milliseconds
- **Description**: Time to first stream chunk
- **Attributes**:
  - `provider`: LLM provider
  - `model`: Model name
- **Buckets**: [10, 25, 50, 100, 250, 500, 1000, 2500]

#### agenticraft.streaming.duration.milliseconds
- **Type**: Histogram
- **Unit**: milliseconds
- **Description**: Total stream duration
- **Attributes**:
  - `provider`: LLM provider
  - `model`: Model name
- **Buckets**: [100, 500, 1000, 5000, 10000, 30000, 60000]

#### agenticraft.streaming.interruptions.total
- **Type**: Counter
- **Unit**: 1 (count)
- **Description**: Stream interruptions
- **Attributes**:
  - `provider`: LLM provider
  - `reason`: timeout, user_cancelled, error

### System Metrics

#### agenticraft.system.cpu.percent
- **Type**: Gauge
- **Unit**: percent
- **Description**: CPU usage percentage
- **Attributes**:
  - `process`: agenticraft

#### agenticraft.system.memory.bytes
- **Type**: Gauge
- **Unit**: bytes
- **Description**: Memory usage
- **Attributes**:
  - `process`: agenticraft
  - `type`: rss, vms, heap

#### agenticraft.system.threads.count
- **Type**: Gauge
- **Unit**: 1 (count)
- **Description**: Number of active threads
- **Attributes**:
  - `process`: agenticraft

#### agenticraft.system.gc.count
- **Type**: Counter
- **Unit**: 1 (count)
- **Description**: Garbage collection runs
- **Attributes**:
  - `generation`: 0, 1, 2

#### agenticraft.system.gc.duration.milliseconds
- **Type**: Histogram
- **Unit**: milliseconds
- **Description**: Garbage collection duration
- **Attributes**:
  - `generation`: 0, 1, 2
- **Buckets**: [1, 5, 10, 25, 50, 100, 250, 500]

## Custom Metrics

### Creating Custom Counters

```python
from agenticraft.telemetry import create_counter

# Create a counter for processed documents
doc_counter = create_counter(
    name="custom.documents.processed",
    description="Number of documents processed",
    unit="1"
)

# Use in your code
doc_counter.add(1, {
    "document.type": "pdf",
    "document.size": "large",
    "processor.version": "2.0"
})
```

### Creating Custom Histograms

```python
from agenticraft.telemetry import create_histogram

# Create a histogram for processing time
processing_time = create_histogram(
    name="custom.processing.duration",
    description="Document processing duration",
    unit="milliseconds",
    boundaries=[10, 50, 100, 500, 1000, 5000]
)

# Record values
processing_time.record(
    value=234.5,
    attributes={
        "processor": "nlp",
        "complexity": "high"
    }
)
```

### Creating Custom Gauges

```python
from agenticraft.telemetry import create_gauge

# Create a gauge for queue size
def get_queue_size():
    return len(processing_queue)

queue_gauge = create_gauge(
    name="custom.queue.size",
    description="Processing queue size",
    unit="1"
)

# Register callback
queue_gauge.add_callback(
    callback=get_queue_size,
    attributes={"queue.name": "documents"}
)
```

## Metric Aggregations

### Prometheus Queries

```promql
# Request rate per minute
rate(agenticraft_agent_requests_total[1m])

# Average latency by agent
avg by (agent_name) (
  rate(agenticraft_agent_latency_milliseconds_sum[5m]) /
  rate(agenticraft_agent_latency_milliseconds_count[5m])
)

# 95th percentile latency
histogram_quantile(0.95,
  rate(agenticraft_provider_latency_milliseconds_bucket[5m])
)

# Error rate percentage
100 * (
  rate(agenticraft_agent_errors_total[5m]) /
  rate(agenticraft_agent_requests_total[5m])
)

# Token usage per hour by model
sum by (model) (
  increase(agenticraft_tokens_total_total[1h])
)

# Memory hit rate
rate(agenticraft_memory_hits_total[5m]) /
(rate(agenticraft_memory_hits_total[5m]) + rate(agenticraft_memory_misses_total[5m]))

# Cost per agent last 24h
sum by (agent_name) (
  increase(agenticraft_tokens_cost_dollars[24h])
)
```

### Grafana Dashboard Panels

#### Request Overview
```json
{
  "title": "Request Rate",
  "targets": [{
    "expr": "sum(rate(agenticraft_agent_requests_total[5m]))",
    "legendFormat": "Total RPS"
  }]
}
```

#### Latency Distribution
```json
{
  "title": "Latency Percentiles",
  "targets": [
    {
      "expr": "histogram_quantile(0.50, rate(agenticraft_agent_latency_milliseconds_bucket[5m]))",
      "legendFormat": "p50"
    },
    {
      "expr": "histogram_quantile(0.90, rate(agenticraft_agent_latency_milliseconds_bucket[5m]))",
      "legendFormat": "p90"
    },
    {
      "expr": "histogram_quantile(0.99, rate(agenticraft_agent_latency_milliseconds_bucket[5m]))",
      "legendFormat": "p99"
    }
  ]
}
```

## Metric Best Practices

### 1. Attribute Cardinality

Keep attribute cardinality low to prevent metric explosion:

```python
# Bad - High cardinality
metric.add(1, {"user_id": user_id})  # Millions of values

# Good - Low cardinality
metric.add(1, {"user_tier": get_user_tier(user_id)})  # Few values
```

### 2. Consistent Naming

Follow the naming convention:

```python
# Good names
"agenticraft.cache.hits.total"
"agenticraft.api.latency.milliseconds"
"agenticraft.queue.size.items"

# Bad names
"hits"  # Too generic
"agenticraft_cache_hits"  # Wrong separator
"latency"  # Missing unit
```

### 3. Meaningful Attributes

Include attributes that aid in debugging and analysis:

```python
# Good attributes
processing_time.record(duration, {
    "stage": "preprocessing",
    "document_type": "pdf",
    "size_category": "large",  # Not exact size
    "version": "2.0"
})

# Avoid sensitive data
# Never include: user_email, api_keys, passwords, PII
```

### 4. Histogram Buckets

Choose buckets that match your SLOs:

```python
# For API latency (SLO: 99% < 1s)
latency_histogram = create_histogram(
    name="api.latency",
    boundaries=[10, 50, 100, 250, 500, 750, 1000, 2000, 5000]
)

# For batch processing (SLO: 99% < 5m)
batch_histogram = create_histogram(
    name="batch.duration",
    boundaries=[1000, 10000, 30000, 60000, 120000, 180000, 300000]
)
```

### 5. Resource Metrics

Monitor resource usage to prevent issues:

```python
# Alert on high memory usage
if memory_gauge.get() > 0.9 * max_memory:
    alert("High memory usage detected")
```

## Alerting Examples

### Prometheus Alert Rules

```yaml
groups:
  - name: agenticraft
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          rate(agenticraft_agent_errors_total[5m]) /
          rate(agenticraft_agent_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Error rate above 5%"
          
      # High latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.99,
            rate(agenticraft_agent_latency_milliseconds_bucket[5m])
          ) > 5000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P99 latency above 5s"
          
      # Token usage spike
      - alert: TokenUsageSpike
        expr: |
          rate(agenticraft_tokens_total_total[5m]) >
          2 * avg_over_time(rate(agenticraft_tokens_total_total[5m])[1h:5m])
        for: 10m
        labels:
          severity: info
        annotations:
          summary: "Token usage 2x above average"
          
      # Memory pressure
      - alert: HighMemoryUsage
        expr: |
          agenticraft_system_memory_bytes{type="rss"} /
          agenticraft_system_memory_bytes{type="limit"} > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memory usage above 80%"
```

## Performance Impact

Metric collection overhead:

| Operation | Overhead |
|-----------|----------|
| Counter increment | ~10ns |
| Histogram record | ~50ns |
| Gauge callback | ~100ns |
| Attribute addition | ~20ns per attribute |

Total overhead with standard instrumentation: <1% of request time

## Troubleshooting Metrics

### Missing Metrics

1. Verify telemetry is enabled:
   ```python
   from agenticraft.telemetry import is_telemetry_enabled
   print(f"Telemetry enabled: {is_telemetry_enabled()}")
   ```

2. Check metric registration:
   ```python
   from agenticraft.telemetry import list_metrics
   for metric in list_metrics():
       print(f"{metric.name}: {metric.description}")
   ```

### Incorrect Values

1. Verify units:
   ```python
   # Ensure consistent units
   latency_ms = latency_seconds * 1000
   histogram.record(latency_ms)
   ```

2. Check attribute values:
   ```python
   # Log attributes for debugging
   logger.debug(f"Recording metric with attributes: {attributes}")
   ```

### High Cardinality

Monitor cardinality:

```python
from agenticraft.telemetry import get_metric_cardinality

for metric_name, cardinality in get_metric_cardinality().items():
    if cardinality > 1000:
        logger.warning(f"High cardinality metric: {metric_name} = {cardinality}")
```

## Next Steps

- [Integration Guide](integration.md) - Connect to monitoring platforms
- [Configuration Guide](configuration.md) - Detailed configuration options
- [Examples](../../examples/telemetry/) - Real-world usage examples
