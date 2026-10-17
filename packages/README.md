# Shared Python packages

Add small, independently named Python packages here when multiple services need the
same infrastructure code. Examples include telemetry setup and generated API clients.
Each package needs its own `pyproject.toml`, `src/` directory, and tests.

This directory groups shared library projects. It is not the same as Hatchling's
`packages = ["src/<name>"]` build setting, which selects source inside one Python
project. A service under `services/` also contains an importable Python package;
that does not make the service a shared library. See
[the package layout guide](../docs/development.md#build-setting-versus-shared-packages-directory)
for examples of all three meanings.

The first shared library is [`telemetry/`](telemetry/README.md): JSON logging with
OpenTelemetry trace correlation and explicit OTLP/HTTP trace setup. For example:

```python
from atlas_telemetry import configure_logging

logger = configure_logging("market-data")
logger.info("Market data service started")
```

Consumers declare the dependency in their manifest and add a UV workspace source:

```toml
[tool.uv.sources]
atlas-telemetry = { workspace = true }
```

Do not place trading rules, persistence models, or service implementations here. Keep
business logic inside its owning service. See the
[telemetry guide](../docs/telemetry.md) for setup and current limits.
