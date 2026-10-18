"""Drive actual Streamlit widgets while replacing only the HTTP boundary."""

from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest
from atlas_workstation import config
from atlas_workstation.api.client import ApiClient, ApiResult
from streamlit.testing.v1 import AppTest

ENTRYPOINT = Path(__file__).parents[1] / "streamlit_app.py"


@pytest.fixture(autouse=True)
def workstation_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ORDERS_API_URL", "http://orders.test")


def test_order_ticket_sends_once_and_keeps_history(monkeypatch: pytest.MonkeyPatch) -> None:
    def response(method: str, path: str, *, body: dict | None = None) -> ApiResult:
        return ApiResult(
            method=method,
            url=f"http://orders.test{path}",
            timestamp="2026-10-17T12:00:00+00:00",
            elapsed_ms=1.0,
            trace_id=uuid4().hex,
            status_code=200,
            request_body=body,
            body={"status": "simulated"},
        )

    request = Mock(side_effect=response)
    monkeypatch.setattr("atlas_workstation.api.client.ApiClient.request", request)
    app = AppTest.from_file(str(ENTRYPOINT)).run()
    assert not app.exception
    request.assert_not_called()
    next(button for button in app.button if button.label == "Send simulated order").click().run()
    assert not app.exception
    request.assert_called_once_with(
        "POST",
        "/orders/v1/orders",
        body={
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "order_type": "market",
            "currency": "USD",
        },
    )
    assert len(app.session_state["request_history"]) == 1
    assert app.success
    app.run()
    assert not app.exception
    assert request.call_count == 1


def test_unavailable_service_renders_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "atlas_workstation.api.client.ApiClient.request",
        Mock(
            return_value=ApiResult(
                method="GET",
                url="http://orders.test/orders/v1/orders",
                timestamp="2026-10-17T12:00:00+00:00",
                elapsed_ms=1.0,
                trace_id=uuid4().hex,
                error="Connection refused",
            )
        ),
    )
    app = AppTest.from_file(str(ENTRYPOINT)).run()
    next(button for button in app.button if button.label == "Load sample orders").click().run()
    assert not app.exception
    assert "Connection refused" in app.error[0].value


def test_app_uses_dotenv_url_without_url_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("ORDERS_API_URL=http://dotenv-orders.test:8003\n", encoding="utf-8")
    monkeypatch.setattr(config, "ENV_FILE", env_file)
    monkeypatch.delenv("ORDERS_API_URL")
    requested_urls = []

    def request(client: ApiClient, method: str, path: str) -> ApiResult:
        url = client.base_url + path
        requested_urls.append(url)
        return ApiResult(
            method=method,
            url=url,
            timestamp="2026-10-18T12:00:00+00:00",
            elapsed_ms=1.0,
            trace_id=uuid4().hex,
            status_code=200,
            body=[],
        )

    monkeypatch.setattr(ApiClient, "request", request)
    app = AppTest.from_file(str(ENTRYPOINT)).run()
    assert not app.exception
    assert not any(widget.label == "Service base URL" for widget in app.text_input)
    next(button for button in app.button if button.label == "Load sample orders").click().run()
    assert not app.exception
    assert requested_urls == ["http://dotenv-orders.test:8003/orders/v1/orders"]


def test_missing_service_configuration_renders_help(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config, "ENV_FILE", tmp_path / "missing.env")
    monkeypatch.delenv("ORDERS_API_URL")
    app = AppTest.from_file(str(ENTRYPOINT)).run()
    assert not app.exception
    assert "Set ORDERS_API_URL in apps/workstation/.env" in app.error[0].value
