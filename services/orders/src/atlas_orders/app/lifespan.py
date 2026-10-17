"""Orders owns telemetry startup and provider shutdown."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from atlas_telemetry import configure_logging, configure_metrics, configure_tracing
from fastapi import FastAPI

from atlas_orders.app.state import TelemetryState, get_app_state


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    state = get_app_state(app)
    settings = state.settings
    configure_logging(settings.app.service_name)
    endpoint = settings.observability.traces_endpoint
    azure_connection_string = settings.observability.azure_connection_string
    provider = configure_tracing(
        settings.app.service_name,
        endpoint=str(endpoint) if endpoint is not None else None,
        azure_connection_string=(
            azure_connection_string.get_secret_value()
            if azure_connection_string is not None
            else None
        ),
    )
    try:
        meter_provider = configure_metrics(settings.app.service_name)
        try:
            meter = meter_provider.get_meter("atlas_orders")
            state.telemetry = TelemetryState(
                tracer=provider.get_tracer("atlas_orders"),
                random_requests=meter.create_counter(
                    "orders.random.requests", description="Number of random endpoint requests"
                ),
            )
            yield
        finally:
            state.telemetry = None
            meter_provider.shutdown()
    finally:
        provider.shutdown()
