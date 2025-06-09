"""Telemetry and observability for AgentiCraft.

This module provides OpenTelemetry integration for monitoring and
observing agent behavior in production environments.

Example:
    Enabling telemetry::

        from agenticraft import Agent, Telemetry

        telemetry = Telemetry(
            service_name="my-agent-app",
            export_to="http://localhost:4317"
        )

        agent = Agent(
            name="MonitoredAgent",
            telemetry=telemetry
        )
"""

import os
from contextlib import contextmanager
from typing import Any

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import BaseModel, Field


class TelemetryConfig(BaseModel):
    """Configuration for telemetry."""

    service_name: str = Field(default="agenticraft")
    service_version: str = Field(default="0.1.0")
    export_endpoint: str | None = Field(default=None)
    export_headers: dict[str, str] = Field(default_factory=dict)
    enabled: bool = Field(default=True)
    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)

    @property
    def endpoint(self) -> str:
        """Get the export endpoint."""
        return self.export_endpoint or os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
        )


class Telemetry:
    """Telemetry manager for AgentiCraft.

    Provides OpenTelemetry integration for distributed tracing
    and metrics collection.

    Args:
        service_name: Name of your service
        service_version: Version of your service
        export_to: OTLP endpoint to export telemetry
        enabled: Whether telemetry is enabled
    """

    def __init__(
        self,
        service_name: str = "agenticraft",
        service_version: str = "0.1.0",
        export_to: str | None = None,
        enabled: bool = True,
    ):
        """Initialize telemetry."""
        self.config = TelemetryConfig(
            service_name=service_name,
            service_version=service_version,
            export_endpoint=export_to,
            enabled=enabled,
        )

        self._tracer: trace.Tracer | None = None
        self._meter: metrics.Meter | None = None

        if self.config.enabled:
            self._setup_telemetry()

    def _setup_telemetry(self) -> None:
        """Set up OpenTelemetry providers."""
        # Create resource
        resource = Resource.create(
            {
                "service.name": self.config.service_name,
                "service.version": self.config.service_version,
            }
        )

        # Set up tracing
        trace_provider = TracerProvider(resource=resource)

        if self.config.export_endpoint:
            span_exporter = OTLPSpanExporter(
                endpoint=self.config.endpoint, headers=self.config.export_headers
            )
            span_processor = BatchSpanProcessor(span_exporter)
            trace_provider.add_span_processor(span_processor)

        trace.set_tracer_provider(trace_provider)
        self._tracer = trace.get_tracer(
            self.config.service_name, self.config.service_version
        )

        # Set up metrics
        if self.config.export_endpoint:
            metric_exporter = OTLPMetricExporter(
                endpoint=self.config.endpoint, headers=self.config.export_headers
            )
            metric_reader = PeriodicExportingMetricReader(
                exporter=metric_exporter, export_interval_millis=60000  # 1 minute
            )
            meter_provider = MeterProvider(
                resource=resource, metric_readers=[metric_reader]
            )
        else:
            meter_provider = MeterProvider(resource=resource)

        metrics.set_meter_provider(meter_provider)
        self._meter = metrics.get_meter(
            self.config.service_name, self.config.service_version
        )

        # Create common metrics
        self._setup_metrics()

    def _setup_metrics(self) -> None:
        """Set up common metrics."""
        if not self._meter:
            return

        # Agent metrics
        self.agent_runs = self._meter.create_counter(
            "agenticraft.agent.runs", description="Number of agent runs"
        )

        self.agent_errors = self._meter.create_counter(
            "agenticraft.agent.errors", description="Number of agent errors"
        )

        self.agent_duration = self._meter.create_histogram(
            "agenticraft.agent.duration",
            description="Agent execution duration in seconds",
            unit="s",
        )

        # Tool metrics
        self.tool_executions = self._meter.create_counter(
            "agenticraft.tool.executions", description="Number of tool executions"
        )

        self.tool_errors = self._meter.create_counter(
            "agenticraft.tool.errors", description="Number of tool errors"
        )

        self.tool_duration = self._meter.create_histogram(
            "agenticraft.tool.duration",
            description="Tool execution duration in seconds",
            unit="s",
        )

        # Token metrics
        self.tokens_used = self._meter.create_counter(
            "agenticraft.tokens.used", description="Number of tokens used"
        )

    @property
    def tracer(self) -> trace.Tracer | None:
        """Get the tracer instance."""
        return self._tracer

    @property
    def meter(self) -> metrics.Meter | None:
        """Get the meter instance."""
        return self._meter

    @contextmanager
    def span(self, name: str, attributes: dict[str, Any] | None = None):
        """Create a traced span.

        Args:
            name: Span name
            attributes: Span attributes

        Example:
            with telemetry.span("agent.run", {"agent.name": "Assistant"}):
                # Do work
                pass
        """
        if not self._tracer or not self.config.enabled:
            yield None
            return

        with self._tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            yield span

    def record_agent_run(
        self,
        agent_name: str,
        duration: float,
        success: bool,
        tokens: int | None = None,
    ) -> None:
        """Record metrics for an agent run.

        Args:
            agent_name: Name of the agent
            duration: Execution duration in seconds
            success: Whether the run was successful
            tokens: Number of tokens used
        """
        if not self._meter or not self.config.enabled:
            return

        attributes = {"agent.name": agent_name}

        self.agent_runs.add(1, attributes)

        if not success:
            self.agent_errors.add(1, attributes)

        self.agent_duration.record(duration, attributes)

        if tokens is not None:
            self.tokens_used.add(tokens, attributes)

    def record_tool_execution(
        self, tool_name: str, duration: float, success: bool
    ) -> None:
        """Record metrics for a tool execution.

        Args:
            tool_name: Name of the tool
            duration: Execution duration in seconds
            success: Whether execution was successful
        """
        if not self._meter or not self.config.enabled:
            return

        attributes = {"tool.name": tool_name}

        self.tool_executions.add(1, attributes)

        if not success:
            self.tool_errors.add(1, attributes)

        self.tool_duration.record(duration, attributes)


# Global telemetry instance
_global_telemetry: Telemetry | None = None


def set_global_telemetry(telemetry: Telemetry) -> None:
    """Set the global telemetry instance.

    Args:
        telemetry: Telemetry instance to use globally
    """
    global _global_telemetry
    _global_telemetry = telemetry


def get_global_telemetry() -> Telemetry | None:
    """Get the global telemetry instance."""
    return _global_telemetry


def init_telemetry(
    service_name: str = "agenticraft",
    export_to: str | None = None,
    enabled: bool = True,
) -> Telemetry:
    """Initialize and set global telemetry.

    Args:
        service_name: Name of your service
        export_to: OTLP endpoint
        enabled: Whether telemetry is enabled

    Returns:
        Telemetry instance
    """
    telemetry = Telemetry(
        service_name=service_name, export_to=export_to, enabled=enabled
    )
    set_global_telemetry(telemetry)
    return telemetry
