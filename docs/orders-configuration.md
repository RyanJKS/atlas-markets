# Orders configuration

Orders separates typed configuration models from environment loading.

- `core/config/settings.py` defines `AppSettings`, `ObservabilitySettings`, and the
  final `Settings` model. These models do not read the environment themselves.
- `core/config/loader.py` uses Pydantic Settings adapters to read each section from
  the environment, validates the values, and injects plain typed models into `Settings`.
- `get_settings()` caches that final model once per process. The entry point passes
  it to `create_app()`, and downstream code receives the same configuration object.

The dependency direction is loader to models, then application to loader. Configuration
models never import the application factory, which avoids circular startup imports.

## Read settings downstream

```python
from atlas_orders.core.config.loader import get_settings

settings = get_settings()
service_name = settings.app.service_name
version = settings.app.version
traces_endpoint = settings.observability.traces_endpoint
```

The factory initializes one typed `AppState` in `app/state.py`, attached at
`app.state.orders`. Read settings through the shared accessor when an application
instance is available:

```python
from atlas_orders.app.state import get_app_state

state = get_app_state(app)
settings = state.settings
```

`AppState` holds settings and an optional `TelemetryState`. Lifespan populates the
telemetry field during startup and clears it during shutdown. Feature code calls
`state.get_telemetry()` to obtain the tracer and counter; calling it outside the
running lifespan raises a clear error. FastAPI state attachment and retrieval stay
inside `state.py`; other modules use the typed state object.

Health responses, application version, logger naming, and logging setup use these
nested settings. Calling `create_app()` without an explicit model also uses
`get_settings()`.

## Environment variables

The environment adapters use case-insensitive names with separate prefixes:

| Variable | Default | Effect |
| --- | --- | --- |
| `APP_SERVICE_NAME` | `orders` | Service identity in health responses and loggers. |
| `APP_VERSION` | `0.1.0` | API metadata and the readiness response version. |
| `OBSERVABILITY_TRACES_ENDPOINT` | Unset (`None`) | Also export spans to this complete OTLP/HTTP URL, such as `http://localhost:4318/v1/traces`. |
| `OBSERVABILITY_AZURE_CONNECTION_STRING` | Unset (`None`) | Also export traces to Azure Application Insights; the value is masked in settings representations. |

Logging and console tracing are always initialized. No enable/disable flags are
needed. Leave the endpoint unset for console output only; set a valid HTTP(S) URL
to add remote trace export. Empty service names, empty versions, and invalid URLs
fail validation during startup.

From the repository root, with a compatible OTLP/HTTP receiver already running:

```sh
OBSERVABILITY_TRACES_ENDPOINT=http://localhost:4318/v1/traces \
  uv run --package atlas-orders uvicorn atlas_orders.main:app --reload --port 8003
```

This adds remote traces while keeping logs and spans in the terminal. Jaeger or an
OpenTelemetry Collector can receive the spans when configured for OTLP/HTTP.
Prometheus scrapes metrics from `/metrics/`; it is not a trace destination.
Application-side log export remains a future step. The optional
[local telemetry stack](orders-docker.md) supplies trace receivers and collects
stderr logs through Alloy.
See [Application Insights traces](telemetry.md#application-insights-traces) for
Azure configuration and [Prometheus metrics](telemetry.md#prometheus-metrics) for
scrape configuration. Both trace destinations can be used together.

## Load a local `.env` file

By default, `get_settings()` reads the existing service file at
`services/orders/src/atlas_orders/.env`. This path is resolved from the loader's
location, so it works regardless of the directory used to start the service.
The file is optional and read as UTF-8. For example:

```dotenv
APP_SERVICE_NAME=orders-local
APP_VERSION=0.2.0
OBSERVABILITY_TRACES_ENDPOINT=http://localhost:4318/v1/traces
```

Values are applied in this order, from highest priority to lowest:

1. Process environment variables.
2. Values from the `.env` file.
3. Model defaults.

Unknown file keys are ignored, allowing both settings sections to share one
file. To select another file or disable file loading explicitly:

```python
settings = get_settings(env_file="/path/to/orders.env")
settings_without_file = get_settings(env_file=None)
```

Relative overrides are resolved against the current working directory. The
loader caches its result for the requested file; restart the service after
changing configuration.

Local `.env` files are excluded from Docker builds, including files nested under
service source directories. Pass container variables through Docker or Compose's
`environment` or `env_file` configuration; a host variable or file is not
automatically available inside the container.

The `/random` route creates one manual span. Logs written inside that span include
its `trace_id` and `span_id`; logs outside a span omit those fields. See
[Shared telemetry](telemetry.md#trace-export) for export behavior.

## Inject configuration explicitly

Tests or another application entry point can construct the models without reading
environment variables:

```python
from atlas_orders.app.bootstrap import create_app
from atlas_orders.core.config.settings import AppSettings, ObservabilitySettings, Settings

settings = Settings(
    app=AppSettings(service_name="orders-worker", version="2.0.0"),
    observability=ObservabilitySettings(traces_endpoint="http://localhost:4318/v1/traces"),
)
app = create_app(settings)
```

`Settings()` alone uses model defaults. Use `get_settings()` when environment-backed
configuration is required. Restart a running service after configuration changes:
the loader caches configuration for the running process.

Tests can call `get_settings.cache_clear()` before loading a changed environment and
again during cleanup. Clearing this cache does not reconfigure an already-created
application or its logger.
