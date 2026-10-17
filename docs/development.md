# Development

## Install the workspace

Use Python 3.12 and UV. CI and container builds pin UV 0.7.13. Run commands from the
repository root unless stated otherwise.

```sh
uv sync --locked --all-packages
uv run pre-commit install
```

UV creates `.venv/` and installs both service packages in editable mode. No manual
activation is required. After changing a dependency manifest, run `uv lock`, then
`uv sync --locked --all-packages`, and commit the updated lockfile.

## Run services

Start each command in its own terminal:

```sh
uv run --package atlas-market-data uvicorn atlas_market_data.main:app --reload --port 8001
uv run --package atlas-fraud-detection uvicorn atlas_fraud_detection.main:app --reload --port 8002
```

Check `http://localhost:8001/health` and `http://localhost:8002/health`. Each returns
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

Each service owns its Dockerfile: `services/market-data/Dockerfile` and
`services/fraud-detection/Dockerfile`. The build context remains the repository root
so builds can access the shared lockfile and workspace manifests. Each Dockerfile
selects its service package and entry point. Runtime processes run as a non-root user.
Only ports 8001 and 8002 are published, bound to `127.0.0.1`. No runtime secrets or
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
5. Add a Dockerfile inside the service directory with its package name and module path.
   Add a Compose service pointing to that Dockerfile, using the repository root as its
   build context and a unique local port. Containerized frontends likewise keep their
   Dockerfiles inside their own directories under `apps/`.
   Add contract definitions when business endpoints or events exist.
6. Update architecture and operations documentation, then run the checks above.

If a service needs a different language or incompatible Python dependencies, give it
its own native tooling and CI checks. The monorepo layout does not require every
service to join the Python workspace. If fraud training is added, place it beside the
fraud service under `services/fraud-detection/training/` with its own environment.
Keep training dependencies out of the inference service's runtime dependencies.
