"""Enhanced observability for production deployments.

This module provides observability features for monitoring AgentiCraft
workflows in production, extracted and simplified from Agentic Framework.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class TraceStatus(Enum):
    """Trace span status."""
    OK = "ok"
    ERROR = "error"


@dataclass
class TraceSpan:
    """Represents a trace span."""
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    span_id: str = field(default_factory=lambda: str(uuid4()))
    operation_name: str = ""
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: TraceStatus = TraceStatus.OK
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Get duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None


@dataclass
class Metric:
    """Represents a metric."""
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class EnhancedObservability:
    """Enhanced observability for production AgentiCraft deployments.
    
    This class provides distributed tracing, metrics collection,
    and performance monitoring for workflows and agents.
    
    Args:
        service_name: Name of the service
        export_interval: How often to export metrics (seconds)
        max_traces: Maximum traces to keep in memory
    """
    
    def __init__(
        self,
        service_name: str = "agenticraft",
        export_interval: int = 60,
        max_traces: int = 1000
    ):
        self.service_name = service_name
        self.export_interval = export_interval
        
        # Storage
        self.traces: deque = deque(maxlen=max_traces)
        self.active_spans: Dict[str, TraceSpan] = {}
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        
        # Metric aggregations
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        
        # Export task
        self._export_task: Optional[asyncio.Task] = None
        
        logger.info(f"Initialized EnhancedObservability for service '{service_name}'")
    
    async def start(self):
        """Start the observability system."""
        self._export_task = asyncio.create_task(self._export_loop())
        logger.info("Started observability export loop")
    
    async def stop(self):
        """Stop the observability system."""
        if self._export_task:
            self._export_task.cancel()
            try:
                await self._export_task
            except asyncio.CancelledError:
                pass
        
        # Export final metrics
        await self._export_metrics()
    
    def start_trace(
        self,
        operation_name: str,
        trace_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> TraceSpan:
        """Start a new trace span.
        
        Args:
            operation_name: Name of the operation
            trace_id: Optional trace ID (generates if not provided)
            attributes: Optional span attributes
            
        Returns:
            Created trace span
        """
        span = TraceSpan(
            trace_id=trace_id or str(uuid4()),
            operation_name=operation_name,
            attributes=attributes or {}
        )
        
        self.active_spans[span.span_id] = span
        self.traces.append(span)
        
        logger.debug(f"Started trace span: {operation_name} ({span.span_id})")
        return span
    
    def end_trace(
        self,
        span: TraceSpan,
        status: TraceStatus = TraceStatus.OK,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """End a trace span.
        
        Args:
            span: Span to end
            status: Final status
            attributes: Additional attributes
        """
        span.end_time = datetime.utcnow()
        span.status = status
        
        if attributes:
            span.attributes.update(attributes)
        
        # Remove from active
        self.active_spans.pop(span.span_id, None)
        
        # Record duration metric
        if span.duration_ms:
            self.record_histogram(
                f"span_duration_{span.operation_name}",
                span.duration_ms,
                {"status": status.value}
            )
        
        logger.debug(
            f"Ended trace span: {span.operation_name} "
            f"({span.span_id}) - {span.duration_ms:.2f}ms"
        )
    
    def record_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record a counter metric.
        
        Args:
            name: Metric name
            value: Value to add (default: 1)
            labels: Optional labels
        """
        key = self._metric_key(name, labels)
        self.counters[key] += value
        
        # Store raw metric
        metric = Metric(
            name=name,
            type=MetricType.COUNTER,
            value=value,
            labels=labels or {}
        )
        self.metrics[name].append(metric)
    
    def record_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record a gauge metric.
        
        Args:
            name: Metric name
            value: Current value
            labels: Optional labels
        """
        key = self._metric_key(name, labels)
        self.gauges[key] = value
        
        # Store raw metric
        metric = Metric(
            name=name,
            type=MetricType.GAUGE,
            value=value,
            labels=labels or {}
        )
        self.metrics[name].append(metric)
    
    def record_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record a histogram metric.
        
        Args:
            name: Metric name
            value: Value to record
            labels: Optional labels
        """
        key = self._metric_key(name, labels)
        self.histograms[key].append(value)
        
        # Store raw metric
        metric = Metric(
            name=name,
            type=MetricType.HISTOGRAM,
            value=value,
            labels=labels or {}
        )
        self.metrics[name].append(metric)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics.
        
        Returns:
            Metrics summary
        """
        summary = {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {}
        }
        
        # Calculate histogram statistics
        for key, values in self.histograms.items():
            if values:
                summary["histograms"][key] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "p50": self._percentile(values, 50),
                    "p95": self._percentile(values, 95),
                    "p99": self._percentile(values, 99)
                }
        
        return summary
    
    def get_traces(
        self,
        operation_name: Optional[str] = None,
        min_duration_ms: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent traces.
        
        Args:
            operation_name: Filter by operation
            min_duration_ms: Minimum duration filter
            limit: Maximum traces to return
            
        Returns:
            List of trace data
        """
        traces = []
        
        for span in reversed(self.traces):
            # Apply filters
            if operation_name and span.operation_name != operation_name:
                continue
            
            if min_duration_ms and (not span.duration_ms or span.duration_ms < min_duration_ms):
                continue
            
            traces.append({
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "operation": span.operation_name,
                "start_time": span.start_time.isoformat(),
                "duration_ms": span.duration_ms,
                "status": span.status.value,
                "attributes": span.attributes
            })
            
            if len(traces) >= limit:
                break
        
        return traces
    
    def create_dashboard(self) -> Dict[str, Any]:
        """Generate a monitoring dashboard.
        
        Returns:
            Dashboard data
        """
        # Calculate key metrics
        total_requests = self.counters.get("requests_total", 0)
        error_requests = self.counters.get("requests_error", 0)
        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Get recent trace statistics
        recent_traces = [
            s for s in self.traces
            if s.start_time >= datetime.utcnow() - timedelta(minutes=5)
        ]
        
        avg_duration = 0
        if recent_traces:
            durations = [s.duration_ms for s in recent_traces if s.duration_ms]
            avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Active operations
        active_operations = [
            {
                "operation": span.operation_name,
                "duration_so_far": (datetime.utcnow() - span.start_time).total_seconds(),
                "span_id": span.span_id
            }
            for span in self.active_spans.values()
        ]
        
        return {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "health_score": self._calculate_health_score(error_rate, avg_duration),
            "metrics": {
                "total_requests": total_requests,
                "error_rate": f"{error_rate:.2f}%",
                "avg_response_time_ms": f"{avg_duration:.2f}",
                "active_operations": len(active_operations)
            },
            "active_operations": active_operations[:10],  # Top 10
            "recent_errors": self._get_recent_errors(),
            "performance": self._get_performance_stats()
        }
    
    def _metric_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Generate metric key from name and labels."""
        if not labels:
            return name
        
        label_str = json.dumps(labels, sort_keys=True)
        return f"{name}:{label_str}"
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _calculate_health_score(self, error_rate: float, avg_duration: float) -> float:
        """Calculate health score (0-100)."""
        score = 100.0
        
        # Deduct for errors
        score -= min(error_rate * 2, 50)
        
        # Deduct for slow response
        if avg_duration > 1000:  # Over 1 second
            score -= min((avg_duration - 1000) / 100, 30)
        
        return max(0, score)
    
    def _get_recent_errors(self) -> List[Dict[str, Any]]:
        """Get recent error traces."""
        errors = []
        
        for span in reversed(self.traces):
            if span.status == TraceStatus.ERROR:
                errors.append({
                    "operation": span.operation_name,
                    "timestamp": span.start_time.isoformat(),
                    "duration_ms": span.duration_ms,
                    "attributes": span.attributes
                })
                
                if len(errors) >= 5:
                    break
        
        return errors
    
    def _get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {}
        
        # Get stats for each operation
        operations = defaultdict(list)
        for span in self.traces:
            if span.duration_ms:
                operations[span.operation_name].append(span.duration_ms)
        
        for op_name, durations in operations.items():
            if durations:
                stats[op_name] = {
                    "count": len(durations),
                    "avg_ms": sum(durations) / len(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations)
                }
        
        return stats
    
    async def _export_loop(self):
        """Background loop to export metrics."""
        while True:
            try:
                await asyncio.sleep(self.export_interval)
                await self._export_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in export loop: {e}")
    
    async def _export_metrics(self):
        """Export metrics to external system."""
        # In production, this would send to Prometheus, DataDog, etc.
        summary = self.get_metrics_summary()
        logger.debug(f"Exporting metrics: {summary}")
        
        # Clear histogram data after export
        self.histograms.clear()
        
        # Trim old metrics
        cutoff = datetime.utcnow() - timedelta(hours=1)
        for name in list(self.metrics.keys()):
            self.metrics[name] = [
                m for m in self.metrics[name]
                if m.timestamp >= cutoff
            ]


# Context manager for tracing
class Trace:
    """Context manager for easy tracing.
    
    Example:
        ```python
        observability = EnhancedObservability()
        
        async with Trace(observability, "database_query") as span:
            # Do work
            result = await db.query("SELECT * FROM users")
            span.attributes["row_count"] = len(result)
        ```
    """
    
    def __init__(
        self,
        observability: EnhancedObservability,
        operation_name: str,
        **attributes
    ):
        self.observability = observability
        self.operation_name = operation_name
        self.attributes = attributes
        self.span: Optional[TraceSpan] = None
        self.error_occurred = False
    
    async def __aenter__(self) -> TraceSpan:
        """Start the trace."""
        self.span = self.observability.start_trace(
            self.operation_name,
            attributes=self.attributes
        )
        return self.span
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End the trace."""
        if self.span:
            status = TraceStatus.ERROR if exc_type else TraceStatus.OK
            
            # Add error details if present
            if exc_type:
                self.span.attributes["error"] = str(exc_val)
                self.span.attributes["error_type"] = exc_type.__name__
            
            self.observability.end_trace(self.span, status)


# Decorator for automatic tracing
def trace_operation(
    observability: EnhancedObservability,
    operation_name: Optional[str] = None
):
    """Decorator to automatically trace operations.
    
    Args:
        observability: Observability instance
        operation_name: Optional operation name (uses function name if not provided)
        
    Example:
        ```python
        observability = EnhancedObservability()
        
        @trace_operation(observability)
        async def process_request(request):
            # Function is automatically traced
            return await handle(request)
        ```
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            
            async with Trace(observability, op_name) as span:
                # Add function details
                span.attributes["function"] = func.__name__
                span.attributes["module"] = func.__module__
                
                # Execute function
                result = await func(*args, **kwargs)
                
                return result
        
        return wrapper
    return decorator
