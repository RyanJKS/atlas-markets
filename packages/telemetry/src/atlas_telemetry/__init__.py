"""Shared logging and tracing primitives; importing does not start exporters."""

from atlas_telemetry.logging import configure_logging
from atlas_telemetry.tracing import create_tracer_provider

__all__ = ["configure_logging", "create_tracer_provider"]
