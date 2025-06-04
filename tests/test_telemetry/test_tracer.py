"""Tests for telemetry tracer."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from agenticraft.telemetry.tracer import (
    TracerManager,
    setup_tracing,
    get_tracer,
    shutdown_tracing,
    traced_operation,
    trace_function,
    add_event,
    set_attribute,
    get_current_trace_id
)
from agenticraft.telemetry.config import TelemetryConfig, ExportFormat


class TestTracerManager:
    """Test tracer manager functionality."""
    
    def test_tracer_manager_init(self):
        """Test tracer manager initialization."""
        config = TelemetryConfig(enabled=False)
        manager = TracerManager(config)
        
        assert manager.config == config
        assert manager._tracer_provider is None
        assert manager._instrumentors == []
    
    def test_disabled_tracing(self):
        """Test that tracing doesn't set up when disabled."""
        config = TelemetryConfig(enabled=False)
        manager = TracerManager(config)
        
        manager.setup()
        
        assert manager._tracer_provider is None
    
    @patch('agenticraft.telemetry.tracer.trace.set_tracer_provider')
    def test_console_exporter_setup(self, mock_set_provider):
        """Test setup with console exporter."""
        config = TelemetryConfig(
            trace_exporter=ExporterConfig(format=ExportFormat.CONSOLE)
        )
        manager = TracerManager(config)
        
        manager.setup()
        
        assert manager._tracer_provider is not None
        mock_set_provider.assert_called_once()
    
    def test_get_tracer(self):
        """Test getting a tracer instance."""
        config = TelemetryConfig(enabled=False)
        manager = TracerManager(config)
        
        tracer = manager.get_tracer("test.module", "1.0.0")
        
        assert tracer is not None
    
    @patch('agenticraft.telemetry.tracer.HTTPXClientInstrumentor')
    @patch('agenticraft.telemetry.tracer.GrpcInstrumentorClient')
    @patch('agenticraft.telemetry.tracer.GrpcInstrumentorServer')
    def test_instrumentation_setup(self, mock_grpc_server, mock_grpc_client, mock_httpx):
        """Test automatic instrumentation setup."""
        config = TelemetryConfig()
        config.instrumentation.instrument_http = True
        config.instrumentation.instrument_grpc = True
        
        manager = TracerManager(config)
        
        # Mock instrumentors
        httpx_inst = Mock()
        grpc_client_inst = Mock()
        grpc_server_inst = Mock()
        
        mock_httpx.return_value = httpx_inst
        mock_grpc_client.return_value = grpc_client_inst
        mock_grpc_server.return_value = grpc_server_inst
        
        manager.setup()
        
        # Verify instrumentors were created and configured
        mock_httpx.assert_called_once()
        mock_grpc_client.assert_called_once()
        mock_grpc_server.assert_called_once()
        
        httpx_inst.instrument.assert_called_once()
        grpc_client_inst.instrument.assert_called_once()
        grpc_server_inst.instrument.assert_called_once()
    
    def test_shutdown(self):
        """Test tracer shutdown."""
        config = TelemetryConfig(enabled=False)
        manager = TracerManager(config)
        
        # Add mock instrumentor
        mock_instrumentor = Mock()
        manager._instrumentors.append(mock_instrumentor)
        
        # Mock tracer provider
        manager._tracer_provider = Mock()
        
        manager.shutdown()
        
        mock_instrumentor.uninstrument.assert_called_once()
        manager._tracer_provider.shutdown.assert_called_once()


class TestTracerFunctions:
    """Test tracer utility functions."""
    
    def test_setup_tracing_with_config(self):
        """Test setting up tracing with config."""
        config = TelemetryConfig(enabled=False)
        
        manager = setup_tracing(config=config)
        
        assert manager is not None
        assert manager.config == config
    
    def test_setup_tracing_with_params(self):
        """Test setting up tracing with parameters."""
        manager = setup_tracing(
            service_name="test-service",
            endpoint="http://localhost:4317"
        )
        
        assert manager is not None
        assert manager.config.resource.service_name == "test-service"
        assert manager.config.trace_exporter.endpoint == "http://localhost:4317"
    
    def test_get_tracer_function(self):
        """Test getting tracer via function."""
        tracer = get_tracer("test.module", "1.0.0")
        assert tracer is not None
    
    def test_traced_operation_success(self):
        """Test traced operation context manager - success case."""
        mock_tracer = Mock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        with patch('agenticraft.telemetry.tracer.get_tracer', return_value=mock_tracer):
            with traced_operation("test_op", {"key": "value"}):
                pass
        
        mock_tracer.start_as_current_span.assert_called_once_with("test_op")
        mock_span.set_attribute.assert_called_once_with("key", "value")
    
    def test_traced_operation_exception(self):
        """Test traced operation context manager - exception case."""
        mock_tracer = Mock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        with patch('agenticraft.telemetry.tracer.get_tracer', return_value=mock_tracer):
            with pytest.raises(ValueError):
                with traced_operation("test_op", record_exception=True):
                    raise ValueError("Test error")
        
        mock_span.record_exception.assert_called_once()
        mock_span.set_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_trace_function_async(self):
        """Test trace function decorator with async function."""
        mock_tracer = Mock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        @trace_function(name="custom_span")
        async def async_func(x, y):
            return x + y
        
        with patch('agenticraft.telemetry.tracer.get_tracer', return_value=mock_tracer):
            result = await async_func(1, 2)
        
        assert result == 3
        mock_tracer.start_as_current_span.assert_called_once_with(
            "custom_span",
            kind=trace.SpanKind.INTERNAL,
            attributes=None
        )
    
    def test_trace_function_sync(self):
        """Test trace function decorator with sync function."""
        mock_tracer = Mock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        @trace_function()
        def sync_func(x, y):
            return x * y
        
        with patch('agenticraft.telemetry.tracer.get_tracer', return_value=mock_tracer):
            result = sync_func(3, 4)
        
        assert result == 12
    
    def test_add_event(self):
        """Test adding event to current span."""
        mock_span = Mock()
        mock_span.is_recording.return_value = True
        
        with patch('opentelemetry.trace.get_current_span', return_value=mock_span):
            add_event("test_event", {"attr": "value"})
        
        mock_span.add_event.assert_called_once_with("test_event", {"attr": "value"})
    
    def test_set_attribute(self):
        """Test setting attribute on current span."""
        mock_span = Mock()
        mock_span.is_recording.return_value = True
        
        with patch('opentelemetry.trace.get_current_span', return_value=mock_span):
            set_attribute("key", "value")
        
        mock_span.set_attribute.assert_called_once_with("key", "value")
    
    def test_get_current_trace_id(self):
        """Test getting current trace ID."""
        mock_span = Mock()
        mock_span.is_recording.return_value = True
        
        mock_context = Mock()
        mock_context.trace_id = 12345
        mock_span.get_span_context.return_value = mock_context
        
        with patch('opentelemetry.trace.get_current_span', return_value=mock_span):
            trace_id = get_current_trace_id()
        
        assert trace_id == format(12345, "032x")
    
    def test_get_current_trace_id_no_span(self):
        """Test getting trace ID when no span is active."""
        mock_span = Mock()
        mock_span.is_recording.return_value = False
        
        with patch('opentelemetry.trace.get_current_span', return_value=mock_span):
            trace_id = get_current_trace_id()
        
        assert trace_id is None
