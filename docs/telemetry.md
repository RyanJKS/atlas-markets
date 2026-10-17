# Shared telemetry

For copyable Docker commands, see [Local observability with Docker](orders-docker.md).

`packages/telemetry/` provides JSON logging through `configure_logging()` and
OpenTelemetry tracing through `configure_tracing()`, and Prometheus metrics through
`configure_metrics()`. Logging writes to
stderr; completed spans print to stdout. Traces can also go to OTLP/HTTP and Azure
Application Insights. Prometheus scrapes metrics from orders at `/metrics/`.
Remote log export is a later step.

## Library and service boundaries

The shared package owns log formatting and reusable logging, tracing, and metrics setup. Each service owns its
name, configuration, startup call, and log messages. HTTP routes and business
logic stay inside the service.

Each process has its own logger. Go and Rust services need their native libraries;
the Python package shares conventions only among Python services.

## Declare the dependency

From the repository root:

```sh
uv add --package atlas-orders atlas-telemetry
```

UV declares the dependency, records the workspace source, updates `uv.lock`, and
installs the package. Importing `atlas_telemetry` alone does none of these things.
The consuming service needs these entries in its existing `pyproject.toml`:

```toml
[project]
name = "atlas-orders"
dependencies = ["atlas-telemetry"]  # Retain other runtime dependencies too.

[tool.uv.sources]
atlas-telemetry = { workspace = true }
```

The service's Dockerfile copies workspace manifests and source before running
`uv sync --locked --no-dev --package atlas-orders`. That installs the service and
its declared shared dependency. Use the repository root as the Docker build context.

## Orders example

Orders always calls `configure_logging(settings.app.service_name)` in its FastAPI
lifespan. The same lifespan creates a tracing provider using the optional
`settings.observability.traces_endpoint` and `azure_connection_string`, stores its
tracer and request counter in the typed `TelemetryState` defined in `app/state.py`,
and shuts both providers down when
the service stops. It keeps your nested settings and cached `.env` loader; see
[Orders configuration](orders-configuration.md). The factory initializes one
`AppState`; lifespan populates its telemetry field before serving requests and
clears the field on shutdown. Routes access it through `get_app_state(app)` and
`state.get_telemetry()` rather than adding individual FastAPI state attributes.

```python
# During service startup:
from atlas_telemetry import configure_logging

configure_logging("orders")
```

```python
# Inside a route or business module:
import logging

logger = logging.getLogger("atlas.orders")
logger.info("Generated random value")
```

`GET /random` demonstrates this flow. Run orders from the repository root:

```sh
uv run --package atlas-orders uvicorn atlas_orders.main:app --reload --port 8003
```

Request `http://localhost:8003/random` and inspect the terminal: the route logs a
message to stderr and prints one `orders.generate_random` span to stdout. The span
wraps the random number generation, counter increment, and log call. Each log record includes timestamp,
service name, severity, logger name, and message.
Logs inside an active span also include matching `trace_id` and `span_id` fields;
logs outside a span omit these fields. Exception logs include exception details.
Repeated setup does not duplicate
handlers; the root logger and Uvicorn logs are unchanged.

## Basic tracing

`configure_tracing()` creates a provider with the service name as a resource
attribute. A `SimpleSpanProcessor` sends each completed span directly to a
`ConsoleSpanExporter`, making the result visible locally.

```python
from atlas_telemetry import configure_tracing

provider = configure_tracing("orders")
tracer = provider.get_tracer(__name__)
try:
    with tracer.start_as_current_span("example-operation"):
        print("Work happens here")
finally:
    provider.shutdown()
```

The service owns startup, span placement, and shutdown. Keep this provider for the
process lifetime. This helper does not register a global provider; obtain tracers
from the returned provider as shown above. Orders uses this same pattern in its lifespan.

## Trace export

Set this in the orders `.env` file or process environment:

```dotenv
OBSERVABILITY_TRACES_ENDPOINT=http://localhost:4318/v1/traces
```

Use a complete OTLP/HTTP trace URL. The service passes it to
`configure_tracing(service_name, endpoint=...)`, which adds a `BatchSpanProcessor`
and `OTLPSpanExporter` alongside console output. Shutdown flushes pending spans.
With neither a trace endpoint nor an Azure connection string, no remote trace
exporter is created. Restart orders after changing
settings. The optional [local telemetry stack](orders-docker.md) supplies an Alloy
receiver that forwards spans to both Jaeger and Tempo.

A Jaeger instance or OpenTelemetry Collector configured for OTLP/HTTP can receive
traces. Inside Docker, use an address reachable from the orders container;
`localhost` refers to that container.

Logging still writes JSON to stderr. A platform or collector can collect that
output; trace export settings do not export logs.

## Application Insights traces

Copy the connection string from your Application Insights resource's Overview
page. Set it in orders' `.env` file or process environment:

```dotenv
OBSERVABILITY_AZURE_CONNECTION_STRING=InstrumentationKey=<key>;IngestionEndpoint=https://<region>.in.applicationinsights.azure.com/
```

Orders passes the value to `configure_tracing(..., azure_connection_string=...)`.
The helper adds an `AzureMonitorTraceExporter` and batch processor, keeping console
output active. Settings mask the connection string in their representation.
Restart orders and request `/random` to generate a span. Azure ingestion can take
time; inspect your Application Insights resource for the trace.

If both the OTLP endpoint and Azure connection string are set, spans go to both
receivers. This exports traces only, not logs or metrics. The Azure and Prometheus
exporter dependencies currently use prerelease versions recorded in `uv.lock`.

## Prometheus metrics

Orders creates a `MeterProvider` using `PrometheusMetricReader`. `/random`
increments the `orders.random.requests` counter, exposed in Prometheus format as
`orders_random_requests_total`. The service owns the counter and provider shutdown;
the shared package owns reusable provider setup.

From another terminal, with orders running locally:

```sh
curl http://localhost:8003/random
curl http://localhost:8003/metrics/
```

Look for `orders_random_requests_total` with value `1` after the first request in
a fresh process. Prometheus pulls this endpoint; orders does not push metrics to
a Prometheus URL. Example scrape configuration when Prometheus runs on the host:

```yaml
scrape_configs:
  - job_name: atlas-orders
    metrics_path: /metrics/
    static_configs:
      - targets: ["localhost:8003"]
```

For Prometheus and orders containers on the same Docker network, use `orders:8000`.
For container-to-host access, use a reachable host address and bind Uvicorn to
`0.0.0.0`; on Linux, `host.docker.internal` requires a host-gateway mapping.
The optional [local telemetry stack](orders-docker.md) includes Prometheus, Alloy,
Loki, Jaeger, Tempo, and Grafana. Azure resources must be provisioned separately.

## Two instrumentation approaches in Kubernetes

The planned comparison uses **orders** for explicit SDK initialization and manual
spans, and **market-data** for Operator-injected Python instrumentation. Orders'
approach is implemented. Market-data injection and the cluster resources shown
below are not deployed by this repository. Fraud and the placeholder services have
no instrumentation approach selected yet.

Both can send traces to one Alloy/OpenTelemetry Collector and use the same trace
backend and Grafana. Keep different `service.name` values so searches can
distinguish services. Automatic instrumentation can coexist with manually added
business spans when both use the same initialized SDK; avoid initializing a second
provider stack in the injected application.

Install the Operator with its
[Helm chart](https://github.com/open-telemetry/opentelemetry-helm-charts/tree/main/charts/opentelemetry-operator)
after satisfying the chart's current Kubernetes/Helm and webhook TLS requirements.
The chart's default certificate setup uses `cert-manager`. The
[Helm overview](https://opentelemetry.io/docs/platforms/kubernetes/helm/) lists
separate Operator, Collector, and Demo charts; an existing Alloy receiver does not
require deploying another Collector. Installing the Operator alone does not
instrument existing pods or create telemetry storage.

For reference, with an application namespace named `atlas` and an Alloy receiver
Service named `alloy` in namespace `observability`, the instrumentation resource
would look like:

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata:
  name: market-data
  namespace: atlas
spec:
  exporter:
    endpoint: http://alloy.observability.svc.cluster.local:4318
  propagators:
    - tracecontext
    - baggage
  python:
    env:
      - name: OTEL_EXPORTER_OTLP_PROTOCOL
        value: http/protobuf
      - name: OTEL_SERVICE_NAME
        value: market-data
```

The OTLP base endpoint omits `/v1/traces` because the injected HTTP exporter adds
the signal path. Orders' explicit `OBSERVABILITY_TRACES_ENDPOINT` setting instead
expects the complete trace URL. Replace the example namespace and Service address
with the actual cluster receiver; it must accept OTLP/HTTP on port `4318`.

Add this fragment under the market-data Deployment's `spec.template`; it is not a
complete Deployment manifest:

```yaml
metadata:
  annotations:
    instrumentation.opentelemetry.io/inject-python: "market-data"
```

The named `Instrumentation` resource must exist in the workload's namespace.
Create/restart pods after adding the annotation, and inspect initialization and
collector output to verify injection. Orders should keep its explicit provider
initialization without the injection annotation.

Continue collecting container stderr through Alloy for Loki. Orders' metrics
remain Prometheus scrapes of `/metrics/`. If the injected service exports metrics
or logs over OTLP, configure those collector pipelines and destinations separately;
the current local Alloy configuration accepts OTLP traces only. The Docker socket
and file log sources in the local Compose config also need Kubernetes-specific
discovery and permissions when deploying Alloy in the cluster.

See the [Operator overview](https://opentelemetry.io/docs/platforms/kubernetes/operator/)
and [Python injection documentation](https://opentelemetry.io/docs/platforms/kubernetes/operator/automatic/)
for supported versions and settings. This documentation change does not install
anything in a cluster.

## Learn next

1. Add application-side OTLP log export if you need an alternative to Alloy's file
   and container log collection.
2. Add automatic HTTP instrumentation.

These next steps are not implemented yet.
