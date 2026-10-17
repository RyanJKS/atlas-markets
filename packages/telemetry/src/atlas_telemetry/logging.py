"""Small JSON logging setup; no exporters or background threads."""

import json
import logging
from datetime import UTC, datetime

from opentelemetry import trace


class JsonFormatter(logging.Formatter):
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


def configure_logging(service_name: str, *, level: int | str = logging.INFO) -> logging.Logger:
    """Configure the service's named logger once, writing JSON to stderr."""
    if not service_name.strip():
        raise ValueError("service_name must not be empty")

    logger = logging.getLogger(f"atlas.{service_name}")
    logger.setLevel(level)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter(service_name))
        logger.addHandler(handler)
    return logger
