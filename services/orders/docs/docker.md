# Local observability with Docker

The default telemetry stack starts Grafana, Prometheus, Alloy, Loki, Jaeger, and
Tempo. Run commands from the repository root with Docker Compose v2 available.
The application still runs separately through UV.

## Start the default stack

```sh
docker compose -f infra/telemetry-docker-compose.yaml up -d
```

Compose creates the `atlas-telemetry_default` network. Grafana already has
Prometheus, Loki, Jaeger, and Tempo data sources configured; no manual setup is
needed. First startup pulls the pinned image versions and may take a little time.

Stop earlier manually started containers that use the same ports before starting
this stack. Container names are scoped to the Compose project, but host ports must
still be available. Inspect existing containers with:

```sh
docker ps --format 'table {{.Names}}\t{{.Ports}}'
```

| Component | Host address | Purpose |
| --- | --- | --- |
| Grafana | <http://localhost:3000> | Explore all four provisioned data sources; login `admin` / `admin`. |
| Prometheus | <http://localhost:9090/targets> | Check scrape targets and query metrics. |
| Loki | <http://localhost:3100/ready> | Log storage readiness; no browser UI. |
| Jaeger | <http://localhost:16686> | Search traces directly. |
| Tempo | <http://localhost:3200/ready> | Trace storage readiness; use Grafana to search. |
| Alloy OTLP/HTTP | `http://localhost:4318/v1/traces` | Receive application spans and forward them to both Jaeger and Tempo. |
| Alloy OTLP/gRPC | `localhost:4317` | Alternative trace ingestion protocol. |

Host ports bind to loopback. These local services use no ingestion authentication;
Grafana uses the development login above.

## Run orders and generate data

Set this in `services/orders/src/atlas_orders/.env`, retaining its other settings:

```dotenv
OBSERVABILITY_TRACES_ENDPOINT=http://localhost:4318/v1/traces
```

Port `4318` now belongs to Alloy. It sends each span to **both Jaeger and Tempo**,
so orders needs only one endpoint. Jaeger and Tempo store separate copies for local
comparison; normally you would choose one trace backend. An Azure connection
string, if also configured, still enables the application's separate Azure export.

Start or restart orders:

```sh
uv run --package atlas-orders uvicorn atlas_orders.main:app \
  --reload --host 0.0.0.0 --port 8003 \
  2>> infra/telemetry/logs/orders.log
```

`--host 0.0.0.0` makes the host application reachable from Prometheus's container.
Prometheus uses `host.docker.internal:8003`, with a Linux host-gateway mapping
provided by Compose. A loopback-only Uvicorn listener cannot serve that scrape.

Logs go to the ignored local file, which Alloy tails and forwards to Loki. Console
spans still appear in the terminal. The tracked log directory is created by the
checkout; you do not need a `/tmp` directory or a separate Alloy command.

In another terminal:

```sh
curl http://localhost:8003/random
curl http://localhost:8003/metrics/
```

Allow a few seconds for batching and the five-second Prometheus scrape interval.
The `atlas-orders` target is expected to be down until orders is running.

## View data in Grafana

Open <http://localhost:3000> and sign in with `admin` / `admin`. Under **Explore**:

- **Prometheus:** query `orders_random_requests_total`.
- **Loki:** query `{service_name="orders"}`. Trace IDs remain in the JSON log fields.
- **Jaeger:** search service `orders` (or your configured `APP_SERVICE_NAME`).
- **Tempo:** search the same service using its search builder or TraceQL.

Use the last 15 minutes and look for `orders.generate_random`. Jaeger and Tempo
receive the same trace IDs. The host file collector uses the fixed label
`service_name="orders"`; change its target labels if you rename the application.
Uvicorn startup and access messages can be plain text alongside application JSON.

## Container logs and application containers

Alloy also discovers containers from the existing `atlas-markets` application
Compose project and forwards their stderr to Loki, labeled by Compose service name.
It reads Docker metadata and logs through the mounted Docker socket. It does not
collect this telemetry stack's own containers, and ignores application stdout so
console spans do not become log entries.

The default metrics target above is for **orders running on the host**. If you run
orders through `infrastructure/compose.yaml` instead, also configure its trace
environment and attach it to the telemetry network. Update the scrape target to
the orders container's reachable address and port; joining a network alone does
not change an existing container's environment. Inside that network the trace
endpoint is `http://alloy:4318/v1/traces`, and orders serves metrics on port `8000`.

## Storage and stopping

Grafana settings, Prometheus samples, Loki data, Tempo traces, and Alloy file read
positions use named Docker volumes. Prometheus retains seven days of samples;
Tempo retains 24 hours of traces. Jaeger uses its default in-memory store and loses
traces when its process stops. Host log files remain in `infra/telemetry/logs/`.

```sh
docker compose -f infra/telemetry-docker-compose.yaml ps
docker compose -f infra/telemetry-docker-compose.yaml logs --tail=100
docker compose -f infra/telemetry-docker-compose.yaml down
```

`down` preserves named volumes. To deliberately reset all persisted demo data:

```sh
docker compose -f infra/telemetry-docker-compose.yaml down --volumes
```

If a host port must change, use its Compose variable. For example:

```sh
ATLAS_GRAFANA_PORT=3001 docker compose -f infra/telemetry-docker-compose.yaml up -d
```

Other variables are `ATLAS_PROMETHEUS_PORT`, `ATLAS_LOKI_PORT`,
`ATLAS_JAEGER_UI_PORT`, `ATLAS_TEMPO_PORT`, `ATLAS_OTLP_HTTP_PORT`, and
`ATLAS_OTLP_GRPC_PORT`. Update application URLs when changing ingestion ports.
Internal data source URLs do not change.

## Alternative: manual three-container setup

The earlier individual commands are retained below for testing Jaeger, Loki, and
Grafana independently. Use this alternative with the Compose stack stopped, since
they share host ports. The manual commands do not provision data sources or start
Prometheus, Tempo, or a log collector.

### Create a manual network

Run this once; skip it if the network already exists:

```sh
docker network create observability
```

Containers on this network can reach each other by name. Grafana uses
`http://jaeger:16686` and `http://loki:3100`, not `localhost`.

### Start three manual containers

If these names or ports are already in use, reuse your existing containers instead
of starting another copy. See [Connect existing containers](#connect-existing-containers).

```sh
docker run --rm -d --name jaeger --network observability \
  -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
  -p 127.0.0.1:16686:16686 \
  -p 127.0.0.1:4317:4317 \
  -p 127.0.0.1:4318:4318 \
  -p 127.0.0.1:9411:9411 \
  jaegertracing/all-in-one:latest

docker run --rm -d --name loki --network observability \
  -p 127.0.0.1:3100:3100 \
  grafana/loki:3.7.0

docker run --rm -d --name grafana --network observability \
  -p 127.0.0.1:3000:3000 \
  grafana/grafana:latest
```

| Tool | Host address | Purpose |
| --- | --- | --- |
| Jaeger UI | <http://localhost:16686> | Search traces directly. |
| Jaeger OTLP/HTTP | `http://localhost:4318/v1/traces` | Receive traces from orders. |
| Loki | <http://localhost:3100/ready> | Check readiness; Loki has no browser UI. |
| Grafana | <http://localhost:3000> | View data from Jaeger and Loki. |

Loki may need a short time before `/ready` returns `ready`.

### Connect existing containers

Find their names:

```sh
docker ps --format 'table {{.Names}}\t{{.Ports}}'
```

For an existing Jaeger container with a generated name, replace
`YOUR_JAEGER_CONTAINER` below:

```sh
docker network connect --alias jaeger observability YOUR_JAEGER_CONTAINER
```

If existing Loki or Grafana containers are not on the network, attach them too:

```sh
docker network connect --alias loki observability YOUR_LOKI_CONTAINER
docker network connect observability YOUR_GRAFANA_CONTAINER
```

Only run these commands for containers that are not already attached. Adding a
network does not change published ports; Jaeger still needs host port `4318` for
orders running through UV.


In the manual Grafana, add Jaeger at `http://jaeger:16686` and Loki at
`http://loki:3100`. Orders can send traces directly to Jaeger at
`http://localhost:4318/v1/traces`. Logs need Alloy or another collector; use the
full Compose stack above for preconfigured local collection.

Containers started with `--rm` are removed when stopped:

```sh
docker stop jaeger loki grafana
```
