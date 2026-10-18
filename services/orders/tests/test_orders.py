"""Exercise sample contracts, no persistence, and correlated API telemetry."""

import json
from io import StringIO

import pytest
from atlas_orders.app.bootstrap import create_app
from atlas_orders.core.config.settings import AppSettings, Settings
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from prometheus_client.parser import text_string_to_metric_families

PATH = "/orders/v1/orders"
TICKET = {"symbol": "AAPL", "side": "buy", "quantity": 10, "order_type": "market"}


def test_sample_orders_and_stateless_acknowledgement() -> None:
    with TestClient(create_app(Settings())) as client:
        original = client.get(PATH)
        assert original.status_code == 200
        assert len(original.json()) == 3
        sample = original.json()[0]
        assert client.get(f"{PATH}/{sample['id']}").json() == sample
        response = client.post(PATH, json=TICKET)
        assert response.status_code == 200
        assert response.json()["status"] == "simulated"
        assert response.json()["quantity"] == 10
        assert client.get(f"{PATH}/{response.json()['id']}").status_code == 404
        assert client.get(PATH).json() == original.json()
        assert client.get("/orders/v1/order?id=42").json() == "This is the details for order 42"


@pytest.mark.parametrize(
    "changes",
    [
        {"quantity": 0},
        {"quantity": 1.5},
        {"quantity": True},
        {"symbol": "bad symbol"},
        {"side": "hold"},
        {"currency": "BTC"},
        {"order_type": "limit"},
        {"limit_price": "1.00"},
        {"order_type": "limit", "limit_price": "-1.00"},
        {"order_type": "limit", "limit_price": "1.001"},
    ],
)
def test_invalid_tickets_return_validation_errors(changes: dict) -> None:
    with TestClient(create_app(Settings())) as client:
        assert client.post(PATH, json=TICKET | changes).status_code == 422


def test_limit_order_uses_decimal_price() -> None:
    with TestClient(create_app(Settings())) as client:
        response = client.post(PATH, json=TICKET | {"order_type": "limit", "limit_price": "12.34"})
        assert response.status_code == 200
        assert response.json()["limit_price"] == "12.34"


def test_order_requests_propagate_trace_context_and_record_metrics(
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    spans = StringIO()
    monkeypatch.setattr(
        "atlas_telemetry.tracing.ConsoleSpanExporter",
        lambda: ConsoleSpanExporter(out=spans),
    )
    trace_id = "1234567890abcdef1234567890abcdef"
    parent_id = "1234567890abcdef"
    with TestClient(
        create_app(Settings(app=AppSettings(service_name="orders-request-test")))
    ) as client:
        response = client.get(
            f"{PATH}/missing",
            headers={"traceparent": f"00-{trace_id}-{parent_id}-01"},
        )
        assert response.status_code == 404
        assert response.headers["X-Trace-ID"] == trace_id
        metrics = client.get("/metrics/").text
    span = json.loads(spans.getvalue())
    assert span["context"]["trace_id"] == f"0x{trace_id}"
    assert span["parent_id"] == f"0x{parent_id}"
    assert span["attributes"]["http.route"] == f"{PATH}/{{order_id}}"
    assert span["attributes"]["http.response.status_code"] == 404
    samples = [
        sample for family in text_string_to_metric_families(metrics) for sample in family.samples
    ]
    for name in ("orders_http_requests_total", "orders_http_duration_seconds_count"):
        sample = next(sample for sample in samples if sample.name == name)
        assert sample.value == 1
        assert sample.labels["http_route"] == f"{PATH}/{{order_id}}"
        assert sample.labels["http_response_status_code"] == "404"
    records = [json.loads(line) for line in capfd.readouterr().err.splitlines()]
    record = next(record for record in records if "Orders API" in record.get("message", ""))
    assert record["trace_id"] == trace_id
