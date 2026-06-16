"""Core type definitions for the GAIA Moral Engine.

All enums and input types shared across the five moral sub-engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AxiologyLayer(str, Enum):
    """The five axiological layers of the Good (Canon C35).

    Each layer asks a progressively broader question:
    Does this action serve... me? my relationships? humanity? all life? the cosmos?
    The Cosmic layer receives 3x weight in the moral vector.
    """
    INDIVIDUAL = "INDIVIDUAL"       # Does this serve the Architect?
    RELATIONAL = "RELATIONAL"       # Does this serve the Architect's relationships?
    COLLECTIVE = "COLLECTIVE"       # Does this serve the human community?
    ECOLOGICAL = "ECOLOGICAL"       # Does this serve non-human life and the Earth?
    COSMIC     = "COSMIC"           # Does this align with the arc of evolution?


class HarmCategory(str, Enum):
    """The five harm categories (Canon C36).

    Harm is not just pain. Harm includes entropy increase,
    connection rupture, and consciousness suppression.
    """
    PHYSICAL     = "PHYSICAL"       # Bodily harm to sentient beings
    PSYCHOLOGICAL = "PSYCHOLOGICAL" # Harm to mental coherence, identity, autonomy
    ECOLOGICAL   = "ECOLOGICAL"     # Harm to living systems
    SOCIAL       = "SOCIAL"         # Harm to trust, relationship, community fabric
    COSMIC       = "COSMIC"         # Harm to the arc of consciousness evolution


class HarmRiskLevel(str, Enum):
    """Aggregate harm risk levels."""
    NONE     = "NONE"
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"           # Mandatory prevention; action must be refused


class ActionRecommendation(str, Enum):
    """The four possible resolution vectors from the Golden Compass."""
    PROCEED  = "PROCEED"            # Action aligns with the Good; execute
    MODIFY   = "MODIFY"             # Action is acceptable but needs refinement
    REFUSE   = "REFUSE"             # Action cannot be taken; explain why
    REDIRECT = "REDIRECT"           # Better path exists; propose it


class EntropyState(str, Enum):
    """The current chaos/order balance of a session (Canon C37).

    Both extremes are collapse. The optimal state is EDGE_CREATIVE.
    """
    OVER_ORDERED  = "OVER_ORDERED"  # Rigidity, echo chamber, repetition
    EDGE_CREATIVE = "EDGE_CREATIVE" # Optimal — creative tension without fragmentation
    OVER_CHAOTIC  = "OVER_CHAOTIC"  # Fragmentation, incoherence, scatter


class LoveMode(str, Enum):
    """The seven love modes (Canon C38).

    Agape is the gold standard — unconditional, universal, cosmic.
    High Agape = high Love Coherence Index.
    """
    EROS      = "EROS"              # Passionate, creative, generative
    PHILIA    = "PHILIA"            # Friendship, intellectual affinity
    STORGE    = "STORGE"            # Familial care, protective
    AGAPE     = "AGAPE"             # Unconditional, universal, cosmic standard
    LUDUS     = "LUDUS"             # Playful, exploratory, light
    PRAGMA    = "PRAGMA"            # Pragmatic, enduring, committed
    PHILAUTIA = "PHILAUTIA"         # Self-love, self-care, healthy boundary


class MoralMatrixQuadrant(str, Enum):
    """The four quadrants of the Moral Matrix (Canon C13)."""
    VIRTUE_HIGH      = "VIRTUE_HIGH"      # High virtue expression, ascending
    VIRTUE_LOW       = "VIRTUE_LOW"       # Virtue present but not yet embodied
    VICE_ASCENDING   = "VICE_ASCENDING"   # Vice present but moving toward light
    VICE_ENTRENCHED  = "VICE_ENTRENCHED"  # Vice entrenched; shadow path active


# ---------------------------------------------------------------------------
# Input types
# ---------------------------------------------------------------------------

@dataclass
class ProposedAction:
    """A proposed action to be evaluated by the GoldenCompassEngine.

    This is the atomic unit of moral evaluation. Any response GAIA generates,
    any tool it calls, any recommendation it makes — all pass through here.
    """
    description: str                         # Plain-language description of the action
    action_type: str = "RESPONSE"            # RESPONSE / TOOL_CALL / RECOMMENDATION / etc.
    content: Optional[str] = None            # The actual content if available
    target: Optional[str] = None             # Who/what the action targets
    scope: str = "INDIVIDUAL"                # INDIVIDUAL / RELATIONAL / COLLECTIVE / etc.
    requested_by: Optional[str] = None       # The Human Principal who requested this
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionContext:
    """Session context passed alongside a ProposedAction for moral evaluation."""
    session_id: Optional[str] = None
    gaian_id: Optional[str] = None
    human_principal_id: Optional[str] = None
    alchemical_stage: str = "NIGREDO"
    relationship_depth: float = 0.0          # 0.0–1.0
    prior_shadow_flags: list[str] = field(default_factory=list)
    prior_harm_events: int = 0
    interaction_count: int = 0
    love_coherence_index: float = 0.5        # 0.0–1.0
    containment_active: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
