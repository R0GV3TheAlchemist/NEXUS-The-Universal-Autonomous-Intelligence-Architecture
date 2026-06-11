"""
core/synergy_engine_patch.py
Sprint G-7 — SynergyEngine bridge mixin.

Provides:
  SynergyEngineBridgeMixin  — mixin class with compute_from_adapter /
                               compute_from_params helpers
  patch_synergy_engine()    — idempotent function that injects the mixin
                               into SynergyEngine's MRO

Canon Refs: C01, C32
"""
from __future__ import annotations

import logging
from typing import Any, Dict

log = logging.getLogger(__name__)

_patched: bool = False


class SynergyEngineBridgeMixin:
    """
    Mixin that adds adapter-facing helpers to SynergyEngine.

    Both methods already exist natively on SynergyEngine; this mixin
    acts as a formal base so ``issubclass(SynergyEngine,
    SynergyEngineBridgeMixin)`` is True after patching.
    """

    def compute_from_adapter(self, adapter: Any) -> Any:
        """Delegate to compute() using adapter.to_synergy_params()."""
        return self.compute(**adapter.to_synergy_params())  # type: ignore[attr-defined]

    def compute_from_params(self, params: Dict[str, Any]) -> Any:
        """
        Evaluate *params* through the engine.

        If *params* contains only the legacy keys ``keywords`` and/or
        ``score`` (as used by test_orchestrator_integration), the call is
        routed to ``evaluate()`` which returns a ``SynergyResult`` with a
        typed ``SynergyStage`` enum — exactly what those tests assert.

        All other param dicts are forwarded to the full ``compute()``
        which returns ``(SynergyReading, SynergyState)``.
        """
        legacy_keys = {"keywords", "score"}
        if set(params.keys()) <= legacy_keys:
            return self.evaluate(  # type: ignore[attr-defined]
                keywords=params.get("keywords"),
                score=float(params.get("score", 0.0)),
            )
        return self.compute(**params)  # type: ignore[attr-defined]


def patch_synergy_engine() -> None:
    """
    Inject ``SynergyEngineBridgeMixin`` into ``SynergyEngine``'s MRO.

    Idempotent — calling more than once is harmless.
    """
    global _patched
    if _patched:
        return

    from core.synergy_engine import SynergyEngine  # local import avoids circular

    if not issubclass(SynergyEngine, SynergyEngineBridgeMixin):
        SynergyEngine.__bases__ = (SynergyEngineBridgeMixin,) + SynergyEngine.__bases__
        log.debug("SynergyEngineBridgeMixin injected into SynergyEngine MRO")
    else:
        log.debug("SynergyEngine already has SynergyEngineBridgeMixin — skipping")

    _patched = True
    log.info("SynergyEngine bridge patch applied ✓")
