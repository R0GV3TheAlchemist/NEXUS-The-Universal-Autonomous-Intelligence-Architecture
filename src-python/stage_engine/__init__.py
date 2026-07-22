"""
stage_engine — Stage / Developmental Stage Engine

Tracks the agent's current developmental or cognitive stage, managing
stage transitions and maintaining a sliding-window history.

Architecture reference: NEXUS_UNIVERSAL_OS.md Domain 2.8
"""
from __future__ import annotations

from stage_engine.engine       import StageEngine, StageState
from stage_engine.window_tracker import WindowTracker
from stage_engine.router       import stage_router, init_stage_engine

__all__ = ["StageEngine", "StageState", "WindowTracker", "stage_router", "init_stage_engine"]
