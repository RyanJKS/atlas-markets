# User applications

`workstation/` is a Streamlit hedge fund sandbox for exercising Orders APIs and
inspecting request telemetry. Its UI pages, HTTP transport, service client, and
shared presentation components are separate modules. Orders use fixed fixtures;
simulated submissions are never stored or executed.

For initial setup, copy `apps/workstation/.env.example` to
`apps/workstation/.env` and set `ORDERS_API_URL`. Keep an existing `.env` file.
Process environment variables override the file; service URLs are not edited
in the UI.

The template also sets `APP_SERVICE_NAME=workstation` and
`OBSERVABILITY_TRACES_ENDPOINT=http://127.0.0.1:4318/v1/traces`. Export Orders
spans to the same collector to see connected Workstation client and Orders server
spans. See the [end-to-end trace guide](../docs/workstation.md#inspect-an-end-to-end-trace).

From the repository root, start Orders and the workstation in separate terminals:

```sh
uv run --package atlas-orders uvicorn atlas_orders.main:app --reload --port 8003
uv run --package atlas-workstation streamlit run apps/workstation/streamlit_app.py
```

Open <http://localhost:8501>. See the [workstation guide](../docs/workstation.md)
for setup, endpoints, telemetry, and adding service pages.

Python applications participate in the root UV workspace. Each application owns
its manifest, source package, and tests. Applications call service APIs; they
must not import service source code or access service databases directly.
Containerized applications keep their Dockerfiles beside their manifests.
