"""Tests for telemetry module."""

import asyncio
from unittest.mock import Mock, patch

import pytest

# Handle imports for not-yet-implemented modules
try:
    from agenticraft.telemetry.metrics import (
        LatencyTimer,
        MetricsConfig,
        get_meter,
        get_metrics_collector,
        initialize_metrics,
        record_error,
        record_latency,
        record_token_usage,
    )
    from agenticraft.telemetry.tracer import (
        TracerConfig,
        create_span,
        get_tracer,
        initialize_tracer,
        record_exception,
        set_span_attributes,
        trace_method,
    )

    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    # Create dummy classes to prevent syntax errors
    TracerConfig = None
    MetricsConfig = None
    LatencyTimer = None

# Skip all tests if module not implemented
pytestmark = pytest.mark.skipif(
    not TELEMETRY_AVAILABLE, reason="Telemetry module not yet implemented"
)


class TestTracer:
    """Test tracer functionality."""

    def test_initialize_tracer(self):
        """Test tracer initialization."""
        config = TracerConfig(
            service_name="test_service", enabled=True, exporter_type="console"
        )

        tracer = initialize_tracer(config)
        assert tracer is not None

        # Get tracer should return same instance
        assert get_tracer() == tracer

    def test_disabled_tracer(self):
        """Test disabled tracer."""
        config = TracerConfig(enabled=False)
        tracer = initialize_tracer(config)

        # Should return no-op tracer
        assert tracer is not None
        with create_span("test") as span:
            assert not span.is_recording()

    def test_create_span(self):
        """Test span creation."""
        initialize_tracer(TracerConfig(enabled=True, exporter_type="console"))

        with create_span("test.operation") as span:
            assert span is not None
            assert span.is_recording()

            # Set attributes
            set_span_attributes({"test.attribute": "value", "test.number": 42})

    def test_record_exception(self):
        """Test exception recording."""
        initialize_tracer(TracerConfig(enabled=True))

        with create_span("test.error") as span:
            try:
                raise ValueError("Test error")
            except ValueError as e:
                record_exception(e, escaped=True)

    @pytest.mark.asyncio
    async def test_trace_method_decorator(self):
        """Test trace method decorator."""
        initialize_tracer(TracerConfig(enabled=True))

        @trace_method("test.method")
        async def test_async_method(value: int) -> int:
            return value * 2

        result = await test_async_method(21)
        assert result == 42

        @trace_method("test.sync_method")
        def test_sync_method(value: int) -> int:
            return value + 1

        result = test_sync_method(41)
        assert result == 42


class TestMetrics:
    """Test metrics functionality."""

    def test_initialize_metrics(self):
        """Test metrics initialization."""
        config = MetricsConfig(
            service_name="test_service", enabled=True, exporter_type="console"
        )

        meter = initialize_metrics(config)
        assert meter is not None

        # Get meter should return same instance
        assert get_meter() == meter

        # Collector should be initialized
        collector = get_metrics_collector()
        assert collector is not None

    def test_disabled_metrics(self):
        """Test disabled metrics."""
        config = MetricsConfig(enabled=False)
        meter = initialize_metrics(config)

        # Should return no-op meter
        assert meter is not None

    def test_record_token_usage(self):
        """Test token usage recording."""
        initialize_metrics(MetricsConfig(enabled=True))

        # Record some token usage
        record_token_usage(
            provider="openai",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )

        # Verify in collector
        collector = get_metrics_collector()
        assert "openai:gpt-4" in collector._token_usage
        assert collector._token_usage["openai:gpt-4"]["prompt"] == 100
        assert collector._token_usage["openai:gpt-4"]["completion"] == 50
        assert collector._token_usage["openai:gpt-4"]["total"] == 150

    def test_record_latency(self):
        """Test latency recording."""
        initialize_metrics(MetricsConfig(enabled=True))

        # Record latencies
        record_latency("test.operation", 100.5)
        record_latency("test.operation", 150.2)
        record_latency("test.operation", 125.7)

        # Verify in collector
        collector = get_metrics_collector()
        assert "test.operation" in collector._latencies
        assert len(collector._latencies["test.operation"]) == 3
        assert 100.5 in collector._latencies["test.operation"]

    def test_record_error(self):
        """Test error recording."""
        initialize_metrics(MetricsConfig(enabled=True))

        # Record errors
        record_error("ValueError", "test.operation")
        record_error("ValueError", "test.operation")
        record_error("TypeError", "test.operation")

        # Verify in collector
        collector = get_metrics_collector()
        assert collector._errors["test.operation:ValueError"] == 2
        assert collector._errors["test.operation:TypeError"] == 1

    @pytest.mark.asyncio
    async def test_latency_timer(self):
        """Test latency timer context manager."""
        initialize_metrics(MetricsConfig(enabled=True))

        # Use timer
        with LatencyTimer("test.timed_operation", category="test"):
            await asyncio.sleep(0.1)

        # Verify latency was recorded
        collector = get_metrics_collector()
        assert "test.timed_operation" in collector._latencies
        assert len(collector._latencies["test.timed_operation"]) == 1
        assert collector._latencies["test.timed_operation"][0] >= 100  # At least 100ms

    def test_latency_timer_with_exception(self):
        """Test latency timer records errors on exception."""
        initialize_metrics(MetricsConfig(enabled=True))

        # Use timer with exception
        with pytest.raises(ValueError):
            with LatencyTimer("test.error_operation"):
                raise ValueError("Test error")

        # Verify error was recorded
        collector = get_metrics_collector()
        assert "test.error_operation:ValueError" in collector._errors
        assert collector._errors["test.error_operation:ValueError"] == 1


class TestExporters:
    """Test different exporters."""

    def test_console_exporter(self):
        """Test console exporter configuration."""
        try:
            from agenticraft.telemetry.exporters.console import ConsoleExporter

            exporter = ConsoleExporter(pretty_print=True)
            assert exporter.pretty_print is True
            assert exporter.include_timestamps is True
        except ImportError:
            pytest.skip("Console exporter not implemented")

    def test_otlp_exporter(self):
        """Test OTLP exporter configuration."""
        try:
            from agenticraft.telemetry.exporters.otlp import OTLPExporter

            # Default configuration
            exporter = OTLPExporter()
            assert exporter.endpoint == "localhost:4317"
            assert exporter.insecure is True

            # HTTP configuration
            http_exporter = OTLPExporter(use_http=True)
            assert http_exporter.endpoint == "localhost:4318"

            # Cloud provider configurations
            jaeger_exporter = OTLPExporter.for_jaeger()
            assert jaeger_exporter.endpoint == "localhost:4317"

            collector_exporter = OTLPExporter.for_collector(
                endpoint="collector.example.com:4317", api_key="test-key"
            )
            assert collector_exporter.headers["api-key"] == "test-key"
        except ImportError:
            pytest.skip("OTLP exporter not implemented")

    def test_prometheus_exporter(self):
        """Test Prometheus exporter configuration."""
        try:
            from agenticraft.telemetry.exporters.prometheus import PrometheusExporter

            exporter = PrometheusExporter(port=9090)
            assert exporter.port == 9090
            assert exporter.addr == "0.0.0.0"

            # Test metrics URL
            url = exporter.get_metrics_url()
            assert url == "http://localhost:9090/metrics"
        except ImportError:
            pytest.skip("Prometheus exporter not implemented")


class TestIntegration:
    """Test telemetry integration features."""

    @pytest.mark.asyncio
    async def test_instrument_agent(self):
        """Test agent instrumentation."""
        from agenticraft.core.agent import Agent
        from agenticraft.telemetry.integration import instrument_agent

        # Initialize telemetry
        initialize_tracer(TracerConfig(enabled=True))
        initialize_metrics(MetricsConfig(enabled=True))

        # Create mock agent class
        class MockAgent(Agent):
            def __init__(self):
                super().__init__(name="TestAgent", instructions="Test")
                self.provider = Mock(name="mock_provider")
                self.model = "test-model"

            async def arun(self, prompt: str):
                response = Mock()
                response.content = "Test response"
                response.usage = {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                }
                return response

        # Instrument the agent
        instrumented_class = instrument_agent(MockAgent)
        agent = instrumented_class()

        # Run and verify telemetry is recorded
        response = await agent.arun("Test prompt")
        assert response.content == "Test response"

        # Check metrics were recorded
        collector = get_metrics_collector()
        assert len(collector._latencies.get("agent.TestAgent", [])) > 0
        assert "mock_provider:test-model" in collector._token_usage

    def test_telemetry_config(self):
        """Test telemetry configuration."""
        from agenticraft.telemetry.integration import TelemetryConfig

        # Test default config
        config = TelemetryConfig()
        assert config.enabled is True
        assert config.traces_enabled is True
        assert config.metrics_enabled is True
        assert config.exporter_type == "console"

        # Test from environment
        with patch.dict(
            "os.environ",
            {
                "AGENTICRAFT_TELEMETRY_ENABLED": "false",
                "AGENTICRAFT_EXPORTER_TYPE": "otlp",
                "AGENTICRAFT_OTLP_ENDPOINT": "localhost:4318",
            },
        ):
            env_config = TelemetryConfig.from_env()
            assert env_config.enabled is False
            assert env_config.exporter_type == "otlp"
            assert env_config.otlp_endpoint == "localhost:4318"

    def test_memory_operation_decorator(self):
        """Test memory operation instrumentation."""
        from agenticraft.telemetry.integration import instrument_memory_operation

        initialize_metrics(MetricsConfig(enabled=True))

        class MockMemory:
            @instrument_memory_operation("get", "test_memory")
            def get(self, key: str):
                return "value" if key == "exists" else None

            @instrument_memory_operation("set", "test_memory")
            def set(self, key: str, value: str):
                return True

        memory = MockMemory()

        # Test get operation (hit)
        result = memory.get("exists")
        assert result == "value"

        # Test get operation (miss)
        result = memory.get("missing")
        assert result is None

        # Test set operation
        result = memory.set("key", "value")
        assert result is True

        # Verify metrics
        collector = get_metrics_collector()
        assert "test_memory:get" in collector._memory_ops
        assert collector._memory_ops["test_memory:get"]["hits"] == 1
        assert collector._memory_ops["test_memory:get"]["misses"] == 1
        assert collector._memory_ops["test_memory:set"]["total"] == 1


class TestPerformance:
    """Test telemetry performance impact."""

    @pytest.mark.asyncio
    async def test_telemetry_overhead(self):
        """Test that telemetry overhead is minimal."""
        import time

        # Initialize with console exporter (fast)
        initialize_tracer(TracerConfig(enabled=True, exporter_type="console"))
        initialize_metrics(MetricsConfig(enabled=True, exporter_type="console"))

        # Measure operation without telemetry
        start = time.time()
        for _ in range(100):
            # Simulate work
            await asyncio.sleep(0.001)
        baseline = time.time() - start

        # Measure operation with telemetry
        start = time.time()
        for i in range(100):
            with create_span(f"test.operation.{i}") as span:
                set_span_attributes({"iteration": i})
                record_latency("test.operation", 1.0)
                await asyncio.sleep(0.001)
        with_telemetry = time.time() - start

        # Calculate overhead
        overhead = (with_telemetry - baseline) / baseline * 100

        # Overhead should be less than 10%
        assert overhead < 10, f"Telemetry overhead too high: {overhead:.1f}%"
