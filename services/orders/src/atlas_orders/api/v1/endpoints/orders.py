from fastapi import APIRouter

router = APIRouter(prefix="/order", tags=["Orders"])


@router.get("")
async def get_order(id: int):
    return f"This is the details for order {id}"
