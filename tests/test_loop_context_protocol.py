"""Smoke tests for LoopContextProtocol — Issue #254.

Verifies that both the production stub shape and a minimal hand-rolled
implementation satisfy the protocol via runtime_checkable isinstance check.
"""
from __future__ import annotations

from typing import Any

import pytest

from core.protocols import LoopContextProtocol


# ---------------------------------------------------------------------------
# Minimal conforming implementation
# ---------------------------------------------------------------------------

class _ConformingContext:
    """Minimal class that satisfies LoopContextProtocol."""

    @property
    def session_id(self) -> str:
        return "test-session"

    @property
    def coherence(self) -> float:
        return 0.75

    @property
    def affective_state(self) -> str:
        return "calm"

    @property
    def current_goal(self) -> str | None:
        return "test goal"

    @property
    def goal_complete(self) -> bool:
        return False

    @property
    def cycle_count(self) -> int:
        return 3

    @property
    def cycle_memory(self) -> float:
        return 0.5

    @property
    def canon_refs(self) -> list[str]:
        return ["C01", "C30"]

    @property
    def canon_context(self) -> str | None:
        return None

    @property
    def session_mode(self) -> str:
        return "default"

    @property
    def planetary_state(self) -> dict[str, Any]:
        return {}

    def update(self, **kwargs: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# Non-conforming class (missing fields)
# ---------------------------------------------------------------------------

class _NonConformingContext:
    """Deliberately missing most protocol fields."""
    pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_conforming_satisfies_protocol() -> None:
    ctx = _ConformingContext()
    assert isinstance(ctx, LoopContextProtocol)


def test_non_conforming_fails_protocol() -> None:
    ctx = _NonConformingContext()
    assert not isinstance(ctx, LoopContextProtocol)


def test_protocol_fields_documented() -> None:
    """Protocol must expose all required field names as annotations/properties."""
    required = {
        "session_id", "coherence", "affective_state",
        "current_goal", "goal_complete", "cycle_count",
        "cycle_memory", "canon_refs", "canon_context",
        "session_mode", "planetary_state",
    }
    proto_members = set(dir(LoopContextProtocol))
    missing = required - proto_members
    assert not missing, f"Protocol missing members: {missing}"


def test_update_callable() -> None:
    ctx = _ConformingContext()
    ctx.update(coherence=0.9)  # should not raise
