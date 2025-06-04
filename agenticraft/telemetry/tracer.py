"""OpenTelemetry tracer setup for AgentiCraft.

This module provides the tracer initialization and configuration
for distributed tracing across AgentiCraft applications.

Example:
    Basic tracer setup::
    
        from agenticraft.telemetry import setup_tracing, get_tracer
        
        # Initialize tracing
        setup_tracing(
            service_name="my-agent-service",
            endpoint="http://jaeger:4317"
        )
        
        # Get a tracer
        tracer = get_tracer(__name__)
        
        # Create spans
        with tracer.start_as_current_span("process_request"):
            # Your code here
            pass
"""

import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Callable

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource

# Try to import exporters, but don't fail if they're not available
try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
except ImportError:
    OTLPSpanExporter = None
    
try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
except ImportError:
    JaegerExporter = None
    
try:
    from opentelemetry.exporter.zipkin.json import ZipkinExporter
except ImportError:
    ZipkinExporter = None
from opentelemetry.sdk.trace import TracerProvider, SpanProcessor
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor
)
from opentelemetry.sdk.trace.sampling import (
    TraceIdRatioBased,
    ParentBased,
    Sampler
)
# AlwaysOff and AlwaysOn might not be available in all versions
try:
    from opentelemetry.sdk.trace.sampling import AlwaysOff, AlwaysOn
except ImportError:
    # Create simple implementations if not available
    class AlwaysOff(Sampler):
        def should_sample(self, *args, **kwargs):
            return False
    
    class AlwaysOn(Sampler):
        def should_sample(self, *args, **kwargs):
            return True
from opentelemetry.trace import Status, StatusCode
# Try to import instrumentors
try:
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
except ImportError:
    HTTPXClientInstrumentor = None
    
try:
    from opentelemetry.instrumentation.grpc import (
        GrpcInstrumentorClient,
        GrpcInstrumentorServer
    )
except ImportError:
    GrpcInstrumentorClient = None
    GrpcInstrumentorServer = None

from .config import TelemetryConfig, ExportFormat, ResourceConfig

logger = logging.getLogger(__name__)


class TracerManager:
    """Manages OpenTelemetry tracer setup and configuration."""
    
    def __init__(self, config: TelemetryConfig):
        """Initialize tracer manager.
        
        Args:
            config: Telemetry configuration
        """
        self.config = config
        self._tracer_provider: Optional[TracerProvider] = None
        self._instrumentors: List[Any] = []
    
    def setup(self) -> None:
        """Set up the tracer with configured exporters and processors."""
        if not self.config.enabled or not self.config.export_traces:
            logger.info("Tracing is disabled")
            return
        
        # Create resource
        resource = self._create_resource()
        
        # Create sampler
        sampler = self._create_sampler()
        
        # Create tracer provider
        self._tracer_provider = TracerProvider(
            resource=resource,
            sampler=sampler
        )
        
        # Add span processors
        processors = self._create_span_processors()
        for processor in processors:
            self._tracer_provider.add_span_processor(processor)
        
        # Set as global tracer provider
        trace.set_tracer_provider(self._tracer_provider)
        
        # Set up instrumentation
        self._setup_instrumentation()
        
        logger.info(
            f"Tracing initialized with {self.config.trace_exporter.format} exporter"
        )
    
    def _create_resource(self) -> Resource:
        """Create OpenTelemetry resource from config."""
        attributes = {
            "service.name": self.config.resource.service_name,
            "service.version": self.config.resource.service_version,
            "deployment.environment": self.config.resource.environment.value,
        }
        
        if self.config.resource.service_instance_id:
            attributes["service.instance.id"] = self.config.resource.service_instance_id
        
        # Add custom attributes
        attributes.update(self.config.resource.attributes)
        
        return Resource.create(attributes)
    
    def _create_sampler(self) -> Sampler:
        """Create sampler from configuration."""
        base_sampler = TraceIdRatioBased(self.config.sampling.sample_rate)
        
        if self.config.sampling.parent_based:
            return ParentBased(root=base_sampler)
        
        return base_sampler
    
    def _create_span_processors(self) -> List[SpanProcessor]:
        """Create span processors based on configuration."""
        processors = []
        
        exporter = self._create_span_exporter()
        if exporter:
            if self.config.trace_exporter.format == ExportFormat.CONSOLE:
                # Use simple processor for console output
                processors.append(SimpleSpanProcessor(exporter))
            else:
                # Use batch processor for network exporters
                processors.append(BatchSpanProcessor(
                    exporter,
                    max_queue_size=2048,
                    max_export_batch_size=512,
                    export_timeout_millis=self.config.trace_exporter.timeout_ms
                ))
        
        return processors
    
    def _create_span_exporter(self):
        """Create appropriate span exporter based on format."""
        format_type = self.config.trace_exporter.format
        
        if format_type == ExportFormat.NONE:
            return None
        
        if format_type == ExportFormat.CONSOLE:
            return ConsoleSpanExporter()
        
        if format_type == ExportFormat.OTLP:
            if OTLPSpanExporter is None:
                logger.warning("OTLP exporter not available. Install opentelemetry-exporter-otlp")
                return ConsoleSpanExporter()
            return OTLPSpanExporter(
                endpoint=self.config.trace_exporter.endpoint,
                headers=self.config.trace_exporter.headers,
                insecure=self.config.trace_exporter.insecure
            )
        
        if format_type == ExportFormat.JAEGER:
            if JaegerExporter is None:
                logger.warning("Jaeger exporter not available. Install opentelemetry-exporter-jaeger")
                return ConsoleSpanExporter()
            # Parse Jaeger endpoint
            if self.config.trace_exporter.endpoint:
                parts = self.config.trace_exporter.endpoint.split(":")
                agent_host = parts[0] if parts else "localhost"
                agent_port = int(parts[1]) if len(parts) > 1 else 6831
            else:
                agent_host = "localhost"
                agent_port = 6831
                
            return JaegerExporter(
                agent_host_name=agent_host,
                agent_port=agent_port,
                udp_split_oversized_batches=True
            )
        
        if format_type == ExportFormat.ZIPKIN:
            if ZipkinExporter is None:
                logger.warning("Zipkin exporter not available. Install opentelemetry-exporter-zipkin")
                return ConsoleSpanExporter()
            return ZipkinExporter(
                endpoint=self.config.trace_exporter.endpoint
            )
        
        raise ValueError(f"Unsupported trace exporter format: {format_type}")
    
    def _setup_instrumentation(self) -> None:
        """Set up automatic instrumentation based on config."""
        instrumentation = self.config.instrumentation
        
        if instrumentation.instrument_http:
            if HTTPXClientInstrumentor is None:
                logger.warning("HTTPX instrumentation not available")
            else:
                instrumentor = HTTPXClientInstrumentor()
                instrumentor.instrument(
                    tracer_provider=self._tracer_provider,
                    excluded_urls=instrumentation.excluded_urls
                )
                self._instrumentors.append(instrumentor)
        
        if instrumentation.instrument_grpc:
            if GrpcInstrumentorClient is None or GrpcInstrumentorServer is None:
                logger.warning("gRPC instrumentation not available")
            else:
                # Client instrumentation
                client_instrumentor = GrpcInstrumentorClient()
                client_instrumentor.instrument(tracer_provider=self._tracer_provider)
                self._instrumentors.append(client_instrumentor)
                
                # Server instrumentation
                server_instrumentor = GrpcInstrumentorServer()
                server_instrumentor.instrument(tracer_provider=self._tracer_provider)
                self._instrumentors.append(server_instrumentor)
    
    def shutdown(self) -> None:
        """Shutdown tracer and exporters."""
        # Uninstrument all instrumentors
        for instrumentor in self._instrumentors:
            try:
                instrumentor.uninstrument()
            except Exception as e:
                logger.warning(f"Failed to uninstrument: {e}")
        
        # Shutdown tracer provider
        if self._tracer_provider:
            self._tracer_provider.shutdown()
            
        logger.info("Tracing shutdown complete")
    
    def get_tracer(self, name: str, version: Optional[str] = None) -> trace.Tracer:
        """Get a tracer instance.
        
        Args:
            name: Name of the tracer (usually __name__)
            version: Optional version string
            
        Returns:
            Tracer instance
        """
        if self._tracer_provider:
            return self._tracer_provider.get_tracer(name, version)
        return trace.get_tracer(name, version)


# Global tracer manager
_tracer_manager: Optional[TracerManager] = None


def setup_tracing(
    config: Optional[TelemetryConfig] = None,
    service_name: Optional[str] = None,
    endpoint: Optional[str] = None
) -> TracerManager:
    """Set up global tracing.
    
    Args:
        config: Full telemetry configuration
        service_name: Service name (if not using config)
        endpoint: Exporter endpoint (if not using config)
        
    Returns:
        TracerManager instance
    """
    global _tracer_manager
    
    if config is None:
        # Create config from environment or parameters
        config = TelemetryConfig.from_env()
        
        if service_name:
            config.resource.service_name = service_name
        
        if endpoint:
            config.trace_exporter.endpoint = endpoint
    
    _tracer_manager = TracerManager(config)
    _tracer_manager.setup()
    
    return _tracer_manager


def get_tracer(name: str, version: Optional[str] = None) -> trace.Tracer:
    """Get a tracer instance.
    
    Args:
        name: Name of the tracer (usually __name__)
        version: Optional version string
        
    Returns:
        Tracer instance
    """
    if _tracer_manager:
        return _tracer_manager.get_tracer(name, version)
    return trace.get_tracer(name, version)


def shutdown_tracing() -> None:
    """Shutdown global tracing."""
    global _tracer_manager
    
    if _tracer_manager:
        _tracer_manager.shutdown()
        _tracer_manager = None


# Utility functions for common tracing patterns

@contextmanager
def traced_operation(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    record_exception: bool = True
):
    """Context manager for traced operations.
    
    Args:
        name: Operation name
        attributes: Span attributes
        record_exception: Whether to record exceptions
        
    Example:
        with traced_operation("database_query", {"query.type": "select"}):
            result = db.query("SELECT * FROM users")
    """
    tracer = get_tracer(__name__)
    
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        try:
            yield span
        except Exception as e:
            if record_exception:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None
) -> Callable:
    """Decorator to trace function execution.
    
    Args:
        name: Span name (defaults to function name)
        attributes: Additional span attributes
        
    Example:
        @trace_function(attributes={"handler.type": "api"})
        async def handle_request(request):
            return {"status": "ok"}
    """
    def decorator(func: Callable) -> Callable:
        span_name = name or f"{func.__module__}.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            with traced_operation(span_name, attributes):
                return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            with traced_operation(span_name, attributes):
                return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def add_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """Add an event to the current span.
    
    Args:
        name: Event name
        attributes: Event attributes
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.add_event(name, attributes or {})


def set_attribute(key: str, value: Any) -> None:
    """Set an attribute on the current span.
    
    Args:
        key: Attribute key
        value: Attribute value
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_attribute(key, value)


def get_current_trace_id() -> Optional[str]:
    """Get the current trace ID if available.
    
    Returns:
        Trace ID as hex string or None
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        context = span.get_span_context()
        if context.trace_id:
            return format(context.trace_id, "032x")
    return None


import asyncio  # Add this import at the top
