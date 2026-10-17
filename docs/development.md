# Development

## Install the workspace

Use Python 3.12 and UV. CI and container builds pin UV 0.7.13. Run commands from the
repository root unless stated otherwise.

```sh
uv sync --locked --all-packages
uv run pre-commit install
```

UV creates `.venv/` and installs the three service packages and shared telemetry
library in editable mode. The four documentation-only service placeholders are excluded
from the workspace. No manual
activation is required. After changing a dependency manifest, run `uv lock`, then
`uv sync --locked --all-packages`, and commit the updated lockfile.

## Python package layout

Each Python service uses a named package inside `src/`. For example:

```text
services/market-data/          Service project directory
  pyproject.toml              Dependencies and build settings
  Dockerfile                  Service image definition
  src/                        Source root, not part of the import name
    atlas_market_data/        Importable Python package
      __init__.py
      main.py                 HTTP entry point
  tests/                      Service tests
```

The inner `atlas_market_data/` directory gives the service a unique Python namespace:

```python
from atlas_market_data.main import app
```

Other services can also have a `main.py` without competing for a generic `main`
module name. Code directly inside `src/main.py` can work for a standalone script;
this workspace uses named, installable packages so services can coexist in the same
development environment. The `src/` layout also keeps imports separate from the
project directory, helping checks exercise the installed package.

The service's `pyproject.toml` configures Hatchling, its Python build backend:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/atlas_market_data"]
```

This setting tells Hatchling which source directory to include in the wheel, an
installable Python package archive. The path is relative to the service's project
directory. The installed package is named `atlas_market_data`; `src/` is not part
of the import path. Uvicorn therefore loads `atlas_market_data.main:app`.

The distribution name in `[project]` is `atlas-market-data`, used by package tools
and `uv run --package atlas-market-data`. The Python import name uses underscores:
`atlas_market_data`. Match the wheel's package path to the actual source directory.

### Build setting versus shared packages directory

The word "package" appears in three places with different roles:

- `src/atlas_market_data/` is an importable Python package containing the market
  data service's code. Its location inside a service does not make it a shared library.
- `packages = ["src/atlas_market_data"]` is a Hatchling build setting. It selects
  source to include when building that one Python project. It does not refer to,
  create, or copy the repository's top-level `packages/` directory.
- The top-level `packages/` directory groups shared library projects used by multiple
  apps or services. Each library has its own manifest, dependencies, tests, and import
  package. These libraries do not run as standalone servers.

For example, the shared telemetry library sits beside the market data service:

```text
services/market-data/
  pyproject.toml              Builds the market data service package
  src/atlas_market_data/      Service code, imported as atlas_market_data
packages/telemetry/           Shared logging and OpenTelemetry library
  pyproject.toml              Builds the telemetry library package
  src/atlas_telemetry/        Shared code, imported as atlas_telemetry
```

The telemetry library also uses Hatchling; its own manifest selects
`packages = ["src/atlas_telemetry"]`. Both projects contain Python packages, but
their repository locations describe their roles: a running backend in `services/`,
or an imported shared library in `packages/`.

A service must explicitly declare a shared library as a dependency and configure its
UV workspace source. Placing code under `packages/` does not automatically make it
a dependency of every service. Keep service business logic in its owning service.
See [Shared telemetry](telemetry.md) for the implemented library and usage examples.

## Run services

Start each command in its own terminal:

```sh
uv run --package atlas-market-data uvicorn atlas_market_data.main:app --reload --port 8001
uv run --package atlas-fraud uvicorn atlas_fraud.main:app --reload --port 8002
uv run --package atlas-orders uvicorn atlas_orders.main:app --reload --port 8003
```

Check `/health` on localhost ports 8001 (market data), 8002 (fraud), and 8003 (orders).
Each returns
its service name and `"status": "ok"`. API explorers are available at `/docs`.
Stop a process with Ctrl+C. If a port is busy, stop the existing process or select a
different `--port`. Health does not prove that a feed or model is available.

## Run containers

Install Docker with Compose v2 and start the Docker daemon.

```sh
docker compose -f infrastructure/compose.yaml config --quiet
docker compose -f infrastructure/compose.yaml up --build -d --wait
docker compose -f infrastructure/compose.yaml logs
docker compose -f infrastructure/compose.yaml down
```

Each runnable service owns its Dockerfile: `services/market-data/Dockerfile`,
`services/fraud/Dockerfile`, and `services/orders/Dockerfile`.
The build context remains the repository root
so builds can access the shared lockfile and workspace manifests. Each Dockerfile
selects its service package and entry point. Runtime processes run as a non-root user.
Only ports 8001, 8002, and 8003 are published, bound to `127.0.0.1`. No runtime secrets or
external services are required. Image builds need network access for Python packages.
If startup fails, inspect the service logs and rebuild after manifest changes.

To build one service directly, run from the repository root:

```sh
docker build -f services/market-data/Dockerfile -t atlas-market-data .
```

## Check changes

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run pre-commit run --all-files
python -m compileall -q services packages
```

Run one service's tests with `uv run pytest services/market-data/tests`. Tests use
FastAPI's HTTP client and do not require containers. Root pytest discovery uses
importlib mode so separate services can use the same test filenames.

## Build documentation

```sh
uv sync --locked --all-packages --group docs
uv run mkdocs build --strict
```

This builds TechDocs locally into ignored `site/` output. Keep `techdocs-core` enabled;
a generic MkDocs build without that plugin does not validate this configuration.
Backstage publishing and permissions are configured outside this repository.

## Add a service

1. Create `services/<domain>/pyproject.toml` with a unique distribution name such as
   `atlas-portfolio`, Python 3.12 support, runtime dependencies, and a build backend.
2. Put source under `src/atlas_<domain>/` and service tests under `tests/`. Match the
   build backend's package configuration to the import directory.
3. Keep business logic and database migrations inside the service. Declare shared
   package dependencies explicitly using UV workspace sources.
4. Run `uv lock` and `uv sync --locked --all-packages`. The root workspace discovers
   Python manifests under `services/*` and `packages/*` automatically.
   Documentation-only placeholders are listed in `[tool.uv.workspace].exclude`;
   remove a service's exclusion when adding its manifest and source package.
5. Add a Dockerfile inside the service directory with its package name and module path.
   Add a Compose service pointing to that Dockerfile, using the repository root as its
   build context and a unique local port. Containerized frontends likewise keep their
   Dockerfiles inside their own directories under `apps/`.
   Add contract definitions when business endpoints or events exist.
6. Update architecture and operations documentation, then run the checks above.

If a service needs a different language or incompatible Python dependencies, give it
its own native tooling and CI checks. The monorepo layout does not require every
service to join the Python workspace. Fraud can start with deterministic rules and
later consume scores from a future `atlas-ml` component. No ML project is created
yet. Give training its own environment when introduced, and keep training dependencies
out of the fraud service's runtime dependencies.
