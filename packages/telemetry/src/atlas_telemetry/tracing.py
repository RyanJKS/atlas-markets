"""Explicit OpenTelemetry setup with batched OTLP/HTTP trace export."""

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter


def create_tracer_provider(
    service_name: str, *, exporter: SpanExporter | None = None
) -> TracerProvider:
    """Create a provider; the caller owns registration and shutdown.

    The default exporter reads standard OTEL_EXPORTER_OTLP_* environment variables.
    An injected exporter supports tests without a collector. This function does not
    replace the process-global provider or instrument a web framework.
    """
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter() if exporter is None else exporter)
    )
    return provider
