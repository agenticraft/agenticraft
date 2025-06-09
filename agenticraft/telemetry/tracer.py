"""OpenTelemetry tracer implementation for AgentiCraft.

This module provides distributed tracing capabilities with:
- Automatic span creation and propagation
- Attribute collection
- Error tracking
- Context management
"""

import functools
import time
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, TypeVar

from opentelemetry import trace
from opentelemetry.context import attach, detach

# Optional imports for exporters
try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    HAS_OTLP = True
except ImportError:
    HAS_OTLP = False
    OTLPSpanExporter = None

try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter

    HAS_JAEGER = True
except ImportError:
    HAS_JAEGER = False
    JaegerExporter = None
from opentelemetry.propagate import extract, inject
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from pydantic import BaseModel

# Type variable for decorators
F = TypeVar("F", bound=Callable[..., Any])


class TracerConfig(BaseModel):
    """Configuration for OpenTelemetry tracer."""

    service_name: str = "agenticraft"
    service_version: str = "0.2.0"
    enabled: bool = True
    exporter_type: str = "console"  # console, otlp, jaeger
    otlp_endpoint: str | None = None
    jaeger_agent_host: str = "localhost"
    jaeger_agent_port: int = 6831
    batch_export: bool = True
    sample_rate: float = 1.0  # 1.0 = 100% sampling

    # Performance settings
    max_queue_size: int = 2048
    max_export_batch_size: int = 512
    export_timeout_millis: int = 30000


# Global tracer instance
_tracer_provider: TracerProvider | None = None
_tracer: trace.Tracer | None = None
_config: TracerConfig | None = None


def initialize_tracer(config: TracerConfig | None = None) -> trace.Tracer:
    """Initialize the OpenTelemetry tracer.

    Args:
        config: Tracer configuration

    Returns:
        Configured tracer instance
    """
    global _tracer_provider, _tracer, _config

    if _tracer is not None and config is None:
        return _tracer

    _config = config or TracerConfig()

    if not _config.enabled:
        # Use no-op tracer when disabled
        trace.set_tracer_provider(trace.NoOpTracerProvider())
        _tracer = trace.get_tracer(__name__)
        return _tracer

    # Create resource
    resource = Resource.create(
        {
            SERVICE_NAME: _config.service_name,
            SERVICE_VERSION: _config.service_version,
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry",
        }
    )

    # Create tracer provider
    _tracer_provider = TracerProvider(
        resource=resource, sampler=TraceIdRatioBased(_config.sample_rate)
    )

    # Configure exporter
    if _config.exporter_type == "console":
        exporter = ConsoleSpanExporter()
    elif _config.exporter_type == "otlp":
        if not HAS_OTLP:
            raise ImportError(
                "OTLP exporter not available. Install with: pip install opentelemetry-exporter-otlp"
            )
        exporter = OTLPSpanExporter(
            endpoint=_config.otlp_endpoint or "localhost:4317", insecure=True
        )
    elif _config.exporter_type == "jaeger":
        if not HAS_JAEGER:
            raise ImportError(
                "Jaeger exporter not available. Install with: pip install opentelemetry-exporter-jaeger"
            )
        exporter = JaegerExporter(
            agent_host_name=_config.jaeger_agent_host,
            agent_port=_config.jaeger_agent_port,
        )
    else:
        raise ValueError(f"Unknown exporter type: {_config.exporter_type}")

    # Configure processor
    if _config.batch_export:
        processor = BatchSpanProcessor(
            exporter,
            max_queue_size=_config.max_queue_size,
            max_export_batch_size=_config.max_export_batch_size,
            export_timeout_millis=_config.export_timeout_millis,
        )
    else:
        processor = SimpleSpanProcessor(exporter)

    _tracer_provider.add_span_processor(processor)

    # Set as global provider
    trace.set_tracer_provider(_tracer_provider)

    # Get tracer
    _tracer = trace.get_tracer(_config.service_name, _config.service_version)

    return _tracer


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance.

    Returns:
        The tracer instance
    """
    if _tracer is None:
        return initialize_tracer()
    return _tracer


@contextmanager
def create_span(
    name: str,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
    links: list | None = None,
):
    """Create a new span.

    Args:
        name: Span name
        kind: Span kind (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
        attributes: Initial span attributes
        links: Links to other spans

    Yields:
        The created span

    Example:
        with create_span("process_request") as span:
            span.set_attribute("request.id", request_id)
            # Process request
    """
    tracer = get_tracer()

    with tracer.start_as_current_span(
        name, kind=kind, attributes=attributes, links=links
    ) as span:
        yield span


def set_span_attributes(attributes: dict[str, Any]) -> None:
    """Set attributes on the current span.

    Args:
        attributes: Dictionary of attributes to set
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            # Convert values to supported types
            if isinstance(value, (str, bool, int, float)):
                span.set_attribute(key, value)
            elif isinstance(value, (list, tuple)):
                # OpenTelemetry supports homogeneous sequences
                if all(isinstance(v, (str, bool, int, float)) for v in value):
                    span.set_attribute(key, value)
                else:
                    span.set_attribute(key, str(value))
            else:
                span.set_attribute(key, str(value))


def record_exception(
    exception: Exception,
    attributes: dict[str, Any] | None = None,
    escaped: bool = False,
) -> None:
    """Record an exception on the current span.

    Args:
        exception: The exception to record
        attributes: Additional attributes
        escaped: Whether the exception escaped
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.record_exception(exception, attributes=attributes)
        if escaped:
            span.set_status(Status(StatusCode.ERROR, str(exception)))


def trace_method(
    name: str | None = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
) -> Callable[[F], F]:
    """Decorator to trace a method.

    Args:
        name: Span name (defaults to function name)
        kind: Span kind
        attributes: Initial attributes

    Returns:
        Decorated function

    Example:
        @trace_method("agent.run")
        async def run(self, prompt: str):
            # Method implementation
    """

    def decorator(func: F) -> F:
        span_name = name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with create_span(span_name, kind=kind, attributes=attributes) as span:
                try:
                    # Add function arguments as attributes
                    if args and hasattr(args[0], "__class__"):
                        span.set_attribute("class", args[0].__class__.__name__)

                    # Add selected kwargs as attributes
                    for key in ["model", "provider", "agent_name", "tool_name"]:
                        if key in kwargs:
                            span.set_attribute(f"param.{key}", str(kwargs[key]))

                    # Execute function
                    start_time = time.time()
                    result = await func(*args, **kwargs)

                    # Record duration
                    duration = time.time() - start_time
                    span.set_attribute("duration_seconds", duration)

                    return result

                except Exception as e:
                    record_exception(e, escaped=True)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with create_span(span_name, kind=kind, attributes=attributes) as span:
                try:
                    # Add function arguments as attributes
                    if args and hasattr(args[0], "__class__"):
                        span.set_attribute("class", args[0].__class__.__name__)

                    # Add selected kwargs as attributes
                    for key in ["model", "provider", "agent_name", "tool_name"]:
                        if key in kwargs:
                            span.set_attribute(f"param.{key}", str(kwargs[key]))

                    # Execute function
                    start_time = time.time()
                    result = func(*args, **kwargs)

                    # Record duration
                    duration = time.time() - start_time
                    span.set_attribute("duration_seconds", duration)

                    return result

                except Exception as e:
                    record_exception(e, escaped=True)
                    raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Semantic convention helpers


def set_agent_attributes(
    agent_name: str,
    agent_type: str,
    instructions: str | None = None,
    model: str | None = None,
    provider: str | None = None,
) -> None:
    """Set agent-specific attributes on current span.

    Args:
        agent_name: Name of the agent
        agent_type: Type of agent
        instructions: Agent instructions
        model: LLM model being used
        provider: LLM provider
    """
    attributes = {
        "agent.name": agent_name,
        "agent.type": agent_type,
    }

    if instructions:
        attributes["agent.instructions"] = instructions[
            :200
        ]  # Truncate long instructions
    if model:
        attributes["llm.model"] = model
    if provider:
        attributes["llm.provider"] = provider

    set_span_attributes(attributes)


def set_tool_attributes(
    tool_name: str, tool_type: str, parameters: dict[str, Any] | None = None
) -> None:
    """Set tool-specific attributes on current span.

    Args:
        tool_name: Name of the tool
        tool_type: Type of tool
        parameters: Tool parameters
    """
    attributes = {
        "tool.name": tool_name,
        "tool.type": tool_type,
    }

    if parameters:
        # Add flattened parameters
        for key, value in parameters.items():
            if isinstance(value, (str, bool, int, float)):
                attributes[f"tool.param.{key}"] = value

    set_span_attributes(attributes)


def set_llm_attributes(
    model: str,
    provider: str,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> None:
    """Set LLM-specific attributes on current span.

    Args:
        model: Model name
        provider: Provider name
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        total_tokens: Total token count
        temperature: Temperature setting
        max_tokens: Max tokens setting
    """
    attributes = {
        "llm.model": model,
        "llm.provider": provider,
    }

    if prompt_tokens is not None:
        attributes["llm.prompt_tokens"] = prompt_tokens
    if completion_tokens is not None:
        attributes["llm.completion_tokens"] = completion_tokens
    if total_tokens is not None:
        attributes["llm.total_tokens"] = total_tokens
    if temperature is not None:
        attributes["llm.temperature"] = temperature
    if max_tokens is not None:
        attributes["llm.max_tokens"] = max_tokens

    set_span_attributes(attributes)


def set_memory_attributes(
    operation: str,
    memory_type: str,
    key: str | None = None,
    size: int | None = None,
    hit: bool | None = None,
) -> None:
    """Set memory operation attributes on current span.

    Args:
        operation: Operation type (get, set, delete, search)
        memory_type: Type of memory
        key: Memory key
        size: Size of data
        hit: Whether it was a cache hit
    """
    attributes = {
        "memory.operation": operation,
        "memory.type": memory_type,
    }

    if key:
        attributes["memory.key"] = key
    if size is not None:
        attributes["memory.size_bytes"] = size
    if hit is not None:
        attributes["memory.hit"] = hit

    set_span_attributes(attributes)


# Context propagation helpers


def inject_context(carrier: dict[str, str]) -> None:
    """Inject trace context into a carrier for propagation.

    Args:
        carrier: Dictionary to inject context into
    """
    propagator = TraceContextTextMapPropagator()
    inject(carrier)


def extract_context(carrier: dict[str, str]) -> Any:
    """Extract trace context from a carrier.

    Args:
        carrier: Dictionary containing trace context

    Returns:
        Context token
    """
    propagator = TraceContextTextMapPropagator()
    return extract(carrier)


@contextmanager
def use_context(carrier: dict[str, str]):
    """Use trace context from a carrier.

    Args:
        carrier: Dictionary containing trace context

    Example:
        with use_context(headers):
            # Operations will be linked to parent trace
    """
    token = extract_context(carrier)
    token = attach(token)
    try:
        yield
    finally:
        detach(token)


# Convenience functions for common operations


def trace_agent_execution(agent_name: str, agent_type: str = "base"):
    """Decorator specifically for agent execution methods."""
    return trace_method(
        name=f"agent.{agent_name}.execute",
        kind=trace.SpanKind.INTERNAL,
        attributes={"agent.name": agent_name, "agent.type": agent_type},
    )


def trace_tool_execution(tool_name: str, tool_type: str = "function"):
    """Decorator specifically for tool execution."""
    return trace_method(
        name=f"tool.{tool_name}.execute",
        kind=trace.SpanKind.INTERNAL,
        attributes={"tool.name": tool_name, "tool.type": tool_type},
    )


def trace_llm_call(provider: str, model: str):
    """Decorator specifically for LLM API calls."""
    return trace_method(
        name=f"llm.{provider}.call",
        kind=trace.SpanKind.CLIENT,
        attributes={"llm.provider": provider, "llm.model": model},
    )


# Import asyncio for the decorator
import asyncio

# Utility functions


def get_current_trace_id() -> str | None:
    """Get the current trace ID.

    Returns:
        Trace ID as hex string or None if no active span
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        context = span.get_span_context()
        if context and context.trace_id:
            return format(context.trace_id, "032x")
    return None


# Shutdown function
def shutdown_tracer() -> None:
    """Shutdown the tracer and flush any pending spans."""
    global _tracer_provider

    if _tracer_provider:
        _tracer_provider.shutdown()
        _tracer_provider = None
