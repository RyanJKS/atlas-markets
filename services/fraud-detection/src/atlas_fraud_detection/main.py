"""HTTP entry point; model loading and scoring are not implemented yet."""

from fastapi import FastAPI

app = FastAPI(title="Atlas Fraud Detection", version="0.1.0")


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    """Report process liveness, not model readiness."""
    return {"service": "fraud-detection", "status": "ok"}
