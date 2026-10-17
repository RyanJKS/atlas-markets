# Service boundaries

The service directories describe planned ownership. Only market data, orders, and
fraud currently have runnable HTTP scaffolds; each exposes process liveness only.
The other four directories contain documentation placeholders, not implementations.

```text
services/
├── market-data/
├── orders/
├── execution-simulator/
├── portfolio/
├── ledger/
├── payments/
└── fraud/
```

- **Market data:** owns synthetic price ingestion and normalized market observations.
- **Orders:** owns order requests, validation, lifecycle, and cancellation.
- **Execution simulator:** simulates fills without connecting to a real broker.
- **Portfolio:** derives positions, valuation, and profit and loss from fills and prices.
- **Ledger:** owns balanced accounting entries and the authoritative accounting record.
- **Payments:** creates and manages transactions and their lifecycle.
- **Fraud:** assesses transactions, initially using rules. It can later use model scores.

Payments creates and manages the transaction; fraud assesses it; the ledger accounts
for it. Fraud does not own payment state or ledger entries. Portfolio does not own
the authoritative cash ledger. A future `atlas-ml` component is optional: fraud can
assess transactions with deterministic rules before machine learning exists.

These boundaries are a design, not implemented transaction flows. There are no payment
APIs, fraud decisions, accounting entries, execution simulations, or databases yet.

## Turn a placeholder into a service

Add its own manifest, `src/atlas_<name>/` package, tests, and Dockerfile. Remove the
directory from the root UV workspace `exclude` list, update `uv.lock`, and add a
Compose entry when it can run. Keep the Dockerfile beside the service's manifest.
See the [development guide](../docs/development.md#add-a-service) for the full procedure.
