"""Process-owned tracing reused across Streamlit reruns and browser sessions."""

import atexit
from functools import cache

import httpx
from atlas_telemetry import configure_tracing
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import Tracer

from atlas_workstation.config import environment_value


@cache
def _create_provider(service_name: str, endpoint: str | None) -> TracerProvider:
    provider = configure_tracing(service_name, endpoint=endpoint)
    atexit.register(provider.shutdown)
    return provider


def get_tracing_provider() -> TracerProvider:
    service_name = (environment_value("APP_SERVICE_NAME", "workstation") or "").strip()
    if not service_name:
        raise ValueError("APP_SERVICE_NAME must not be empty")
    endpoint = (environment_value("OBSERVABILITY_TRACES_ENDPOINT") or "").strip() or None
    if endpoint is not None:
        try:
            url = httpx.URL(endpoint)
        except httpx.InvalidURL as error:
            raise ValueError("Invalid OBSERVABILITY_TRACES_ENDPOINT") from error
        if url.scheme not in {"http", "https"} or not url.host:
            raise ValueError("OBSERVABILITY_TRACES_ENDPOINT must be an HTTP(S) URL")
    return _create_provider(service_name, endpoint)


def get_tracer() -> Tracer:
    return get_tracing_provider().get_tracer("atlas_workstation")
