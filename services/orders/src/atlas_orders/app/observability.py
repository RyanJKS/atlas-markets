"""Observe service HTTP requests and continue upstream trace and baggage context."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter

from fastapi import FastAPI, Request
from opentelemetry.context import attach, detach
from opentelemetry.propagate import extract
from opentelemetry.trace import SpanKind, StatusCode
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from atlas_orders.app.state import get_app_state


@contextmanager
def _incoming_context(request: Request) -> Iterator[None]:
    token = attach(extract(request.headers))
    try:
        yield
    finally:
        detach(token)


def register_order_observability(app: FastAPI) -> None:
    logger = logging.getLogger(f"atlas.{get_app_state(app).settings.app.service_name}")

    @app.middleware("http")
    async def observe_order_request(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path == "/metrics" or request.url.path.startswith("/metrics/"):
            return await call_next(request)

        telemetry = get_app_state(app).get_telemetry()
        started = perf_counter()
        status_code = 500
        with (
            _incoming_context(request),
            telemetry.tracer.start_as_current_span(
                "orders.http.request",
                kind=SpanKind.SERVER,
            ) as span,
        ):
            try:
                response = await call_next(request)
                status_code = response.status_code
                response.headers["X-Trace-ID"] = format(span.get_span_context().trace_id, "032x")
                return response
            finally:
                route = request.scope.get("route")
                route_path = (
                    str(
                        app.url_path_for(
                            route.name,
                            **{name: f"{{{name}}}" for name in request.path_params},
                        )
                    )
                    if route is not None
                    else "unmatched"
                )
                attributes = {
                    "http.request.method": request.method,
                    "http.route": route_path,
                    "http.response.status_code": status_code,
                }
                duration = perf_counter() - started
                span.update_name(f"{request.method} {route_path}")
                span.set_attributes(attributes)
                if status_code >= 500:
                    span.set_status(StatusCode.ERROR)
                telemetry.http_requests.add(1, attributes)
                telemetry.http_duration.record(duration, attributes)
                logger.info(
                    "Orders API %s %s status=%s duration_ms=%.2f",
                    request.method,
                    route_path,
                    status_code,
                    duration * 1000,
                )
