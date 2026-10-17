import json
import logging
import sys

import pytest
from atlas_telemetry import configure_logging, create_tracer_provider
from atlas_telemetry.logging import JsonFormatter
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def test_named_logger_is_idempotent_and_does_not_change_root(
    capfd: pytest.CaptureFixture[str],
) -> None:
    root_handlers = list(logging.getLogger().handlers)
    logger = configure_logging("telemetry-test-logger")
    try:
        assert configure_logging("telemetry-test-logger") is logger
        logger.info("Prices refreshed: %s", 3)
        output = capfd.readouterr().err.splitlines()
        assert len(output) == 1
        record = json.loads(output[0])
        assert record["message"] == "Prices refreshed: 3"
        assert record["service_name"] == "telemetry-test-logger"
        assert record["severity"] == "INFO"
        assert "trace_id" not in record
        assert logging.getLogger().handlers == root_handlers
    finally:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()


def test_exported_span_and_json_log_share_trace_context() -> None:
    exporter = InMemorySpanExporter()
    provider = create_tracer_provider("market-data", exporter=exporter)
    try:
        with provider.get_tracer("test").start_as_current_span("refresh-prices") as span:
            record = logging.LogRecord(
                "market-data", logging.INFO, __file__, 0, "Updated", (), None
            )
            output = json.loads(JsonFormatter("market-data").format(record))
            assert output["trace_id"] == format(span.get_span_context().trace_id, "032x")
            assert output["span_id"] == format(span.get_span_context().span_id, "016x")
        assert provider.force_flush(timeout_millis=5000)
        spans = exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "refresh-prices"
        assert spans[0].resource.attributes["service.name"] == "market-data"
    finally:
        provider.shutdown()


def test_exception_and_newline_remain_one_json_record() -> None:
    try:
        raise ValueError("bad price")
    except ValueError:
        record = logging.makeLogRecord(
            {"msg": "Price rejected\nReview input", "exc_info": sys.exc_info()}
        )
    output = JsonFormatter("market-data").format(record)
    assert len(output.splitlines()) == 1
    fields = json.loads(output)
    assert fields["message"] == "Price rejected\nReview input"
    assert "ValueError: bad price" in fields["exception"]
