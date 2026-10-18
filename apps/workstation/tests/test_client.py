"""Verify transport failures, HTTP errors, payloads, and trace propagation."""

import json

import httpx
import pytest
from atlas_workstation.api.client import ApiClient
from atlas_workstation.api.orders import OrdersClient


def test_order_client_sends_payload_and_traceparent() -> None:
    ticket = {"symbol": "AAPL", "side": "buy", "quantity": 10}
    captured = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        assert json.loads(request.content) == ticket
        return httpx.Response(200, json={"status": "simulated"})

    client = OrdersClient(ApiClient("http://orders.test", transport=httpx.MockTransport(handler)))
    result = client.simulate_order(ticket)
    assert result.ok
    assert result.url == "http://orders.test/orders/v1/orders"
    assert result.request_body == ticket
    assert result.body == {"status": "simulated"}
    assert captured[0].headers["traceparent"].split("-")[1] == result.trace_id


def test_http_error_keeps_response_for_inspection() -> None:
    client = ApiClient(
        "http://orders.test",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(422, json={"detail": "Invalid ticket"}),
        ),
    )
    result = client.request("POST", "/orders/v1/orders", body={})
    assert not result.ok
    assert result.status_code == 422
    assert result.body == {"detail": "Invalid ticket"}
    assert result.error is None


def test_connection_failure_is_a_result() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused", request=request)

    result = ApiClient("http://orders.test", transport=httpx.MockTransport(handler)).request(
        "GET", "/health"
    )
    assert not result.ok
    assert result.status_code is None
    assert result.error == "Connection refused"


def test_metrics_response_stays_text() -> None:
    result = ApiClient(
        "http://orders.test",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, text="orders_http_requests_total 1\n"),
        ),
    ).request("GET", "/metrics/")
    assert result.ok
    assert result.body == "orders_http_requests_total 1\n"


@pytest.mark.parametrize(
    "url",
    [
        "ftp://orders.test",
        "http://",
        "http://user:pass@orders.test",
        "http://orders.test?q=1",
        "http://orders.test:invalid",
    ],
)
def test_invalid_service_urls_are_rejected(url: str) -> None:
    with pytest.raises(ValueError):
        ApiClient(url)
