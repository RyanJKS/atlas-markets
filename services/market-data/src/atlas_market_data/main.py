"""HTTP entry point; feed ingestion is not implemented yet."""

from fastapi import FastAPI

app = FastAPI(title="Atlas Market Data", version="0.1.0")


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    """Report process liveness, not feed availability."""
    return {"service": "market-data", "status": "ok"}
