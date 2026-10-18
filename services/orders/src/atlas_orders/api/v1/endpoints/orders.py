from atlas_orders.models.orders import Order, OrderRequest, SimulatedOrder
from atlas_orders.services.orders import OrderService
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["Orders"])


@router.get("/order", deprecated=True)
async def get_order(id: int):
    return f"This is the details for order {id}"


@router.get("/orders", response_model=list[Order])
def list_orders() -> tuple[Order, ...]:
    return OrderService().list_orders()


@router.get("/orders/{order_id}", response_model=Order)
def get_order_details(order_id: str) -> Order:
    order = OrderService().get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Sample order not found")
    return order


@router.post("/orders", response_model=SimulatedOrder)
def simulate_order(order: OrderRequest) -> SimulatedOrder:
    """Return a simulated acknowledgement without storing or executing the order.

    The order-simulated webhook documents this acknowledgement as an outbound
    notification contract. HTTP notification delivery is not implemented.
    """
    return OrderService().simulate_order(order)
