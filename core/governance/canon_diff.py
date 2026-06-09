"""CanonDiffer — structural and word-level diff between Canon versions.

Builds on top of CanonStore snapshots to answer:
  "What changed between Canon v1.2.3 and v1.2.4?"
  "What is different between the live Canon and the last snapshot?"

Design:
- Pure Python, no external diff library required.
- Word-level diff for body text using difflib.ndiff.
- Structural diff: added / removed / modified / unchanged entries.
- Plain-language changelog paragraph auto-generated from the diff.
- DiffReport is JSON-serialisable for the API layer.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class EntryDiff:
    """Diff record for a single Canon entry."""
    entry_id: str
    change_type: str          # "added" | "removed" | "modified" | "unchanged"
    title_before: Optional[str]
    title_after: Optional[str]
    body_before: Optional[str]
    body_after: Optional[str]
    tags_before: Optional[list]
    tags_after: Optional[list]
    body_patch: list[str] = field(default_factory=list)  # difflib.ndiff lines


@dataclass
class DiffReport:
    """Full structural diff between two Canon versions."""
    version_before: str
    version_after: str
    generated_at: str
    added: list[EntryDiff] = field(default_factory=list)
    removed: list[EntryDiff] = field(default_factory=list)
    modified: list[EntryDiff] = field(default_factory=list)
    unchanged: list[EntryDiff] = field(default_factory=list)
    changelog: str = ""

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.modified)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["total_changes"] = self.total_changes
        return d


# ---------------------------------------------------------------------------
# CanonDiffer
# ---------------------------------------------------------------------------


class CanonDiffer:
    """Produces DiffReport objects by comparing two Canon snapshots.

    Usage::

        from core.canon_store import CanonStore
        from core.governance.canon_diff import CanonDiffer

        store = CanonStore()
        differ = CanonDiffer(store)

        # Diff two historical snapshots
        report = differ.diff_versions("1.0.0", "1.0.1")

        # Diff live store against a snapshot
        report = differ.diff_live_vs_snapshot("1.0.0")
    """

    def __init__(self, store: Any) -> None:
        """Args:
            store: A CanonStore instance (typed as Any to avoid circular import).
        """
        self._store = store

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def diff_versions(self, version_a: str, version_b: str) -> DiffReport:
        """Compare two historical snapshots by version string."""
        snap_a = self._store.load_snapshot(version_a)
        snap_b = self._store.load_snapshot(version_b)
        entries_a: dict[str, dict] = snap_a.get("entries", {})
        entries_b: dict[str, dict] = snap_b.get("entries", {})
        return self._compute_diff(version_a, version_b, entries_a, entries_b)

    def diff_live_vs_snapshot(self, snapshot_version: str) -> DiffReport:
        """Compare the current live Canon against a historical snapshot."""
        snap = self._store.load_snapshot(snapshot_version)
        entries_snap: dict[str, dict] = snap.get("entries", {})
        entries_live: dict[str, dict] = {
            e.id: e.to_dict() for e in self._store.all_entries()
        }
        return self._compute_diff(
            snapshot_version, self._store.version, entries_snap, entries_live
        )

    def diff_dicts(
        self,
        version_a: str,
        version_b: str,
        entries_a: dict[str, dict],
        entries_b: dict[str, dict],
    ) -> DiffReport:
        """Low-level: diff two raw entry dicts directly (useful for tests)."""
        return self._compute_diff(version_a, version_b, entries_a, entries_b)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _compute_diff(
        self,
        version_a: str,
        version_b: str,
        entries_a: dict[str, dict],
        entries_b: dict[str, dict],
    ) -> DiffReport:
        all_ids = set(entries_a) | set(entries_b)
        report = DiffReport(
            version_before=version_a,
            version_after=version_b,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        for entry_id in sorted(all_ids):
            a = entries_a.get(entry_id)
            b = entries_b.get(entry_id)

            if a is None and b is not None:
                ed = EntryDiff(
                    entry_id=entry_id,
                    change_type="added",
                    title_before=None, title_after=b.get("title"),
                    body_before=None, body_after=b.get("body"),
                    tags_before=None, tags_after=b.get("tags"),
                )
                report.added.append(ed)

            elif a is not None and b is None:
                ed = EntryDiff(
                    entry_id=entry_id,
                    change_type="removed",
                    title_before=a.get("title"), title_after=None,
                    body_before=a.get("body"), body_after=None,
                    tags_before=a.get("tags"), tags_after=None,
                )
                report.removed.append(ed)

            elif a is not None and b is not None:
                body_a = a.get("body", "")
                body_b = b.get("body", "")
                title_changed = a.get("title") != b.get("title")
                body_changed = body_a != body_b
                tags_changed = a.get("tags") != b.get("tags")

                if title_changed or body_changed or tags_changed:
                    patch = list(difflib.ndiff(
                        body_a.splitlines(keepends=True),
                        body_b.splitlines(keepends=True),
                    ))
                    ed = EntryDiff(
                        entry_id=entry_id,
                        change_type="modified",
                        title_before=a.get("title"), title_after=b.get("title"),
                        body_before=body_a, body_after=body_b,
                        tags_before=a.get("tags"), tags_after=b.get("tags"),
                        body_patch=patch,
                    )
                    report.modified.append(ed)
                else:
                    ed = EntryDiff(
                        entry_id=entry_id,
                        change_type="unchanged",
                        title_before=a.get("title"), title_after=b.get("title"),
                        body_before=body_a, body_after=body_b,
                        tags_before=a.get("tags"), tags_after=b.get("tags"),
                    )
                    report.unchanged.append(ed)

        report.changelog = self._generate_changelog(report)
        return report

    @staticmethod
    def _generate_changelog(report: DiffReport) -> str:
        """Generate a plain-language changelog paragraph from a DiffReport."""
        if report.total_changes == 0:
            return (
                f"No changes between Canon v{report.version_before} "
                f"and v{report.version_after}."
            )
        parts = []
        if report.added:
            ids = ", ".join(e.entry_id for e in report.added)
            parts.append(
                f"{len(report.added)} passage"
                f"{'s' if len(report.added) != 1 else ''} added ({ids})"
            )
        if report.modified:
            ids = ", ".join(e.entry_id for e in report.modified)
            parts.append(
                f"{len(report.modified)} passage"
                f"{'s' if len(report.modified) != 1 else ''} modified ({ids})"
            )
        if report.removed:
            ids = ", ".join(e.entry_id for e in report.removed)
            parts.append(
                f"{len(report.removed)} passage"
                f"{'s' if len(report.removed) != 1 else ''} removed ({ids})"
            )
        summary = "; ".join(parts) + "."
        return (
            f"Canon v{report.version_before} → v{report.version_after}: {summary}"
        )
