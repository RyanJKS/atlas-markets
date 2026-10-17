"""HTTP entry point; order management is not implemented yet."""

from fastapi import FastAPI

app = FastAPI(title="Atlas Orders", version="0.1.0")


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    """Report process liveness, not order processing readiness."""
    return {"service": "orders", "status": "ok"}
