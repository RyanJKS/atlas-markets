# Atlas Telemetry

Shared JSON logging and OpenTelemetry tracing for Python applications and services.
The distribution is `atlas-telemetry`; the import package is `atlas_telemetry`.
This library is imported into a process and does not run as a separate service.

```python
from atlas_telemetry import configure_logging

logger = configure_logging("market-data")
logger.info("Market data service started")
```

`configure_logging` returns an `atlas.<service-name>` logger that writes JSON to stderr.
Logs include the active OpenTelemetry trace and span IDs when a span exists. The
root logger and framework access loggers are unchanged. Calling setup again for the
same service reuses the library's handler.

`create_tracer_provider` creates a provider with batched OTLP/HTTP trace export. The
application explicitly registers the provider once and shuts it down on process exit.
Importing the library or configuring logging does not start an exporter.

See the [telemetry guide](../../docs/telemetry.md) for dependency declarations,
collector configuration, tracing examples, lifecycle ownership, and current limits.
