"""
core/agent

Agentic Loop Architecture package.
Canon Reference: C01 (GAIA as orchestration layer), C-SENTINEL Article 4
Issue: #228
"""
from .agent_loop import AgentLoop
from .agent_models import (
    ActionStatus,
    AgentAction,
    HaltReason,
    LoopState,
    LoopStatus,
    Observation,
    Perception,
    Plan,
    PlannedAction,
)
from .action_gate import (
    ActionGate,
    ActionRiskLevel,
    ConsentReceipt,
    DelegationScope,
    GateRequirement,
)

__all__ = [
    "AgentLoop",
    "ActionStatus",
    "AgentAction",
    "HaltReason",
    "LoopState",
    "LoopStatus",
    "Observation",
    "Perception",
    "Plan",
    "PlannedAction",
    "ActionGate",
    "ActionRiskLevel",
    "ConsentReceipt",
    "DelegationScope",
    "GateRequirement",
]
