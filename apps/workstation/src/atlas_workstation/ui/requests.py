"""Session-local request history and a common response inspector."""

import streamlit as st

from atlas_workstation.api.client import ApiResult

HISTORY_LIMIT = 50


def record_result(result: ApiResult) -> ApiResult:
    history = st.session_state.setdefault("request_history", [])
    history.insert(0, result)
    del history[HISTORY_LIMIT:]
    return result


def render_result(result: ApiResult) -> None:
    status = str(result.status_code) if result.status_code is not None else "Connection error"
    columns = st.columns(3)
    columns[0].metric("HTTP status", status)
    columns[1].metric("Response time", f"{result.elapsed_ms:.1f} ms")
    columns[2].metric("Method", result.method)
    st.caption(result.url)
    st.text_input("Trace ID", value=result.trace_id, disabled=True, key=f"trace-{result.trace_id}")
    if result.error:
        st.error(f"Service request failed: {result.error}")
        st.caption("Start the service and check its URL in apps/workstation/.env.")
    elif not result.ok:
        st.warning("API returned an error. Inspect the response below.")
    if isinstance(result.body, dict | list):
        st.json(result.body)
    elif result.body is not None:
        st.code(str(result.body), language="text")
    with st.expander("Request payload and response headers"):
        st.json({"request_body": result.request_body, "response_headers": result.headers})
