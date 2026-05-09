"""
core/server_lifecycle.py
GAIA API Server — Startup / Shutdown lifecycle hooks.

v2.4.0 additions:
  - _wire_spiritu_goals(): registers the live GAIANRuntime singleton
    with the goals_router via patch_runtime() so every POST /goals
    auto-stamps the GAIAN’s live Spiritus state onto new goals.
"""

from __future__ import annotations

from fastapi import FastAPI

from core.logger import GAIAEvent, get_logger, log_event

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Spiritus → Goals wire-up  (C128)
# ---------------------------------------------------------------------------

def _wire_spiritu_goals() -> None:
    """
    Register the live GAIANRuntime singleton with the goals_router
    so that POST /goals auto-stamps the GAIAN’s Spiritus state
    (stage, pneuma_flow, breath_rhythm) onto every new goal.

    Called once during FastAPI startup, after the runtime singleton
    is guaranteed to be initialised by ensure_default_gaian().

    Safe to call even if the runtime is not yet initialised —
    goals_router._live_spiritu() falls back to safe defaults.
    """
    try:
        from core.gaian_runtime_patch import patch_runtime
        # Retrieve the singleton runtime from the gaians registry
        from core.gaian import get_default_runtime  # type: ignore
        rt = get_default_runtime()
        if rt is not None:
            patch_runtime(rt)
            log_event(
                GAIAEvent.GAIAN_LOADED,
                message="Spiritus → Goals wire-up complete (C128).",
                gaian="gaia",
            )
        else:
            logger.warning(
                "Spiritus→Goals: no default runtime found. "
                "Goals will use safe Spiritus defaults until a runtime is registered."
            )
    except Exception as exc:
        # Non-fatal — goals still work, just without live Spiritus injection
        logger.warning(f"Spiritus→Goals wire-up skipped: {exc}")


# ---------------------------------------------------------------------------
# Lifecycle registration
# ---------------------------------------------------------------------------

def register_lifecycle(app: FastAPI) -> None:
    """
    Attach GAIA startup and shutdown hooks to the FastAPI app.
    All heavy initialisation (MotherThread, Viriditas, Spiritus→Goals)
    happens here so server.py stays clean.
    """

    @app.on_event("startup")
    async def _startup() -> None:
        logger.info("[GAIA] Server starting up — v2.4.0")

        # MotherThread boot (existing)
        try:
            from core.mother_thread import MotherThread
            MotherThread.instance().start()
            log_event(GAIAEvent.GAIAN_LOADED, message="MotherThread started.", gaian="gaia")
        except Exception as exc:
            logger.warning(f"MotherThread start skipped: {exc}")

        # Viriditas Magnum Opus boot (existing)
        try:
            from core.viriditas_magnum_opus import ViriditasMagnumOpus
            ViriditasMagnumOpus.instance().start()
            log_event(GAIAEvent.GAIAN_LOADED, message="Viriditas Magnum Opus started.", gaian="gaia")
        except Exception as exc:
            logger.warning(f"Viriditas start skipped: {exc}")

        # ★ Spiritus → Goals wire-up (C128)
        _wire_spiritu_goals()

        logger.info("[GAIA] Startup complete. All systems breathing.")

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        logger.info("[GAIA] Server shutting down gracefully.")

        try:
            from core.mother_thread import MotherThread
            MotherThread.instance().stop()
        except Exception:
            pass

        try:
            from core.viriditas_magnum_opus import ViriditasMagnumOpus
            ViriditasMagnumOpus.instance().stop()
        except Exception:
            pass

        logger.info("[GAIA] Shutdown complete. The breath returns to silence.")
