# Fraud

Planned responsibility: assess transactions and return explainable decisions.
Start with deterministic rules; a future `atlas-ml` component can supply model scores
when useful. Fraud assessment does not require machine learning.

Payments creates and manages transactions. Fraud assesses them. The ledger accounts
for them. Fraud does not own payment state or accounting entries.

Current implementation: a FastAPI scaffold with `GET /health`, `/docs`, and
`/openapi.json`. No assessment routes, rules, or model scoring are implemented yet.

From the repository root:

```sh
uv run --package atlas-fraud uvicorn atlas_fraud.main:app --reload --port 8002
```

The distribution is `atlas-fraud`; the import package is `atlas_fraud`.
The service owns its Dockerfile, source, and HTTP test. See
[service boundaries](../README.md) for the wider design.
