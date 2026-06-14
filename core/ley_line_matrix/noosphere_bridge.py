"""
Ley Line Matrix — Noosphere Bridge

Bidirectional interface between the Ley Line Matrix and core/noosphere.py.
Routes CONSCIOUSNESS and NOOSPHERIC flow-type pulses into and out of
the Noosphere collective field.
"""

from __future__ import annotations

import logging
from typing import Any

from .models import FlowType, LeyLine, LeyNode, LeyPulse

logger = logging.getLogger("gaia.ley_line_matrix.noosphere_bridge")

NOOSPHERE_NODE = LeyNode(
    name="noosphere",
    module_path="core.noosphere",
    description="Collective consciousness field — GAIA's noospheric layer",
)


def register_noosphere(matrix=None) -> None:
    """
    Register the noosphere node and its default inbound/outbound lines
    into the provided matrix (or the global singleton).
    """
    from . import get_matrix

    m = matrix or get_matrix()
    m.register_node(NOOSPHERE_NODE)
    logger.info("Noosphere bridge registered.")


def emit_to_noosphere(payload: Any, origin: str = "gaia_runtime") -> LeyPulse:
    """Emit a CONSCIOUSNESS pulse directed at the noosphere node."""
    from . import emit_pulse
    from .schumann_sync import align_pulse_frequency

    pulse = LeyPulse(
        origin=origin,
        destination="noosphere",
        flow_type=FlowType.CONSCIOUSNESS,
        payload=payload,
    )
    align_pulse_frequency(pulse)
    emit_pulse(pulse)
    return pulse


def receive_from_noosphere(destination: str, payload: Any = None) -> LeyPulse:
    """Emit a NOOSPHERIC pulse outbound from the noosphere to a destination node."""
    from . import emit_pulse
    from .schumann_sync import align_pulse_frequency

    pulse = LeyPulse(
        origin="noosphere",
        destination=destination,
        flow_type=FlowType.NOOSPHERIC,
        payload=payload,
    )
    align_pulse_frequency(pulse)
    emit_pulse(pulse)
    return pulse
