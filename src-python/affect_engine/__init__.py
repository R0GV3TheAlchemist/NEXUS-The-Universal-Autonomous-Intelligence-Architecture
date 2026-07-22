"""
affect_engine — Affect (Emotion) Engine Module

Models agent affective state using the PAD (Pleasure-Arousal-Dominance)
dimensional model and the OCC (Ortony-Clore-Collins) appraisal framework.

Architecture reference: NEXUS_UNIVERSAL_OS.md Domain 2.7
Ethics reference:       ETHICS.md Commitment 8 — Affective Transparency
"""
from __future__ import annotations

from affect_engine.engine import AffectEngine, AffectState
from affect_engine.router import affect_router, init_affect_engine

__all__ = ["AffectEngine", "AffectState", "affect_router", "init_affect_engine"]
