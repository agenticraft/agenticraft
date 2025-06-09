"""Telemetry module for AgentiCraft.

This module provides observability capabilities including:
- Distributed tracing with OpenTelemetry
- Metrics collection and export
- Performance monitoring
- Error tracking
"""

from .decorators import (
    count_calls,
    measure_time,
    observe_value,
    trace,
    trace_agent_method,
    trace_tool_execution,
    track_metrics,
)
from .metrics import (
    LatencyTimer,
    MetricsCollector,
    MetricsConfig,
    get_meter,
    initialize_metrics,
    record_error,
    record_latency,
    record_memory_operation,
    record_token_usage,
    shutdown_metrics,
)
from .tracer import (
    TracerConfig,
    create_span,
    get_current_trace_id,
    get_tracer,
    initialize_tracer,
    record_exception,
    set_span_attributes,
    shutdown_tracer,
)

__all__ = [
    # Tracer
    "get_tracer",
    "create_span",
    "set_span_attributes",
    "record_exception",
    "TracerConfig",
    "get_current_trace_id",
    "initialize_tracer",
    "shutdown_tracer",
    # Metrics
    "get_meter",
    "MetricsCollector",
    "record_token_usage",
    "record_latency",
    "record_error",
    "record_memory_operation",
    "LatencyTimer",
    "initialize_metrics",
    "shutdown_metrics",
    "MetricsConfig",
    # Decorators
    "track_metrics",
    "trace",
    "measure_time",
    "count_calls",
    "observe_value",
    "trace_agent_method",
    "trace_tool_execution",
]
