"""Telemetry decorators for AgentiCraft.

This module provides decorators for adding telemetry to functions
and methods, including automatic tracing, metrics collection, and
error tracking.

Example:
    Using telemetry decorators::

        from agenticraft.telemetry.decorators import track_metrics, trace

        @trace(name="api.process_request")
        @track_metrics(
            labels=["method", "endpoint"],
            track_duration=True,
            track_errors=True
        )
        async def process_request(method: str, endpoint: str):
            # Automatically traced and measured
            return await handle_api_call(method, endpoint)
"""

import asyncio
import functools
import time
from collections.abc import Callable
from typing import Any

from opentelemetry import trace as otel_trace
from opentelemetry.trace import Span, SpanKind, Status, StatusCode

from ..core.telemetry import get_global_telemetry
from .tracer import get_current_trace_id, get_tracer


def track_metrics(
    name: str | None = None,
    labels: list[str] | None = None,
    track_duration: bool = True,
    track_errors: bool = True,
    track_calls: bool = True,
    custom_metrics: dict[str, str] | None = None,
) -> Callable:
    """Decorator to track metrics for a function.

    Args:
        name: Metric name prefix (defaults to function name)
        labels: List of parameter names to use as metric labels
        track_duration: Whether to track execution duration
        track_errors: Whether to track error count
        track_calls: Whether to track call count
        custom_metrics: Additional metrics to track

    Example:
        @track_metrics(
            labels=["agent_name", "tool_name"],
            track_duration=True
        )
        async def execute_tool(agent_name: str, tool_name: str, args: dict):
            # Metrics will be tracked with agent_name and tool_name labels
            return await tool.run(args)
    """

    def decorator(func: Callable) -> Callable:
        # Determine metric name
        metric_name = name or f"{func.__module__}.{func.__name__}"
        metric_labels = labels or []

        # Get telemetry instance
        telemetry = get_global_telemetry()

        # Create metrics if telemetry is available
        call_counter = None
        error_counter = None
        duration_histogram = None

        if telemetry and telemetry.meter:
            meter = telemetry.meter

            if track_calls:
                call_counter = meter.create_counter(
                    f"{metric_name}.calls",
                    description=f"Number of calls to {func.__name__}",
                )

            if track_errors:
                error_counter = meter.create_counter(
                    f"{metric_name}.errors",
                    description=f"Number of errors in {func.__name__}",
                )

            if track_duration:
                duration_histogram = meter.create_histogram(
                    f"{metric_name}.duration",
                    description=f"Execution duration of {func.__name__}",
                    unit="s",
                )

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()

            # Extract label values
            label_values = _extract_label_values(func, args, kwargs, metric_labels)

            # Track call
            if call_counter:
                call_counter.add(1, label_values)

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                # Track error
                if error_counter:
                    error_label_values = {
                        **label_values,
                        "error_type": type(e).__name__,
                    }
                    error_counter.add(1, error_label_values)
                raise
            finally:
                # Track duration
                if duration_histogram:
                    duration = time.time() - start_time
                    duration_histogram.record(duration, label_values)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()

            # Extract label values
            label_values = _extract_label_values(func, args, kwargs, metric_labels)

            # Track call
            if call_counter:
                call_counter.add(1, label_values)

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                # Track error
                if error_counter:
                    error_label_values = {
                        **label_values,
                        "error_type": type(e).__name__,
                    }
                    error_counter.add(1, error_label_values)
                raise
            finally:
                # Track duration
                if duration_histogram:
                    duration = time.time() - start_time
                    duration_histogram.record(duration, label_values)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def trace(
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
    record_exception: bool = True,
    set_status_on_exception: bool = True,
) -> Callable:
    """Decorator to add tracing to a function.

    Args:
        name: Span name (defaults to function name)
        attributes: Static span attributes
        kind: Span kind (INTERNAL, SERVER, CLIENT, etc.)
        record_exception: Whether to record exceptions
        set_status_on_exception: Whether to set error status on exception

    Example:
        @trace(
            attributes={"component": "agent"},
            kind=trace.SpanKind.SERVER
        )
        async def handle_agent_request(request):
            return await process(request)
    """

    def decorator(func: Callable) -> Callable:
        span_name = name or f"{func.__module__}.{func.__name__}"
        tracer = get_tracer(func.__module__)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(
                span_name, kind=kind, attributes=attributes
            ) as span:
                try:
                    # Add dynamic attributes from function parameters
                    _add_span_attributes_from_params(span, func, args, kwargs)

                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    if record_exception:
                        span.record_exception(e)
                    if set_status_on_exception:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(
                span_name, kind=kind, attributes=attributes
            ) as span:
                try:
                    # Add dynamic attributes from function parameters
                    _add_span_attributes_from_params(span, func, args, kwargs)

                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    if record_exception:
                        span.record_exception(e)
                    if set_status_on_exception:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def measure_time(metric_name: str, labels: dict[str, str] | None = None) -> Callable:
    """Simple decorator to measure execution time.

    Args:
        metric_name: Name for the duration metric
        labels: Static labels for the metric

    Example:
        @measure_time("database.query.duration", {"db": "postgres"})
        def query_database(sql: str):
            return db.execute(sql)
    """

    def decorator(func: Callable) -> Callable:
        telemetry = get_global_telemetry()

        # Create histogram metric
        histogram = None
        if telemetry and telemetry.meter:
            histogram = telemetry.meter.create_histogram(
                metric_name, description=f"Duration of {func.__name__}", unit="s"
            )

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                if histogram:
                    duration = time.time() - start
                    histogram.record(duration, labels or {})

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                if histogram:
                    duration = time.time() - start
                    histogram.record(duration, labels or {})

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def count_calls(metric_name: str, labels: dict[str, str] | None = None) -> Callable:
    """Decorator to count function calls.

    Args:
        metric_name: Name for the counter metric
        labels: Static labels for the metric

    Example:
        @count_calls("api.requests", {"version": "v1"})
        async def handle_api_request(request):
            return process(request)
    """

    def decorator(func: Callable) -> Callable:
        telemetry = get_global_telemetry()

        # Create counter metric
        counter = None
        if telemetry and telemetry.meter:
            counter = telemetry.meter.create_counter(
                metric_name, description=f"Count of {func.__name__} calls"
            )

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if counter:
                counter.add(1, labels or {})
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if counter:
                counter.add(1, labels or {})
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def observe_value(
    metric_name: str,
    value_func: Callable[..., int | float],
    labels: dict[str, str] | None = None,
) -> Callable:
    """Decorator to observe a value from function result.

    Args:
        metric_name: Name for the gauge metric
        value_func: Function to extract value from result
        labels: Static labels for the metric

    Example:
        @observe_value(
            "cache.size",
            value_func=lambda result: len(result),
            labels={"cache": "memory"}
        )
        def get_cache_contents():
            return cache.get_all()
    """

    def decorator(func: Callable) -> Callable:
        telemetry = get_global_telemetry()

        # Create gauge metric
        gauge = None
        if telemetry and telemetry.meter:
            gauge = telemetry.meter.create_gauge(
                metric_name, description=f"Value observed from {func.__name__}"
            )

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            if gauge:
                try:
                    value = value_func(result)
                    gauge.set(value, labels or {})
                except Exception:
                    pass  # Don't fail if metric extraction fails
            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if gauge:
                try:
                    value = value_func(result)
                    gauge.set(value, labels or {})
                except Exception:
                    pass  # Don't fail if metric extraction fails
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Helper functions


def _extract_label_values(
    func: Callable, args: tuple, kwargs: dict, label_names: list[str]
) -> dict[str, str]:
    """Extract label values from function parameters.

    Args:
        func: The function being called
        args: Positional arguments
        kwargs: Keyword arguments
        label_names: Names of parameters to extract

    Returns:
        Dictionary of label values
    """
    import inspect

    sig = inspect.signature(func)
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()

    label_values = {}
    for label_name in label_names:
        if label_name in bound_args.arguments:
            value = bound_args.arguments[label_name]
            # Convert to string for metric labels
            label_values[label_name] = str(value)

    return label_values


def _add_span_attributes_from_params(
    span: Span, func: Callable, args: tuple, kwargs: dict, prefix: str = "param"
) -> None:
    """Add span attributes from function parameters.

    Only adds simple types (str, int, float, bool) as attributes.

    Args:
        span: The span to add attributes to
        func: The function being called
        args: Positional arguments
        kwargs: Keyword arguments
        prefix: Prefix for attribute names
    """
    import inspect

    sig = inspect.signature(func)
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()

    for param_name, value in bound_args.arguments.items():
        if isinstance(value, (str, int, float, bool)):
            span.set_attribute(f"{prefix}.{param_name}", value)


# Convenience decorators for common patterns


def trace_agent_method(method_name: str | None = None) -> Callable:
    """Specialized decorator for agent methods.

    Automatically adds agent-specific attributes and metrics.

    Example:
        class MyAgent(Agent):
            @trace_agent_method()
            async def process(self, input: str) -> str:
                return await self._generate_response(input)
    """

    def decorator(func: Callable) -> Callable:
        name = method_name or func.__name__

        @trace(name=f"agent.{name}", kind=SpanKind.INTERNAL)
        @track_metrics(
            name=f"agenticraft.agent.{name}",
            labels=["agent_name"],
            track_duration=True,
            track_errors=True,
        )
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Add agent context to current span
            span = otel_trace.get_current_span()
            if span and hasattr(self, "name"):
                span.set_attribute("agent.name", self.name)
                span.set_attribute("agent.id", getattr(self, "id", "unknown"))

                # Add trace ID to span attributes instead of kwargs
                trace_id = get_current_trace_id()
                if trace_id:
                    span.set_attribute("trace.id", trace_id)

            return await func(self, *args, **kwargs)

        return wrapper

    return decorator


def trace_tool_execution(tool_name: str | None = None) -> Callable:
    """Specialized decorator for tool execution.

    Example:
        @trace_tool_execution("web_search")
        async def search_web(query: str) -> List[Dict]:
            return await search_api.search(query)
    """

    def decorator(func: Callable) -> Callable:
        name = tool_name or func.__name__

        @trace(
            name=f"tool.{name}", kind=SpanKind.CLIENT, attributes={"tool.name": name}
        )
        @track_metrics(
            name=f"agenticraft.tool.{name}", track_duration=True, track_errors=True
        )
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator
