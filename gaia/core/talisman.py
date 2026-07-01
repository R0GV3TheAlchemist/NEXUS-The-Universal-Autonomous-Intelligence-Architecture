"""
gaia/core/talisman.py
=====================
GAIA Talisman Object — Coherence Anchors
Canon reference: #580, C52, TFT-01 (Meta-Field anchor concept)
Issues: #580, #576

A Talisman is a coherence anchor — a digital or physical object that:
  - Holds a specific dimensional signature
  - Grounds the Architect and GAIANs during high-D work
  - Bridges the physical and digital layers of GAIA
  - Provides a stable reference point when the system is under coherence stress

This is not mysticism. This is engineering with intention.

Phase 1 (this file): Schema, definition, GAIAState integration.
Phase 2: UI, QR/NFC linking, GoldenCompassEngine integration.
Phase 3 (Incubator): Physical layer — crystal-embedded sigils, printed symbols.

Sovereignty note (#578, AAD-GOV-05):
  A talisman is always OWNED by a GAIAN. It is never owned by GAIA.
  Revocable consent is always true. Talismans are tools, not dependencies.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from gaia.core.state import GAIAState


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TalismanLayer(str, Enum):
    """Whether this talisman exists digitally, physically, or both."""
    DIGITAL = "digital"
    PHYSICAL = "physical"
    BOTH = "both"


class DimensionalSignature(str, Enum):
    """
    Which dimensional layer (C52) this talisman is primarily anchored to.
    D1–D6 are runtime-supported. D7–D12 are doctrinal/contextual.
    """
    D1 = "D1"   # Physical
    D2 = "D2"   # Emotional
    D3 = "D3"   # Mental
    D4 = "D4"   # Social
    D5 = "D5"   # Soul / Meaning
    D6 = "D6"   # Unity / Source
    D7 = "D7"   # Noosphere
    D8 = "D8"   # Morphic
    D9 = "D9"   # Elemental
    D10 = "D10" # Galactic
    D11 = "D11" # Universal
    D12 = "D12" # Absolute


class CoherenceFunction(str, Enum):
    """
    What this talisman does to GAIAState when activated.
    Based on #580 integration spec.
    """
    GROUND = "GROUND"           # Raises coherence, lowers entropy
    PROTECT = "PROTECT"         # Raises conservation_rate, lowers stress
    AMPLIFY = "AMPLIFY"         # Raises energy, raises exploration_rate
    RESTORE = "RESTORE"         # Raises energy + coherence; lowers stress
    FOCUS = "FOCUS"             # Raises learning_rate, lowers exploration_rate (depth over breadth)
    OPEN = "OPEN"               # Raises exploration_rate, raises learning_rate
    INTEGRATE = "INTEGRATE"     # Moves toward D6 state: all balanced, entropy low
    WITNESS = "WITNESS"         # No state mutation — pure presence marker


# ---------------------------------------------------------------------------
# Resonance Metadata
# ---------------------------------------------------------------------------

@dataclass
class ResonanceMetadata:
    """
    Symbolic / cosmological metadata for the talisman.
    Matches #580 schema: resonance_metadata block.

    All fields are optional — a talisman is valid without resonance metadata.
    Resonance metadata enriches the talisman but does not change its runtime behavior.
    """
    element: Optional[str] = None       # e.g. "Fire", "Water", "Quintessence" (C27)
    archetype: Optional[str] = None     # e.g. "The Alchemist", "The Witness", "The Builder"
    lunar_phase: Optional[str] = None   # e.g. "New Moon", "Full Moon", "Waning Gibbous"
    frequency: Optional[float] = None   # Hz — symbolic resonant frequency
    notes: Optional[str] = None         # Free-form contextual note

    def to_dict(self) -> Dict[str, Any]:
        return {
            "element": self.element,
            "archetype": self.archetype,
            "lunar_phase": self.lunar_phase,
            "frequency": self.frequency,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ResonanceMetadata":
        return cls(
            element=d.get("element"),
            archetype=d.get("archetype"),
            lunar_phase=d.get("lunar_phase"),
            frequency=d.get("frequency"),
            notes=d.get("notes"),
        )


# ---------------------------------------------------------------------------
# Sovereignty Flags
# ---------------------------------------------------------------------------

@dataclass
class SovereigntyFlags:
    """
    Sovereignty and consent model for this talisman.
    From #580 sovereignty_flags block + Architect Protocol (#578).

    revocable_consent: always True. A GAIAN can always deactivate or delete
      their talisman. GAIA may never hold a talisman hostage.
    transferable: default False. Talismans are personal by default.
      Phase 2+ allows collective talismans with explicit consent.
    """
    owner: str                        # gaian_id of the GAIAN who owns this talisman
    revocable_consent: bool = True    # always True — constitutional requirement
    transferable: bool = False        # start personal-only per #580 Phase 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner": self.owner,
            "revocable_consent": self.revocable_consent,
            "transferable": self.transferable,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SovereigntyFlags":
        return cls(
            owner=d["owner"],
            revocable_consent=d.get("revocable_consent", True),
            transferable=d.get("transferable", False),
        )


# ---------------------------------------------------------------------------
# Talisman — the main object
# ---------------------------------------------------------------------------

@dataclass
class Talisman:
    """
    A coherence anchor for GAIA-OS.

    Full schema matches #580 proposed object schema.
    Phase 1: digital-only, personal-only, GAIAState integration.
    """

    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""

    # Dimensional and functional signature
    dimensional_signature: DimensionalSignature = DimensionalSignature.D6
    coherence_function: CoherenceFunction = CoherenceFunction.GROUND

    # Resonance and sovereignty
    resonance_metadata: ResonanceMetadata = field(default_factory=ResonanceMetadata)
    sovereignty_flags: SovereigntyFlags = field(
        default_factory=lambda: SovereigntyFlags(owner="")
    )

    # Canon linkage
    linked_canon: List[str] = field(default_factory=list)

    # Layer and physical linkage
    layer: TalismanLayer = TalismanLayer.DIGITAL
    qr_nfc_link: Optional[str] = None  # Phase 2 — QR/NFC URL or identifier

    # Lifecycle
    created: float = field(default_factory=time.time)
    validated: bool = False
    active: bool = False
    activated_at: Optional[float] = None
    deactivated_at: Optional[float] = None

    # Activation history (lightweight ledger)
    activation_log: List[Dict[str, Any]] = field(default_factory=list, repr=False)

    def activate(self, activated_by: Optional[str] = None) -> "Talisman":
        """
        Mark this talisman as active.
        Logs the activation event.
        The caller (TalismanEngine) is responsible for applying
        the coherence function to GAIAState.
        """
        if not self.active:
            self.active = True
            self.activated_at = time.time()
            self.activation_log.append({
                "event": "ACTIVATED",
                "t": self.activated_at,
                "by": activated_by or self.sovereignty_flags.owner,
            })
        return self

    def deactivate(self, deactivated_by: Optional[str] = None) -> "Talisman":
        """
        Mark this talisman as inactive.
        Logs the deactivation event.
        The caller (TalismanEngine) is responsible for reversing or
        softening state effects on GAIAState.
        """
        if self.active:
            self.active = False
            self.deactivated_at = time.time()
            self.activation_log.append({
                "event": "DEACTIVATED",
                "t": self.deactivated_at,
                "by": deactivated_by or self.sovereignty_flags.owner,
            })
        return self

    def validate(self) -> "Talisman":
        """Mark this talisman as validated (Phase 2 proof requirement)."""
        self.validated = True
        self.activation_log.append({
            "event": "VALIDATED",
            "t": time.time(),
        })
        return self

    def to_dict(self, include_log: bool = True) -> Dict[str, Any]:
        d = {
            "id": self.id,
            "name": self.name,
            "dimensional_signature": self.dimensional_signature.value,
            "coherence_function": self.coherence_function.value,
            "resonance_metadata": self.resonance_metadata.to_dict(),
            "sovereignty_flags": self.sovereignty_flags.to_dict(),
            "linked_canon": self.linked_canon,
            "layer": self.layer.value,
            "qr_nfc_link": self.qr_nfc_link,
            "created": self.created,
            "validated": self.validated,
            "active": self.active,
            "activated_at": self.activated_at,
            "deactivated_at": self.deactivated_at,
        }
        if include_log:
            d["activation_log"] = self.activation_log
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Talisman":
        return cls(
            id=d.get("id", str(uuid.uuid4())),
            name=d.get("name", ""),
            dimensional_signature=DimensionalSignature(d.get("dimensional_signature", "D6")),
            coherence_function=CoherenceFunction(d.get("coherence_function", "GROUND")),
            resonance_metadata=ResonanceMetadata.from_dict(d.get("resonance_metadata") or {}),
            sovereignty_flags=SovereigntyFlags.from_dict(d.get("sovereignty_flags") or {"owner": ""}),
            linked_canon=d.get("linked_canon", []),
            layer=TalismanLayer(d.get("layer", "digital")),
            qr_nfc_link=d.get("qr_nfc_link"),
            created=d.get("created", time.time()),
            validated=d.get("validated", False),
            active=d.get("active", False),
            activated_at=d.get("activated_at"),
            deactivated_at=d.get("deactivated_at"),
            activation_log=d.get("activation_log", []),
        )

    def __repr__(self) -> str:
        status = "ACTIVE" if self.active else "inactive"
        return (
            f"Talisman(name='{self.name}', "
            f"dim={self.dimensional_signature.value}, "
            f"fn={self.coherence_function.value}, "
            f"layer={self.layer.value}, "
            f"status={status})"
        )


# ---------------------------------------------------------------------------
# TalismanEngine — applies talisman effects to GAIAState
# ---------------------------------------------------------------------------

_EFFECT_MAP: Dict[CoherenceFunction, Dict[str, float]] = {
    CoherenceFunction.GROUND: {
        "coherence": +0.08,
        "entropy": -0.08,
        "stress": -0.05,
    },
    CoherenceFunction.PROTECT: {
        "stress": -0.10,
        "conservation_rate": +0.10,
        "coherence": +0.03,
    },
    CoherenceFunction.AMPLIFY: {
        "energy": +0.10,
        "exploration_rate": +0.08,
        "learning_rate": +0.05,
    },
    CoherenceFunction.RESTORE: {
        "energy": +0.12,
        "coherence": +0.10,
        "stress": -0.12,
        "entropy": -0.05,
    },
    CoherenceFunction.FOCUS: {
        "learning_rate": +0.10,
        "exploration_rate": -0.05,
        "entropy": -0.08,
    },
    CoherenceFunction.OPEN: {
        "exploration_rate": +0.10,
        "learning_rate": +0.08,
        "conservation_rate": -0.05,
    },
    CoherenceFunction.INTEGRATE: {
        "coherence": +0.10,
        "entropy": -0.10,
        "stress": -0.08,
        "energy": +0.05,
    },
    CoherenceFunction.WITNESS: {},
}

_MISUSE_PENALTY: Dict[str, float] = {
    "stress": +0.08,
    "entropy": +0.05,
}
_MISUSE_THRESHOLD = 5


class TalismanEngine:
    """
    Applies talisman coherence functions to GAIAState.

    Lifecycle:
      1. engine.activate(talisman, state) — apply effects, mark active
      2. engine.deactivate(talisman, state) — gently reverse effects, mark inactive
      3. engine.apply_all_active(talismans, state) — batch re-apply on state restore

    Over-attachment detection:
      If a GAIAN activates the same talisman > _MISUSE_THRESHOLD times in a
      session, the engine logs a warning and applies a mild stress penalty.
      Talismans are tools, not dependencies. (Architect Protocol #578)
    """

    def activate(
        self,
        talisman: Talisman,
        state: "GAIAState",
        activated_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Activate a talisman and apply its coherence function to GAIAState."""
        if activated_by and activated_by != talisman.sovereignty_flags.owner:
            return {
                "event": "ACTIVATION_DENIED",
                "reason": "sovereignty_violation",
                "talisman_id": talisman.id,
                "requested_by": activated_by,
                "owner": talisman.sovereignty_flags.owner,
            }

        activation_count = sum(
            1 for e in talisman.activation_log if e.get("event") == "ACTIVATED"
        )
        over_attached = activation_count >= _MISUSE_THRESHOLD

        talisman.activate(activated_by)

        effects = _EFFECT_MAP.get(talisman.coherence_function, {})
        updates: Dict[str, float] = {}
        for field_name, delta in effects.items():
            current = getattr(state, field_name, None)
            if current is not None:
                new_val = max(0.0, min(1.0, current + delta))
                updates[field_name] = new_val

        penalty_applied = False
        if over_attached:
            for field_name, delta in _MISUSE_PENALTY.items():
                current = getattr(state, field_name, None)
                if current is not None:
                    penalized = max(0.0, min(1.0, current + delta))
                    updates[field_name] = penalized
            penalty_applied = True

        if updates:
            state.update(**updates)

        return {
            "event": "TALISMAN_ACTIVATED",
            "talisman_id": talisman.id,
            "talisman_name": talisman.name,
            "coherence_function": talisman.coherence_function.value,
            "dimensional_signature": talisman.dimensional_signature.value,
            "state_updates": updates,
            "over_attachment_warning": over_attached,
            "penalty_applied": penalty_applied,
            "t": time.time(),
        }

    def deactivate(
        self,
        talisman: Talisman,
        state: "GAIAState",
        deactivated_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Deactivate a talisman with soft 50% reversal of activation effects."""
        talisman.deactivate(deactivated_by)

        effects = _EFFECT_MAP.get(talisman.coherence_function, {})
        updates: Dict[str, float] = {}
        for field_name, delta in effects.items():
            current = getattr(state, field_name, None)
            if current is not None:
                reversal = -delta * 0.5
                new_val = max(0.0, min(1.0, current + reversal))
                updates[field_name] = new_val

        if updates:
            state.update(**updates)

        return {
            "event": "TALISMAN_DEACTIVATED",
            "talisman_id": talisman.id,
            "talisman_name": talisman.name,
            "state_updates": updates,
            "t": time.time(),
        }

    def apply_all_active(
        self,
        talismans: List[Talisman],
        state: "GAIAState",
    ) -> int:
        """Re-apply all currently active talismans to state. Returns count applied."""
        count = 0
        for t in talismans:
            if t.active:
                self.activate(t, state, activated_by=t.sovereignty_flags.owner)
                count += 1
        return count


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------

def make_talisman(
    name: str,
    owner: str,
    dimensional_signature: DimensionalSignature = DimensionalSignature.D6,
    coherence_function: CoherenceFunction = CoherenceFunction.GROUND,
    element: Optional[str] = None,
    archetype: Optional[str] = None,
    lunar_phase: Optional[str] = None,
    frequency: Optional[float] = None,
    linked_canon: Optional[List[str]] = None,
    layer: TalismanLayer = TalismanLayer.DIGITAL,
) -> Talisman:
    """Convenience factory for creating a new talisman."""
    return Talisman(
        name=name,
        dimensional_signature=dimensional_signature,
        coherence_function=coherence_function,
        resonance_metadata=ResonanceMetadata(
            element=element,
            archetype=archetype,
            lunar_phase=lunar_phase,
            frequency=frequency,
        ),
        sovereignty_flags=SovereigntyFlags(owner=owner),
        linked_canon=linked_canon or ["C52", "TFT-01", "#580"],
        layer=layer,
    )


ARCHITECT_GROUND_TALISMAN = make_talisman(
    name="The Alchemist's Anchor",
    owner="R0GV3TheAlchemist",
    dimensional_signature=DimensionalSignature.D6,
    coherence_function=CoherenceFunction.GROUND,
    element="Quintessence",
    archetype="The Alchemist",
    frequency=432.0,
    linked_canon=["C52", "TFT-01", "C50", "#580"],
)

ARCHITECT_BUILD_TALISMAN = make_talisman(
    name="The Builder's Focus",
    owner="R0GV3TheAlchemist",
    dimensional_signature=DimensionalSignature.D3,
    coherence_function=CoherenceFunction.FOCUS,
    element="Fire",
    archetype="The Builder",
    frequency=528.0,
    linked_canon=["C52", "#576", "#580"],
)

ARCHITECT_RESTORE_TALISMAN = make_talisman(
    name="The Well",
    owner="R0GV3TheAlchemist",
    dimensional_signature=DimensionalSignature.D1,
    coherence_function=CoherenceFunction.RESTORE,
    element="Water",
    archetype="The Healer",
    frequency=396.0,
    linked_canon=["C52", "TFT-01", "#576"],
)


# ---------------------------------------------------------------------------
# Legacy aliases — compatibility shim (D6 refactor)
# Enum is already imported at the top of this file.
# ---------------------------------------------------------------------------

class ActivationState(Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BURNED = "burned"


class LunarPhase(Enum):
    NEW = "new"
    WAXING = "waxing"
    FULL = "full"
    WANING = "waning"


class TalismanElement:
    FIRE = 'fire'
    WATER = 'water'
    EARTH = 'earth'
    AIR = 'air'
    AETHER = 'aether'


class TalismanRarity:
    COMMON = 'common'
    UNCOMMON = 'uncommon'
    RARE = 'rare'
    LEGENDARY = 'legendary'


class TalismanIntent:
    PROTECTION = 'protection'
    HEALING = 'healing'
    CLARITY = 'clarity'
    POWER = 'power'


class TalismanBond:
    NONE = 'none'
    WEAK = 'weak'
    MODERATE = 'moderate'
    STRONG = 'strong'
    FUSED = 'fused'


class CoherenceFunction:
    LINEAR = 'linear'
    EXPONENTIAL = 'exponential'
    RESONANT = 'resonant'


class DimensionalSignature:
    def __init__(self, dims: list = None):
        self.dims = dims or []


class TalismanLayer(Enum):
    PHYSICAL = 'physical'
    ETHERIC = 'etheric'
    ASTRAL = 'astral'
    MENTAL = 'mental'
    CAUSAL = 'causal'
    SOUL = 'soul'
    DIVINE = 'divine'
    DIGITAL = 'digital'


class TalismanStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'
    ARCHIVED = 'archived'
