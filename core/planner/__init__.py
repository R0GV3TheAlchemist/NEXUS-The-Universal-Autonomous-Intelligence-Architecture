"""
core/planner
~~~~~~~~~~~~
Planner layer for the GAIA-OS agentic loop.

Public surface
--------------
PlannerProtocol      — typing.Protocol defining the planner callable contract.
ActionDict           — TypedDict for the action map returned by a planner.
BasePlanner          — Abstract base class with validation + safe_call().
CanonGroundedPlanner — Concrete planner that injects Canon context into the
                       LLM system prompt before each reasoning step.
"""

from .protocol import PlannerProtocol, ActionDict, PlannerResult
from .base import BasePlanner
from .canon_grounded import CanonGroundedPlanner

__all__ = [
    "PlannerProtocol",
    "ActionDict",
    "PlannerResult",
    "BasePlanner",
    "CanonGroundedPlanner",
]
