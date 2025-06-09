"""Console exporter for development and debugging.

This exporter prints telemetry data to the console in a human-readable format.
"""

import json
from datetime import datetime
from typing import Any

from opentelemetry.sdk.metrics.export import MetricsData
from opentelemetry.sdk.trace import ReadableSpan


class ConsoleExporter:
    """Console exporter for traces and metrics."""

    def __init__(self, pretty_print: bool = True, include_timestamps: bool = True):
        """Initialize console exporter.

        Args:
            pretty_print: Whether to pretty-print JSON output
            include_timestamps: Whether to include timestamps
        """
        self.pretty_print = pretty_print
        self.include_timestamps = include_timestamps

    def export_spans(self, spans: list[ReadableSpan]) -> None:
        """Export spans to console.

        Args:
            spans: List of spans to export
        """
        print("\n" + "=" * 60)
        print("TRACES")
        print("=" * 60)

        for span in spans:
            self._print_span(span)

    def export_metrics(self, metrics_data: MetricsData) -> None:
        """Export metrics to console.

        Args:
            metrics_data: Metrics data to export
        """
        print("\n" + "=" * 60)
        print("METRICS")
        print("=" * 60)

        for resource_metric in metrics_data.resource_metrics:
            for scope_metric in resource_metric.scope_metrics:
                for metric in scope_metric.metrics:
                    self._print_metric(metric)

    def _print_span(self, span: ReadableSpan) -> None:
        """Print a single span."""
        # Build span data
        span_data = {
            "name": span.name,
            "trace_id": format(span.get_span_context().trace_id, "032x"),
            "span_id": format(span.get_span_context().span_id, "016x"),
            "parent_id": format(span.parent.span_id, "016x") if span.parent else None,
            "start_time": self._format_time(span.start_time),
            "end_time": self._format_time(span.end_time),
            "duration_ms": (
                (span.end_time - span.start_time) / 1_000_000 if span.end_time else None
            ),
            "status": {
                "code": span.status.status_code.name,
                "description": span.status.description,
            },
            "attributes": dict(span.attributes or {}),
            "events": (
                [
                    {
                        "name": event.name,
                        "timestamp": self._format_time(event.timestamp),
                        "attributes": dict(event.attributes or {}),
                    }
                    for event in span.events
                ]
                if span.events
                else []
            ),
            "links": (
                [
                    {
                        "trace_id": format(link.context.trace_id, "032x"),
                        "span_id": format(link.context.span_id, "016x"),
                        "attributes": dict(link.attributes or {}),
                    }
                    for link in span.links
                ]
                if span.links
                else []
            ),
        }

        # Remove empty fields
        span_data = {k: v for k, v in span_data.items() if v}

        # Print
        if self.pretty_print:
            print(json.dumps(span_data, indent=2))
        else:
            print(json.dumps(span_data))
        print("-" * 60)

    def _print_metric(self, metric: Any) -> None:
        """Print a single metric."""
        metric_data = {
            "name": metric.name,
            "description": metric.description,
            "unit": metric.unit,
            "type": metric.__class__.__name__,
            "data": [],
        }

        # Extract data points based on metric type
        if hasattr(metric, "data"):
            if hasattr(metric.data, "data_points"):
                for point in metric.data.data_points:
                    point_data = {
                        "attributes": dict(point.attributes or {}),
                        "time": self._format_time(point.time_unix_nano),
                    }

                    # Add value based on type
                    if hasattr(point, "value"):
                        point_data["value"] = point.value
                    elif hasattr(point, "sum"):
                        point_data["sum"] = point.sum
                    elif hasattr(point, "count"):
                        point_data["count"] = point.count
                        if hasattr(point, "sum"):
                            point_data["mean"] = (
                                point.sum / point.count if point.count > 0 else 0
                            )

                    metric_data["data"].append(point_data)

        # Print
        if self.pretty_print:
            print(json.dumps(metric_data, indent=2))
        else:
            print(json.dumps(metric_data))
        print("-" * 60)

    def _format_time(self, timestamp_ns: int) -> str:
        """Format nanosecond timestamp to ISO format."""
        if not timestamp_ns:
            return ""

        if self.include_timestamps:
            # Convert nanoseconds to seconds
            timestamp_s = timestamp_ns / 1_000_000_000
            dt = datetime.fromtimestamp(timestamp_s)
            return dt.isoformat()
        else:
            return str(timestamp_ns)


# Convenience function
def create_console_exporter(**kwargs) -> ConsoleExporter:
    """Create a console exporter with default settings.

    Args:
        **kwargs: Arguments passed to ConsoleExporter

    Returns:
        Configured console exporter
    """
    return ConsoleExporter(**kwargs)
