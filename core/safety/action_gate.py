"""
core/safety/action_gate.py
~~~~~~~~~~~~~~~~~~~~~~~~~~
Re-export shim: the canonical implementation lives in core.agent.action_gate.
Importing from either path will work identically.
"""
from core.agent.action_gate import (  # noqa: F401
    ActionGate,
    ActionRiskLevel,
    GateRequirement,
    ConsentReceipt,
    DelegationScope,
    PERMISSION_GRANT,
    PERMISSION_DENY,
)

__all__ = [
    "ActionGate",
    "ActionRiskLevel",
    "GateRequirement",
    "ConsentReceipt",
    "DelegationScope",
    "PERMISSION_GRANT",
    "PERMISSION_DENY",
]
