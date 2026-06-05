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

from typing import Any, Protocol, TypedDict, runtime_checkable


# ---------------------------------------------------------------------------
# TypedDicts
# ---------------------------------------------------------------------------

class ActionDict(TypedDict, total=False):
    """
    The map returned by a planner after each reasoning step.

    Exactly one of ``tool`` or ``complete`` must be present.
    """
    tool:           str    # name of the tool to invoke
    complete:       bool   # True → session complete, halt loop
    args:           dict   # kwargs forwarded to the tool callable
    requires_human: bool   # True → route through ActionGate
    progress:       str    # short human-readable progress note
    reasoning:      str    # internal chain-of-thought (audit only)


class PlannerResult(TypedDict):
    """
    Extended result returned by BasePlanner subclasses.
    Wraps ActionDict with planner-level metadata.
    """
    action:         ActionDict
    planner_name:   str
    canon_used:     bool   # True if non-empty canon_context was provided
    canon_chars:    int    # length of the canon_context string
    latency_s:      float  # wall-clock time for this planning step


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

    Example conforming callables
    ----------------------------
    # 1. Plain function
    def my_planner(state, *, canon_context="") -> ActionDict:
        return {"tool": "search", "args": {"q": state.goal}}

    # 2. Class with __call__
    class MyPlanner:
        def __call__(self, state, *, canon_context="") -> ActionDict:
            ...

    # 3. BasePlanner subclass (also conforms)
    class MyPlanner(BasePlanner):
        def _plan(self, state, canon_context) -> ActionDict:
            ...
    """

    def __call__(
        self,
        state: Any,
        *,
        canon_context: str = "",
    ) -> ActionDict:
        """Produce the next action given the current agent state."""
        ...
