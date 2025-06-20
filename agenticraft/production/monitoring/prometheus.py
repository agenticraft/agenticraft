"""
Prometheus metrics exporter for AgentiCraft.

This module provides comprehensive metrics collection and export
for monitoring AgentiCraft in production.
"""
import time
import psutil
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from collections import defaultdict
import logging

try:
    from prometheus_client import (
        Counter, Gauge, Histogram, Summary,
        CollectorRegistry, generate_latest,
        CONTENT_TYPE_LATEST, Info
    )
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    # Mock classes for when prometheus_client is not installed
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self
        
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self
        
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self
        def time(self): return self
        def __enter__(self): return self
        def __exit__(self, *args): pass
        
    class Summary:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self
        
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
        
    CollectorRegistry = object
    CONTENT_TYPE_LATEST = "text/plain"
    
    def generate_latest(registry=None):
        return b"# Prometheus client not installed"

logger = logging.getLogger(__name__)


class AgentMetrics:
    """Metrics for agent operations."""
    
    def __init__(self, registry=None):
        """Initialize agent metrics."""
        # Execution metrics
        self.executions_total = Counter(
            'agenticraft_agent_executions_total',
            'Total number of agent executions',
            ['agent_name', 'status'],
            registry=registry
        )
        
        self.execution_duration = Histogram(
            'agenticraft_agent_execution_duration_seconds',
            'Agent execution duration in seconds',
            ['agent_name'],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
            registry=registry
        )
        
        self.active_agents = Gauge(
            'agenticraft_active_agents',
            'Number of active agents',
            registry=registry
        )
        
        # Tool usage metrics
        self.tool_calls_total = Counter(
            'agenticraft_tool_calls_total',
            'Total number of tool calls',
            ['tool_name', 'agent_name', 'status'],
            registry=registry
        )
        
        self.tool_duration = Histogram(
            'agenticraft_tool_duration_seconds',
            'Tool execution duration in seconds',
            ['tool_name'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
            registry=registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'agenticraft_agent_errors_total',
            'Total number of agent errors',
            ['agent_name', 'error_type'],
            registry=registry
        )
        
        # Token usage
        self.tokens_used = Counter(
            'agenticraft_tokens_used_total',
            'Total tokens used by agents',
            ['agent_name', 'token_type'],  # token_type: input, output
            registry=registry
        )


class WorkflowMetrics:
    """Metrics for workflow operations."""
    
    def __init__(self, registry=None):
        """Initialize workflow metrics."""
        self.executions_total = Counter(
            'agenticraft_workflow_executions_total',
            'Total number of workflow executions',
            ['workflow_name', 'status'],
            registry=registry
        )
        
        self.execution_duration = Histogram(
            'agenticraft_workflow_execution_duration_seconds',
            'Workflow execution duration in seconds',
            ['workflow_name'],
            buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0),
            registry=registry
        )
        
        self.active_workflows = Gauge(
            'agenticraft_active_workflows',
            'Number of active workflows',
            registry=registry
        )
        
        self.steps_completed = Counter(
            'agenticraft_workflow_steps_completed_total',
            'Total workflow steps completed',
            ['workflow_name', 'step_name'],
            registry=registry
        )


class SecurityMetrics:
    """Metrics for security operations."""
    
    def __init__(self, registry=None):
        """Initialize security metrics."""
        # Authentication metrics
        self.auth_attempts = Counter(
            'agenticraft_auth_attempts_total',
            'Total authentication attempts',
            ['method', 'status'],
            registry=registry
        )
        
        self.auth_duration = Histogram(
            'agenticraft_auth_duration_seconds',
            'Authentication duration in seconds',
            ['method'],
            registry=registry
        )
        
        # Authorization metrics
        self.authz_checks = Counter(
            'agenticraft_authz_checks_total',
            'Total authorization checks',
            ['resource', 'action', 'result'],
            registry=registry
        )
        
        # Sandbox metrics
        self.sandbox_executions = Counter(
            'agenticraft_sandbox_executions_total',
            'Total sandbox executions',
            ['sandbox_type', 'status'],
            registry=registry
        )
        
        self.sandbox_violations = Counter(
            'agenticraft_sandbox_violations_total',
            'Sandbox security violations',
            ['sandbox_type', 'violation_type'],
            registry=registry
        )
        
        # Active sessions
        self.active_sessions = Gauge(
            'agenticraft_active_sessions',
            'Number of active user sessions',
            registry=registry
        )


class ProtocolMetrics:
    """Metrics for protocol operations."""
    
    def __init__(self, registry=None):
        """Initialize protocol metrics."""
        # A2A metrics
        self.a2a_messages_sent = Counter(
            'agenticraft_a2a_messages_sent_total',
            'Total A2A messages sent',
            ['protocol_type', 'message_type'],
            registry=registry
        )
        
        self.a2a_messages_received = Counter(
            'agenticraft_a2a_messages_received_total',
            'Total A2A messages received',
            ['protocol_type', 'message_type'],
            registry=registry
        )
        
        self.a2a_latency = Histogram(
            'agenticraft_a2a_latency_seconds',
            'A2A message latency',
            ['protocol_type'],
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
            registry=registry
        )
        
        # MCP metrics
        self.mcp_requests = Counter(
            'agenticraft_mcp_requests_total',
            'Total MCP requests',
            ['method', 'status'],
            registry=registry
        )
        
        self.mcp_request_duration = Histogram(
            'agenticraft_mcp_request_duration_seconds',
            'MCP request duration',
            ['method'],
            registry=registry
        )
        
        self.mcp_active_connections = Gauge(
            'agenticraft_mcp_active_connections',
            'Active MCP connections',
            ['transport_type'],
            registry=registry
        )


class SystemMetrics:
    """System-level metrics."""
    
    def __init__(self, registry=None):
        """Initialize system metrics."""
        # Resource usage
        self.cpu_usage = Gauge(
            'agenticraft_cpu_usage_percent',
            'CPU usage percentage',
            registry=registry
        )
        
        self.memory_usage = Gauge(
            'agenticraft_memory_usage_bytes',
            'Memory usage in bytes',
            registry=registry
        )
        
        self.memory_percent = Gauge(
            'agenticraft_memory_usage_percent',
            'Memory usage percentage',
            registry=registry
        )
        
        # Async event loop metrics
        self.event_loop_lag = Histogram(
            'agenticraft_event_loop_lag_seconds',
            'Event loop lag in seconds',
            buckets=(0.001, 0.01, 0.1, 1.0),
            registry=registry
        )
        
        self.active_tasks = Gauge(
            'agenticraft_active_tasks',
            'Number of active async tasks',
            registry=registry
        )
        
        # Thread pool metrics
        self.thread_pool_size = Gauge(
            'agenticraft_thread_pool_size',
            'Thread pool size',
            registry=registry
        )
        
        # Process info
        self.process_info = Info(
            'agenticraft_process',
            'Process information',
            registry=registry
        )


class PrometheusExporter:
    """Main Prometheus metrics exporter for AgentiCraft."""
    
    def __init__(self, registry=None):
        """Initialize metrics exporter."""
        if not HAS_PROMETHEUS:
            logger.warning(
                "prometheus_client not installed. Metrics will be disabled. "
                "Install with: pip install prometheus-client"
            )
            
        self.registry = registry or CollectorRegistry()
        
        # Initialize metric groups
        self.agent = AgentMetrics(self.registry)
        self.workflow = WorkflowMetrics(self.registry)
        self.security = SecurityMetrics(self.registry)
        self.protocol = ProtocolMetrics(self.registry)
        self.system = SystemMetrics(self.registry)
        
        # Custom metrics storage
        self._custom_metrics: Dict[str, Any] = {}
        
        # Start system metrics collection
        self._collection_task = None
        self._stop_collection = False
        
    async def start_collection(self, interval: float = 10.0):
        """Start periodic system metrics collection."""
        self._stop_collection = False
        self._collection_task = asyncio.create_task(
            self._collect_system_metrics(interval)
        )
        
    async def stop_collection(self):
        """Stop system metrics collection."""
        self._stop_collection = True
        if self._collection_task:
            await self._collection_task
            
    async def _collect_system_metrics(self, interval: float):
        """Periodically collect system metrics."""
        while not self._stop_collection:
            try:
                # CPU usage
                self.system.cpu_usage.set(psutil.cpu_percent())
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.system.memory_usage.set(memory.used)
                self.system.memory_percent.set(memory.percent)
                
                # Event loop metrics
                loop = asyncio.get_running_loop()
                tasks = asyncio.all_tasks(loop)
                self.system.active_tasks.set(len(tasks))
                
                # Process info
                process = psutil.Process()
                self.system.process_info.info({
                    'pid': str(process.pid),
                    'create_time': str(process.create_time()),
                    'num_threads': str(process.num_threads())
                })
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                
            await asyncio.sleep(interval)
            
    def track_agent_execution(self, agent_name: str):
        """Context manager for tracking agent execution."""
        class ExecutionTracker:
            def __init__(self, metrics, name):
                self.metrics = metrics
                self.name = name
                self.timer = None
                
            def __enter__(self):
                self.timer = self.metrics.agent.execution_duration.labels(
                    agent_name=self.name
                ).time()
                self.timer.__enter__()
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.timer.__exit__(exc_type, exc_val, exc_tb)
                
                # Update counters
                status = "error" if exc_type else "success"
                self.metrics.agent.executions_total.labels(
                    agent_name=self.name,
                    status=status
                ).inc()
                
                if exc_type:
                    self.metrics.agent.errors_total.labels(
                        agent_name=self.name,
                        error_type=exc_type.__name__
                    ).inc()
                    
        return ExecutionTracker(self, agent_name)
        
    def track_workflow_execution(self, workflow_name: str):
        """Context manager for tracking workflow execution."""
        class ExecutionTracker:
            def __init__(self, metrics, name):
                self.metrics = metrics
                self.name = name
                self.timer = None
                
            def __enter__(self):
                self.timer = self.metrics.workflow.execution_duration.labels(
                    workflow_name=self.name
                ).time()
                self.timer.__enter__()
                self.metrics.workflow.active_workflows.inc()
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.timer.__exit__(exc_type, exc_val, exc_tb)
                self.metrics.workflow.active_workflows.dec()
                
                status = "error" if exc_type else "success"
                self.metrics.workflow.executions_total.labels(
                    workflow_name=self.name,
                    status=status
                ).inc()
                
        return ExecutionTracker(self, workflow_name)
        
    def register_custom_metric(
        self,
        name: str,
        metric_type: str,
        description: str,
        labels: Optional[List[str]] = None,
        **kwargs
    ):
        """Register a custom metric."""
        if metric_type == "counter":
            metric = Counter(name, description, labels or [], registry=self.registry, **kwargs)
        elif metric_type == "gauge":
            metric = Gauge(name, description, labels or [], registry=self.registry, **kwargs)
        elif metric_type == "histogram":
            metric = Histogram(name, description, labels or [], registry=self.registry, **kwargs)
        elif metric_type == "summary":
            metric = Summary(name, description, labels or [], registry=self.registry, **kwargs)
        else:
            raise ValueError(f"Unknown metric type: {metric_type}")
            
        self._custom_metrics[name] = metric
        return metric
        
    def get_custom_metric(self, name: str):
        """Get a custom metric by name."""
        return self._custom_metrics.get(name)
        
    def generate_metrics(self) -> bytes:
        """Generate metrics in Prometheus format."""
        if not HAS_PROMETHEUS:
            return b"# Prometheus client not installed\n"
            
        return generate_latest(self.registry)
        
    @property
    def content_type(self) -> str:
        """Get content type for metrics response."""
        return CONTENT_TYPE_LATEST


# Global metrics instance
_metrics: Optional[PrometheusExporter] = None


def get_metrics() -> PrometheusExporter:
    """Get global metrics instance."""
    global _metrics
    
    if _metrics is None:
        _metrics = PrometheusExporter()
        
    return _metrics


def init_metrics(registry=None) -> PrometheusExporter:
    """Initialize global metrics."""
    global _metrics
    
    _metrics = PrometheusExporter(registry)
    
    return _metrics
