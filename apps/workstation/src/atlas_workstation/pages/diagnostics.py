"""Explicit service probes and bounded request inspection."""

import streamlit as st

from atlas_workstation.api.client import ApiClient
from atlas_workstation.ui.requests import record_result, render_result


def render_diagnostics(client: ApiClient) -> None:
    st.title("Request inspector")
    st.caption("Run a probe, then use the trace ID to find Orders API requests in logs and traces.")
    path = st.selectbox("Probe endpoint", ["/health", "/ready", "/random", "/metrics/"])
    if st.button("Send probe", type="primary"):
        record_result(client.request("GET", path))
    st.caption(
        "Use the trace ID to find Workstation client and Orders server spans together. "
        "Metrics probes create only a client span; scraping is excluded from server tracing."
    )
    history = st.session_state.get("request_history", [])
    st.subheader("Request history")
    st.caption("Latest 50 requests in this browser session. No automatic polling or retries.")
    if not history:
        st.info("No requests yet. Send a probe or use the Orders page.")
        return
    if st.button("Clear history"):
        st.session_state["request_history"] = []
        st.rerun()
    selected = st.selectbox(
        "Inspect request",
        range(len(history)),
        format_func=lambda index: (
            f"{history[index].timestamp[11:19]} UTC · {history[index].method} "
            f"{history[index].url} · {history[index].status_code or 'connection error'}"
        ),
    )
    render_result(history[selected])
