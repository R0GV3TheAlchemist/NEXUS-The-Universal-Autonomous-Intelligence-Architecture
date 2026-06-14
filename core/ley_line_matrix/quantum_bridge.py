"""
Ley Line Matrix — Quantum Bridge

Routes QUANTUM flow-type pulses through the core/quantum/ subsystem.
Quantum pulses support superposition routing: a single pulse can be
in-transit on multiple Ley Lines simultaneously until observed/collapsed.

Integrates with: core/quantum/
"""

from __future__ import annotations

import logging
from typing import Any

from .models import FlowType, LeyNode, LeyPulse

logger = logging.getLogger("gaia.ley_line_matrix.quantum_bridge")

QUANTUM_NODE = LeyNode(
    name="quantum",
    module_path="core.quantum",
    description="Quantum superposition routing and entanglement flows",
)


def register_quantum(matrix=None) -> None:
    """Register the quantum node into the matrix."""
    from . import get_matrix

    m = matrix or get_matrix()
    m.register_node(QUANTUM_NODE)
    logger.info("Quantum bridge registered.")


def emit_quantum_pulse(
    origin: str,
    destination: str,
    payload: Any = None,
    entangled_with: str | None = None,
) -> LeyPulse:
    """
    Emit a QUANTUM pulse that travels all viable paths simultaneously.
    If `entangled_with` is provided, the pulse is linked to a peer node
    (collapse of one collapses the other).
    """
    from . import emit_pulse
    from .schumann_sync import align_pulse_frequency

    pulse = LeyPulse(
        origin=origin,
        destination=destination,
        flow_type=FlowType.QUANTUM,
        payload=payload,
        metadata={"entangled_with": entangled_with} if entangled_with else {},
    )
    align_pulse_frequency(pulse)
    emit_pulse(pulse)
    return pulse


def collapse_pulse(pulse: LeyPulse, chosen_path_index: int = 0) -> LeyPulse:
    """
    Collapse a quantum pulse from superposition to a single path.
    Selects `chosen_path_index` from the pulse's `quantum_paths` metadata.
    """
    paths = pulse.metadata.get("quantum_paths", [])
    if not paths:
        logger.warning("No quantum paths to collapse for pulse %s", pulse.pulse_id)
        return pulse

    idx = min(chosen_path_index, len(paths) - 1)
    pulse.metadata["collapsed_path"] = paths[idx]
    pulse.metadata["collapsed"] = True
    logger.info(
        "Quantum pulse %s collapsed to path: %s",
        pulse.pulse_id, paths[idx]
    )
    return pulse
