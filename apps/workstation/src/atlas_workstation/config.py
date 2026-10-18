"""Service registration and dotenv configuration, separate from UI pages."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def environment_value(name: str, default: str | None = None) -> str | None:
    """Read a process override or app-local dotenv value without changing os.environ."""
    return os.environ.get(name, dotenv_values(ENV_FILE, encoding="utf-8").get(name, default))


@dataclass(frozen=True)
class Service:
    key: str
    name: str
    url_environment_variable: str

    @property
    def base_url(self) -> str:
        value = environment_value(self.url_environment_variable)
        if not value or not value.strip():
            raise ValueError(
                f"Set {self.url_environment_variable} in apps/workstation/.env "
                "or the process environment."
            )
        return value.strip()


SERVICES = (Service("orders", "Orders", "ORDERS_API_URL"),)
