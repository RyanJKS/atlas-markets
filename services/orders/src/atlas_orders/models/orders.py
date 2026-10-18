"""Validated contracts for the simulated order workflow."""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrderRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    symbol: str = Field(pattern=r"^[A-Z][A-Z0-9.\-]{0,11}$")
    side: Literal["buy", "sell"]
    quantity: int = Field(gt=0, le=1_000_000, strict=True)
    order_type: Literal["market", "limit"] = "market"
    limit_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: Literal["USD", "GBP", "EUR"] = "USD"

    @model_validator(mode="after")
    def validate_limit_price(self) -> Self:
        if self.order_type == "limit" and self.limit_price is None:
            raise ValueError("Limit orders require a limit price")
        if self.order_type == "market" and self.limit_price is not None:
            raise ValueError("Market orders must not include a limit price")
        return self


class Order(OrderRequest):
    id: str
    status: Literal["open", "filled", "simulated"]
    submitted_at: datetime


class SimulatedOrder(Order):
    """Acknowledgement shared by the submission response and webhook contract."""

    # Both contracts describe emitted JSON, including decimal strings for prices.
    model_config = ConfigDict(json_schema_mode_override="serialization")

    status: Literal["simulated"] = "simulated"
