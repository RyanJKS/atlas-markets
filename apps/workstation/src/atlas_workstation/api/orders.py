"""Orders endpoint paths and payloads, independent of UI rendering."""

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from atlas_workstation.api.client import ApiClient, ApiResult


@dataclass(frozen=True)
class OrdersClient:
    http: ApiClient

    def list_orders(self) -> ApiResult:
        return self.http.request("GET", "/orders/v1/orders")

    def get_order(self, order_id: str) -> ApiResult:
        return self.http.request("GET", f"/orders/v1/orders/{quote(order_id, safe='')}")

    def simulate_order(self, order: dict[str, Any]) -> ApiResult:
        return self.http.request("POST", "/orders/v1/orders", body=order)
