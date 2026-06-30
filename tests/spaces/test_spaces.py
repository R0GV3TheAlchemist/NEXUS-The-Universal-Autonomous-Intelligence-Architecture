"""Tests for core/spaces — model, store, and manager."""
from __future__ import annotations

import pytest

from core.spaces.model import Space, SpaceEventKind, SpaceRole, SpaceStatus
from core.spaces.store import SpaceStore
from core.spaces.manager import PermissionError, SpaceManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manager() -> tuple[SpaceManager, SpaceStore]:
    store = SpaceStore()
    manager = SpaceManager(store)
    return manager, store


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestSpaceModel:
    def test_owner_can_write(self) -> None:
        space = Space(name="test", owner_id="alice")
        space.add_member("alice", SpaceRole.OWNER)
        assert space.can_write("alice")

    def test_observer_cannot_write(self) -> None:
        space = Space(name="test", owner_id="alice")
        space.add_member("bob", SpaceRole.OBSERVER)
        assert not space.can_write("bob")

    def test_steward_can_write(self) -> None:
        space = Space(name="test", owner_id="alice")
        space.add_member("bot", SpaceRole.STEWARD)
        assert space.can_write("bot")

    def test_nonmember_cannot_write(self) -> None:
        space = Space(name="test", owner_id="alice")
        assert not space.can_write("ghost")

    def test_set_context_emits_event(self) -> None:
        space = Space(name="test", owner_id="alice")
        space.set_context("key", "value", actor_id="alice")
        event_kinds = [e.kind for e in space.events]
        assert SpaceEventKind.CONTEXT_SET in event_kinds

    def test_delete_context_emits_event(self) -> None:
        space = Space(name="test", owner_id="alice")
        space.set_context("x", 1)
        space.delete_context("x", actor_id="alice")
        assert "x" not in space.context
        assert any(e.kind == SpaceEventKind.CONTEXT_DELETED for e in space.events)

    def test_member_join_leave_events(self) -> None:
        space = Space(name="test", owner_id="alice")
        space.add_member("bob", actor_id="alice")
        space.remove_member("bob", actor_id="alice")
        kinds = [e.kind for e in space.events]
        assert SpaceEventKind.MEMBER_JOINED in kinds
        assert SpaceEventKind.MEMBER_LEFT in kinds

    def test_summary_keys(self) -> None:
        space = Space(name="test", owner_id="alice")
        s = space.summary()
        for key in ("space_id", "name", "status", "owner_id", "member_count"):
            assert key in s

    def test_set_status(self) -> None:
        space = Space(name="test", owner_id="alice")
        space.set_status(SpaceStatus.LOCKED)
        assert space.status == SpaceStatus.LOCKED
        assert any(e.kind == SpaceEventKind.STATUS_CHANGED for e in space.events)


# ---------------------------------------------------------------------------
# Store tests
# ---------------------------------------------------------------------------

class TestSpaceStore:
    def test_save_and_get(self) -> None:
        store = SpaceStore()
        space = Space(name="alpha", owner_id="alice")
        store.save(space)
        assert store.get(space.space_id) is space

    def test_get_by_name(self) -> None:
        store = SpaceStore()
        space = Space(name="beta", owner_id="alice")
        store.save(space)
        assert store.get_by_name("beta") is space

    def test_duplicate_name_different_id_raises(self) -> None:
        store = SpaceStore()
        store.save(Space(name="gamma", owner_id="alice"))
        with pytest.raises(ValueError):
            store.save(Space(name="gamma", owner_id="bob"))

    def test_delete(self) -> None:
        store = SpaceStore()
        space = Space(name="delta", owner_id="alice")
        store.save(space)
        store.delete(space.space_id)
        assert store.get(space.space_id) is None
        assert store.get_by_name("delta") is None

    def test_list_for_principal(self) -> None:
        store = SpaceStore()
        s1 = Space(name="s1", owner_id="alice")
        s1.add_member("alice", SpaceRole.OWNER)
        s2 = Space(name="s2", owner_id="bob")
        s2.add_member("bob", SpaceRole.OWNER)
        store.save(s1)
        store.save(s2)
        result = store.list_for_principal("alice")
        assert len(result) == 1
        assert result[0].name == "s1"

    def test_search(self) -> None:
        store = SpaceStore()
        store.save(Space(name="project-atlas", owner_id="alice", description="mapping"))
        store.save(Space(name="music-room", owner_id="alice", tags=["creative"]))
        assert len(store.search("atlas")) == 1
        assert len(store.search("creative")) == 1
        assert len(store.search("project")) == 1


# ---------------------------------------------------------------------------
# Manager tests
# ---------------------------------------------------------------------------

class TestSpaceManager:
    def test_create_auto_joins_owner(self) -> None:
        manager, store = _make_manager()
        space = manager.create("room", owner_id="alice")
        assert space.is_member("alice")
        assert space.members["alice"].role == SpaceRole.OWNER

    def test_create_persists_to_store(self) -> None:
        manager, store = _make_manager()
        space = manager.create("room", owner_id="alice")
        assert store.get(space.space_id) is not None

    def test_join_as_observer(self) -> None:
        manager, _ = _make_manager()
        space = manager.create("room", owner_id="alice")
        manager.join(space.space_id, "bob")
        assert space.is_member("bob")
        assert space.members["bob"].role == SpaceRole.OBSERVER

    def test_leave(self) -> None:
        manager, _ = _make_manager()
        space = manager.create("room", owner_id="alice")
        manager.join(space.space_id, "bob")
        manager.leave(space.space_id, "bob")
        assert not space.is_member("bob")

    def test_set_context_by_steward(self) -> None:
        manager, _ = _make_manager()
        space = manager.create("room", owner_id="alice")
        manager.join(space.space_id, "bot", role=SpaceRole.STEWARD, actor_id="alice")
        manager.set_context(space.space_id, "phase", "planning", actor_id="bot")
        assert manager.get_context(space.space_id, "phase") == "planning"

    def test_set_context_by_observer_raises(self) -> None:
        manager, _ = _make_manager()
        space = manager.create("room", owner_id="alice")
        manager.join(space.space_id, "eve")
        with pytest.raises(PermissionError):
            manager.set_context(space.space_id, "key", "val", actor_id="eve")

    def test_archive_blocks_context_writes(self) -> None:
        manager, _ = _make_manager()
        space = manager.create("room", owner_id="alice")
        manager.archive(space.space_id, actor_id="alice")
        with pytest.raises(PermissionError):
            manager.set_context(space.space_id, "x", 1, actor_id="alice")

    def test_destroy_blocks_all_writes(self) -> None:
        manager, _ = _make_manager()
        space = manager.create("room", owner_id="alice")
        manager.destroy(space.space_id, actor_id="alice")
        with pytest.raises(PermissionError):
            manager.join(space.space_id, "bob")

    def test_lock_and_unlock(self) -> None:
        manager, _ = _make_manager()
        space = manager.create("room", owner_id="alice")
        manager.lock(space.space_id, actor_id="alice")
        assert space.status == SpaceStatus.LOCKED
        manager.unlock(space.space_id, actor_id="alice")
        assert space.status == SpaceStatus.ACTIVE

    def test_non_owner_cannot_archive(self) -> None:
        manager, _ = _make_manager()
        space = manager.create("room", owner_id="alice")
        manager.join(space.space_id, "bob")
        with pytest.raises(PermissionError):
            manager.archive(space.space_id, actor_id="bob")

    def test_emit_event(self) -> None:
        manager, _ = _make_manager()
        space = manager.create("room", owner_id="alice")
        event = manager.emit(space.space_id, actor_id="alice", payload={"note": "hello"})
        assert event.kind == SpaceEventKind.CUSTOM
        assert event.payload["note"] == "hello"

    def test_emit_by_nonmember_raises(self) -> None:
        manager, _ = _make_manager()
        space = manager.create("room", owner_id="alice")
        with pytest.raises(PermissionError):
            manager.emit(space.space_id, actor_id="ghost")

    def test_consent_checker_blocks_write(self) -> None:
        store = SpaceStore()
        manager = SpaceManager(store, consent_checker=lambda sid, aid, action: False)
        space = manager.create("room", owner_id="alice")
        with pytest.raises(PermissionError):
            manager.set_context(space.space_id, "x", 1, actor_id="alice")

    def test_consent_checker_allows_write(self) -> None:
        store = SpaceStore()
        manager = SpaceManager(store, consent_checker=lambda sid, aid, action: True)
        space = manager.create("room", owner_id="alice")
        manager.set_context(space.space_id, "x", 42, actor_id="alice")
        assert manager.get_context(space.space_id, "x") == 42

    def test_set_criticality(self) -> None:
        manager, _ = _make_manager()
        space = manager.create("room", owner_id="alice")
        manager.set_criticality(space.space_id, 0.75)
        assert space.criticality == 0.75

    def test_criticality_out_of_range_raises(self) -> None:
        manager, _ = _make_manager()
        space = manager.create("room", owner_id="alice")
        with pytest.raises(ValueError):
            manager.set_criticality(space.space_id, 1.5)

    def test_change_role(self) -> None:
        manager, _ = _make_manager()
        space = manager.create("room", owner_id="alice")
        manager.join(space.space_id, "bob")
        manager.change_role(space.space_id, "bob", SpaceRole.STEWARD, actor_id="alice")
        assert space.members["bob"].role == SpaceRole.STEWARD

    def test_get_events_filtered(self) -> None:
        manager, _ = _make_manager()
        space = manager.create("room", owner_id="alice")
        manager.join(space.space_id, "bob")
        manager.set_context(space.space_id, "k", "v", actor_id="alice")
        context_events = manager.get_events(space.space_id, kind=SpaceEventKind.CONTEXT_SET)
        assert all(e.kind == SpaceEventKind.CONTEXT_SET for e in context_events)
