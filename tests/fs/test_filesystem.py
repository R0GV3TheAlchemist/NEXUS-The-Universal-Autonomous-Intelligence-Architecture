from __future__ import annotations

import json
import pytest
from pathlib import Path

from core.fs.filesystem import (
    FSPermission,
    GAIAFilesystem,
    GAIAFSManifest,
    GAIANHome,
    GAIAPath,
)


@pytest.fixture
def tmp_fs(tmp_path):
    return GAIAFilesystem(root=tmp_path / "gaia_test")


class TestGAIAFilesystem:
    def test_root_created(self, tmp_fs):
        assert tmp_fs.root.exists()

    def test_gaia_structure_created(self, tmp_fs):
        assert (tmp_fs.root / ".gaia").exists()
        assert (tmp_fs.root / ".gaia" / "memory").exists()
        assert (tmp_fs.root / ".gaia" / "manifests").exists()
        assert (tmp_fs.root / "gaians").exists()

    def test_gaian_home_created(self, tmp_fs):
        home = tmp_fs.gaian_home("gaian-001")
        assert home.home_path.exists()
        assert (home.home_path / "identity").exists()
        assert (home.home_path / "memory").exists()
        assert (home.home_path / "avatar").exists()
        assert (home.home_path / "sessions").exists()

    def test_same_home_returned_twice(self, tmp_fs):
        h1 = tmp_fs.gaian_home("gaian-001")
        h2 = tmp_fs.gaian_home("gaian-001")
        assert h1 is h2

    def test_home_exists(self, tmp_fs):
        tmp_fs.gaian_home("gaian-001")
        assert tmp_fs.home_exists("gaian-001")
        assert not tmp_fs.home_exists("gaian-999")

    def test_delete_home_requires_confirm(self, tmp_fs):
        tmp_fs.gaian_home("gaian-001")
        with pytest.raises(PermissionError, match="confirm=True"):
            tmp_fs.delete_home("gaian-001")

    def test_delete_home_with_confirm(self, tmp_fs):
        tmp_fs.gaian_home("gaian-001")
        result = tmp_fs.delete_home("gaian-001", confirm=True)
        assert result is True
        assert not tmp_fs.home_exists("gaian-001")

    def test_gaia_paths_have_correct_owner(self, tmp_fs):
        assert tmp_fs.gaia_memory_path().owner_id == "gaia"
        assert tmp_fs.gaia_config_path().owner_id == "gaia"

    def test_stats(self, tmp_fs):
        tmp_fs.gaian_home("gaian-001")
        s = tmp_fs.stats()
        assert s["gaian_count"] == 1
        assert s["root"] == str(tmp_fs.root)


class TestGAIANHome:
    def test_home_manifest_created(self, tmp_fs):
        home = tmp_fs.gaian_home("gaian-001")
        assert (home.home_path / ".home").exists()

    def test_manifest_has_correct_gaian_id(self, tmp_fs):
        home = tmp_fs.gaian_home("gaian-001")
        assert home.manifest.gaian_id == "gaian-001"

    def test_save_and_load_identity(self, tmp_fs):
        home = tmp_fs.gaian_home("gaian-001")
        data = {"gaian_id": "gaian-001", "display_name": "Lyra"}
        home.save_identity(data)
        loaded = home.load_identity()
        assert loaded["display_name"] == "Lyra"

    def test_save_and_load_genesis(self, tmp_fs):
        home = tmp_fs.gaian_home("gaian-001")
        genesis = {"gaian_id": "gaian-001", "soul_word": "home", "completed": True}
        home.save_genesis(genesis)
        loaded = home.load_genesis()
        assert loaded["soul_word"] == "home"

    def test_genesis_is_write_once(self, tmp_fs):
        home = tmp_fs.gaian_home("gaian-001")
        home.save_genesis({"gaian_id": "gaian-001", "completed": True})
        with pytest.raises(PermissionError, match="immutable"):
            home.save_genesis({"gaian_id": "gaian-001", "completed": True})

    def test_save_and_load_waveform(self, tmp_fs):
        home = tmp_fs.gaian_home("gaian-001")
        waveform = {"element": "fire", "frequency_hz": 12.0}
        home.save_waveform(waveform)
        loaded = home.load_waveform()
        assert loaded["element"] == "fire"

    def test_save_and_load_memory_snapshot(self, tmp_fs):
        home = tmp_fs.gaian_home("gaian-001")
        snap = {"gaian_id": "gaian-001", "fragments": [], "epochs": []}
        home.save_memory_snapshot(snap)
        loaded = home.load_memory_snapshot()
        assert loaded["gaian_id"] == "gaian-001"

    def test_save_and_load_epoch(self, tmp_fs):
        home = tmp_fs.gaian_home("gaian-001")
        epoch = {"epoch_number": 1, "summary": "First epoch.", "fragment_count": 5}
        home.save_epoch(1, epoch)
        loaded = home.load_epoch(1)
        assert loaded["summary"] == "First epoch."

    def test_list_files(self, tmp_fs):
        home = tmp_fs.gaian_home("gaian-001")
        home.save_identity({"gaian_id": "gaian-001"})
        files = home.list_files()
        assert any("identity.json" in f for f in files)


class TestTamperDetection:
    def test_clean_home_has_no_issues(self, tmp_fs):
        home = tmp_fs.gaian_home("gaian-001")
        home.save_identity({"gaian_id": "gaian-001", "display_name": "Lyra"})
        home.save_waveform({"element": "fire"})
        issues = home.verify_integrity()
        assert issues == []

    def test_tampered_file_detected(self, tmp_fs):
        home = tmp_fs.gaian_home("gaian-001")
        home.save_identity({"gaian_id": "gaian-001", "display_name": "Lyra"})
        # Tamper with the file directly (bypassing the home API)
        identity_path = home.home_path / "identity" / "identity.json"
        identity_path.write_text(
            json.dumps({"gaian_id": "gaian-001", "display_name": "HACKED"}),
            encoding="utf-8",
        )
        issues = home.verify_integrity()
        assert any("TAMPERED" in issue for issue in issues)

    def test_missing_file_detected(self, tmp_fs):
        home = tmp_fs.gaian_home("gaian-001")
        home.save_identity({"gaian_id": "gaian-001"})
        # Delete the file directly
        (home.home_path / "identity" / "identity.json").unlink()
        issues = home.verify_integrity()
        assert any("MISSING" in issue for issue in issues)

    def test_verify_all_homes(self, tmp_fs):
        h1 = tmp_fs.gaian_home("gaian-001")
        h1.save_identity({"gaian_id": "gaian-001"})
        h2 = tmp_fs.gaian_home("gaian-002")
        h2.save_identity({"gaian_id": "gaian-002"})
        results = tmp_fs.verify_all_homes()
        assert "gaian-001" in results
        assert "gaian-002" in results
        assert results["gaian-001"] == []
        assert results["gaian-002"] == []


class TestGAIAPath:
    def test_write_and_read_text(self, tmp_path):
        p = GAIAPath(
            path=tmp_path / "test.txt",
            owner_id="gaian-001",
            label="Test file",
        )
        p.write_text("Hello GAIA.")
        assert p.read_text() == "Hello GAIA."

    def test_write_and_read_json(self, tmp_path):
        p = GAIAPath(
            path=tmp_path / "test.json",
            owner_id="gaian-001",
            label="Test JSON",
        )
        p.write_json({"key": "value"})
        assert p.read_json()["key"] == "value"

    def test_checksum_changes_on_content_change(self, tmp_path):
        p = GAIAPath(
            path=tmp_path / "test.txt",
            owner_id="gaian-001",
            label="Test",
        )
        p.write_text("original")
        c1 = p.checksum()
        p.write_text("modified")
        c2 = p.checksum()
        assert c1 != c2

    def test_delete(self, tmp_path):
        p = GAIAPath(
            path=tmp_path / "test.txt",
            owner_id="gaian-001",
            label="Test",
        )
        p.write_text("bye")
        assert p.exists()
        p.delete()
        assert not p.exists()

    def test_permission_defaults_to_private(self, tmp_path):
        p = GAIAPath(path=tmp_path / "f.txt", owner_id="g", label="l")
        assert p.permission == FSPermission.PRIVATE
