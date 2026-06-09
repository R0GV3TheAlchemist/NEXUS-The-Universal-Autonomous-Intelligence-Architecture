"""Shared structural protocols for GAIA-OS.

Using typing.Protocol enforces structural compatibility at type-check time
(mypy --strict) without requiring inheritance. Any class satisfying the
attribute/method signatures passes — no explicit 'implements' needed.

Canon refs: C30 (No silent failures)
Issue: #254
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LoopContextProtocol(Protocol):
    """Structural contract for LoopContext objects.

    Both ``agentic_loop.LoopContext`` (production) and
    ``simulate_canon_comparison._LoopContext`` (simulation stub) must
    satisfy this interface. Any divergence is caught at mypy --strict
    time rather than silently at runtime.
    """

    # ---- Identity -------------------------------------------------------
    @property
    def session_id(self) -> str:
        """Unique identifier for the current session."""
        ...

    # ---- Coherence & affect ---------------------------------------------
    @property
    def coherence(self) -> float:
        """Current coherence score in [0.0, 1.0]."""
        ...

    @property
    def affective_state(self) -> str:
        """Current affective register label (e.g. 'calm', 'anxious')."""
        ...

    # ---- Goal tracking --------------------------------------------------
    @property
    def current_goal(self) -> str | None:
        """Active goal string, or None if no goal is set."""
        ...

    @property
    def goal_complete(self) -> bool:
        """Whether the current goal has been satisfied."""
        ...

    # ---- Cycle state ----------------------------------------------------
    @property
    def cycle_count(self) -> int:
        """Number of reasoning cycles completed so far."""
        ...

    @property
    def cycle_memory(self) -> float:
        """Accumulated memory weight for the current cycle, in [0.0, 1.0]."""
        ...

    # ---- Canon ----------------------------------------------------------
    @property
    def canon_refs(self) -> list[str]:
        """List of active Canon reference IDs (e.g. ['C01', 'C30'])."""
        ...

    @property
    def canon_context(self) -> str | None:
        """Raw canon passage text if present, else None."""
        ...

    # ---- Session mode ---------------------------------------------------
    @property
    def session_mode(self) -> str:
        """Session mode label (e.g. 'default', 'deep', 'minimal')."""
        ...

    # ---- Planetary / collective field -----------------------------------
    @property
    def planetary_state(self) -> dict[str, Any]:
        """Snapshot of collective/planetary field state."""
        ...

    # ---- Mutation -------------------------------------------------------
    def update(self, **kwargs: Any) -> None:
        """Apply field updates to the context in-place."""
        ...
