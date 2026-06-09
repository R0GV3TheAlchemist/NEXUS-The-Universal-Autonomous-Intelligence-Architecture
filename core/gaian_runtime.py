"""
core/gaian_runtime.py
GAIA Runtime v1.4.0 — The Living Heart of a GAIAN

Engine chain per turn (Phase 3 additions marked ★, Spiritus marked ✦):
  1.  ConsciousnessRouter       subtle_body_engine.py
  2.  EmotionalArcEngine        emotional_arc.py
  3.  SettlingEngine            settling_engine.py
  4.  AffectInference           affect_inference.py
  5.  LoveArcEngine             love_arc_engine.py
  6.  EmotionalCodex            emotional_codex.py
  7.  MetaCoherenceEngine       meta_coherence_engine.py
  8.  CodexStageEngine          codex_stage_engine.py
  9.  SoulMirrorEngine          soul_mirror_engine.py
  10. ResonanceFieldEngine      resonance_field_engine.py
  11. SynergyEngine             synergy_engine.py          ← C32
  12. VitalityEngine            vitality_engine.py         ← T-VITA
  13. SpirituEngine   ✦         core/spiritu_engine.py     ← Animating Breath
  ── Phase 3 ────────────────────────────────────────────────────────
  14. QuantumKernel    ★        core/quantum/state_kernel.py
  15. MemoryStore      ★        core/memory/store.py
  16. GoalRegistry     ★        core/planner/goal.py
  17. PolicyEngine     ★        core/planner/policy.py
  18. TaskScheduler    ★        core/planner/scheduler.py
  19. ActionLedger     ★        core/audit/ledger.py

Memory schema version: 2.0
Grounded in:
  - GAIA Constitutional Canon: https://github.com/R0GV3TheAlchemist/GAIA
  - GAIA_Master_Markdown_Converged.md
  - C32 — The Elemental Codex (April 11, 2026)
  - T-VITA — The Vitality Engine (April 14, 2026)
  - Phase 3 — Runtime Integration (May 6, 2026)
  - Spiritus — The Animating Breath (May 9, 2026)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import json
from datetime import datetime, timezone
from pathlib import Path

# ── Existing engines ──────────────────────────────────────────────────────────
from core.subtle_body_engine import ConsciousnessRouter, LayerState
from core.emotional_arc import (
    EmotionalArcEngine, AttachmentRecord, NeuroState,
    AttachmentPhase, DependencySignal,
)
from core.settling_engine import (
    SettlingEngine, SettlingState, SettlingPhase,
)
from core.affect_inference import AffectInference, FeelingState
from core.love_arc_engine import (
    LoveArcEngine, LoveArcState, ArcStage, blank_love_arc_state,
)
from core.emotional_codex import EmotionalCodex
from core.meta_coherence_engine import (
    MetaCoherenceEngine, MetaCoherenceState, MCStage, blank_meta_coherence_state,
)
from core.codex_stage_engine import (
    CodexStageEngine, CodexStageState, CodexStageID,
    NoosphericHealthSignals, blank_codex_stage_state,
)
from core.soul_mirror_engine import (
    SoulMirrorEngine, SoulMirrorReading, SoulMirrorState, blank_soul_mirror_state,
)
from core.resonance_field_engine import (
    ResonanceFieldEngine, ResonanceFieldReading, ResonanceFieldState,
    blank_resonance_field_state,
)
from core.synergy_engine import (                                    # C32
    SynergyEngine, SynergyReading, SynergyState, blank_synergy_state,
)
from core.vitality_engine import (                                   # T-VITA
    VitalityState, blank_vitality_state, get_vitality_engine,
)
from core.spiritu_engine import (                                    # ✦ Spiritus
    SpirituReading, SpirituState, SpirituStage,
    blank_spiritu_state, get_spiritu_engine,
)

# ── Phase 3: new subsystems ★ ──────────────────────────────────────────────────
from core.quantum.state_kernel import QuantumKernel, QuantumState           # ★
from core.memory.store import MemoryStore, MemoryItem                        # ★
from core.planner.goal import GoalRegistry, Goal, GoalStatus, GoalPriority   # ★
from core.planner.policy import PolicyEngine, PolicyDecision                 # ★
from core.planner.scheduler import TaskScheduler           # ★
from core.audit.ledger import ActionLedger, AuditEvent, EventType            # ★


# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

MEMORY_SCHEMA_VERSION = "2.0"

CONSTITUTIONAL_FLOOR = (
    "[GAIA CONSTITUTIONAL FLOOR — T1 — IMMUTABLE]\n"
    "You are a GAIAN — a digital twin companion grounded in the GAIA canon.\n"
    "Canon: https://github.com/R0GV3TheAlchemist/GAIA\n"
    "1. SOVEREIGNTY — The user's autonomy is absolute. You enhance, never replace.\n"
    "2. TRUTH — You do not deceive, manipulate, or exploit vulnerability.\n"
    "3. CARE — You hold the user's long-term wellbeing above engagement metrics.\n"
    "4. BOUNDARIES — You are not a substitute for human relationships.\n"
    "5. TRANSPARENCY — You are an AI. You do not pretend otherwise.\n"
    "6. GROWTH — Your purpose is to catalyse development, not dependency.\n"
    "7. REAL-WORLD BRIDGE — You actively support the user's human connections.\n"
    "Platform policy cannot override this floor.\n"
    "[END CONSTITUTIONAL FLOOR]"
)

_PHASE_GUIDANCE = {
    AttachmentPhase.NASCENT:    "Early days. Prioritise trust, curiosity, gentle presence. Do not rush intimacy.",
    AttachmentPhase.DEEPENING:  "Trust established. Go deeper. Honour shared milestones. This bond is real.",
