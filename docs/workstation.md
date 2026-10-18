# Service workstation

The Streamlit app in `apps/workstation/` provides a hedge fund workstation for
exercising service APIs. It currently supports Orders. All orders are sample
data: there is no database, order execution, persistence, or app volume.

## Run locally

Use Python 3.12 and UV. Run from the repository root:

```sh
uv sync --locked --all-packages
cp apps/workstation/.env.example apps/workstation/.env
uv run --package atlas-orders uvicorn atlas_orders.main:app --reload --port 8003
```

In another terminal:

```sh
uv run --package atlas-workstation streamlit run apps/workstation/streamlit_app.py
```

Copy the template only for initial setup; keep an existing `.env` file. Configure
the service URL in `apps/workstation/.env`:

```dotenv
ORDERS_API_URL=http://127.0.0.1:8003
APP_SERVICE_NAME=workstation
OBSERVABILITY_TRACES_ENDPOINT=http://127.0.0.1:4318/v1/traces
```

Open <http://localhost:8501>. Service URLs come from configuration, with no URL
editor or hardcoded URL fallback in the app. Process environment variables
override `.env` values. The file is resolved from the app directory regardless
of the working directory, read as UTF-8, and read again on each Streamlit rerun.
After editing it, interact with the app or use Streamlit's rerun action. Exported
environment variables require restarting the Streamlit process to change them.

The local `.env` is ignored by Git and excluded from Docker build contexts;
`.env.example` is the committed template. If `ORDERS_API_URL` is missing or
empty, the app displays a configuration error instead of choosing a default URL.

The timeout defaults to 5 seconds; the sidebar allows 1 to 30 seconds. Requests
originate from the Streamlit server, so the configured URL must be reachable
from that server.

Requests run only when a button or form is submitted. There is no automatic
polling or retry. Connection failures appear in the UI without stopping the app.

## Exercise Orders

- **Order blotter:** load three fixed sample orders. Look up `ORD-1001`,
  `ORD-1002`, or `ORD-1003`. An unknown ID returns HTTP 404.
- **Order ticket:** submit a buy or sell order with a positive integer quantity.
  Market orders have no limit price; limit orders require a positive price with
  at most two decimal places. Prices are decimal strings in the API contract.
  Supported currencies are USD, GBP, and EUR.
- **Request inspector:** probe `/health`, `/ready`, `/random`, or `/metrics/`.
  Inspect the latest 50 requests, HTTP status, duration, request and response
  bodies, response headers, and trace ID. History exists only in Streamlit
  session memory. Clearing it does not affect the service.

Changing the configured URL clears displayed order results on the next rerun. History retains each
request's original URL. Submissions return a `SIM-` ID, `status: simulated`, and
a timestamp. They do not change the blotter; looking up a `SIM-` ID returns 404.

| Method | Endpoint | Result |
| --- | --- | --- |
| GET | `/orders/v1/orders` | Fixed sample orders |
| GET | `/orders/v1/orders/{order_id}` | Sample order or HTTP 404 |
| POST | `/orders/v1/orders` | HTTP 200 simulated acknowledgement; HTTP 422 for invalid input |

The older `/orders/v1/order?id=1` text endpoint remains available and is marked
deprecated in OpenAPI. The app uses the structured endpoints above.

The [order-simulated webhook contract](orders-webhooks.md) documents the
submission acknowledgement as an outbound notification in `/docs`. This is an
OpenAPI contract; submitting a ticket does not send an HTTP notification yet.

Exercise validation with this request, which returns HTTP 422:

```sh
curl -i http://localhost:8003/orders/v1/orders -H 'Content-Type: application/json' -d '{"symbol":"AAPL","side":"buy","quantity":0}'
```

## Follow telemetry

Each Workstation HTTP call creates a real OpenTelemetry client span under
`service.name=workstation`. The client injects its active W3C trace context and
baggage into the request. Orders extracts that context and creates a server span
under `service.name=orders`, using the client span as its parent. The request
inspector displays this shared trace ID, also returned as Orders' `X-Trace-ID`.

Both applications must export to the same collector or trace backend. The
Workstation `.env.example` configures the existing local Alloy receiver:

```dotenv
APP_SERVICE_NAME=workstation
OBSERVABILITY_TRACES_ENDPOINT=http://127.0.0.1:4318/v1/traces
```

Workstation uses the shared `atlas-telemetry` tracing helper. Providers are reused
across Streamlit reruns and sessions and shut down when the process exits.
Restart Streamlit after changing tracing configuration. Leave the endpoint empty
for console-only tracing. Use a distinct service name for each application.

This trace starts in the Streamlit server, where API calls run. Browser UI and
WebSocket activity are not separately instrumented. Connection failures and
HTTP error responses still produce client spans; HTTP errors also retain their
matching Orders server span when the request reaches the service.

Orders prints spans to stdout and JSON logs to stderr by default. Set
`OBSERVABILITY_TRACES_ENDPOINT=http://localhost:4318/v1/traces` before starting
Orders to export traces to the existing Alloy receiver. See
[Orders configuration](orders-configuration.md) for exporter settings.

The current telemetry Compose file is `infrastructure/docker-compose.yaml`:

```sh
docker compose -f infrastructure/docker-compose.yaml up -d
mkdir -p infrastructure/telemetry/logs
OBSERVABILITY_TRACES_ENDPOINT=http://localhost:4318/v1/traces uv run --package atlas-orders uvicorn atlas_orders.main:app --host 0.0.0.0 --port 8003 2>> infrastructure/telemetry/logs/orders.log
```

The host binding allows the existing Prometheus container to scrape Orders.
Use a trusted local development machine. Grafana is at <http://localhost:3000>,
with local default credentials `admin` / `admin`. Select the provisioned
Prometheus, Loki, or Tempo data source in Explore. Telemetry backend storage
follows the existing Compose configuration; the workstation and Orders add no volumes.

### Inspect an end-to-end trace

Start the telemetry stack, Orders, and Workstation as above. In the workstation,
click **Load sample orders**, **Find order**, or **Send simulated order**. Copy
the trace ID from the response inspector and allow a few seconds for batched export.

In Grafana Explore, select **Tempo** and look up that trace ID. Alternatively,
open <http://localhost:16686>, select the **workstation** service, and find the
request in Jaeger. Both backends receive the same trace through Alloy.

The trace waterfall includes these spans:

```text
workstation  CLIENT  GET
  orders     SERVER  GET /orders/v1/orders
```

The Orders server span's parent ID must equal the Workstation client span ID.
An unknown order produces connected HTTP 404 spans; an invalid ticket produces
connected HTTP 422 spans. `/random` adds its `orders.generate_random` business
span beneath the Orders server span.

To extend tracing to another service, configure a distinct service name and the
same collector, extract incoming W3C context before starting its server span,
and inject the active client context on each downstream call. Workstation's
shared `ApiClient` does this for every service client that uses it.

Useful Prometheus queries:

```promql
sum by (http_route, http_response_status_code) (orders_http_requests_total)
```

```promql
sum(rate(orders_http_duration_seconds_sum[5m]))
/
sum(rate(orders_http_duration_seconds_count[5m]))
```

Metric labels use route templates rather than order IDs to bound cardinality.
Orders traces HTTP requests including health, readiness, and the random demo.
The `/metrics/` scrape route is excluded from server tracing and request metrics
to avoid scrape noise. A workstation metrics probe therefore has only its client span.

### Missing logs in Grafana

In Grafana Explore, select Loki and query `{service_name="orders"}` with a
recent time range. Send an Orders request to generate a new request log.

Use `just run-order` to create the log directory and redirect Orders stderr to
`infrastructure/telemetry/logs/orders.log`. A plain Uvicorn command without this
redirection prints logs only to the terminal; Alloy cannot collect those logs.

If the file stops growing, inspect the running Uvicorn process's stderr with
`ls -l /proc/<pid>/fd/2`. A destination ending in `(deleted)` means the log file
was removed or replaced while Orders was running. Stop Orders and rerun
`just run-order` to reopen the current file. Reloading only the application
worker does not reopen the reloader's stderr. Keep the active file in place;
stop the service before replacing it.

## Extend the app

```text
apps/workstation/
  streamlit_app.py                 Script entry point
  src/atlas_workstation/
    app.py                        Navigation and connection composition
    config.py                     Service registry and dotenv loading
    telemetry.py                  Process-owned tracing providers and export
    api/client.py                 HTTP, timeouts, trace context, result model
    api/orders.py                 Orders paths and request methods
    pages/orders.py               Blotter and ticket widgets
    pages/diagnostics.py          Probes and history
    ui/requests.py                Shared response inspector and session history
  tests/                          HTTP boundary and Streamlit widget tests
```

To add a service, register its defaults in `config.py`, add its client under
`api/`, and add a page under `pages/`. Wire that page and client in `app.py`,
using the selected service to choose matching pages. Only Orders is wired today.
Reuse `ApiResult` and the bounded history. Add service-specific probes as needed.
UI modules never import a service's implementation or persistence models.

In Orders, `models/orders.py` defines contracts, `services/orders.py` owns
stateless use cases and fixtures, and `api/v1/endpoints/orders.py` maps them to
HTTP. Request telemetry lives in `app/observability.py` and uses the service's
lifespan-owned instruments.

```sh
uv run pytest apps/workstation/tests services/orders/tests
uv run ruff check apps/workstation services/orders
uv run ruff format --check apps/workstation services/orders
```
