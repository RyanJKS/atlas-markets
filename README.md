# Atlas Markets

A monorepo for a hedge fund simulation: market data, trading, portfolio management,
risk, and ML-assisted fraud detection. This is an experimental learning project.
The current implementation contains three FastAPI service scaffolds with liveness
endpoints and four documentation-only service placeholders. Trading, payment processing,
accounting, fraud rules, data ingestion, model training, and scoring are not implemented.

## Folder roles

- **`apps/`** — user interfaces: trader dashboard, admin console.
- **`services/`** — independently running backends: your API, market data,
  fraud detection, and workers.
- **`packages/`** — shared libraries imported by apps or services. No standalone server.

Your API belongs in `services/api/`, with its own dependencies, source, and tests.
Start with one API; split by business domain when useful. Each containerized app or
service owns its Dockerfile beside its package manifest.

See [Python package layout](docs/development.md#python-package-layout) for why services
use `src/<package>/` and what the `packages` setting in `pyproject.toml` means.
That build setting selects source for one Python project; the top-level `packages/`
directory groups reusable library projects.

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
uv run --package atlas-fraud uvicorn atlas_fraud.main:app --reload --port 8002
```

Orders runs with `uv run --package atlas-orders uvicorn atlas_orders.main:app --reload --port 8003`.
Open `/docs` on ports 8001 (market data), 8002 (fraud), or 8003 (orders) for the API explorers.
`GET /health` reports process liveness only.

## Layout

```text
apps/                   User applications, reserved for future frontends
services/
  market-data/          Runnable HTTP scaffold
  orders/               Runnable HTTP scaffold
  execution-simulator/  Documentation placeholder
  portfolio/            Documentation placeholder
  ledger/               Documentation placeholder
  payments/             Documentation placeholder
  fraud/                Runnable HTTP scaffold
packages/
  telemetry/            Shared JSON logging and OpenTelemetry tracing
contracts/              HTTP and event contract conventions
infrastructure/         Local orchestration and deployment configuration
tests/                  Future cross-service tests; unit tests live beside services
docs/                   Architecture, development, and roadmap
```

Payments creates and manages the transaction; fraud assesses it; the ledger accounts
for it. These are separate responsibilities. Fraud can start with deterministic rules
before a future `atlas-ml` component exists. See [service boundaries](services/README.md)
for ownership and placeholder status. The four documentation-only services are excluded
from the Python workspace until implementation starts.

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

See [Shared telemetry](docs/telemetry.md) to adopt the logging and OpenTelemetry
library. Services opt in explicitly; a collector is not deployed by this repository.
