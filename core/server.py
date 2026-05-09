"""
GAIA API Server — FastAPI bootstrap v2.4.0

Split from the monolith in Sprint C47+. All endpoints live in
core/routers/. Shared process state lives in core/server_state.py.
Lifecycle hooks (MotherThread + Viriditas boot) live in core/server_lifecycle.py.

v2.4.0 additions:
  - Goals router mounted at /goals  (CRUD + Spiritus birth-stamping)
  - patch_runtime() called at startup to wire live Spiritus into goal creation

Canon Refs: C01, C04, C12, C15, C17, C20, C21, C27, C30, C42, C43, C44, C47, C48,
            C128 (Spiritus Pneuma Canon)
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.auth import auth_router
from core.error_boundary import install_error_handlers
from core.gaian import ensure_default_gaian
from core.logger import GAIAEvent, LoggingMiddleware, get_logger, log_event
from core.rate_limiter import RateLimitMiddleware
from core.routers import (
    admin_router,
    auth_users_router,
    chat_router,
    gaians_router,
    goals_router,           # ★ Goals + Spiritus
    health_router,
    internal_router,
    memory_router,
    mood_ws_router,
    query_router,
    room_router,
    system_router,
    zodiac_router,
)
from core.server_lifecycle import register_lifecycle
from core.server_state import SERVER_VERSION, canon

logger = get_logger(__name__)

_CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "GAIA_CORS_ORIGINS",
        "http://localhost:1420,http://localhost:5173,http://localhost:8008,http://127.0.0.1:1420",
    ).split(",")
    if o.strip()
]

app = FastAPI(title="GAIA API", version=SERVER_VERSION)

# — Error boundary (must be first) —
install_error_handlers(app)

# — Middleware stack: Logging → RateLimit → CORS —
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Correlation-ID"],
)

# — Routers —
# auth_users_router provides /auth/register, /auth/login, /auth/me
# auth_router (legacy) provides /auth/token for dev/admin bootstrap — kept for backward compat
app.include_router(auth_users_router)   # POST /auth/register, POST /auth/login, GET /auth/me
app.include_router(auth_router)         # POST /auth/token (dev bootstrap)
app.include_router(health_router)       # /health, /health/ready — no auth
app.include_router(internal_router)     # /internal/* — Rust → Python signals, loopback only
app.include_router(system_router)
app.include_router(gaians_router)
app.include_router(chat_router)
app.include_router(memory_router)
app.include_router(zodiac_router)
app.include_router(query_router)
app.include_router(admin_router)
app.include_router(mood_ws_router)
app.include_router(room_router)
app.include_router(goals_router, prefix="/goals", tags=["Goals"])  # ★ C128

# — Startup / shutdown lifecycle —
register_lifecycle(app)

# — Bootstrap —
try:
    ensure_default_gaian()
    log_event(GAIAEvent.GAIAN_LOADED, message="Default GAIAN (GAIA) ready.", gaian="gaia")
except Exception as e:
    logger.warning(f"Could not initialise default GAIAN: {e}")

# ★ Spiritus → Goals wire-up
# Deferred to lifecycle startup so the runtime singleton is guaranteed to exist.
# See: core/server_lifecycle.py — _wire_spiritu_goals()

log_event(
    GAIAEvent.CANON_LOADED,
    message=f"Canon loaded: {len(canon.list_documents())} docs status={canon.status}",
    doc_count=len(canon.list_documents()),
    canon_status=canon.status,
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("core.server:app", host="127.0.0.1", port=8008, reload=False, log_level="info")
