"""
GAIA OS FastAPI application factory.

The create_app() factory:
  1. Creates the FastAPI app with lifespan context manager
  2. Adds CORS, auth, and logging middleware
  3. Includes all routers
  4. Boots the Primordial Session at startup
  5. Tears it down cleanly at shutdown

Usage:
  # Direct run
  python -m server.app

  # With uvicorn (recommended)
  uvicorn server.app:app --reload

  # With explicit config
  GAIA_PORT=9000 GAIA_ROOT=/data/gaia uvicorn server.app:app
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.api.api import GAIAOSApi
from core.fs.filesystem import GAIAFilesystem
from core.identity.gaian.registry import GAIANRegistry
from core.primordial.session import PrimordialSession
from server.config import ServerConfig
from server.middleware import BearerAuthMiddleware, RequestLogMiddleware
from server.routes import router as api_router
from server.ws import ws_router

logger = logging.getLogger("gaia.server")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
)

# Module-level singletons — set during lifespan, read by routes
gaia_session: PrimordialSession | None = None
gaia_api: GAIAOSApi | None = None
gaia_fs: GAIAFilesystem | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan: boot GAIA on startup, log on shutdown.

    The Primordial Session is booted exactly once. All subsystems
    are wired before the first request is served.
    """
    global gaia_session, gaia_api, gaia_fs

    config: ServerConfig = app.state.config
    logger.info("GAIA OS booting... root=%s", config.gaia_root)

    gaia_fs      = GAIAFilesystem(root=config.gaia_root)
    gaia_session = PrimordialSession(
        registry=GAIANRegistry(),
        boot_number=config.boot_number,
    )
    gaia_session.awaken()
    gaia_api = GAIAOSApi()
    gaia_api.wire(gaia_session, gaia_fs)

    manifest = gaia_session.manifest
    logger.info(
        "Primordial Session %s | Schumann %.2f Hz | %d GAIAN(s)",
        manifest.boot_status.value.upper(),
        manifest.schumann_hz,
        manifest.gaian_count,
    )

    # Make session/api/fs available on app.state for routes
    app.state.session = gaia_session
    app.state.api     = gaia_api
    app.state.fs      = gaia_fs

    yield

    logger.info(
        "GAIA OS shutting down. Session %s",
        gaia_session.session_id[:8] if gaia_session else "none",
    )


def create_app(config: ServerConfig | None = None) -> FastAPI:
    """Create and configure the GAIA FastAPI application."""
    config = config or ServerConfig.from_env()

    app = FastAPI(
        title="GAIA OS",
        description=(
            "The Global Autonomous Intelligence Architecture — "
            "HTTP API surface for the GAIA Operating System."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.state.config = config

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Auth + logging middleware (outermost = runs first)
    app.add_middleware(RequestLogMiddleware)
    app.add_middleware(BearerAuthMiddleware, config=config)

    # Routers
    app.include_router(api_router)
    app.include_router(ws_router)

    return app


# Default app instance (used by uvicorn server.app:app)
app = create_app()


if __name__ == "__main__":
    import uvicorn
    cfg = ServerConfig.from_env()
    uvicorn.run(
        "server.app:app",
        host=cfg.host,
        port=cfg.port,
        reload=cfg.reload,
    )
