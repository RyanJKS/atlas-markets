# Changelog

Record notable changes here. Group release entries under Added, Changed, Fixed, and Removed as needed.

## Unreleased

### Added

- Documentation placeholders for execution simulator, portfolio, ledger, and payments,
  with separate transaction management, fraud assessment, and accounting responsibilities.
- A runnable orders scaffold with its own package, entry point, HTTP test, and container.
- Shared `atlas-telemetry` package with JSON logs, OpenTelemetry trace correlation,
  batched OTLP/HTTP trace export, in-memory exporter tests, and a setup guide.
- Initial repository scaffold with Python entry point, CI, and development conventions.
- UV monorepo workspace with independently packaged market data and fraud detection
  HTTP scaffolds, service tests, local container builds, and Compose health checks.
- Boundaries for user applications, shared packages, contracts, and
  cross-service tests; architecture, development, and incremental delivery guides.

### Changed

- Renamed the fraud scaffold to `services/fraud/`, distribution `atlas-fraud`, and
  import package `atlas_fraud`; updated Compose and development commands.
- Fixed the orders package and container configuration, included it in the shared
  lockfile, and excluded documentation-only placeholders from the Python workspace.
- Each service owns its Dockerfile; Compose references service-local image definitions.
- The root README explains folder roles and where to place the initial backend API.
- Replaced the hello-world entry point with service-local source trees.
- CI uses locked workspace dependencies, runs service tests, validates Compose, and
  builds TechDocs with strict checks instead of referencing a missing requirements file.
