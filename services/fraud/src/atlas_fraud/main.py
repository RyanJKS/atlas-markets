"""HTTP entry point; fraud rules and scoring are not implemented yet."""

from fastapi import FastAPI

app = FastAPI(title="Atlas Fraud", version="0.1.0")


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    """Report process liveness, not fraud assessment readiness."""
    return {"service": "fraud", "status": "ok"}
