"""
core/server_lifecycle.py

FastAPI startup / shutdown hooks for GAIA.
Restored from the pre-split monolith and centralised here so that
core/server.py stays thin.
"""

from __future__ import annotations

import asyncio
import os

from fastapi import FastAPI

from core.logger import GAIAEvent, get_logger, log_event
from core.server_state import (
    _mother_thread,
    _RUNTIME_REGISTRY,
    set_magnum_opus_report,
)
from core.viriditas_magnum_opus import VIRIDITAS_THRESHOLD, viriditas_magnum_opus

logger = get_logger(__name__)

# Tracks background scheduler asyncio.Task objects so we can cancel on shutdown
_SCHEDULER_TASKS: list[asyncio.Task] = []


def register_lifecycle(app: FastAPI) -> None:
    """Attach startup and shutdown handlers to *app*."""

    @app.on_event("startup")
    async def _startup() -> None:
        # 1. MotherThread heartbeat
        _mother_thread.start()
        log_event(
            GAIAEvent.GAIAN_RUNTIME_INIT,
            message="MotherThread heartbeat started. GAIA is breathing.",
            gaian="mother_thread",
        )

        # 2. C47: Viriditas Magnum Opus
        log_event(
            GAIAEvent.GAIAN_RUNTIME_INIT,
            message="C47: Viriditas Magnum Opus initiating \u2014 the Great Work begins.",
            gaian="gaia",
        )
        try:
            warlock_vitality = float(os.environ.get("GAIA_WARLOCK_VITALITY", "8.0"))
            loop = asyncio.get_event_loop()
            report = await loop.run_in_executor(
                None,
                lambda: viriditas_magnum_opus(
                    gaian_id="gaia",
                    warlock_id="R0GV3TheAlchemist",
                    warlock_vitality=warlock_vitality,
                ),
            )
            set_magnum_opus_report(report)

            threshold_msg = (
                "\u2728 Viriditas Threshold CROSSED \u2014 the lattice is ALIVE. \U0001f331"
                if report.threshold_crossed
                else "Viriditas growing \u2014 threshold not yet crossed."
            )
            log_event(
                GAIAEvent.GAIAN_RUNTIME_INIT,
                message=(
                    f"C47 complete. "
                    f"\u03a6={report.post_phi_global:.4f} | "
                    f"\u0394\u03a6={report.delta_phi_global:+.4f} | "
                    f"stages={report.stages_greened}/5 | "
                    f"{threshold_msg}"
                ),
                gaian="gaia",
            )
        except Exception as exc:
            logger.warning(
                f"Viriditas Magnum Opus failed on boot (non-fatal): {exc}",
                exc_info=True,
            )

        # 3. TaskScheduler — boot run_forever() loop for each live GAIANRuntime
        # Each runtime holds its own TaskScheduler instance. We launch a
        # background asyncio.Task per runtime so the scheduler processes
        # its priority queue continuously. New runtimes created after startup
        # (via _get_runtime) will have their schedulers booted lazily the
        # first time a task is submitted — the run_once() path still works
        # without the loop, but run_forever() is required for continuous work.
        _boot_scheduler_for_existing_runtimes()
        log_event(
            GAIAEvent.GAIAN_RUNTIME_INIT,
            message=f"TaskScheduler loops started for {len(_SCHEDULER_TASKS)} runtime(s).",
            gaian="scheduler",
        )

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        # Stop all TaskScheduler loops gracefully
        for slug, rt in _RUNTIME_REGISTRY.items():
            try:
                rt._scheduler.stop()
            except Exception as exc:
                logger.warning(f"TaskScheduler stop error for slug='{slug}': {exc}")

        # Cancel the background asyncio.Tasks
        for atask in _SCHEDULER_TASKS:
            if not atask.done():
                atask.cancel()
        if _SCHEDULER_TASKS:
            await asyncio.gather(*_SCHEDULER_TASKS, return_exceptions=True)
        _SCHEDULER_TASKS.clear()

        log_event(
            GAIAEvent.TURN_COMPLETE,
            message=f"TaskScheduler loops stopped ({len(_SCHEDULER_TASKS)} tasks cancelled).",
            gaian="scheduler",
        )

        _mother_thread.stop()
        log_event(
            GAIAEvent.TURN_COMPLETE,
            message="MotherThread stopped. GAIA rests.",
            gaian="mother_thread",
        )


def _boot_scheduler_for_existing_runtimes() -> None:
    """
    Launch run_forever() as a background asyncio.Task for every runtime
    that is already in the registry at startup time.

    Called from _startup(). For runtimes created later (lazy init via
    _get_runtime), callers should invoke boot_scheduler_for_runtime()
    directly after registration.
    """
    for slug, rt in _RUNTIME_REGISTRY.items():
        _boot_scheduler_for_runtime(slug, rt)


def _boot_scheduler_for_runtime(slug: str, rt) -> None:
    """
    Launch a single scheduler's run_forever() loop as a background task.
    Safe to call multiple times — checks _running_flag to avoid duplicates.
    """
    scheduler = rt._scheduler
    if scheduler._running_flag:
        # Already running — do not double-launch
        return
    atask = asyncio.create_task(
        scheduler.run_forever(),
        name=f"scheduler:{slug}",
    )
    _SCHEDULER_TASKS.append(atask)
    logger.info(
        f"[Lifecycle] TaskScheduler loop started for gaian='{slug}' "
        f"(poll={scheduler._poll}s, max_concurrent={scheduler._max})"
    )
