"""Build the orders HTTP scaffold."""

import logging
from random import randint

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from atlas_orders.app.lifespan import lifespan
from atlas_orders.app.state import get_app_state, initialize_app_state
from atlas_orders.core.config.loader import get_settings
from atlas_orders.core.config.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else get_settings()
    app = FastAPI(
        title="Atlas Orders",
        version=settings.app.version,
        description="API Service for Orders",
        lifespan=lifespan,
    )
    initialize_app_state(app, settings)
    app.mount("/metrics", make_asgi_app())  # configure for metrics
    register_health_routes(app)
    register_demo_routes(app)
    return app


def register_health_routes(app: FastAPI) -> None:
    """Register liveness and startup readiness, not business dependency readiness."""
    settings = get_app_state(app).settings

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"service": settings.app.service_name, "status": "ok"}

    @app.get("/ready", tags=["health"])
    def ready() -> dict[str, str]:
        return {
            "service": settings.app.service_name,
            "status": "ready",
            "version": settings.app.version,
        }


def register_demo_routes(app: FastAPI) -> None:
    """Demonstrate a manual span and a log message in a route."""
    state = get_app_state(app)
    logger = logging.getLogger(f"atlas.{state.settings.app.service_name}")

    @app.get("/random", tags=["random"])
    def get_random() -> int:
        telemetry = state.get_telemetry()
        with telemetry.tracer.start_as_current_span("orders.generate_random"):
            telemetry.random_requests.add(1)
            value = randint(1, 100)
            logger.info("Generated random value")
            return value
