# Shared telemetry

`packages/telemetry/` is an implemented shared Python library. It provides JSON
application logs and OpenTelemetry tracing primitives. It does not run as a server.
Services opt in by declaring the dependency and calling its setup functions. The
existing service scaffolds do not call these functions yet.

## Add the dependency

In the consuming Python service's `pyproject.toml`, add `atlas-telemetry` to its
existing dependency list and configure a workspace source:

```toml
[project]
dependencies = [
    # Keep the service's existing runtime dependencies here too.
    "atlas-telemetry",
]

[tool.uv.sources]
atlas-telemetry = { workspace = true }
```

Run `uv lock` and `uv sync --locked --all-packages` from the repository root.
The distribution name is `atlas-telemetry`; Python imports use `atlas_telemetry`.

## Write application logs

```python
from atlas_telemetry import configure_logging

logger = configure_logging("market-data")
logger.info("Market data service started")
```

The returned logger is named `atlas.market-data`. It writes one JSON object per
line to stderr, including timestamp, service name, severity, logger name, and message.
Inside an active OpenTelemetry span, it adds `trace_id` and `span_id`. Exception
information is included when logging with `logger.exception`.

Call setup during startup and use the returned logger for application messages.
Repeated calls for the same service reuse the library's handler. The root logger,
Uvicorn access logs, and other third-party loggers retain their existing configuration.
Messages are not automatically redacted.

## Configure trace export

A reachable OpenTelemetry Collector or compatible backend is required for trace
export. This repository does not deploy a collector. The library uses OTLP over
HTTP/protobuf, normally on port 4318. Configure the endpoint before starting a process:

```sh
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_RESOURCE_ATTRIBUTES=deployment.environment.name=local,service.version=0.1.0
```

The HTTP exporter appends `/v1/traces` to the general endpoint. Alternatively,
`OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` sets the complete traces URL. The exporter also
supports standard OTLP headers and timeout variables. These helpers use the HTTP
exporter; selecting a gRPC protocol through environment variables does not change it.
Inside a container, use an endpoint reachable from that container rather than the
host's loopback address.

An application can explicitly create and register its provider:

```python
from opentelemetry import trace

from atlas_telemetry import configure_logging, create_tracer_provider

logger = configure_logging("market-data")
provider = create_tracer_provider("market-data")
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

try:
    with tracer.start_as_current_span("refresh-prices"):
        logger.info("Refreshing prices")
finally:
    provider.shutdown()
```

The provider attaches `service.name` and batches completed spans for background export.
Creating it opts into export; importing the library or configuring logging alone does
not. If no endpoint is configured, the SDK uses its default local HTTP endpoint.

The application owns the provider lifecycle. Register it once per process, then shut
it down after request handling stops. In a web service, put setup and cleanup in the
application's startup and shutdown lifecycle, not in individual request handlers.
Do not combine this manual provider setup with an auto-instrumentation launcher that
already manages the global provider.

## Scope and checks

The library currently exports traces and writes local JSON logs. It does not configure
metrics, OTLP log export, FastAPI instrumentation, dashboards, or collector deployment.
Instrument service boundaries explicitly or add framework instrumentation when a
service adopts tracing. The library does not create request spans automatically.

Tests use an in-memory exporter and require no collector:

```sh
uv run pytest packages/telemetry/tests
```
