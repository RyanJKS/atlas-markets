"""Typed configuration models; environment loading belongs to loader.py."""

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, SecretStr


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    service_name: str = Field(default="orders", min_length=1)
    version: str = Field(default="0.1.0", min_length=1)


class ObservabilitySettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    traces_endpoint: HttpUrl | None = None
    azure_connection_string: SecretStr | None = None


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app: AppSettings = Field(default_factory=AppSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
