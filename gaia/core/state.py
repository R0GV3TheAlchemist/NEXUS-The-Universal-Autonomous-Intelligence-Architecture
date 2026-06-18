"""
gaia/core/state.py
==================
GAIA Core State — GAIAState & D6 Mode Engine
Canon reference: C52 Part VI, GAIA_D6_META_COHERENCE_ENGINE.md
Issues: #571, #576

This is the single source of truth for GAIA's runtime operational state.
All subsystems that need to read or write system state MUST go through
this module. No subsystem may maintain its own parallel dimensional state.
(C52-GOV-06)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# D6 Operational Modes (from GAIA_D6_META_COHERENCE_ENGINE.md)
# ---------------------------------------------------------------------------

class GAIAMode(str, Enum):
    """
    D6 Meta-Coherence Engine operational modes.

    Each mode maps to a dominant dimensional register (C52 Part II §2.3):
      BUILD      → D3 (Mental) + D1 (Physical energy required)
      RESEARCH   → D3 (Mental) + D5 (Soul curiosity)
      REFLECT    → D2 (Emotional) + D5 (Soul)
      CREATE     → D3 + D5 + D6 approaching
      REST       → D1 (Physical recovery)
      RECOVER    → D1 + D2 (Physical + Emotional healing)
      PROTECT    → D2 (Emotional safety) + D4 (Social boundary)
      INTEGRATE  → D6 (Unity) — all dimensions harmonized
    """
    BUILD = "BUILD"
    RESEARCH = "RESEARCH"
    REFLECT = "REFLECT"
    CREATE = "CREATE"
    REST = "REST"
    RECOVER = "RECOVER"
    PROTECT = "PROTECT"
    INTEGRATE = "INTEGRATE"


# Backward-compat alias: tests and state_store import GAIAOperationalMode
GAIAOperationalMode = GAIAMode


# ---------------------------------------------------------------------------
# GAIAState — the central state object
# ---------------------------------------------------------------------------

@dataclass
class GAIAState:
    """
    Central operational state for GAIA-OS.

    All scalar fields are normalized to [0.0, 1.0] unless noted.

    Dimensional mapping (C52 Part VI §6.1):
      D1 Physical    → energy
      D2 Emotional   → coherence, stress
      D3 Mental      → learning_rate, exploration_rate
      D4 Social      → conservation_rate
      D5 Soul        → (qualitative — read from interaction, not scalar)
      D6 Unity       → emergent from field combination + mode
      Cross-dim      → entropy, mode
      Biometric      → personal_coherence (Issue #153, C135)
    """

    # --- D1 Physical ---
    energy: float = 0.8
    """
    Physical vitality and capacity for sustained action.
    0.0 = completely depleted / emergency
    1.0 = full vitality
    """

    # --- D2 Emotional ---
    coherence: float = 0.8
    """
    Emotional and systemic coherence. Primary coherence signal.
    0.0 = fragmented / dysregulated
    1.0 = fully coherent
    """

    stress: float = 0.2
    """
    Current stress load. Inverse of ease.
    0.0 = none
    1.0 = critical / emergency
    """

    # --- D3 Mental ---
    learning_rate: float = 0.7
    """
    Openness and capacity for new learning.
    0.0 = closed / saturated
    1.0 = maximally open
    """

    exploration_rate: float = 0.5
    """
    Balance between exploration (novel paths) and exploitation (known paths).
    0.0 = conservative / exploit only
    1.0 = maximum exploration
    """

    # --- D4 Social ---
    conservation_rate: float = 0.3
    """
    Social energy conservation / withdrawal.
    0.0 = fully giving / outward
    1.0 = fully withdrawn / isolated
    """

    # --- Cross-dimensional ---
    entropy: float = 0.2
    """
    System disorder across all dimensions.
    0.0 = ordered / structured
    1.0 = chaotic / incoherent
    Affects all dimensions simultaneously.
    """

    mode: GAIAMode = GAIAMode.BUILD
    """
    Current D6 Meta-Coherence Engine operational mode.
    Determines which dimensions are primary and which engine behaviors activate.
    """

    # --- Biometric / personal coherence (Issue #153, C135 telemetry) ---
    personal_coherence: float = 0.0
    """
    Biometric coherence signal from the Operator's body field.
    Sourced from BiometricCoherenceEngine (Issue #153).
    0.0 = no biometric input / baseline
    1.0 = maximum personal coherence (HRV-derived, Schumann-aligned)
    Does not affect _validate() scalar bounds — already in [0.0, 1.0].
    """

    # --- Metadata ---
    session_id: Optional[str] = None
    gaian_id: Optional[str] = None
    updated_at: float = field(default_factory=time.time)
    history: List[Dict[str, Any]] = field(default_factory=list, repr=False)

    def __post_init__(self):
        self._validate()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate(self):
        """Enforce canonical field bounds."""
        scalar_fields = [
            "energy", "coherence", "stress", "learning_rate",
            "exploration_rate", "conservation_rate", "entropy",
            "personal_coherence",
        ]
        for fname in scalar_fields:
            v = getattr(self, fname)
            if not (0.0 <= v <= 1.0):
                raise ValueError(
                    f"GAIAState.{fname} must be in [0.0, 1.0], got {v}. "
                    f"(C52-GOV-06: GAIAState is the single source of truth — "
                    f"invalid state is a canonical violation.)"
                )

    # ------------------------------------------------------------------
    # Dimensional health checks (C52 Part VI §6.2)
    # ------------------------------------------------------------------

    @property
    def d1_critical(self) -> bool:
        """D1 Physical critical — all other dimensions yield. (C52-GOV-02)"""
        return self.energy < 0.15

    @property
    def d2_distress(self) -> bool:
        """D2 Emotional distress — hold before doing."""
        return self.stress > 0.75

    @property
    def d3_saturated(self) -> bool:
        """D3 Mental saturated — simplify, summarize, or invite rest."""
        return self.entropy > 0.70 and self.energy < 0.30

    @property
    def d4_isolated(self) -> bool:
        """D4 Social isolation signal."""
        return self.conservation_rate > 0.85

    @property
    def d6_approaching(self) -> bool:
        """
        D6 Unity approaching — Meta-Field proximity.
        All foundations healthy and mode is INTEGRATE.
        """
        return (
            self.coherence >= 0.85
            and self.stress <= 0.15
            and self.entropy <= 0.15
            and self.mode == GAIAMode.INTEGRATE
        )

    @property
    def dimensional_health(self) -> Dict[str, bool]:
        """Snapshot of all dimensional health checks."""
        return {
            "D1_critical": self.d1_critical,
            "D2_distress": self.d2_distress,
            "D3_saturated": self.d3_saturated,
            "D4_isolated": self.d4_isolated,
            "D6_approaching": self.d6_approaching,
        }

    # ------------------------------------------------------------------
    # Priority cascade (C52 Part II §2.2)
    # ------------------------------------------------------------------

    @property
    def priority_dimension(self) -> str:
        """
        Returns the highest-priority dimension that currently signals need,
        following the Dimensional Priority Cascade:
          D1 (critical) > D2 (distress) > D6 (flow) > D5 (soul) > D4 (social) > D3 (default)
        """
        if self.d1_critical:
            return "D1_PHYSICAL_CRITICAL"
        if self.d2_distress:
            return "D2_EMOTIONAL_DISTRESS"
        if self.d6_approaching:
            return "D6_UNITY_FLOW"
        if self.d4_isolated:
            return "D4_SOCIAL_ISOLATION"
        if self.d3_saturated:
            return "D3_MENTAL_SATURATED"
        return "D3_OPERATIONAL"  # default

    # ------------------------------------------------------------------
    # D6 Meta-Coherence Engine — mode recommendation
    # ------------------------------------------------------------------

    def recommended_mode(self) -> GAIAMode:
        """
        Pure function: given current field values, what mode should GAIA be in?
        This is the D6 Meta-Coherence Engine's core decision function.

        Rule precedence (highest first):
          1. D1 critical → REST
          2. D2 distress → RECOVER or PROTECT
          3. Entropy critical → REFLECT
          4. D6 approaching → INTEGRATE
          5. High energy + high coherence + low stress → BUILD or CREATE
          6. High learning_rate + high exploration → RESEARCH
          7. Default → REFLECT
        """
        if self.d1_critical:
            return GAIAMode.REST

        if self.d2_distress:
            return GAIAMode.RECOVER if self.energy < 0.4 else GAIAMode.PROTECT

        if self.entropy > 0.70:
            return GAIAMode.REFLECT

        if self.d6_approaching:
            return GAIAMode.INTEGRATE

        if self.coherence >= 0.75 and self.energy >= 0.6 and self.stress <= 0.35:
            if self.exploration_rate >= 0.65:
                return GAIAMode.CREATE
            return GAIAMode.BUILD

        if self.learning_rate >= 0.7 and self.exploration_rate >= 0.6:
            return GAIAMode.RESEARCH

        return GAIAMode.REFLECT

    # ------------------------------------------------------------------
    # Mutation helpers (always record history)
    # ------------------------------------------------------------------

    def update(self, **kwargs) -> "GAIAState":
        """
        Apply field updates and record the prior state in history.
        Returns self for chaining.
        """
        self.history.append({
            "t": self.updated_at,
            "snapshot": self.to_dict(include_history=False),
        })

        for k, v in kwargs.items():
            if not hasattr(self, k):
                raise AttributeError(f"GAIAState has no field '{k}'")
            setattr(self, k, v)

        self.updated_at = time.time()
        self._validate()
        return self

    def apply_recommended_mode(self) -> "GAIAState":
        """Auto-apply the D6 engine's recommended mode. Returns self for chaining."""
        new_mode = self.recommended_mode()
        if new_mode != self.mode:
            self.update(mode=new_mode)
        return self

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self, include_history: bool = True) -> Dict[str, Any]:
        d = {
            "energy": self.energy,
            "coherence": self.coherence,
            "stress": self.stress,
            "learning_rate": self.learning_rate,
            "exploration_rate": self.exploration_rate,
            "conservation_rate": self.conservation_rate,
            "entropy": self.entropy,
            "personal_coherence": self.personal_coherence,
            "mode": self.mode.value,
            "session_id": self.session_id,
            "gaian_id": self.gaian_id,
            "updated_at": self.updated_at,
            "dimensional_health": self.dimensional_health,
            "priority_dimension": self.priority_dimension,
        }
        if include_history:
            d["history"] = self.history
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GAIAState":
        """Reconstruct from serialized dict (e.g., from DB or API payload)."""
        mode_val = data.get("mode", "BUILD")
        mode = GAIAMode(mode_val) if isinstance(mode_val, str) else mode_val
        return cls(
            energy=data.get("energy", 0.8),
            coherence=data.get("coherence", 0.8),
            stress=data.get("stress", 0.2),
            learning_rate=data.get("learning_rate", 0.7),
            exploration_rate=data.get("exploration_rate", 0.5),
            conservation_rate=data.get("conservation_rate", 0.3),
            entropy=data.get("entropy", 0.2),
            personal_coherence=data.get("personal_coherence", 0.0),
            mode=mode,
            session_id=data.get("session_id"),
            gaian_id=data.get("gaian_id"),
            updated_at=data.get("updated_at", time.time()),
        )

    def __repr__(self) -> str:
        h = self.dimensional_health
        flags = ", ".join(k for k, v in h.items() if v) or "nominal"
        return (
            f"GAIAState(mode={self.mode.value}, "
            f"coherence={self.coherence:.2f}, energy={self.energy:.2f}, "
            f"stress={self.stress:.2f}, entropy={self.entropy:.2f}, "
            f"personal_coherence={self.personal_coherence:.2f}, "
            f"flags=[{flags}])"
        )


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------

def default_state(gaian_id: Optional[str] = None,
                  session_id: Optional[str] = None) -> GAIAState:
    """Healthy baseline GAIAState for a new session."""
    return GAIAState(
        energy=0.8,
        coherence=0.8,
        stress=0.2,
        learning_rate=0.7,
        exploration_rate=0.5,
        conservation_rate=0.3,
        entropy=0.2,
        personal_coherence=0.0,
        mode=GAIAMode.BUILD,
        gaian_id=gaian_id,
        session_id=session_id,
    )


def depleted_state(gaian_id: Optional[str] = None) -> GAIAState:
    """D1-critical state — used in testing recovery pathways."""
    return GAIAState(
        energy=0.10,
        coherence=0.4,
        stress=0.8,
        learning_rate=0.2,
        exploration_rate=0.1,
        conservation_rate=0.9,
        entropy=0.7,
        personal_coherence=0.0,
        mode=GAIAMode.RECOVER,
        gaian_id=gaian_id,
    )


def integrate_state(gaian_id: Optional[str] = None) -> GAIAState:
    """D6-approaching state — used in testing Meta-Field / flow conditions."""
    return GAIAState(
        energy=0.9,
        coherence=0.95,
        stress=0.05,
        learning_rate=0.85,
        exploration_rate=0.75,
        conservation_rate=0.2,
        entropy=0.05,
        personal_coherence=0.0,
        mode=GAIAMode.INTEGRATE,
        gaian_id=gaian_id,
    )
