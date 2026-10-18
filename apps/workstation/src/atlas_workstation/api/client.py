"""Small HTTP client with bounded timeouts and inspectable results."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

import httpx
from opentelemetry.propagate import inject
from opentelemetry.trace import SpanKind, StatusCode, Tracer

from atlas_workstation.telemetry import get_tracer


@dataclass(frozen=True)
class ApiResult:
    method: str
    url: str
    timestamp: str
    elapsed_ms: float
    trace_id: str
    status_code: int | None = None
    request_body: dict[str, Any] | None = None
    body: Any = None
    headers: dict[str, str] = field(default_factory=dict)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status_code is not None and 200 <= self.status_code < 300


@dataclass(frozen=True)
class ApiClient:
    base_url: str
    timeout: float = 5.0
    transport: httpx.BaseTransport | None = field(default=None, repr=False)
    tracer: Tracer = field(default_factory=get_tracer, repr=False, compare=False)

    def __post_init__(self) -> None:
        try:
            url = httpx.URL(self.base_url)
        except httpx.InvalidURL as error:
            raise ValueError(f"Invalid service URL: {error}") from error
        if url.scheme not in {"http", "https"} or not url.host or url.userinfo:
            raise ValueError("Use an HTTP(S) service URL without credentials")
        if url.query or url.fragment:
            raise ValueError("Service URLs must not include a query or fragment")
        if not 0 < self.timeout <= 30:
            raise ValueError("Timeout must be greater than 0 and at most 30 seconds")

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
    ) -> ApiResult:
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("API paths must start with a single slash")
        url = self.base_url.rstrip("/") + path
        timestamp = datetime.now(UTC).isoformat()
        started = perf_counter()
        target = httpx.URL(url)
        with self.tracer.start_as_current_span(
            method,
            kind=SpanKind.CLIENT,
            attributes={
                "http.request.method": method,
                "server.address": target.host,
                "server.port": target.port or (443 if target.scheme == "https" else 80),
                "url.full": url,
            },
        ) as span:
            trace_id = format(span.get_span_context().trace_id, "032x")
            headers: dict[str, str] = {}
            inject(headers)
            try:
                with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
                    response = client.request(method, url, json=body, headers=headers)
                span.set_attribute("http.response.status_code", response.status_code)
                if response.status_code >= 400:
                    span.set_status(StatusCode.ERROR)
                try:
                    content = response.json()
                except ValueError:
                    content = response.text
                return ApiResult(
                    method=method,
                    url=url,
                    timestamp=timestamp,
                    elapsed_ms=(perf_counter() - started) * 1000,
                    trace_id=trace_id,
                    status_code=response.status_code,
                    request_body=body,
                    body=content,
                    headers=dict(response.headers),
                )
            except httpx.RequestError as error:
                span.record_exception(error)
                span.set_status(StatusCode.ERROR, str(error))
                span.set_attribute("error.type", type(error).__name__)
                return ApiResult(
                    method=method,
                    url=url,
                    timestamp=timestamp,
                    elapsed_ms=(perf_counter() - started) * 1000,
                    trace_id=trace_id,
                    request_body=body,
                    error=str(error),
                )
