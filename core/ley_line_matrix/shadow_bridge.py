"""
Ley Line Matrix — Shadow Bridge

Interface between the Ley Line Matrix and core/shadow_engine.py.
Routes SHADOW flow-type pulses for shadow integration and polarity work.
Ensures shadow signals do not bypass canon-law enforcement.
"""

from __future__ import annotations

import logging
from typing import Any

from .models import FlowType, LeyNode, LeyPulse

logger = logging.getLogger("gaia.ley_line_matrix.shadow_bridge")

SHADOW_NODE = LeyNode(
    name="shadow_engine",
    module_path="core.shadow_engine",
    description="Shadow integration and polarity processing engine",
)


def register_shadow(matrix=None) -> None:
    """Register the shadow node into the matrix."""
    from . import get_matrix

    m = matrix or get_matrix()
    m.register_node(SHADOW_NODE)
    logger.info("Shadow bridge registered.")


def emit_shadow_pulse(payload: Any, origin: str, destination: str = "shadow_engine") -> LeyPulse:
    """
    Route a SHADOW pulse from `origin` into the shadow engine.
    The pulse passes through canon_bridge validation before routing.
    """
    from . import emit_pulse
    from .canon_bridge import enforce_canon
    from .schumann_sync import align_pulse_frequency

    pulse = LeyPulse(
        origin=origin,
        destination=destination,
        flow_type=FlowType.SHADOW,
        payload=payload,
    )
    align_pulse_frequency(pulse)

    if not enforce_canon(pulse):
        logger.warning("Shadow pulse blocked by canon enforcement: %s", pulse.pulse_id)
        return pulse

    emit_pulse(pulse)
    return pulse
