"""
Prometheus metrics exporter for AgentiCraft.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import time
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PrometheusMetric:
    """Represents a Prometheus metric."""
    name: str
    value: float
    metric_type: str  # counter, gauge, histogram, summary
    help_text: str
    labels: Dict[str, str] = field(default_factory=dict)


class PrometheusExporter:
    """Export AgentiCraft metrics in Prometheus format."""
    
    def __init__(self, namespace: str = "agenticraft"):
        """
        Initialize Prometheus exporter.
        
        Args:
            namespace: Metric namespace prefix
        """
        self.namespace = namespace
        self.metrics: Dict[str, PrometheusMetric] = {}
        self._metric_definitions = self._define_metrics()
        
    def _define_metrics(self) -> Dict[str, Dict[str, str]]:
        """Define standard AgentiCraft metrics."""
        return {
            # Workflow metrics
            "workflow_executions_total": {
                "type": "counter",
                "help": "Total number of workflow executions",
            },
            "workflow_execution_duration_seconds": {
                "type": "histogram",
                "help": "Workflow execution duration in seconds",
            },
            "workflow_errors_total": {
                "type": "counter",
                "help": "Total number of workflow errors",
            },
            "workflow_active_tasks": {
                "type": "gauge",
                "help": "Number of currently active workflow tasks",
            },
            
            # Agent metrics
            "agent_tasks_total": {
                "type": "counter",
                "help": "Total number of tasks processed by agents",
            },
            "agent_task_duration_seconds": {
                "type": "histogram",
                "help": "Agent task processing duration in seconds",
            },
            "agent_errors_total": {
                "type": "counter",
                "help": "Total number of agent errors",
            },
            "agent_health_score": {
                "type": "gauge",
                "help": "Agent health score (0-1)",
            },
            "agent_memory_usage_bytes": {
                "type": "gauge",
                "help": "Agent memory usage in bytes",
            },
            
            # System metrics
            "system_cpu_usage_percent": {
                "type": "gauge",
                "help": "System CPU usage percentage",
            },
            "system_memory_usage_percent": {
                "type": "gauge",
                "help": "System memory usage percentage",
            },
            "system_memory_available_bytes": {
                "type": "gauge",
                "help": "Available system memory in bytes",
            },
            "system_disk_usage_percent": {
                "type": "gauge",
                "help": "System disk usage percentage",
            },
            "system_uptime_seconds": {
                "type": "counter",
                "help": "System uptime in seconds",
            },
            
            # Application metrics
            "app_http_requests_total": {
                "type": "counter",
                "help": "Total number of HTTP requests",
            },
            "app_http_request_duration_seconds": {
                "type": "histogram",
                "help": "HTTP request duration in seconds",
            },
            "app_active_connections": {
                "type": "gauge",
                "help": "Number of active connections",
            },
            
            # Custom metrics
            "llm_api_calls_total": {
                "type": "counter",
                "help": "Total number of LLM API calls",
            },
            "llm_api_tokens_total": {
                "type": "counter",
                "help": "Total number of tokens processed",
            },
            "llm_api_cost_dollars": {
                "type": "counter",
                "help": "Total LLM API cost in dollars",
            },
        }
        
    def register_metric(
        self,
        name: str,
        value: float,
        metric_type: str = "gauge",
        help_text: str = "",
        labels: Dict[str, str] = None
    ):
        """
        Register or update a metric.
        
        Args:
            name: Metric name (without namespace)
            value: Metric value
            metric_type: Type of metric (counter, gauge, histogram, summary)
            help_text: Help text for the metric
            labels: Optional labels for the metric
        """
        full_name = f"{self.namespace}_{name}"
        
        # Get help text from definitions if not provided
        if not help_text and name in self._metric_definitions:
            help_text = self._metric_definitions[name]["help"]
            
        metric = PrometheusMetric(
            name=full_name,
            value=value,
            metric_type=metric_type,
            help_text=help_text,
            labels=labels or {}
        )
        
        # Create unique key including labels
        metric_key = self._get_metric_key(full_name, labels)
        self.metrics[metric_key] = metric
        
    def _get_metric_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Generate unique key for metric including labels."""
        if not labels:
            return name
            
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
        
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment a counter metric."""
        full_name = f"{self.namespace}_{name}"
        metric_key = self._get_metric_key(full_name, labels)
        
        if metric_key in self.metrics:
            self.metrics[metric_key].value += value
        else:
            self.register_metric(name, value, "counter", labels=labels)
            
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric value."""
        self.register_metric(name, value, "gauge", labels=labels)
        
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """
        Observe a value for histogram metric.
        
        Note: This is a simplified implementation. A full implementation
        would maintain buckets and calculate quantiles.
        """
        # For simplicity, we'll track as a gauge with additional labels
        bucket_labels = (labels or {}).copy()
        
        # Add to sum metric
        sum_key = self._get_metric_key(f"{self.namespace}_{name}_sum", labels)
        if sum_key in self.metrics:
            self.metrics[sum_key].value += value
        else:
            self.register_metric(f"{name}_sum", value, "gauge", labels=labels)
            
        # Increment count metric
        count_key = self._get_metric_key(f"{self.namespace}_{name}_count", labels)
        if count_key in self.metrics:
            self.metrics[count_key].value += 1
        else:
            self.register_metric(f"{name}_count", 1, "gauge", labels=labels)
            
    def format_metrics(self) -> str:
        """
        Format metrics in Prometheus exposition format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        lines = []
        
        # Group metrics by name (without labels)
        metric_groups = {}
        for metric in self.metrics.values():
            base_name = metric.name.split("{")[0]
            if base_name not in metric_groups:
                metric_groups[base_name] = []
            metric_groups[base_name].append(metric)
            
        # Format each metric group
        for base_name, metrics in metric_groups.items():
            # Add HELP and TYPE comments only once per metric
            if metrics:
                first_metric = metrics[0]
                if first_metric.help_text:
                    lines.append(f"# HELP {base_name} {first_metric.help_text}")
                lines.append(f"# TYPE {base_name} {first_metric.metric_type}")
                
            # Add metric values
            for metric in metrics:
                if metric.labels:
                    label_str = ",".join(
                        f'{k}="{v}"' for k, v in sorted(metric.labels.items())
                    )
                    lines.append(f"{metric.name}{{{label_str}}} {metric.value}")
                else:
                    lines.append(f"{metric.name} {metric.value}")
                    
        return "\n".join(lines) + "\n"
        
    def export_metrics(self) -> bytes:
        """
        Export metrics in Prometheus format.
        
        Returns:
            UTF-8 encoded metrics
        """
        return self.format_metrics().encode("utf-8")
        
    def collect_workflow_metrics(self, workflow_name: str, metrics: Dict[str, Any]):
        """
        Collect metrics from a workflow.
        
        Args:
            workflow_name: Name of the workflow
            metrics: Dictionary of metrics from the workflow
        """
        labels = {"workflow": workflow_name}
        
        # Execution metrics
        if "total_executions" in metrics:
            self.set_gauge(
                "workflow_executions_total",
                metrics["total_executions"],
                labels
            )
            
        if "average_duration_ms" in metrics:
            self.observe_histogram(
                "workflow_execution_duration_seconds",
                metrics["average_duration_ms"] / 1000,
                labels
            )
            
        if "error_count" in metrics:
            self.set_gauge(
                "workflow_errors_total",
                metrics["error_count"],
                labels
            )
            
        if "active_tasks" in metrics:
            self.set_gauge(
                "workflow_active_tasks",
                metrics["active_tasks"],
                labels
            )
            
    def collect_agent_metrics(self, agent_name: str, metrics: Dict[str, Any]):
        """
        Collect metrics from an agent.
        
        Args:
            agent_name: Name of the agent
            metrics: Dictionary of metrics from the agent
        """
        labels = {"agent": agent_name}
        
        if "tasks_completed" in metrics:
            self.set_gauge(
                "agent_tasks_total",
                metrics["tasks_completed"],
                labels
            )
            
        if "average_response_time_ms" in metrics:
            self.observe_histogram(
                "agent_task_duration_seconds",
                metrics["average_response_time_ms"] / 1000,
                labels
            )
            
        if "tasks_failed" in metrics:
            self.set_gauge(
                "agent_errors_total",
                metrics["tasks_failed"],
                labels
            )
            
        if "health_score" in metrics:
            self.set_gauge(
                "agent_health_score",
                metrics["health_score"],
                labels
            )
            
        if "memory_usage_mb" in metrics:
            self.set_gauge(
                "agent_memory_usage_bytes",
                metrics["memory_usage_mb"] * 1024 * 1024,
                labels
            )
            
    def collect_system_metrics(self, metrics: Dict[str, Any]):
        """
        Collect system-wide metrics.
        
        Args:
            metrics: Dictionary of system metrics
        """
        if "cpu_percent" in metrics:
            self.set_gauge("system_cpu_usage_percent", metrics["cpu_percent"])
            
        if "memory_percent" in metrics:
            self.set_gauge("system_memory_usage_percent", metrics["memory_percent"])
            
        if "memory_available_mb" in metrics:
            self.set_gauge(
                "system_memory_available_bytes",
                metrics["memory_available_mb"] * 1024 * 1024
            )
            
        if "disk_usage_percent" in metrics:
            self.set_gauge("system_disk_usage_percent", metrics["disk_usage_percent"])
            
        if "uptime_seconds" in metrics:
            self.set_gauge("system_uptime_seconds", metrics["uptime_seconds"])
            
    def create_metrics_endpoint(self) -> Dict[str, Any]:
        """
        Create metrics endpoint response.
        
        Returns:
            Dictionary with status code and body
        """
        try:
            metrics_text = self.format_metrics()
            return {
                "status_code": 200,
                "headers": {"Content-Type": "text/plain; version=0.0.4"},
                "body": metrics_text,
            }
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return {
                "status_code": 500,
                "headers": {"Content-Type": "text/plain"},
                "body": f"# Error generating metrics: {str(e)}\n",
            }
            

# Example Grafana dashboard configuration
GRAFANA_DASHBOARD_CONFIG = {
    "dashboard": {
        "title": "AgentiCraft Monitoring",
        "panels": [
            {
                "title": "Workflow Execution Rate",
                "targets": [
                    {
                        "expr": "rate(agenticraft_workflow_executions_total[5m])",
                        "legendFormat": "{{workflow}}",
                    }
                ],
            },
            {
                "title": "Agent Task Duration",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(agenticraft_agent_task_duration_seconds_bucket[5m]))",
                        "legendFormat": "p95 - {{agent}}",
                    }
                ],
            },
            {
                "title": "System Resources",
                "targets": [
                    {
                        "expr": "agenticraft_system_cpu_usage_percent",
                        "legendFormat": "CPU %",
                    },
                    {
                        "expr": "agenticraft_system_memory_usage_percent",
                        "legendFormat": "Memory %",
                    },
                ],
            },
            {
                "title": "Error Rate",
                "targets": [
                    {
                        "expr": "rate(agenticraft_workflow_errors_total[5m]) / rate(agenticraft_workflow_executions_total[5m])",
                        "legendFormat": "{{workflow}}",
                    }
                ],
            },
        ],
    }
}
