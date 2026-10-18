"""Keep unit and UI tests independent of developer collector configuration."""

import pytest


@pytest.fixture(autouse=True)
def disable_remote_trace_export(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OBSERVABILITY_TRACES_ENDPOINT", "")
    monkeypatch.setenv("APP_SERVICE_NAME", "workstation-test")
