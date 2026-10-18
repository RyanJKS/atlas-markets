"""Outbound event contracts included in OpenAPI, separate from inbound routes."""

from fastapi import APIRouter, Response

from atlas_orders.models.orders import SimulatedOrder

router = APIRouter(tags=["Order webhooks"])


@router.post(
    "order-simulated",
    summary="A simulated order is acknowledged",
    status_code=204,
    response_class=Response,
)
def order_simulated(body: SimulatedOrder) -> None:
    """Describe the notification associated with successful POST /orders/v1/orders.

    The intended outbound POST carries the same JSON acknowledgement returned
    by order submission, including its SIM- ID, simulated status, and timestamp.
    A recipient acknowledges the notification with HTTP 204.

    This is an OpenAPI webhook contract, not an inbound Orders URL. Webhook URL
    registration and HTTP delivery are not implemented; submitting an order
    currently returns its acknowledgement without sending a notification.
    """
