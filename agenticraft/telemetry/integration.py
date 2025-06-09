"""Integration module for adding telemetry to AgentiCraft components.

This module provides decorators and utilities to automatically instrument
agents, tools, providers, and memory operations with telemetry.
"""

import asyncio
import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar

from ..core.agent import Agent, AgentResponse
from ..core.provider import BaseProvider
from ..core.tool import FunctionTool as Tool
from .metrics import (
    LatencyTimer,
    record_error,
    record_latency,
    record_memory_operation,
    record_token_usage,
)
from .tracer import (
    create_span,
    set_agent_attributes,
    set_llm_attributes,
    set_memory_attributes,
    set_tool_attributes,
)

F = TypeVar("F", bound=Callable[..., Any])


def instrument_agent(agent_class: type[Agent]) -> type[Agent]:
    """Instrument an agent class with telemetry.

    Args:
        agent_class: Agent class to instrument

    Returns:
        Instrumented agent class
    """
    # Save original methods
    original_run = agent_class.run
    original_arun = agent_class.arun

    @functools.wraps(original_run)
    def instrumented_run(self, *args, **kwargs) -> AgentResponse:
        """Instrumented run method."""
        with create_span(f"agent.{self.name}.run") as span:
            try:
                # Set agent attributes
                set_agent_attributes(
                    agent_name=self.name,
                    agent_type=self.__class__.__name__,
                    instructions=getattr(self, "instructions", None),
                    model=getattr(self, "model", None),
                    provider=(
                        getattr(self.provider, "name", None)
                        if hasattr(self, "provider")
                        else None
                    ),
                )

                # Measure latency
                start_time = time.time()

                # Execute original method
                result = original_run(self, *args, **kwargs)

                # Record metrics
                duration_ms = (time.time() - start_time) * 1000
                record_latency(f"agent.{self.name}", duration_ms)

                # Record token usage if available
                if hasattr(result, "usage") and result.usage:
                    provider_name = (
                        getattr(self.provider, "name", "unknown")
                        if hasattr(self, "provider")
                        else "unknown"
                    )
                    record_token_usage(
                        provider=provider_name,
                        model=getattr(self, "model", "unknown"),
                        prompt_tokens=result.usage.get("prompt_tokens", 0),
                        completion_tokens=result.usage.get("completion_tokens", 0),
                        total_tokens=result.usage.get("total_tokens"),
                    )

                return result

            except Exception as e:
                record_error(type(e).__name__, f"agent.{self.name}")
                raise

    @functools.wraps(original_arun)
    async def instrumented_arun(self, *args, **kwargs) -> AgentResponse:
        """Instrumented async run method."""
        with create_span(f"agent.{self.name}.arun") as span:
            try:
                # Set agent attributes
                set_agent_attributes(
                    agent_name=self.name,
                    agent_type=self.__class__.__name__,
                    instructions=getattr(self, "instructions", None),
                    model=getattr(self, "model", None),
                    provider=(
                        getattr(self.provider, "name", None)
                        if hasattr(self, "provider")
                        else None
                    ),
                )

                # Measure latency
                start_time = time.time()

                # Execute original method
                result = await original_arun(self, *args, **kwargs)

                # Record metrics
                duration_ms = (time.time() - start_time) * 1000
                record_latency(f"agent.{self.name}", duration_ms)

                # Record token usage if available
                if hasattr(result, "usage") and result.usage:
                    provider_name = (
                        getattr(self.provider, "name", "unknown")
                        if hasattr(self, "provider")
                        else "unknown"
                    )
                    record_token_usage(
                        provider=provider_name,
                        model=getattr(self, "model", "unknown"),
                        prompt_tokens=result.usage.get("prompt_tokens", 0),
                        completion_tokens=result.usage.get("completion_tokens", 0),
                        total_tokens=result.usage.get("total_tokens"),
                    )

                return result

            except Exception as e:
                record_error(type(e).__name__, f"agent.{self.name}")
                raise

    # Replace methods
    agent_class.run = instrumented_run
    agent_class.arun = instrumented_arun

    return agent_class


def instrument_tool(tool: Tool) -> Tool:
    """Instrument a tool with telemetry.

    Args:
        tool: Tool to instrument

    Returns:
        Instrumented tool
    """
    original_func = tool.func

    @functools.wraps(original_func)
    async def instrumented_func(*args, **kwargs):
        """Instrumented tool function."""
        with create_span(f"tool.{tool.name}.execute") as span:
            try:
                # Set tool attributes
                set_tool_attributes(
                    tool_name=tool.name, tool_type="function", parameters=kwargs
                )

                # Measure latency
                with LatencyTimer(f"tool.{tool.name}"):
                    # Execute original function
                    if asyncio.iscoroutinefunction(original_func):
                        result = await original_func(*args, **kwargs)
                    else:
                        result = original_func(*args, **kwargs)

                return result

            except Exception as e:
                record_error(type(e).__name__, f"tool.{tool.name}")
                raise

    # Create new tool with instrumented function

    instrumented_tool = Tool(
        name=tool.name,
        description=tool.description,
        func=instrumented_func,
        parameters=tool.parameters,
    )

    return instrumented_tool


def instrument_provider(provider_class: type[BaseProvider]) -> type[BaseProvider]:
    """Instrument a provider class with telemetry.

    Args:
        provider_class: Provider class to instrument

    Returns:
        Instrumented provider class
    """
    # Get provider name from class name
    provider_name = provider_class.__name__.replace("Provider", "").lower()

    # Check which methods exist before instrumenting
    if hasattr(provider_class, "complete"):
        # Save original method
        original_complete = provider_class.complete

        @functools.wraps(original_complete)
        def instrumented_complete(self, *args, **kwargs):
            """Instrumented complete method."""
            # Get provider name
            name = getattr(self, "name", provider_name)

            with create_span(f"llm.{name}.complete") as span:
                try:
                    # Set LLM attributes
                    model = kwargs.get("model", getattr(self, "model", "unknown"))
                    set_llm_attributes(
                        model=model,
                        provider=name,
                        temperature=kwargs.get("temperature"),
                        max_tokens=kwargs.get("max_tokens"),
                    )

                    # Measure latency
                    start_time = time.time()

                    # Execute original method
                    result = original_complete(self, *args, **kwargs)

                    # Record metrics
                    duration_ms = (time.time() - start_time) * 1000
                    record_latency(f"llm.{name}", duration_ms, model=model)

                    # Record token usage
                    if hasattr(result, "usage") and result.usage:
                        record_token_usage(
                            provider=name,
                            model=model,
                            prompt_tokens=result.usage.get("prompt_tokens", 0),
                            completion_tokens=result.usage.get("completion_tokens", 0),
                            total_tokens=result.usage.get("total_tokens"),
                        )

                        # Also set as span attributes
                        set_llm_attributes(
                            model=model,
                            provider=name,
                            prompt_tokens=result.usage.get("prompt_tokens"),
                            completion_tokens=result.usage.get("completion_tokens"),
                            total_tokens=result.usage.get("total_tokens"),
                        )

                    return result

                except Exception as e:
                    record_error(type(e).__name__, f"llm.{name}")
                    raise

        # Replace method
        provider_class.complete = instrumented_complete

    if hasattr(provider_class, "acomplete"):
        # Save original method
        original_acomplete = provider_class.acomplete

        @functools.wraps(original_acomplete)
        async def instrumented_acomplete(self, *args, **kwargs):
            """Instrumented async complete method."""
            # Get provider name
            name = getattr(self, "name", provider_name)

            with create_span(f"llm.{name}.acomplete") as span:
                try:
                    # Set LLM attributes
                    model = kwargs.get("model", getattr(self, "model", "unknown"))
                    set_llm_attributes(
                        model=model,
                        provider=name,
                        temperature=kwargs.get("temperature"),
                        max_tokens=kwargs.get("max_tokens"),
                    )

                    # Measure latency
                    start_time = time.time()

                    # Execute original method
                    result = await original_acomplete(self, *args, **kwargs)

                    # Record metrics
                    duration_ms = (time.time() - start_time) * 1000
                    record_latency(f"llm.{name}", duration_ms, model=model)

                    # Record token usage
                    if hasattr(result, "usage") and result.usage:
                        record_token_usage(
                            provider=name,
                            model=model,
                            prompt_tokens=result.usage.get("prompt_tokens", 0),
                            completion_tokens=result.usage.get("completion_tokens", 0),
                            total_tokens=result.usage.get("total_tokens"),
                        )

                        # Also set as span attributes
                        set_llm_attributes(
                            model=model,
                            provider=name,
                            prompt_tokens=result.usage.get("prompt_tokens"),
                            completion_tokens=result.usage.get("completion_tokens"),
                            total_tokens=result.usage.get("total_tokens"),
                        )

                    return result

                except Exception as e:
                    record_error(type(e).__name__, f"llm.{name}")
                    raise

        # Replace method
        provider_class.acomplete = instrumented_acomplete

    # Instrument streaming methods if they exist
    if hasattr(provider_class, "stream"):
        original_stream = provider_class.stream

        @functools.wraps(original_stream)
        def instrumented_stream(self, *args, **kwargs):
            """Instrumented stream method."""
            name = getattr(self, "name", provider_name)

            with create_span(f"llm.{name}.stream") as span:
                model = kwargs.get("model", getattr(self, "model", "unknown"))
                set_llm_attributes(
                    model=model,
                    provider=name,
                    temperature=kwargs.get("temperature"),
                    max_tokens=kwargs.get("max_tokens"),
                )

                # Return original generator
                return original_stream(self, *args, **kwargs)

        provider_class.stream = instrumented_stream

    if hasattr(provider_class, "astream"):
        original_astream = provider_class.astream

        @functools.wraps(original_astream)
        async def instrumented_astream(self, *args, **kwargs):
            """Instrumented async stream method."""
            name = getattr(self, "name", provider_name)

            with create_span(f"llm.{name}.astream") as span:
                model = kwargs.get("model", getattr(self, "model", "unknown"))
                set_llm_attributes(
                    model=model,
                    provider=name,
                    temperature=kwargs.get("temperature"),
                    max_tokens=kwargs.get("max_tokens"),
                )

                # Return original async generator
                async for chunk in original_astream(self, *args, **kwargs):
                    yield chunk

        provider_class.astream = instrumented_astream

    return provider_class


def instrument_memory_operation(operation: str, memory_type: str) -> Callable[[F], F]:
    """Decorator to instrument memory operations.

    Args:
        operation: Operation type (get, set, delete, search)
        memory_type: Type of memory

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            with create_span(f"memory.{memory_type}.{operation}") as span:
                try:
                    # Extract key if available
                    key = args[0] if args else kwargs.get("key")

                    # Set memory attributes
                    set_memory_attributes(
                        operation=operation,
                        memory_type=memory_type,
                        key=str(key) if key else None,
                    )

                    # Measure latency
                    start_time = time.time()

                    # Execute operation
                    result = await func(self, *args, **kwargs)

                    # Determine if it was a hit (for get operations)
                    hit = result is not None if operation == "get" else None

                    # Record metrics
                    duration_ms = (time.time() - start_time) * 1000
                    record_latency(
                        f"memory.{memory_type}", duration_ms, operation=operation
                    )

                    # Record memory operation
                    size = len(str(result)) if result else 0
                    record_memory_operation(
                        operation=operation,
                        memory_type=memory_type,
                        hit=hit if hit is not None else True,
                        size_bytes=size,
                    )

                    return result

                except Exception as e:
                    record_error(type(e).__name__, f"memory.{memory_type}.{operation}")
                    raise

        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            with create_span(f"memory.{memory_type}.{operation}") as span:
                try:
                    # Extract key if available
                    key = args[0] if args else kwargs.get("key")

                    # Set memory attributes
                    set_memory_attributes(
                        operation=operation,
                        memory_type=memory_type,
                        key=str(key) if key else None,
                    )

                    # Measure latency
                    start_time = time.time()

                    # Execute operation
                    result = func(self, *args, **kwargs)

                    # Determine if it was a hit (for get operations)
                    hit = result is not None if operation == "get" else None

                    # Record metrics
                    duration_ms = (time.time() - start_time) * 1000
                    record_latency(
                        f"memory.{memory_type}", duration_ms, operation=operation
                    )

                    # Record memory operation
                    size = len(str(result)) if result else 0
                    record_memory_operation(
                        operation=operation,
                        memory_type=memory_type,
                        hit=hit if hit is not None else True,
                        size_bytes=size,
                    )

                    return result

                except Exception as e:
                    record_error(type(e).__name__, f"memory.{memory_type}.{operation}")
                    raise

        # Return appropriate wrapper

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Auto-instrumentation function


def auto_instrument() -> None:
    """Automatically instrument all AgentiCraft components.

    This function should be called once at startup to enable telemetry.
    """
    # Import components
    from ..core.agent import Agent
    from ..core.provider import BaseProvider

    # Import available providers (with error handling)
    providers_to_instrument = []

    try:
        from ..providers import OpenAIProvider

        providers_to_instrument.append(OpenAIProvider)
    except ImportError:
        pass

    try:
        from ..providers import AnthropicProvider

        providers_to_instrument.append(AnthropicProvider)
    except ImportError:
        pass

    try:
        from ..providers import OllamaProvider

        providers_to_instrument.append(OllamaProvider)
    except ImportError:
        pass

    # Import available agents
    agents_to_instrument = []

    try:
        from ..agents import ReasoningAgent

        agents_to_instrument.append(ReasoningAgent)
    except ImportError:
        pass

    try:
        from ..agents import WorkflowAgent

        agents_to_instrument.append(WorkflowAgent)
    except ImportError:
        pass

    # Instrument base classes
    instrument_agent(Agent)
    instrument_provider(BaseProvider)

    # Instrument specific providers
    for provider_class in providers_to_instrument:
        instrument_provider(provider_class)

    # Instrument specific agents
    for agent_class in agents_to_instrument:
        instrument_agent(agent_class)

    print("✅ AgentiCraft telemetry auto-instrumentation complete")


# Configuration helper


class TelemetryConfig:
    """Global telemetry configuration."""

    def __init__(
        self,
        enabled: bool = True,
        traces_enabled: bool = True,
        metrics_enabled: bool = True,
        exporter_type: str = "console",
        otlp_endpoint: str | None = None,
        service_name: str = "agenticraft",
        auto_instrument: bool = True,
    ):
        """Initialize telemetry configuration.

        Args:
            enabled: Whether telemetry is enabled
            traces_enabled: Whether traces are enabled
            metrics_enabled: Whether metrics are enabled
            exporter_type: Type of exporter (console, otlp, prometheus)
            otlp_endpoint: OTLP endpoint if using OTLP
            service_name: Service name for telemetry
            auto_instrument: Whether to auto-instrument components
        """
        self.enabled = enabled
        self.traces_enabled = traces_enabled
        self.metrics_enabled = metrics_enabled
        self.exporter_type = exporter_type
        self.otlp_endpoint = otlp_endpoint
        self.service_name = service_name
        self.auto_instrument = auto_instrument

    def initialize(self) -> None:
        """Initialize telemetry with this configuration."""
        if not self.enabled:
            print("ℹ️ Telemetry disabled")
            return

        # Initialize tracer
        if self.traces_enabled:
            from .tracer import TracerConfig, initialize_tracer

            tracer_config = TracerConfig(
                service_name=self.service_name,
                enabled=True,
                exporter_type=self.exporter_type,
                otlp_endpoint=self.otlp_endpoint,
            )
            initialize_tracer(tracer_config)
            print(f"✅ Tracer initialized with {self.exporter_type} exporter")

        # Initialize metrics
        if self.metrics_enabled:
            from .metrics import MetricsConfig, initialize_metrics

            metrics_config = MetricsConfig(
                service_name=self.service_name,
                enabled=True,
                exporter_type=self.exporter_type,
                otlp_endpoint=self.otlp_endpoint,
            )
            initialize_metrics(metrics_config)
            print(f"✅ Metrics initialized with {self.exporter_type} exporter")

        # Auto-instrument if requested
        if self.auto_instrument:
            auto_instrument()

    @classmethod
    def from_env(cls) -> "TelemetryConfig":
        """Create configuration from environment variables."""
        import os

        return cls(
            enabled=os.getenv("AGENTICRAFT_TELEMETRY_ENABLED", "true").lower()
            == "true",
            traces_enabled=os.getenv("AGENTICRAFT_TRACES_ENABLED", "true").lower()
            == "true",
            metrics_enabled=os.getenv("AGENTICRAFT_METRICS_ENABLED", "true").lower()
            == "true",
            exporter_type=os.getenv("AGENTICRAFT_EXPORTER_TYPE", "console"),
            otlp_endpoint=os.getenv("AGENTICRAFT_OTLP_ENDPOINT"),
            service_name=os.getenv("AGENTICRAFT_SERVICE_NAME", "agenticraft"),
            auto_instrument=os.getenv("AGENTICRAFT_AUTO_INSTRUMENT", "true").lower()
            == "true",
        )


# Import asyncio for instrumentation
