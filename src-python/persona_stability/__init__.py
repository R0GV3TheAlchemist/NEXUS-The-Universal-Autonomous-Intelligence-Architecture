"""
persona_stability — Persona Stability Engine

Monitors and maintains the coherence and stability of the NEXUS agent's
identity persona. Detects identity drift and emits stabilisation signals.

Architecture reference: NEXUS_UNIVERSAL_OS.md Domain 2.5
Ethics reference:       ETHICS.md Commitment 10 — Identity Integrity
"""
from __future__ import annotations

from persona_stability.engine import PersonaStabilityEngine, PersonaProfile
from persona_stability.router import persona_router, init_persona_engine

__all__ = ["PersonaStabilityEngine", "PersonaProfile", "persona_router", "init_persona_engine"]
