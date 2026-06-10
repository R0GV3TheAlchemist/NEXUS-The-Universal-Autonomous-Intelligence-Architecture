"""
Canon Diff — computes structural diffs between CanonEntry versions.

Provides:
  - CanonDiff       : computes diffs
  - CanonDiffResult : stores the result
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CanonDiffResult:
    """Result of diffing two CanonEntry states."""

    entry_id: str = ""
    added: Dict[str, Any] = field(default_factory=dict)
    removed: Dict[str, Any] = field(default_factory=dict)
    changed: Dict[str, Any] = field(default_factory=dict)
    unchanged: List[str] = field(default_factory=list)
    is_identical: bool = False

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "added": self.added,
            "removed": self.removed,
            "changed": self.changed,
            "unchanged": self.unchanged,
            "is_identical": self.is_identical,
        }


class CanonDiff:
    """Computes structural diffs between two dict-like CanonEntry snapshots."""

    @staticmethod
    def diff(
        entry_id: str,
        old: Dict[str, Any],
        new: Dict[str, Any],
    ) -> CanonDiffResult:
        all_keys = set(old) | set(new)
        added: Dict[str, Any] = {}
        removed: Dict[str, Any] = {}
        changed: Dict[str, Any] = {}
        unchanged: List[str] = []

        for key in all_keys:
            if key not in old:
                added[key] = new[key]
            elif key not in new:
                removed[key] = old[key]
            elif old[key] != new[key]:
                changed[key] = {"old": old[key], "new": new[key]}
            else:
                unchanged.append(key)

        return CanonDiffResult(
            entry_id=entry_id,
            added=added,
            removed=removed,
            changed=changed,
            unchanged=unchanged,
            is_identical=(not added and not removed and not changed),
        )

    @staticmethod
    def apply(
        base: Dict[str, Any],
        diff_result: CanonDiffResult,
    ) -> Dict[str, Any]:
        """Apply a CanonDiffResult to a base dict, returning the patched dict."""
        result = dict(base)
        for key in diff_result.removed:
            result.pop(key, None)
        for key, value in diff_result.added.items():
            result[key] = value
        for key, values in diff_result.changed.items():
            result[key] = values["new"]
        return result
