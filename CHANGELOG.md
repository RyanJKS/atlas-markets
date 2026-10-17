# Changelog

Record notable changes here. Group release entries under Added, Changed, Fixed, and Removed as needed.

## Unreleased

### Added

- Local telemetry Compose stack under `infra/` with provisioned Grafana data
  sources, Prometheus scraping, Alloy log collection and trace fan-out, Loki,
  Jaeger, and Tempo; named volumes preserve supported local backend data.

- Prometheus metrics helper and orders `/metrics/` endpoint with a counter for
  `/random` requests; optional Azure Application Insights trace export configured
  through `OBSERVABILITY_AZURE_CONNECTION_STRING`.

- Orders application factory with startup logging, console tracing around
  `/random`, tracing provider shutdown, and a startup readiness probe.
- Documentation placeholders for execution simulator, portfolio, ledger, and payments,
  with separate transaction management, fraud assessment, and accounting responsibilities.
- A runnable orders scaffold with its own package, entry point, HTTP test, and container.
- Small shared `atlas-telemetry` package with JSON logging and a basic OpenTelemetry
  tracing helper with console output and optional OTLP/HTTP export; logs include
  trace/span IDs inside active spans. Remote log export remains a future step.
- Initial repository scaffold with Python entry point, CI, and development conventions.
- UV monorepo workspace with independently packaged market data and fraud detection
  HTTP scaffolds, service tests, local container builds, and Compose health checks.
- Boundaries for user applications, shared packages, contracts, and
  cross-service tests; architecture, development, and incremental delivery guides.

### Changed

- Orders centralizes settings and runtime instruments in typed application state
  defined in `app/state.py`; lifecycle cleanup clears telemetry after shutdown.

- Orders always initializes console logging and tracing. The optional
  `OBSERVABILITY_TRACES_ENDPOINT` replaces the logging enable/disable flag and
  adds remote span export.

- Orders settings also read the service's UTF-8 `.env` file, with process
  environment taking precedence; nested dotenv files are excluded from images.

- Orders now composes `AppSettings` and `ObservabilitySettings` into `Settings`, with
  a cached Pydantic Settings loader for `APP_*` and `OBSERVABILITY_*` environment values.
- Renamed the fraud scaffold to `services/fraud/`, distribution `atlas-fraud`, and
  import package `atlas_fraud`; updated Compose and development commands.
- Fixed the orders package and container configuration, included it in the shared
  lockfile, and excluded documentation-only placeholders from the Python workspace.
- Each service owns its Dockerfile; Compose references service-local image definitions.
- The root README explains folder roles and where to place the initial backend API.
- Replaced the hello-world entry point with service-local source trees.
- CI uses locked workspace dependencies, runs service tests, validates Compose, and
  builds TechDocs with strict checks instead of referencing a missing requirements file.
