# Architecture

## Current implementation

Atlas Markets uses a UV workspace for Python 3.12 services. Each service has its own
`pyproject.toml`, uniquely named import package, `src/` tree, tests, and Dockerfile. A root
`uv.lock` resolves dependencies together; a container installs only its selected
service and its dependencies. This enforces dependency compatibility within the
Python workspace. A service needing incompatible dependencies must use a separate
project and lockfile instead.

Three FastAPI service scaffolds exist:

- `services/market-data/`: `atlas-market-data`, served locally on port 8001.
- `services/fraud/`: `atlas-fraud`, served locally on port 8002.
- `services/orders/`: `atlas-orders`, served locally on port 8003.

All three expose `GET /health`, `/docs`, and `/openapi.json`. Health checks indicate
process liveness, not feed availability, order processing, or fraud assessment readiness.
There are no databases, event brokers, market feeds, trained models, financial
workflows, fraud rules, authentication mechanisms, or service-to-service calls yet. Local
containers bind to loopback only and are not configured for public deployment.

Orders also exposes startup readiness at `/ready` and a logging and tracing demo
at `/random`. Its application factory registers routes, and its lifespan configures
shared JSON logging and console tracing, then shuts the tracing provider down on
exit. Logs inside a span include its trace/span IDs. An optional OTLP/HTTP endpoint
adds remote trace export; an Azure connection string adds Application Insights
trace export. A meter provider exposes the `/random` request counter at `/metrics/`
for Prometheus to scrape. Both providers shut down on exit. Requests under
`/orders/` now have HTTP spans, correlated logs, and request metrics. Other routes retain their existing instrumentation.

`execution-simulator/`, `portfolio/`, `ledger/`, and `payments/` are documentation-only
placeholders under `services/`. They have no manifests, runtimes, or containers and
are explicitly excluded from the UV workspace until implementation starts.

## Service workstation and sample Orders API

`apps/workstation/` is an installed Python package serving a Streamlit UI on
port 8501. UI pages call service clients through a shared HTTP transport; they
never import service source. Configuration, navigation, service clients, and
presentation components remain separate so later services can add pages.
See the [workstation guide](workstation.md).

Orders now exposes fixed sample list and lookup endpoints, plus a validated
simulated submission endpoint. Pydantic models define the HTTP contracts; a
stateless service owns fixtures and acknowledgements. No submissions persist,
execute, or change the sample blotter. Request middleware continues W3C trace
context, emits correlated logs, and records counts and latency by route template.
Workstation exports HTTP client spans and propagates W3C trace context and
baggage to Orders. Its server spans share the same trace and parent relationship
in the configured backend. Health, readiness, and random requests are included;
metrics scrapes are excluded from request instrumentation.

## Repository boundaries

- `apps/` owns deployable user interfaces. The Streamlit workstation joins the Python workspace.
  Containerized applications keep their Dockerfiles inside their own directories.
- `services/` owns independently deployable domain services and their business logic.
  Each service keeps its Dockerfile alongside its package manifest.
  This includes your backend API. A single backend can start in `services/api/`;
  split it into domain services when separate ownership or deployment is useful.
- `packages/` holds reusable infrastructure code or generated clients when needed.
  `packages/telemetry/` provides JSON logging, tracing exporters, and a Prometheus metrics helper;
  services explicitly opt in. See [Shared telemetry](telemetry.md) for current scope.
  Never import another service's source tree or share its persistence models.
  A package is imported by a running application; it is not deployed as its own server.
- `contracts/` owns reviewed HTTP and event interfaces, including versioning rules.
- `infra/` holds the optional local telemetry stack and its supporting configurations.
  See [local Docker setup](orders-docker.md).
- `infrastructure/` holds local orchestration configuration. Add deployment
  configuration here when a target environment is chosen.
- `tests/` is reserved for cross-service workflows. Service tests remain local.

## Proposed domain services

The following seven directories define the target boundaries, not implemented
business functionality. Only market data, orders, and fraud have runnable scaffolds.
Keep the remaining services as documentation placeholders until their first workflow.

- **Market data:** ingest synthetic prices first; normalize symbols and timestamps.
- **Orders:** own order state, validation, idempotency, and cancellation.
- **Execution simulator:** produce reproducible simulated fills and execution results
  without connecting to a real broker.
- **Portfolio:** derive positions, valuations, and profit and loss from fills and prices.
  The ledger owns the authoritative accounting record.
- **Ledger:** account for transactions with balanced, auditable entries and idempotent
  posting. Own accounting records rather than payment orchestration or fraud decisions.
- **Payments:** create and manage transactions, including identifiers, state changes,
  idempotency, and completion.
- **Fraud:** assess transactions and return explainable decisions. Start with rules;
  optionally consume model scores from a future `atlas-ml` component.

Payments creates and manages the transaction; fraud assesses it; the ledger accounts
for it. These are separate responsibilities. Fraud does not require an ML component
to make rules-based decisions. No transaction processing or rules exist yet.

Use an identity provider for user identity and service credentials when authentication
is needed. Add a gateway or backend for the frontend only when it simplifies actual
client workflows.

## Proposed data flow

For simulated trading, the trader interface submits an order to orders. Orders applies
validation and risk controls before the execution simulator produces fills. Portfolio
consumes fills and market prices to derive positions and valuation. Accounting effects
belong to the ledger rather than a separate portfolio cash ledger.

For payments, payments creates a transaction and requests an assessment from fraud.
Fraud returns a decision; payments owns the resulting transaction state and processing.
The ledger accounts for completed transactions through a versioned posting contract.
Define exact states and posting triggers during implementation. Deduplicate ledger
postings by stable transaction identifiers. A fraud decision itself is not a posting.

Start with synchronous HTTP for commands and queries. Add a durable event broker when
the first asynchronous consumer exists. Kafka-compatible infrastructure is a candidate
for replayable trading events, but no broker is selected or deployed yet.

Services own their data and migrations. Local development may share a PostgreSQL
instance with separate databases and credentials. No service reads or writes another
service's tables. Use explicit APIs, events, and read models for data exchange.

When adding asynchronous writes, use a transactional outbox, consumer idempotency,
bounded retries, and a dead-letter recovery procedure. Assume at-least-once delivery;
do not promise exactly-once processing across services. Include correlation IDs and
event versions. Represent money as decimal values with explicit currency.

## ML lifecycle

Fraud can begin with deterministic rules before any ML work. A future `atlas-ml`
component may own model training and evaluation, while fraud continues to own the
transaction assessment contract. No `atlas-ml` project is created in this repository.

The optional ML workflow separates dataset preparation, time-based feature generation,
training, evaluation, artifact promotion, and serving. Store datasets and artifacts
outside Git. Track data, feature, and model versions together. Keep preprocessing
consistent between training and inference and prevent future data leakage.

There is no separate ML directory. Give training its own project and environment
when introduced. Keep heavy training dependencies out of the fraud runtime.

Begin with rules and an interpretable tabular baseline using synthetic data. Measure
precision, recall, false positive rate, drift, and latency. Introduce shadow scoring
and human review before automated blocking. Inference should identify its model version
and report readiness only after the approved model and feature configuration load.

## Delivery and operations

Current CI checks the complete Python workspace, service HTTP tests, Compose syntax,
and a strict TechDocs build. The local Compose stack runs only the three HTTP scaffolds. It
does not provision storage or deploy to a cluster.

As workflows grow, add contract and cross-service tests, automated image publishing, request
tracing, structured logs, metrics, and documented rollback procedures. Introduce
affected-service CI only when full checks become slow. Add Kubernetes and GitOps
configuration when there is a working service to deploy and operate.
