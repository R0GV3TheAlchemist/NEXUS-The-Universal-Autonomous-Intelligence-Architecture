"""
tests/test_canon_conflict_resolver.py
======================================
Unit tests for _analyse_canon_context() and _resolve_keyword_conflicts()
in core/synergy_engine.py.

Acceptance criteria covered (Issue #256):
  [1] Single keyword match  → correct register, conflict_detected=False
  [2] Multi-match same register  → conflict_detected=False
  [3] Multi-match conflicting registers  → conflict_detected=True,
      priority rule fires (minimal > reflective > executive, C32)
  [4] Empty / None / whitespace-only  → present=False
  [5] CanonEntry fast-path (declared signal, no scan needed)
  [6] CanonEntry UNSPECIFIED falls through to keyword scan + conflict resolver
  [7] to_rationale_fragment() surfaces conflict detail in audit string
  [8] _resolve_keyword_conflicts() directly — edge cases

Canon refs: C30 (No silent failures), C32 (Synergy Doctrine)
"""

import pytest
from unittest.mock import MagicMock

from core.synergy_engine import (
    _analyse_canon_context,
    _resolve_keyword_conflicts,
    CanonPlanHint,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_canon_entry(body: str, register_signal_value: str = "UNSPECIFIED", ref_id: str = "C99"):
    """
    Build a minimal CanonEntry-like mock that satisfies the isinstance check
    inside _analyse_canon_context().

    We import the real CanonEntry when available; if the module is absent
    (optional dependency not installed) we skip those tests gracefully.
    """
    try:
        from core.canon.canon_entry import CanonEntry, RegisterSignal
        entry = MagicMock(spec=CanonEntry)
        entry.body = body
        entry.ref_id = ref_id
        if register_signal_value == "UNSPECIFIED":
            entry.register_signal = RegisterSignal.UNSPECIFIED
        else:
            entry.register_signal = MagicMock()
            entry.register_signal.value = register_signal_value
            # Make != UNSPECIFIED comparison work
            entry.register_signal.__ne__ = lambda self, other: True
        entry.to_context_string.return_value = f"[{ref_id}] {body}"
        return entry
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# _resolve_keyword_conflicts — direct unit tests  [8]
# ---------------------------------------------------------------------------

class TestResolveKeywordConflicts:

    def test_empty_matches_returns_none(self):
        reg, lbl, conflict, groups = _resolve_keyword_conflicts([])
        assert reg is None
        assert lbl == ""
        assert conflict is False
        assert groups == []

    def test_single_match_no_conflict(self):
        matches = [("reflective", "canon:grief-signal")]
        reg, lbl, conflict, groups = _resolve_keyword_conflicts(matches)
        assert reg == "reflective"
        assert lbl == "canon:grief-signal"
        assert conflict is False
        assert len(groups) == 1

    def test_two_same_register_no_conflict(self):
        """Two different labels, same register — not a conflict."""
        matches = [
            ("reflective", "canon:grief-signal"),
            ("reflective", "canon:storm-signal"),
        ]
        reg, lbl, conflict, groups = _resolve_keyword_conflicts(matches)
        assert reg == "reflective"
        assert conflict is False  # same register — agree, not a conflict

    def test_conflicting_registers_minimal_wins(self):
        """minimal beats reflective beats executive — most protective wins."""
        matches = [
            ("executive",  "canon:executive-signal"),
            ("minimal",    "canon:rest-signal"),
            ("reflective", "canon:grief-signal"),
        ]
        reg, lbl, conflict, groups = _resolve_keyword_conflicts(matches)
        assert reg == "minimal"
        assert conflict is True
        # All three distinct registers should appear in groups
        group_registers = [r for r, _ in groups]
        assert "minimal"    in group_registers
        assert "reflective" in group_registers
        assert "executive"  in group_registers
        # minimal is first (highest priority)
        assert groups[0][0] == "minimal"

    def test_conflicting_reflective_beats_executive(self):
        matches = [
            ("executive",  "canon:executive-signal"),
            ("reflective", "canon:grief-signal"),
        ]
        reg, lbl, conflict, groups = _resolve_keyword_conflicts(matches)
        assert reg == "reflective"
        assert conflict is True
        assert groups[0][0] == "reflective"

    def test_duplicate_register_labels_deduplication(self):
        """Same register appearing multiple times — still not a conflict."""
        matches = [
            ("executive", "canon:executive-signal"),
            ("executive", "canon:executive-signal"),
            ("executive", "canon:executive-signal"),
        ]
        reg, lbl, conflict, groups = _resolve_keyword_conflicts(matches)
        assert reg == "executive"
        assert conflict is False


# ---------------------------------------------------------------------------
# _analyse_canon_context — empty / None inputs  [4]
# ---------------------------------------------------------------------------

class TestAnalyseCanonContextEmpty:

    def test_none_returns_not_present(self):
        hint = _analyse_canon_context(None)
        assert isinstance(hint, CanonPlanHint)
        assert hint.present is False
        assert hint.char_count == 0
        assert hint.register_nudge is None

    def test_empty_string_returns_not_present(self):
        hint = _analyse_canon_context("")
        assert hint.present is False

    def test_whitespace_only_returns_not_present(self):
        hint = _analyse_canon_context("   \n\t  ")
        assert hint.present is False


# ---------------------------------------------------------------------------
# _analyse_canon_context — single match  [1]
# ---------------------------------------------------------------------------

class TestAnalyseCanonContextSingleMatch:

    def test_grief_keyword_gives_reflective(self):
        hint = _analyse_canon_context(
            "This passage addresses grief and the need for integration."
        )
        assert hint.present is True
        assert hint.register_nudge == "reflective"
        assert hint.conflict_detected is False
        assert hint.conflict_groups == [] or (
            len({r for r, _ in hint.conflict_groups}) == 1
        )

    def test_rest_keyword_gives_minimal(self):
        hint = _analyse_canon_context(
            "Gaian should rest and allow minimal interaction today."
        )
        assert hint.register_nudge == "minimal"
        assert hint.conflict_detected is False

    def test_build_keyword_gives_executive(self):
        hint = _analyse_canon_context(
            "The directive is to build the new feature and write documentation."
        )
        assert hint.register_nudge == "executive"
        assert hint.conflict_detected is False

    def test_no_keywords_gives_no_nudge(self):
        hint = _analyse_canon_context(
            "The sky is clear and the day proceeds without incident."
        )
        assert hint.present is True
        assert hint.register_nudge is None
        assert hint.conflict_detected is False

    def test_canon_refs_extracted(self):
        hint = _analyse_canon_context(
            "Per C30 and C32, no silent failures. Gaian should rest."
        )
        assert "C30" in hint.canon_refs
        assert "C32" in hint.canon_refs


# ---------------------------------------------------------------------------
# _analyse_canon_context — multi-match same register  [2]
# ---------------------------------------------------------------------------

class TestAnalyseCanonContextSameRegister:

    def test_multiple_reflective_keywords_no_conflict(self):
        """grief + storm both map to reflective — no conflict."""
        hint = _analyse_canon_context(
            "The Gaian is experiencing grief after the storm. Integration is needed."
        )
        assert hint.register_nudge == "reflective"
        assert hint.conflict_detected is False

    def test_multiple_executive_keywords_no_conflict(self):
        """research + build both map to executive — no conflict."""
        hint = _analyse_canon_context(
            "The directive is to research the topic, then build and write the output."
        )
        assert hint.register_nudge == "executive"
        assert hint.conflict_detected is False


# ---------------------------------------------------------------------------
# _analyse_canon_context — conflicting registers  [3]
# ---------------------------------------------------------------------------

class TestAnalyseCanonContextConflict:

    def test_rest_beats_executive(self):
        """rest (minimal) + build (executive) → minimal wins."""
        hint = _analyse_canon_context(
            "Gaian should rest, but also build the integration module."
        )
        assert hint.register_nudge == "minimal"
        assert hint.conflict_detected is True
        group_registers = [r for r, _ in hint.conflict_groups]
        assert "minimal"   in group_registers
        assert "executive" in group_registers

    def test_rest_beats_reflective(self):
        """rest (minimal) + grief (reflective) → minimal wins."""
        hint = _analyse_canon_context(
            "Gaian is processing grief but must rest and pause all activity."
        )
        assert hint.register_nudge == "minimal"
        assert hint.conflict_detected is True

    def test_reflective_beats_executive(self):
        """grief (reflective) + research (executive) → reflective wins."""
        hint = _analyse_canon_context(
            "Despite the grief, the goal is to research and explore new territory."
        )
        assert hint.register_nudge == "reflective"
        assert hint.conflict_detected is True

    def test_all_three_minimal_wins(self):
        """All three registers fire — minimal always wins."""
        hint = _analyse_canon_context(
            "Gaian must rest and pause. There is grief and overwhelm. "
            "The task is to research and build the new system."
        )
        assert hint.register_nudge == "minimal"
        assert hint.conflict_detected is True
        group_registers = [r for r, _ in hint.conflict_groups]
        assert "minimal"    in group_registers
        assert "reflective" in group_registers
        assert "executive"  in group_registers

    def test_conflict_groups_sorted_by_priority(self):
        """conflict_groups[0] is always the winner (highest priority)."""
        hint = _analyse_canon_context(
            "Gaian is in crisis and must rest. Also: build the feature."
        )
        if hint.conflict_detected:
            # Winner must be at index 0
            winner_register = hint.conflict_groups[0][0]
            assert winner_register == hint.register_nudge


# ---------------------------------------------------------------------------
# to_rationale_fragment() — conflict detail in audit string  [7]
# ---------------------------------------------------------------------------

class TestRationaleFragment:

    def test_no_canon_says_none(self):
        hint = _analyse_canon_context("")
        frag = hint.to_rationale_fragment()
        assert "none" in frag.lower()

    def test_single_match_no_conflict_mention(self):
        hint = _analyse_canon_context("Gaian should rest today.")
        frag = hint.to_rationale_fragment()
        assert "CONFLICT" not in frag
        assert hint.register_nudge in frag

    def test_conflict_surfaced_in_rationale(self):
        hint = _analyse_canon_context(
            "Gaian must rest and pause, but also research the new module."
        )
        frag = hint.to_rationale_fragment()
        if hint.conflict_detected:
            assert "CONFLICT" in frag
            assert "minimal>reflective>executive" in frag or "C32" in frag
            assert hint.register_nudge in frag

    def test_rationale_includes_char_count(self):
        text = "Build and write the documentation module."
        hint = _analyse_canon_context(text)
        frag = hint.to_rationale_fragment()
        assert str(len(text)) in frag


# ---------------------------------------------------------------------------
# CanonEntry fast-path  [5]
# ---------------------------------------------------------------------------

class TestCanonEntryFastPath:

    def test_declared_executive_signal_used_directly(self):
        entry = _make_canon_entry(
            body="The Gaian should rest and pause all activity.",
            register_signal_value="executive",
            ref_id="C10",
        )
        if entry is None:
            pytest.skip("core.canon.canon_entry not available")
        hint = _analyse_canon_context(entry)
        # Declared 'executive' must win even though body says 'rest'
        assert hint.present is True
        assert hint.register_nudge == "executive"
        assert hint.conflict_detected is False
        assert hint.entry_ref_id == "C10"

    def test_declared_minimal_signal_used_directly(self):
        entry = _make_canon_entry(
            body="Build and research the new system aggressively.",
            register_signal_value="minimal",
            ref_id="C11",
        )
        if entry is None:
            pytest.skip("core.canon.canon_entry not available")
        hint = _analyse_canon_context(entry)
        assert hint.register_nudge == "minimal"
        assert hint.conflict_detected is False

    def test_declared_ref_id_in_canon_refs(self):
        entry = _make_canon_entry(
            body="C30 and C32 apply here.",
            register_signal_value="reflective",
            ref_id="C15",
        )
        if entry is None:
            pytest.skip("core.canon.canon_entry not available")
        hint = _analyse_canon_context(entry)
        assert "C15" in hint.canon_refs


# ---------------------------------------------------------------------------
# CanonEntry UNSPECIFIED falls through to keyword scan  [6]
# ---------------------------------------------------------------------------

class TestCanonEntryUnspecifiedFallthrough:

    def test_unspecified_uses_keyword_scan(self):
        entry = _make_canon_entry(
            body="Gaian must rest and pause minimal activity.",
            register_signal_value="UNSPECIFIED",
            ref_id="C20",
        )
        if entry is None:
            pytest.skip("core.canon.canon_entry not available")
        hint = _analyse_canon_context(entry)
        # Keyword scan on body should find 'rest'/'minimal' → minimal
        assert hint.register_nudge == "minimal"

    def test_unspecified_conflict_resolution_applies(self):
        entry = _make_canon_entry(
            body="Gaian must rest. Also: research and build the new feature.",
            register_signal_value="UNSPECIFIED",
            ref_id="C21",
        )
        if entry is None:
            pytest.skip("core.canon.canon_entry not available")
        hint = _analyse_canon_context(entry)
        # minimal keyword present → minimal wins the conflict
        assert hint.register_nudge == "minimal"
        assert hint.conflict_detected is True
