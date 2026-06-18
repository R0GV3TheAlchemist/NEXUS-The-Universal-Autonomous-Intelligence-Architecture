"""
core/memory/__init__.py

Public surface for the GAIA memory subsystem.

Exports the factory function used by tests and production code:
    build_default_router() -> MemoryRouter

Also re-exports the core hierarchy types for convenience.

Canon: C01 (GAIA as orchestration layer), C34 (Memory Sovereignty)
Issue: #213
"""
from __future__ import annotations

from core.memory.hierarchy import (
    MemoryTier,
    MemoryQuery,
    MemoryStore,
    MemoryRouter,
    build_default_router,
)

__all__ = [
    # Hierarchy types
    "MemoryTier",
    "MemoryQuery",
    "MemoryStore",
    "MemoryRouter",
    # Factory
    "build_default_router",
]
