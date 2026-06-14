"""
Ley Line Matrix — Core Data Models

Defines the fundamental data structures:
  - FlowType:  The typed nature of energy flowing along a line
  - LeyNode:   A registered anchor point (engine/module) in the matrix
  - LeyLine:   A directional channel between two LeyNodes
  - LeyPulse:  A discrete signal packet transmitted along a line
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class FlowType(str, Enum):
    """The typed nature of energy flowing along a Ley Line."""

    RESONANCE = "resonance"         # Harmonic / vibrational signals
    CONSCIOUSNESS = "consciousness"  # Awareness, intent, sentient state
    QUANTUM = "quantum"             # Superposition, entanglement flows
    CANON_LAW = "canon_law"         # GAIAN LAW enforcement signals
    SHADOW = "shadow"               # Shadow integration / polarity work
    SOMATIC = "somatic"             # Body/biometric signals
    SYNERGY = "synergy"             # Amplification and coherence boost
    DREAM = "dream"                 # Dream-state / subconscious signals
    NOOSPHERIC = "noospheric"       # Collective field transmissions
    RAW = "raw"                     # Untyped / generic data flow


@dataclass
class LeyNode:
    """
    A named anchor point in the Ley Line Matrix.

    Any GAIA-OS engine or module registers itself as a LeyNode.
    The `module_path` is the dotted Python import path of the engine
    (e.g. 'core.noosphere') for lazy resolution at runtime.
    """

    name: str
    module_path: str
    description: str = ""
    active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, LeyNode):
            return self.name == other.name
        return NotImplemented


@dataclass
class LeyLine:
    """
    A directional channel between two LeyNodes.

    strength:     0.0 (severed) → 1.0 (full coherence)
    bidirectional: if True, flow is permitted in both directions
    blocked:      if True, pulses are rejected and logged as 'dark lines'
    """

    source: LeyNode
    target: LeyNode
    flow_type: FlowType
    strength: float = 1.0          # 0.0–1.0
    bidirectional: bool = False
    blocked: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        direction = "<->" if self.bidirectional else "->"
        return f"{self.source.name} {direction} {self.target.name} [{self.flow_type.value}]"

    def is_traversable(self) -> bool:
        """A line is traversable when unblocked and has non-zero strength."""
        return not self.blocked and self.strength > 0.0


@dataclass
class LeyPulse:
    """
    A discrete signal packet transmitted along the Ley Line Matrix.

    frequency_hz defaults to 7.83 (Schumann fundamental resonance).
    Pulses of FlowType.QUANTUM may be in-transit on multiple lines
    simultaneously (superposition routing).
    """

    origin: str                            # Name of source LeyNode
    destination: str                       # Name of target LeyNode
    flow_type: FlowType
    payload: Any = None
    frequency_hz: float = 7.83             # Schumann fundamental
    pulse_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    routed: bool = False                   # Set True once successfully routed
    blocked: bool = False                  # Set True if routing was rejected
