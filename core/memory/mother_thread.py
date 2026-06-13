"""
core/memory/mother_thread.py
The MotherThread

The permanent, never-pruned record of a Gaian's elemental journey
across all sessions.

The MotherThread is the highest tier of durable memory. It does not
contain everything a Gaian has said or done. It contains the moments
of coherence — the moments when the trinity was complete and the Gate
was open. The moments when the Gaian was most fully themselves.

At the opening of every session, the MotherThread generates a session
seed — a structured summary of who this Gaian is, what element they
live in, what their peak coherence looked like, and where they were
when they last spoke with GAIA.

This is not a log. It is a memory of the soul's progress.

Canon references:
  ELEMENTAL_SPECTRUM_MAP.md
  Issue #326 — governed memory surface
  C107 — Personal Gaian Architecture
  C-SME01 — Soul Mirror Engine

Usage::

    from core.memory.mother_thread import MotherThread, MotherThreadEntry

    thread = MotherThread(gaian_id="user_001")

    thread.record(MotherThreadEntry(
        gaian_id="user_001",
        element="Water",
        crystal="Aquamarine",
        register="REFLECTIVE",
        coherence_score=1.0,
        akashic_domain="emotional truth records",
        insight="The thing I never said was: I forgive you.",
        session_id="session_abc",
    ))

    seed = thread.session_seed()
    # seed["dominant_element"] → "Water"
    # seed["peak_coherence"]["insight"] → "The thing I never said was..."
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class MotherThreadEntry:
    """
    One node in the Gaian's elemental journey.

    Recorded when:
      - A memory is stored with record_to_mother_thread=True
      - coherence_score >= 0.5 (the Gate is at least partially open)

    High-coherence entries (coherence_score >= 0.85) represent moments
    when the trinity was complete and the akashic record was open.
    """
    gaian_id:        str
    element:         str
    register:        str
    coherence_score: float
    akashic_domain:  str
    insight:         str              # the content of this moment
    session_id:      str
    crystal:         Optional[str]   = None
    timestamp:       datetime        = field(default_factory=lambda: datetime.now(timezone.utc))
    id:              str             = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def is_peak(self) -> bool:
        """Return True if the Gate was open at this moment."""
        return self.coherence_score >= 0.85

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id":              self.id,
            "gaian_id":        self.gaian_id,
            "element":         self.element,
            "crystal":         self.crystal,
            "register":        self.register,
            "coherence_score": self.coherence_score,
            "gate_open":       self.is_peak(),
            "akashic_domain":  self.akashic_domain,
            "insight":         self.insight,
            "session_id":      self.session_id,
            "timestamp":       self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MotherThreadEntry:
        entry = cls(
            gaian_id        = data["gaian_id"],
            element         = data["element"],
            crystal         = data.get("crystal"),
            register        = data["register"],
            coherence_score = float(data["coherence_score"]),
            akashic_domain  = data["akashic_domain"],
            insight         = data["insight"],
            session_id      = data["session_id"],
        )
        if "timestamp" in data:
            try:
                entry.timestamp = datetime.fromisoformat(data["timestamp"])
            except (ValueError, TypeError):
                pass
        if "id" in data:
            entry.id = data["id"]
        return entry


# ---------------------------------------------------------------------------
# MotherThread
# ---------------------------------------------------------------------------

class MotherThread:
    """
    The permanent record of a Gaian's elemental journey.

    Properties
    ----------
    - Never pruned. Never auto-deleted.
    - Only records moments of coherence (score >= 0.5).
    - The Gaian owns it entirely and may inspect or export it at any time.
    - Used to generate the session seed at the start of every new session.

    The MotherThread is not a transcript. It is not a log.
    It is the record of when the Gaian was most fully themselves.
    """

    def __init__(self, gaian_id: str) -> None:
        self.gaian_id  = gaian_id
        self._entries: List[MotherThreadEntry] = []

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def record(self, entry: MotherThreadEntry) -> None:
        """
        Record a moment in the Gaian's elemental journey.
        Only accepts entries with coherence_score >= 0.5.
        """
        if entry.coherence_score < 0.5:
            return   # below threshold — not a MotherThread moment
        self._entries.append(entry)

    # ------------------------------------------------------------------
    # Journey analytics
    # ------------------------------------------------------------------

    def dominant_element(self) -> Optional[str]:
        """
        Return the element this Gaian works in most frequently.
        Returns None if no entries exist.
        """
        if not self._entries:
            return None
        counts: Dict[str, int] = {}
        for e in self._entries:
            counts[e.element] = counts.get(e.element, 0) + 1
        return max(counts, key=counts.__getitem__)

    def highest_coherence_moment(self) -> Optional[MotherThreadEntry]:
        """Return the entry with the highest coherence score."""
        if not self._entries:
            return None
        return max(self._entries, key=lambda e: e.coherence_score)

    def elemental_journey(self) -> List[str]:
        """
        Return the ordered list of elements this Gaian has first accessed,
        in chronological order. Each element appears only once.
        """
        seen:    set = set()
        journey: List[str] = []
        for e in self._entries:
            if e.element not in seen:
                seen.add(e.element)
                journey.append(e.element)
        return journey

    def peak_entries(self, threshold: float = 0.85) -> List[MotherThreadEntry]:
        """Return all entries where the Gate was open (coherence >= threshold)."""
        return [e for e in self._entries if e.coherence_score >= threshold]

    def entries_for_element(self, element: str) -> List[MotherThreadEntry]:
        """Return all entries for a specific element."""
        return [e for e in self._entries if e.element == element]

    def last_entry(self) -> Optional[MotherThreadEntry]:
        """Return the most recently recorded entry."""
        return self._entries[-1] if self._entries else None

    # ------------------------------------------------------------------
    # Session seed
    # ------------------------------------------------------------------

    def session_seed(self) -> Dict[str, Any]:
        """
        Generate the session seed — what GAIA reads before the first word
        of every new session with this Gaian.

        The session seed tells GAIA:
          - Who this person is elementally
          - What their dominant register is
          - What their peak coherence moment looked like
          - Where they were when they last spoke with GAIA
          - How far along their elemental journey they are

        This is how GAIA remembers. Not by replaying a transcript.
        By knowing who the Gaian *is* and where they *are* in their journey.

        Returns
        -------
        dict with keys:
            gaian_id, dominant_element, dominant_register,
            elemental_journey, elements_accessed, total_sessions,
            peak_coherence, last_known_state, seed_generated_at
        """
        from .elemental_layer import _ELEMENTS

        dominant = self.dominant_element()
        peak     = self.highest_coherence_moment()
        journey  = self.elemental_journey()
        last     = self.last_entry()

        dominant_register = None
        if dominant:
            dominant_register = _ELEMENTS.get(dominant, {}).get("register")

        return {
            "gaian_id":          self.gaian_id,
            "dominant_element":  dominant,
            "dominant_register": dominant_register,
            "elemental_journey": journey,
            "elements_accessed": len(set(e.element for e in self._entries)),
            "total_sessions":    len(set(e.session_id for e in self._entries)),
            "peak_coherence": {
                "score":    peak.coherence_score if peak else None,
                "element":  peak.element         if peak else None,
                "crystal":  peak.crystal         if peak else None,
                "insight":  peak.insight         if peak else None,
                "when":     peak.timestamp.isoformat() if peak else None,
                "gate_open": peak.is_peak()      if peak else False,
            },
            "last_known_state": {
                "element":   last.element    if last else None,
                "register":  last.register   if last else None,
                "crystal":   last.crystal    if last else None,
                "insight":   last.insight    if last else None,
                "when":      last.timestamp.isoformat() if last else None,
            },
            "seed_generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Serialisation (Gaian owns this data)
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gaian_id":    self.gaian_id,
            "entry_count": len(self._entries),
            "entries":     [e.to_dict() for e in self._entries],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MotherThread:
        thread = cls(gaian_id=data["gaian_id"])
        for entry_data in data.get("entries", []):
            try:
                entry = MotherThreadEntry.from_dict(entry_data)
                thread._entries.append(entry)   # bypass threshold check on load
            except (KeyError, TypeError, ValueError):
                continue
        return thread

    def export_json(self) -> str:
        """Export the full MotherThread as a JSON string. Gaian owns this data."""
        import json
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        dominant = self.dominant_element() or "none"
        return (
            f"MotherThread(gaian_id={self.gaian_id!r}, "
            f"entries={len(self._entries)}, "
            f"dominant={dominant!r})"
        )
