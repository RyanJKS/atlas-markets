import json
import logging
import sys

import pytest
from atlas_telemetry import configure_logging
from atlas_telemetry.logging import JsonFormatter


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
