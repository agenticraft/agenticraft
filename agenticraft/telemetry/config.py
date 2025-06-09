"""Telemetry configuration for AgentiCraft.

This module provides configuration management for OpenTelemetry
settings, including exporters, sampling, and instrumentation options.

Example:
    Basic configuration::

        from agenticraft.telemetry import TelemetryConfig

        config = TelemetryConfig(
            service_name="my-agent-service",
            export_endpoint="http://jaeger:4317",
            sample_rate=0.1,  # Sample 10% of traces
            export_metrics=True,
            export_traces=True
        )
"""

import os
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ExportFormat(str, Enum):
    """Supported telemetry export formats."""

    OTLP = "otlp"
    JAEGER = "jaeger"
    ZIPKIN = "zipkin"
    CONSOLE = "console"
    NONE = "none"


class TelemetryEnvironment(str, Enum):
    """Deployment environment for telemetry."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class ExporterConfig(BaseModel):
    """Configuration for telemetry exporters."""

    format: ExportFormat = Field(
        default=ExportFormat.OTLP, description="Export format to use"
    )
    endpoint: str | None = Field(default=None, description="Endpoint for exporter")
    headers: dict[str, str] = Field(
        default_factory=dict, description="Headers to include with exports"
    )
    timeout_ms: int = Field(default=30000, description="Export timeout in milliseconds")
    insecure: bool = Field(
        default=True, description="Whether to use insecure connection"
    )

    @model_validator(mode="after")
    def set_endpoint_defaults(self):
        """Set endpoint defaults based on format."""
        if self.endpoint is None and self.format != ExportFormat.CONSOLE:
            format_map = {
                ExportFormat.OTLP: "http://localhost:4317",
                ExportFormat.JAEGER: "http://localhost:14250",
                ExportFormat.ZIPKIN: "http://localhost:9411/api/v2/spans",
            }
            self.endpoint = format_map.get(self.format)
        return self


class ResourceConfig(BaseModel):
    """Resource attributes for telemetry."""

    service_name: str = Field(default="agenticraft", description="Name of the service")
    service_version: str = Field(
        default="unknown", description="Version of the service"
    )
    service_instance_id: str | None = Field(
        default=None, description="Unique instance identifier"
    )
    environment: TelemetryEnvironment = Field(
        default=TelemetryEnvironment.DEVELOPMENT, description="Deployment environment"
    )
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Additional resource attributes"
    )


class SamplingConfig(BaseModel):
    """Sampling configuration for traces."""

    sample_rate: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Base sampling rate (0.0-1.0)"
    )
    parent_based: bool = Field(
        default=True, description="Honor parent span sampling decision"
    )
    rules: list[dict[str, Any]] = Field(
        default_factory=list, description="Custom sampling rules"
    )


class InstrumentationConfig(BaseModel):
    """Configuration for automatic instrumentation."""

    instrument_http: bool = Field(default=True, description="Instrument HTTP requests")
    instrument_grpc: bool = Field(default=True, description="Instrument gRPC calls")
    instrument_redis: bool = Field(
        default=False, description="Instrument Redis operations"
    )
    instrument_sqlalchemy: bool = Field(
        default=False, description="Instrument database queries"
    )
    excluded_urls: list[str] = Field(
        default_factory=lambda: ["/health", "/metrics"],
        description="URLs to exclude from tracing",
    )


class TelemetryConfig(BaseModel):
    """Complete telemetry configuration."""

    enabled: bool = Field(default=True, description="Whether telemetry is enabled")

    # Resource configuration
    resource: ResourceConfig = Field(
        default_factory=ResourceConfig, description="Resource configuration"
    )

    # Tracing configuration
    export_traces: bool = Field(default=True, description="Whether to export traces")
    trace_exporter: ExporterConfig = Field(
        default_factory=ExporterConfig, description="Trace exporter configuration"
    )
    sampling: SamplingConfig = Field(
        default_factory=SamplingConfig, description="Trace sampling configuration"
    )

    # Metrics configuration
    export_metrics: bool = Field(default=True, description="Whether to export metrics")
    metric_exporter: ExporterConfig = Field(
        default_factory=ExporterConfig, description="Metric exporter configuration"
    )
    metric_interval_ms: int = Field(
        default=60000, description="Metric export interval in milliseconds"
    )

    # Instrumentation
    instrumentation: InstrumentationConfig = Field(
        default_factory=InstrumentationConfig,
        description="Automatic instrumentation settings",
    )

    # Logging integration
    log_correlation: bool = Field(default=True, description="Add trace IDs to logs")

    @classmethod
    def from_env(cls) -> "TelemetryConfig":
        """Create configuration from environment variables.

        Supports standard OpenTelemetry environment variables:
        - OTEL_SERVICE_NAME
        - OTEL_EXPORTER_OTLP_ENDPOINT
        - OTEL_TRACES_EXPORTER
        - OTEL_METRICS_EXPORTER
        - OTEL_TRACES_SAMPLER_ARG

        Returns:
            Configured TelemetryConfig instance
        """
        config = cls()

        # Service configuration
        if service_name := os.getenv("OTEL_SERVICE_NAME"):
            config.resource.service_name = service_name

        if service_version := os.getenv("OTEL_SERVICE_VERSION"):
            config.resource.service_version = service_version

        # Endpoint configuration
        if endpoint := os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
            config.trace_exporter.endpoint = endpoint
            config.metric_exporter.endpoint = endpoint

        # Trace-specific endpoint
        if trace_endpoint := os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"):
            config.trace_exporter.endpoint = trace_endpoint

        # Metric-specific endpoint
        if metric_endpoint := os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT"):
            config.metric_exporter.endpoint = metric_endpoint

        # Headers
        if headers := os.getenv("OTEL_EXPORTER_OTLP_HEADERS"):
            parsed_headers = {}
            for header in headers.split(","):
                if "=" in header:
                    key, value = header.split("=", 1)
                    parsed_headers[key.strip()] = value.strip()
            config.trace_exporter.headers = parsed_headers
            config.metric_exporter.headers = parsed_headers

        # Sampling
        if sample_rate := os.getenv("OTEL_TRACES_SAMPLER_ARG"):
            try:
                config.sampling.sample_rate = float(sample_rate)
            except ValueError:
                pass

        # Exporters
        if traces_exporter := os.getenv("OTEL_TRACES_EXPORTER"):
            if traces_exporter == "none":
                config.export_traces = False
            elif traces_exporter in ExportFormat.__members__.values():
                config.trace_exporter.format = ExportFormat(traces_exporter)

        if metrics_exporter := os.getenv("OTEL_METRICS_EXPORTER"):
            if metrics_exporter == "none":
                config.export_metrics = False
            elif metrics_exporter in ExportFormat.__members__.values():
                config.metric_exporter.format = ExportFormat(metrics_exporter)

        return config

    def to_env_dict(self) -> dict[str, str]:
        """Convert configuration to environment variables.

        Returns:
            Dictionary of environment variables
        """
        env_vars = {
            "OTEL_SERVICE_NAME": self.resource.service_name,
            "OTEL_SERVICE_VERSION": self.resource.service_version,
            "OTEL_TRACES_SAMPLER_ARG": str(self.sampling.sample_rate),
        }

        if self.trace_exporter.endpoint:
            env_vars["OTEL_EXPORTER_OTLP_ENDPOINT"] = self.trace_exporter.endpoint

        if self.trace_exporter.headers:
            headers_str = ",".join(
                f"{k}={v}" for k, v in self.trace_exporter.headers.items()
            )
            env_vars["OTEL_EXPORTER_OTLP_HEADERS"] = headers_str

        if not self.export_traces:
            env_vars["OTEL_TRACES_EXPORTER"] = "none"
        else:
            env_vars["OTEL_TRACES_EXPORTER"] = self.trace_exporter.format.value

        if not self.export_metrics:
            env_vars["OTEL_METRICS_EXPORTER"] = "none"
        else:
            env_vars["OTEL_METRICS_EXPORTER"] = self.metric_exporter.format.value

        return env_vars


# Preset configurations for common scenarios


def development_config() -> TelemetryConfig:
    """Get development environment configuration.

    - Console exporter for easy debugging
    - Full sampling
    - All instrumentation enabled
    """
    return TelemetryConfig(
        resource=ResourceConfig(environment=TelemetryEnvironment.DEVELOPMENT),
        trace_exporter=ExporterConfig(format=ExportFormat.CONSOLE),
        metric_exporter=ExporterConfig(format=ExportFormat.CONSOLE),
        sampling=SamplingConfig(sample_rate=1.0),
    )


def production_config(
    service_name: str, otlp_endpoint: str, sample_rate: float = 0.1
) -> TelemetryConfig:
    """Get production environment configuration.

    Args:
        service_name: Name of your service
        otlp_endpoint: OTLP collector endpoint
        sample_rate: Sampling rate (default 10%)

    Returns:
        Production-ready configuration
    """
    return TelemetryConfig(
        resource=ResourceConfig(
            service_name=service_name, environment=TelemetryEnvironment.PRODUCTION
        ),
        trace_exporter=ExporterConfig(
            format=ExportFormat.OTLP, endpoint=otlp_endpoint, insecure=False
        ),
        metric_exporter=ExporterConfig(
            format=ExportFormat.OTLP, endpoint=otlp_endpoint, insecure=False
        ),
        sampling=SamplingConfig(sample_rate=sample_rate),
    )


def test_config() -> TelemetryConfig:
    """Get test environment configuration.

    - Telemetry disabled by default
    - No external dependencies
    """
    return TelemetryConfig(
        enabled=False, resource=ResourceConfig(environment=TelemetryEnvironment.TEST)
    )
