import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from atlas_orders.core.config.loader import get_settings
from atlas_orders.core.config.settings import AppSettings, ObservabilitySettings, Settings
from pydantic import ValidationError


@pytest.fixture(autouse=True)
def isolate_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for variable in os.environ:
        if variable.upper().startswith(("APP_", "OBSERVABILITY_")):
            monkeypatch.delenv(variable)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_default_models_compose_without_loading_environment() -> None:
    settings = Settings()
    assert settings.app == AppSettings(service_name="orders", version="0.1.0")
    assert settings.observability == ObservabilitySettings()


def test_dotenv_loads_both_sections_and_ignores_other_keys(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "APP_SERVICE_NAME=orders-file\nAPP_VERSION=4.0.0\n"
        "OBSERVABILITY_TRACES_ENDPOINT=http://collector.test:4318/v1/traces\n"
        "OBSERVABILITY_AZURE_CONNECTION_STRING=InstrumentationKey=file-key\n"
        "UNRELATED_SETTING=ignored\n",
        encoding="utf-8",
    )
    settings = get_settings(env_file)
    assert settings.app == AppSettings(service_name="orders-file", version="4.0.0")
    assert str(settings.observability.traces_endpoint) == "http://collector.test:4318/v1/traces"
    assert (
        settings.observability.azure_connection_string.get_secret_value()
        == "InstrumentationKey=file-key"
    )
    assert "InstrumentationKey=file-key" not in repr(settings)


def test_process_environment_overrides_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "APP_VERSION=4.0.0\nOBSERVABILITY_TRACES_ENDPOINT=http://collector.test:4318/v1/traces\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("APP_VERSION", "5.0.0")
    monkeypatch.setenv("OBSERVABILITY_TRACES_ENDPOINT", "http://override.test:4318/v1/traces")
    settings = get_settings(str(env_file))
    assert settings.app.version == "5.0.0"
    assert str(settings.observability.traces_endpoint) == "http://override.test:4318/v1/traces"


def test_missing_dotenv_file_uses_defaults(tmp_path: Path) -> None:
    assert get_settings(tmp_path / "missing.env") == Settings()


def test_loader_injects_both_environment_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable, value in {
        "APP_SERVICE_NAME": "orders-worker",
        "APP_VERSION": "2.4.0",
        "OBSERVABILITY_TRACES_ENDPOINT": "http://collector.test:4318/v1/traces",
    }.items():
        monkeypatch.setenv(variable, value)
    settings = get_settings(env_file=None)
    assert settings.app == AppSettings(service_name="orders-worker", version="2.4.0")
    assert settings.observability == ObservabilitySettings(
        traces_endpoint="http://collector.test:4318/v1/traces"
    )


def test_prefixes_keep_environment_sources_separate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVICE_NAME", "wrong")
    monkeypatch.setenv("APP_LOGS", "false")
    monkeypatch.setenv("OBSERVABILITY_VERSION", "99.0.0")
    assert get_settings(env_file=None) == Settings()


def test_loader_caches_until_explicitly_cleared(monkeypatch: pytest.MonkeyPatch) -> None:
    original = get_settings(env_file=None)
    monkeypatch.setenv("APP_VERSION", "3.0.0")
    assert get_settings(env_file=None) is original
    assert get_settings(env_file=None).app.version == "0.1.0"
    get_settings.cache_clear()
    assert get_settings(env_file=None).app.version == "3.0.0"


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("APP_SERVICE_NAME", "   "),
        ("APP_VERSION", ""),
        ("OBSERVABILITY_TRACES_ENDPOINT", "not-a-url"),
    ],
)
def test_invalid_environment_fails_loading(
    monkeypatch: pytest.MonkeyPatch, variable: str, value: str
) -> None:
    monkeypatch.setenv(variable, value)
    with pytest.raises(ValidationError):
        get_settings(env_file=None)
