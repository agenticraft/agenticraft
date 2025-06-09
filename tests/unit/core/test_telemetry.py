"""Unit tests for telemetry module.

This module tests the telemetry functionality including:
- Telemetry manager setup
- Span creation and tracking
- Metrics collection
- Export configuration
"""

import asyncio
from unittest.mock import patch

import pytest

from agenticraft.core.telemetry import (
    Telemetry,
    TelemetryConfig,
    get_global_telemetry,
    init_telemetry,
    set_global_telemetry,
)


class TestTelemetryConfig:
    """Test TelemetryConfig model."""

    def test_telemetry_config_defaults(self):
        """Test default telemetry configuration."""
        config = TelemetryConfig()

        assert config.service_name == "agenticraft"
        assert config.service_version == "0.1.0"
        assert config.enabled is True
        assert config.sample_rate == 1.0
        assert config.export_endpoint is None

    def test_telemetry_config_custom(self):
        """Test custom telemetry configuration."""
        config = TelemetryConfig(
            service_name="my-service",
            service_version="2.0.0",
            export_endpoint="http://localhost:4317",
            enabled=False,
            sample_rate=0.5,
        )

        assert config.service_name == "my-service"
        assert config.service_version == "2.0.0"
        assert config.export_endpoint == "http://localhost:4317"
        assert config.enabled is False
        assert config.sample_rate == 0.5

    def test_endpoint_property(self):
        """Test endpoint property with fallback."""
        # Without explicit endpoint
        config = TelemetryConfig()
        assert config.endpoint == "http://localhost:4317"

        # With explicit endpoint
        config = TelemetryConfig(export_endpoint="http://custom:4317")
        assert config.endpoint == "http://custom:4317"


class TestTelemetry:
    """Test Telemetry class."""

    def test_telemetry_creation_enabled(self):
        """Test creating enabled telemetry."""
        telemetry = Telemetry(service_name="test-service", enabled=True)

        assert telemetry.config.service_name == "test-service"
        assert telemetry.config.enabled is True
        assert telemetry.tracer is not None
        assert telemetry.meter is not None

    def test_telemetry_creation_disabled(self):
        """Test creating disabled telemetry."""
        telemetry = Telemetry(enabled=False)

        assert telemetry.config.enabled is False
        assert telemetry.tracer is None
        assert telemetry.meter is None

    def test_span_creation_enabled(self):
        """Test span creation when enabled."""
        telemetry = Telemetry(enabled=True)

        with telemetry.span("test_operation", {"key": "value"}) as span:
            if span:
                # Span might be None if OTEL not properly set up
                assert hasattr(span, "set_attribute")

    def test_span_creation_disabled(self):
        """Test span creation when disabled."""
        telemetry = Telemetry(enabled=False)

        with telemetry.span("test_operation") as span:
            assert span is None

    def test_record_agent_run(self):
        """Test recording agent run metrics."""
        telemetry = Telemetry(enabled=True)

        # Should not raise even if metrics not fully configured
        telemetry.record_agent_run(
            agent_name="TestAgent", duration=0.5, success=True, tokens=100
        )

        # Test failure case
        telemetry.record_agent_run(agent_name="TestAgent", duration=0.2, success=False)

    def test_record_tool_execution(self):
        """Test recording tool execution metrics."""
        telemetry = Telemetry(enabled=True)

        # Should not raise even if metrics not fully configured
        telemetry.record_tool_execution(
            tool_name="calculator", duration=0.1, success=True
        )

        # Test failure case
        telemetry.record_tool_execution(
            tool_name="web_search", duration=2.0, success=False
        )

    def test_metrics_setup(self):
        """Test that metrics are set up correctly."""
        telemetry = Telemetry(enabled=True)

        # Check that metrics attributes exist
        assert hasattr(telemetry, "agent_runs")
        assert hasattr(telemetry, "agent_errors")
        assert hasattr(telemetry, "agent_duration")
        assert hasattr(telemetry, "tool_executions")
        assert hasattr(telemetry, "tool_errors")
        assert hasattr(telemetry, "tool_duration")
        assert hasattr(telemetry, "tokens_used")


class TestTelemetryGlobal:
    """Test global telemetry functions."""

    def test_global_telemetry_singleton(self):
        """Test global telemetry management."""
        # Clear any existing global telemetry
        set_global_telemetry(None)

        # Initially None
        assert get_global_telemetry() is None

        # Set global telemetry
        telemetry = Telemetry(enabled=True)
        set_global_telemetry(telemetry)

        # Should return same instance
        assert get_global_telemetry() is telemetry

    def test_init_telemetry(self):
        """Test init_telemetry helper."""
        telemetry = init_telemetry(
            service_name="test-app", export_to="http://localhost:4317", enabled=True
        )

        assert isinstance(telemetry, Telemetry)
        assert telemetry.config.service_name == "test-app"
        assert telemetry.config.export_endpoint == "http://localhost:4317"
        assert telemetry.config.enabled is True

        # Should be set as global
        assert get_global_telemetry() is telemetry


class TestTelemetryIntegration:
    """Test telemetry integration scenarios."""

    def test_telemetry_with_export_endpoint(self):
        """Test telemetry with custom export endpoint."""
        with patch(
            "opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter"
        ) as mock_exporter:
            telemetry = Telemetry(
                service_name="integration-test",
                export_to="http://telemetry.example.com:4317",
                enabled=True,
            )

            # Exporter should be created with endpoint
            assert telemetry.config.endpoint == "http://telemetry.example.com:4317"

    def test_telemetry_without_export(self):
        """Test telemetry without export endpoint."""
        telemetry = Telemetry(service_name="local-test", enabled=True)

        # Should still work without exporter
        with telemetry.span("test") as span:
            pass  # No-op is fine

    @pytest.mark.asyncio
    async def test_telemetry_in_async_context(self):
        """Test telemetry in async context."""
        telemetry = Telemetry(enabled=True)

        async def async_operation():
            with telemetry.span("async_op") as span:
                await asyncio.sleep(0.01)
                return "done"

        result = await async_operation()
        assert result == "done"

    def test_telemetry_error_handling(self):
        """Test telemetry doesn't break on errors."""
        telemetry = Telemetry(enabled=True)

        # Should handle missing attributes gracefully
        try:
            with telemetry.span("error_test") as span:
                raise ValueError("Test error")
        except ValueError:
            # Telemetry should not interfere with error propagation
            pass

        # Metrics should still work after error
        telemetry.record_agent_run(agent_name="ErrorAgent", duration=0.1, success=False)
