"""Check that outbound contracts appear in OpenAPI rather than inbound routes."""

from atlas_orders.app.bootstrap import create_app
from atlas_orders.core.config.settings import Settings
from atlas_orders.models.orders import OrderRequest, SimulatedOrder
from atlas_orders.services.orders import OrderService


def test_simulated_order_webhook_uses_submission_response_contract() -> None:
    app = create_app(Settings())
    schema = app.openapi()
    assert schema["openapi"].startswith("3.1.")
    webhook = schema["webhooks"]["order-simulated"]["post"]
    submission = schema["paths"]["/orders/v1/orders"]["post"]
    payload_schema = webhook["requestBody"]["content"]["application/json"]["schema"]
    response_schema = submission["responses"]["200"]["content"]["application/json"]["schema"]
    assert payload_schema == response_schema == {"$ref": "#/components/schemas/SimulatedOrder"}
    assert webhook["requestBody"]["required"]
    assert "204" in webhook["responses"]
    assert "/order-simulated" not in schema["paths"]
    assert all(getattr(route, "path", None) != "order-simulated" for route in app.routes)
    price_schema = schema["components"]["schemas"]["SimulatedOrder"]["properties"]["limit_price"]
    assert price_schema["anyOf"][0]["type"] == "string"
    assert (
        schema["components"]["schemas"]["SimulatedOrder"]["properties"]["status"]["const"]
        == "simulated"
    )


def test_submission_acknowledgement_validates_as_webhook_payload() -> None:
    order = OrderService().simulate_order(OrderRequest(symbol="AAPL", side="buy", quantity=10))
    payload = SimulatedOrder.model_validate_json(order.model_dump_json())
    assert payload.status == "simulated"
    assert payload.id.startswith("SIM-")
