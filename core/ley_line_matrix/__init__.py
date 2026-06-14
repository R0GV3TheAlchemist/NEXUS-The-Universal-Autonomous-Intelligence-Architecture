"""
Ley Line Matrix — Public API

The connective tissue of GAIA-OS: a living graph of typed, directional
channels (Ley Lines) that carry resonance, consciousness, canon-law,
quantum, shadow, and somatic flow between GAIA's engines.

Usage:
    from core.ley_line_matrix import register_node, emit_pulse, query_matrix
"""

from .matrix import LeyLineMatrix
from .models import LeyNode, LeyLine, LeyPulse, FlowType
from .registry import register_node, ley_node

# Singleton matrix instance shared across GAIA runtime
_matrix: LeyLineMatrix | None = None


def get_matrix() -> LeyLineMatrix:
    """Return the global LeyLineMatrix singleton, initializing if needed."""
    global _matrix
    if _matrix is None:
        _matrix = LeyLineMatrix()
    return _matrix


def emit_pulse(pulse: LeyPulse) -> bool:
    """Emit a LeyPulse into the global matrix. Returns True if routed."""
    return get_matrix().emit(pulse)


def query_matrix() -> dict:
    """Return a snapshot of the current matrix topology and flow state."""
    return get_matrix().snapshot()


__all__ = [
    "LeyLineMatrix",
    "LeyNode",
    "LeyLine",
    "LeyPulse",
    "FlowType",
    "register_node",
    "ley_node",
    "get_matrix",
    "emit_pulse",
    "query_matrix",
]
