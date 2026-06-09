"""Test suite for Canon versioning, diff, amendment workflow,
conflict detection, and regulatory export — issue #249.

All tests use a temporary CanonStore pointed at a tmp_path so
no production data is touched.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.canon_store import CanonEntry, CanonStore
from core.governance.canon_diff import CanonDiffer, DiffReport


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def store(tmp_path: Path) -> CanonStore:
    return CanonStore(store_path=tmp_path / "canon")


@pytest.fixture()
def populated_store(store: CanonStore) -> CanonStore:
    """Store with two entries and one approved amendment (three versions)."""
    # Seed v0.1.0 with two entries by directly mutating internals
    store._entries = {
        "C01": CanonEntry(id="C01", title="Sovereignty",
                          body="GAIA must always respect Gaian autonomy.",
                          tags=["autonomy", "sovereignty"]),
        "C02": CanonEntry(id="C02", title="Transparency",
                          body="GAIA must never conceal its reasoning.",
                          tags=["transparency", "honesty"]),
    }
    store._save_all()
    store._snapshot()   # snapshot at v0.1.0

    # Propose + approve an update to C01
    amd = store.propose_amendment(
        action="update",
        entry_id="C01",
        proposed_by="gaian-root",
        justification="Clarify scope.",
        new_body="GAIA must always respect and protect Gaian autonomy.",
    )
    store.approve_amendment(amd.amendment_id, reviewed_by="gaian-root")
    # Now at v0.1.1 with a snapshot
    return store


@pytest.fixture()
def differ(populated_store: CanonStore) -> CanonDiffer:
    return CanonDiffer(populated_store)


# ---------------------------------------------------------------------------
# Versioning tests
# ---------------------------------------------------------------------------


class TestVersioning:
    def test_initial_version(self, store: CanonStore) -> None:
        assert store.version == "0.1.0"

    def test_version_bumps_on_approve(self, populated_store: CanonStore) -> None:
        assert populated_store.version == "0.1.1"

    def test_snapshot_created_on_approve(self, populated_store: CanonStore) -> None:
        assert "0.1.1" in populated_store.list_snapshots()

    def test_snapshot_contains_entries(self, populated_store: CanonStore) -> None:
        snap = populated_store.load_snapshot("0.1.1")
        assert "C01" in snap["entries"]
        assert "C02" in snap["entries"]

    def test_load_nonexistent_snapshot_raises(self, populated_store: CanonStore) -> None:
        with pytest.raises(FileNotFoundError):
            populated_store.load_snapshot("9.9.9")


# ---------------------------------------------------------------------------
# Amendment workflow tests
# ---------------------------------------------------------------------------


class TestAmendments:
    def test_propose_creates_pending_amendment(self, store: CanonStore) -> None:
        store._entries["C01"] = CanonEntry(
            id="C01", title="T", body="Original body.", tags=[]
        )
        store._save_all()
        amd = store.propose_amendment(
            action="update",
            entry_id="C01",
            proposed_by="gaian-1",
            justification="Improve wording.",
            new_body="Improved body.",
        )
        assert amd.status == "pending"
        assert len(store.pending_amendments()) == 1

    def test_approve_applies_change(self, store: CanonStore) -> None:
        store._entries["C01"] = CanonEntry(
            id="C01", title="T", body="Old.", tags=[]
        )
        store._save_all()
        amd = store.propose_amendment(
            action="update", entry_id="C01",
            proposed_by="g1", justification="x", new_body="New.",
        )
        store.approve_amendment(amd.amendment_id, reviewed_by="g1")
        assert store.get("C01").body == "New."

    def test_reject_sets_rejected_status(self, store: CanonStore) -> None:
        store._entries["C01"] = CanonEntry(
            id="C01", title="T", body="Body.", tags=[]
        )
        store._save_all()
        amd = store.propose_amendment(
            action="update", entry_id="C01",
            proposed_by="g1", justification="x", new_body="Alt.",
        )
        store.reject_amendment(amd.amendment_id, reviewed_by="reviewer")
        assert amd.status == "rejected"
        assert store.get("C01").body == "Body."  # unchanged

    def test_double_approve_raises(self, populated_store: CanonStore) -> None:
        amd_id = populated_store._amendments[0].amendment_id
        with pytest.raises(ValueError):
            populated_store.approve_amendment(amd_id, reviewed_by="g")

    def test_add_new_entry_via_amendment(self, store: CanonStore) -> None:
        amd = store.propose_amendment(
            action="add", entry_id="C99",
            proposed_by="g1", justification="New principle.",
            new_body="All Gaians are equal.", new_title="Equality",
        )
        store.approve_amendment(amd.amendment_id, reviewed_by="g1",
                                new_title="Equality")
        assert store.get("C99") is not None
        assert store.get("C99").title == "Equality"

    def test_remove_entry_via_amendment(self, populated_store: CanonStore) -> None:
        amd = populated_store.propose_amendment(
            action="remove", entry_id="C02",
            proposed_by="g1", justification="Deprecated.",
        )
        populated_store.approve_amendment(amd.amendment_id, reviewed_by="g1")
        assert populated_store.get("C02") is None


# ---------------------------------------------------------------------------
# Diff tests
# ---------------------------------------------------------------------------


class TestCanonDiff:
    def test_diff_detects_modified_entry(self, differ: CanonDiffer,
                                         populated_store: CanonStore) -> None:
        report = differ.diff_versions("0.1.0", "0.1.1")
        modified_ids = {e.entry_id for e in report.modified}
        assert "C01" in modified_ids

    def test_diff_unchanged_entry_not_in_modified(self, differ: CanonDiffer,
                                                   populated_store: CanonStore) -> None:
        report = differ.diff_versions("0.1.0", "0.1.1")
        modified_ids = {e.entry_id for e in report.modified}
        assert "C02" not in modified_ids

    def test_diff_added_entry(self, differ: CanonDiffer,
                              populated_store: CanonStore) -> None:
        amd = populated_store.propose_amendment(
            action="add", entry_id="C03",
            proposed_by="g", justification="new.",
            new_body="New entry body.", new_title="New",
        )
        populated_store.approve_amendment(amd.amendment_id, reviewed_by="g",
                                          new_title="New")
        report = differ.diff_versions("0.1.1", populated_store.version)
        added_ids = {e.entry_id for e in report.added}
        assert "C03" in added_ids

    def test_diff_removed_entry(self, differ: CanonDiffer,
                                populated_store: CanonStore) -> None:
        amd = populated_store.propose_amendment(
            action="remove", entry_id="C02",
            proposed_by="g", justification="drop.",
        )
        populated_store.approve_amendment(amd.amendment_id, reviewed_by="g")
        report = differ.diff_versions("0.1.1", populated_store.version)
        removed_ids = {e.entry_id for e in report.removed}
        assert "C02" in removed_ids

    def test_diff_changelog_mentions_version(self, differ: CanonDiffer) -> None:
        report = differ.diff_versions("0.1.0", "0.1.1")
        assert "0.1.0" in report.changelog
        assert "0.1.1" in report.changelog

    def test_diff_no_changes_message(self, differ: CanonDiffer) -> None:
        report = differ.diff_versions("0.1.1", "0.1.1")
        assert "No changes" in report.changelog

    def test_diff_body_patch_populated(self, differ: CanonDiffer) -> None:
        report = differ.diff_versions("0.1.0", "0.1.1")
        c01_diff = next(e for e in report.modified if e.entry_id == "C01")
        assert len(c01_diff.body_patch) > 0

    def test_diff_live_vs_snapshot(self, differ: CanonDiffer,
                                   populated_store: CanonStore) -> None:
        report = differ.diff_live_vs_snapshot("0.1.0")
        assert report.version_before == "0.1.0"
        assert report.version_after == populated_store.version

    def test_total_changes_count(self, differ: CanonDiffer) -> None:
        report = differ.diff_versions("0.1.0", "0.1.1")
        assert report.total_changes == 1  # only C01 was modified

    def test_diff_to_dict_is_json_serialisable(self, differ: CanonDiffer) -> None:
        report = differ.diff_versions("0.1.0", "0.1.1")
        dumped = json.dumps(report.to_dict())  # must not raise
        assert "version_before" in dumped


# ---------------------------------------------------------------------------
# Conflict detection tests
# ---------------------------------------------------------------------------


class TestConflictDetection:
    def test_duplicate_body_detected(self, store: CanonStore) -> None:
        body = "GAIA must always protect Gaian autonomy."
        store._entries = {
            "C01": CanonEntry(id="C01", title="A", body=body, tags=["x"]),
            "C02": CanonEntry(id="C02", title="B", body=body, tags=["x"]),
        }
        conflicts = store.detect_conflicts()
        assert any(c.entry_a in ("C01", "C02") for c in conflicts)

    def test_negation_conflict_detected(self, store: CanonStore) -> None:
        store._entries = {
            "C01": CanonEntry(id="C01", title="A",
                              body="GAIA must always log actions.",
                              tags=["logging"]),
            "C02": CanonEntry(id="C02", title="B",
                              body="GAIA must not log user data.",
                              tags=["logging"]),
        }
        conflicts = store.detect_conflicts()
        assert len(conflicts) >= 1

    def test_no_conflict_unrelated_entries(self, store: CanonStore) -> None:
        store._entries = {
            "C01": CanonEntry(id="C01", title="A",
                              body="GAIA must be efficient.", tags=["perf"]),
            "C02": CanonEntry(id="C02", title="B",
                              body="GAIA must be honest.", tags=["ethics"]),
        }
        conflicts = store.detect_conflicts()
        assert len(conflicts) == 0


# ---------------------------------------------------------------------------
# Regulatory export tests
# ---------------------------------------------------------------------------


class TestRegulatoryExport:
    def test_export_has_required_keys(self, populated_store: CanonStore) -> None:
        export = populated_store.regulatory_export()
        for key in ("gaia_canon_export", "version", "entries",
                    "amendment_log", "conflicts_at_export"):
            assert key in export

    def test_export_entry_count_matches(self, populated_store: CanonStore) -> None:
        export = populated_store.regulatory_export()
        assert export["total_entries"] == len(populated_store.all_entries())

    def test_export_writes_to_file(self, populated_store: CanonStore,
                                   tmp_path: Path) -> None:
        out = tmp_path / "export.json"
        populated_store.regulatory_export(output_path=out)
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["gaia_canon_export"] is True

    def test_export_is_json_serialisable(self, populated_store: CanonStore) -> None:
        export = populated_store.regulatory_export()
        dumped = json.dumps(export)  # must not raise
        assert "version" in dumped
