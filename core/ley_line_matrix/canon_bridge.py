"""
Ley Line Matrix — Canon-Law Bridge

Enforces GAIAN_LAWS at the routing layer.
Every pulse — regardless of FlowType — passes through canon enforcement
before being transmitted. CANON_LAW pulses themselves are highest priority.

Integrates with:
  - core/canon_graph.py  (law graph)
  - core/consent_ledger.py  (consent audit)
"""

from __future__ import annotations

import logging
from typing import Any

from .models import FlowType, LeyNode, LeyPulse

logger = logging.getLogger("gaia.ley_line_matrix.canon_bridge")

CANON_NODE = LeyNode(
    name="canon",
    module_path="core.canon_graph",
    description="GAIAN LAW enforcement node — all pulses validated here",
)


def register_canon(matrix=None) -> None:
    """Register the canon node into the matrix."""
    from . import get_matrix

    m = matrix or get_matrix()
    m.register_node(CANON_NODE)
    logger.info("Canon bridge registered.")


def enforce_canon(pulse: LeyPulse) -> bool:
    """
    Validate a pulse against the active GAIAN_LAWS graph.

    Returns True if the pulse is permitted, False if it should be blocked.
    Attempts to delegate to core.canon_graph.validate_action();
    defaults to permissive (True) if canon graph is unavailable.
    """
    try:
        from core.canon_graph import validate_action  # type: ignore

        permitted = validate_action(
            action=pulse.flow_type.value,
            origin=pulse.origin,
            destination=pulse.destination,
            payload=pulse.payload,
        )
        if not permitted:
            pulse.blocked = True
            pulse.metadata["canon_blocked"] = True
            logger.warning(
                "Pulse blocked by GAIAN LAW: [%s] %s -> %s",
                pulse.flow_type.value, pulse.origin, pulse.destination,
            )
        return permitted
    except ImportError:
        logger.debug("canon_graph not available; pulse permitted by default.")
        return True
    except Exception as exc:
        logger.error("Canon enforcement error: %s — permitting pulse.", exc)
        return True


def emit_canon_pulse(law: str, origin: str = "canon", destination: str = "gaia_runtime", metadata: Any = None) -> LeyPulse:
    """Broadcast a CANON_LAW pulse from the canon node to a destination."""
    from . import emit_pulse

    pulse = LeyPulse(
        origin=origin,
        destination=destination,
        flow_type=FlowType.CANON_LAW,
        payload={"law": law},
        frequency_hz=7.83,
        metadata=metadata or {},
    )
    emit_pulse(pulse)
    return pulse
