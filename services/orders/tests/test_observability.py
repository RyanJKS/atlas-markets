import json
from io import StringIO
from unittest.mock import Mock

import pytest
from atlas_orders.app.bootstrap import create_app
from atlas_orders.core.config.settings import AppSettings, ObservabilitySettings, Settings
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from prometheus_client.parser import text_string_to_metric_families


@pytest.mark.parametrize("endpoint", [None, "http://collector.test:4318/v1/traces"])
@pytest.mark.parametrize("azure_connection_string", [None, "InstrumentationKey=test-key"])
def test_random_route_logs_and_traces(
    capfd: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    endpoint: str | None,
    azure_connection_string: str | None,
) -> None:
    service_name = "orders-export-test" if endpoint else "orders-console-test"
    if azure_connection_string:
        service_name += "-azure"
    spans = StringIO()
    monkeypatch.setattr(
        "atlas_telemetry.tracing.ConsoleSpanExporter",
        lambda: ConsoleSpanExporter(
            out=spans, formatter=lambda span: span.to_json(indent=None) + "\n"
        ),
    )
    exported = InMemorySpanExporter()
    exporter_factory = Mock(return_value=exported)
    monkeypatch.setattr("atlas_telemetry.tracing.OTLPSpanExporter", exporter_factory)
    azure_exported = InMemorySpanExporter()
    azure_factory = Mock(return_value=azure_exported)
    monkeypatch.setattr("atlas_telemetry.tracing.AzureMonitorTraceExporter", azure_factory)
    app = create_app(
        Settings(
            app=AppSettings(service_name=service_name),
            observability=ObservabilitySettings(
                traces_endpoint=endpoint, azure_connection_string=azure_connection_string
            ),
        )
    )
    with TestClient(app) as client:
        assert 1 <= client.get("/random").json() <= 100
        metrics = client.get("/metrics/")
        assert metrics.status_code == 200
        values = [
            sample.value
            for family in text_string_to_metric_families(metrics.text)
            for sample in family.samples
            if sample.name == "orders_random_requests_total"
        ]
        assert values == [1.0]
    output = capfd.readouterr()
    span = next(
        json.loads(line)
        for line in spans.getvalue().splitlines()
        if json.loads(line)["name"] == "orders.generate_random"
    )
    assert span["name"] == "orders.generate_random"
    assert span["resource"]["attributes"]["service.name"] == service_name
    records = [json.loads(line) for line in output.err.splitlines()]
    record = next(item for item in records if item["message"] == "Generated random value")
    assert record["service_name"] == service_name
    assert record["trace_id"] == span["context"]["trace_id"].removeprefix("0x")
    assert record["span_id"] == span["context"]["span_id"].removeprefix("0x")
    if endpoint is None:
        exporter_factory.assert_not_called()
    else:
        exporter_factory.assert_called_once_with(endpoint=endpoint)
        assert len(exported.get_finished_spans()) == 2
        assert (
            format(exported.get_finished_spans()[0].context.trace_id, "032x") == record["trace_id"]
        )
    if azure_connection_string is None:
        azure_factory.assert_not_called()
    else:
        azure_factory.assert_called_once_with(connection_string=azure_connection_string)
        assert len(azure_exported.get_finished_spans()) == 2
        assert (
            format(azure_exported.get_finished_spans()[0].context.trace_id, "032x")
            == record["trace_id"]
        )
