# Shared Python packages

Add small, independently named Python packages here when multiple services need the
same infrastructure code. Examples include telemetry setup and generated API clients.
Each package needs its own `pyproject.toml`, `src/` directory, and tests.

Consumers declare the dependency in their manifest and add a UV workspace source:

```toml
[tool.uv.sources]
atlas-example = { workspace = true }
```

Do not place trading rules, persistence models, or service implementations here. Keep
business logic inside its owning service. No shared package is implemented yet.
