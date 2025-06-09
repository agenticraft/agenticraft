"""Prometheus exporter configuration.

This module provides configuration helpers for Prometheus exporters.
"""

import logging

from opentelemetry.exporter.prometheus import PrometheusMetricReader
from prometheus_client import REGISTRY, CollectorRegistry, start_http_server

logger = logging.getLogger(__name__)


class PrometheusExporter:
    """Prometheus exporter configuration and server management."""

    def __init__(
        self,
        port: int = 8000,
        addr: str = "0.0.0.0",
        namespace: str | None = None,
        registry: CollectorRegistry | None = None,
    ):
        """Initialize Prometheus exporter.

        Args:
            port: Port to expose metrics on
            addr: Address to bind to
            namespace: Metric namespace prefix
            registry: Custom collector registry
        """
        self.port = port
        self.addr = addr
        self.namespace = namespace
        self.registry = registry or REGISTRY
        self._server = None

    def create_metric_reader(self) -> PrometheusMetricReader:
        """Create Prometheus metric reader.

        Returns:
            Configured metric reader
        """
        return PrometheusMetricReader(port=self.port, namespace=self.namespace)

    def start_server(self) -> None:
        """Start Prometheus HTTP server.

        This starts a separate HTTP server to expose metrics.
        """
        if self._server is not None:
            logger.warning("Prometheus server already started")
            return

        try:
            start_http_server(port=self.port, addr=self.addr, registry=self.registry)
            logger.info(f"Prometheus metrics server started on {self.addr}:{self.port}")

            # Print example queries
            self._print_example_queries()

        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")
            raise

    def _print_example_queries(self) -> None:
        """Print example Prometheus queries."""
        base_url = (
            f"http://{self.addr if self.addr != '0.0.0.0' else 'localhost'}:{self.port}"
        )

        print("\n" + "=" * 60)
        print("Prometheus Metrics Available")
        print("=" * 60)
        print(f"Metrics endpoint: {base_url}/metrics")
        print("\nExample queries:")
        print("- Total tokens by provider:")
        print("  sum(agenticraft_tokens_total) by (provider)")
        print("- Error rate by operation:")
        print("  rate(agenticraft_errors_total[5m]) by (operation)")
        print("- P99 latency:")
        print("  agenticraft_latency_p99")
        print("- Memory hit rate:")
        print("  agenticraft_memory_hit_rate")
        print("=" * 60 + "\n")

    def get_metrics_url(self) -> str:
        """Get the URL where metrics are exposed.

        Returns:
            Metrics URL
        """
        host = self.addr if self.addr != "0.0.0.0" else "localhost"
        return f"http://{host}:{self.port}/metrics"

    @classmethod
    def with_defaults(cls) -> "PrometheusExporter":
        """Create Prometheus exporter with default settings.

        Returns:
            Configured exporter
        """
        return cls(port=8000, addr="0.0.0.0", namespace="agenticraft")


# Grafana dashboard configuration
GRAFANA_DASHBOARD_CONFIG = {
    "dashboard": {
        "title": "AgentiCraft Metrics",
        "panels": [
            {
                "title": "Token Usage by Provider",
                "targets": [
                    {
                        "expr": "sum(rate(agenticraft_tokens_total[5m])) by (provider, model)"
                    }
                ],
                "type": "graph",
            },
            {
                "title": "Request Latency (P50, P90, P99)",
                "targets": [
                    {
                        "expr": 'agenticraft_latency_p99{percentile="p50"}',
                        "legendFormat": "P50",
                    },
                    {
                        "expr": 'agenticraft_latency_p99{percentile="p90"}',
                        "legendFormat": "P90",
                    },
                    {
                        "expr": 'agenticraft_latency_p99{percentile="p99"}',
                        "legendFormat": "P99",
                    },
                ],
                "type": "graph",
            },
            {
                "title": "Error Rate",
                "targets": [
                    {
                        "expr": "sum(rate(agenticraft_errors_total[5m])) by (operation, error_type)"
                    }
                ],
                "type": "graph",
            },
            {
                "title": "Memory Hit Rate",
                "targets": [{"expr": "agenticraft_memory_hit_rate"}],
                "type": "gauge",
                "format": "percentunit",
            },
            {
                "title": "Active Traces",
                "targets": [{"expr": "sum(agenticraft_traces_active)"}],
                "type": "stat",
            },
            {
                "title": "Token Cost Estimate (USD)",
                "targets": [
                    {
                        "expr": """
                        sum(agenticraft_tokens_total{token_type="prompt"} * 0.00001) by (provider) +
                        sum(agenticraft_tokens_total{token_type="completion"} * 0.00003) by (provider)
                    """
                    }
                ],
                "type": "stat",
                "format": "currencyUSD",
            },
        ],
    }
}


def generate_grafana_dashboard() -> dict:
    """Generate Grafana dashboard configuration.

    Returns:
        Dashboard configuration dict
    """
    return GRAFANA_DASHBOARD_CONFIG


def save_grafana_dashboard(filepath: str = "agenticraft_dashboard.json") -> None:
    """Save Grafana dashboard configuration to file.

    Args:
        filepath: Path to save dashboard JSON
    """
    import json

    dashboard = generate_grafana_dashboard()

    with open(filepath, "w") as f:
        json.dump(dashboard, f, indent=2)

    print(f"Grafana dashboard saved to: {filepath}")
    print("Import this in Grafana to visualize AgentiCraft metrics")


# Convenience functions


def create_prometheus_reader(port: int = 8000, **kwargs) -> PrometheusMetricReader:
    """Create Prometheus metric reader with defaults.

    Args:
        port: Port to expose metrics
        **kwargs: Additional configuration

    Returns:
        Configured metric reader
    """
    exporter = PrometheusExporter(port=port, **kwargs)
    return exporter.create_metric_reader()
