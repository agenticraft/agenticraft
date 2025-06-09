"""Tests for telemetry tracer."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from agenticraft.telemetry.tracer import (
    TracerConfig,
    create_span,
    extract_context,
    get_tracer,
    initialize_tracer,
    inject_context,
    record_exception,
    set_agent_attributes,
    set_span_attributes,
    shutdown_tracer,
    trace_method,
)


class TestTracerConfig:
    """Test tracer configuration and initialization."""

    def test_tracer_config_defaults(self):
        """Test tracer config defaults."""
        config = TracerConfig()

        assert config.service_name == "agenticraft"
        assert config.service_version == "0.2.0"
        assert config.enabled is True
        assert config.exporter_type == "console"
        assert config.batch_export is True
        assert config.sample_rate == 1.0

    def test_disabled_tracing(self):
        """Test that tracing doesn't set up when disabled."""
        config = TracerConfig(enabled=False)
        tracer = initialize_tracer(config)

        # Should return no-op tracer
        assert tracer is not None

    @patch("agenticraft.telemetry.tracer.trace.set_tracer_provider")
    def test_console_exporter_setup(self, mock_set_provider):
        """Test setup with console exporter."""
        config = TracerConfig(exporter_type="console")
        tracer = initialize_tracer(config)

        assert tracer is not None
        mock_set_provider.assert_called_once()

    def test_get_tracer(self):
        """Test getting a tracer instance."""
        tracer = get_tracer()
        assert tracer is not None

    def test_invalid_exporter_type(self):
        """Test invalid exporter type raises error."""
        config = TracerConfig(exporter_type="invalid")

        with pytest.raises(ValueError, match="Unknown exporter type"):
            initialize_tracer(config)

    @patch("agenticraft.telemetry.tracer._tracer_provider")
    def test_shutdown(self, mock_provider):
        """Test tracer shutdown."""
        # Mock should be not None
        mock_provider.shutdown = Mock()

        shutdown_tracer()

        mock_provider.shutdown.assert_called_once()


class TestTracerConfig:
    """Test tracer configuration and initialization."""

    def test_tracer_config_defaults(self):
        """Test tracer config defaults."""
        config = TracerConfig()

        assert config.service_name == "agenticraft"
        assert config.service_version == "0.2.0"
        assert config.enabled is True
        assert config.exporter_type == "console"
        assert config.batch_export is True
        assert config.sample_rate == 1.0

    def test_disabled_tracing(self):
        """Test that tracing doesn't set up when disabled."""
        config = TracerConfig(enabled=False)
        tracer = initialize_tracer(config)

        # Should return no-op tracer
        assert tracer is not None

    @patch("agenticraft.telemetry.tracer.trace.set_tracer_provider")
    def test_console_exporter_setup(self, mock_set_provider):
        """Test setup with console exporter."""
        config = TracerConfig(exporter_type="console")
        tracer = initialize_tracer(config)

        assert tracer is not None
        mock_set_provider.assert_called_once()

    def test_get_tracer(self):
        """Test getting a tracer instance."""
        tracer = get_tracer()
        assert tracer is not None

    def test_invalid_exporter_type(self):
        """Test invalid exporter type raises error."""
        config = TracerConfig(exporter_type="invalid")

        with pytest.raises(ValueError, match="Unknown exporter type"):
            initialize_tracer(config)

    @patch("agenticraft.telemetry.tracer._tracer_provider")
    def test_shutdown(self, mock_provider):
        """Test tracer shutdown."""
        # Mock should be not None
        mock_provider.shutdown = Mock()

        shutdown_tracer()

        mock_provider.shutdown.assert_called_once()


class TestTracerFunctions:
    """Test tracer utility functions."""

    def test_initialize_tracer_with_config(self):
        """Test initializing tracer with config."""
        config = TracerConfig(enabled=False)

        tracer = initialize_tracer(config)

        assert tracer is not None

    def test_initialize_tracer_with_custom_params(self):
        """Test initializing tracer with custom parameters."""
        config = TracerConfig(
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
            exporter_type="console",
        )

        tracer = initialize_tracer(config)

        assert tracer is not None

    def test_get_tracer_function(self):
        """Test getting tracer via function."""
        tracer = get_tracer()
        assert tracer is not None

    def test_create_span_success(self):
        """Test create span context manager - success case."""
        mock_tracer = Mock()
        mock_span = MagicMock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = Mock(return_value=mock_span)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_tracer.start_as_current_span.return_value = mock_context_manager

        with patch("agenticraft.telemetry.tracer.get_tracer", return_value=mock_tracer):
            with create_span("test_op", attributes={"key": "value"}) as span:
                assert span == mock_span

        mock_tracer.start_as_current_span.assert_called_once()

    def test_record_exception_function(self):
        """Test record exception function."""
        mock_span = Mock()
        mock_span.is_recording.return_value = True

        with patch("opentelemetry.trace.get_current_span", return_value=mock_span):
            exc = ValueError("Test error")
            record_exception(exc, escaped=True)

        mock_span.record_exception.assert_called_once_with(exc, attributes=None)
        mock_span.set_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_trace_method_async(self):
        """Test trace method decorator with async function."""
        mock_tracer = Mock()
        mock_span = MagicMock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = Mock(return_value=mock_span)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_tracer.start_as_current_span.return_value = mock_context_manager

        with patch("agenticraft.telemetry.tracer.get_tracer", return_value=mock_tracer):

            @trace_method(name="custom_span")
            async def async_func(x, y):
                return x + y

            result = await async_func(1, 2)

        assert result == 3

    def test_trace_method_sync(self):
        """Test trace method decorator with sync function."""
        mock_tracer = Mock()
        mock_span = MagicMock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = Mock(return_value=mock_span)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_tracer.start_as_current_span.return_value = mock_context_manager

        with patch("agenticraft.telemetry.tracer.get_tracer", return_value=mock_tracer):

            @trace_method()
            def sync_func(x, y):
                return x * y

            result = sync_func(3, 4)

        assert result == 12

    def test_set_span_attributes(self):
        """Test setting attributes on current span."""
        mock_span = Mock()
        mock_span.is_recording.return_value = True

        with patch("opentelemetry.trace.get_current_span", return_value=mock_span):
            set_span_attributes({"key1": "value1", "key2": 42})

        mock_span.set_attribute.assert_any_call("key1", "value1")
        mock_span.set_attribute.assert_any_call("key2", 42)

    def test_set_agent_attributes(self):
        """Test setting agent-specific attributes."""
        mock_span = Mock()
        mock_span.is_recording.return_value = True

        with patch("opentelemetry.trace.get_current_span", return_value=mock_span):
            set_agent_attributes(
                agent_name="test_agent",
                agent_type="test_type",
                model="gpt-4",
                provider="openai",
            )

        mock_span.set_attribute.assert_any_call("agent.name", "test_agent")
        mock_span.set_attribute.assert_any_call("agent.type", "test_type")
        mock_span.set_attribute.assert_any_call("llm.model", "gpt-4")
        mock_span.set_attribute.assert_any_call("llm.provider", "openai")

    def test_inject_and_extract_context(self):
        """Test context injection and extraction."""
        carrier = {}

        # Initialize tracer first
        from agenticraft.telemetry.tracer import initialize_tracer

        initialize_tracer()

        # Test injection - patch where it's imported in the module
        with patch("agenticraft.telemetry.tracer.inject") as mock_inject:
            inject_context(carrier)
            mock_inject.assert_called_once_with(carrier)

        # Test extraction - patch where it's imported in the module
        with patch("agenticraft.telemetry.tracer.extract") as mock_extract:
            mock_extract.return_value = {"trace_id": "12345"}
            context = extract_context(carrier)
            mock_extract.assert_called_once_with(carrier)
            assert context == {"trace_id": "12345"}
