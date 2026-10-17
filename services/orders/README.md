# Orders

Planned responsibility: own order requests, validation, state transitions, and
cancellation. Execution simulation belongs in `execution-simulator/`.

The current scaffold exposes `GET /health`, `GET /ready`, `/docs`, `/openapi.json`,
`GET /random`, and the `/metrics/` scrape endpoint. There is no order processing yet.

`atlas_orders.main` creates the application through `app/bootstrap.py`.
`app/state.py` defines one typed `AppState` for settings and runtime telemetry.
Use `get_app_state(app)` to access it; lifespan populates and clears its
`TelemetryState` around request handling.
`app/lifespan.py` calls the shared logging and tracing helpers at startup and
shuts the tracing provider down on exit. `/random` returns a random number, logs
a message with matching trace/span IDs, and prints an `orders.generate_random`
span to the console. Set `OBSERVABILITY_TRACES_ENDPOINT` to a complete OTLP/HTTP URL
such as `http://localhost:4318/v1/traces` to also send spans to a receiver.
Set `OBSERVABILITY_AZURE_CONNECTION_STRING` to also export traces to Application
Insights. `/random` increments `orders_random_requests_total`, which Prometheus can
scrape at `/metrics/`. Remote log export and automatic HTTP instrumentation remain
future steps.

From the repository root:

```sh
uv run --package atlas-orders uvicorn atlas_orders.main:app --reload --port 8003
```

The `just run-order` recipe redirects stderr to a file for Alloy log collection.
If startup fails without showing an error in the terminal, inspect the traceback:

```sh
tail -n 80 infrastructure/telemetry/logs/orders.log
```

See [Local observability with Docker](docs/docker.md) for Jaeger, Loki, Grafana,
the shared network, and optional Alloy log collection.

The distribution is `atlas-orders`; the import package is `atlas_orders`.
See [Shared telemetry](../../docs/telemetry.md) for logging and planned learning steps.

`AppSettings` supplies the service name and version; `ObservabilitySettings`
contains the optional `traces_endpoint` and `azure_connection_string`; console
logs and tracing are always on. The cached `get_settings()` loader also
reads `src/atlas_orders/.env`. Process environment values override file values;
missing files use model defaults. Local `.env` files are excluded from images;
pass container configuration as environment variables.

See [Orders configuration](../../docs/orders-configuration.md) for prefixes and
explicit injection, and [service boundaries](../README.md) for the wider design.
