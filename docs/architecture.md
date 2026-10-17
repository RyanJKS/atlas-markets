# Architecture

## Current implementation

Atlas Markets uses a UV workspace for Python 3.12 services. Each service has its own
`pyproject.toml`, uniquely named import package, `src/` tree, tests, and Dockerfile. A root
`uv.lock` resolves dependencies together; a container installs only its selected
service and its dependencies. This enforces dependency compatibility within the
Python workspace. A service needing incompatible dependencies must use a separate
project and lockfile instead.

Two FastAPI service scaffolds exist:

- `services/market-data/`: `atlas-market-data`, served locally on port 8001.
- `services/fraud-detection/`: `atlas-fraud-detection`, served locally on port 8002.

Both expose `GET /health`, `/docs`, and `/openapi.json`. Health checks indicate that
the process responds; they do not indicate feed availability or model readiness.
There are no databases, event brokers, market feeds, trained models, scoring routes,
authentication mechanisms, or service-to-service calls yet. Local containers bind to
loopback only. These scaffolds are not configured for public deployment.

## Repository boundaries

- `apps/` owns deployable user interfaces. Add frontend tooling when a frontend exists.
  Containerized applications keep their Dockerfiles inside their own directories.
- `services/` owns independently deployable domain services and their business logic.
  Each service keeps its Dockerfile alongside its package manifest.
  This includes your backend API. A single backend can start in `services/api/`;
  split it into domain services when separate ownership or deployment is useful.
- `packages/` holds reusable infrastructure code or generated clients when needed.
  Never import another service's source tree or share its persistence models.
  A package is imported by a running application; it is not deployed as its own server.
- `contracts/` owns reviewed HTTP and event interfaces, including versioning rules.
- `infrastructure/` holds local orchestration configuration. Add deployment
  configuration here when a target environment is chosen.
- `tests/` is reserved for cross-service workflows. Service tests remain local.

## Proposed domain services

The following boundaries are a target design, not implemented functionality. Add a
service when its first workflow exists rather than creating many empty deployments.

- **Market data:** ingest synthetic prices first; normalize symbols and timestamps.
- **Order management:** own order state, validation, idempotency, and cancellation.
- **Execution:** simulate broker fills and publish execution results. Add external
  adapters only after simulated execution works.
- **Portfolio:** own positions, cash, and an auditable transaction ledger; reconcile
  fills and calculate profit and loss.
- **Risk:** calculate exposure and enforce deterministic pre-trade limits. Keep this
  decision path distinct from asynchronous fraud analysis.
- **Fraud detection:** score versioned trade features and emit suspicious-activity
  decisions with model version and explanation metadata.
- **Compliance:** own review cases, dispositions, and access to the audit history.
- **Strategy:** generate proposed orders from research signals through the same order
  and risk controls as a user.

Use an identity provider for user identity and service credentials when authentication
is needed. Add a gateway or backend for the frontend only when it simplifies actual
client workflows.

## Proposed data flow

The trader interface submits an order to order management. Order management obtains a
risk decision before execution accepts the order. Execution publishes fills. Portfolio
consumes fills and records positions and cash. Fraud detection evaluates trade events
asynchronously and sends suspicious cases to compliance. Market data supplies prices
to strategy, risk, and portfolio valuation.

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

The target fraud workflow separates dataset preparation, time-based feature generation,
training, evaluation, artifact promotion, and serving. Store datasets and artifacts
outside Git. Track data, feature, and model versions together. Keep preprocessing
consistent between training and inference and prevent future data leakage.

There is no separate ML directory. When training exists, start beside the fraud
service under `services/fraud-detection/training/`, using a separate project and
environment for heavy training dependencies. Inference keeps its own small runtime.

Begin with rules and an interpretable tabular baseline using synthetic data. Measure
precision, recall, false positive rate, drift, and latency. Introduce shadow scoring
and human review before automated blocking. Inference should identify its model version
and report readiness only after the approved model and feature configuration load.

## Delivery and operations

Current CI checks the complete Python workspace, service HTTP tests, Compose syntax,
and a strict TechDocs build. The local Compose stack runs only the two scaffolds. It
does not provision storage or deploy to a cluster.

As workflows grow, add contract and cross-service tests, automated image publishing, request
tracing, structured logs, metrics, and documented rollback procedures. Introduce
affected-service CI only when full checks become slow. Add Kubernetes and GitOps
configuration when there is a working service to deploy and operate.
