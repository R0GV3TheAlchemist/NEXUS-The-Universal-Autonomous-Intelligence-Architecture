"""
core/stage_bridge.py
Stage Bridge — compatibility shim between affect stage and synergy stages.

Imports should come from here; core.affect_stage_bridge is the canonical
current module but this shim re-exports for backward compatibility.
"""
from __future__ import annotations

try:
    from core.affect_stage_bridge import AffectStageAdapter, is_shadow_surface_safe  # type: ignore
except ImportError:
    # Provide minimal stubs so tests can import without error even when
    # core.affect_stage_bridge is not yet implemented.
    from typing import Any

    class AffectStageAdapter:  # type: ignore
        """Stub — replace when core/affect_stage_bridge.py is complete."""
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    def is_shadow_surface_safe(*args: Any, **kwargs: Any) -> bool:  # type: ignore
        return True

__all__ = ["AffectStageAdapter", "is_shadow_surface_safe"]
