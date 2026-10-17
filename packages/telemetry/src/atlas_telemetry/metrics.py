"""Basic OpenTelemetry metrics exposed through Prometheus."""

from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource


def configure_metrics(service_name: str) -> MeterProvider:
    """Create a provider; the service owns instruments and shutdown."""
    return MeterProvider(
        resource=Resource.create({"service.name": service_name}),
        metric_readers=[PrometheusMetricReader()],
    )
