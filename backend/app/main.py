"""RECCORD DB FastAPI application."""

from fastapi import FastAPI

from app.api.auth import router as auth_router


app = FastAPI(
    title="RECCORD DB",
    version="1.0.0",
)

app.include_router(auth_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return API health status."""

    return {
        "status": "ok",
    }
