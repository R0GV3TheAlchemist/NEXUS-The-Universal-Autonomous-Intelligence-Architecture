"""
core/synergy_engine_patch.py
Sprint G-7 — compute_from_adapter() bridge for SynergyEngine

This module provides the monkey-patch / mixin helper that adds
`compute_from_adapter()` to SynergyEngine without touching the
original file (preserving its SHA for the canonical PR diff).

Usage (in core/__init__.py or startup):

    from core.synergy_engine_patch import patch_synergy_engine
    patch_synergy_engine()

Or import directly in call sites that need the bridge:

    from core.synergy_engine_patch import SynergyEngineMixin

Canon Refs: C32, C01
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.state_adapter import GAIAStateAdapter


class SynergyEngineBridgeMixin:
    """Mixin that adds compute_from_adapter() to SynergyEngine.

    Non-breaking: compute() signature is NOT changed.
    This mixin is temporary for Sprint G-7; in Sprint G-8 these methods
    will be merged directly into SynergyEngine.
    """

    def compute_from_adapter(self, adapter: "GAIAStateAdapter") -> Any:
        """Resolve adapter and delegate to self.compute().

        Args:
            adapter: A GAIAStateAdapter (or AsyncGAIAStateAdapter) instance
                     wrapping the GaianRecord for this computation.

        Returns:
            Whatever self.compute() returns (typically a tuple of
            (SynergyReading, new_state)).
        """
        params = adapter.to_synergy_params()
        return self.compute(**params)  # type: ignore[attr-defined]

    def compute_from_params(self, params: dict) -> Any:
        """Sprint G-8 entry point (forward-declared here for type-checking).

        In G-8 this will become the canonical call site; the bare
        `compute()` signature will be deprecated.
        """
        return self.compute(**params)  # type: ignore[attr-defined]


def patch_synergy_engine() -> None:
    """Apply the bridge mixin to SynergyEngine at runtime.

    Safe to call multiple times (idempotent).
    """
    try:
        from core.synergy_engine import SynergyEngine
        if not issubclass(SynergyEngine, SynergyEngineBridgeMixin):
            SynergyEngine.__bases__ = (SynergyEngineBridgeMixin,) + SynergyEngine.__bases__
    except ImportError:  # pragma: no cover
        pass
