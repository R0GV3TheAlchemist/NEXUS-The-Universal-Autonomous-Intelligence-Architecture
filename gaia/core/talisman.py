"""
gaia/core/talisman.py

Talisman Object v2  —  coherence anchors for GAIA-OS.

Canon anchors:
  - GAIA_TALISMAN_OBJECT.md   (sealed 2026-06-17  —  Phase 1 canon)
  - Issue #580  (Talisman Object)
  - Issue #576  (GAIAState)
  - Issue #568  (D6 Meta-Coherence Engine)
  - Issue #578  (Architect Protocol — human sovereignty absolute)

Design rules (v2):
  - Phase 1 is DIGITAL ONLY and PERSONAL ONLY.
  - A Talisman never bypasses D6; it nudges probes and lets D6 decide.
  - Maximum 7 active talismans at any time (MAX_ACTIVE_TALISMANS).
  - Total coherence boost capped at 0.08 (COHERENCE_BOOST_CAP) —
    also enforced by D6, but enforced here too for belt-and-suspenders.
  - Over-activation (count > SAFE_ACTIVATION_THRESHOLD) applies stress_draw.
  - revocable_consent is always True. Non-negotiable.
  - validated=False until validate() is called with a proof document.
    Unvalidated talismans receive 50 % boost reduction.
  - Physical layer (Phase 3) held in Research Incubator (#577).

For the Good and the Greater Good.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


# ---------------------------------------------------------------------------
# Canon constants
# ---------------------------------------------------------------------------

MAX_ACTIVE_TALISMANS: int = 7
"""Maximum number of simultaneously active talismans (canon: GAIA_TALISMAN_OBJECT.md)."""

COHERENCE_BOOST_CAP: float = 0.08
"""Maximum total coherence boost across ALL active talismans (canon, also enforced in D6)."""

SAFE_ACTIVATION_THRESHOLD: int = 12
"""Lifetime activation count before stress_draw is applied on each subsequent activation."""

UNVALIDATED_BOOST_FACTOR: float = 0.50
"""Unvalidated talismans receive this fraction of their declared coherence_boost."""

ANCHOR_MAX_CYCLES: int = 1
"""ANCHOR coherence_function is limited to this many D6 cycles (canon)."""


# ---------------------------------------------------------------------------
# Enums — all values match the canonical JSON schema
# ---------------------------------------------------------------------------

class ActivationState(str, Enum):
    """maps to schema field: activation_state"""
    INACTIVE  = "inactive"
    ACTIVE    = "active"
    DEPLETED  = "depleted"
    LOCKED    = "locked"


class DimensionalSignature(str, Enum):
    """maps to schema field: dimensional_signature"""
    D1      = "D1"
    D2      = "D2"
    D3      = "D3"
    D4      = "D4"
    D5      = "D5"
    D6      = "D6"
    D1_D3   = "D1-D3"
    D4_D6   = "D4-D6"
    D1_D6   = "D1-D6"   # full-spectrum — requires Architect validation


class CoherenceFunction(str, Enum):
    """
    maps to schema field: coherence_function

    GROUND   — raises targeted d_health by boost amount
    AMPLIFY  — multiplies boost × 1.5 on targeted dimension
    STABILIZE — prevents targeted probe falling below 0.75 for one D6 cycle
    CLEAR    — reduces entropy by up to 0.05
    BRIDGE   — equalises two probes (pulls lower toward higher)
    ANCHOR   — locks mode for one D6 cycle (CANNOT lock PROTECT)
    """
    GROUND    = "GROUND"
    AMPLIFY   = "AMPLIFY"
    STABILIZE = "STABILIZE"
    CLEAR     = "CLEAR"
    BRIDGE    = "BRIDGE"
    ANCHOR    = "ANCHOR"


class TalismanLayer(str, Enum):
    """maps to schema field: layer"""
    DIGITAL  = "digital"
    PHYSICAL = "physical"
    BOTH     = "both"


class TalismanElement(str, Enum):
    """maps to resonance_metadata.element"""
    FIRE    = "Fire"
    WATER   = "Water"
    EARTH   = "Earth"
    AIR     = "Air"
    AETHER  = "Aether"
    VOID    = "Void"


class LunarPhase(str, Enum):
    """maps to resonance_metadata.lunar_phase"""
    NEW              = "new"
    WAXING_CRESCENT  = "waxing_crescent"
    FIRST_QUARTER    = "first_quarter"
    WAXING_GIBBOUS   = "waxing_gibbous"
    FULL             = "full"
    WANING_GIBBOUS   = "waning_gibbous"
    LAST_QUARTER     = "last_quarter"
    WANING_CRESCENT  = "waning_crescent"


# ---------------------------------------------------------------------------
# ResonanceMetadata
# ---------------------------------------------------------------------------

@dataclass
class ResonanceMetadata:
    """
    Corresponds to schema block: resonance_metadata.
    All fields optional — Phase 1 is digital-first, not physics-first.
    """
    element:    Optional[TalismanElement] = None
    archetype:  str                        = ""
    lunar_phase: Optional[LunarPhase]     = None
    frequency:  Optional[float]            = None   # Hz

    def to_json(self) -> dict:
        return {
            "element":    self.element.value if self.element else None,
            "archetype":  self.archetype,
            "lunar_phase": self.lunar_phase.value if self.lunar_phase else None,
            "frequency":  self.frequency,
        }

    @classmethod
    def from_json(cls, data: dict) -> ResonanceMetadata:
        el = data.get("element")
        lp = data.get("lunar_phase")
        return cls(
            element     = TalismanElement(el) if el else None,
            archetype   = data.get("archetype", ""),
            lunar_phase = LunarPhase(lp) if lp else None,
            frequency   = data.get("frequency"),
        )


# ---------------------------------------------------------------------------
# SovereigntyFlags
# ---------------------------------------------------------------------------

@dataclass
class SovereigntyFlags:
    """
    Corresponds to schema block: sovereignty_flags.
    revocable_consent is ALWAYS True. Do not change this.
    transferable is ALWAYS False in Phase 1.
    """
    revocable_consent: bool = True
    owner:             str  = ""
    transferable:      bool = False

    def __post_init__(self) -> None:
        # Enforce canon rules — cannot be overridden by callers
        object.__setattr__(self, "revocable_consent", True)
        object.__setattr__(self, "transferable", False)

    def to_json(self) -> dict:
        return {
            "revocable_consent": True,
            "owner":             self.owner,
            "transferable":      False,
        }

    @classmethod
    def from_json(cls, data: dict) -> SovereigntyFlags:
        return cls(owner=data.get("owner", ""))


# ---------------------------------------------------------------------------
# Talisman  —  the primary object
# ---------------------------------------------------------------------------

@dataclass
class Talisman:
    """
    A coherence anchor for GAIA-OS.

    Holds a dimensional signature and a coherence function.
    When activated, it is registered in GAIAState.active_talismans
    and the D6 engine applies _talisman_coherence_boost() on the next cycle.

    The talisman is a tool, never a dependency.
    Human sovereignty is absolute.

    Phase 1: digital + personal only.
    Phase 3 (physical layer) held in Research Incubator (#577).
    """

    # ---- Required at creation -----------------------------------------------
    name:                  str
    dimensional_signature: DimensionalSignature
    coherence_function:    CoherenceFunction

    # ---- Optional at creation — have defaults --------------------------------
    id:               str                  = field(default_factory=lambda: str(uuid4()))
    archetype:        str                  = ""
    coherence_boost:  float                = 0.05
    stress_draw:      float                = 0.02
    layer:            TalismanLayer        = TalismanLayer.DIGITAL
    phase:            int                  = 1
    linked_canon:     list[str]            = field(default_factory=list)
    qr_nfc_link:      Optional[str]        = None
    notes:            str                  = ""

    # ---- State fields (managed by activate/deactivate/validate) -------------
    activation_state:  ActivationState     = ActivationState.INACTIVE
    activation_count:  int                 = 0
    validated:         bool                = False
    created:           datetime            = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activated:    Optional[datetime]  = None

    # ---- Nested objects -----------------------------------------------------
    resonance_metadata: ResonanceMetadata  = field(default_factory=ResonanceMetadata)
    sovereignty_flags:  SovereigntyFlags   = field(default_factory=SovereigntyFlags)

    def __post_init__(self) -> None:
        # Clamp coherence_boost to canon range [0.0, 0.08]
        self.coherence_boost = max(0.0, min(COHERENCE_BOOST_CAP, self.coherence_boost))
        # Clamp stress_draw to canon range [0.0, 0.05]
        self.stress_draw = max(0.0, min(0.05, self.stress_draw))
        # Full-spectrum talismans require Architect validation before activation
        if self.dimensional_signature == DimensionalSignature.D1_D6:
            self.validated = False  # always starts unvalidated

    # -----------------------------------------------------------------------
    # Effective boost (accounts for validation state)
    # -----------------------------------------------------------------------

    @property
    def effective_boost(self) -> float:
        """Returns coherence_boost adjusted for validation state.

        Unvalidated talismans receive UNVALIDATED_BOOST_FACTOR (50 %) of
        their declared boost. D6 also enforces the global cap across all
        active talismans, but this property is the per-talisman value.
        """
        if not self.validated:
            return self.coherence_boost * UNVALIDATED_BOOST_FACTOR
        return self.coherence_boost

    @property
    def is_overused(self) -> bool:
        """True when activation_count exceeds SAFE_ACTIVATION_THRESHOLD."""
        return self.activation_count > SAFE_ACTIVATION_THRESHOLD

    # -----------------------------------------------------------------------
    # activate()
    # -----------------------------------------------------------------------

    def activate(self, *, owner_id: str = "", run_cycle: bool = True) -> dict:
        """
        Activate this talisman.

        Steps:
          1. Guard checks (locked / depleted / max active count).
          2. Set activation_state = ACTIVE.
          3. Increment activation_count and record last_activated.
          4. If is_overused: call state_store.run_d6_cycle(stress=current+stress_draw).
          5. Register self.id in GAIAState.active_talismans via
             state_store.update_talismans().
          6. Return a result dict with decision summary.

        Args:
            owner_id:   GAIAN ID for sovereignty check (Phase 2 will enforce).
            run_cycle:  If True (default), D6 runs immediately after activation.

        Returns:
            dict with keys: success, talisman_id, mode, interventions, warning.
        """
        from gaia.core import state_store  # lazy import — avoids circular at module load

        # ---- Guard: locked --------------------------------------------------
        if self.activation_state == ActivationState.LOCKED:
            return {
                "success":      False,
                "talisman_id":  self.id,
                "warning":      "Talisman is locked. Architect must unlock it.",
                "mode":         state_store.get_mode(),
                "interventions": [],
            }

        # ---- Guard: depleted ------------------------------------------------
        if self.activation_state == ActivationState.DEPLETED:
            return {
                "success":      False,
                "talisman_id":  self.id,
                "warning":      "Talisman is depleted. Recharge required before activation.",
                "mode":         state_store.get_mode(),
                "interventions": [],
            }

        # ---- Guard: max active talismans ------------------------------------
        current_state = state_store.get_state()
        current_active_ids: list[str] = list(current_state.active_talismans or [])
        if self.id not in current_active_ids and len(current_active_ids) >= MAX_ACTIVE_TALISMANS:
            return {
                "success":      False,
                "talisman_id":  self.id,
                "warning": (
                    f"Maximum active talismans ({MAX_ACTIVE_TALISMANS}) reached. "
                    "Deactivate one before activating another."
                ),
                "mode":         state_store.get_mode(),
                "interventions": [],
            }

        # ---- Activate -------------------------------------------------------
        self.activation_state = ActivationState.ACTIVE
        self.activation_count += 1
        self.last_activated    = datetime.now(timezone.utc)

        warning: Optional[str] = None

        # ---- Overuse: apply stress_draw -------------------------------------
        if self.is_overused:
            current_stress = current_state.stress
            new_stress = min(1.0, current_stress + self.stress_draw)
            state_store.run_d6_cycle(stress=new_stress)
            warning = (
                f"Talisman over-activation detected (count={self.activation_count}). "
                f"stress_draw={self.stress_draw:.3f} applied to GAIAState."
            )

        # ---- Register in GAIAState ------------------------------------------
        if self.id not in current_active_ids:
            current_active_ids.append(self.id)

        decision = state_store.update_talismans(
            active_talismans=current_active_ids,
            run_cycle=run_cycle,
        )

        result: dict = {
            "success":      True,
            "talisman_id":  self.id,
            "mode":         decision.next_state.mode.value if decision else state_store.get_mode(),
            "interventions": decision.interventions if decision else [],
        }
        if warning:
            result["warning"] = warning
        return result

    # -----------------------------------------------------------------------
    # deactivate()
    # -----------------------------------------------------------------------

    def deactivate(self, *, run_cycle: bool = True) -> dict:
        """
        Deactivate this talisman.

        Steps:
          1. Set activation_state = INACTIVE.
          2. Remove self.id from GAIAState.active_talismans via
             state_store.update_talismans().
          3. Return a result dict with decision summary.

        The talisman is never deleted here — only its active registration
        is removed from GAIAState. The talisman object persists in
        talisman_store for history and future reactivation.

        Args:
            run_cycle: If True (default), D6 runs after deactivation.

        Returns:
            dict with keys: success, talisman_id, mode, interventions.
        """
        from gaia.core import state_store

        self.activation_state = ActivationState.INACTIVE

        current_state = state_store.get_state()
        updated_ids = [
            tid for tid in (current_state.active_talismans or [])
            if tid != self.id
        ]

        decision = state_store.update_talismans(
            active_talismans=updated_ids,
            run_cycle=run_cycle,
        )

        return {
            "success":       True,
            "talisman_id":   self.id,
            "mode":          decision.next_state.mode.value if decision else state_store.get_mode(),
            "interventions": decision.interventions if decision else [],
        }

    # -----------------------------------------------------------------------
    # validate()
    # -----------------------------------------------------------------------

    def validate(
        self,
        *,
        proof_text: str = "",
        proof_dir: str = "proofs/talismans",
    ) -> dict:
        """
        Validate this talisman and write a proof stub.

        Steps:
          1. Set validated = True.
          2. Write a Markdown proof document to {proof_dir}/{self.id}.md.
          3. Return a result dict.

        A validated talisman receives full coherence_boost (not 50 %-reduced).
        Full-spectrum (D1-D6) talismans require explicit Architect validation
        before they can be activated at full boost.

        Args:
            proof_text: Optional human-authored proof / intention statement.
            proof_dir:  Directory where the proof file is written.
                        Defaults to proofs/talismans/ (relative to CWD).

        Returns:
            dict with keys: success, talisman_id, proof_path, validated.
        """
        self.validated = True

        os.makedirs(proof_dir, exist_ok=True)
        proof_path = os.path.join(proof_dir, f"{self.id}.md")

        proof_content = (
            f"# Talisman Proof: {self.name}\n"
            f"\n"
            f"**Talisman ID:** `{self.id}`  \n"
            f"**Dimensional Signature:** {self.dimensional_signature.value}  \n"
            f"**Coherence Function:** {self.coherence_function.value}  \n"
            f"**Validated at:** {datetime.now(timezone.utc).isoformat()}  \n"
            f"\n"
            f"## Intention Statement\n"
            f"\n"
            f"{proof_text if proof_text else '_No proof text provided._'}\n"
            f"\n"
            f"---\n"
            f"\n"
            f"*For the Good and the Greater Good.*  \n"
            f"*So Be It.* \u2764\ufe0f\n"
        )

        with open(proof_path, "w", encoding="utf-8") as fh:
            fh.write(proof_content)

        return {
            "success":      True,
            "talisman_id":  self.id,
            "proof_path":   proof_path,
            "validated":    True,
        }

    # -----------------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------------

    def to_json(self) -> dict:
        """Full round-trip serialisation matching the canonical JSON schema."""
        return {
            "id":                    self.id,
            "name":                  self.name,
            "dimensional_signature": self.dimensional_signature.value,
            "coherence_function":    self.coherence_function.value,
            "resonance_metadata":    self.resonance_metadata.to_json(),
            "linked_canon":          self.linked_canon,
            "sovereignty_flags":     self.sovereignty_flags.to_json(),
            "layer":                 self.layer.value,
            "qr_nfc_link":           self.qr_nfc_link,
            "activation_state":      self.activation_state.value,
            "coherence_boost":       self.coherence_boost,
            "effective_boost":       self.effective_boost,
            "stress_draw":           self.stress_draw,
            "created":               self.created.isoformat(),
            "last_activated":        self.last_activated.isoformat() if self.last_activated else None,
            "activation_count":      self.activation_count,
            "validated":             self.validated,
            "phase":                 self.phase,
            "archetype":             self.archetype,
            "notes":                 self.notes,
        }

    @classmethod
    def from_json(cls, data: dict) -> Talisman:
        """Reconstruct a Talisman from a canonical JSON dict."""
        t = cls(
            id                    = data["id"],
            name                  = data["name"],
            dimensional_signature = DimensionalSignature(data["dimensional_signature"]),
            coherence_function    = CoherenceFunction(data["coherence_function"]),
            coherence_boost       = data.get("coherence_boost", 0.05),
            stress_draw           = data.get("stress_draw", 0.02),
            layer                 = TalismanLayer(data.get("layer", "digital")),
            phase                 = data.get("phase", 1),
            linked_canon          = data.get("linked_canon", []),
            qr_nfc_link           = data.get("qr_nfc_link"),
            archetype             = data.get("archetype", ""),
            notes                 = data.get("notes", ""),
            activation_state      = ActivationState(data.get("activation_state", "inactive")),
            activation_count      = data.get("activation_count", 0),
            validated             = data.get("validated", False),
            resonance_metadata    = ResonanceMetadata.from_json(
                data.get("resonance_metadata", {})
            ),
            sovereignty_flags     = SovereigntyFlags.from_json(
                data.get("sovereignty_flags", {})
            ),
        )
        # Restore timestamps without triggering __post_init__ re-clamp
        created_raw = data.get("created")
        if created_raw:
            t.created = datetime.fromisoformat(created_raw)
        last_act_raw = data.get("last_activated")
        if last_act_raw:
            t.last_activated = datetime.fromisoformat(last_act_raw)
        return t

    def __repr__(self) -> str:
        return (
            f"Talisman(id={self.id[:8]!r}, name={self.name!r}, "
            f"sig={self.dimensional_signature.value}, "
            f"fn={self.coherence_function.value}, "
            f"state={self.activation_state.value}, "
            f"validated={self.validated})"
        )
