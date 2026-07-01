"""
Tests for the persistence hook wiring in server/app.py.

Covers:
  _wire_persistence_hooks  — registers all 5 hooks on the session
  _make_fragment_hook      — adapter delegates to persistence correctly
  _make_epoch_hook         — adapter delegates to persistence correctly
  _make_session_ended_hook — adapter delegates to persistence correctly
  _patch_registry_for_persistence — fallback: monkey-patches register()
  _flush_runtime_stats     — shutdown flushes all active runtimes
  integration              — fire event through session -> hook -> persistence

Design principles:
  - PrimordialSession and PersistenceManager are replaced by minimal
    fakes / MagicMock so these tests have zero I/O and never boot
    the real GAIA infrastructure.
  - The functions under test are imported directly from server.app so
    any refactor of the wiring logic is caught immediately.
  - The integration tests fire through the real session.fire_hook()
    path to confirm the adapters are transparent.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List
from unittest.mock import MagicMock, call, patch

import pytest

from server.app import (
    _flush_runtime_stats,
    _make_epoch_hook,
    _make_fragment_hook,
    _make_session_ended_hook,
    _patch_registry_for_persistence,
    _wire_persistence_hooks,
)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeSession:
    """
    Minimal PrimordialSession stand-in that implements the hook API
    exactly as the real session does: add_hook / remove_hook / fire_hook.
    """
    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = defaultdict(list)
        self.registry = FakeRegistry()

    def add_hook(self, event: str, fn: Callable) -> None:
        if fn not in self._hooks[event]:
            self._hooks[event].append(fn)

    def remove_hook(self, event: str, fn: Callable) -> None:
        try:
            self._hooks[event].remove(fn)
        except ValueError:
            pass

    def fire_hook(self, event: str, *args: Any, **kwargs: Any) -> None:
        for fn in list(self._hooks.get(event, [])):
            try:
                fn(*args, **kwargs)
            except Exception:
                pass


class FakeRegistry:
    """Minimal registry with a recordable register() method."""
    def __init__(self):
        self._registered: list = []

    def register(self, gaian) -> None:
        self._registered.append(gaian)


class NoHookSession:
    """
    Session without add_hook — triggers the fallback patching branch
    in _wire_persistence_hooks.
    """
    def __init__(self):
        self.registry = FakeRegistry()


def _fake_persistence() -> MagicMock:
    """MagicMock shaped like PersistenceManager."""
    p = MagicMock()
    p.on_gaian_born        = MagicMock()
    p.on_gaian_named       = MagicMock()
    p.on_fragment_written  = MagicMock()
    p.on_epoch_closed      = MagicMock()
    p.on_session_ended     = MagicMock()
    return p


def _fake_api() -> MagicMock:
    return MagicMock()


# ---------------------------------------------------------------------------
# TestWirePersistenceHooks — registration
# ---------------------------------------------------------------------------

class TestWirePersistenceHooks:
    def test_all_five_hooks_registered(self):
        s = FakeSession()
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)
        assert len(s._hooks["gaian_born"])       == 1
        assert len(s._hooks["gaian_named"])      == 1
        assert len(s._hooks["fragment_written"]) == 1
        assert len(s._hooks["epoch_closed"])     == 1
        assert len(s._hooks["session_ended"])    == 1

    def test_gaian_born_hook_is_persistence_method(self):
        """gaian_born maps directly to persistence.on_gaian_born."""
        s = FakeSession()
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)
        assert p.on_gaian_born in s._hooks["gaian_born"]

    def test_gaian_named_hook_is_persistence_method(self):
        s = FakeSession()
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)
        assert p.on_gaian_named in s._hooks["gaian_named"]

    def test_fragment_written_hook_is_adapter(self):
        """fragment_written uses an adapter, not the raw method."""
        s = FakeSession()
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)
        hook = s._hooks["fragment_written"][0]
        # It must be callable and not be the raw persistence method
        assert callable(hook)
        assert hook is not p.on_fragment_written

    def test_epoch_closed_hook_is_adapter(self):
        s = FakeSession()
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)
        hook = s._hooks["epoch_closed"][0]
        assert callable(hook)
        assert hook is not p.on_epoch_closed

    def test_session_ended_hook_is_adapter(self):
        s = FakeSession()
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)
        hook = s._hooks["session_ended"][0]
        assert callable(hook)
        assert hook is not p.on_session_ended

    def test_wire_is_idempotent_on_second_call(self):
        """Calling _wire twice must not double-register any hook."""
        s = FakeSession()
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)
        _wire_persistence_hooks(s, _fake_api(), p)
        # gaian_born / gaian_named are registered directly — dedup by list.count
        assert s._hooks["gaian_born"].count(p.on_gaian_born) == 1
        assert s._hooks["gaian_named"].count(p.on_gaian_named) == 1


# ---------------------------------------------------------------------------
# TestFallbackPatch — _patch_registry_for_persistence
# ---------------------------------------------------------------------------

class TestFallbackPatch:
    def test_wire_uses_fallback_when_no_add_hook(self):
        """When session has no add_hook, the registry must be patched."""
        s = NoHookSession()
        original_register = s.registry.register
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)
        # register() must have been replaced
        assert s.registry.register is not original_register

    def test_patched_register_calls_original(self):
        s = NoHookSession()
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)
        gaian = object()
        s.registry.register(gaian)
        assert gaian in s.registry._registered

    def test_patched_register_calls_on_gaian_born(self):
        s = NoHookSession()
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)
        gaian = object()
        s.registry.register(gaian)
        p.on_gaian_born.assert_called_once_with(gaian)

    def test_patched_register_tolerates_persistence_exception(self):
        """A raising persistence.on_gaian_born must never propagate out."""
        s = NoHookSession()
        p = _fake_persistence()
        p.on_gaian_born.side_effect = RuntimeError("disk full")
        _wire_persistence_hooks(s, _fake_api(), p)
        gaian = object()
        s.registry.register(gaian)  # must not raise
        assert gaian in s.registry._registered  # original still ran


# ---------------------------------------------------------------------------
# TestAdapterHooks — _make_fragment_hook / _make_epoch_hook / _make_session_ended_hook
# ---------------------------------------------------------------------------

class TestAdapterHooks:
    def test_fragment_hook_delegates_correctly(self):
        p = _fake_persistence()
        hook = _make_fragment_hook(p)
        frag = {"content": "test"}
        hook("gid-1", frag)
        p.on_fragment_written.assert_called_once_with("gid-1", frag)

    def test_epoch_hook_delegates_correctly(self):
        p = _fake_persistence()
        hook = _make_epoch_hook(p)
        epoch = {"epoch_id": "e-99"}
        hook("gid-1", epoch)
        p.on_epoch_closed.assert_called_once_with("gid-1", epoch)

    def test_session_ended_hook_delegates_correctly(self):
        p = _fake_persistence()
        hook = _make_session_ended_hook(p)
        runtime = object()
        hook("gid-1", runtime)
        p.on_session_ended.assert_called_once_with("gid-1", runtime)

    def test_fragment_hook_passes_exact_args(self):
        p = _fake_persistence()
        hook = _make_fragment_hook(p)
        frag = {"content": "exact", "importance": 0.9}
        hook("gid-xyz", frag)
        args = p.on_fragment_written.call_args
        assert args[0][0] == "gid-xyz"
        assert args[0][1] is frag

    def test_multiple_fragment_hook_calls_all_delegated(self):
        p = _fake_persistence()
        hook = _make_fragment_hook(p)
        for i in range(5):
            hook(f"gid-{i}", {"content": str(i)})
        assert p.on_fragment_written.call_count == 5


# ---------------------------------------------------------------------------
# TestFlushRuntimeStats — _flush_runtime_stats at shutdown
# ---------------------------------------------------------------------------

class TestFlushRuntimeStats:
    def test_flush_calls_on_session_ended_for_each_runtime(self):
        session = MagicMock()
        rt1, rt2 = MagicMock(), MagicMock()
        session._runtimes = {"gid-1": rt1, "gid-2": rt2}
        p = _fake_persistence()
        _flush_runtime_stats(session, p)
        assert p.on_session_ended.call_count == 2

    def test_flush_passes_correct_gaian_id_and_runtime(self):
        session = MagicMock()
        rt = MagicMock()
        session._runtimes = {"gid-abc": rt}
        p = _fake_persistence()
        _flush_runtime_stats(session, p)
        p.on_session_ended.assert_called_once_with("gid-abc", rt)

    def test_flush_tolerates_empty_runtimes(self):
        session = MagicMock()
        session._runtimes = {}
        p = _fake_persistence()
        _flush_runtime_stats(session, p)  # must not raise
        p.on_session_ended.assert_not_called()

    def test_flush_tolerates_missing_runtimes_attr(self):
        """Session without _runtimes (e.g. boot failure) must not raise."""
        session = MagicMock(spec=[])  # no attributes at all
        p = _fake_persistence()
        _flush_runtime_stats(session, p)  # must not raise
        p.on_session_ended.assert_not_called()

    def test_flush_continues_after_one_raises(self):
        session = MagicMock()
        rt1, rt2 = MagicMock(), MagicMock()
        session._runtimes = {"gid-1": rt1, "gid-2": rt2}
        p = _fake_persistence()
        p.on_session_ended.side_effect = [
            RuntimeError("flush failed"),
            None,
        ]
        _flush_runtime_stats(session, p)  # must not raise
        assert p.on_session_ended.call_count == 2


# ---------------------------------------------------------------------------
# TestIntegration — fire event through session -> hook -> persistence
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_gaian_born_fires_persistence_on_gaian_born(self):
        s = FakeSession()
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)
        identity = MagicMock()
        s.fire_hook("gaian_born", identity)
        p.on_gaian_born.assert_called_once_with(identity)

    def test_gaian_named_fires_persistence_on_gaian_named(self):
        s = FakeSession()
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)
        s.fire_hook("gaian_named", "gid-1", "Aether")
        p.on_gaian_named.assert_called_once_with("gid-1", "Aether")

    def test_fragment_written_fires_persistence_on_fragment_written(self):
        s = FakeSession()
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)
        frag = {"content": "hello"}
        s.fire_hook("fragment_written", "gid-1", frag)
        p.on_fragment_written.assert_called_once_with("gid-1", frag)

    def test_epoch_closed_fires_persistence_on_epoch_closed(self):
        s = FakeSession()
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)
        epoch = {"epoch_id": "e-1"}
        s.fire_hook("epoch_closed", "gid-1", epoch)
        p.on_epoch_closed.assert_called_once_with("gid-1", epoch)

    def test_session_ended_fires_persistence_on_session_ended(self):
        s = FakeSession()
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)
        runtime = object()
        s.fire_hook("session_ended", "gid-1", runtime)
        p.on_session_ended.assert_called_once_with("gid-1", runtime)

    def test_persistence_exception_does_not_propagate_through_session(self):
        """A persistence failure must never crash the GAIA session."""
        s = FakeSession()
        p = _fake_persistence()
        p.on_gaian_born.side_effect = IOError("disk full")
        _wire_persistence_hooks(s, _fake_api(), p)
        identity = MagicMock()
        s.fire_hook("gaian_born", identity)  # must not raise

    def test_all_five_events_fire_correct_persistence_method(self):
        """One comprehensive test: wire, fire all five, check all five."""
        s = FakeSession()
        p = _fake_persistence()
        _wire_persistence_hooks(s, _fake_api(), p)

        identity = MagicMock()
        frag     = {"content": "x"}
        epoch    = {"epoch_id": "e-1"}
        runtime  = object()

        s.fire_hook("gaian_born",       identity)
        s.fire_hook("gaian_named",      "gid-1", "Nova")
        s.fire_hook("fragment_written", "gid-1", frag)
        s.fire_hook("epoch_closed",     "gid-1", epoch)
        s.fire_hook("session_ended",    "gid-1", runtime)

        p.on_gaian_born.assert_called_once_with(identity)
        p.on_gaian_named.assert_called_once_with("gid-1", "Nova")
        p.on_fragment_written.assert_called_once_with("gid-1", frag)
        p.on_epoch_closed.assert_called_once_with("gid-1", epoch)
        p.on_session_ended.assert_called_once_with("gid-1", runtime)
