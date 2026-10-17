# Atlas Telemetry

Shared JSON logging and basic OpenTelemetry tracing for Python services.
Completed spans print to the console and can also use an optional OTLP/HTTP endpoint.
Metrics use a Prometheus reader. Azure Application Insights trace export is also
available; remote log export is a later step.

The distribution is `atlas-telemetry`; the import package is `atlas_telemetry`.
Importing it does not install dependencies or configure logging.

## Library and service boundaries

This library owns reusable log formatting, trace/span ID correlation, and the small
`configure_logging()`, `configure_tracing()`, and `configure_metrics()` helpers.
Each service owns its service name, configuration, startup call, and log messages
inside its routes and business logic. Keep HTTP routes and application lifecycle
code in the service.

Each service process configures its own logger. Sharing a library shares conventions,
not a running logger across services. Go and Rust services use their native libraries;
this package contains Python code only.

## Declare the dependency

From the repository root:

```sh
uv add --package atlas-orders atlas-telemetry
```

Use the consuming project's `[project].name` in place of `atlas-orders`.
UV updates its manifest and the shared lockfile and installs the dependency.
For a manual edit, merge these entries into the service's `pyproject.toml`:

```toml
[project]
name = "atlas-orders"
dependencies = [
    # Retain the service's other dependencies.
    "atlas-telemetry",
]

[tool.uv.sources]
atlas-telemetry = { workspace = true }
```

After a manual edit, run `uv lock` and `uv sync --locked --all-packages` from the
repository root. An import alone does not declare or install a dependency.

## Initialize inside the service

Call once during startup:

```python
from atlas_telemetry import configure_logging

logger = configure_logging("orders")
logger.info("Orders service started")
```

In other modules, use `logging.getLogger("atlas.orders")`. The shared setup writes
JSON to stderr, leaves the root logger unchanged, and avoids duplicate handlers
when called again. Logs inside an active span include its `trace_id` and `span_id`.

See the [telemetry guide](../../docs/telemetry.md) for the orders example and learning steps.

## Basic tracing

`configure_tracing("orders")` returns an OpenTelemetry provider with console output.
Use `provider.get_tracer(__name__)` to create manual spans and call
`provider.shutdown()` when the service stops. The helper does not register a global
provider or instrument HTTP routes. Pass `endpoint="http://localhost:4318/v1/traces"`
to also export spans over OTLP/HTTP; console output remains active. The service
owns environment loading and passes the endpoint into this helper. Orders uses
`OBSERVABILITY_TRACES_ENDPOINT`. See the [tracing example](../../docs/telemetry.md#basic-tracing)
and [export guide](../../docs/telemetry.md#trace-export).

## Azure traces and Prometheus metrics

Pass `azure_connection_string=...` to `configure_tracing()` to add Application
Insights trace export. Orders loads `OBSERVABILITY_AZURE_CONNECTION_STRING` and
passes the value explicitly. If the OTLP endpoint is also set, both receive spans.
Console output remains active; these settings do not export logs or metrics.

`configure_metrics(service_name)` returns a meter provider with a
`PrometheusMetricReader`. The service creates counters, exposes the scrape route
using `prometheus_client.make_asgi_app()`, and shuts the provider down. Orders
exposes `/metrics/`; its `/random` route increments a request counter.

The service owns framework routes and environment loading. See the
[telemetry guide](../../docs/telemetry.md#prometheus-metrics) for scrape setup.

## Include the dependency in the service image

Keep the Dockerfile in the service directory, with the repository root as build context.
These steps belong inside the existing Dockerfile, after installing UV:

```dockerfile
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY services/ ./services/
COPY packages/ ./packages/
RUN uv sync --locked --no-dev --package atlas-orders
```

UV installs telemetry because orders declares it as a dependency. For another
service, use that service's distribution name and entry point. If Python apps
join the workspace later, also copy their manifests and source.

After changing dependencies, rebuild the consuming service's image:

```sh
docker compose -f infrastructure/compose.yaml build orders
```
