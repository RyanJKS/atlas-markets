"""Order blotter and simulated order entry."""

import streamlit as st

from atlas_workstation.api.orders import OrdersClient
from atlas_workstation.ui.requests import record_result, render_result


def render_orders(client: OrdersClient) -> None:
    st.title("Orders")
    st.caption("Explore the sample blotter and send simulated orders to the Orders API.")
    st.info(
        "Sandbox · Fixed sample orders. Submissions are acknowledged but never stored or executed."
    )
    blotter, ticket = st.tabs(["Order blotter", "Order ticket"])
    with blotter:
        render_blotter(client)
    with ticket:
        render_ticket(client)


def render_blotter(client: OrdersClient) -> None:
    st.subheader("Sample orders")
    if st.button("Load sample orders", type="primary"):
        st.session_state["blotter_result"] = record_result(client.list_orders())
    result = st.session_state.get("blotter_result")
    if result is not None:
        if result.ok and isinstance(result.body, list):
            st.dataframe(result.body, hide_index=True, width="stretch")
        with st.expander("Inspect list response", expanded=not result.ok):
            render_result(result)
    with st.form("order_lookup"):
        order_id = st.text_input("Order ID", "ORD-1001", help="Use an unknown ID to test HTTP 404.")
        submitted = st.form_submit_button("Find order")
    if submitted:
        if order_id.strip():
            st.session_state["lookup_result"] = record_result(client.get_order(order_id.strip()))
        else:
            st.warning("Enter an order ID.")
    if "lookup_result" in st.session_state:
        render_result(st.session_state["lookup_result"])


def render_ticket(client: OrdersClient) -> None:
    st.subheader("Simulate an order")
    order_type = st.radio("Order type", ["market", "limit"], horizontal=True)
    with st.form("order_ticket"):
        left, right = st.columns(2)
        symbol = left.text_input("Symbol", "AAPL", max_chars=12)
        side = right.selectbox("Side", ["buy", "sell"])
        quantity = left.number_input(
            "Quantity", min_value=1, max_value=1_000_000, value=100, step=1
        )
        currency = right.selectbox("Currency", ["USD", "GBP", "EUR"])
        limit_price = None
        if order_type == "limit":
            limit_price = st.number_input("Limit price", min_value=0.01, value=225.50, step=0.01)
        submitted = st.form_submit_button("Send simulated order", type="primary")
    if submitted:
        payload = {
            "symbol": symbol.strip().upper(),
            "side": side,
            "quantity": int(quantity),
            "order_type": order_type,
            "currency": currency,
        }
        if limit_price is not None:
            payload["limit_price"] = f"{limit_price:.2f}"
        st.session_state["ticket_result"] = record_result(client.simulate_order(payload))
    if "ticket_result" in st.session_state:
        result = st.session_state["ticket_result"]
        if result.ok:
            st.success("Simulated acknowledgement received. No order was stored or executed.")
        render_result(result)
