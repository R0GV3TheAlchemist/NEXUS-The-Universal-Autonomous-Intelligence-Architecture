"""
core/server_lifecycle.py
──────────────────────────────────────────────────────────────────────────────
FastAPI application lifecycle hooks.

Startup sequence
----------------
  1. MotherThread boot
  2. Viriditas boot
  3. Spiritus → Goals wire-up      (deferred so runtime singleton exists)  ★
  4. LCI + Status set_dependencies  (deferred, same reason)                ❤️
  5. Router set_dependencies for query_router (canon + inference + runtime)

Shutdown sequence
-----------------
  1. MeshServer stop (if enabled)
  2. MotherThread shutdown

Canon Refs: C01, C04, C12, C15, C17
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI

logger = logging.getLogger("gaia.lifecycle")


def register_lifecycle(app: FastAPI) -> None:
    """Attach startup and shutdown handlers to the FastAPI app."""

    @app.on_event("startup")
    async def _startup() -> None:
        logger.info("[Lifecycle] ★ Startup sequence beginning...")

        # 1. MotherThread
        _boot_mother_thread()

        # 2. Viriditas
        _boot_viriditas()

        # 3. Spiritus → Goals wire-up
        _wire_spiritu_goals()

        # 4. LCI + Status router set_dependencies  ❤️
        _wire_lci_status()

        # 5. Query router set_dependencies
        _wire_query_router()

        logger.info("[Lifecycle] ♥ Startup sequence complete.")

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        logger.info("[Lifecycle] Shutdown sequence beginning...")
        _stop_mesh()
        _stop_mother_thread()
        logger.info("[Lifecycle] Shutdown complete.")


# ─────────────────────────────────────────────────────────────────────────────
#  Private startup steps
# ─────────────────────────────────────────────────────────────────────────────

def _boot_mother_thread() -> None:
    try:
        from core.mother_thread import get_mother_thread
        mt = get_mother_thread()
        mt.start()
        logger.info("[Lifecycle] ★ MotherThread started.")
    except Exception as exc:
        logger.warning("[Lifecycle] MotherThread boot failed (non-fatal): %s", exc)


def _boot_viriditas() -> None:
    try:
        from core.viriditas import boot_viriditas
        boot_viriditas()
        logger.info("[Lifecycle] ★ Viriditas booted.")
    except Exception as exc:
        logger.warning("[Lifecycle] Viriditas boot failed (non-fatal): %s", exc)


def _wire_spiritu_goals() -> None:
    """
    Inject the live Spiritus context function into the goals router.
    Called at startup so the GAIANRuntime singleton is already initialised.
    """
    try:
        from core.server_state import get_runtime
        from core.goals_router import set_spiritu_context_fn
        set_spiritu_context_fn(lambda slug: get_runtime(slug).spiritu_context())
        logger.info("[Lifecycle] ★ Spiritus → Goals wire-up complete.")
    except Exception as exc:
        logger.warning("[Lifecycle] Spiritus→Goals wire-up failed (non-fatal): %s", exc)


def _wire_lci_status() -> None:                                          # ❤️
    """
    Inject get_runtime_fn (and inference_router for lci/reflect) into
    the LCI and Status routers so they can resolve the correct
    GAIANRuntime per request.

    Called at startup so the singleton is guaranteed to exist.
    Graceful — logs a warning and continues if wiring fails.
    """
    try:
        from core.server_state import get_runtime
        from core.api.lci_router import set_dependencies as lci_set_deps
        from core.api.status_router import set_dependencies as status_set_deps

        # Try to get the inference router (may not exist in all deployments)
        inference_router: Optional[object] = None
        try:
            from core.server_state import inference_router as _ir
            inference_router = _ir
        except (ImportError, AttributeError):
            try:
                from core.inference_router import get_inference_router
                inference_router = get_inference_router()
            except Exception:
                pass  # reflect endpoint will degrade gracefully

        lci_set_deps(
            get_runtime_fn=get_runtime,
            inference_router=inference_router,
        )
        status_set_deps(
            get_runtime_fn=get_runtime,
        )
        logger.info(
            "[Lifecycle] ❤️ LCI + Status set_dependencies wired. "
            "inference_router=%s",
            "yes" if inference_router is not None else "not available (reflect will degrade gracefully)",
        )
    except Exception as exc:
        logger.warning(
            "[Lifecycle] LCI/Status set_dependencies failed (non-fatal): %s", exc
        )


def _wire_query_router() -> None:
    """
    Inject canon, inference_router, and get_runtime into the query router.
    This preserves the original query_router.set_dependencies() contract.
    """
    try:
        from core.server_state import canon, get_runtime
        from core.api.query_router import set_dependencies as query_set_deps

        inference_router: Optional[object] = None
        try:
            from core.server_state import inference_router as _ir
            inference_router = _ir
        except (ImportError, AttributeError):
            try:
                from core.inference_router import get_inference_router
                inference_router = get_inference_router()
            except Exception:
                pass

        query_set_deps(
            canon=canon,
            inference_router=inference_router,
            get_runtime_fn=get_runtime,
        )
        logger.info("[Lifecycle] ★ Query router set_dependencies wired.")
    except Exception as exc:
        logger.warning(
            "[Lifecycle] Query router set_dependencies failed (non-fatal): %s", exc
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Private shutdown steps
# ─────────────────────────────────────────────────────────────────────────────

def _stop_mesh() -> None:
    """
    Gracefully stop the MeshServer if one is running.
    We don't have a reference here, so we ask the runtime singleton directly.
    """
    try:
        from core.server_state import get_runtime
        rt = get_runtime("gaia")  # primary node
        if rt is not None and hasattr(rt, "async_stop"):
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(rt.async_stop())
                else:
                    loop.run_until_complete(rt.async_stop())
                logger.info("[Lifecycle] ⬡ MeshServer stop requested.")
            except Exception as exc:
                logger.warning("[Lifecycle] MeshServer stop error (non-fatal): %s", exc)
    except Exception as exc:
        logger.warning("[Lifecycle] _stop_mesh failed (non-fatal): %s", exc)


def _stop_mother_thread() -> None:
    try:
        from core.mother_thread import get_mother_thread
        mt = get_mother_thread()
        mt.stop()
        logger.info("[Lifecycle] ★ MotherThread stopped.")
    except Exception as exc:
        logger.warning("[Lifecycle] MotherThread stop failed (non-fatal): %s", exc)
