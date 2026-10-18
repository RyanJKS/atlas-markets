"""Validate dotenv resolution, environment precedence, and missing configuration."""

import os
from pathlib import Path

import pytest
from atlas_workstation import config


@pytest.fixture
def env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "workstation.env"
    monkeypatch.setattr(config, "ENV_FILE", path)
    monkeypatch.delenv("ORDERS_API_URL", raising=False)
    return path


def test_dotenv_is_read_independently_of_working_directory(
    env_file: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file.write_text("ORDERS_API_URL=http://dotenv-orders.test:8003\n", encoding="utf-8")
    other_directory = tmp_path / "other"
    other_directory.mkdir()
    monkeypatch.chdir(other_directory)
    assert config.SERVICES[0].base_url == "http://dotenv-orders.test:8003"
    assert "ORDERS_API_URL" not in os.environ


def test_process_environment_overrides_dotenv(
    env_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file.write_text("ORDERS_API_URL=http://dotenv-orders.test:8003\n", encoding="utf-8")
    monkeypatch.setenv("ORDERS_API_URL", "http://environment-orders.test:8003")
    assert config.SERVICES[0].base_url == "http://environment-orders.test:8003"


def test_dotenv_changes_are_read_again(env_file: Path) -> None:
    env_file.write_text("ORDERS_API_URL=http://first-orders.test:8003\n", encoding="utf-8")
    assert config.SERVICES[0].base_url == "http://first-orders.test:8003"
    env_file.write_text("ORDERS_API_URL=http://second-orders.test:8003\n", encoding="utf-8")
    assert config.SERVICES[0].base_url == "http://second-orders.test:8003"


@pytest.mark.parametrize("content", [None, "", "ORDERS_API_URL=\n"])
def test_missing_url_has_actionable_error(env_file: Path, content: str | None) -> None:
    if content is not None:
        env_file.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match="Set ORDERS_API_URL in apps/workstation/.env"):
        _ = config.SERVICES[0].base_url
