"""OTLP (OpenTelemetry Protocol) exporter configuration.

This module provides configuration helpers for OTLP exporters.
"""

from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
    OTLPMetricExporter as HTTPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as HTTPSpanExporter,
)


class OTLPExporter:
    """OTLP exporter configuration and factory."""

    def __init__(
        self,
        endpoint: str = "localhost:4317",
        headers: dict[str, str] | None = None,
        use_http: bool = False,
        insecure: bool = True,
        timeout: int = 10,
    ):
        """Initialize OTLP exporter configuration.

        Args:
            endpoint: OTLP endpoint (default: localhost:4317 for gRPC)
            headers: Optional headers for authentication
            use_http: Use HTTP instead of gRPC
            insecure: Use insecure connection
            timeout: Export timeout in seconds
        """
        self.endpoint = endpoint
        self.headers = headers or {}
        self.use_http = use_http
        self.insecure = insecure
        self.timeout = timeout

        # Adjust default endpoint for HTTP
        if use_http and endpoint == "localhost:4317":
            self.endpoint = "localhost:4318"

    def create_span_exporter(self) -> OTLPSpanExporter:
        """Create OTLP span exporter.

        Returns:
            Configured span exporter
        """
        if self.use_http:
            endpoint = f"http://{self.endpoint}/v1/traces"
            return HTTPSpanExporter(
                endpoint=endpoint, headers=self.headers, timeout=self.timeout
            )
        else:
            return OTLPSpanExporter(
                endpoint=self.endpoint,
                headers=self._format_grpc_headers(self.headers),
                insecure=self.insecure,
                timeout=self.timeout,
            )

    def create_metric_exporter(self) -> OTLPMetricExporter:
        """Create OTLP metric exporter.

        Returns:
            Configured metric exporter
        """
        if self.use_http:
            endpoint = f"http://{self.endpoint}/v1/metrics"
            return HTTPMetricExporter(
                endpoint=endpoint, headers=self.headers, timeout=self.timeout
            )
        else:
            return OTLPMetricExporter(
                endpoint=self.endpoint,
                headers=self._format_grpc_headers(self.headers),
                insecure=self.insecure,
                timeout=self.timeout,
            )

    def _format_grpc_headers(self, headers: dict[str, str]) -> str:
        """Format headers for gRPC metadata.

        Args:
            headers: Dictionary of headers

        Returns:
            Formatted header string
        """
        if not headers:
            return ""

        # gRPC expects headers as key=value,key=value
        return ",".join(f"{k}={v}" for k, v in headers.items())

    @classmethod
    def for_jaeger(cls, host: str = "localhost", port: int = 4317) -> "OTLPExporter":
        """Create OTLP exporter configured for Jaeger.

        Args:
            host: Jaeger host
            port: Jaeger OTLP port

        Returns:
            Configured exporter
        """
        return cls(endpoint=f"{host}:{port}", insecure=True)

    @classmethod
    def for_collector(
        cls, endpoint: str, api_key: str | None = None, use_http: bool = True
    ) -> "OTLPExporter":
        """Create OTLP exporter for OpenTelemetry Collector.

        Args:
            endpoint: Collector endpoint
            api_key: Optional API key for authentication
            use_http: Use HTTP transport

        Returns:
            Configured exporter
        """
        headers = {}
        if api_key:
            headers["api-key"] = api_key

        return cls(
            endpoint=endpoint, headers=headers, use_http=use_http, insecure=False
        )

    @classmethod
    def for_cloud_provider(cls, provider: str, **kwargs) -> "OTLPExporter":
        """Create OTLP exporter for cloud providers.

        Args:
            provider: Cloud provider name (aws, gcp, azure)
            **kwargs: Provider-specific configuration

        Returns:
            Configured exporter
        """
        if provider == "aws":
            # AWS X-Ray through OpenTelemetry Collector
            endpoint = kwargs.get("endpoint", "localhost:4317")
            return cls(endpoint=endpoint)

        elif provider == "gcp":
            # Google Cloud Trace
            project_id = kwargs.get("project_id")
            if not project_id:
                raise ValueError("project_id required for GCP")

            return cls(
                endpoint="cloudtrace.googleapis.com:443",
                headers={"x-goog-project-id": project_id},
                insecure=False,
            )

        elif provider == "azure":
            # Azure Monitor through OpenTelemetry Collector
            endpoint = kwargs.get("endpoint", "localhost:4317")
            instrumentation_key = kwargs.get("instrumentation_key")

            headers = {}
            if instrumentation_key:
                headers["instrumentation-key"] = instrumentation_key

            return cls(endpoint=endpoint, headers=headers)

        else:
            raise ValueError(f"Unknown cloud provider: {provider}")


# Convenience functions


def create_otlp_span_exporter(
    endpoint: str = "localhost:4317", **kwargs
) -> OTLPSpanExporter:
    """Create OTLP span exporter with defaults.

    Args:
        endpoint: OTLP endpoint
        **kwargs: Additional configuration

    Returns:
        Configured span exporter
    """
    exporter = OTLPExporter(endpoint=endpoint, **kwargs)
    return exporter.create_span_exporter()


def create_otlp_metric_exporter(
    endpoint: str = "localhost:4317", **kwargs
) -> OTLPMetricExporter:
    """Create OTLP metric exporter with defaults.

    Args:
        endpoint: OTLP endpoint
        **kwargs: Additional configuration

    Returns:
        Configured metric exporter
    """
    exporter = OTLPExporter(endpoint=endpoint, **kwargs)
    return exporter.create_metric_exporter()
