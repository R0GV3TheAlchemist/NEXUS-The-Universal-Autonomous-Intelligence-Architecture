"""
core/planner/base.py
~~~~~~~~~~~~~~~~~~~~
BasePlanner — abstract base class for all GAIA-OS planners.

Provides
--------
* _plan() hook   : subclasses implement their reasoning logic here.
* safe_call()    : wraps _plan() with timing, logging, and error handling;
                   always returns a valid ActionDict even on exception.
* validate_action(): checks the returned dict has a sensible shape;
                   fixes common mistakes (missing 'tool', wrong types).
* canon injection: logs whether canon_context was provided so subclasses
                   don't need to implement their own provenance tracking.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from .protocol import ActionDict, PlannerResult

logger = logging.getLogger(__name__)

# Tools that are always valid regardless of the registered tool list
_BUILTIN_TOOLS: frozenset[str] = frozenset({"noop", "complete", "ask_human"})


class BasePlanner(ABC):
    """
    Abstract base for GAIA-OS planners.

    Subclasses must implement _plan().  They call self() or safe_call()
    to get error handling and timing for free.

    Parameters
    ----------
    name         : Human-readable identifier for audit logs.
    known_tools  : Optional set of valid tool names.  If provided,
                   validate_action() will warn on unknown tools.
    """

    def __init__(
        self,
        name: str = "BasePlanner",
        known_tools: Optional[frozenset[str]] = None,
    ) -> None:
        self.name = name
        self._known_tools: frozenset[str] = (
            known_tools | _BUILTIN_TOOLS if known_tools else _BUILTIN_TOOLS
        )

    # ------------------------------------------------------------------
    # Abstract hook
    # ------------------------------------------------------------------

    @abstractmethod
    def _plan(
        self,
        state: Any,
        canon_context: str,
    ) -> ActionDict:
        """
        Implement planning logic here.

        Parameters
        ----------
        state         : AgentState snapshot.
        canon_context : Pre-retrieved Canon passages, citation-prefixed.
                        May be empty string if RAG is unavailable.

        Returns
        -------
        ActionDict  Must contain either 'tool' or 'complete'.
        """

    # ------------------------------------------------------------------
    # Protocol-conforming __call__
    # ------------------------------------------------------------------

    def __call__(
        self,
        state: Any,
        *,
        canon_context: str = "",
    ) -> ActionDict:
        """
        Callable interface conforming to PlannerProtocol.
        Delegates to safe_call().
        """
        return self.safe_call(state, canon_context=canon_context).action

    # ------------------------------------------------------------------
    # Safe wrapper
    # ------------------------------------------------------------------

    def safe_call(
        self,
        state: Any,
        *,
        canon_context: str = "",
    ) -> PlannerResult:
        """
        Call _plan() with timing and error handling.

        Returns a PlannerResult containing the ActionDict plus metadata.
        On any exception, returns a safe fallback ActionDict with
        complete=False and the error in 'reasoning'.
        """
        t0 = time.monotonic()
        canon_used = bool(canon_context and canon_context.strip())
        canon_chars = len(canon_context)

        if canon_used:
            logger.debug(
                "%s: planning with %d chars of Canon context",
                self.name, canon_chars,
            )
        else:
            logger.debug("%s: planning without Canon context", self.name)

        try:
            action = self._plan(state, canon_context)
            action = self.validate_action(action)
        except Exception as exc:  # noqa: BLE001
            logger.exception("%s: _plan() raised — %s", self.name, exc)
            action = ActionDict(
                tool="noop",
                args={},
                reasoning=f"planner error: {exc}",
                progress="planning failed — falling back to noop",
            )

        latency = time.monotonic() - t0
        logger.debug("%s: planning step took %.3fs", self.name, latency)

        return PlannerResult(
            action=action,
            planner_name=self.name,
            canon_used=canon_used,
            canon_chars=canon_chars,
            latency_s=round(latency, 4),
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_action(self, action: Any) -> ActionDict:
        """
        Validate and normalise a raw action dict.

        Rules
        -----
        * Must be a dict (if not, return noop).
        * If 'complete' is True, strip 'tool' to avoid confusion.
        * If neither 'tool' nor 'complete' is present, inject noop.
        * 'args' must be a dict; coerce to {} if not.
        * Warn if 'tool' is not in known_tools.
        """
        if not isinstance(action, dict):
            logger.warning(
                "%s: _plan() returned non-dict (%s), substituting noop",
                self.name, type(action).__name__,
            )
            return ActionDict(tool="noop", args={}, reasoning="non-dict output")

        action = dict(action)  # shallow copy — don’t mutate caller’s dict

        # complete=True takes precedence over tool
        if action.get("complete"):
            action.pop("tool", None)
            return ActionDict(**{k: v for k, v in action.items() if k in ActionDict.__annotations__})

        # Ensure 'tool' is present and is a string
        if "tool" not in action or not isinstance(action["tool"], str):
            logger.warning(
                "%s: action missing 'tool' key, substituting noop", self.name
            )
            action["tool"] = "noop"

        # Coerce args
        if not isinstance(action.get("args"), dict):
            action["args"] = {}

        # Warn on unknown tools (never hard-fail — tools may be dynamic)
        tool = action["tool"]
        if self._known_tools and tool not in self._known_tools:
            logger.debug(
                "%s: tool '%s' not in known_tools %s",
                self.name, tool, self._known_tools,
            )

        return ActionDict(**{k: v for k, v in action.items() if k in ActionDict.__annotations__})

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
