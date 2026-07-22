"""
sovereign_memory — Sovereign Memory Module

Provides SovereignMemory, the long-term, cryptographically-anchored
memory store for NEXUS agents. All memory operations are capability-gated
and audit-logged per GAIAN law.

Architecture reference: NEXUS_UNIVERSAL_OS.md Domain 2.6
GAIAN law:              GAIAN_LAWS.md Law II — Memory Sovereignty
"""
from __future__ import annotations

from sovereign_memory.engine import SovereignMemory
from sovereign_memory.router import memory_router, init_memory

__all__ = ["SovereignMemory", "memory_router", "init_memory"]
