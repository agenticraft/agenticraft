"""Tests for telemetry configuration."""

import os
import pytest
from unittest.mock import patch

from agenticraft.telemetry.config import (
    TelemetryConfig,
    ExportFormat,
    TelemetryEnvironment,
    ExporterConfig,
    ResourceConfig,
    SamplingConfig,
    development_config,
    production_config,
    test_config
)


class TestTelemetryConfig:
    """Test telemetry configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = TelemetryConfig()
        
        assert config.enabled is True
        assert config.export_traces is True
        assert config.export_metrics is True
        assert config.resource.service_name == "agenticraft"
        assert config.resource.environment == TelemetryEnvironment.DEVELOPMENT
        assert config.sampling.sample_rate == 1.0
    
    def test_exporter_config_defaults(self):
        """Test exporter configuration defaults."""
        config = ExporterConfig()
        
        assert config.format == ExportFormat.OTLP
        assert config.endpoint == "http://localhost:4317"
        assert config.timeout_ms == 30000
        assert config.insecure is True
    
    def test_exporter_endpoint_defaults(self):
        """Test that exporter endpoints get sensible defaults."""
        # OTLP
        otlp = ExporterConfig(format=ExportFormat.OTLP)
        assert otlp.endpoint == "http://localhost:4317"
        
        # Jaeger
        jaeger = ExporterConfig(format=ExportFormat.JAEGER)
        assert jaeger.endpoint == "http://localhost:14250"
        
        # Zipkin
        zipkin = ExporterConfig(format=ExportFormat.ZIPKIN)
        assert zipkin.endpoint == "http://localhost:9411/api/v2/spans"
        
        # Console doesn't need endpoint
        console = ExporterConfig(format=ExportFormat.CONSOLE)
        assert console.endpoint is None
    
    def test_from_env(self):
        """Test configuration from environment variables."""
        env_vars = {
            "OTEL_SERVICE_NAME": "test-service",
            "OTEL_SERVICE_VERSION": "1.2.3",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://collector:4317",
            "OTEL_EXPORTER_OTLP_HEADERS": "api-key=secret,tenant=test",
            "OTEL_TRACES_SAMPLER_ARG": "0.5",
            "OTEL_TRACES_EXPORTER": "otlp",
            "OTEL_METRICS_EXPORTER": "console"
        }
        
        with patch.dict(os.environ, env_vars):
            config = TelemetryConfig.from_env()
        
        assert config.resource.service_name == "test-service"
        assert config.resource.service_version == "1.2.3"
        assert config.trace_exporter.endpoint == "http://collector:4317"
        assert config.trace_exporter.headers == {"api-key": "secret", "tenant": "test"}
        assert config.sampling.sample_rate == 0.5
        assert config.trace_exporter.format == ExportFormat.OTLP
        assert config.metric_exporter.format == ExportFormat.CONSOLE
    
    def test_to_env_dict(self):
        """Test converting config to environment variables."""
        config = TelemetryConfig(
            resource=ResourceConfig(
                service_name="my-service",
                service_version="2.0.0"
            ),
            trace_exporter=ExporterConfig(
                endpoint="http://jaeger:4317",
                headers={"auth": "token123"}
            ),
            sampling=SamplingConfig(sample_rate=0.1)
        )
        
        env_dict = config.to_env_dict()
        
        assert env_dict["OTEL_SERVICE_NAME"] == "my-service"
        assert env_dict["OTEL_SERVICE_VERSION"] == "2.0.0"
        assert env_dict["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://jaeger:4317"
        assert env_dict["OTEL_EXPORTER_OTLP_HEADERS"] == "auth=token123"
        assert env_dict["OTEL_TRACES_SAMPLER_ARG"] == "0.1"
    
    def test_development_config(self):
        """Test development configuration preset."""
        config = development_config()
        
        assert config.resource.environment == TelemetryEnvironment.DEVELOPMENT
        assert config.trace_exporter.format == ExportFormat.CONSOLE
        assert config.metric_exporter.format == ExportFormat.CONSOLE
        assert config.sampling.sample_rate == 1.0
    
    def test_production_config(self):
        """Test production configuration preset."""
        config = production_config(
            service_name="prod-service",
            otlp_endpoint="http://prod-collector:4317",
            sample_rate=0.05
        )
        
        assert config.resource.service_name == "prod-service"
        assert config.resource.environment == TelemetryEnvironment.PRODUCTION
        assert config.trace_exporter.endpoint == "http://prod-collector:4317"
        assert config.trace_exporter.insecure is False
        assert config.sampling.sample_rate == 0.05
    
    def test_test_config(self):
        """Test test environment configuration."""
        config = test_config()
        
        assert config.enabled is False
        assert config.resource.environment == TelemetryEnvironment.TEST
    
    def test_resource_attributes(self):
        """Test resource configuration with custom attributes."""
        config = ResourceConfig(
            service_name="my-app",
            service_version="1.0.0",
            service_instance_id="instance-123",
            attributes={
                "deployment.region": "us-west-2",
                "custom.team": "platform"
            }
        )
        
        assert config.service_name == "my-app"
        assert config.attributes["deployment.region"] == "us-west-2"
        assert config.attributes["custom.team"] == "platform"
    
    def test_instrumentation_config(self):
        """Test instrumentation configuration."""
        config = TelemetryConfig()
        
        assert config.instrumentation.instrument_http is True
        assert config.instrumentation.instrument_grpc is True
        assert config.instrumentation.instrument_redis is False
        assert "/health" in config.instrumentation.excluded_urls
        assert "/metrics" in config.instrumentation.excluded_urls
