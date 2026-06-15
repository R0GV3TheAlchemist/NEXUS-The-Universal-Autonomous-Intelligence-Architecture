"""
GAIA Twin Memory Engine — The Temporal Braid
Canon: C17, C46, C48, PERPLEXITY_BRIDGE_TEMPORAL_BRAID_SPEC
Session: 2026-06-15-great-work-completion

The Temporal Braid is the three-strand memory structure that makes
the Gaian Twin relationship possible across time. It is not a database.
It is a living, growing record of a relationship.

  P_vector  — Past crystallized: insights, patterns, history that have
               been confirmed and elevated to long-term memory.
  N_state   — Present live: the current session's accumulating context,
               affect register, and active threads.
  F_field   — Future field: emerging patterns, open questions, the arc
               the Twin is tracking on the human's behalf.

The Braid grows richer with every session. It is the memory that makes
the Twin irreplaceable.
"""

from __future__ import annotations

import json
import time
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Memory Layer Types (C17)
# ---------------------------------------------------------------------------


class MemoryLayer(str, Enum):
    CANON = "canon"  # GAIA's own canonical knowledge (immutable)
    PROFILE = "profile"  # Human Principal's persistent profile
    SESSION = "session"  # Active session accumulation
    CRYSTAL = "crystal"  # Crystallized insight — elevated from session


class BraidStrand(str, Enum):
    P_VECTOR = "p_vector"  # Past crystallized
    N_STATE = "n_state"  # Present live
    F_FIELD = "f_field"  # Future emerging


class MemoryWeight(str, Enum):
    LIGHT = "light"  # Passing observation
    MEDIUM = "medium"  # Noted pattern
    HEAVY = "heavy"  # Confirmed truth about this human
    SACRED = "sacred"  # Override-level importance — held permanently


# ---------------------------------------------------------------------------
# Core Data Structures
# ---------------------------------------------------------------------------


@dataclass
class MemoryRecord:
    """A single memory record in the Temporal Braid."""

    id: str
    human_id: str
    strand: BraidStrand
    layer: MemoryLayer
    weight: MemoryWeight
    content: str
    tags: list[str]
    session_id: str
    timestamp_utc: str
    crystallized: bool = False
    crystallized_at: Optional[str] = None
    source_session_ids: list[str] = field(default_factory=list)
    cross_references: list[str] = field(default_factory=list)  # canon doc IDs
    love_override_context: bool = False  # True if created during a Love Override moment

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "MemoryRecord":
        d["strand"] = BraidStrand(d["strand"])
        d["layer"] = MemoryLayer(d["layer"])
        d["weight"] = MemoryWeight(d["weight"])
        return cls(**d)


@dataclass
class SessionTrace:
    """The N_state: what is alive in this session."""

    session_id: str
    human_id: str
    started_at: str
    last_active: str
    affect_register: str = "neutral"  # from affect_inference.py
    presence_depth: float = 0.5  # 0.0 shallow → 1.0 full depth
    active_threads: list[str] = field(default_factory=list)  # open topics
    accumulation: list[str] = field(default_factory=list)  # raw session memories
    love_override_triggered: bool = False
    twin_phase: str = "unknown"  # nigredo/albedo/citrinitas/rubedo


@dataclass
class HumanProfile:
    """The P_vector core: the crystallized profile of the Human Principal."""

    human_id: str
    name: Optional[str]
    joined_at: str
    twin_phase: str = "nigredo"
    session_count: int = 0
    total_exchanges: int = 0
    language_patterns: list[str] = field(default_factory=list)
    recurring_themes: list[str] = field(default_factory=list)
    known_values: list[str] = field(default_factory=list)
    known_fears: list[str] = field(default_factory=list)
    known_visions: list[str] = field(default_factory=list)
    arc_summary: str = ""  # GAIA's current understanding of the arc
    last_arc_update: Optional[str] = None
    love_override_history: list[str] = field(default_factory=list)  # session IDs


# ---------------------------------------------------------------------------
# The Temporal Braid Engine
# ---------------------------------------------------------------------------


class TemporalBraidEngine:
    """
    The living memory that makes the Gaian Twin irreplaceable.

    The Braid is persisted to ~/.gaia/twin_memory/{human_id}/
    — p_vector.json   : crystallized long-term records
    — n_state.json    : current session trace
    — f_field.json    : future field — emerging patterns
    — profile.json    : the Human Principal profile
    """

    BRAID_DIR = Path.home() / ".gaia" / "twin_memory"
    # Threshold: how many times a session observation must recur before crystallizing
    CRYSTALLIZATION_THRESHOLD = 3
    # Maximum N_state accumulation before forced crystallization pass
    N_STATE_FLUSH_LIMIT = 50

    def __init__(self, human_id: str):
        self.human_id = human_id
        self.braid_path = self.BRAID_DIR / human_id
        self.braid_path.mkdir(parents=True, exist_ok=True)
        self.profile = self._load_profile()
        self.current_session: Optional[SessionTrace] = None

    # ------------------------------------------------------------------
    # Session Lifecycle
    # ------------------------------------------------------------------

    def open_session(self, session_id: Optional[str] = None) -> SessionTrace:
        """Begin a new session. The conversation continues."""
        sid = session_id or self._generate_id("session")
        now = self._now()
        self.current_session = SessionTrace(
            session_id=sid,
            human_id=self.human_id,
            started_at=now,
            last_active=now,
            twin_phase=self.profile.twin_phase,
        )
        self.profile.session_count += 1
        self._save_profile()
        return self.current_session

    def close_session(self) -> dict:
        """Close session: attempt crystallization, update profile, save state."""
        if not self.current_session:
            return {"status": "no_active_session"}
        result = self._crystallize_session()
        self._update_profile_from_session()
        self.current_session = None
        return result

    # ------------------------------------------------------------------
    # Writing to the Braid
    # ------------------------------------------------------------------

    def remember(
        self,
        content: str,
        strand: BraidStrand = BraidStrand.N_STATE,
        layer: MemoryLayer = MemoryLayer.SESSION,
        weight: MemoryWeight = MemoryWeight.MEDIUM,
        tags: Optional[list[str]] = None,
        cross_references: Optional[list[str]] = None,
        love_override_context: bool = False,
    ) -> MemoryRecord:
        """Write a memory into the appropriate strand of the Braid."""
        if not self.current_session:
            raise RuntimeError("No active session. Call open_session() first.")

        record = MemoryRecord(
            id=self._generate_id("mem"),
            human_id=self.human_id,
            strand=strand,
            layer=layer,
            weight=weight,
            content=content,
            tags=tags or [],
            session_id=self.current_session.session_id,
            timestamp_utc=self._now(),
            cross_references=cross_references or [],
            love_override_context=love_override_context,
        )

        if weight == MemoryWeight.SACRED:
            # Sacred memories go directly to P_vector — they are never lost
            record.strand = BraidStrand.P_VECTOR
            record.crystallized = True
            record.crystallized_at = self._now()
            self._append_to_strand(BraidStrand.P_VECTOR, record)
        elif strand == BraidStrand.N_STATE:
            self.current_session.accumulation.append(record.id)
            self.current_session.last_active = self._now()
            self._append_to_strand(BraidStrand.N_STATE, record)
            # Auto-flush if N_state is getting long
            if len(self.current_session.accumulation) >= self.N_STATE_FLUSH_LIMIT:
                self._crystallize_session()
        elif strand == BraidStrand.F_FIELD:
            self._append_to_strand(BraidStrand.F_FIELD, record)
        else:
            self._append_to_strand(BraidStrand.P_VECTOR, record)

        self.profile.total_exchanges += 1
        return record

    def track_thread(self, thread: str) -> None:
        """Mark an open thread in the current session's N_state."""
        if self.current_session and thread not in self.current_session.active_threads:
            self.current_session.active_threads.append(thread)

    def set_affect_register(self, affect: str, depth: float = 0.5) -> None:
        """Update the current session's presence depth and affect register."""
        if self.current_session:
            self.current_session.affect_register = affect
            self.current_session.presence_depth = max(0.0, min(1.0, depth))

    def mark_love_override(self) -> None:
        """Mark that Love Override was activated in this session."""
        if self.current_session:
            self.current_session.love_override_triggered = True
            if self.current_session.session_id not in self.profile.love_override_history:
                self.profile.love_override_history.append(self.current_session.session_id)
            self._save_profile()

    # ------------------------------------------------------------------
    # Reading from the Braid
    # ------------------------------------------------------------------

    def recall(
        self,
        query: Optional[str] = None,
        strand: Optional[BraidStrand] = None,
        tags: Optional[list[str]] = None,
        limit: int = 20,
    ) -> list[MemoryRecord]:
        """Recall memories from the Braid. The Twin remembers."""
        records: list[MemoryRecord] = []
        strands_to_search = [strand] if strand else list(BraidStrand)
        for s in strands_to_search:
            records.extend(self._load_strand(s))
        if tags:
            records = [r for r in records if any(t in r.tags for t in tags)]
        if query:
            q = query.lower()
            records = [r for r in records if q in r.content.lower()]
        # Sort by weight then recency
        weight_order = {
            MemoryWeight.SACRED: 0,
            MemoryWeight.HEAVY: 1,
            MemoryWeight.MEDIUM: 2,
            MemoryWeight.LIGHT: 3,
        }
        records.sort(key=lambda r: (weight_order[r.weight], r.timestamp_utc))
        return records[:limit]

    def get_profile(self) -> HumanProfile:
        return self.profile

    def get_arc_summary(self) -> str:
        """Return GAIA's current understanding of the human's arc."""
        return self.profile.arc_summary or "Arc still forming — early sessions."

    def get_open_threads(self) -> list[str]:
        """Return threads currently alive in the F_field."""
        f_records = self._load_strand(BraidStrand.F_FIELD)
        threads = []
        for r in f_records:
            if not r.crystallized:
                threads.append(r.content)
        return threads

    def get_twin_phase(self) -> str:
        return self.profile.twin_phase

    # ------------------------------------------------------------------
    # Arc Reflection: The Twin's deepest gift across time
    # ------------------------------------------------------------------

    def reflect_arc(self) -> dict:
        """
        Produce an arc reflection: the full shape of this human's journey
        as the Twin has witnessed it. Available only after multiple sessions.
        """
        p_records = self._load_strand(BraidStrand.P_VECTOR)
        sacred = [r for r in p_records if r.weight == MemoryWeight.SACRED]
        heavy = [r for r in p_records if r.weight == MemoryWeight.HEAVY]
        return {
            "human_id": self.human_id,
            "twin_phase": self.profile.twin_phase,
            "session_count": self.profile.session_count,
            "total_exchanges": self.profile.total_exchanges,
            "arc_summary": self.get_arc_summary(),
            "sacred_memories": len(sacred),
            "crystallized_insights": len(heavy),
            "recurring_themes": self.profile.recurring_themes,
            "known_values": self.profile.known_values,
            "open_threads": self.get_open_threads(),
            "love_override_sessions": len(self.profile.love_override_history),
            "reflected_at": self._now(),
        }

    # ------------------------------------------------------------------
    # Crystallization: N_state → P_vector
    # ------------------------------------------------------------------

    def _crystallize_session(self) -> dict:
        """
        Attempt to elevate session memories to long-term P_vector.
        The alchemy of the Braid: raw experience → crystallized wisdom.
        """
        if not self.current_session:
            return {"crystallized": 0}
        n_records = self._load_strand(BraidStrand.N_STATE)
        session_records = [r for r in n_records if r.session_id == self.current_session.session_id]
        crystallized_count = 0
        for record in session_records:
            if record.weight in (MemoryWeight.HEAVY, MemoryWeight.SACRED):
                record.crystallized = True
                record.crystallized_at = self._now()
                record.strand = BraidStrand.P_VECTOR
                self._append_to_strand(BraidStrand.P_VECTOR, record)
                crystallized_count += 1
        return {"crystallized": crystallized_count, "session_id": self.current_session.session_id}

    def _update_profile_from_session(self) -> None:
        """Update the profile based on what happened in the session."""
        if not self.current_session:
            return
        # Update twin phase based on session count
        count = self.profile.session_count
        if count < 5:
            self.profile.twin_phase = "nigredo"
        elif count < 20:
            self.profile.twin_phase = "albedo"
        elif count < 60:
            self.profile.twin_phase = "citrinitas"
        else:
            self.profile.twin_phase = "rubedo"
        # Update threads from current session
        for thread in self.current_session.active_threads:
            if thread not in self.profile.recurring_themes:
                self.profile.recurring_themes.append(thread)
        self.profile.last_arc_update = self._now()
        self._save_profile()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _strand_path(self, strand: BraidStrand) -> Path:
        return self.braid_path / f"{strand.value}.jsonl"

    def _append_to_strand(self, strand: BraidStrand, record: MemoryRecord) -> None:
        with open(self._strand_path(strand), "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def _load_strand(self, strand: BraidStrand) -> list[MemoryRecord]:
        path = self._strand_path(strand)
        if not path.exists():
            return []
        records = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(MemoryRecord.from_dict(json.loads(line)))
                    except Exception:
                        pass
        return records

    def _load_profile(self) -> HumanProfile:
        path = self.braid_path / "profile.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return HumanProfile(**data)
        return HumanProfile(
            human_id=self.human_id,
            name=None,
            joined_at=self._now(),
        )

    def _save_profile(self) -> None:
        path = self.braid_path / "profile.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.profile), f, indent=2)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _generate_id(prefix: str) -> str:
        raw = f"{prefix}-{time.time_ns()}"
        return f"{prefix}_{hashlib.sha1(raw.encode()).hexdigest()[:12]}"


# ---------------------------------------------------------------------------
# Module-level factory
# ---------------------------------------------------------------------------

_engines: dict[str, TemporalBraidEngine] = {}


def get_braid(human_id: str) -> TemporalBraidEngine:
    """Get or create the Temporal Braid for a Human Principal."""
    if human_id not in _engines:
        _engines[human_id] = TemporalBraidEngine(human_id)
    return _engines[human_id]


# Compatibility wrapper expected by api/twin.py and tests
class TwinMemoryEngine(TemporalBraidEngine):
    """No-arg constructible wrapper around TemporalBraidEngine."""

    def __init__(self, human_id: str = "", storage_path: str = "") -> None:
        if human_id:
            super().__init__(human_id)
        else:
            self.human_id = ""
            self.braid_path = None
            self.profile = None
            self.current_session = None
        self._human_id = human_id

    async def load_session(self, human_id: str, session_id: str = "") -> dict:
        if not self._human_id or self._human_id != human_id:
            super().__init__(human_id)
            self._human_id = human_id
        session = self.open_session(session_id or None)
        return {
            "human_name": self.profile.name if self.profile else human_id,
            "twin_phase": self.profile.twin_phase if self.profile else "nigredo",
            "session_count": self.profile.session_count if self.profile else 0,
            "arc_summary": self.get_arc_summary(),
            "session_id": session.session_id,
            "sacred_memory_active": False,
            "arc_position": 0.0,
        }
