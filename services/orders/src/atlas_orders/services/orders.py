"""Stateless sample data; acknowledgements never change the fixtures."""

from datetime import UTC, datetime
from uuid import uuid4

from atlas_orders.models.orders import Order, OrderRequest, SimulatedOrder

SAMPLE_ORDERS = (
    Order(
        id="ORD-1001",
        symbol="AAPL",
        side="buy",
        quantity=250,
        order_type="limit",
        limit_price="225.50",
        currency="USD",
        status="open",
        submitted_at=datetime(2026, 10, 16, 9, 30, tzinfo=UTC),
    ),
    Order(
        id="ORD-1002",
        symbol="MSFT",
        side="sell",
        quantity=100,
        order_type="market",
        currency="USD",
        status="filled",
        submitted_at=datetime(2026, 10, 16, 10, 15, tzinfo=UTC),
    ),
    Order(
        id="ORD-1003",
        symbol="VOD.L",
        side="buy",
        quantity=500,
        order_type="limit",
        limit_price="0.75",
        currency="GBP",
        status="open",
        submitted_at=datetime(2026, 10, 16, 11, 0, tzinfo=UTC),
    ),
)


class OrderService:
    def list_orders(self) -> tuple[Order, ...]:
        return SAMPLE_ORDERS

    def get_order(self, order_id: str) -> Order | None:
        return next((order for order in SAMPLE_ORDERS if order.id == order_id), None)

    def simulate_order(self, order: OrderRequest) -> SimulatedOrder:
        return SimulatedOrder(
            **order.model_dump(),
            id=f"SIM-{uuid4().hex[:12]}",
            status="simulated",
            submitted_at=datetime.now(UTC),
        )
