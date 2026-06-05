"""
core/planner/protocol.py
~~~~~~~~~~~~~~~~~~~~~~~~
Formal contract for every planner in the GAIA-OS agentic loop.

Why a Protocol?
---------------
Python's typing.Protocol allows structural subtyping — any callable whose
signature matches PlannerProtocol is accepted by AgenticLoop without needing
to inherit from a base class.  This keeps third-party or user-defined
planners loosely coupled to the core framework.

Contract
--------
A planner is any callable with the signature:

    planner(state: AgentState, *, canon_context: str = "") -> ActionDict

The returned ActionDict MUST contain at least:
  - "tool"     : str   — name of the tool to invoke, OR
  - "complete" : bool  — True signals the loop to halt successfully.

Optional keys:
  - "args"           : dict  — keyword arguments forwarded to the tool.
  - "requires_human" : bool  — True triggers the ActionGate approval flow.
  - "progress"       : str   — human-readable progress note for audit logs.
  - "reasoning"      : str   — internal CoT explanation (not forwarded to tools).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol, TypedDict, runtime_checkable


# ---------------------------------------------------------------------------
# ActionDict (TypedDict — plain dict at runtime, typed at check time)
# ---------------------------------------------------------------------------

class ActionDict(TypedDict, total=False):
    """
    The map returned by a planner after each reasoning step.
    Exactly one of ``tool`` or ``complete`` must be present.
    """
    tool:           str
    complete:       bool
    args:           dict
    requires_human: bool
    progress:       str
    reasoning:      str


# ---------------------------------------------------------------------------
# PlannerResult (dataclass — supports both .attr and ["key"] access)
# ---------------------------------------------------------------------------

@dataclass
class PlannerResult:
    """
    Extended result returned by BasePlanner.safe_call().
    Wraps ActionDict with planner-level metadata.

    Supports both attribute access (result.action) and dict-style
    access (result["action"]) for test and downstream compatibility.
    """
    action:       ActionDict
    planner_name: str
    canon_used:   bool
    canon_chars:  int
    latency_s:    float

    # ------------------------------------------------------------------
    # Dict-style access so callers can use result["action"] as well
    # ------------------------------------------------------------------

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class PlannerProtocol(Protocol):
    """
    Structural type for any GAIA-OS planner.

    Conforming objects are accepted by AgenticLoop._reason() without
    inheritance.  Use isinstance(obj, PlannerProtocol) to check at
    runtime (requires @runtime_checkable).
    """

    def __call__(
        self,
        state: Any,
        *,
        canon_context: str = "",
    ) -> ActionDict:
        """Produce the next action given the current agent state."""
        ...
