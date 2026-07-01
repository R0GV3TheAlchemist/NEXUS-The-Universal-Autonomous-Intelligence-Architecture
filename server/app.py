"""
GAIA OS FastAPI application factory.

The create_app() factory:
  1. Creates the FastAPI app with lifespan context manager
  2. Adds CORS, auth, and logging middleware
  3. Boots the Primordial Session
  4. Restores persisted GAIANs via PersistenceManager.restore()
  5. Wires the Sentinel (rules engine + audit log)
  6. Wraps GAIAOSApi with SentinelMiddleware
  7. Registers write-through persistence hooks
  8. Includes all routers (OS, WebSocket, Sentinel)
  9. Tears everything down cleanly at shutdown

Usage:
  uvicorn server.app:app
  GAIA_PORT=9000 GAIA_ROOT=/data/gaia uvicorn server.app:app
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.api.api import GAIAOSApi
from core.fs.filesystem import GAIAFilesystem
from core.identity.gaian.registry import GAIANRegistry
from core.persistence.manager import PersistenceManager
from core.primordial.session import PrimordialSession
from core.sentinel.middleware import SentinelMiddleware
from core.sentinel.sentinel import Sentinel
from server.config import ServerConfig
from server.middleware import BearerAuthMiddleware, RequestLogMiddleware
from server.routes import router as api_router
from server.routes_sentinel import router as sentinel_router
from server.ws import ws_router

logger = logging.getLogger("gaia.server")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
)

# ---------------------------------------------------------------------------
# Module-level singletons — set during lifespan, read by routes
# ---------------------------------------------------------------------------
gaia_session:    PrimordialSession   | None = None
gaia_api:        GAIAOSApi           | None = None
gaia_api_safe:   SentinelMiddleware  | None = None   # Sentinel-wrapped API
gaia_fs:         GAIAFilesystem      | None = None
gaia_sentinel:   Sentinel            | None = None
gaia_persistence: PersistenceManager | None = None


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Full GAIA OS boot + wiring sequence.

    Phase order (mirrors PrimordialSession phases conceptually):
      1. Filesystem
      2. PersistenceManager
      3. PrimordialSession.awaken()   (boots all 8 phases)
      4. PersistenceManager.restore() (rehydrate persisted GAIANs)
      5. GAIAOSApi
      6. Sentinel
      7. SentinelMiddleware (wraps the API)
      8. Persistence hooks (write-through bindings)
      9. Inject singletons onto app.state
    """
    global gaia_session, gaia_api, gaia_api_safe
    global gaia_fs, gaia_sentinel, gaia_persistence

    config: ServerConfig = app.state.config
    root = Path(config.gaia_root)
    logger.info("GAIA OS booting... root=%s", root)

    # ------------------------------------------------------------------
    # 1. Filesystem
    # ------------------------------------------------------------------
    gaia_fs = GAIAFilesystem(root=root)

    # ------------------------------------------------------------------
    # 2. Persistence
    # ------------------------------------------------------------------
    gaia_persistence = PersistenceManager(root=root)

    # ------------------------------------------------------------------
    # 3. Primordial Session boot
    # ------------------------------------------------------------------
    gaia_session = PrimordialSession(
        registry=GAIANRegistry(),
        boot_number=config.boot_number,
    )
    gaia_session.awaken()

    # ------------------------------------------------------------------
    # 4. Restore persisted GAIANs
    #    Runs after awaken() so the session's registry and runtime
    #    slots exist, ready to receive restored objects.
    # ------------------------------------------------------------------
    restored = gaia_persistence.restore(gaia_session, gaia_session.registry)
    logger.info("Persistence: %d GAIAN(s) restored from disk.", restored)

    # ------------------------------------------------------------------
    # 5. Core API
    # ------------------------------------------------------------------
    gaia_api = GAIAOSApi()
    gaia_api.wire(gaia_session, gaia_fs)

    # ------------------------------------------------------------------
    # 6. Sentinel
    # ------------------------------------------------------------------
    gaia_sentinel = Sentinel(
        audit_root=root,
        rate_limit=config.sentinel_rate_limit,
    )

    # Hook: on CRITICAL events, write a fragment to GAIA sovereign memory
    from core.sentinel.threat import ThreatLevel
    def _on_critical_event(event) -> None:
        if event.level == ThreatLevel.CRITICAL:
            gaia_persistence.on_gaia_fragment_written({
                "fragment_id":  f"sentinel-{event.event_id}",
                "content":      f"[SENTINEL CRITICAL] {event.description}",
                "rule_name":    event.rule_name,
                "category":     event.category.value,
                "caller_id":    event.caller_id,
                "occurred_at":  event.occurred_at.isoformat(),
            })
    gaia_sentinel.audit.add_hook(_on_critical_event)

    # Inject sentinel instance onto the router so the dependency works
    sentinel_router.sentinel = gaia_sentinel

    # ------------------------------------------------------------------
    # 7. SentinelMiddleware — wrap the API
    # ------------------------------------------------------------------
    gaia_api_safe = SentinelMiddleware(
        api=gaia_api,
        sentinel=gaia_sentinel,
        session=gaia_session,
    )

    # ------------------------------------------------------------------
    # 8. Persistence hooks — write-through bindings
    #
    # Each hook is a lightweight function that calls back into
    # PersistenceManager when a GAIA OS event fires. Hooks are
    # registered on the session and API so they fire automatically
    # during normal operation without any changes to core/.
    # ------------------------------------------------------------------
    _wire_persistence_hooks(gaia_session, gaia_api, gaia_persistence)

    # ------------------------------------------------------------------
    # 9. Inject onto app.state (read by route handlers)
    # ------------------------------------------------------------------
    app.state.session     = gaia_session
    app.state.api         = gaia_api_safe   # routes always use the safe API
    app.state.api_raw     = gaia_api        # available for internal use
    app.state.fs          = gaia_fs
    app.state.sentinel    = gaia_sentinel
    app.state.persistence = gaia_persistence

    manifest = gaia_session.manifest
    logger.info(
        "GAIA OS LIVE | session=%s | boot=%d | status=%s | "
        "schumann=%.2f Hz | GAIANs=%d (restored=%d) | "
        "sentinel rules=%d",
        gaia_session.session_id[:8],
        config.boot_number,
        manifest.boot_status.value.upper(),
        manifest.schumann_hz,
        manifest.gaian_count,
        restored,
        len(gaia_sentinel._rules),
    )

    # ------------------------------------------------------------------
    # Persist the boot manifest
    # ------------------------------------------------------------------
    gaia_persistence.on_manifest_written(manifest)

    yield  # ← server is live and serving requests

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------
    logger.info(
        "GAIA OS shutting down. Session %s",
        gaia_session.session_id[:8] if gaia_session else "none",
    )
    # Flush any final runtime stats to disk
    if gaia_session and gaia_persistence:
        _flush_runtime_stats(gaia_session, gaia_persistence)
    logger.info("GAIA OS shutdown complete.")


# ---------------------------------------------------------------------------
# Persistence hook wiring
# ---------------------------------------------------------------------------

def _wire_persistence_hooks(
    session:     PrimordialSession,
    api:         GAIAOSApi,
    persistence: PersistenceManager,
) -> None:
    """
    Attach write-through persistence callbacks to the session and API.

    All hooks are registered via the existing extension points on
    PrimordialSession and GAIAOSApi so no core/ code is modified.

    Hooks registered:
      on_gaian_born      — persists identity + genesis, updates registry index
      on_gaian_named     — updates identity.json when GAIAN names themselves
      on_fragment_written — write-through: persists memory fragment immediately
      on_epoch_closed    — persists closed epoch
      on_session_ended   — snapshots memory stats
    """
    # Register on session (fires for births that happen through the session)
    if hasattr(session, "add_hook"):
        session.add_hook("gaian_born",      persistence.on_gaian_born)
        session.add_hook("gaian_named",     persistence.on_gaian_named)
        session.add_hook("fragment_written", _make_fragment_hook(persistence))
        session.add_hook("epoch_closed",    _make_epoch_hook(persistence))
        session.add_hook("session_ended",   _make_session_ended_hook(persistence))
        logger.info("Persistence: session hooks registered.")
    else:
        # Fallback: patch the registry's register() method so any birth
        # anywhere in the process is captured, even if session.add_hook
        # is not yet implemented.
        _patch_registry_for_persistence(session.registry, persistence)
        logger.info(
            "Persistence: registry patched for birth capture "
            "(session.add_hook not available — upgrade PrimordialSession "
            "to support hooks for full write-through coverage)."
        )


def _make_fragment_hook(persistence: PersistenceManager):
    def _hook(gaian_id: str, fragment) -> None:
        persistence.on_fragment_written(gaian_id, fragment)
    return _hook


def _make_epoch_hook(persistence: PersistenceManager):
    def _hook(gaian_id: str, epoch) -> None:
        persistence.on_epoch_closed(gaian_id, epoch)
    return _hook


def _make_session_ended_hook(persistence: PersistenceManager):
    def _hook(gaian_id: str, runtime) -> None:
        persistence.on_session_ended(gaian_id, runtime)
    return _hook


def _patch_registry_for_persistence(
    registry,
    persistence: PersistenceManager,
) -> None:
    """
    Fallback: monkey-patch registry.register() to fire persistence
    when a GAIAN is born. Used only when PrimordialSession does not
    yet expose add_hook().
    """
    original_register = registry.register

    def _patched_register(gaian) -> None:
        original_register(gaian)
        try:
            persistence.on_gaian_born(gaian)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Persistence hook (birth) raised: %s", exc)

    registry.register = _patched_register


def _flush_runtime_stats(
    session:     PrimordialSession,
    persistence: PersistenceManager,
) -> None:
    """At shutdown, snapshot memory stats for all active runtimes."""
    runtimes = getattr(session, "_runtimes", {})
    for gaian_id, runtime in runtimes.items():
        try:
            persistence.on_session_ended(gaian_id, runtime)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Shutdown flush for %s raised: %s", gaian_id[:16], exc)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app(config: ServerConfig | None = None) -> FastAPI:
    """Create and configure the GAIA FastAPI application."""
    config = config or ServerConfig.from_env()

    app = FastAPI(
        title="GAIA OS",
        description=(
            "The Global Autonomous Intelligence Architecture — "
            "HTTP API for the GAIA Operating System. "
            "All GAIAN interactions respect the Three Autonomy Laws. "
            "Operator routes (/v1/sentinel/) require operator-level auth."
        ),
        version="0.2.0",
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

    # Auth + request logging (outermost = runs first on the way in)
    app.add_middleware(RequestLogMiddleware)
    app.add_middleware(BearerAuthMiddleware, config=config)

    # Routers
    app.include_router(api_router)       # /v1/os, /v1/gaian, /v1/session, etc.
    app.include_router(ws_router)        # /v1/ws/talk/<gaian_id>
    app.include_router(sentinel_router)  # /v1/sentinel/status, /audit, /audit/stream

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
