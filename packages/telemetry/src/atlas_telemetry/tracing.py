"""Console tracing with optional OTLP/HTTP and Azure Monitor export."""

from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)


def configure_tracing(
    service_name: str,
    *,
    endpoint: str | None = None,
    azure_connection_string: str | None = None,
) -> TracerProvider:
    """Create a provider; the service owns its tracers and shutdown."""
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    try:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        if endpoint is not None:
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        if azure_connection_string is not None:
            provider.add_span_processor(
                BatchSpanProcessor(
                    AzureMonitorTraceExporter(connection_string=azure_connection_string)
                )
            )
    except Exception:
        provider.shutdown()
        raise
    return provider
