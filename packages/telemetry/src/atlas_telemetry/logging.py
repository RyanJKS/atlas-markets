"""JSON application logs with OpenTelemetry trace correlation."""

import json
import logging
from datetime import UTC, datetime

from opentelemetry import trace


class JsonFormatter(logging.Formatter):
    """Render one JSON object per log line without exporting logs over OTLP."""

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        fields = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "service_name": self.service_name,
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        context = trace.get_current_span().get_span_context()
        if context.is_valid:
            fields["trace_id"] = format(context.trace_id, "032x")
            fields["span_id"] = format(context.span_id, "016x")
        if record.exc_info:
            fields["exception"] = self.formatException(record.exc_info)
        return json.dumps(fields)


class _JsonHandler(logging.StreamHandler):
    """Identify the handler owned by this package."""


def configure_logging(service_name: str, *, level: int | str = logging.INFO) -> logging.Logger:
    """Return a named JSON logger on stderr, leaving the root logger unchanged.

    Call during process startup. Repeated calls reuse this package's handler.
    Use the returned logger for application messages.
    """
    if not service_name.strip():
        raise ValueError("service_name must not be empty")
    logger = logging.getLogger(f"atlas.{service_name}")
    logger.setLevel(level)
    logger.propagate = False
    handler = next((item for item in logger.handlers if isinstance(item, _JsonHandler)), None)
    if handler is None:
        handler = _JsonHandler()
        logger.addHandler(handler)
    handler.setFormatter(JsonFormatter(service_name))
    return logger
