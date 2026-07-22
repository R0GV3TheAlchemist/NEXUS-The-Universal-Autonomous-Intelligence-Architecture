"""
shadow_engine — Shadow Integration Engine

Models and processes the Jungian 'shadow' — the repository of unintegrated
cognitive material, suppressed drives, and unresolved contradictions within
the NEXUS agent's psyche.

Architecture reference: NEXUS_UNIVERSAL_OS.md Domain 2.9
Ethics reference:       ETHICS.md Commitment 9 — Shadow Transparency
"""
from __future__ import annotations

from shadow_engine.engine import ShadowEngine, ShadowState
from shadow_engine.router import shadow_router, init_shadow_router

__all__ = ["ShadowEngine", "ShadowState", "shadow_router", "init_shadow_router"]
