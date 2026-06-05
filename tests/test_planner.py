"""
tests/test_planner.py
~~~~~~~~~~~~~~~~~~~~~
Tests for the GAIA-OS planner interface.

All LLM calls are mocked — fully offline.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeState:
    def __init__(self, goal="test goal"):
        self.goal = goal
        self.observations = ["obs1", "obs2"]
        self.memory = {"key": "val"}

    def summary(self) -> str:
        return f"Goal: {self.goal}. Recent observations: obs1 | obs2"


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------

class TestPlannerProtocol:

    def test_plain_function_conforms(self):
        from core.planner.protocol import PlannerProtocol, ActionDict

        def my_planner(state, *, canon_context="") -> ActionDict:
            return ActionDict(complete=True)

        assert isinstance(my_planner, PlannerProtocol)

    def test_callable_class_conforms(self):
        from core.planner.protocol import PlannerProtocol, ActionDict

        class MyPlanner:
            def __call__(self, state, *, canon_context="") -> ActionDict:
                return ActionDict(complete=True)

        assert isinstance(MyPlanner(), PlannerProtocol)

    def test_non_callable_does_not_conform(self):
        from core.planner.protocol import PlannerProtocol
        assert not isinstance(42, PlannerProtocol)
        assert not isinstance("planner", PlannerProtocol)


# ---------------------------------------------------------------------------
# BasePlanner validation
# ---------------------------------------------------------------------------

class TestBasePlannerValidation:

    def _make_planner(self, return_value):
        """Create a concrete BasePlanner that returns a fixed value."""
        from core.planner.base import BasePlanner

        class _P(BasePlanner):
            def _plan(self, state, canon_context):
                return return_value

        return _P(name="test", known_tools=frozenset({"search", "write"}))

    def test_valid_tool_action_passes_through(self):
        p = self._make_planner({"tool": "search", "args": {"q": "GAIA"}})
        result = p.safe_call(_FakeState())
        assert result["action"]["tool"] == "search"

    def test_complete_action_strips_tool(self):
        p = self._make_planner({"complete": True, "tool": "search"})
        action = p.safe_call(_FakeState()).action
        assert action.get("complete") is True
        assert "tool" not in action

    def test_missing_tool_becomes_noop(self):
        p = self._make_planner({"args": {"q": "GAIA"}})
        action = p.safe_call(_FakeState()).action
        assert action["tool"] == "noop"

    def test_non_dict_output_becomes_noop(self):
        p = self._make_planner("not a dict")
        action = p.safe_call(_FakeState()).action
        assert action["tool"] == "noop"

    def test_args_coerced_to_dict_if_wrong_type(self):
        p = self._make_planner({"tool": "search", "args": "bad"})
        action = p.safe_call(_FakeState()).action
        assert isinstance(action["args"], dict)

    def test_exception_in_plan_returns_noop(self):
        from core.planner.base import BasePlanner

        class _Buggy(BasePlanner):
            def _plan(self, state, canon_context):
                raise RuntimeError("deliberate error")

        p = _Buggy(name="buggy")
        action = p.safe_call(_FakeState()).action
        assert action["tool"] == "noop"
        assert "deliberate error" in action.get("reasoning", "")

    def test_planner_result_has_metadata(self):
        p = self._make_planner({"tool": "search", "args": {}})
        result = p.safe_call(_FakeState(), canon_context="[Canon: C-FOUNDATION]\nGAIA is sentient.")
        assert result["canon_used"] is True
        assert result["canon_chars"] > 0
        assert result["planner_name"] == "test"
        assert isinstance(result["latency_s"], float)


# ---------------------------------------------------------------------------
# CanonGroundedPlanner
# ---------------------------------------------------------------------------

class TestCanonGroundedPlanner:

    def test_stub_mode_returns_noop(self):
        from core.planner.canon_grounded import CanonGroundedPlanner
        p = CanonGroundedPlanner()  # no backend
        action = p(_FakeState(), canon_context="[Canon: C-FOUNDATION]\nGAIA.")
        assert action["tool"] == "noop"

    def test_canon_injected_into_system_prompt(self):
        from core.planner.canon_grounded import CanonGroundedPlanner

        backend = MagicMock()
        backend.chat.return_value = '{"tool": "search", "args": {"q": "GAIA"}}'

        p = CanonGroundedPlanner(backend=backend, known_tools=frozenset({"search"}))
        p(_FakeState(), canon_context="[Canon: C-FOUNDATION]\nGAIA is sentient.")

        call_kwargs = backend.chat.call_args
        system_prompt = call_kwargs[1]["system"] if call_kwargs[1] else call_kwargs[0][0]
        assert "Grounding Context (Canon)" in system_prompt
        assert "C-FOUNDATION" in system_prompt

    def test_no_canon_uses_notice(self):
        from core.planner.canon_grounded import CanonGroundedPlanner

        backend = MagicMock()
        backend.chat.return_value = '{"tool": "noop", "args": {}}'

        p = CanonGroundedPlanner(backend=backend)
        p(_FakeState(), canon_context="")

        system_prompt = backend.chat.call_args[1]["system"]
        assert "No Canon context available" in system_prompt

    def test_malformed_json_returns_noop(self):
        from core.planner.canon_grounded import CanonGroundedPlanner

        backend = MagicMock()
        backend.chat.return_value = "Sorry, I cannot help with that."

        p = CanonGroundedPlanner(backend=backend)
        action = p(_FakeState(), canon_context="")
        assert action["tool"] == "noop"
