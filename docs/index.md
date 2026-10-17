# Atlas Markets

Atlas Markets is an experimental monorepo for a hedge fund simulation, including
market data, trade execution, portfolio accounting, risk, and fraud detection.

The repository currently provides three independent Python service scaffolds, a shared
development workspace, local container definitions, tests, and CI. Each service exposes
`GET /health` and generated API documentation. No financial workflow or ML model is
implemented yet.

Market data, orders, and fraud have runnable scaffolds. Execution simulator, portfolio,
ledger, and payments contain documentation placeholders only. Payments will create and
manage transactions; fraud will assess them; the ledger will account for them. Fraud
can begin with rules before a future `atlas-ml` component exists.

- Read [Architecture](architecture.md) for current components and proposed boundaries.
- Follow [Development](development.md) to install, run, check, and extend the workspace.
- Use [Orders configuration](orders-configuration.md) for nested settings and environment overrides.
- Read [Shared telemetry](telemetry.md) for logging, trace export, and Prometheus metrics.
- Use the [Roadmap](roadmap.md) to build a complete simulated workflow incrementally.

These pages are published through Backstage TechDocs. The catalog descriptor keeps
its documentation reference at the repository root, beside `mkdocs.yml`.
