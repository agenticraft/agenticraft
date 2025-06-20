"""
Metrics collectors for AgentiCraft components.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Metric:
    """A metric with historical data."""
    name: str
    metric_type: MetricType
    description: str
    data_points: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    def add_point(self, value: float, labels: Dict[str, str] = None):
        """Add a data point to the metric."""
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        self.data_points.append(point)
        
    def get_latest(self) -> Optional[MetricPoint]:
        """Get the most recent data point."""
        return self.data_points[-1] if self.data_points else None
        
    def get_points_since(self, since: datetime) -> List[MetricPoint]:
        """Get all points since a given timestamp."""
        return [p for p in self.data_points if p.timestamp >= since]


class BaseMetricsCollector:
    """Base class for metrics collectors."""
    
    def __init__(self, collection_interval: int = 60):
        """
        Initialize metrics collector.
        
        Args:
            collection_interval: Interval in seconds between collections
        """
        self.collection_interval = collection_interval
        self.metrics: Dict[str, Metric] = {}
        self._running = False
        self._collection_task = None
        
    def register_metric(self, name: str, metric_type: MetricType, description: str):
        """Register a new metric."""
        if name not in self.metrics:
            self.metrics[name] = Metric(name, metric_type, description)
            
    def record_value(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a metric value."""
        if name in self.metrics:
            self.metrics[name].add_point(value, labels)
        else:
            logger.warning(f"Metric '{name}' not registered")
            
    async def collect(self):
        """Collect metrics (to be implemented by subclasses)."""
        raise NotImplementedError
        
    async def start_collection(self):
        """Start automatic metric collection."""
        if self._running:
            return
            
        self._running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info(f"Started {self.__class__.__name__} collection")
        
    async def stop_collection(self):
        """Stop automatic metric collection."""
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        logger.info(f"Stopped {self.__class__.__name__} collection")
        
    async def _collection_loop(self):
        """Main collection loop."""
        while self._running:
            try:
                await self.collect()
            except Exception as e:
                logger.error(f"Collection error in {self.__class__.__name__}: {e}")
                
            await asyncio.sleep(self.collection_interval)
            
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all collected metrics."""
        summary = {}
        
        for name, metric in self.metrics.items():
            latest = metric.get_latest()
            if latest:
                summary[name] = {
                    "value": latest.value,
                    "timestamp": latest.timestamp.isoformat(),
                    "type": metric.metric_type.value,
                }
                
        return summary


class WorkflowMetrics(BaseMetricsCollector):
    """Collect metrics for workflows."""
    
    def __init__(self, workflow_name: str):
        """
        Initialize workflow metrics collector.
        
        Args:
            workflow_name: Name of the workflow to monitor
        """
        super().__init__()
        self.workflow_name = workflow_name
        self._register_workflow_metrics()
        
        # Internal counters
        self._execution_count = 0
        self._error_count = 0
        self._active_tasks = 0
        self._execution_times = deque(maxlen=100)
        
    def _register_workflow_metrics(self):
        """Register workflow-specific metrics."""
        self.register_metric("executions_total", MetricType.COUNTER, "Total workflow executions")
        self.register_metric("errors_total", MetricType.COUNTER, "Total workflow errors")
        self.register_metric("active_tasks", MetricType.GAUGE, "Currently active tasks")
        self.register_metric("execution_duration_ms", MetricType.HISTOGRAM, "Execution duration in milliseconds")
        self.register_metric("success_rate", MetricType.GAUGE, "Success rate (0-1)")
        self.register_metric("throughput_per_minute", MetricType.GAUGE, "Executions per minute")
        
    def record_execution_start(self):
        """Record the start of a workflow execution."""
        self._active_tasks += 1
        self.record_value("active_tasks", self._active_tasks)
        return time.time()
        
    def record_execution_end(self, start_time: float, success: bool = True):
        """Record the end of a workflow execution."""
        duration_ms = (time.time() - start_time) * 1000
        
        self._active_tasks = max(0, self._active_tasks - 1)
        self._execution_count += 1
        
        if not success:
            self._error_count += 1
            
        self._execution_times.append((datetime.now(), duration_ms))
        
        # Record metrics
        self.record_value("executions_total", self._execution_count)
        self.record_value("errors_total", self._error_count)
        self.record_value("active_tasks", self._active_tasks)
        self.record_value("execution_duration_ms", duration_ms)
        
        # Calculate derived metrics
        success_rate = (self._execution_count - self._error_count) / self._execution_count if self._execution_count > 0 else 0
        self.record_value("success_rate", success_rate)
        
    async def collect(self):
        """Collect workflow metrics."""
        # Calculate throughput
        now = datetime.now()
        recent_executions = [
            t for t, _ in self._execution_times 
            if t > now - timedelta(minutes=1)
        ]
        throughput = len(recent_executions)
        self.record_value("throughput_per_minute", throughput)
        
    def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed workflow metrics."""
        avg_duration = (
            sum(d for _, d in self._execution_times) / len(self._execution_times)
            if self._execution_times else 0
        )
        
        return {
            "workflow_name": self.workflow_name,
            "total_executions": self._execution_count,
            "error_count": self._error_count,
            "success_rate": (self._execution_count - self._error_count) / self._execution_count if self._execution_count > 0 else 0,
            "active_tasks": self._active_tasks,
            "average_duration_ms": avg_duration,
            "metrics": self.get_metrics_summary(),
        }


class AgentMetrics(BaseMetricsCollector):
    """Collect metrics for individual agents."""
    
    def __init__(self, agent_name: str, agent_type: str):
        """
        Initialize agent metrics collector.
        
        Args:
            agent_name: Name of the agent
            agent_type: Type of the agent
        """
        super().__init__(collection_interval=30)
        self.agent_name = agent_name
        self.agent_type = agent_type
        self._register_agent_metrics()
        
        # Internal counters
        self._task_count = 0
        self._error_count = 0
        self._response_times = deque(maxlen=100)
        
    def _register_agent_metrics(self):
        """Register agent-specific metrics."""
        self.register_metric("tasks_total", MetricType.COUNTER, "Total tasks processed")
        self.register_metric("errors_total", MetricType.COUNTER, "Total task errors")
        self.register_metric("response_time_ms", MetricType.HISTOGRAM, "Task response time in milliseconds")
        self.register_metric("health_score", MetricType.GAUGE, "Agent health score (0-1)")
        self.register_metric("queue_length", MetricType.GAUGE, "Task queue length")
        
    def record_task_start(self) -> float:
        """Record the start of a task."""
        return time.time()
        
    def record_task_end(self, start_time: float, success: bool = True):
        """Record the end of a task."""
        duration_ms = (time.time() - start_time) * 1000
        
        self._task_count += 1
        if not success:
            self._error_count += 1
            
        self._response_times.append(duration_ms)
        
        # Record metrics
        self.record_value("tasks_total", self._task_count)
        self.record_value("errors_total", self._error_count)
        self.record_value("response_time_ms", duration_ms)
        
    def update_health_score(self, score: float):
        """Update agent health score."""
        self.record_value("health_score", max(0, min(1, score)))
        
    def update_queue_length(self, length: int):
        """Update task queue length."""
        self.record_value("queue_length", length)
        
    async def collect(self):
        """Collect agent metrics."""
        # This is where you could collect runtime metrics
        # For now, we'll just ensure metrics are up to date
        pass
        
    def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed agent metrics."""
        avg_response_time = (
            sum(self._response_times) / len(self._response_times)
            if self._response_times else 0
        )
        
        health_metric = self.metrics.get("health_score")
        health_score = health_metric.get_latest().value if health_metric and health_metric.get_latest() else 1.0
        
        return {
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "tasks_completed": self._task_count,
            "tasks_failed": self._error_count,
            "success_rate": (self._task_count - self._error_count) / self._task_count if self._task_count > 0 else 0,
            "average_response_time_ms": avg_response_time,
            "health_score": health_score,
            "metrics": self.get_metrics_summary(),
        }


class SystemMetrics(BaseMetricsCollector):
    """Collect system-wide metrics."""
    
    def __init__(self):
        """Initialize system metrics collector."""
        super().__init__()
        self._register_system_metrics()
        self.start_time = datetime.now()
        
    def _register_system_metrics(self):
        """Register system metrics."""
        self.register_metric("cpu_percent", MetricType.GAUGE, "CPU usage percentage")
        self.register_metric("memory_percent", MetricType.GAUGE, "Memory usage percentage")
        self.register_metric("memory_available_mb", MetricType.GAUGE, "Available memory in MB")
        self.register_metric("disk_usage_percent", MetricType.GAUGE, "Disk usage percentage")
        self.register_metric("network_bytes_sent", MetricType.COUNTER, "Network bytes sent")
        self.register_metric("network_bytes_recv", MetricType.COUNTER, "Network bytes received")
        self.register_metric("uptime_seconds", MetricType.COUNTER, "System uptime in seconds")
        
    async def collect(self):
        """Collect system metrics."""
        try:
            import psutil
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_value("cpu_percent", cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.record_value("memory_percent", memory.percent)
            self.record_value("memory_available_mb", memory.available / 1024 / 1024)
            
            # Disk metrics
            disk = psutil.disk_usage("/")
            self.record_value("disk_usage_percent", disk.percent)
            
            # Network metrics
            net_io = psutil.net_io_counters()
            self.record_value("network_bytes_sent", net_io.bytes_sent)
            self.record_value("network_bytes_recv", net_io.bytes_recv)
            
            # Uptime
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()
            self.record_value("uptime_seconds", uptime_seconds)
            
        except ImportError:
            logger.warning("psutil not available, system metrics collection disabled")
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")


class MetricsCollector:
    """Central metrics collector that aggregates all metrics."""
    
    def __init__(self):
        """Initialize the metrics collector."""
        self.workflow_collectors: Dict[str, WorkflowMetrics] = {}
        self.agent_collectors: Dict[str, AgentMetrics] = {}
        self.system_collector = SystemMetrics()
        self._custom_collectors: Dict[str, BaseMetricsCollector] = {}
        
    def register_workflow(self, workflow_name: str) -> WorkflowMetrics:
        """Register a workflow for metrics collection."""
        if workflow_name not in self.workflow_collectors:
            collector = WorkflowMetrics(workflow_name)
            self.workflow_collectors[workflow_name] = collector
            return collector
        return self.workflow_collectors[workflow_name]
        
    def register_agent(self, agent_name: str, agent_type: str) -> AgentMetrics:
        """Register an agent for metrics collection."""
        if agent_name not in self.agent_collectors:
            collector = AgentMetrics(agent_name, agent_type)
            self.agent_collectors[agent_name] = collector
            return collector
        return self.agent_collectors[agent_name]
        
    def register_custom_collector(self, name: str, collector: BaseMetricsCollector):
        """Register a custom metrics collector."""
        self._custom_collectors[name] = collector
        
    async def start_all_collectors(self):
        """Start all registered collectors."""
        # Start system collector
        await self.system_collector.start_collection()
        
        # Start workflow collectors
        for collector in self.workflow_collectors.values():
            await collector.start_collection()
            
        # Start agent collectors
        for collector in self.agent_collectors.values():
            await collector.start_collection()
            
        # Start custom collectors
        for collector in self._custom_collectors.values():
            await collector.start_collection()
            
        logger.info("Started all metrics collectors")
        
    async def stop_all_collectors(self):
        """Stop all collectors."""
        # Stop all collectors
        all_collectors = (
            [self.system_collector] +
            list(self.workflow_collectors.values()) +
            list(self.agent_collectors.values()) +
            list(self._custom_collectors.values())
        )
        
        for collector in all_collectors:
            await collector.stop_collection()
            
        logger.info("Stopped all metrics collectors")
        
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return {
            "system": self.system_collector.get_metrics_summary(),
            "workflows": {
                name: collector.get_detailed_metrics()
                for name, collector in self.workflow_collectors.items()
            },
            "agents": {
                name: collector.get_detailed_metrics()
                for name, collector in self.agent_collectors.items()
            },
            "custom": {
                name: collector.get_metrics_summary()
                for name, collector in self._custom_collectors.items()
            },
            "timestamp": datetime.now().isoformat(),
        }
        
    def export_to_prometheus(self, exporter) -> None:
        """
        Export all metrics to a Prometheus exporter.
        
        Args:
            exporter: PrometheusExporter instance
        """
        # Export system metrics
        system_metrics = self.system_collector.get_metrics_summary()
        for name, data in system_metrics.items():
            if "value" in data:
                exporter.set_gauge(f"system_{name}", data["value"])
                
        # Export workflow metrics
        for workflow_name, collector in self.workflow_collectors.items():
            metrics = collector.get_detailed_metrics()
            exporter.collect_workflow_metrics(workflow_name, metrics)
            
        # Export agent metrics
        for agent_name, collector in self.agent_collectors.items():
            metrics = collector.get_detailed_metrics()
            exporter.collect_agent_metrics(agent_name, metrics)


# Context manager for metric timing
class MetricTimer:
    """Context manager for timing operations."""
    
    def __init__(self, collector: BaseMetricsCollector, metric_name: str, labels: Dict[str, str] = None):
        """
        Initialize metric timer.
        
        Args:
            collector: Metrics collector to record to
            metric_name: Name of the metric
            labels: Optional labels for the metric
        """
        self.collector = collector
        self.metric_name = metric_name
        self.labels = labels
        self.start_time = None
        
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and record metric."""
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.collector.record_value(self.metric_name, duration_ms, self.labels)
