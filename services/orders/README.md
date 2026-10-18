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
scrape at `/metrics/`.

The structured sample API provides `GET /orders/v1/orders`,
`GET /orders/v1/orders/{order_id}`, and `POST /orders/v1/orders`. Responses use
fixed fixtures or simulated acknowledgements. Submissions are never stored or
executed. Invalid tickets return HTTP 422; unknown IDs return HTTP 404. The
original `/orders/v1/order?id=1` endpoint remains available but is deprecated.
Models, stateless service use cases, and HTTP routes live in separate modules.

The `order-simulated` webhook appears in the **Webhooks** section of `/docs`.
It shares the submission's `SimulatedOrder` payload and documents an outbound
POST with an HTTP 204 acknowledgement. This declares the OpenAPI contract;
destination registration and HTTP delivery are not implemented. See the
[webhook guide](../../docs/orders-webhooks.md).

HTTP requests continue incoming W3C trace context and baggage and return `X-Trace-ID`.
Request logs include method, route template, status, duration, and trace/span IDs.
`orders_http_requests_total` and `orders_http_duration_seconds` record count and
latency, including error responses. Health, readiness, and random requests now
have server spans; `/metrics/` scraping is excluded from request instrumentation.
Workstation exports the matching client spans to the same collector. See the
[workstation guide](../../docs/workstation.md) for the Streamlit UI and telemetry
queries.

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
