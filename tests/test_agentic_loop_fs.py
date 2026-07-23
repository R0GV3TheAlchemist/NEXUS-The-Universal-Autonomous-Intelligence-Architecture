"""
test_agentic_loop_fs.py
~~~~~~~~~~~~~~~~~~~~~~~
Tests for FSToolRegistry integration inside the PRAO agentic loop.

Covers:
  1. Happy path  – FS tool dispatches through FSToolRegistry, not the flat dict.
  2. Fallback    – Non-FS tools still route through the existing flat-dict path.
  3. No registry – Loop constructed without fs_tool_registry degrades gracefully.
  4. FS failure  – FSToolResult(success=False) surfaces as ActionResult failure.
  5. Priority    – Higher-priority FS tool wins when two tools share a name.
  6. Gate block  – ActionGate veto on an FS tool propagates correctly.
  7. Async-native dispatch – registry.execute() is awaited, not run_until_complete'd.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Minimal stubs so the test module imports even when optional deps are absent
# ---------------------------------------------------------------------------

class _FSToolResult:
    """Minimal stand-in for core.fs.tool_registry.FSToolResult."""
    def __init__(self, *, success: bool, data: Any = None, error: str = ""):
        self.success = success
        self.data    = data
        self.error   = error


class _FSToolRegistry:
    """Minimal stand-in for core.fs.tool_registry.FSToolRegistry."""
    def __init__(self, tools: Dict[str, Any] | None = None):
        self._tools = tools or {}

    def is_fs_tool(self, name: str) -> bool:
        return name in self._tools

    async def execute(self, name: str, **kwargs) -> _FSToolResult:
        handler = self._tools.get(name)
        if handler is None:
            return _FSToolResult(success=False, error=f"Unknown FS tool: {name}")
        result = handler(**kwargs)
        if asyncio.iscoroutine(result):
            result = await result
        return result


# ---------------------------------------------------------------------------
# Helpers to build a minimal AgenticLoop under test
# ---------------------------------------------------------------------------

def _make_loop(
    flat_tools: Dict[str, Any] | None = None,
    fs_registry: Optional[_FSToolRegistry] = None,
):
    """
    Import AgenticLoop (or a duck-type stub) and wire it with the supplied
    flat_tools dict and an optional FSToolRegistry.

    We patch the heavy optional deps (obs, RAG, CapabilityRegistry,
    TrustActionGate) so the loop constructs without external services.
    """
    try:
        from core.agentic_loop import AgenticLoop, create_loop  # noqa: F401
    except ImportError:
        pytest.skip("core.agentic_loop not importable in this environment")

    cap_reg = MagicMock()
    cap_reg.assert_registered = MagicMock()          # never raises by default

    gate = MagicMock()
    gate.engine = MagicMock()
    gate.engine.evaluate = MagicMock(return_value=True)  # allow by default

    loop = AgenticLoop(
        tools=flat_tools or {},
        capability_registry=cap_reg,
        action_gate=gate,
        fs_tool_registry=fs_registry,
    )
    loop._cap_reg = cap_reg  # expose for assertions
    loop._gate    = gate
    return loop


# ---------------------------------------------------------------------------
# 1. Happy path – FS tool dispatches through FSToolRegistry
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fs_tool_dispatches_via_registry():
    """An FS-registered tool must be executed by FSToolRegistry.execute(), not
    via the flat self._tools dict."""
    called_via_registry: list[str] = []

    def _handler(**kw):
        called_via_registry.append("registry")
        return _FSToolResult(success=True, data={"files": []})

    registry = _FSToolRegistry(tools={"fs:list": _handler})
    loop = _make_loop(fs_registry=registry)

    with patch.object(registry, "execute", wraps=registry.execute) as mock_exec:
        result = await loop._act(tool_name="fs:list", tool_args={})

    mock_exec.assert_awaited_once_with("fs:list")
    assert result.success is True


# ---------------------------------------------------------------------------
# 2. Fallback – non-FS tools still route through the flat-dict path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_non_fs_tool_uses_flat_dict():
    """A tool not known to FSToolRegistry must still execute via self._tools."""
    called: list[str] = []

    def _legacy_tool(**kw):
        called.append("legacy")
        return {"status": "ok"}

    registry = _FSToolRegistry(tools={})  # empty — doesn't know about this tool
    loop = _make_loop(
        flat_tools={"legacy:op": _legacy_tool},
        fs_registry=registry,
    )

    result = await loop._act(tool_name="legacy:op", tool_args={})

    assert called == ["legacy"]
    assert result.success is True


# ---------------------------------------------------------------------------
# 3. No registry – graceful degradation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_fs_registry_still_executes_flat_tools():
    """When fs_tool_registry=None the loop must behave exactly as before."""
    called: list[str] = []

    def _tool(**kw):
        called.append("flat")
        return {"ok": True}

    loop = _make_loop(flat_tools={"plain:op": _tool}, fs_registry=None)
    result = await loop._act(tool_name="plain:op", tool_args={})

    assert called == ["flat"]
    assert result.success is True


# ---------------------------------------------------------------------------
# 4. FS failure – FSToolResult(success=False) propagates as ActionResult failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fs_tool_failure_surfaces_in_action_result():
    """A failed FSToolResult must produce ActionResult.success == False with
    the error message preserved."""
    def _bad_handler(**kw):
        return _FSToolResult(success=False, error="permission denied")

    registry = _FSToolRegistry(tools={"fs:delete": _bad_handler})
    loop = _make_loop(fs_registry=registry)

    result = await loop._act(tool_name="fs:delete", tool_args={"path": "/etc"})

    assert result.success is False
    assert "permission denied" in (result.error or "")


# ---------------------------------------------------------------------------
# 5. Priority – higher-priority FS tool shadows a flat-dict tool of the same name
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fs_registry_takes_priority_over_flat_dict_on_name_collision():
    """If both the FS registry and the flat dict contain 'fs:op', the registry
    must win — the flat callable must never be invoked."""
    flat_called: list[str] = []
    fs_called:   list[str] = []

    def _flat(**kw):
        flat_called.append("flat")
        return {"source": "flat"}

    def _fs(**kw):
        fs_called.append("fs")
        return _FSToolResult(success=True, data={"source": "registry"})

    registry = _FSToolRegistry(tools={"fs:op": _fs})
    loop = _make_loop(flat_tools={"fs:op": _flat}, fs_registry=registry)

    result = await loop._act(tool_name="fs:op", tool_args={})

    assert fs_called   == ["fs"],   "FS registry handler was not called"
    assert flat_called == [],        "Flat-dict handler must NOT be called"
    assert result.success is True


# ---------------------------------------------------------------------------
# 6. Gate block – ActionGate veto propagates on an FS tool
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gate_veto_on_fs_tool_returns_failure():
    """When the ActionGate blocks an FS tool the loop must return a failure
    ActionResult *before* reaching FSToolRegistry.execute()."""
    def _should_not_run(**kw):
        raise AssertionError("Should never be called after a gate veto")

    registry = _FSToolRegistry(tools={"fs:write": _should_not_run})
    loop = _make_loop(fs_registry=registry)

    # Make the gate refuse the action
    loop._gate.engine.evaluate.return_value = False

    with patch.object(registry, "execute", wraps=registry.execute) as mock_exec:
        result = await loop._act(tool_name="fs:write", tool_args={"data": "x"})

    mock_exec.assert_not_called()
    assert result.success is False


# ---------------------------------------------------------------------------
# 7. Async-native dispatch – registry.execute() is awaited correctly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fs_registry_execute_is_awaited_not_run_until_complete():
    """registry.execute() must be awaited directly, never wrapped in
    asyncio.get_event_loop().run_until_complete(), which would deadlock
    inside a running loop."""
    exec_mock = AsyncMock(
        return_value=_FSToolResult(success=True, data={"async": True})
    )

    registry = _FSToolRegistry(tools={})
    registry.execute  = exec_mock            # type: ignore[method-assign]
    registry.is_fs_tool = MagicMock(return_value=True)

    loop = _make_loop(fs_registry=registry)

    result = await loop._act(tool_name="fs:any", tool_args={"key": "val"})

    exec_mock.assert_awaited_once()
    assert result.success is True


# ---------------------------------------------------------------------------
# 8. create_loop() factory surfaces fs_tool_registry kwarg
# ---------------------------------------------------------------------------

def test_create_loop_accepts_fs_tool_registry_kwarg():
    """The create_loop() convenience factory must accept and store
    fs_tool_registry without raising."""
    try:
        from core.agentic_loop import create_loop
    except ImportError:
        pytest.skip("core.agentic_loop not importable in this environment")

    registry = _FSToolRegistry(tools={})
    loop = create_loop(tools={}, fs_tool_registry=registry)
    assert loop.fs_tool_registry is registry
