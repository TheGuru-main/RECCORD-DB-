"""RECCORD DB FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.core.schema import initialize_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database schema before serving requests."""

    initialize_schema()
    yield


app = FastAPI(
    title="RECCORD DB",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return API health status."""

    return {
        "status": "ok",
    }
