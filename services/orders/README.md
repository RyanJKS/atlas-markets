# Orders

Planned responsibility: own order requests, validation, state transitions, and
cancellation. Execution simulation belongs to `execution-simulator/`.

Current implementation: a FastAPI scaffold with `GET /health`, `/docs`, and
`/openapi.json`. There are no order routes, storage, or trading workflows yet.

From the repository root:

```sh
uv run --package atlas-orders uvicorn atlas_orders.main:app --reload --port 8003
```

The distribution is `atlas-orders`; the import package is `atlas_orders`.
The service owns its Dockerfile, source, and HTTP test. See
[service boundaries](../README.md) for the wider design.
