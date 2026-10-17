import pytest
from atlas_orders.app.bootstrap import create_app
from atlas_orders.app.state import get_app_state
from atlas_orders.core.config.settings import AppSettings, Settings
from fastapi.testclient import TestClient


def test_health() -> None:
    app = create_app(Settings())
    with TestClient(app) as client:
        response = client.get("/health")
        ready = client.get("/ready")
        assert ready.json() == {"service": "orders", "status": "ready", "version": "0.1.0"}
        random_response = client.get("/random")
        assert random_response.status_code == 200
        assert 1 <= random_response.json() <= 100
    assert response.status_code == 200
    assert response.json() == {"service": "orders", "status": "ok"}


def test_app_uses_injected_nested_settings() -> None:
    settings = Settings(
        app=AppSettings(service_name="orders-test", version="2.0.0"),
    )
    app = create_app(settings)
    state = get_app_state(app)
    assert state.settings is settings
    assert state.telemetry is None
    assert get_app_state(create_app(settings)) is not state
    with pytest.raises(RuntimeError, match="lifespan"):
        state.get_telemetry()
    assert app.version == "2.0.0"
    with TestClient(app) as client:
        assert state.get_telemetry() is state.telemetry
        assert client.get("/health").json() == {"service": "orders-test", "status": "ok"}
        assert client.get("/ready").json() == {
            "service": "orders-test",
            "status": "ready",
            "version": "2.0.0",
        }
    assert state.telemetry is None
    with pytest.raises(RuntimeError, match="lifespan"):
        state.get_telemetry()
