"""Telemetry and observability for AgentiCraft.

This package provides comprehensive telemetry support including:
- OpenTelemetry integration for distributed tracing
- Metrics collection and export
- Automatic instrumentation
- Decorators for easy telemetry addition

Example:
    Basic telemetry setup::
    
        from agenticraft.telemetry import setup_telemetry, track_metrics
        
        # Initialize telemetry
        setup_telemetry(
            service_name="my-agent-app",
            export_endpoint="http://localhost:4317"
        )
        
        # Use decorators for automatic tracking
        @track_metrics(labels=["agent_name"])
        async def run_agent(agent_name: str):
            # Your code here
            pass
"""

from .config import (
    TelemetryConfig,
    ExportFormat,
    TelemetryEnvironment,
    ExporterConfig,
    ResourceConfig,
    SamplingConfig,
    InstrumentationConfig,
    development_config,
    production_config,
    test_config
)

from .tracer import (
    setup_tracing,
    get_tracer,
    shutdown_tracing,
    traced_operation,
    trace_function,
    add_event,
    set_attribute,
    get_current_trace_id,
    TracerManager
)

from .decorators import (
    track_metrics,
    trace,
    measure_time,
    count_calls,
    observe_value,
    trace_agent_method,
    trace_tool_execution
)

# Re-export from core for convenience
from ..core.telemetry import (
    Telemetry,
    set_global_telemetry,
    get_global_telemetry,
    init_telemetry
)

__all__ = [
    # Config
    "TelemetryConfig",
    "ExportFormat",
    "TelemetryEnvironment",
    "ExporterConfig",
    "ResourceConfig",
    "SamplingConfig",
    "InstrumentationConfig",
    "development_config",
    "production_config",
    "test_config",
    
    # Tracer
    "setup_tracing",
    "get_tracer",
    "shutdown_tracing",
    "traced_operation",
    "trace_function",
    "add_event",
    "set_attribute",
    "get_current_trace_id",
    "TracerManager",
    
    # Decorators
    "track_metrics",
    "trace",
    "measure_time",
    "count_calls",
    "observe_value",
    "trace_agent_method",
    "trace_tool_execution",
    
    # Core telemetry
    "Telemetry",
    "set_global_telemetry",
    "get_global_telemetry",
    "init_telemetry",
]


def setup_telemetry(
    service_name: str = "agenticraft",
    export_endpoint: str = "http://localhost:4317",
    environment: str = "development",
    **kwargs
) -> Telemetry:
    """Convenience function to set up both telemetry and tracing.
    
    Args:
        service_name: Name of your service
        export_endpoint: OTLP endpoint for telemetry export
        environment: Deployment environment
        **kwargs: Additional configuration options
        
    Returns:
        Configured Telemetry instance
        
    Example:
        telemetry = setup_telemetry(
            service_name="my-agent-service",
            export_endpoint="http://jaeger:4317",
            environment="production",
            sample_rate=0.1
        )
    """
    # Create config based on environment
    if environment == "development":
        config = development_config()
    elif environment == "production":
        config = production_config(
            service_name=service_name,
            otlp_endpoint=export_endpoint,
            sample_rate=kwargs.get("sample_rate", 0.1)
        )
    elif environment == "test":
        config = test_config()
    else:
        config = TelemetryConfig()
    
    # Update with provided values
    config.resource.service_name = service_name
    if export_endpoint:
        config.trace_exporter.endpoint = export_endpoint
        config.metric_exporter.endpoint = export_endpoint
    
    # Apply any additional kwargs
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    # Set up tracing
    setup_tracing(config)
    
    # Initialize and return telemetry
    return init_telemetry(
        service_name=service_name,
        export_to=export_endpoint,
        enabled=config.enabled
    )
