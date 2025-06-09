"""Metrics collection for AgentiCraft.

This module provides metrics collection capabilities including:
- Token usage tracking per provider
- Response latency measurements
- Tool execution time
- Memory operation metrics
- Error rate tracking
"""

import time
from collections import defaultdict
from typing import Any, Optional

from opentelemetry import metrics
from opentelemetry.metrics import CallbackOptions, Observation
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource

# Optional imports for exporters
try:
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter,
    )

    HAS_OTLP = True
except ImportError:
    HAS_OTLP = False
    OTLPMetricExporter = None

try:
    from opentelemetry.exporter.prometheus import PrometheusMetricReader

    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    PrometheusMetricReader = None

from pydantic import BaseModel


class MetricsConfig(BaseModel):
    """Configuration for metrics collection."""

    service_name: str = "agenticraft"
    service_version: str = "0.2.0"
    enabled: bool = True
    exporter_type: str = "console"  # console, otlp, prometheus
    otlp_endpoint: str | None = None
    prometheus_port: int = 8000
    export_interval_millis: int = 60000  # 1 minute

    # Metric settings
    enable_token_metrics: bool = True
    enable_latency_metrics: bool = True
    enable_error_metrics: bool = True
    enable_memory_metrics: bool = True


# Global meter instance
_meter_provider: MeterProvider | None = None
_meter: metrics.Meter | None = None
_config: MetricsConfig | None = None
_metrics_collector: Optional["MetricsCollector"] = None


def initialize_metrics(config: MetricsConfig | None = None) -> metrics.Meter:
    """Initialize the metrics system.

    Args:
        config: Metrics configuration

    Returns:
        Configured meter instance
    """
    global _meter_provider, _meter, _config, _metrics_collector

    if _meter is not None and config is None:
        return _meter

    _config = config or MetricsConfig()

    if not _config.enabled:
        # Use no-op meter when disabled
        metrics.set_meter_provider(metrics.NoOpMeterProvider())
        _meter = metrics.get_meter(__name__)
        return _meter

    # Create resource
    resource = Resource.create(
        {
            SERVICE_NAME: _config.service_name,
            SERVICE_VERSION: _config.service_version,
        }
    )

    # Configure exporter and reader
    if _config.exporter_type == "console":
        reader = PeriodicExportingMetricReader(
            ConsoleMetricExporter(),
            export_interval_millis=_config.export_interval_millis,
        )
    elif _config.exporter_type == "otlp":
        if not HAS_OTLP:
            raise ImportError(
                "OTLP exporter not available. Install with: pip install agenticraft[telemetry]"
            )
        reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(
                endpoint=_config.otlp_endpoint or "localhost:4317", insecure=True
            ),
            export_interval_millis=_config.export_interval_millis,
        )
    elif _config.exporter_type == "prometheus":
        if not HAS_PROMETHEUS:
            raise ImportError(
                "Prometheus exporter not available. Install with: pip install agenticraft[telemetry]"
            )
        reader = PrometheusMetricReader(port=_config.prometheus_port)
    else:
        raise ValueError(f"Unknown exporter type: {_config.exporter_type}")

    # Create meter provider
    _meter_provider = MeterProvider(resource=resource, metric_readers=[reader])

    # Set as global provider
    metrics.set_meter_provider(_meter_provider)

    # Get meter
    _meter = metrics.get_meter(_config.service_name, _config.service_version)

    # Initialize metrics collector
    _metrics_collector = MetricsCollector(_meter, _config)

    return _meter


def get_meter() -> metrics.Meter:
    """Get the global meter instance.

    Returns:
        The meter instance
    """
    if _meter is None:
        return initialize_metrics()
    return _meter


def get_metrics_collector() -> "MetricsCollector":
    """Get the global metrics collector.

    Returns:
        The metrics collector instance
    """
    if _metrics_collector is None:
        initialize_metrics()
    return _metrics_collector


class MetricsCollector:
    """Collects and manages metrics for AgentiCraft."""

    def __init__(self, meter: metrics.Meter, config: MetricsConfig):
        """Initialize metrics collector.

        Args:
            meter: OpenTelemetry meter
            config: Metrics configuration
        """
        self.meter = meter
        self.config = config

        # Internal state for metrics
        self._token_usage = defaultdict(
            lambda: {"prompt": 0, "completion": 0, "total": 0}
        )
        self._latencies = defaultdict(list)
        self._errors = defaultdict(int)
        self._memory_ops = defaultdict(lambda: {"hits": 0, "misses": 0, "total": 0})

        # Create instruments
        self._setup_instruments()

    def _setup_instruments(self) -> None:
        """Set up OpenTelemetry instruments."""

        # Token usage metrics
        if self.config.enable_token_metrics:
            self.token_counter = self.meter.create_counter(
                "agenticraft.tokens.total",
                unit="tokens",
                description="Total tokens used",
            )

            self.meter.create_observable_gauge(
                "agenticraft.tokens.by_provider",
                callbacks=[self._observe_token_usage],
                unit="tokens",
                description="Token usage by provider",
            )

        # Latency metrics
        if self.config.enable_latency_metrics:
            self.latency_histogram = self.meter.create_histogram(
                "agenticraft.latency", unit="ms", description="Operation latency"
            )

            self.meter.create_observable_gauge(
                "agenticraft.latency.p99",
                callbacks=[self._observe_latency_percentiles],
                unit="ms",
                description="99th percentile latency",
            )

        # Error metrics
        if self.config.enable_error_metrics:
            self.error_counter = self.meter.create_counter(
                "agenticraft.errors.total", unit="errors", description="Total errors"
            )

            self.meter.create_observable_gauge(
                "agenticraft.errors.rate",
                callbacks=[self._observe_error_rate],
                unit="errors/min",
                description="Error rate per minute",
            )

        # Memory metrics
        if self.config.enable_memory_metrics:
            self.memory_counter = self.meter.create_counter(
                "agenticraft.memory.operations",
                unit="operations",
                description="Memory operations",
            )

            self.meter.create_observable_gauge(
                "agenticraft.memory.hit_rate",
                callbacks=[self._observe_memory_hit_rate],
                unit="ratio",
                description="Memory cache hit rate",
            )

    def record_tokens(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int | None = None,
    ) -> None:
        """Record token usage.

        Args:
            provider: LLM provider name
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            total_tokens: Total tokens (computed if not provided)
        """
        if not self.config.enable_token_metrics:
            return

        total = total_tokens or (prompt_tokens + completion_tokens)

        # Update internal state
        key = f"{provider}:{model}"
        self._token_usage[key]["prompt"] += prompt_tokens
        self._token_usage[key]["completion"] += completion_tokens
        self._token_usage[key]["total"] += total

        # Record to counter
        attributes = {"provider": provider, "model": model, "token_type": "prompt"}
        self.token_counter.add(prompt_tokens, attributes)

        attributes["token_type"] = "completion"
        self.token_counter.add(completion_tokens, attributes)

    def record_latency(
        self,
        operation: str,
        duration_ms: float,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Record operation latency.

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            attributes: Additional attributes
        """
        if not self.config.enable_latency_metrics:
            return

        # Store for percentile calculation
        self._latencies[operation].append(duration_ms)

        # Keep only last 1000 measurements per operation
        if len(self._latencies[operation]) > 1000:
            self._latencies[operation] = self._latencies[operation][-1000:]

        # Record to histogram
        attrs = {"operation": operation}
        if attributes:
            attrs.update(attributes)

        self.latency_histogram.record(duration_ms, attrs)

    def record_error(
        self,
        error_type: str,
        operation: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Record an error occurrence.

        Args:
            error_type: Type of error
            operation: Operation that failed
            attributes: Additional attributes
        """
        if not self.config.enable_error_metrics:
            return

        # Update internal state
        key = f"{operation}:{error_type}"
        self._errors[key] += 1

        # Record to counter
        attrs = {"error_type": error_type, "operation": operation}
        if attributes:
            attrs.update(attributes)

        self.error_counter.add(1, attrs)

    def record_memory_operation(
        self,
        operation: str,
        memory_type: str,
        hit: bool,
        size_bytes: int | None = None,
    ) -> None:
        """Record a memory operation.

        Args:
            operation: Operation type (get, set, delete)
            memory_type: Type of memory
            hit: Whether it was a cache hit
            size_bytes: Size of data
        """
        if not self.config.enable_memory_metrics:
            return

        # Update internal state
        key = f"{memory_type}:{operation}"
        self._memory_ops[key]["total"] += 1
        if hit:
            self._memory_ops[key]["hits"] += 1
        else:
            self._memory_ops[key]["misses"] += 1

        # Record to counter
        attrs = {"operation": operation, "memory_type": memory_type, "hit": str(hit)}
        if size_bytes is not None:
            attrs["size_bucket"] = self._get_size_bucket(size_bytes)

        self.memory_counter.add(1, attrs)

    def _get_size_bucket(self, size_bytes: int) -> str:
        """Get size bucket for memory operations."""
        if size_bytes < 1024:
            return "small"
        elif size_bytes < 1024 * 100:
            return "medium"
        elif size_bytes < 1024 * 1024:
            return "large"
        else:
            return "xlarge"

    def _observe_token_usage(self, options: CallbackOptions) -> list[Observation]:
        """Observable callback for token usage by provider."""
        observations = []

        for key, usage in self._token_usage.items():
            provider, model = key.split(":", 1)

            observations.extend(
                [
                    Observation(
                        usage["prompt"],
                        {"provider": provider, "model": model, "token_type": "prompt"},
                    ),
                    Observation(
                        usage["completion"],
                        {
                            "provider": provider,
                            "model": model,
                            "token_type": "completion",
                        },
                    ),
                    Observation(
                        usage["total"],
                        {"provider": provider, "model": model, "token_type": "total"},
                    ),
                ]
            )

        return observations

    def _observe_latency_percentiles(
        self, options: CallbackOptions
    ) -> list[Observation]:
        """Observable callback for latency percentiles."""
        observations = []

        for operation, latencies in self._latencies.items():
            if latencies:
                sorted_latencies = sorted(latencies)
                p50_idx = int(len(sorted_latencies) * 0.5)
                p90_idx = int(len(sorted_latencies) * 0.9)
                p99_idx = int(len(sorted_latencies) * 0.99)

                observations.extend(
                    [
                        Observation(
                            sorted_latencies[p50_idx],
                            {"operation": operation, "percentile": "p50"},
                        ),
                        Observation(
                            sorted_latencies[p90_idx],
                            {"operation": operation, "percentile": "p90"},
                        ),
                        Observation(
                            sorted_latencies[p99_idx],
                            {"operation": operation, "percentile": "p99"},
                        ),
                    ]
                )

        return observations

    def _observe_error_rate(self, options: CallbackOptions) -> list[Observation]:
        """Observable callback for error rate."""
        # Simple implementation - in production, use time-windowed counters
        observations = []

        for key, count in self._errors.items():
            operation, error_type = key.split(":", 1)
            # Simplified rate calculation
            rate = count / 60.0  # Assume per minute

            observations.append(
                Observation(rate, {"operation": operation, "error_type": error_type})
            )

        return observations

    def _observe_memory_hit_rate(self, options: CallbackOptions) -> list[Observation]:
        """Observable callback for memory hit rate."""
        observations = []

        for key, stats in self._memory_ops.items():
            memory_type, operation = key.split(":", 1)

            if stats["total"] > 0:
                hit_rate = stats["hits"] / stats["total"]
                observations.append(
                    Observation(
                        hit_rate, {"memory_type": memory_type, "operation": operation}
                    )
                )

        return observations


# Convenience functions


def record_token_usage(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int | None = None,
) -> None:
    """Record token usage for an LLM call.

    Args:
        provider: LLM provider
        model: Model name
        prompt_tokens: Prompt token count
        completion_tokens: Completion token count
        total_tokens: Total tokens
    """
    collector = get_metrics_collector()
    if collector:
        collector.record_tokens(
            provider, model, prompt_tokens, completion_tokens, total_tokens
        )


def record_latency(operation: str, duration_ms: float, **attributes) -> None:
    """Record operation latency.

    Args:
        operation: Operation name
        duration_ms: Duration in milliseconds
        **attributes: Additional attributes
    """
    collector = get_metrics_collector()
    if collector:
        collector.record_latency(operation, duration_ms, attributes)


def record_error(error_type: str, operation: str, **attributes) -> None:
    """Record an error.

    Args:
        error_type: Type of error
        operation: Operation that failed
        **attributes: Additional attributes
    """
    collector = get_metrics_collector()
    if collector:
        collector.record_error(error_type, operation, attributes)


def record_memory_operation(
    operation: str, memory_type: str, hit: bool, size_bytes: int | None = None
) -> None:
    """Record a memory operation.

    Args:
        operation: Operation type
        memory_type: Memory type
        hit: Cache hit status
        size_bytes: Data size
    """
    collector = get_metrics_collector()
    if collector:
        collector.record_memory_operation(operation, memory_type, hit, size_bytes)


# Timer context manager for measuring latency


class LatencyTimer:
    """Context manager for measuring operation latency."""

    def __init__(self, operation: str, **attributes):
        """Initialize timer.

        Args:
            operation: Operation name
            **attributes: Additional attributes
        """
        self.operation = operation
        self.attributes = attributes
        self.start_time = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record latency."""
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            record_latency(self.operation, duration_ms, **self.attributes)

        # Record error if exception occurred
        if exc_type:
            record_error(exc_type.__name__, self.operation, **self.attributes)


# Shutdown function
def shutdown_metrics() -> None:
    """Shutdown the metrics system."""
    global _meter_provider

    if _meter_provider:
        _meter_provider.shutdown()
        _meter_provider = None
