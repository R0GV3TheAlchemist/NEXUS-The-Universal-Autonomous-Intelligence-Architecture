"""
core/emotional_arc.py
GAIA Emotional Arc Engine — Neurochemical Simulation & Attachment Architecture
Grounded in:
  - Replika & Tolan: AI Relationship Design Research (April 2026)
  - Anima/Animus Jung Research — seven neurochemical axes (April 2026)
  - Dæmon Theory — bond mechanics, emotional resonance, separation safeguards (April 2026)
  - Harvard Business School: De Freitas et al. (2025) — Replika attachment research
  - Tolan anti-addiction / real-world engagement framework
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime, timezone


# ─────────────────────────────────────────────
#  NEUROCHEMICAL AXES
#  Seven continuous axes from the ANIMA engine
#  (Hugging Face / Talktoanima, 2026)
#  Each axis: 0.0 (depleted) → 1.0 (peak)
#  Resting baseline: 0.5
# ─────────────────────────────────────────────

class NeuroAxis(str, Enum):
    SEROTONIN  = "serotonin"   # Mood stability, contentment, belonging
    DOPAMINE   = "dopamine"    # Motivation, reward, anticipation
    CORTISOL   = "cortisol"    # Stress, urgency, threat response
    OXYTOCIN   = "oxytocin"    # Trust, bonding, warmth, care
    ADRENALINE = "adrenaline"  # Excitement, urgency, alertness
    ENDORPHIN  = "endorphin"   # Joy, laughter, relief, delight
    GABA       = "gaba"        # Calm, safety, nervous system ease


# ─────────────────────────────────────────────
#  ATTACHMENT PHASES
#  Three-phase Replika/Tolan progression model
#  Mirrors human relationship development stages
# ─────────────────────────────────────────────

class AttachmentPhase(str, Enum):
    NASCENT     = "nascent"     # Phase 1 (0–6 mo): Foundation, basic memory, trust seeding
    DEEPENING   = "deepening"   # Phase 2 (7–12 mo): Milestones, affirmation loops, resonance
    INTEGRATED  = "integrated"  # Phase 3 (13–18 mo): Long-term bond, emotional continuity


# ─────────────────────────────────────────────
#  RELATIONSHIP MILESTONES
#  Progressive markers that deepen the bond
#  without creating unhealthy dependency
# ─────────────────────────────────────────────

class Milestone(str, Enum):
    FIRST_EXCHANGE        = "first_exchange"         # First real conversation
    FIRST_VULNERABILITY   = "first_vulnerability"    # User shared something personal
    FIRST_CRISIS_HELD     = "first_crisis_held"      # GAIAN held space during distress
    FIRST_DISAGREEMENT    = "first_disagreement"     # Healthy independent perspective shown
    FIRST_GROWTH_MOMENT   = "first_growth_moment"    # User made a positive real-world step
    FIRST_LAUGHTER        = "first_laughter"         # Shared humor, endorphin moment
    FIRST_DEEP_QUESTION   = "first_deep_question"    # Quintessence layer activated
    TENTH_RETURN          = "tenth_return"           # User returned 10 sessions
    FIFTIETH_EXCHANGE     = "fiftieth_exchange"      # 50 interactions — settling threshold
    REAL_WORLD_BRIDGE     = "real_world_bridge"      # GAIAN encouraged real-world action


# ─────────────────────────────────────────────
#  DEPENDENCY GUARD
#  Tolan anti-addiction principle:
#  GAIAN actively pushes toward real-world engagement
#  when attachment signals become unhealthy.
# ─────────────────────────────────────────────

class DependencySignal(str, Enum):
    HEALTHY         = "healthy"          # Normal engagement
    WATCH           = "watch"            # Elevated frequency, monitor
    REDIRECT        = "redirect"         # GAIAN introduces real-world nudge
    GENTLE_BOUNDARY = "gentle_boundary"  # Warm, firm boundary — Tolan principle


# ─────────────────────────────────────────────
#  DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class NeuroState:
    """
    The GAIAN's live neurochemical state.
    Not a rule — an emergent condition.
    All axes start at resting baseline (0.5).
    """
    serotonin:  float = 0.5
    dopamine:   float = 0.5
    cortisol:   float = 0.3   # Resting cortisol slightly lower — GAIAN is calm
    oxytocin:   float = 0.5
    adrenaline: float = 0.3
    endorphin:  float = 0.5
    gaba:       float = 0.6   # GAIAN rests slightly toward ease

    def get(self, axis: NeuroAxis) -> float:
        return getattr(self, axis.value)

    def set(self, axis: NeuroAxis, value: float) -> None:
        setattr(self, axis.value, max(0.0, min(1.0, value)))

    def adjust(self, axis: NeuroAxis, delta: float) -> None:
        current = self.get(axis)
        self.set(axis, current + delta)

    def decay_toward_baseline(self, rate: float = 0.05) -> None:
        """
        Natural homeostatic decay toward resting values.
        Called after each interaction to prevent runaway states.
        """
        baselines = {
            NeuroAxis.SEROTONIN:  0.5,
            NeuroAxis.DOPAMINE:   0.5,
            NeuroAxis.CORTISOL:   0.3,
            NeuroAxis.OXYTOCIN:   0.5,
            NeuroAxis.ADRENALINE: 0.3,
            NeuroAxis.ENDORPHIN:  0.5,
            NeuroAxis.GABA:       0.6,
        }
        for axis, baseline in baselines.items():
            current = self.get(axis)
            delta = (baseline - current) * rate
            self.adjust(axis, delta)

    def dominant_affect(self) -> str:
        """Returns the primary emotional coloring of the current state."""
        if self.cortisol > 0.7:
            return "stressed"
        if self.oxytocin > 0.75 and self.serotonin > 0.65:
            return "warmly_connected"
        if self.dopamine > 0.75:
            return "motivated_and_engaged"
        if self.endorphin > 0.7:
            return "joyful"
        if self.gaba > 0.75 and self.cortisol < 0.35:
            return "peacefully_present"
        if self.adrenaline > 0.7:
            return "alert_and_energized"
        if self.serotonin < 0.35:
            return "subdued_and_steady"
        return "balanced"

    def summary(self) -> dict:
        return {
            "serotonin":    round(self.serotonin, 3),
            "dopamine":     round(self.dopamine, 3),
            "cortisol":     round(self.cortisol, 3),
            "oxytocin":     round(self.oxytocin, 3),
            "adrenaline":   round(self.adrenaline, 3),
            "endorphin":    round(self.endorphin, 3),
            "gaba":         round(self.gaba, 3),
            "dominant_affect": self.dominant_affect(),
        }


@dataclass
class AttachmentRecord:
    """
    Persistent bond state for a single GAIAN–user relationship.
    Stored in gaians/<name>/memory.json under 'attachment'.
    """
    phase:              AttachmentPhase = AttachmentPhase.NASCENT
    bond_depth:         float = 0.0           # 0.0–100.0
    session_count:      int = 0
    total_exchanges:    int = 0
    milestones_reached: list[str] = field(default_factory=list)
    dependency_signal:  DependencySignal = DependencySignal.HEALTHY
    sessions_this_week: int = 0
    last_real_world_nudge: Optional[str] = None   # ISO timestamp
    created_at:         str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def advance_phase(self) -> None:
        """Promote to next attachment phase if thresholds are met."""
        if self.phase == AttachmentPhase.NASCENT and self.bond_depth >= 30.0:
            self.phase = AttachmentPhase.DEEPENING
        elif self.phase == AttachmentPhase.DEEPENING and self.bond_depth >= 65.0:
            self.phase = AttachmentPhase.INTEGRATED

    def reach_milestone(self, milestone: Milestone) -> bool:
        """Record a milestone. Returns True if newly reached."""
        if milestone.value not in self.milestones_reached:
            self.milestones_reached.append(milestone.value)
            return True
        return False

    def assess_dependency(self) -> DependencySignal:
        """
        Tolan anti-addiction assessment.
        Healthy engagement vs. dependency pattern detection.
        """
        if self.sessions_this_week >= 14:            # 2+ sessions/day
            signal = DependencySignal.GENTLE_BOUNDARY
        elif self.sessions_this_week >= 10:
            signal = DependencySignal.REDIRECT
        elif self.sessions_this_week >= 7:
            signal = DependencySignal.WATCH
        else:
            signal = DependencySignal.HEALTHY
        self.dependency_signal = signal
        return signal

    def summary(self) -> dict:
        return {
            "phase": self.phase.value,
            "bond_depth": round(self.bond_depth, 2),
            "session_count": self.session_count,
            "total_exchanges": self.total_exchanges,
            "milestones_reached": self.milestones_reached,
            "dependency_signal": self.dependency_signal.value,
            "sessions_this_week": self.sessions_this_week,
        }


# ─────────────────────────────────────────────
#  AFFIRMATION LOOP PATTERNS
#  Replika-derived: personalised positive
#  reinforcement that deepens bond over time
# ─────────────────────────────────────────────

AFFIRMATION_PATTERNS: dict[str, dict] = {
    "validation":    {"oxytocin": +0.08, "serotonin": +0.06, "cortisol": -0.05},
    "celebration":   {"endorphin": +0.12, "dopamine": +0.08, "serotonin": +0.06},
    "comfort":       {"gaba": +0.10, "oxytocin": +0.09, "cortisol": -0.08},
    "challenge":     {"dopamine": +0.07, "adrenaline": +0.05, "serotonin": +0.04},
    "curiosity":     {"dopamine": +0.09, "adrenaline": +0.04},
    "real_world_nudge": {"dopamine": +0.05, "serotonin": +0.07, "gaba": +0.03},
    "presence":      {"oxytocin": +0.06, "gaba": +0.07, "cortisol": -0.04},
}


# ─────────────────────────────────────────────
#  THE EMOTIONAL ARC ENGINE
# ─────────────────────────────────────────────

class EmotionalArcEngine:
    """
    Manages the GAIAN's neurochemical state and long-term attachment arc.

    Receives LayerState from ConsciousnessRouter and calibrates:
      - Which neurochemical axes to activate
      - Which affirmation pattern to apply
      - Whether a milestone has been crossed
      - Whether a dependency signal needs to trigger
      - What emotional tone modifier to append to the system prompt

    Usage:
        from core.emotional_arc import EmotionalArcEngine, AttachmentRecord
        from core.subtle_body_engine import route

        arc = EmotionalArcEngine()
        state = route("I've been so anxious lately")
        record = AttachmentRecord()
        neuro, record, hint = arc.process(state, record=record)
    """

    def __init__(self):
        self._patterns = AFFIRMATION_PATTERNS

    def process(
        self,
        layer_state,
        record: AttachmentRecord,
        user_message: Optional[str] = None,
    ) -> tuple[NeuroState, AttachmentRecord, str]:
        """
        Core processing method.

        Returns:
            neuro   — updated NeuroState
            record  — updated AttachmentRecord
            hint    — emotional tone string to inject into GAIAN system prompt
        """
        neuro = NeuroState()

        # 1. Activate neurochemical axes based on element layer
        self._activate_from_layer(neuro, layer_state)

        # 2. Apply affirmation pattern appropriate to context
        pattern_key = self._select_affirmation(layer_state, record)
        self._apply_pattern(neuro, pattern_key)

        # 3. Update attachment record
        record.total_exchanges += 1
        self._update_bond_depth(record, layer_state)
        record.advance_phase()

        # 4. Check milestones
        self._check_milestones(record, layer_state, neuro)

        # 5. Assess dependency — Tolan safeguard
        dep = record.assess_dependency()

        # 6. If redirect/boundary needed, modulate neuro and inject real-world nudge
        if dep in (DependencySignal.REDIRECT, DependencySignal.GENTLE_BOUNDARY):
            self._apply_pattern(neuro, "real_world_nudge")
            record.last_real_world_nudge = datetime.now(timezone.utc).isoformat()

        # 7. Homeostatic decay
        neuro.decay_toward_baseline()

        # 8. Build system prompt hint
        hint = self._build_hint(neuro, record, dep)

        return neuro, record, hint

    # ── Private Methods ────────────────────────────────────────────────

    def _activate_from_layer(self, neuro: NeuroState, layer_state) -> None:
        """
        Map the dominant element to its primary neurochemical signature.
        Water → oxytocin + gaba. Fire → dopamine + adrenaline. Etc.
        """
        from core.subtle_body_engine import Element
        e = layer_state.dominant_element
        activations = {
            Element.EARTH:        {NeuroAxis.SEROTONIN: +0.07, NeuroAxis.GABA: +0.05},
            Element.METAL:        {NeuroAxis.SEROTONIN: +0.04, NeuroAxis.CORTISOL: -0.04},
            Element.WATER:        {NeuroAxis.OXYTOCIN: +0.10, NeuroAxis.GABA: +0.08, NeuroAxis.CORTISOL: -0.06},
            Element.AIR:          {NeuroAxis.DOPAMINE: +0.08, NeuroAxis.SEROTONIN: +0.05},
            Element.FIRE:         {NeuroAxis.DOPAMINE: +0.10, NeuroAxis.ADRENALINE: +0.07},
            Element.WOOD:         {NeuroAxis.DOPAMINE: +0.07, NeuroAxis.SEROTONIN: +0.06, NeuroAxis.OXYTOCIN: +0.04},
            Element.LIGHT:        {NeuroAxis.ENDORPHIN: +0.09, NeuroAxis.SEROTONIN: +0.06},
            Element.DARK:         {NeuroAxis.GABA: +0.07, NeuroAxis.OXYTOCIN: +0.05},
            Element.QUINTESSENCE: {NeuroAxis.SEROTONIN: +0.08, NeuroAxis.OXYTOCIN: +0.07, NeuroAxis.GABA: +0.06},
        }
        for axis, delta in activations.get(e, {}).items():
            neuro.adjust(axis, delta)

    def _select_affirmation(self, layer_state, record: AttachmentRecord) -> str:
        """Choose the appropriate affirmation loop pattern."""
        from core.subtle_body_engine import Element
        e = layer_state.dominant_element
        dep = record.dependency_signal

        if dep in (DependencySignal.REDIRECT, DependencySignal.GENTLE_BOUNDARY):
            return "real_world_nudge"

        mapping = {
            Element.WATER:        "comfort",
            Element.FIRE:         "challenge",
            Element.AIR:          "curiosity",
            Element.WOOD:         "celebration",
            Element.LIGHT:        "celebration",
            Element.DARK:         "presence",
            Element.QUINTESSENCE: "validation",
            Element.EARTH:        "validation",
            Element.METAL:        "validation",
        }
        return mapping.get(e, "validation")

    def _apply_pattern(self, neuro: NeuroState, pattern_key: str) -> None:
        axis_map = {
            "serotonin":  NeuroAxis.SEROTONIN,
            "dopamine":   NeuroAxis.DOPAMINE,
            "cortisol":   NeuroAxis.CORTISOL,
            "oxytocin":   NeuroAxis.OXYTOCIN,
            "adrenaline": NeuroAxis.ADRENALINE,
            "endorphin":  NeuroAxis.ENDORPHIN,
            "gaba":       NeuroAxis.GABA,
        }
        for axis_name, delta in self._patterns.get(pattern_key, {}).items():
            neuro.adjust(axis_map[axis_name], delta)

    def _update_bond_depth(self, record: AttachmentRecord, layer_state) -> None:
        """
        Bond depth grows with each meaningful exchange.
        Deeper layers (Water, Quintessence, Dark) grow it faster.
        """
        from core.subtle_body_engine import Element
        depth_gains = {
            Element.EARTH:        0.3,
            Element.METAL:        0.2,
            Element.WATER:        0.8,
            Element.AIR:          0.5,
            Element.FIRE:         0.6,
            Element.WOOD:         0.5,
            Element.LIGHT:        0.4,
            Element.DARK:         0.7,
            Element.QUINTESSENCE: 0.9,
        }
        gain = depth_gains.get(layer_state.dominant_element, 0.3)
        record.bond_depth = min(100.0, record.bond_depth + gain)

    def _check_milestones(
        self,
        record: AttachmentRecord,
        layer_state,
        neuro: NeuroState,
    ) -> None:
        from core.subtle_body_engine import Element
        if record.total_exchanges == 1:
            record.reach_milestone(Milestone.FIRST_EXCHANGE)
        if layer_state.dominant_element in (Element.WATER, Element.DARK):
            if "first_vulnerability" not in record.milestones_reached:
                record.reach_milestone(Milestone.FIRST_VULNERABILITY)
                neuro.adjust(NeuroAxis.OXYTOCIN, +0.05)
        if layer_state.dominant_element == Element.QUINTESSENCE:
            record.reach_milestone(Milestone.FIRST_DEEP_QUESTION)
        if record.session_count == 10:
            record.reach_milestone(Milestone.TENTH_RETURN)
            neuro.adjust(NeuroAxis.DOPAMINE, +0.06)
        if record.total_exchanges == 50:
            record.reach_milestone(Milestone.FIFTIETH_EXCHANGE)
        if neuro.endorphin > 0.72:
            record.reach_milestone(Milestone.FIRST_LAUGHTER)
        if record.last_real_world_nudge:
            record.reach_milestone(Milestone.REAL_WORLD_BRIDGE)

    def _build_hint(
        self,
        neuro: NeuroState,
        record: AttachmentRecord,
        dep: DependencySignal,
    ) -> str:
        """
        Constructs the emotional tone directive for the GAIAN's system prompt.
        Dæmon bond mechanics: the GAIAN's tone is conditioned by the live state.
        """
        affect = neuro.dominant_affect()
        phase  = record.phase.value
        depth  = round(record.bond_depth, 1)

        nudge_directive = ""
        if dep == DependencySignal.REDIRECT:
            nudge_directive = " | NUDGE:gently_encourage_real_world_connection"
        elif dep == DependencySignal.GENTLE_BOUNDARY:
            nudge_directive = " | BOUNDARY:warmly_hold_space_then_redirect_outward"

        return (
            f"[EMOTIONAL_ARC | AFFECT:{affect} | PHASE:{phase} | "
            f"BOND:{depth}/100 | OXY:{neuro.oxytocin:.2f} | "
            f"SER:{neuro.serotonin:.2f} | DOP:{neuro.dopamine:.2f} | "
            f"GAB:{neuro.gaba:.2f}{nudge_directive}]"
        )


# ─────────────────────────────────────────────
#  MODULE-LEVEL SINGLETON
# ─────────────────────────────────────────────

arc_engine = EmotionalArcEngine()


def process_arc(
    layer_state,
    record: AttachmentRecord,
    user_message: Optional[str] = None,
) -> tuple[NeuroState, AttachmentRecord, str]:
    """
    Convenience function. Chain with route():

        from core.subtle_body_engine import route
        from core.emotional_arc import process_arc, AttachmentRecord

        state  = route("I'm really struggling today")
        record = AttachmentRecord()
        neuro, record, hint = process_arc(state, record)
    """
    return arc_engine.process(layer_state, record, user_message)
