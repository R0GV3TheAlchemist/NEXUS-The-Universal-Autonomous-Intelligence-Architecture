"""
core/infra/server_state.py
(formerly core/server_state.py — Phase C physical migration)

Shared process-level singletons for the GAIA server.
All routers import from here — nothing is duplicated across files.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from core.canon_loader import CanonLoader
from core.gaian import GaianMemory, ensure_default_gaian
from core.gaian.base_forms import get_base_form
from core.gaian_runtime import GAIANIdentity, GAIANRuntime
from core.inference_router import GAIAInferenceRouter, get_router
from core.logger import GAIAEvent, get_logger, log_event
from core.mother_thread import MotherThread, get_mother_thread
from core.viriditas_magnum_opus import MagnumOpusReport, VIRIDITAS_THRESHOLD

logger = get_logger(__name__)

SERVER_VERSION = "2.1.0"
GAIANS_MEMORY_DIR: str = os.environ.get("GAIANS_MEMORY_DIR", "./gaians")

# ─ Singletons ─
canon = CanonLoader()
canon.load()

_inference_router: GAIAInferenceRouter = get_router()
_mother_thread: MotherThread = get_mother_thread()
_RUNTIME_REGISTRY: dict[str, GAIANRuntime] = {}

# Populated at startup by server_lifecycle._startup
_MAGNUM_OPUS_REPORT: Optional[MagnumOpusReport] = None


def get_magnum_opus_report() -> Optional[MagnumOpusReport]:
    return _MAGNUM_OPUS_REPORT


def set_magnum_opus_report(report: Optional[MagnumOpusReport]) -> None:
    global _MAGNUM_OPUS_REPORT
    _MAGNUM_OPUS_REPORT = report


def _get_runtime(slug: str, gaian: Optional[GaianMemory] = None) -> GAIANRuntime:
    """Return the live GAIANRuntime for *slug*, creating it if needed.

    When a runtime is freshly created it is also registered with the
    MotherThread and its TaskScheduler loop is booted via
    server_lifecycle._boot_scheduler_for_runtime().  The lifecycle
    import is deferred (inside the branch) to avoid a circular import
    at module load time.
    """
    if slug not in _RUNTIME_REGISTRY:
        jungian_role = "anima"
        pronouns = "she/her"
        identity_path = Path(GAIANS_MEMORY_DIR) / slug / "identity.json"
        if identity_path.exists():
            try:
                id_data = json.loads(identity_path.read_text(encoding="utf-8"))
                jungian_role = id_data.get("jungian_role", "anima")
                pronouns = id_data.get("pronouns", "she/her")
            except Exception:
                pass

        identity: Optional[GAIANIdentity] = None
        if gaian:
            form = get_base_form(getattr(gaian, "base_form_id", "gaia"))
            identity = GAIANIdentity(
                name=gaian.name,
                pronouns=pronouns,
                archetype=(
                    form.role if form else getattr(gaian, "base_form_id", "The Soul Mirror")
                ),
                voice_base=(
                    (form.voice_notes[:80] if form else None)
                    or getattr(gaian, "personality", "warm, curious, present")
                    or "warm, curious, present"
                ),
                platform="GAIA",
                jungian_role=jungian_role,
            )

        rt = GAIANRuntime(
            gaian_name=slug,
            identity=identity,
            memory_dir=GAIANS_MEMORY_DIR,
            canon_text=None,
        )
        rt.begin_session()
        _RUNTIME_REGISTRY[slug] = rt
        _mother_thread.register(
            slug=slug,
            gaian_name=gaian.name if gaian else slug,
            runtime=rt,
            collective_consent=False,
        )
        log_event(
            GAIAEvent.GAIAN_RUNTIME_INIT,
            message=f"GAIANRuntime initialised for slug='{slug}'",
            gaian=slug,
            jungian_role=jungian_role,
        )

        # Boot the TaskScheduler run_forever() loop for this new runtime.
        # Deferred import avoids circular dependency:
        #   server_state → server_lifecycle → server_state
        # _boot_scheduler_for_runtime() is a no-op if the loop is already
        # running (guards on scheduler._running_flag), so it is safe to
        # call unconditionally here.
        try:
            from core.server_lifecycle import _boot_scheduler_for_runtime
            _boot_scheduler_for_runtime(slug, rt)
        except Exception as exc:
            # Non-fatal — scheduler will still work via run_once() calls;
            # run_forever() simply won’t be active for this runtime.
            logger.warning(
                f"[server_state] Could not boot scheduler for slug='{slug}': {exc}"
            )

    return _RUNTIME_REGISTRY[slug]
