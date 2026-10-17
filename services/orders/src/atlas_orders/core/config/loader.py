"""Load environment-backed configuration and compose the downstream settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from atlas_orders.core.config.settings import AppSettings, ObservabilitySettings, Settings

DEFAULT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class _EnvironmentAppSettings(AppSettings, BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", case_sensitive=False, extra="ignore")


class _EnvironmentObservabilitySettings(ObservabilitySettings, BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OBSERVABILITY_", case_sensitive=False, extra="ignore"
    )


@lru_cache(maxsize=1)
def get_settings(env_file: str | Path | None = DEFAULT_ENV_FILE) -> Settings:
    """Load environment/file values and inject both sections into the final model.

    Process environment overrides the optional UTF-8 dotenv file. Pass another
    path to select a file, or None to read only the process environment.
    """
    return Settings(
        app=AppSettings.model_validate(
            _EnvironmentAppSettings(_env_file=env_file, _env_file_encoding="utf-8").model_dump()
        ),
        observability=ObservabilitySettings.model_validate(
            _EnvironmentObservabilitySettings(
                _env_file=env_file, _env_file_encoding="utf-8"
            ).model_dump()
        ),
    )
