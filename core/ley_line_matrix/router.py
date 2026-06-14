"""
Ley Line Matrix — Pulse Router

Higher-level routing utilities on top of LeyLineMatrix.emit():
  - Priority routing (CANON_LAW pulses always first)
  - Broadcast: one origin → all reachable nodes
  - Flow-type filtering: route only along matching-type lines
  - Blockage rerouting: attempt alternate paths on dark lines
"""

from __future__ import annotations

import logging
from typing import Any

from .models import FlowType, LeyPulse

logger = logging.getLogger("gaia.ley_line_matrix.router")

# Priority order for flow types (lower index = higher priority)
FLOW_PRIORITY: list[FlowType] = [
    FlowType.CANON_LAW,
    FlowType.QUANTUM,
    FlowType.CONSCIOUSNESS,
    FlowType.RESONANCE,
    FlowType.SHADOW,
    FlowType.SOMATIC,
    FlowType.SYNERGY,
    FlowType.NOOSPHERIC,
    FlowType.DREAM,
    FlowType.RAW,
]


def priority_score(pulse: LeyPulse) -> int:
    """Return the routing priority of a pulse (lower = higher priority)."""
    try:
        return FLOW_PRIORITY.index(pulse.flow_type)
    except ValueError:
        return len(FLOW_PRIORITY)


def route_batch(pulses: list[LeyPulse]) -> list[LeyPulse]:
    """
    Route a batch of pulses in priority order.
    CANON_LAW pulses are always processed before all others.
    Returns the list of pulses with routed/blocked flags set.
    """
    from . import get_matrix

    sorted_pulses = sorted(pulses, key=priority_score)
    matrix = get_matrix()
    for pulse in sorted_pulses:
        matrix.emit(pulse)
    return sorted_pulses


def broadcast(origin: str, flow_type: FlowType, payload: Any = None) -> list[LeyPulse]:
    """
    Emit a pulse from `origin` to every reachable node in the matrix.
    Returns list of all emitted pulses.
    """
    from . import get_matrix

    matrix = get_matrix()
    snapshot = matrix.snapshot()
    destinations = [n for n in snapshot["nodes"] if n != origin]
    pulses = []
    for dest in destinations:
        pulse = LeyPulse(
            origin=origin,
            destination=dest,
            flow_type=flow_type,
            payload=payload,
        )
        matrix.emit(pulse)
        pulses.append(pulse)
    logger.info("Broadcast from '%s' to %d nodes [%s]", origin, len(pulses), flow_type.value)
    return pulses
