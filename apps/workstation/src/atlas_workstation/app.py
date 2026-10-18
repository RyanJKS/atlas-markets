"""Compose navigation, service connections, and independent UI pages."""

import streamlit as st

from atlas_workstation.api.client import ApiClient
from atlas_workstation.api.orders import OrdersClient
from atlas_workstation.config import SERVICES
from atlas_workstation.pages.diagnostics import render_diagnostics
from atlas_workstation.pages.orders import render_orders


def main() -> None:
    st.set_page_config(
        page_title="Atlas Markets | Workstation",
        page_icon=":material/candlestick_chart:",
        layout="wide",
    )
    with st.sidebar:
        st.title("ATLAS MARKETS")
        st.caption("HEDGE FUND · SERVICE SANDBOX")
        service = st.selectbox("Service", SERVICES, format_func=lambda item: item.name)
        timeout = st.number_input("Timeout (seconds)", min_value=1, max_value=30, value=5)
        st.caption("Requests run from the Streamlit server, not your browser.")
    try:
        base_url = service.base_url
        client = ApiClient(base_url, float(timeout))
    except ValueError as error:
        st.error(str(error))
        st.stop()
    previous_url = st.session_state.get("active_url")
    if previous_url != base_url:
        for key in ("blotter_result", "lookup_result", "ticket_result"):
            st.session_state.pop(key, None)
        st.session_state["active_url"] = base_url
    page = st.navigation(
        {
            "Trading": [
                st.Page(
                    lambda: render_orders(OrdersClient(client)),
                    title="Orders",
                    url_path="orders",
                    icon=":material/receipt_long:",
                )
            ],
            "Operations": [
                st.Page(
                    lambda: render_diagnostics(client),
                    title="Request inspector",
                    url_path="requests",
                    icon=":material/monitoring:",
                )
            ],
        }
    )
    page.run()
