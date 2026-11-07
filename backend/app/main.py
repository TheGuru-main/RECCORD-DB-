"""RECCORD DB FastAPI application + static frontend."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.objects import router as objects_router
from app.api.narrations import router as narrations_router
from app.api.workers import router as workers_router
from app.api.roles import router as roles_router
from app.api.elections import router as elections_router
from app.api.grid import router as grid_router
from app.api.hosts import router as hosts_router
from app.api.media import router as media_router
from app.core.schema import initialize_schema

# Repo layout on Render: root has index.html, pages/, css/, js/
# Service rootDirectory is often "backend" — parent is repo root
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
FRONTEND_ROOT = REPO_ROOT if (REPO_ROOT / "index.html").exists() else BACKEND_DIR


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
app.include_router(media_router)
app.include_router(hosts_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


# API stays on /auth, /objects, /grid, etc.
# Static assets
if (FRONTEND_ROOT / "css").is_dir():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_ROOT / "css")), name="css")
if (FRONTEND_ROOT / "js").is_dir():
    app.mount("/js", StaticFiles(directory=str(FRONTEND_ROOT / "js")), name="js")
if (FRONTEND_ROOT / "pages").is_dir():
    app.mount("/pages", StaticFiles(directory=str(FRONTEND_ROOT / "pages"), html=True), name="pages")
if (FRONTEND_ROOT / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_ROOT / "assets")), name="assets")


@app.get("/")
def serve_index():
    index = FRONTEND_ROOT / "index.html"
    if index.is_file():
        return FileResponse(index)
    return {
        "service": "RECCORD DB",
        "health": "/health",
        "docs": "/docs",
        "note": "index.html not found on server",
    }
