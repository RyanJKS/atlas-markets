# Atlas Markets

A monorepo for a hedge fund simulation: market data, trading, portfolio management,
risk, and ML-assisted fraud detection. This is an experimental learning project.
The current implementation contains two FastAPI service scaffolds with liveness
endpoints. Trading, data ingestion, model training, and scoring are not implemented.

## Folder roles

- **`apps/`** — user interfaces: trader dashboard, admin console.
- **`services/`** — independently running backends: your API, market data,
  fraud detection, and workers.
- **`packages/`** — shared libraries imported by apps or services. No standalone server.

Your API belongs in `services/api/`, with its own dependencies, source, and tests.
Start with one API; split by business domain when useful. Each containerized app or
service owns its Dockerfile beside its package manifest.

## Quick start

Install Python 3.12 and [UV](https://docs.astral.sh/uv/) (CI uses UV 0.7.13).
From the repository root:

```sh
uv sync --locked --all-packages
uv run pre-commit install
uv run --package atlas-market-data uvicorn atlas_market_data.main:app --reload --port 8001
```

In a second terminal:

```sh
uv run --package atlas-fraud-detection uvicorn atlas_fraud_detection.main:app --reload --port 8002
```

Open `http://localhost:8001/docs` or `http://localhost:8002/docs` for the API explorers.
`GET /health` reports process liveness only.

## Layout

```text
apps/                   User applications, reserved for future frontends
services/
  market-data/          Independent Python package and HTTP service scaffold
    Dockerfile          Market data image definition
  fraud-detection/      Independent Python package and HTTP service scaffold
    Dockerfile          Fraud detection image definition
packages/               Shared infrastructure packages, added when needed
contracts/              HTTP and event contract conventions
infrastructure/         Local orchestration and deployment configuration
tests/                  Future cross-service tests; unit tests live beside services
docs/                   Architecture, development, and roadmap
```

Read [architecture](docs/architecture.md) for service boundaries and the target design,
[development](docs/development.md) for checks and containers, and the
[roadmap](docs/roadmap.md) for the build order. See [CONTRIBUTING.md](CONTRIBUTING.md)
and [SECURITY.md](SECURITY.md) before contributing.

## Checks

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run pre-commit run --all-files
uv sync --locked --all-packages --group docs
uv run mkdocs build --strict
```

CI runs these checks and validates Compose configuration. Each service has its own
runtime dependencies; the root lockfile makes local development and CI reproducible.
Record notable changes in [CHANGELOG.md](CHANGELOG.md). Releases and deployments
remain manual; no workflow publishes an application.
