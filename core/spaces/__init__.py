"""
core/spaces/__init__.py

GAIA Spaces — persistent, named, shared environments.

A Space is a durable context container that survives across sessions. It
holds a shared key-value store, a membership roster, and a structured
event log. Multiple Gaian agents or Human Principals can participate in
the same Space, read its context, and emit events into it.

Spaces differ from Sessions (ephemeral per-conversation) and from
Memory (which is per-principal). A Space is explicitly created, named,
and owned; its state persists until it is archived or destroyed.

Canon grounding:
  - C01: GAIA as orchestration layer — Spaces are the durable context
    units that the agentic loop operates within.
  - C03: action_gate consent — joining or modifying a Space with
    write access requires consent when the Space is locked.
  - Super-Computation Alignment phase: Spaces carry a criticality
    score that the CriticalityMonitor can read to determine whether
    the Space is operating at edge-of-chaos.
"""
from __future__ import annotations

from core.spaces.model import (
    Space,
    SpaceStatus,
    SpaceMember,
    SpaceRole,
    SpaceEvent,
    SpaceEventKind,
)
from core.spaces.store import SpaceStore
from core.spaces.manager import SpaceManager

__all__ = [
    "Space",
    "SpaceStatus",
    "SpaceMember",
    "SpaceRole",
    "SpaceEvent",
    "SpaceEventKind",
    "SpaceStore",
    "SpaceManager",
]
