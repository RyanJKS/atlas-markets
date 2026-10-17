from fastapi import APIRouter

from atlas_orders.api.v1.endpoints.orders import router as orders_router

router = APIRouter()

router.include_router(orders_router)
