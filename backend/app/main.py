"""RECCORD DB FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.objects import router as objects_router
from app.api.narrations import router as narrations_router
from app.api.workers import router as workers_router
from app.api.roles import router as roles_router
from app.api.elections import router as elections_router
from app.api.grid import router as grid_router
from app.core.schema import initialize_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_schema()
    yield


app = FastAPI(
    title="RECCORD DB",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(objects_router)
app.include_router(narrations_router)
app.include_router(workers_router)
app.include_router(roles_router)
app.include_router(elections_router)
app.include_router(grid_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
