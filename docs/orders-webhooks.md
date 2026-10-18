# Orders webhook contract

Orders documents an `order-simulated` webhook using FastAPI's OpenAPI webhook
support. It describes an outbound POST notification associated with a successful
`POST /orders/v1/orders` submission. The payload is the same simulated order
acknowledgement returned by that endpoint.

This implements the contract and automatic documentation from the
[FastAPI OpenAPI webhooks guide](https://fastapi.tiangolo.com/advanced/openapi-webhooks/).
Destination registration and HTTP delivery are not implemented. Submitting an
order currently returns its acknowledgement without sending another request.
No database or subscription storage is added.

## Check the automatic documentation

Start Orders from the repository root:

```sh
just run-order
```

Open <http://localhost:8003/docs> and find **Webhooks**, then **order-simulated**.
The entry shows the outgoing POST body and the expected recipient response,
HTTP 204. The regular submission endpoint remains under **Orders**.

The machine-readable definition is at
<http://localhost:8003/openapi.json>, under `webhooks.order-simulated.post`.
Both the submission response and webhook request reference `SimulatedOrder`.
Its status is constrained to `simulated`.

`order-simulated` is an event identifier, not a URL served by Orders. It does not
create an inbound `/order-simulated` endpoint. A future recipient would provide
the destination URL separately.

## Payload

Example outgoing JSON body:

```json
{
  "symbol": "AAPL",
  "side": "buy",
  "quantity": 10,
  "order_type": "market",
  "limit_price": null,
  "currency": "USD",
  "id": "SIM-a1b2c3d4e5f6",
  "status": "simulated",
  "submitted_at": "2026-10-17T12:00:00Z"
}
```

Prices use decimal strings when present. Market orders have no limit price;
limit orders require one. All existing order validation applies. See the
[workstation guide](workstation.md#exercise-orders) for submission examples.

## Code boundaries

- `models/orders.py` defines `SimulatedOrder`, shared by the submission response
  and webhook body so the contracts stay aligned.
- `api/webhooks.py` declares a dedicated `APIRouter` with the named webhook.
- `app/bootstrap.py` includes that router through `app.webhooks.include_router`,
  keeping webhook definitions separate from inbound API routes.

The webhook declaration documents an outbound operation. FastAPI does not
execute its declaration function when an order is submitted.
