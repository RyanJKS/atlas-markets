"""Typed application state and its single FastAPI attachment point."""

from dataclasses import dataclass
from typing import cast

from fastapi import FastAPI
from opentelemetry.metrics import Counter
from opentelemetry.trace import Tracer

from atlas_orders.core.config.settings import Settings


@dataclass
class TelemetryState:
    tracer: Tracer
    random_requests: Counter


@dataclass
class AppState:
    settings: Settings
    telemetry: TelemetryState | None = None

    def get_telemetry(self) -> TelemetryState:
        """Require startup before using instruments, and prevent use after shutdown."""
        if self.telemetry is None:
            raise RuntimeError("Orders telemetry requires a running application lifespan")
        return self.telemetry


def initialize_app_state(app: FastAPI, settings: Settings) -> AppState:
    state = AppState(settings=settings)
    app.state.orders = state
    return state


def get_app_state(app: FastAPI) -> AppState:
    return cast(AppState, app.state.orders)
