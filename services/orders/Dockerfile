FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app
RUN pip install --no-cache-dir uv==0.7.13
COPY pyproject.toml uv.lock ./
COPY services/ ./services/
COPY packages/ ./packages/
RUN uv sync --locked --no-dev --package atlas-orders \
    && useradd --system --uid 10001 atlas
USER atlas
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "atlas_orders.main:app", "--host", "0.0.0.0", "--port", "8000"]
