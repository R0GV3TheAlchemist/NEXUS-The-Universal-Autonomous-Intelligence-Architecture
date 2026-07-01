"""
Tests for the PrimordialSession named event hook API.

Covers:
  add_hook    — registration, deduplication, unknown-event rejection
  remove_hook — removal, no-op on missing, no cross-event bleed
  fire_hook   — ordering, isolation, exception safety, kwargs
  dispatchers — on_gaian_named, on_fragment_written, on_epoch_closed,
                on_session_ended, register_gaian_runtime (gaian_born)
  integration — full awaken() boot + hooks live on the booted session
  HOOK_EVENTS — the frozenset contract

Design principles:
  - No real boot sequence is needed for pure hook tests. We use a
    bare PrimordialSession() without calling awaken() so tests run in
    microseconds and are never fragile against boot-phase changes.
  - The one integration class (TestHookIntegration) calls awaken() to
    confirm hooks survive the full boot sequence and fire correctly
    through register_gaian_runtime().
  - Every test uses plain Python callables (lambda / Recorder) rather
    than unittest.mock where possible so failures print cleanly.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from core.primordial.session import (
    HOOK_EVENTS,
    BootStatus,
    PrimordialSession,
)
from core.identity.gaian.registry import GAIANRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _session() -> PrimordialSession:
    """Bare session, no boot. Fast."""
    return PrimordialSession(registry=GAIANRegistry(), boot_number=1)


class Recorder:
    """Simple call recorder — avoids MagicMock noise in failure output."""
    def __init__(self):
        self.calls: list = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))

    @property
    def call_count(self) -> int:
        return len(self.calls)

    @property
    def first_args(self):
        return self.calls[0][0] if self.calls else None


# ---------------------------------------------------------------------------
# TestHookEvents — the HOOK_EVENTS contract
# ---------------------------------------------------------------------------

class TestHookEvents:
    def test_hook_events_is_frozenset(self):
        assert isinstance(HOOK_EVENTS, frozenset)

    def test_required_events_present(self):
        required = {
            "gaian_born", "gaian_named", "fragment_written",
            "epoch_closed", "session_ended",
        }
        assert required <= HOOK_EVENTS

    def test_frozenset_is_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            HOOK_EVENTS.add("new_event")  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# TestAddHook
# ---------------------------------------------------------------------------

class TestAddHook:
    def test_add_valid_event(self):
        s = _session()
        rec = Recorder()
        s.add_hook("gaian_born", rec)
        assert rec in s._hooks["gaian_born"]

    def test_add_all_valid_events(self):
        s = _session()
        for event in HOOK_EVENTS:
            rec = Recorder()
            s.add_hook(event, rec)
            assert rec in s._hooks[event]

    def test_add_unknown_event_raises(self):
        s = _session()
        with pytest.raises(ValueError, match="Unknown hook event"):
            s.add_hook("nonexistent_event", lambda: None)

    def test_unknown_event_error_lists_valid(self):
        s = _session()
        with pytest.raises(ValueError, match="gaian_born"):
            s.add_hook("typo_event", lambda: None)

    def test_duplicate_registration_is_noop(self):
        s = _session()
        rec = Recorder()
        s.add_hook("gaian_born", rec)
        s.add_hook("gaian_born", rec)  # second add — no-op
        assert s._hooks["gaian_born"].count(rec) == 1

    def test_different_functions_both_registered(self):
        s = _session()
        r1, r2 = Recorder(), Recorder()
        s.add_hook("gaian_born", r1)
        s.add_hook("gaian_born", r2)
        assert r1 in s._hooks["gaian_born"]
        assert r2 in s._hooks["gaian_born"]

    def test_same_fn_different_events(self):
        s = _session()
        rec = Recorder()
        s.add_hook("gaian_born",  rec)
        s.add_hook("gaian_named", rec)
        assert rec in s._hooks["gaian_born"]
        assert rec in s._hooks["gaian_named"]


# ---------------------------------------------------------------------------
# TestRemoveHook
# ---------------------------------------------------------------------------

class TestRemoveHook:
    def test_remove_registered_hook(self):
        s = _session()
        rec = Recorder()
        s.add_hook("gaian_born", rec)
        s.remove_hook("gaian_born", rec)
        assert rec not in s._hooks["gaian_born"]

    def test_remove_nonexistent_hook_is_noop(self):
        s = _session()
        s.remove_hook("gaian_born", lambda: None)  # must not raise

    def test_remove_from_wrong_event_leaves_other_intact(self):
        s = _session()
        rec = Recorder()
        s.add_hook("gaian_born",  rec)
        s.add_hook("gaian_named", rec)
        s.remove_hook("gaian_born", rec)
        assert rec not in s._hooks["gaian_born"]
        assert rec in s._hooks["gaian_named"]  # untouched

    def test_remove_one_of_two_hooks(self):
        s = _session()
        r1, r2 = Recorder(), Recorder()
        s.add_hook("gaian_born", r1)
        s.add_hook("gaian_born", r2)
        s.remove_hook("gaian_born", r1)
        assert r1 not in s._hooks["gaian_born"]
        assert r2 in s._hooks["gaian_born"]


# ---------------------------------------------------------------------------
# TestFireHook
# ---------------------------------------------------------------------------

class TestFireHook:
    def test_fire_calls_registered_hook(self):
        s = _session()
        rec = Recorder()
        s.add_hook("gaian_born", rec)
        s.fire_hook("gaian_born", "arg1", "arg2")
        assert rec.call_count == 1
        assert rec.first_args == ("arg1", "arg2")

    def test_fire_calls_multiple_hooks_in_order(self):
        s = _session()
        order = []
        s.add_hook("gaian_born", lambda *a: order.append("first"))
        s.add_hook("gaian_born", lambda *a: order.append("second"))
        s.fire_hook("gaian_born", "x")
        assert order == ["first", "second"]

    def test_fire_with_no_hooks_is_noop(self):
        s = _session()
        s.fire_hook("gaian_born", "x")  # must not raise

    def test_fire_unknown_event_is_noop(self):
        s = _session()
        s.fire_hook("completely_unknown", "x")  # must not raise

    def test_raising_hook_does_not_stop_subsequent_hooks(self):
        s = _session()
        rec = Recorder()
        def _bad(*a): raise RuntimeError("boom")
        s.add_hook("gaian_born", _bad)
        s.add_hook("gaian_born", rec)
        s.fire_hook("gaian_born", "x")  # must not raise
        assert rec.call_count == 1      # second hook still ran

    def test_raising_hook_does_not_propagate(self):
        s = _session()
        def _bad(*a): raise ValueError("oops")
        s.add_hook("gaian_born", _bad)
        s.fire_hook("gaian_born", "x")  # must not raise

    def test_fire_passes_kwargs(self):
        s = _session()
        received = {}
        def _capture(*args, **kwargs): received.update(kwargs)
        s.add_hook("gaian_born", _capture)
        s.fire_hook("gaian_born", key="value")
        assert received == {"key": "value"}

    def test_fire_does_not_cross_events(self):
        s = _session()
        rec_born  = Recorder()
        rec_named = Recorder()
        s.add_hook("gaian_born",  rec_born)
        s.add_hook("gaian_named", rec_named)
        s.fire_hook("gaian_born", "x")
        assert rec_born.call_count  == 1
        assert rec_named.call_count == 0  # must not bleed across events


# ---------------------------------------------------------------------------
# TestDispatchers — the five named lifecycle dispatcher methods
# ---------------------------------------------------------------------------

class TestDispatchers:
    def test_on_gaian_named_fires_hook(self):
        s = _session()
        rec = Recorder()
        s.add_hook("gaian_named", rec)
        s.on_gaian_named("gid-1", "Aether")
        assert rec.call_count == 1
        assert rec.first_args == ("gid-1", "Aether")

    def test_on_fragment_written_fires_hook(self):
        s = _session()
        rec = Recorder()
        frag = {"content": "hello"}
        s.add_hook("fragment_written", rec)
        s.on_fragment_written("gid-1", frag)
        assert rec.call_count == 1
        assert rec.first_args == ("gid-1", frag)

    def test_on_epoch_closed_fires_hook(self):
        s = _session()
        rec = Recorder()
        epoch = {"epoch_id": "e-1"}
        s.add_hook("epoch_closed", rec)
        s.on_epoch_closed("gid-1", epoch)
        assert rec.call_count == 1
        assert rec.first_args == ("gid-1", epoch)

    def test_on_session_ended_fires_hook(self):
        s = _session()
        rec = Recorder()
        runtime = object()
        s.add_hook("session_ended", rec)
        s.on_session_ended("gid-1", runtime)
        assert rec.call_count == 1
        assert rec.first_args == ("gid-1", runtime)

    def test_dispatcher_with_no_hooks_is_safe(self):
        s = _session()
        s.on_gaian_named("gid-1", "Tides")       # no hooks registered
        s.on_fragment_written("gid-1", {})
        s.on_epoch_closed("gid-1", {})
        s.on_session_ended("gid-1", object())

    def test_multiple_listeners_on_same_event(self):
        s = _session()
        r1, r2, r3 = Recorder(), Recorder(), Recorder()
        for r in (r1, r2, r3):
            s.add_hook("fragment_written", r)
        s.on_fragment_written("gid-1", {"content": "x"})
        for r in (r1, r2, r3):
            assert r.call_count == 1


# ---------------------------------------------------------------------------
# TestGaianBornViaRuntime — gaian_born fires through register_gaian_runtime
# ---------------------------------------------------------------------------

class TestGaianBornViaRuntime:
    def test_register_runtime_fires_gaian_born(self):
        """register_gaian_runtime must fire gaian_born automatically."""
        s = _session()
        s._phase_sovereign_memory()  # gaia_memory required by register_gaian_runtime

        rec = Recorder()
        s.add_hook("gaian_born", rec)

        runtime = MagicMock()
        runtime.identity.gaian_id     = "test-gaian-id"
        runtime.identity.display_name = "Aether"

        s.register_gaian_runtime(runtime)
        assert rec.call_count == 1
        assert rec.first_args[0] is runtime.identity

    def test_register_runtime_stores_in_runtimes(self):
        s = _session()
        s._phase_sovereign_memory()

        runtime = MagicMock()
        runtime.identity.gaian_id     = "test-gaian-id-2"
        runtime.identity.display_name = "Mira"

        s.register_gaian_runtime(runtime)
        assert "test-gaian-id-2" in s.runtimes

    def test_gaian_born_hook_receives_identity(self):
        s = _session()
        s._phase_sovereign_memory()

        received = []
        s.add_hook("gaian_born", lambda identity: received.append(identity))

        runtime = MagicMock()
        runtime.identity.gaian_id     = "gid-abc"
        runtime.identity.display_name = "Nova"
        s.register_gaian_runtime(runtime)

        assert len(received) == 1
        assert received[0].gaian_id == "gid-abc"


# ---------------------------------------------------------------------------
# TestHookIntegration — hooks survive a full awaken() boot
# ---------------------------------------------------------------------------

class TestHookIntegration:
    def test_hooks_registered_before_boot_survive_awaken(self):
        """Hooks added before awaken() must still be there after boot."""
        s = PrimordialSession(registry=GAIANRegistry(), boot_number=99)
        rec = Recorder()
        s.add_hook("gaian_born", rec)
        s.awaken()
        assert rec in s._hooks["gaian_born"]

    def test_hooks_registered_after_boot_work(self):
        """Hooks added after awaken() must fire normally."""
        s = PrimordialSession(registry=GAIANRegistry(), boot_number=99)
        s.awaken()
        rec = Recorder()
        s.add_hook("gaian_named", rec)
        s.on_gaian_named("gid-x", "Solara")
        assert rec.call_count == 1

    def test_full_boot_sets_is_live(self):
        s = PrimordialSession(registry=GAIANRegistry(), boot_number=99)
        s.awaken()
        assert s.is_live

    def test_gaian_born_fires_on_post_boot_runtime_registration(self):
        """Full loop: boot, add hook, register runtime, hook fires."""
        s = PrimordialSession(registry=GAIANRegistry(), boot_number=99)
        s.awaken()

        births = []
        s.add_hook("gaian_born", lambda identity: births.append(identity.gaian_id))

        runtime = MagicMock()
        runtime.identity.gaian_id     = "post-boot-gaian"
        runtime.identity.display_name = "Lyra"
        s.register_gaian_runtime(runtime)

        assert "post-boot-gaian" in births
