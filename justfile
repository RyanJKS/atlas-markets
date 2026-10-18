run-order:
  mkdir -p infrastructure/telemetry/logs
  # uv run --package atlas-orders uvicorn atlas_orders.main:app --reload --port 8003
  uv run --package atlas-orders uvicorn atlas_orders.main:app \
  --reload --host 0.0.0.0 --port 8003 \
  2>> infrastructure/telemetry/logs/orders.log

run-workstation:
  uv run --package atlas-workstation streamlit run apps/workstation/streamlit_app.py
