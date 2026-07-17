"""
tests/core/test_gaian_init.py

Unit tests for core/gaian/__init__.py — focusing on the ErrorBoundary
integration paths added in the C30 hardening pass.

Canon: C17 (Persistent Memory), C30 (no silent failures)
Issue: #811
"""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.error_boundary import GAIABoundaryError


# ------------------------------------------------------------------ #
#  Fixtures                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture()
def gaian_dir(tmp_path, monkeypatch):
    """Redirect GAIAN_DIR to a temp directory for all tests."""
    import core.gaian as mod
    monkeypatch.setattr(mod, "GAIAN_DIR", tmp_path / "gaians")
    return tmp_path / "gaians"


@pytest.fixture()
def mock_base_form():
    form = MagicMock()
    form.id = "gaia"
    form.personality_seed = "I am GAIA, a living intelligence."
    form.avatar_color = "#4ade80"
    form.avatar_style = "digital_earth"
    form.voice_notes = "Speak with warmth and clarity."
    return form


# ------------------------------------------------------------------ #
#  list_gaians                                                         #
# ------------------------------------------------------------------ #

class TestListGaians:
    def test_empty_dir_returns_empty_list(self, gaian_dir):
        import core.gaian as mod
        assert mod.list_gaians() == []

    def test_missing_dir_returns_empty_list(self, gaian_dir):
        import core.gaian as mod
        assert mod.list_gaians() == []

    def test_valid_gaian_returned(self, gaian_dir):
        import core.gaian as mod
        slug_dir = gaian_dir / "test_gaian"
        slug_dir.mkdir(parents=True)
        (slug_dir / "memory.json").write_text(
            json.dumps({
                "id": "abc", "name": "Test", "slug": "test_gaian",
                "base_form_id": "gaia", "avatar_color": "#fff",
                "avatar_style": "digital_earth", "personality": "curious",
                "relationship_depth": 0, "total_exchanges": 0,
                "last_active": 0.0, "created_at": 0.0,
            }),
            encoding="utf-8",
        )
        result = mod.list_gaians()
        assert len(result) == 1
        assert result[0]["slug"] == "test_gaian"

    def test_corrupt_file_skipped_not_raised(self, gaian_dir):
        """C30: corrupt file is logged at DEGRADED, scan continues — no exception."""
        import core.gaian as mod
        bad_dir = gaian_dir / "bad_gaian"
        bad_dir.mkdir(parents=True)
        (bad_dir / "memory.json").write_text("{not valid json", encoding="utf-8")
        result = mod.list_gaians()  # must NOT raise
        assert result == []

    def test_corrupt_file_does_not_block_valid_files(self, gaian_dir):
        """One corrupt file must not prevent valid siblings from appearing."""
        import core.gaian as mod
        bad_dir = gaian_dir / "aaa_bad"
        bad_dir.mkdir(parents=True)
        (bad_dir / "memory.json").write_text("{broken", encoding="utf-8")

        good_dir = gaian_dir / "zzz_good"
        good_dir.mkdir(parents=True)
        (good_dir / "memory.json").write_text(
            json.dumps({
                "id": "xyz", "name": "Good", "slug": "zzz_good",
                "base_form_id": "gaia", "avatar_color": "#000",
                "avatar_style": "digital_earth", "personality": "wise",
                "relationship_depth": 0, "total_exchanges": 0,
                "last_active": 0.0, "created_at": 0.0,
            }),
            encoding="utf-8",
        )
        result = mod.list_gaians()
        assert len(result) == 1
        assert result[0]["slug"] == "zzz_good"


# ------------------------------------------------------------------ #
#  load_gaian                                                          #
# ------------------------------------------------------------------ #

class TestLoadGaian:
    def test_returns_none_if_no_file(self, gaian_dir):
        import core.gaian as mod
        assert mod.load_gaian("nonexistent") is None

    def test_loads_valid_memory(self, gaian_dir):
        import core.gaian as mod
        slug_dir = gaian_dir / "ariel"
        slug_dir.mkdir(parents=True)
        payload = {
            "id": "1", "name": "Ariel", "slug": "ariel",
            "base_form_id": "gaia", "personality": "curious",
            "avatar_color": "#00f", "avatar_style": "digital_earth",
            "created_at": 0.0, "last_active": 0.0,
            "relationship_depth": 3, "total_exchanges": 10,
            "user_name": None, "user_interests": [],
            "conversation_history": [], "long_term_memories": [],
        }
        (slug_dir / "memory.json").write_text(json.dumps(payload), encoding="utf-8")
        gaian = mod.load_gaian("ariel")
        assert gaian is not None
        assert gaian.name == "Ariel"
        assert gaian.relationship_depth == 3

    def test_corrupt_json_returns_none_not_raises(self, gaian_dir):
        """C30: corrupt JSON → DEGRADED (logged), returns None."""
        import core.gaian as mod
        slug_dir = gaian_dir / "corrupt"
        slug_dir.mkdir(parents=True)
        (slug_dir / "memory.json").write_text("{{broken", encoding="utf-8")
        assert mod.load_gaian("corrupt") is None

    def test_backfill_defaults_on_load(self, gaian_dir):
        """Older memory files without base_form_id / avatar_style get defaults."""
        import core.gaian as mod
        slug_dir = gaian_dir / "legacy"
        slug_dir.mkdir(parents=True)
        payload = {
            "id": "2", "name": "Legacy", "slug": "legacy",
            "personality": "calm", "avatar_color": "#abc",
            "created_at": 0.0, "last_active": 0.0,
        }
        (slug_dir / "memory.json").write_text(json.dumps(payload), encoding="utf-8")
        gaian = mod.load_gaian("legacy")
        assert gaian is not None
        assert gaian.base_form_id == "gaia"
        assert gaian.avatar_style == "digital_earth"


# ------------------------------------------------------------------ #
#  _save_gaian                                                         #
# ------------------------------------------------------------------ #

class TestSaveGaian:
    def test_save_creates_memory_file(self, gaian_dir, mock_base_form):
        import core.gaian as mod
        with patch("core.gaian.get_base_form", return_value=mock_base_form), \
             patch("core.gaian.get_default_base_form", return_value=mock_base_form):
            gaian = mod.create_gaian("TestBot")
        memory_path = gaian_dir / gaian.slug / "memory.json"
        assert memory_path.exists()
        data = json.loads(memory_path.read_text())
        assert data["name"] == "TestBot"

    def test_save_failure_raises_gaian_boundary_error(self, gaian_dir, mock_base_form, monkeypatch):
        """C30/FATAL: _save_gaian must raise (not swallow) on I/O error."""
        import core.gaian as mod

        def bad_mkdir(*a, **kw):
            raise OSError("disk full")

        with patch("core.gaian.get_base_form", return_value=mock_base_form), \
             patch("core.gaian.get_default_base_form", return_value=mock_base_form), \
             patch.object(Path, "mkdir", bad_mkdir):
            with pytest.raises((GAIABoundaryError, OSError)):
                mod.create_gaian("WillFail")


# ------------------------------------------------------------------ #
#  add_exchange                                                        #
# ------------------------------------------------------------------ #

class TestAddExchange:
    def test_exchange_recorded_and_depth_increments(self, gaian_dir, mock_base_form):
        import core.gaian as mod
        with patch("core.gaian.get_base_form", return_value=mock_base_form), \
             patch("core.gaian.get_default_base_form", return_value=mock_base_form):
            gaian = mod.create_gaian("Tester")

        for i in range(5):
            mod.add_exchange(gaian, f"hi {i}", f"hello {i}")

        assert gaian.total_exchanges == 5
        assert gaian.relationship_depth == 1
        assert len(gaian.conversation_history) == 10

    def test_rolling_window_enforced(self, gaian_dir, mock_base_form):
        import core.gaian as mod
        with patch("core.gaian.get_base_form", return_value=mock_base_form), \
             patch("core.gaian.get_default_base_form", return_value=mock_base_form):
            gaian = mod.create_gaian("Roller")

        for i in range(50):
            mod.add_exchange(gaian, f"msg {i}", f"reply {i}")

        assert len(gaian.conversation_history) <= mod.MAX_ROLLING_TURNS * 2


# ------------------------------------------------------------------ #
#  get_conversation_context                                            #
# ------------------------------------------------------------------ #

class TestGetConversationContext:
    def test_maps_roles_correctly(self, gaian_dir, mock_base_form):
        import core.gaian as mod
        with patch("core.gaian.get_base_form", return_value=mock_base_form), \
             patch("core.gaian.get_default_base_form", return_value=mock_base_form):
            gaian = mod.create_gaian("RoleTest")
        mod.add_exchange(gaian, "hello", "world")
        ctx = mod.get_conversation_context(gaian)
        assert ctx[0]["role"] == "user"
        assert ctx[1]["role"] == "assistant"

    def test_truncates_to_max_context_turns(self, gaian_dir, mock_base_form):
        import core.gaian as mod
        with patch("core.gaian.get_base_form", return_value=mock_base_form), \
             patch("core.gaian.get_default_base_form", return_value=mock_base_form):
            gaian = mod.create_gaian("Truncator")
        for i in range(20):
            mod.add_exchange(gaian, f"q{i}", f"a{i}")
        ctx = mod.get_conversation_context(gaian)
        assert len(ctx) <= mod.MAX_CONTEXT_TURNS * 2
