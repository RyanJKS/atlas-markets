# Changelog

Record notable changes here. Group release entries under Added, Changed, Fixed, and Removed as needed.

## Unreleased

### Added

- Initial repository scaffold with Python entry point, CI, and development conventions.
- UV monorepo workspace with independently packaged market data and fraud detection
  HTTP scaffolds, service tests, local container builds, and Compose health checks.
- Boundaries for user applications, shared packages, contracts, and
  cross-service tests; architecture, development, and incremental delivery guides.

### Changed

- Each service owns its Dockerfile; Compose references service-local image definitions.
- The root README explains folder roles and where to place the initial backend API.
- Replaced the hello-world entry point with service-local source trees.
- CI uses locked workspace dependencies, runs service tests, validates Compose, and
  builds TechDocs with strict checks instead of referencing a missing requirements file.
