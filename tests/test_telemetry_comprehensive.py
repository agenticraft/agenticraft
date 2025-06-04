"""Comprehensive tests for telemetry module to achieve >95% coverage."""

import os
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional
from unittest.mock import Mock, patch, MagicMock, call

import pytest

from agenticraft.core.telemetry import (
    Telemetry, TelemetryConfig,
    set_global_telemetry, get_global_telemetry, init_telemetry
)


class TestTelemetryConfig:
    """Test TelemetryConfig."""
    
    def test_telemetry_config_defaults(self):
        """Test default telemetry configuration."""
        config = TelemetryConfig()
        
        assert config.service_name == "agenticraft"
        assert config.service_version == "0.1.0"
        assert config.export_endpoint is None
        assert config.export_headers == {}
        assert config.enabled is True
        assert config.sample_rate == 1.0
    
    def test_telemetry_config_custom(self):
        """Test custom telemetry configuration."""
        config = TelemetryConfig(
            service_name="my-agent",
            service_version="2.0.0",
            export_endpoint="http://localhost:4317",
            export_headers={"auth": "token"},
            enabled=False,
            sample_rate=0.5
        )
        
        assert config.service_name == "my-agent"
        assert config.service_version == "2.0.0"
        assert config.export_endpoint == "http://localhost:4317"
        assert config.export_headers == {"auth": "token"}
        assert config.enabled is False
        assert config.sample_rate == 0.5
    
    def test_telemetry_config_endpoint_property(self):
        """Test endpoint property."""
        # With explicit endpoint
        config = TelemetryConfig(export_endpoint="http://custom:4317")
        assert config.endpoint == "http://custom:4317"
        
        # Without endpoint - should use default
        config2 = TelemetryConfig()
        assert config2.endpoint == "http://localhost:4317"
        
        # With environment variable
        with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://env:4317"}):
            config3 = TelemetryConfig()
            assert config3.endpoint == "http://env:4317"
    
    def test_telemetry_config_validation(self):
        """Test config validation."""
        # Valid sample rates
        TelemetryConfig(sample_rate=0.0)
        TelemetryConfig(sample_rate=0.5)
        TelemetryConfig(sample_rate=1.0)
        
        # Invalid sample rates
        with pytest.raises(ValueError):
            TelemetryConfig(sample_rate=-0.1)
        
        with pytest.raises(ValueError):
            TelemetryConfig(sample_rate=1.1)


class TestTelemetry:
    """Test Telemetry class."""
    
    @pytest.fixture
    def mock_tracer_provider(self):
        """Mock TracerProvider."""
        with patch("agenticraft.core.telemetry.TracerProvider") as mock:
            yield mock
    
    @pytest.fixture
    def mock_meter_provider(self):
        """Mock MeterProvider."""
        with patch("agenticraft.core.telemetry.MeterProvider") as mock:
            yield mock
    
    @pytest.fixture
    def mock_span_exporter(self):
        """Mock OTLP span exporter."""
        with patch("agenticraft.core.telemetry.OTLPSpanExporter") as mock:
            yield mock
    
    @pytest.fixture
    def mock_metric_exporter(self):
        """Mock OTLP metric exporter."""
        with patch("agenticraft.core.telemetry.OTLPMetricExporter") as mock:
            yield mock
    
    def test_telemetry_init_enabled(self, mock_tracer_provider, mock_meter_provider):
        """Test telemetry initialization when enabled."""
        telemetry = Telemetry(
            service_name="test-service",
            service_version="1.0.0",
            enabled=True
        )
        
        assert telemetry.config.service_name == "test-service"
        assert telemetry.config.service_version == "1.0.0"
        assert telemetry.config.enabled is True
        
        # Should set up providers
        mock_tracer_provider.assert_called_once()
        mock_meter_provider.assert_called_once()
    
    def test_telemetry_init_disabled(self, mock_tracer_provider, mock_meter_provider):
        """Test telemetry initialization when disabled."""
        telemetry = Telemetry(enabled=False)
        
        assert telemetry.config.enabled is False
        assert telemetry._tracer is None
        assert telemetry._meter is None
        
        # Should not set up providers
        mock_tracer_provider.assert_not_called()
        mock_meter_provider.assert_not_called()
    
    def test_telemetry_with_export_endpoint(
        self, mock_tracer_provider, mock_meter_provider,
        mock_span_exporter, mock_metric_exporter
    ):
        """Test telemetry with export endpoint."""
        with patch("agenticraft.core.telemetry.trace") as mock_trace:
            with patch("agenticraft.core.telemetry.metrics") as mock_metrics:
                telemetry = Telemetry(
                    service_name="test-service",
                    export_to="http://localhost:4317",
                    enabled=True
                )
                
                # Should create exporters
                mock_span_exporter.assert_called_once()
                mock_metric_exporter.assert_called_once()
                
                # Should set providers
                mock_trace.set_tracer_provider.assert_called_once()
                mock_metrics.set_meter_provider.assert_called_once()
    
    def test_telemetry_setup_metrics(self):
        """Test metric setup."""
        with patch("agenticraft.core.telemetry.trace"), \
             patch("agenticraft.core.telemetry.metrics") as mock_metrics:
            
            mock_meter = Mock()
            mock_metrics.get_meter.return_value = mock_meter
            
            telemetry = Telemetry(enabled=True)
            
            # Should create standard metrics
            assert mock_meter.create_counter.call_count >= 4  # agent_runs, agent_errors, tool_executions, tool_errors, tokens_used
            assert mock_meter.create_histogram.call_count >= 2  # agent_duration, tool_duration
            
            # Check metric names
            counter_calls = [call[0][0] for call in mock_meter.create_counter.call_args_list]
            assert "agenticraft.agent.runs" in counter_calls
            assert "agenticraft.agent.errors" in counter_calls
            assert "agenticraft.tool.executions" in counter_calls
            assert "agenticraft.tokens.used" in counter_calls
    
    def test_telemetry_span_enabled(self):
        """Test creating spans when enabled."""
        with patch("agenticraft.core.telemetry.trace") as mock_trace, \
             patch("agenticraft.core.telemetry.metrics"):
            
            mock_tracer = Mock()
            mock_span = Mock()
            mock_trace.get_tracer.return_value = mock_tracer
            
            # Configure context manager
            mock_context = MagicMock()
            mock_context.__enter__.return_value = mock_span
            mock_context.__exit__.return_value = None
            mock_tracer.start_as_current_span.return_value = mock_context
            
            telemetry = Telemetry(enabled=True)
            telemetry._tracer = mock_tracer
            
            with telemetry.span("test_operation", {"attr1": "value1"}) as span:
                assert span == mock_span
                mock_span.set_attribute.assert_called_with("attr1", "value1")
            
            mock_tracer.start_as_current_span.assert_called_once_with("test_operation")
    
    def test_telemetry_span_disabled(self):
        """Test creating spans when disabled."""
        telemetry = Telemetry(enabled=False)
        
        with telemetry.span("test_operation") as span:
            assert span is None
    
    def test_record_agent_run_enabled(self):
        """Test recording agent run metrics."""
        with patch("agenticraft.core.telemetry.trace"), \
             patch("agenticraft.core.telemetry.metrics"):
            
            telemetry = Telemetry(enabled=True)
            
            # Mock metrics
            telemetry.agent_runs = Mock()
            telemetry.agent_errors = Mock()
            telemetry.agent_duration = Mock()
            telemetry.tokens_used = Mock()
            
            # Record successful run
            telemetry.record_agent_run(
                agent_name="TestAgent",
                duration=1.5,
                success=True,
                tokens=100
            )
            
            attrs = {"agent.name": "TestAgent"}
            telemetry.agent_runs.add.assert_called_once_with(1, attrs)
            telemetry.agent_errors.add.assert_not_called()
            telemetry.agent_duration.record.assert_called_once_with(1.5, attrs)
            telemetry.tokens_used.add.assert_called_once_with(100, attrs)
    
    def test_record_agent_run_failure(self):
        """Test recording failed agent run."""
        with patch("agenticraft.core.telemetry.trace"), \
             patch("agenticraft.core.telemetry.metrics"):
            
            telemetry = Telemetry(enabled=True)
            
            # Mock metrics
            telemetry.agent_runs = Mock()
            telemetry.agent_errors = Mock()
            telemetry.agent_duration = Mock()
            
            # Record failed run
            telemetry.record_agent_run(
                agent_name="TestAgent",
                duration=0.5,
                success=False
            )
            
            attrs = {"agent.name": "TestAgent"}
            telemetry.agent_runs.add.assert_called_once_with(1, attrs)
            telemetry.agent_errors.add.assert_called_once_with(1, attrs)
            telemetry.agent_duration.record.assert_called_once_with(0.5, attrs)
    
    def test_record_agent_run_disabled(self):
        """Test recording when disabled."""
        telemetry = Telemetry(enabled=False)
        
        # Should not raise
        telemetry.record_agent_run("Agent", 1.0, True, 50)
    
    def test_record_tool_execution_enabled(self):
        """Test recording tool execution metrics."""
        with patch("agenticraft.core.telemetry.trace"), \
             patch("agenticraft.core.telemetry.metrics"):
            
            telemetry = Telemetry(enabled=True)
            
            # Mock metrics
            telemetry.tool_executions = Mock()
            telemetry.tool_errors = Mock()
            telemetry.tool_duration = Mock()
            
            # Record successful execution
            telemetry.record_tool_execution(
                tool_name="calculator",
                duration=0.1,
                success=True
            )
            
            attrs = {"tool.name": "calculator"}
            telemetry.tool_executions.add.assert_called_once_with(1, attrs)
            telemetry.tool_errors.add.assert_not_called()
            telemetry.tool_duration.record.assert_called_once_with(0.1, attrs)
    
    def test_record_tool_execution_failure(self):
        """Test recording failed tool execution."""
        with patch("agenticraft.core.telemetry.trace"), \
             patch("agenticraft.core.telemetry.metrics"):
            
            telemetry = Telemetry(enabled=True)
            
            # Mock metrics
            telemetry.tool_executions = Mock()
            telemetry.tool_errors = Mock()
            telemetry.tool_duration = Mock()
            
            # Record failed execution
            telemetry.record_tool_execution(
                tool_name="web_search",
                duration=2.0,
                success=False
            )
            
            attrs = {"tool.name": "web_search"}
            telemetry.tool_executions.add.assert_called_once_with(1, attrs)
            telemetry.tool_errors.add.assert_called_once_with(1, attrs)
            telemetry.tool_duration.record.assert_called_once_with(2.0, attrs)
    
    def test_record_tool_execution_disabled(self):
        """Test recording when disabled."""
        telemetry = Telemetry(enabled=False)
        
        # Should not raise
        telemetry.record_tool_execution("tool", 0.5, False)
    
    def test_tracer_property(self):
        """Test tracer property."""
        with patch("agenticraft.core.telemetry.trace"), \
             patch("agenticraft.core.telemetry.metrics"):
            
            telemetry = Telemetry(enabled=True)
            mock_tracer = Mock()
            telemetry._tracer = mock_tracer
            
            assert telemetry.tracer == mock_tracer
    
    def test_meter_property(self):
        """Test meter property."""
        with patch("agenticraft.core.telemetry.trace"), \
             patch("agenticraft.core.telemetry.metrics"):
            
            telemetry = Telemetry(enabled=True)
            mock_meter = Mock()
            telemetry._meter = mock_meter
            
            assert telemetry.meter == mock_meter


class TestGlobalFunctions:
    """Test global telemetry functions."""
    
    def test_set_and_get_global_telemetry(self):
        """Test setting and getting global telemetry."""
        # Clear global
        set_global_telemetry(None)
        assert get_global_telemetry() is None
        
        # Set telemetry
        telemetry = Mock(spec=Telemetry)
        set_global_telemetry(telemetry)
        
        assert get_global_telemetry() == telemetry
        
        # Clean up
        set_global_telemetry(None)
    
    def test_init_telemetry(self):
        """Test initializing global telemetry."""
        with patch("agenticraft.core.telemetry.trace"), \
             patch("agenticraft.core.telemetry.metrics"):
            
            telemetry = init_telemetry(
                service_name="test-app",
                export_to="http://localhost:4317",
                enabled=True
            )
            
            assert isinstance(telemetry, Telemetry)
            assert telemetry.config.service_name == "test-app"
            assert telemetry.config.export_endpoint == "http://localhost:4317"
            assert telemetry.config.enabled is True
            
            # Should be set as global
            assert get_global_telemetry() == telemetry
            
            # Clean up
            set_global_telemetry(None)
    
    def test_init_telemetry_disabled(self):
        """Test initializing disabled telemetry."""
        telemetry = init_telemetry(enabled=False)
        
        assert isinstance(telemetry, Telemetry)
        assert telemetry.config.enabled is False
        assert get_global_telemetry() == telemetry
        
        # Clean up
        set_global_telemetry(None)


class TestTelemetryIntegration:
    """Integration tests for telemetry."""
    
    def test_full_telemetry_flow(self):
        """Test complete telemetry flow."""
        with patch("agenticraft.core.telemetry.trace") as mock_trace, \
             patch("agenticraft.core.telemetry.metrics") as mock_metrics:
            
            # Mock setup
            mock_tracer = Mock()
            mock_meter = Mock()
            mock_trace.get_tracer.return_value = mock_tracer
            mock_metrics.get_meter.return_value = mock_meter
            
            # Mock span
            mock_span = Mock()
            mock_context = MagicMock()
            mock_context.__enter__.return_value = mock_span
            mock_context.__exit__.return_value = None
            mock_tracer.start_as_current_span.return_value = mock_context
            
            # Initialize telemetry
            telemetry = init_telemetry(
                service_name="integration-test",
                enabled=True
            )
            
            # Create span and record metrics
            with telemetry.span("operation", {"user.id": "123"}) as span:
                # Record agent run
                telemetry.record_agent_run(
                    agent_name="TestAgent",
                    duration=1.0,
                    success=True,
                    tokens=50
                )
                
                # Record tool execution
                telemetry.record_tool_execution(
                    tool_name="search",
                    duration=0.5,
                    success=True
                )
            
            # Verify interactions
            mock_tracer.start_as_current_span.assert_called_with("operation")
            mock_span.set_attribute.assert_called_with("user.id", "123")
            
            # Clean up
            set_global_telemetry(None)
    
    def test_telemetry_with_environment_config(self):
        """Test telemetry using environment variables."""
        with patch.dict(os.environ, {
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://env-endpoint:4317"
        }):
            with patch("agenticraft.core.telemetry.trace"), \
                 patch("agenticraft.core.telemetry.metrics"):
                
                telemetry = Telemetry()
                assert telemetry.config.endpoint == "http://env-endpoint:4317"
    
    def test_telemetry_resource_attributes(self):
        """Test resource attributes are set correctly."""
        with patch("agenticraft.core.telemetry.Resource") as mock_resource, \
             patch("agenticraft.core.telemetry.trace"), \
             patch("agenticraft.core.telemetry.metrics"):
            
            telemetry = Telemetry(
                service_name="test-service",
                service_version="2.0.0",
                enabled=True
            )
            
            # Check resource was created with correct attributes
            mock_resource.create.assert_called_with({
                "service.name": "test-service",
                "service.version": "2.0.0"
            })
