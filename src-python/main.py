"""
GAIA-OS Python Sidecar — main entry point
==========================================

Launches the FastAPI application that serves all GAIA inference engines
to the Tauri frontend via localhost HTTP.

Engines mounted
---------------
  /memory  — SovereignMemory (soul_mirror.db, episodic + semantic + biometric)
  /affect  — AffectEngine    (affect signal analysis, arc trends)
  /stage   — StageEngine     (Magnum Opus stage evaluation, WindowTracker)

Usage (development)
-------------------
  cd src-python
  uvicorn main:app --host 127.0.0.1 --port 52000 --reload

Usage (Tauri sidecar — production)
------------------------------------
  Tauri spawns this process automatically via tauri.conf.json sidecar config.
  The port is negotiated via the GAIA_SIDECAR_PORT env var (default: 52000).

Environment variables
---------------------
  GAIA_SIDECAR_PORT   TCP port to listen on            (default: 52000)
  GAIA_DB_PATH        Path to soul_mirror.db            (default: <app_data>/gaia/memory.db)
  GAIA_AFFECT_BACKEND NLP backend for affect analysis  (default: heuristic)
  GAIA_LOG_LEVEL      Python log level string           (default: INFO)
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Engine imports ────────────────────────────────────────────────────────────
from sovereign_memory import SovereignMemory
from sovereign_memory.router import memory_router, init_memory

from affect_engine.engine import AffectEngine
from affect_engine.router import affect_router, init_affect_engine

from stage_engine.engine import StageEngine
from stage_engine.window_tracker import WindowTracker
from stage_engine.router import stage_router, init_stage_engine


# ── Logging setup ─────────────────────────────────────────────────────────────
_log_level = os.environ.get("GAIA_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=_log_level,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("gaia.sidecar")


# ── Database path ─────────────────────────────────────────────────────────────
def _resolve_db_path() -> Path:
    """
    Determine the path to soul_mirror.db.

    Priority:
      1. GAIA_DB_PATH env var (absolute or relative)
      2. <cwd>/data/memory.db  (dev fallback — keeps DB out of src-python/)
    """
    env_path = os.environ.get("GAIA_DB_PATH")
    if env_path:
        p = Path(env_path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    dev_path = Path(__file__).parent.parent / "data" / "memory.db"
    dev_path.parent.mkdir(parents=True, exist_ok=True)
    return dev_path.resolve()


# ── Application lifespan ──────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: open SovereignMemory, instantiate all engines, inject into routers.
    Shutdown: close the memory connection cleanly.
    """
    db_path = _resolve_db_path()
    logger.info("GAIA sidecar starting — db=%s", db_path)

    # ── 1. Sovereign Memory (shared across all engines) ───────────────────────
    memory = SovereignMemory(db_path=str(db_path))
    memory.open()
    logger.info("SovereignMemory opened ✓")

    # ── 2. Affect Engine ──────────────────────────────────────────────────────
    affect_backend = os.environ.get("GAIA_AFFECT_BACKEND", "heuristic")
    affect_engine = AffectEngine(memory=memory)
    init_affect_engine(affect_engine, backend_name=affect_backend)
    logger.info("AffectEngine initialised (backend=%s) ✓", affect_backend)

    # ── 3. Stage Engine + WindowTracker ──────────────────────────────────────
    stage_engine = StageEngine(memory=memory)
    window_tracker = WindowTracker()
    init_stage_engine(memory=memory, engine=stage_engine, tracker=window_tracker)
    logger.info("StageEngine + WindowTracker initialised ✓")

    # ── 4. Sovereign Memory router (last — has its own init signature) ────────
    init_memory(memory)
    logger.info("SovereignMemory router initialised ✓")

    logger.info("━━━ GAIA sidecar ready — all engines online ━━━")

    yield  # ── application runs ──────────────────────────────────────────────

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("GAIA sidecar shutting down…")
    memory.close()
    logger.info("SovereignMemory closed. Goodbye. 💚")


# ── FastAPI application ───────────────────────────────────────────────────────
app = FastAPI(
    title="GAIA-OS Sidecar",
    version="0.1.0",
    description=(
        "Local-first inference sidecar for GAIA-OS. "
        "Serves Soul Mirror memory, affect analysis, and stage evaluation "
        "to the Tauri frontend over localhost."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS — allow only localhost origins (Tauri WebView + dev server) ──────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:1420",   # Tauri dev server default
        "http://127.0.0.1",
        "http://127.0.0.1:1420",
        "tauri://localhost",       # Tauri production WebView origin
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ─────────────────────────────────────────────────────────────
app.include_router(memory_router, prefix="/memory")
app.include_router(affect_router, prefix="/affect")
app.include_router(stage_router,  prefix="/stage")


# ── Root health endpoint ──────────────────────────────────────────────────────
@app.get("/", tags=["sidecar"])
async def root() -> JSONResponse:
    """Sidecar liveness probe — returns version and online engines."""
    return JSONResponse(content={
        "service": "gaia-sidecar",
        "version": "0.1.0",
        "status": "online",
        "engines": ["memory", "affect", "stage"],
    })


@app.get("/health", tags=["sidecar"])
async def health() -> JSONResponse:
    """Tauri sidecar health check — used to confirm process is ready."""
    return JSONResponse(content={"ok": True})


# ── Dev entrypoint ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("GAIA_SIDECAR_PORT", 52000))
    logger.info("Starting uvicorn on 127.0.0.1:%d", port)
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=port,
        reload=False,           # reload=True for local dev: run via CLI instead
        log_level=_log_level.lower(),
    )
