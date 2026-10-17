# Atlas Markets

Atlas Markets is an experimental monorepo for a hedge fund simulation, including
market data, trade execution, portfolio accounting, risk, and fraud detection.

The repository currently provides two independent Python service scaffolds, a shared
development workspace, local container definitions, tests, and CI. Each service exposes
`GET /health` and generated API documentation. No financial workflow or ML model is
implemented yet.

- Read [Architecture](architecture.md) for current components and proposed boundaries.
- Follow [Development](development.md) to install, run, check, and extend the workspace.
- Use the [Roadmap](roadmap.md) to build a complete simulated workflow incrementally.

These pages are published through Backstage TechDocs. The catalog descriptor keeps
its documentation reference at the repository root, beside `mkdocs.yml`.
