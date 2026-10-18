# Cross-application tests

`test_tracing.py` exercises the Workstation HTTP client against the real Orders
FastAPI application through a test transport. The transport clears in-process
OpenTelemetry context so propagation must cross HTTP headers, as it would
between separate applications.

Tests verify shared trace IDs, client/server parent relationships, distinct
service resources, baggage propagation, successful requests, HTTP errors, health
and readiness probes, and the random demo's nested business span. A Streamlit
widget test follows the Load sample orders action through both applications.
They use in-memory exporters and need no running collector or containers.

Run from the repository root:

```sh
uv run pytest tests/test_tracing.py
```

Root pytest discovery includes this directory. Application and service unit
tests remain beside their packages. See the
[live trace guide](../docs/workstation.md#inspect-an-end-to-end-trace) to verify
exports in Jaeger and Tempo with the local telemetry stack.
